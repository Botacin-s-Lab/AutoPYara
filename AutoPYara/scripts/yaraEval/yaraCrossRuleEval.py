import pandas as pd
import yara
from tqdm import tqdm
from pathlib import Path
import os
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import threading
import pyarrow.parquet as pq
import pyarrow as pa


def validate_parquet_extension(file_path):
    """Validate that the file path has a .parquet extension."""
    if not file_path.lower().endswith('.parquet'):
        raise argparse.ArgumentTypeError(f"Output file '{file_path}' must have a .parquet extension")
    return file_path
def test_rule(yara_python_rule, files):
    """Runs the rule on all samples in a directory."""
    matches_count = 0
    total = 0
    for file in files:
        total += 1
        if not os.path.exists(file):
            continue
        try:
            matches = yara_python_rule.match(file)
            if matches:
                matches_count += 1
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue
    return matches_count, total

def evaluateRule(rules, valid_clusters):
    """Evaluates YARA rules against files in valid_clusters."""
    results = []
    for cluster, file_list in valid_clusters.items():
        matches, total = test_rule(rules, file_list)
        tprate = matches / total if total > 0 else 0
        results.append({
            'cluster': cluster,
            'matches': matches,
            'total': total,
            'TPrate': tprate
        })
    if not results:
        print("No results generated, returning empty DataFrame.")
        return pd.DataFrame(columns=['cluster', 'matches', 'total', 'TPrate'])
    return pd.DataFrame(results)

def validateRule(file_path):
    """Validates and compiles a YARA rule file."""
    try:
        rules = yara.compile(filepath=str(file_path))
        return rules
    except yara.SyntaxError as e:
        print(f"Syntax error in YARA rule {file_path}: {e}")
        return None
    except yara.Error as e:
        print(f"Error compiling YARA rule {file_path}: {e}")
        return None

def process_rule_file(cluster_folder, rule_folder, valid_clusters):
    """Processes a single rule file and returns the result for the results_map."""
    cluster_name = cluster_folder.name
    rule_id = rule_folder.name
    rule_file = rule_folder / "yaraRule.yar"
    if rule_file.exists():
        rules = validateRule(rule_file)
        if rules is None:
            print(f"Skipping {rule_file} due to validation error.")
            return None
        df = evaluateRule(rules, valid_clusters)
        return (cluster_name, rule_id), df
    return None

def read_and_evaluate_rules(base_path, valid_clusters, max_workers=50, max_rules=None):
    """
    Reads YARA rules from base_path, evaluates each rule in parallel, and returns a mapping of results.
    Stops after processing max_rules if specified; processes all rules if max_rules is None.
    
    Args:
        base_path (str): Path to the folder containing cluster subfolders.
        valid_clusters (dict): Dictionary mapping cluster names to lists of files.
        max_workers (int, optional): Number of threads to use. Defaults to 50.
        max_rules (int or None, optional): Maximum number of rules to process. Defaults to 100. If None, processes all rules.
    
    Returns:
        dict: Mapping of (cluster, rule_id) to DataFrame of results.
    """
    base_path = Path(base_path)
    if not base_path.is_dir():
        raise ValueError(f"Base path {base_path} is not a valid directory.")
    
    results_map = {}
    results_lock = threading.Lock()  # Lock for thread-safe updates to results_map
    tasks = []
    rule_count = 0

    # Collect tasks (cluster folders and rule folders)
    for cluster_folder in base_path.glob("cluster_*"):
        for rule_folder in cluster_folder.glob("[0-9]*"):
            if max_rules is not None and rule_count >= max_rules:
                break  # Stop collecting tasks if max_rules reached
            tasks.append((cluster_folder, rule_folder))
            rule_count += 1
        if max_rules is not None and rule_count >= max_rules:
            break  # Exit outer loop if max_rules reached

    def process_task(task):
        cluster_folder, rule_folder = task
        result = process_rule_file(cluster_folder, rule_folder, valid_clusters)
        if result:
            with results_lock:
                results_map[result[0]] = result[1]

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(tqdm(executor.map(process_task, tasks), total=len(tasks), desc="Processing rules"))
    
    return results_map

def get_files_by_all_clusters(df):
    """
    Organizes file paths by cluster labels, sorted by cluster size.
    
    Args:
        df (pd.DataFrame): DataFrame with File_Path and Cluster_Label columns.
    
    Returns:
        dict: Dictionary of cluster labels to lists of file paths.
    """
    # givenWkdir = '/mnt/data_disk1/mabon/'
    # # Replace the initial part of the path
    # df['File_Path'] = df['File_Path'].str.replace('/usr/src/app/', givenWkdir, regex=False)
    print(df['File_Path'][0:2])
    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)

def main(csv_file, rPaths,output_file):
    print(output_file)
    output_file = Path(output_file)
    output_dir = output_file.parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Ensured output directory exists: {output_dir}")
    except Exception as e:
        print(f"Error creating output directory {output_dir}: {e}")
        sys.exit(1)
        
    """Main function to process CSV and evaluate YARA rules."""
    df = pd.read_csv(csv_file)
    required_columns = ['File_Path', 'Cluster_Label']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV file must contain columns: {required_columns}")
    
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    results_map = read_and_evaluate_rules(rPaths, valid_clusters)

    if results_map:
        try:
            # Initialize Parquet writer with schema
            schema = pa.schema([
                ('cluster', pa.string()),
                ('rule_id', pa.string()),
                ('matches', pa.int64()),
                ('total', pa.int64()),
                ('TPrate', pa.float64())
            ])
            writer = pq.ParquetWriter(output_file, schema, compression='snappy')

            # Write each DataFrame incrementally to minimize memory usage
            for (cluster, rule_id), df in results_map.items():
                # Convert DataFrame to arrow Table
                table = pa.Table.from_pandas(
                    df.assign(cluster=cluster, rule_id=rule_id)[['cluster', 'rule_id', 'matches', 'total', 'TPrate']],
                    preserve_index=False
                )
                writer.write_table(table)

            # Close the writer
            writer.close()
            print(f"Saved results_map to {output_file} as compressed Parquet")
        except Exception as e:
            print(f"Error saving results_map to {output_file}: {e}")
    else:
        print("No results to save (results_map is empty).")
    return 0

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate YARA rules for clustered files.")
    parser.add_argument('--csv-file', type=str, required=True, help='Path to CSV file with cluster data')
    parser.add_argument('--rPaths', type=str, required=True, help='Path to YARA rules directory')
    parser.add_argument('--opfile', type=validate_parquet_extension, required=True, help='Output file path (must end with .parquet)')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    exit(main(args.csv_file, args.rPaths,args.opfile))