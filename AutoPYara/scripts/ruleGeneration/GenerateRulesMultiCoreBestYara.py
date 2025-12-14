import argparse
import subprocess
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import os
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
    givenWkdir = '/usr/src/app/HDDdata/datacopy/'
    # Replace the initial part of the path
    df['File_Path'] = df['File_Path'].str.replace('/usr/src/app/HDDdata/data/Windows/', givenWkdir, regex=False)

    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)

failure_values = {'nan', 'NaN', 'Failed', 'FAILED'}

def handle_hardk_cluster(args):
    try:
        cluster, file_list, kval, TH = args
        kval_subset = kval[kval['cluster_index'] == cluster]

        if kval_subset.empty:
            print(f"Cluster {cluster} not found in K CSV file. SEARCHING OPTIMAL K.")
            HPK = 'True'
            return 0
            listofK = []
        else:
            k_clusters = kval_subset.iloc[0].get('k_clusters', [])
            k_clusters_normalized = pd.Series(k_clusters).astype(str).str.strip().str.lower()

            if k_clusters_normalized.isin(failure_values).all():
                print(f"Cluster {cluster} has invalid k_clusters. SEARCHING OPTIMAL K.")
                HPK = 'True'
                return 0
                listofK = []
            else:
                listofK = kval_subset['k_clusters'].values
                HPK = 'False'
                print(f"Cluster {cluster} found in K CSV file with k_clusters: {listofK}")

        dir_path_skip=f'/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/sdhash/AutoPYara/BestK/Th{TH}/cluster_{cluster}'
        if os.path.exists(dir_path_skip):
            print(f"Skipping: {dir_path_skip} already exists.")
            return 0
        cmd = [
            'python', '/usr/src/app/yaraMain.py',
            '--bfMalicious', '/usr/src/app/YaraResults/RetrainedBloomFilters/malicious/',
            '--bfBenign', '/usr/src/app/YaraResults/RetrainedBloomFilters/benign/',
            '--malwarePath', ','.join(file_list),
            '--generateRule', 'False',
            '--HardK', 'True',
            '--HardKPike', HPK,
            '--biclusterAlgorithmType', 'SpectralCoCluster',
            '--clusterAlgorithm', 'AugmentedKMeansDBSCANSoft',
            '--ruleOutputType', 'string',
            '--outputDirectory', f'/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/sdhash/AutoPYara/BestK/Th{TH}/cluster_{cluster}',
            '--augmentedTarget_k'
        ] + [str(k) for k in listofK]
        subprocess.run(cmd)
        return 1  # success
    except Exception as e:
        print(f"[ERROR] Cluster {args[0]} failed: {e}")
        return 0


def handle_softk_cluster(args):
    try:
        cluster, file_list, kval ,TH = args
        if cluster not in kval['cluster_index'].values:
            print(f"Cluster {cluster} not found in K CSV file. Skipping.")
            return

        listofK = kval[kval['cluster_index'] == cluster]['k_clusters'].values
        # print(f"Cluster {cluster} found in K CSV file with k_clusters: {listofK}")
        # if len(listofK) == 5:
        #     print("LOG: SANITY VERIFICATION")

        dir_path_skip=f'/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/sdhash/AutoPYara/Th{TH}/cluster_{cluster}'
        if os.path.exists(dir_path_skip):
            print(f"Skipping: {dir_path_skip} already exists.")
            return 0
        cmd = [
            'python', '/usr/src/app/yaraMain.py',
            '--bfMalicious', '/usr/src/app/YaraResults/RetrainedBloomFilters/malicious/',
            '--bfBenign', '/usr/src/app/YaraResults/RetrainedBloomFilters/benign/',
            '--malwarePath', ','.join(file_list),
            '--generateRule', 'False',
            '--HardK', 'False',
            '--biclusterAlgorithmType', 'SpectralCoCluster',
            '--clusterAlgorithm', 'AugmentedKMeansDBSCANSoft',
            '--ruleOutputType', 'string',
            '--outputDirectory', f'/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/sdhash/AutoPYara/Th{TH}/cluster_{cluster}',
            '--augmentedTarget_k'
        ] + [str(k) for k in listofK]
        #subprocess.run(cmd)
        #subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[ERROR] Cluster {args[0]} failed: {e}")
        return 0

def process_clusters(csv_file, kcsv_file, TH, HardK):
    df = pd.read_csv(csv_file)
    kval = pd.read_csv(kcsv_file)
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    
    print(f"{len(valid_clusters)} clusters with at least 2 files.")
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return

    task_args = [(cluster, files, kval,TH) for cluster, files in valid_clusters.items()]
    
    print("Starting multiprocessing pool...")
    with Pool(processes=min(cpu_count(),15)) as pool:
        if HardK:
            print("LOG: HARD K SETTING")
            list(tqdm(pool.imap(handle_hardk_cluster, task_args), total=len(task_args)))
        else:
            print("LOG: NOT HARD K SETTING")
            list(tqdm(pool.imap(handle_softk_cluster, task_args), total=len(task_args)))

def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files from a CSV and run yaraMain.py for each cluster.")
    parser.add_argument('--csv-file', type=str, required=True, help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)')
    parser.add_argument('--kcsv-file', type=str, required=True, help='Path to the K CSV file containing cluster K-values')
    parser.add_argument('-hk', '--HardK', type=str2bool, default=False, help='Set to True for HardK mode')
    parser.add_argument(
        '--TH', 
        type=str, 
        required=True, 
        help='Threshold value (THV) for sdhash directory path'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file, args.kcsv_file,args.TH, args.HardK)
