import argparse
import subprocess
import pandas as pd
from tqdm import tqdm
import multiprocessing as mp
from functools import partial

def get_files_by_all_clusters(df):
    """
    Get all file paths organized by their cluster labels, sorted by cluster size in descending order.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing File_Path and Cluster_Label columns
    
    Returns:
    dict: Dictionary where keys are cluster labels and values are lists of file paths,
          ordered by cluster size (largest to smallest)
    """
    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)

def process_single_cluster(cluster_data, kval):
    """
    Process a single cluster by running the yaraMain.py subprocess.
    
    Parameters:
    cluster_data (tuple): Tuple of (cluster_label, file_list)
    kval (pd.DataFrame): DataFrame containing K CSV data
    """
    cluster, file_list = cluster_data
    print(f"Processing Cluster {cluster}")
    
    # Check if the cluster is in the K CSV file
    if cluster not in kval['cluster_index'].values:
        print(f"Cluster {cluster} not found in K CSV file. Skipping.")
        return
    
    listofK = kval[kval['cluster_index'] == cluster]['k_clusters'].values
    print(f"Cluster {cluster} found in K CSV file with k_clusters: {listofK}")
    
    if len(listofK) == 30:
        print("LOG: SANITY VERIFICATION")

    cmd = [
        'python', '/usr/src/app/yaraMain.py',
        '--bfMalicious', '/usr/src/app/intermediate/bloom_filters/malicious-bytes',
        '--bfBenign', '/usr/src/app/intermediate/bloom_filters/benign-bytes',
        '--malwarePath', ','.join(file_list),
        '--generateRule', 'False',
        '--biclusterAlgorithmType', 'SpectralCoCluster',
        '--clusterAlgorithm', 'AugmentedKMeansDBSCANSoft',
        '--ruleOutputType', 'string',
        '--outputDirectory', f'/usr/src/app/YaraTest/AutoPYaraBestFK/SSdeep/Th50/cluster_{cluster}',
        '--augmentedTarget_k'
    ] + [str(k) for k in listofK]
    
    #subprocess.run(cmd)
    # Optionally suppress output:
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_clusters(csv_file, kcsv_file):
    # Read the CSV files
    df = pd.read_csv(csv_file)
    kval = pd.read_csv(kcsv_file)
    
    # Get files organized by clusters
    all_cluster_files = get_files_by_all_clusters(df)
    
    # Filter out clusters with fewer than two elements
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    
    print(f"Number of valid clusters: {len(valid_clusters)}")
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return
    
    # Determine the number of processes (use CPU count, but cap to avoid overloading)
    num_processes = min(mp.cpu_count(), len(valid_clusters), 16)  # Cap at 8 to avoid resource exhaustion
    print(f"Using {num_processes} processes")
    
    # Create a partial function with kval pre-passed
    worker = partial(process_single_cluster, kval=kval)
    
    # Process clusters in parallel
    with mp.Pool(processes=num_processes) as pool:
        # Use imap_unordered for progress tracking
        for _ in tqdm(pool.imap_unordered(worker, valid_clusters.items()), 
                     total=len(valid_clusters), 
                     desc="Processing clusters"):
            pass

def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files from a CSV and run yaraMain.py for each cluster.")
    parser.add_argument(
        '--csv-file', 
        type=str, 
        required=True, 
        help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)'
    )
    parser.add_argument(
        '--kcsv-file', 
        type=str, 
        required=True, 
        help='Path to the K CSV file containing cluster data (must have File_Path and Cluster_Label columns)'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file, args.kcsv_file)