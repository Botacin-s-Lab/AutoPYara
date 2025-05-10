import pandas as pd
import yara
from tqdm import tqdm
from pathlib import Path
import os
import argparse
import json

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

def read_and_evaluate_rules(base_path, valid_clusters):
    """
    Reads YARA rules from base_path, evaluates each rule, and returns a mapping of results.
    
    Args:
        base_path (str): Path to the folder containing cluster subfolders.
        valid_clusters (dict): Dictionary mapping cluster names to lists of files.
    
    Returns:
        dict: Mapping of (cluster, rule_id) to DataFrame of results.
    """
    base_path = Path(base_path)
    if not base_path.is_dir():
        raise ValueError(f"Base path {base_path} is not a valid directory.")
    
    results_map = {}
    i=0
    for cluster_folder in tqdm(base_path.glob("cluster_*"), desc="Processing cluster folders"):
        i+=1
        if i>=5:
            break
        cluster_name = cluster_folder.name
        for rule_folder in cluster_folder.glob("[0-9]*"):
            rule_id = rule_folder.name
            rule_file = rule_folder / "yaraRule.yar"
            if rule_file.exists():
                rules = validateRule(rule_file)
                if rules is None:
                    print(f"Skipping {rule_file} due to validation error.")
                    continue
                df = evaluateRule(rules, valid_clusters)
                results_map[(cluster_name, rule_id)] = df
                # output_dir = base_path / "results" / cluster_name
                # output_dir.mkdir(parents=True, exist_ok=True)
                # output_file = output_dir / f"rule_{rule_id}_results.csv"
                # df.to_csv(output_file, index=False)
                #print(f"Saved results for {cluster_name}/rule_{rule_id} to {output_file}")
    return results_map

def get_files_by_all_clusters(df):
    """
    Organizes file paths by cluster labels, sorted by cluster size.
    
    Args:
        df (pd.DataFrame): DataFrame with File_Path and Cluster_Label columns.
    
    Returns:
        dict: Dictionary of cluster labels to lists of file paths.
    """
    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)

def main(csv_file, rPaths):
    """Main function to process CSV and evaluate YARA rules."""
    df = pd.read_csv(csv_file)
    required_columns = ['File_Path', 'Cluster_Label']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV file must contain columns: {required_columns}")
    
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    results_map = read_and_evaluate_rules(rPaths, valid_clusters)
    json_file =  "results_map.json"
    if results_map:
        json_data = {
            f"{cluster},rule_{rule_id}": df.to_dict('records')
            for (cluster, rule_id), df in results_map.items()
        }
        try:
            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=4)
            print(f"Saved all results_map data to {json_file}")
        except Exception as e:
            print(f"Error saving results_map to {json_file}: {e}")
    else:
        print("No results to save to JSON (results_map is empty).")
    return 0

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate YARA rules for clustered files.")
    parser.add_argument('--csv-file', type=str, required=True, help='Path to CSV file with cluster data')
    parser.add_argument('--rPaths', type=str, required=True, help='Path to YARA rules directory')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    exit(main(args.csv_file, args.rPaths))