import argparse
import subprocess
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import os
import random

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
    try:   
        cluster, file_list, TH = args
        #k=int(len(file_list))
        #k = int(len(file_list) / 2)

        # # get max possible K
        max_k = int(len(file_list))

        # select random k between 1 and max_k (inclusive)
        k = random.randint(1, max_k)
        listofK = [k]

        dir_path_skip=f'/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/sdhash/AutoPYara/Heuristics/Bad/Random/Th{TH}/cluster_{cluster}'
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
            '--clusterAlgorithm', 'AugmentedKMeansDBSCAN',
            '--ruleOutputType', 'string',
            '--outputDirectory', f'/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/sdhash/AutoPYara/Heuristics/Bad/Random/Th{TH}/cluster_{cluster}',
            '--augmentedTarget_k'
        ] + [str(k) for k in listofK]
        # print(cmd)
        # exit(-1)
        subprocess.run(cmd)
        #subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 1  # success
    except Exception as e:
        print(f"[ERROR] Cluster {args[0]} failed: {e}")
        return 0
def process_clusters(csv_file, TH):
    df = pd.read_csv(csv_file)
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 2}
    
    print(f"{len(valid_clusters)} clusters with at least 2 files.")
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return

    task_args = [(cluster, files, TH) for cluster, files in valid_clusters.items()]

    print("Starting multiprocessing pool...")
    with Pool(processes=min(cpu_count(), 10)) as pool:
        list(tqdm(pool.imap(handle_softk_cluster, task_args), total=len(task_args)))

def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files from a CSV and run yaraMain.py for each cluster.")
    parser.add_argument('--csv-file', type=str, required=True, help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)')
    parser.add_argument(
        '--TH', 
        type=str, 
        required=True, 
        help='Threshold value (THV) for sdhash directory path'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file, args.TH)
