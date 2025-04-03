import argparse
import subprocess
import pandas as pd
from multiprocessing import Pool, cpu_count

def get_files_by_all_clusters(df):
    """
    Get all file paths organized by their cluster labels, sorted by cluster size in descending order.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing File_Path and Cluster_Label columns
    
    Returns:
    dict: Dictionary where keys are cluster labels and values are lists of file paths,
          ordered by cluster size (largest to smallest)
    """
    # Group by Cluster_Label and get lists of File_Path
    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    
    # Sort by length of file lists and create new ordered dictionary
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)


def run_yara_script(args):
    cluster, file_list = args
    print(f"[INFO] Processing Cluster {cluster} with {len(file_list)} files")
    
    cmd = [
        'python', '/usr/src/app/yaraMain.py',
        '--bfMalicious', '/usr/src/app/intermediate/bloom_filters/malicious-bytes',
        '--bfBenign', '/usr/src/app/intermediate/bloom_filters/benign-bytes',
        '--malwarePath', ','.join(file_list),
        '--generateRule', 'False',
        '--biclusterAlgorithmType', 'SpectralCoCluster',
        '--clusterAlgorithm', 'VBGMM',
        '--ruleOutputType', 'string',
        '--outputDirectory', f'/usr/src/app/YaraTest/Baseline/SSdeep/Th70/cluster_{cluster}'
    ]
    
    try:
        subprocess.run(cmd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Cluster {cluster} failed: {e.stderr.decode().strip()}")

def process_clusters(csv_file):
    """
    Process clusters in parallel using multiprocessing.
    """
    df = pd.read_csv(csv_file)
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    for i, (label, file_list) in enumerate(list(valid_clusters.items())[:5]):
        print(f"Cluster {label} (index {i}): {len(file_list)} files")
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return
    num_processes = min(cpu_count(), 32)  # Use max available CPUs but cap at 16
    print(f"[INFO] Using {num_processes} processes")

    tasks = [(cluster, file_list) for cluster, file_list in valid_clusters.items()]
    
    with Pool(processes=num_processes) as pool:
        pool.map(run_yara_script, tasks)

def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files and run yaraMain.py.")
    parser.add_argument(
        '--csv-file', 
        type=str, 
        required=True, 
        help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file)
