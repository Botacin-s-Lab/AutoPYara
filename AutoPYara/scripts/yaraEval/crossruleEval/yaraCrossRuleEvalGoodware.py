import yara
from tqdm import tqdm
from pathlib import Path
import os
import argparse
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_files_by_all_clusters(df):
    givenWkdir = '/usr/src/app/HDDdata/datacopy/'
    # Replace the initial part of the path
    df['File_Path'] = df['File_Path'].str.replace('/usr/src/app/HDDdata/data/Windows/', givenWkdir, regex=False)

    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)

def process_file(file_fname_rules_lock_tuple):
    """
    Process a single file with YARA rules and update DataFrame counts.
    
    Args:
        file_fname_rules_lock_tuple: Tuple of (file_path, file_name, yara_rules, df_lock, df).
    """
    file_path, fname, rules, df_lock, df = file_fname_rules_lock_tuple
    try:
        # Find YARA rule matches for the file
        matches = rules.match(file_path)
        updates = []
        
        # Process each match
        for match in matches:
            # Extract cluster number from rule name (e.g., Cluster123_...)
            cluster_number = re.search(r'Cluster(\d+)_', match.rule)
            if cluster_number:
                cluster_id = cluster_number.group(1)  # Get the numeric part as string
                if cluster_id in df.columns:  # Compare as string
                    updates.append(cluster_id)
        
        # Perform DataFrame updates in a thread-safe manner
        with df_lock:
            for cluster_id in updates:
                df.loc[fname, cluster_id] += 1
    except Exception as e:
        logger.error(f"Error processing file {fname}: {e}")

def main(csv_file, datapath, rPaths, output_file):
    output_file = Path(output_file)
    output_dir = output_file.parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured output directory exists: {output_dir}")
    except Exception as e:
        logger.error(f"Error creating output directory {output_dir}: {e}")
        sys.exit(1)
    
    # Load data

    df_list = pd.read_csv(datapath)
    givenWkdir = '/usr/src/app/HDDdata/'
    # Ensure file paths are valid; replace prefix if needed
    df_list['File_Path'] = df_list['File_Path'].str.replace('/mnt/data_disk1/mabon/', givenWkdir, regex=False)

    filePaths = df_list['File_Path']
    fileName = df_list['File_Name']
    dfclusters = pd.read_csv(csv_file)

    
    # Get clustered files
    all_cluster_files = get_files_by_all_clusters(dfclusters)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    
    # Create a DataFrame with cluster labels as columns (as strings)
    cluster_labels = [str(k) for k in valid_clusters.keys()]
    df = pd.DataFrame(0, index=fileName, columns=cluster_labels)
    
    # Compile YARA rules
    try:
        rules = yara.compile(filepath=rPaths)
    except Exception as e:
        logger.error(f"Error compiling YARA rules from {rPaths}: {e}")
        sys.exit(1)
    
    # Initialize a lock for thread-safe DataFrame updates
    df_lock = Lock()
    
    # Process files with ThreadPoolExecutor
    max_workers = 80  # Adjust based on system
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(tqdm(
                executor.map(
                    process_file,
                    [(fp, fn, rules, df_lock, df) for fp, fn in zip(filePaths, fileName)]
                ),
                total=len(filePaths),
                desc="Processing files"
            ))
    except Exception as e:
        logger.error(f"Error during parallel processing: {e}")
        sys.exit(1)
    
    # Save results
    try:
        df.to_csv(output_file, index=True)  # Include index (file names)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving output to {output_file}: {e}")
        sys.exit(1)
    
    return 0

def validate_csv_extension(file_path):
    """Validate that the file path has a .csv extension."""
    if not file_path.lower().endswith('.csv'):
        raise argparse.ArgumentTypeError(f"Output file '{file_path}' must have a .csv extension")
    return file_path

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate YARA rules for goodware files.")
    parser.add_argument('--csv-file', type=str, required=True, help='Path to CSV file with cluster info')
    parser.add_argument('--datapath', type=str, required=True, help='Path to CSV file with file paths')
    parser.add_argument('--rPaths', type=str, required=True, help='Path to YARA rules file')
    parser.add_argument('--opfile', type=validate_csv_extension, required=True, help='Output file path (must end with .csv)')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    exit(main(args.csv_file, args.datapath, args.rPaths, args.opfile))