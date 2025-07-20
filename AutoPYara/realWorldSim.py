import argparse
import subprocess
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import pandas as pd
import os
from AutoPYara import AutoPYara
from utils.utils import split_file_paths,save_kval_to_file,sanitize_yara_rule
import yara


bfMalicious='/usr/src/app/YaraResults/RetrainedBloomFilters/malicious/'
bfBenign='/usr/src/app/YaraResults/RetrainedBloomFilters/benign/'



def get_files_by_all_clusters(df):
    givenWkdir = '/usr/src/app/HDDdata/'
    df['File_Path'] = df['File_Path'].str.replace('/usr/src/app/', givenWkdir, regex=False)
    # Group by Cluster_Label and get lists of File_Path
    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    # Sort by length of file lists and create new ordered dictionary
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)


def baseYara(dir_path_skip,file_list):
    subfolder_path = os.path.join(dir_path_skip,'baseYara')
    os.makedirs(subfolder_path, exist_ok=True)

    yara_instance = AutoPYara()
    a = yara_instance.generate(
        file_list,
        bfMalicious,
        bfBenign,
        bicluster_alg='SpectralCoCluster',
        cluster_alg='VBGMM',
        output_format='string',
        output_dir=subfolder_path,
        bicluster_feature_prune_coverage=50,
        selection_heuristic="AutoYara",
    )
    save_kval_to_file(a, subfolder_path)
    return (int(a['k_clusters'])),str(a['output'])


def test_rule(yara_python_rule, files):
    clean_rule = sanitize_yara_rule(yara_python_rule)
    rules = yara.compile(source=str(clean_rule))
    """Runs the rule on all samples in a directory."""
    matches_count = 0
    total = 0
    for file in files:
        total += 1
        if not os.path.exists(file):
            continue
        try:
            matches = rules.match(file)
            if matches:
                matches_count += 1
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue
    return matches_count, total


def bestYara(dir_path_skip,file_list,ktarget_kval):
    subfolder_path = os.path.join(dir_path_skip,'bestYara')
    os.makedirs(subfolder_path, exist_ok=True)
    yara_instance = AutoPYara()
    a = yara_instance.generate(
        file_list,
        bfMalicious,
        bfBenign,
        bicluster_alg='SpectralCoCluster',
        cluster_alg='AugmentedKMeansDBSCANSoft',
        output_format='string',
        output_dir=subfolder_path,
        augmented_target_k=ktarget_kval, 
        bicluster_feature_prune_coverage=50,
        selection_heuristic="PYara",
    )
    save_kval_to_file(a, subfolder_path)
    return str(a['output'])

def run_yara(args):
    cluster, file_list,TH,train_ratio = args
    dir_path_skip=f'/usr/src/app/BUILDTEST/Th{TH}/cluster_{cluster}'
    if os.path.exists(dir_path_skip):
        print(f"Skipping: {dir_path_skip} already exists.")
        #return 0
    else:
        try:
            os.makedirs(dir_path_skip, exist_ok=True)
            train_list, test_list=split_file_paths(file_list, dir_path_skip, train_ratio=train_ratio, seed=42)    
            print(f"Processing cluster: {cluster} with {len(train_list)} training files and {len(test_list)} testing files")
            print("LOG:----------------------------------- Generating baseYara for cluster: ", cluster)
            ktarget_kval,baserule=baseYara(dir_path_skip,train_list)



            matches_count, total=test_rule(baserule, test_list)
            tprate = matches_count / total if total > 0 else 0
            tprate_file = os.path.join(dir_path_skip, 'tprateAutoyaraBase.txt')
            with open(tprate_file, 'w') as f:
                f.write(f"TP Rate: {tprate:.4f} ({matches_count}/{total})\n")


            print("LOG:-----------------------------------Using K Value : ",ktarget_kval)
            print("LOG:----------------------------------- Generating bestYara for cluster: ", cluster)

            yara_python_rule=bestYara(dir_path_skip,train_list,ktarget_kval)
            matches_count, total=test_rule(yara_python_rule, test_list)
            tprate = matches_count / total if total > 0 else 0


            print(f"LOG:----------------------------------- Testing bestYara for cluster: {cluster}")
            print(f"LOG:----------------------------------- Matches found: {matches_count}/{total}")
            print(f"LOG:----------------------------------- True Positive Rate: {tprate:.2f}")


            tprate_file = os.path.join(dir_path_skip, 'tprateAutoPYara.txt')
            with open(tprate_file, 'w') as f:
                f.write(f"TP Rate: {tprate:.4f} ({matches_count}/{total})\n")
            print(f"TP rate saved to: {tprate_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Cluster {cluster} failed: {e.stderr.decode().strip()}")




def process_clusters(csv_file,TH,train_ratio):
    """
    Process clusters in parallel using multiprocessing with tqdm progress bar.
    """
    df = pd.read_csv(csv_file)
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 10}
    print(f"Number of valid clusters (≥ 50 files): {len(valid_clusters)}")

    for i, (label, file_list) in enumerate(list(valid_clusters.items())[:5]):
        print(f"Cluster {label} (index {i}): {len(file_list)} files")
    
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return

    num_processes = min(cpu_count(), 1)
    print("USING", num_processes)
    print(f"[INFO] Using {num_processes} processes")

    tasks = [(cluster, file_list,TH,train_ratio) for cluster, file_list in valid_clusters.items()]

    with Pool(processes=num_processes) as pool:
        for _ in tqdm(pool.imap_unordered(run_yara, tasks), total=len(tasks)):
            pass  # Progress bar updates here

def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files and run yaraMain.py.")
    parser.add_argument(
        '--csv-file', 
        type=str, 
        required=True, 
        help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)'
    )
    parser.add_argument(
        '--TH', 
        type=str, 
        required=True, 
        help='Threshold value (THV) for sdhash directory path'
    )

    parser.add_argument(
        '--train-ratio', 
        type=float, 
        required=True, 
        help='Proportion of data to use for training (between 0 and 1)'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file,args.TH,args.train_ratio)
