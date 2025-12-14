import argparse
import subprocess
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from pathlib import Path
import os
from tempfile import NamedTemporaryFile
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



def handle_softk_cluster(args):
    cluster, file_list, kval, TH = args

    try:
        kval_value = kval.loc[kval['cluster_index'] == cluster, 'k_clusters']
        if pd.isna(kval_value).any() or kval_value.isin(['FAILED']).any():
            print(f"[INFO] Cluster {cluster} has NaN or 'FAILED' in k_clusters. Skipping.")
            return
        dir_path = f'/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/sdhash/AutoPYara/WorstPyara/Th{TH}/cluster_{cluster}'
        if os.path.exists(dir_path):
            print(f"[INFO] Skipping: {dir_path} already exists.")
            return

        # protect against giant argument list
        malwarePathArg = None
        if len(','.join(file_list)) > 100_000:  # approximate safeguard
            with NamedTemporaryFile(mode="w", delete=False) as tf:
                for f in file_list:
                    tf.write(f + "\n")
                malwarePathArg = f"@{tf.name}"
            print(f"[INFO] Cluster {cluster} uses temp file {tf.name} for malwarePath.")
        else:
            malwarePathArg = ','.join(file_list)

        cmd = [
            'python', '/usr/src/app/yaraMain2.py',
            '--bfMalicious', '/usr/src/app/YaraResults/RetrainedBloomFilters/malicious/',
            '--bfBenign', '/usr/src/app/YaraResults/RetrainedBloomFilters/benign/',
            '--malwarePath', malwarePathArg,
            '--generateRule', 'False',
            '--HardK', 'False',
            '--biclusterAlgorithmType', 'SpectralCoCluster',
            '--clusterAlgorithm', 'AugmentedKMeansDBSCAN',
            '--ruleOutputType', 'string',
            '--outputDirectory', dir_path
        ]

        print(f"[INFO] Running subprocess for cluster {cluster} with {len(file_list)} files.")
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Subprocess failed for cluster {cluster}: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in cluster {cluster}: {e}")

def process_clusters(csv_file, kcsv_file, TH):
    try:
        df = pd.read_csv(csv_file)
        kval = pd.read_csv(kcsv_file)
    except Exception as e:
        print(f"[FATAL] Error reading CSV files: {e}")
        return

    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}

    print(f"[INFO] {len(valid_clusters)} clusters with at least 2 files.")
    if not valid_clusters:
        print("[INFO] No clusters with at least two files. Exiting.")
        return

    task_args = [(cluster, files, kval, TH) for cluster, files in valid_clusters.items()]
    
    print("[INFO] Starting multiprocessing pool...")
    with Pool(processes=min(cpu_count(), 10)) as pool:
        list(tqdm(pool.imap(handle_softk_cluster, task_args), total=len(task_args)))

def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files from a CSV and run yaraMain.py for each cluster.")
    parser.add_argument('--csv-file', type=str, required=True, help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)')
    parser.add_argument('--kcsv-file', type=str, required=True, help='Path to the K CSV file containing cluster K-values')
    parser.add_argument('--TH', type=str, required=True, help='Threshold value (THV) for sdhash directory path')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file, args.kcsv_file, args.TH)