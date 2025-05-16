import yara
from tqdm import tqdm
from pathlib import Path
import os
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import threading
import pandas as pd
import pickle
import sys

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
    
    Args:
        base_path (str): Path to the folder containing cluster subfolders.
        valid_clusters (dict): Dictionary mapping cluster names to lists of files.
        max_workers (int, optional): Number of threads to use. Defaults to 50.
        max_rules (int, optional): Maximum number of rules to evaluate. If None, no limit is applied.
    
    Returns:
        dict: Mapping of (cluster, rule_id) to DataFrame of results.
    """
    base_path = Path(base_path)
    if not base_path.is_dir():
        raise ValueError(f"Base path {base_path} is not a valid directory.")
    
    results_map = {}
    results_lock = threading.Lock()  # Lock for thread-safe updates to results_map
    tasks = []

    # Collect all tasks (cluster folders and rule folders)
    for cluster_folder in base_path.glob("cluster_*"):
        for rule_folder in cluster_folder.glob("[0-9]*"):
            tasks.append((cluster_folder, rule_folder))
    
    # Apply max_rules limit if specified
    if max_rules is not None:
        tasks = tasks[:max_rules]
        print(f"Limiting evaluation to {max_rules} rules.")
    
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
    givenWkdir = '/mnt/data_disk1/mabon/'
    # Replace the initial part of the path
    #df['File_Path'] = df['File_Path'].str.replace('/usr/src/app/', givenWkdir, regex=False)
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
    # Saving
    with open(output_file, "wb") as f:
        pickle.dump(results_map, f)
    return 0


def validate_pkl_extension(file_path):
    """Validate that the file path has a .pkl extension."""
    if not file_path.lower().endswith('.pkl'):
        raise argparse.ArgumentTypeError(f"Output file '{file_path}' must have a .pkl extension")
    return file_path


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate YARA rules for clustered files.")
    parser.add_argument('--csv-file', type=str, required=True, help='Path to CSV file with cluster data')
    parser.add_argument('--rPaths', type=str, required=True, help='Path to YARA rules directory')
    parser.add_argument('--opfile', type=validate_pkl_extension, required=True, help='Output file path (must end with .pkl)')
    return parser.parse_args()
if __name__ == '__main__':
    args = parse_args()
    exit(main(args.csv_file, args.rPaths,args.opfile))