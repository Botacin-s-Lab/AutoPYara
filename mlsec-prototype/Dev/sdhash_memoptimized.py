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
from sklearn.cluster import DBSCAN

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
    return valid_paths[:max_files] if max_files else valid_paths

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

def compute_distance(file_i, file_j, hashes):
    """Compute distance between two files using sdhash."""
    if not hashes[file_i] or not hashes[file_j]:
        return 1.0
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sdbf', delete=False) as f1, \
         tempfile.NamedTemporaryFile(mode='w', suffix='.sdbf', delete=False) as f2:
        f1.write(hashes[file_i])
        f2.write(hashes[file_j])
        temp_file_i, temp_file_j = f1.name, f2.name
    
    try:
        result = subprocess.run(
            ["sdhash", "-c", temp_file_i, temp_file_j],
            check=True, capture_output=True, text=True
        )
        output = result.stdout.strip()
        if output:
            similarity = float(output.split('|')[3]) / 100.0  # Normalize to 0-1
            distance = 1 - similarity
        else:
            distance = 1.0
        return max(0.0, min(1.0, distance))
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return 1.0
    finally:
        for temp_file in [temp_file_i, temp_file_j]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

def cluster_in_batches(file_paths, hashes, similarity_threshold, min_samples=2, batch_size=500, 
                      noise_labeling: str = 'Ascending', max_clusters=None, max_workers=10, num_batch_threads=8):
    """Cluster files in batches with parallel batch processing and progress tracking."""
    if similarity_threshold >= 100:
        similarity_threshold = 99.9
    eps = 1 - (similarity_threshold / 100.0)
    
    n_files = len(file_paths)
    labels = np.full(n_files, -1, dtype=int)  # Initialize all as noise
    
    def process_batch(batch_range):
        start, end = batch_range
        batch_paths = file_paths[start:end]
        batch_hashes = {path: hashes[path] for path in batch_paths}
        n_batch = len(batch_paths)
        distance_matrix = np.zeros((n_batch, n_batch), dtype=np.float32)
        
        pairs = [(i, j, batch_paths, batch_hashes) 
                 for i in range(n_batch) 
                 for j in range(i + 1, n_batch)]
        total_pairs = len(pairs)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            with tqdm(total=total_pairs, desc=f"Computing distances (batch {start//batch_size + 1})", 
                      leave=False, position=start//batch_size + 1) as distance_pbar:
                results = executor.map(lambda args: (args[0], args[1], compute_distance(args[2][args[0]], args[2][args[1]], args[3])), pairs)
                for i, j, distance in results:
                    distance_matrix[i, j] = distance
                    distance_matrix[j, i] = distance
                    distance_pbar.update(1)
        
        db = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
        batch_labels = db.fit_predict(distance_matrix)
        return start, end, batch_labels
    
    # Parallel batch processing
    batch_ranges = [(start, min(start + batch_size, n_files)) for start in range(0, n_files, batch_size)]
    cluster_offset = 0
    
    with ThreadPoolExecutor(max_workers=num_batch_threads) as executor:
        batch_results = list(tqdm(executor.map(process_batch, batch_ranges), 
                                 total=len(batch_ranges), desc=f"Processing batches (threshold {similarity_threshold}%)"))
    
    # Combine results
    for start, end, batch_labels in batch_results:
        for i, label in enumerate(batch_labels):
            if label != -1:
                labels[start + i] = label + cluster_offset
            else:
                labels[start + i] = -1
        cluster_offset += max(0, max(batch_labels)) + 1 if batch_labels.max() >= 0 else 0

    # Post-process noise labeling and max_clusters
    path_to_cluster = {file: label for file, label in zip(file_paths, labels)}
    noise_cluster = cluster_offset if cluster_offset > 0 else 0
    
    for file in path_to_cluster:
        if path_to_cluster[file] == -1:
            if noise_labeling == "Zeros":
                path_to_cluster[file] = 0
            elif noise_labeling == "Ascending":
                path_to_cluster[file] = noise_cluster
                noise_cluster += 1
    
    if max_clusters is not None:
        cluster_sizes = {}
        for label in path_to_cluster.values():
            if label >= 0:
                cluster_sizes[label] = cluster_sizes.get(label, 0) + 1
        
        if noise_labeling == "Zeros" and 0 in cluster_sizes:
            del cluster_sizes[0]
        sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_clusters) > max_clusters:
            allowed_clusters = set(c[0] for c in sorted_clusters[:max_clusters])
            for file in path_to_cluster:
                if path_to_cluster[file] not in allowed_clusters and path_to_cluster[file] != -1:
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
        'SDHash': [hashes[file] for file in file_paths],
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
                              max_files=None, max_clusters=None, num_cores=None, batch_size=500, num_batch_threads=4):
    """Run clustering with multiple thresholds in parallel batches."""
    verify_sdhash_installed()
    file_paths = get_files_from_csv(folder_path, csv_path, max_files=max_files)
    folder_name = os.path.basename(folder_path)

    hashes, sha256_hashes = load_or_compute_hashes(file_paths, num_cores=num_cores)

    for threshold in tqdm(thresholds, desc="Clustering thresholds", unit="threshold"):
        labels = cluster_in_batches(file_paths, hashes, threshold, min_samples, batch_size, 
                                  noise_labeling, max_clusters, max_workers=16, num_batch_threads=num_batch_threads)
        # plot_clusters(file_paths, labels, threshold, folder_name)  # Uncomment if needed
        save_cluster_info(file_paths, labels, threshold, folder_name, output_dir, sha256_hashes, hashes)

if __name__ == "__main__":
    folder_path = ""
    csv_path = "/usr/src/app/Dev/output/merged_csv.csv"
    output_dir = "cluster_output/sdhash/main/"
    run_with_varying_thresholds(folder_path, csv_path, output_dir, thresholds=[ 60, 70, 75, 80, 85, 90], 
                              min_samples=2, noise_labeling='Ascending', max_files=None, 
                              max_clusters=None, num_cores=64, batch_size=1000, num_batch_threads=16)