from sklearn.cluster import DBSCAN
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import Literal
import subprocess
import pandas as pd
import hashlib
import time
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import tempfile

NoiseLabelling = Literal['Zeros', 'Ascending']

def verify_sdhash_installed():
    """Verify that sdhash is installed and accessible."""
    try:
        subprocess.run(['sdhash', '--version'], capture_output=True, text=True)
    except FileNotFoundError:
        raise ImportError("sdhash is not installed or not found in PATH. "
                          "Please install it (e.g., 'apt-get install sdhash' or from source).")

def get_files_from_csv(folder_path="/usr/src/app/sdhashdata", csv_path="path.csv", max_files=100):
    """Retrieve up to max_files file paths from a CSV file or folder, with path mapping."""
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if 'File_Name' not in df.columns or 'Full_Path' not in df.columns:
            raise ValueError("CSV must contain 'File_Name' and 'Full_Path' columns")
        
        host_path = "/mnt/data_disk1/mabon/datacopy"
        docker_path = "/usr/src/app/datacopy"
        df['Full_Path'] = df['Full_Path'].str.replace(host_path, docker_path, regex=False)

        file_paths = df['Full_Path'].tolist()
    else:
        if not os.path.isdir(folder_path):
            raise ValueError(f"'{folder_path}' is not a valid directory.")
        file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                      if os.path.isfile(os.path.join(folder_path, f))]

    valid_paths = [path for path in file_paths if os.path.isfile(path)]
    if len(valid_paths) < 2:
        raise ValueError("At least two valid files required for clustering.")
    if len(valid_paths) > max_files:
        valid_paths = valid_paths[:max_files]
        
    return valid_paths

def hash_file(file_path):
    """Compute sdhash similarity digest and SHA256 hash for a single file."""
    try:
        result = subprocess.run(["sdhash", file_path], check=True, capture_output=True, text=True)
        sdhash_output = result.stdout.strip()
        if not sdhash_output:
            return file_path, None, None
        
        with open(file_path, 'rb') as f:
            content = f.read()
            if not content:
                return file_path, None, None
            sha256_hash = hashlib.sha256(content).hexdigest()
        return file_path, sdhash_output, sha256_hash
    except subprocess.CalledProcessError:
        return file_path, None, None

def load_or_compute_hashes(file_paths, cache_file="hash_cache_sdhash.json", num_cores=None):
    """Load cached hashes or compute them in parallel."""
    num_cores = min(num_cores or multiprocessing.cpu_count(), multiprocessing.cpu_count(), 64)

    cached_hashes = {}
    cached_sha256 = {}
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
            cached_hashes = cached_data.get('sdhash', {})
            cached_sha256 = cached_data.get('sha256', {})

    hashes = {}
    sha256_hashes = {}
    files_to_hash = [f for f in file_paths if f not in cached_hashes]

    if files_to_hash:
        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            results = list(tqdm(executor.map(hash_file, files_to_hash), total=len(files_to_hash), 
                               desc="Hashing files", unit="file"))
        
        for file_path, sdhash_hash, sha256_hash in results:
            if sdhash_hash and sha256_hash:
                hashes[file_path] = sdhash_hash
                sha256_hashes[file_path] = sha256_hash
        
        cached_hashes.update(hashes)
        cached_sha256.update(sha256_hashes)
        with open(cache_file, 'w') as f:
            json.dump({'sdhash': cached_hashes, 'sha256': cached_sha256}, f)

    hashes.update({f: cached_hashes[f] for f in file_paths if f in cached_hashes})
    sha256_hashes.update({f: cached_sha256[f] for f in file_paths if f in cached_sha256})
    
    return hashes, sha256_hashes

def compute_pair(args):
    """Helper function to compute distance for a pair of files."""
    i, j, file_paths, hashes = args
    
    try:
        if not hashes[file_paths[i]] or not hashes[file_paths[j]]:
            return i, j, 1.0
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sdbf', delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode='w', suffix='.sdbf', delete=False) as f2:
            f1.write(hashes[file_paths[i]])
            f2.write(hashes[file_paths[j]])
            temp_file_i, temp_file_j = f1.name, f2.name
        
        result = subprocess.run(
            ["sdhash", "-c", temp_file_i, temp_file_j],
            check=True, capture_output=True, text=True
        )
        output = result.stdout.strip()
        
        if output:
            similarity = float(output.split('|')[3])
            similarity = max(0.0, min(1.0, similarity))
            distance = 1 - similarity
        else:
            distance = 1.0
        
        if distance < 0:
            distance = 0.0
        
        return i, j, distance
    
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return i, j, 1.0
    finally:
        for temp_file in [temp_file_i, temp_file_j]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

def compute_distance_matrix(file_paths, hashes, max_workers=32):
    """Compute distance matrix for given file paths and hashes."""
    n_files = len(file_paths)
    distance_matrix = np.zeros((n_files, n_files), dtype=np.float32)
    
    pairs = [(i, j, file_paths, hashes) 
             for i in range(n_files) 
             for j in range(i + 1, n_files)]
    
    total_comparisons = len(pairs)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        with tqdm(total=total_comparisons, desc="Computing distances", unit="comparison") as pbar:
            results = executor.map(compute_pair, pairs)
            for i, j, distance in results:
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance
                pbar.update(1)
    
    min_distance = np.min(distance_matrix)
    if min_distance < 0:
        distance_matrix = np.clip(distance_matrix, 0, None)
    
    return distance_matrix

