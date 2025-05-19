import argparse
import subprocess
import pandas as pd
from tqdm import tqdm

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('true', '1', 'yes'):
        return True
    elif v.lower() in ('false', '0', 'no'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

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
    givenWkdir = '/usr/src/app/HDDdata/'
    
    # Replace the initial part of the path
    df['File_Path'] = df['File_Path'].str.replace('/usr/src/app/', givenWkdir, regex=False)

    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    
    # Sort by length of file lists and create new ordered dictionary
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)


failure_values = {'nan', 'NaN', 'Failed', 'FAILED'}

def HardKFunc(csv_file,kcsv_file):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    kval=pd.read_csv(kcsv_file)
    # Get files organized by clusters
    all_cluster_files = get_files_by_all_clusters(df)
        # Filter out clusters with fewer than two elements
    valid_clusters= {k: v for k, v in all_cluster_files.items() if len(v) >= 2}

    # print(valid_clusters)
    print(len(valid_clusters))
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return
    # Process each cluster

    for cluster, file_list in tqdm(valid_clusters.items(), desc="Processing clusters"):
        print(f"Processing Cluster {cluster}")
        # print(file_list)
        # Check if the cluster is in the K CSV file
        # Normalize the values to strings for robust comparison
        kval_subset = kval[kval['cluster_index'] == cluster]

        if kval_subset.empty:
            print(f"Cluster {cluster} not found in K CSV file. SEARCHING OPTIMAL K.")
            HPK = 'True'
            listofK=[]
        else:
            k_clusters = kval_subset.iloc[0].get('k_clusters', [])

            # Normalize values to lowercase strings
            k_clusters_normalized = pd.Series(k_clusters).astype(str).str.strip().str.lower()

            failure_indicators = {'nan', 'failed', 'dailed'}

            if k_clusters_normalized.isin(failure_indicators).all():
                print(f"Cluster {cluster} has invalid k_clusters. SEARCHING OPTIMAL K.")
                HPK = 'True'
                listofK=[]
            
            else:
                listofK = kval_subset['k_clusters'].values
                HPK = 'False'
                print(f"Cluster {cluster} found in K CSV file with k_clusters: {listofK}")
                if len(listofK) >= 10:
                    print("LOG: SANITY VERIFICATION")
        cmd = [
            'python', '/usr/src/app/yaraMain.py',
            '--bfMalicious', '/usr/src/app/intermediate/bloom_filters/malicious-bytes',
            '--bfBenign', '/usr/src/app/intermediate/bloom_filters/benign-bytes',
            '--malwarePath', ','.join(file_list),
            '--generateRule', 'False',
            '--HardK', 'True',
            '--HardKPike', HPK,
            '--biclusterAlgorithmType', 'SpectralCoCluster',
            '--clusterAlgorithm', 'AugmentedKMeansDBSCANSoft',
            '--ruleOutputType', 'string',
            '--outputDirectory', f'/usr/src/app/YaraTest/TEMP/cluster_{cluster}',
            '--augmentedTarget_k'
        ] + [str(k) for k in listofK]
        subprocess.run(cmd)
        # Suppress output
        #subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_clusters(csv_file,kcsv_file,HardK):
    if HardK:
        print("LOG: HARD K SETTING")
        HardKFunc(csv_file,kcsv_file)
    else:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        kval=pd.read_csv(kcsv_file)
        # Get files organized by clusters
        all_cluster_files = get_files_by_all_clusters(df)
            # Filter out clusters with fewer than two elements
        valid_clusters= {k: v for k, v in all_cluster_files.items() if len(v) >= 2}

        # print(valid_clusters)
        print(len(valid_clusters))
        if not valid_clusters:
            print("No clusters with at least two files. Exiting.")
            return
        # Process each cluster

        for cluster, file_list in tqdm(valid_clusters.items(), desc="Processing clusters"):
            print(f"Processing Cluster {cluster}")
            # print(file_list)
            # Check if the cluster is in the K CSV file
            if cluster not in kval['cluster_index'].values:
                print(f"Cluster {cluster} not found in K CSV file. Skipping.")
                continue
            else:
                listofK=kval[kval['cluster_index'] == cluster]['k_clusters'].values
                print(f"Cluster {cluster} found in K CSV file with k_clusters: {listofK}")
                if(len(listofK)>=10):
                    print("LOG: SANITY VERIFICATION")

        #     subprocess.run(cmd)

            cmd = [
                'python', '/usr/src/app/yaraMain.py',
                '--bfMalicious', '/usr/src/app/intermediate/bloom_filters/malicious-bytes',
                '--bfBenign', '/usr/src/app/intermediate/bloom_filters/benign-bytes',
                '--malwarePath', ','.join(file_list),
                '--generateRule', 'False',
                '--HardK', 'False',
                '--biclusterAlgorithmType', 'SpectralCoCluster',
                '--clusterAlgorithm', 'AugmentedKMeansDBSCANSoft',
                '--ruleOutputType', 'string',
                '--outputDirectory', f'/usr/src/app/YaraTest/TEMP/cluster_{cluster}',
                '--augmentedTarget_k'
            ] + [str(k) for k in listofK]
            subprocess.run(cmd)
            # Suppress output
            #subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

    parser.add_argument('-hk', '--HardK', type=str2bool, default=False, help='THIS IS FOR OPTIMAL K SELECTION. IF TRUE, THE K VALUE WILL BE HARD SET. IF FALSE, THE K VALUE WILL BE SOFT SET. DEFAULT: FALSE')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file,args.kcsv_file,args.HardK)




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