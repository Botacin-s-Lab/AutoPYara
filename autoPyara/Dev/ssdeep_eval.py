import hashlib
import os
import time
import pandas as pd
from sklearn.cluster import DBSCAN
import ssdeep
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import Literal
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing

NoiseLabelling = Literal['Zeros', 'Ascending']

def verify_ssdeep_module():
    """Verify that the ssdeep module has required methods."""
    if not hasattr(ssdeep, 'hash') or not hasattr(ssdeep, 'compare'):
        raise ImportError("The 'ssdeep' module is missing required methods.")

def get_files_from_csv(csv_path="path.csv", max_files=100):
    """Retrieve up to max_files file paths from a CSV file."""
    if not os.path.isfile(csv_path):
        raise ValueError(f"'{csv_path}' is not a valid file.")
    
    df = pd.read_csv(csv_path)
    if 'File_Name' not in df.columns or 'Full_Path' not in df.columns:
        raise ValueError("CSV must contain 'File_name' and 'FilePath' columns")
    
  
    # Define the original and Docker mount paths
    host_path = "/mnt/data_disk1/mabon/datacopy"
    docker_path = "/usr/src/app/datacopy"
    df['Full_Path'] = df['Full_Path'].str.replace(host_path, docker_path, regex=False)

    file_paths = df['Full_Path'].tolist()
    file_names = df['File_Name'].tolist()   
    # Verify files exist
    valid_paths = [path for path in file_paths if os.path.isfile(path)]
    if len(valid_paths) < 2:
        raise ValueError("At least two valid files required for clustering.")
    
    if len(valid_paths) > max_files:
        valid_paths = valid_paths[:max_files]
    
    return valid_paths

def hash_file(file_path):
    """Compute SSDEEP and SHA256 hashes for a single file."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            return file_path, ssdeep.hash(content), hashlib.sha256(content).hexdigest()
    except Exception:
        return file_path, None, None

def load_or_compute_hashes(file_paths, cache_file="hash_cache.json", num_cores=None):
    """Load cached hashes or compute them in parallel."""
    if num_cores is None:
        num_cores = multiprocessing.cpu_count()
    else:
        num_cores = min(num_cores, multiprocessing.cpu_count(), 64)
    print("USING",num_cores)
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
            cached_hashes = cached_data.get('ssdeep', {})
            cached_sha256 = cached_data.get('sha256', {})
    else:
        cached_hashes = {}
        cached_sha256 = {}

    hashes = {}
    sha256_hashes = {}
    files_to_hash = [f for f in file_paths if f not in cached_hashes]

    if files_to_hash:
        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            results = list(tqdm(executor.map(hash_file, files_to_hash), total=len(files_to_hash), 
                                desc="Hashing files", unit="file", leave=False))
        
        for file_path, ssdeep_hash, sha256_hash in results:
            if ssdeep_hash and sha256_hash:
                hashes[file_path] = ssdeep_hash
                sha256_hashes[file_path] = sha256_hash
        
        cached_hashes.update(hashes)
        cached_sha256.update(sha256_hashes)
        with open(cache_file, 'w') as f:
            json.dump({'ssdeep': cached_hashes, 'sha256': sha256_hashes}, f)

    hashes.update({f: cached_hashes[f] for f in file_paths if f in cached_hashes})
    sha256_hashes.update({f: cached_sha256[f] for f in file_paths if f in cached_sha256})
    
    return hashes, sha256_hashes

def compute_distance_matrix(file_paths, hashes):
    """Compute pairwise distance matrix efficiently."""
    n_files = len(file_paths)
    distance_matrix = np.zeros((n_files, n_files), dtype=np.float32)

    total_comparisons = (n_files * (n_files - 1)) // 2
    with tqdm(total=total_comparisons, desc="Computing distances", unit="comparison", leave=False) as pbar:
        for i in range(n_files):
            for j in range(i + 1, n_files):
                similarity = ssdeep.compare(hashes[file_paths[i]], hashes[file_paths[j]]) / 100.0
                distance = 1 - similarity
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance
                pbar.update(1)

    return distance_matrix

def save_cluster_info(file_paths, labels, threshold, csv_name, output_dir, sha256_hashes,hashes):
    """Save cluster assignments to a CSV file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    data = {
        'File_Path': file_paths,
        'SHA256': [sha256_hashes[file] for file in file_paths],
        'SSDeep': [hashes[file] for file in file_paths],
        'Cluster_Label': labels,
        'Threshold': [threshold] * len(file_paths)
    }
    df = pd.DataFrame(data)
    
    csv_path = os.path.join(output_dir, f"cluster_results_{csv_name}_threshold_{threshold}_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(csv_path, index=False)

def cluster_with_threshold(file_paths, hashes, similarity_threshold, min_samples=2, noise_labeling: NoiseLabelling = 'Ascending', max_clusters=None):
    """Cluster files using DBSCAN with a given similarity threshold."""
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
                raise ValueError(f"Invalid noise_labeling: {noise_labeling}")
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

def plot_clusters(file_paths, labels, similarity_threshold, csv_name, output_dir):
    """Generate and save a histogram of cluster sizes."""
    cluster_sizes = {label: labels.count(label) for label in set(labels) if label >= 0}
    
    if not cluster_sizes:
        return

    sizes = list(cluster_sizes.values())
    plt.figure(figsize=(10, 6))
    plt.hist(sizes, bins=range(min(sizes), max(sizes) + 2), align='left', rwidth=0.8, color='skyblue', edgecolor='black')
    plt.xlabel("Cluster Size")
    plt.ylabel("Frequency")
    plt.title(f"Threshold {similarity_threshold}% - {csv_name}")
    plt.grid(True, alpha=0.3)
    plot_path = os.path.join(output_dir, f"cluster_histogram_threshold_{similarity_threshold}_{time.strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(plot_path)
    plt.close()

def run_with_varying_thresholds(csv_path="path.csv", output_dir="cluster_output", thresholds=[50, 60, 70, 80, 90], min_samples=2, noise_labeling: NoiseLabelling = 'Ascending', max_files=100, max_clusters=None, num_cores=None):
    """Run clustering with multiple thresholds, minimal output."""
    verify_ssdeep_module()
    file_paths = get_files_from_csv(csv_path, max_files=max_files)
    csv_name = os.path.splitext(os.path.basename(csv_path))[0]

    print(f"Processing {csv_path} with {len(file_paths)} files")
    hashes, sha256_hashes = load_or_compute_hashes(file_paths, num_cores=num_cores)

    for threshold in tqdm(thresholds, desc="Clustering", unit="threshold"):
        labels = cluster_with_threshold(file_paths, hashes, threshold, min_samples, noise_labeling, max_clusters)
        save_cluster_info(file_paths, labels, threshold, csv_name, output_dir, sha256_hashes,hashes)
        plot_clusters(file_paths, labels, threshold, csv_name, output_dir)

    print(f"Output saved in {output_dir}")

if __name__ == "__main__":
    csv_path = "/usr/src/app/Dev/output/merged_csv.csv"
    output_dir = "newtest/"
    run_with_varying_thresholds(csv_path, output_dir=output_dir, thresholds=[50], 
                                min_samples=2, noise_labeling='Ascending', max_files=50, num_cores=16)