def cluster_with_threshold(file_paths, hashes, similarity_threshold, min_samples=2, 
                         noise_labeling: NoiseLabelling = 'Ascending', max_clusters=None):
    """Cluster files using DBSCAN with a given similarity threshold, limiting to max_clusters."""
    if similarity_threshold >= 100:
        similarity_threshold = 99.9

    distance_matrix = compute_distance_matrix(file_paths, hashes)
    eps = 1 - (similarity_threshold / 100.0)
    db = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = db.fit_predict(distance_matrix)

    path_to_cluster = {}
    noise_cluster = max(labels) + 1 if max(labels) >= 0 else 0

    for idx, (file, label) in enumerate(zip(file_paths, labels)):
        if label == -1:
            if noise_labeling == "Zeros":
                transformed_cluster_num = 0
            elif noise_labeling == "Ascending":
                transformed_cluster_num = noise_cluster
                noise_cluster += 1
            else:
                raise ValueError(f"Invalid noise_labeling format: {noise_labeling}")
        else:
            transformed_cluster_num = label
        path_to_cluster[file] = transformed_cluster_num

    if max_clusters is not None:
        cluster_sizes = {}
        for label in path_to_cluster.values():
            cluster_sizes[label] = cluster_sizes.get(label, 0) + 1
        
        if noise_labeling == "Zeros" and 0 in cluster_sizes:
            del cluster_sizes[0]
        sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_clusters) > max_clusters:
            allowed_clusters = set(c[0] for c in sorted_clusters[:max_clusters])
            for file in path_to_cluster:
                if path_to_cluster[file] not in allowed_clusters:
                    path_to_cluster[file] = -1

    return [path_to_cluster[file] for file in file_paths]

def plot_clusters(file_paths, labels, similarity_threshold, folder_name):
    """Generate a histogram of cluster sizes."""
    cluster_sizes = {}
    for label in labels:
        if label >= 0:
            cluster_sizes[label] = cluster_sizes.get(label, 0) + 1
    
    if not cluster_sizes:
        return

    sizes = list(cluster_sizes.values())
    n_clusters = len(sizes)
    n_noise = labels.count(-1)

    plt.figure(figsize=(10, 6))
    plt.hist(sizes, bins=range(min(sizes), max(sizes) + 2), align='left', rwidth=0.8, 
             color='skyblue', edgecolor='black')
    plt.xlabel("Cluster Size (Number of Files)")
    plt.ylabel("Frequency (Number of Clusters)")
    plt.title(f"Cluster Size Distribution at Similarity Threshold {similarity_threshold}%\n"
              f"Folder: {folder_name} | Clusters: {n_clusters} | Noise: {n_noise}")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"cluster_histogram_threshold_{similarity_threshold}.png")
    plt.close()

def save_cluster_info(file_paths, labels, threshold, folder_name, output_dir, sha256_hashes, hashes):
    """Save cluster assignments to a CSV file, including sdhash values."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    data = {
        'File_Path': file_paths,
        'SHA256': [sha256_hashes[file] for file in file_paths],
        'SDHash': [hashes[file] for file in file_paths],  # Add sdhash values
        'Cluster_Label': labels,
        'Threshold': [threshold] * len(file_paths)
    }
    df = pd.DataFrame(data)
    
    csv_path = os.path.join(output_dir, f"cluster_results_{folder_name}_threshold_{threshold}_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved cluster results to {csv_path}")

def run_with_varying_thresholds(folder_path="/usr/src/app/sdhashdata", csv_path="path.csv", 
                              output_dir="cluster_output", thresholds=[50, 60, 70, 80, 90], 
                              min_samples=2, noise_labeling: NoiseLabelling = 'Ascending', 
                              max_files=100, max_clusters=None, num_cores=None):
    """Run clustering with multiple thresholds and plot results with progress bar, limiting clusters."""
    verify_sdhash_installed()
    file_paths = get_files_from_csv(folder_path, csv_path, max_files=max_files)
    folder_name = os.path.basename(folder_path)

    hashes, sha256_hashes = load_or_compute_hashes(file_paths, num_cores=num_cores)

    for threshold in tqdm(thresholds, desc="Clustering thresholds", unit="threshold"):
        labels = cluster_with_threshold(file_paths, hashes, threshold, min_samples, 
                                      noise_labeling, max_clusters)
        #plot_clusters(file_paths, labels, threshold, folder_name)
        save_cluster_info(file_paths, labels, threshold, folder_name, output_dir, sha256_hashes, hashes)

if __name__ == "__main__":
    folder_path = ""
    csv_path = "/usr/src/app/Dev/output/merged_csv.csv"
    output_dir = "cluster_output/sdhash/test"
    run_with_varying_thresholds(folder_path, csv_path, output_dir, thresholds=[10], 
                              min_samples=2, noise_labeling='Ascending', max_files=1000, 
                              max_clusters=None, num_cores=64)