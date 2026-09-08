import argparse
import subprocess
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import pandas as pd
import os
from AutoPYara import AutoPYara
from utils.utils import split_file_paths,save_kval_to_file,sanitize_yara_rule
import yara
import time
import threading
bfMalicious='/usr/src/app/HDDdata/AutoPYaraReady/Autoyara/YaraResults/RetrainedBloomFilters/malicious/'
bfBenign='/usr/src/app/HDDdata/AutoPYaraReady/Autoyara/YaraResults/RetrainedBloomFilters/benign/'


# /usr/src/app/datacopy/
def get_files_by_all_clusters(df):
    givenWkdir = '/usr/src/app/HDDdata/datacopy/'
    # Replace the initial part of the path
    df['File_Path'] = df['File_Path'].str.replace('/usr/src/app/HDDdata/data/Windows/', givenWkdir, regex=False)

    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
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



def RuleTEST(rule, file_list,tprate_file):
    matches_count, total=test_rule(rule, file_list)
    tprate = matches_count / total if total > 0 else 0
    with open(tprate_file, 'w') as f:
        f.write(f"TP Rate: {tprate:.4f} ({matches_count}/{total})\n")

def find_file_families(df_vtfam, file_list):
    # Initialize an empty list to store cluster labels
    cluster_labels = []
    # Iterate through the file_list
    for file_name in file_list:
        # Find the row in the dataframe where File_Name matches
        match = df_vtfam[df_vtfam['File_Path'] == file_name]
        
        # If a match is found, append the Cluster_Label to the list
        if not match.empty:
            cluster_labels.append(int(match['Cluster_Label'].iloc[0]))
        else:
            # If no match is found, append None or a placeholder
            continue
    
    return cluster_labels

def HeuristicExtract(file_list):
    givenWkdir = '/usr/src/app/HDDdata/datacopy/'
    df_optimumK=pd.read_csv("/usr/src/app/HDDdata/AutoPYaraReady/Autoyara/YaraResults/clusterCSV/BestKvalueCluster_VT.csv")
    df_vtfam=pd.read_csv("/usr/src/app/HDDdata/AutoPYaraReady/Autoyara/YaraResults/clusterCSV/virusTotal/MainVtCluster.csv")
    df_vtfam['File_Path'] = df_vtfam['File_Path'].str.replace('/mnt/data_disk1/mabon/datacopy/', givenWkdir, regex=False)

    cluster_labels = find_file_families(df_vtfam, file_list)
    unique_clusters = list(set(cluster_labels))
    optimal_k_dict = dict(zip(df_optimumK['cluster_number'], df_optimumK['best_k_value']))

    # Step 3: Find the best_k_value for each unique cluster in cluster_labels
    optimal_k_values = [optimal_k_dict.get(cluster, 1) for cluster in unique_clusters]  # Default to 1 if cluster not found

        # Sort the optimal_k_values in descending order
    sorted_k = sorted(optimal_k_values, reverse=True)

    optimal_k = next((k for k in sorted_k if k <= len(file_list)), None)
    # print("Optimal k values for each cluster:", optimal_k)
    return optimal_k


    
def run_yara(args):
    cluster, file_list,TH,train_ratio = args
    dir_path_skip=f'/usr/src/app/YaraResultsFinal/Exp1NOHEUsdhash/Th{TH}/Ratio_{train_ratio}/cluster_{cluster}'
    if os.path.exists(dir_path_skip):
        print(f"Skipping: {dir_path_skip} already exists.")
        #return 0
    else:
        import traceback
        try:
            os.makedirs(dir_path_skip, exist_ok=True)
            train_list, test_list = split_file_paths(file_list, dir_path_skip, train_ratio=train_ratio, seed=42)

            ktarget_kval, baserule = baseYara(dir_path_skip, train_list)

            RuleTEST(baserule, train_list, tprate_file=os.path.join(dir_path_skip, 'tprateAutoyaraBase_Train.txt'))
            RuleTEST(baserule, test_list, tprate_file=os.path.join(dir_path_skip, 'tprateAutoyaraBase_Test.txt'))

            ktarget_kval = len(train_list)


            yara_python_rule = bestYara(dir_path_skip, train_list, ktarget_kval)

            RuleTEST(yara_python_rule, train_list, tprate_file=os.path.join(dir_path_skip, 'tprateAutoPYara_Train.txt'))
            RuleTEST(yara_python_rule, test_list, tprate_file=os.path.join(dir_path_skip, 'tprateAutoPYara_Test.txt'))

        except Exception as e:
            print(f"Error processing cluster {cluster}: {file_list}")
            print(f"Exception: {e}")
            traceback.print_exc()

def run_with_timeout(num_processes, tasks, timeout_seconds=2000):
    # Create an Event to signal timeout
    timeout_event = threading.Event()
    
    # Function to run the pool processing
    def process_tasks():
        try:
            with Pool(processes=num_processes) as pool:
                for _ in tqdm(pool.imap_unordered(run_yara, tasks), total=len(tasks)):
                    if timeout_event.is_set():
                        pool.terminate()  # Terminate pool if timeout occurs
                        break
        except Exception as e:
            print(f"Error in pool processing: {e}")
        finally:
            pool.close()
            pool.join()  # Ensure pool resources are cleaned up
    
    # Start the processing in a separate thread
    process_thread = threading.Thread(target=process_tasks)
    process_thread.start()
    
    # Wait for the timeout duration or until processing completes
    process_thread.join(timeout=timeout_seconds)
    
    if process_thread.is_alive():
        print("Timeout of 2 hours reached, terminating pool...")
        timeout_event.set()  # Signal to terminate
        process_thread.join()  # Wait for the thread to finish after termination
        return False  # Indicate timeout occurred
    else:
        print("Processing completed within 2 hours.")
        return True  # Indicate successful completion


def process_clusters(csv_file,TH,train_ratio):
    """
    Process clusters in parallel using multiprocessing with tqdm progress bar.
    """
    df = pd.read_csv(csv_file)
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters = {k: v for k, v in all_cluster_files.items() if len(v) >= 10}
    print(f"Number of valid clusters (≥ 10 files): {len(valid_clusters)}")

    for i, (label, file_list) in enumerate(list(valid_clusters.items())[:5]):
        print(f"Cluster {label} (index {i}): {len(file_list)} files")
    
    if not valid_clusters:
        print("No clusters with at least two files. Exiting.")
        return

    num_processes = min(cpu_count(),4)
    print("USING", num_processes)
    print(f"[INFO] Using {num_processes} processes")

    import random
    cluster_items = list(valid_clusters.items())
    random.shuffle(cluster_items)
    tasks = [(cluster, file_list, TH, train_ratio) for cluster, file_list in cluster_items]

    # with Pool(processes=num_processes) as pool:
    #     for _ in tqdm(pool.imap_unordered(run_yara, tasks), total=len(tasks)):
    #         pass  # Progress bar updates here

    num_processes = 3  # Adjust as needed
    success = run_with_timeout(num_processes, tasks, timeout_seconds=7200)
    if success:
        print("All tasks completed successfully.")
    else:
        print("Tasks were interrupted due to timeout.")
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
