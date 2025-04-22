import argparse
import subprocess
import pandas as pd

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


def process_clusters(csv_file):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Get files organized by clusters
    all_cluster_files = get_files_by_all_clusters(df)
        # Filter out clusters with fewer than two elements
    valid_clusters= {k: v for k, v in all_cluster_files.items() if len(v) >= 2}

    print(valid_clusters)
    print(len(valid_clusters))
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return
    # Process each cluster
    for cluster, file_list in valid_clusters.items():
        print(f"Processing Cluster {cluster}")
        # print(file_list)
        cmd = [
            'python', '/usr/src/app/yaraMain.py',
            '--bfMalicious', '/usr/src/app/intermediate/bloom_filters/malicious-bytes',
            '--bfBenign', '/usr/src/app/intermediate/bloom_filters/benign-bytes',
            '--malwarePath', ','.join(file_list),
            '--generateRule', 'False',
            '--biclusterAlgorithmType', 'SpectralCoCluster',
            '--clusterAlgorithm', 'VBGMM',
            '--ruleOutputType', 'string',
            '--outputDirectory', f'/usr/src/app/YaraTest/Baseline/SSdeep/Th80/cluster_{cluster}'
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




# def original_autoyara():
#                 return myYara.generate(
#                     directory_path,
#                     bloom_filter_malicious_path,
#                     bloom_filter_benign_path,
#                     bicluster_alg="SpectralCoCluster",
#                     cluster_alg="VBGMM",
#                     output_format="yara-python",
#                     selection_heuristic="AutoYara",
#                     bicluster_feature_prune_coverage=50,
#                 )
#MABON U USED A DIFFRENCT SECLECTION HEURISTIC


# def augmented_DBSCAN(target_k):
        #     return myYara.generate(
        #         directory_path,
        #         bloom_filter_malicious_path,
        #         bloom_filter_benign_path,
        #         bicluster_alg="SpectralCoCluster",
        #         cluster_alg="AugmentedKMeansDBSCANSoft",
        #         output_format="yara-python",
        #         augmented_target_k=target_k,
        #         bicluster_feature_prune_coverage=50,
        #          selection_heuristic: SelectionHeuristic = "PYara", 
        #     )