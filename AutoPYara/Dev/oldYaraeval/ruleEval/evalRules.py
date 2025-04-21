import argparse
import subprocess
import pandas as pd
import os
from tqdm import tqdm
def get_yara_files(cluster, base_path):
    yara_files = []
    cluster_path = os.path.join(base_path, f'cluster_{cluster}')
    # Check if cluster directory exists
    if not os.path.exists(cluster_path):
        return yara_files  # Return empty list if cluster doesn't exist

    # Loop through possible X values (e.g., 1 to 30 or more)
    x = 1
    while True:
        subfolder = os.path.join(cluster_path, f'{x}')
        if not os.path.exists(subfolder):
            break  # Stop if folder doesn't exist
        
        # Look for all .yara files in this subfolder
        for file_name in os.listdir(subfolder):
            if file_name.endswith('.yara'):
                full_path = os.path.join(subfolder, file_name)
                yara_files.append(full_path)
        x += 1
    
    return yara_files

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


def process_clusters(csv_file,thv):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    mainbase='/usr/src/app/YaraTest/Baseline/SSdeep/'
    # Get files organized by clusters
    all_cluster_files = get_files_by_all_clusters(df)
        # Filter out clusters with fewer than two elements
    valid_clusters= {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    valid_clusters2= {k: v for k, v in all_cluster_files.items() if len(v) >= 2}

    #print(valid_clusters)
    print(len(valid_clusters))
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return
    # Process each cluster
    for cluster_rule, file_list_rule in valid_clusters.items():

        print(f"Processing Rules from Cluster {cluster_rule}")
        rulesPath=get_yara_files(cluster_rule, base_path= os.path.join(mainbase, f'Th{thv}'))
        for cluster, file_list in tqdm(valid_clusters2.items()):
            if cluster==cluster_rule:
                continue
            path = os.path.join(mainbase, f'CrossRuleEval/Th{thv}/RuleCluster_{cluster_rule}')
            if not os.path.exists(path):
                os.makedirs(path)
            # print(file_list)
            cmd = [
                'python', '/usr/src/app/yaraEval.py',
                '--rulePath', ','.join(rulesPath),
                '--directory', ','.join(file_list),
                '--eval', 'batchEval',
                '--ruleCluster', str(cluster_rule),  # Convert to string
                '--evalCluster', str(cluster),       # Convert to string
                '--output', os.path.join(path, f'Evalcluster_{cluster}.csv')
            ]
            subprocess.run(cmd)


def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files from a CSV and run yaraMain.py for each cluster.")
    parser.add_argument(
        '--csv-file', 
        type=str, 
        required=True, 
        help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)'
    )

    parser.add_argument(
        '--thv', 
        type=str, 
        required=True, 
        help='threshold Val'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file,args.thv)