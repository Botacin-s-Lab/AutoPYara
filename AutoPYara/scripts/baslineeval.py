import argparse
import subprocess
import pandas as pd

def get_files_by_all_clusters(df):
    """
    Get all file paths organized by their cluster labels.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing File_Path and Cluster_Label columns
    
    Returns:
    dict: Dictionary where keys are cluster labels and values are lists of file paths
    """
    # Group by Cluster_Label and convert to dictionary
    cluster_files_dict = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    return cluster_files_dict

def process_clusters(csv_file):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Get files organized by clusters
    all_cluster_files = get_files_by_all_clusters(df)
    
    # Process each cluster
    for cluster, file_list in all_cluster_files.items():
        print(f"Processing Cluster {cluster}")
        # print(file_list)
        cmd = [
            'python', '/usr/src/app/yaraMain.py',
            '--bfMalicious', '/usr/src/app/intermediate/bloom_filters/malicious',
            '--bfBenign', '/usr/src/app/intermediate/bloom_filters/benign',
            '--malwarePath', ','.join(file_list),
            '--generateRule', 'False',
            '--biclusterAlgorithmType', 'SpectralCoCluster',
            '--clusterAlgorithm', 'VBGMM',
            '--ruleOutputType', 'string',
            '--outputDirectory', f'/usr/src/app/YaraTest/Baseline/SSdeep/Th60/cluster_{cluster}'
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
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file)