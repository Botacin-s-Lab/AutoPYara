from sklearn.cluster import DBSCAN
import ssdeep
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import Literal

NoiseLabelling = Literal['Zeros', 'Ascending']

def verify_ssdeep_module():
    """Verify that the ssdeep module has required methods."""
    print(f"ssdeep module path: {ssdeep.__file__}")
    print(f"ssdeep attributes: {dir(ssdeep)}")
    if not hasattr(ssdeep, 'hash') or not hasattr(ssdeep, 'compare'):
        raise ImportError("The 'ssdeep' module is missing 'hash' or 'compare'. "
                          "Ensure 'pydeep' is installed (pip install ssdeep) and no naming conflicts exist.")

def get_files_from_folder(folder_path, max_files=100):
    """Retrieve up to max_files file paths from a folder."""
    if not os.path.isdir(folder_path):
        raise ValueError(f"'{folder_path}' is not a valid directory.")
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                  if os.path.isfile(os.path.join(folder_path, f))]
    if len(file_paths) < 2:
        raise ValueError("The folder must contain at least two files to perform clustering.")
    if len(file_paths) > max_files:
        print(f"Folder has {len(file_paths)} files; limiting to {max_files} for testing.")
        file_paths = file_paths[:max_files]
    return file_paths

def compute_distance_matrix(file_paths):
    """Compute pairwise distance matrix using ssdeep with progress bar."""
    n_files = len(file_paths)
    hashes = {}
    
    for file in tqdm(file_paths, desc="Hashing files", unit="file", disable=n_files < 50):
        try:
            with open(file, 'rb') as f:
                content = f.read()
                hashes[file] = ssdeep.hash(content)
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            raise

    distance_matrix = np.zeros((n_files, n_files), dtype=np.float32)

    total_comparisons = (n_files * (n_files - 1)) // 2
    with tqdm(total=total_comparisons, desc="Computing distances", unit="comparison", disable=n_files < 50) as pbar:
        for i in range(n_files):
            for j in range(i + 1, n_files):
                similarity = ssdeep.compare(hashes[file_paths[i]], hashes[file_paths[j]]) / 100.0
                distance = 1 - similarity
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance
                pbar.update(1)

    return distance_matrix

def cluster_with_threshold(file_paths, similarity_threshold, min_samples=2, noise_labeling: NoiseLabelling = 'Ascending', max_clusters=None):
    """Cluster files using DBSCAN with a given similarity threshold, limiting to max_clusters."""
    if similarity_threshold >= 100:
        similarity_threshold = 99.9

    distance_matrix = compute_distance_matrix(file_paths)
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
    # Get cluster sizes (exclude noise, i.e., -1)
    cluster_sizes = {}
    for label in labels:
        if label >= 0:  # Only count actual clusters
            cluster_sizes[label] = cluster_sizes.get(label, 0) + 1
    
    if not cluster_sizes:
        print(f"No clusters found at threshold {similarity_threshold}%, skipping plot.")
        return

    # Prepare data for histogram
    sizes = list(cluster_sizes.values())  # List of cluster sizes
    n_clusters = len(sizes)
    n_noise = labels.count(-1)

    plt.figure(figsize=(10, 6))
    plt.hist(sizes, bins=range(min(sizes), max(sizes) + 2), align='left', rwidth=0.8, color='skyblue', edgecolor='black')
    plt.xlabel("Cluster Size (Number of Files)")
    plt.ylabel("Frequency (Number of Clusters)")
    plt.title(f"Cluster Size Distribution at Similarity Threshold {similarity_threshold}%\n"
              f"Folder: {folder_name} | Clusters: {n_clusters} | Noise: {n_noise}")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"cluster_histogram_threshold_{similarity_threshold}.png")
    plt.close()

def run_with_varying_thresholds(folder_path, thresholds=[50, 60, 70, 80, 90], min_samples=2, noise_labeling: NoiseLabelling = 'Ascending', max_files=100, max_clusters=None):
    """Run clustering with multiple thresholds and plot results with progress bar, limiting clusters."""
    verify_ssdeep_module()
    file_paths = get_files_from_folder(folder_path, max_files=max_files)
    folder_name = os.path.basename(folder_path)

    print(f"Processing folder: {folder_path}")
    print(f"Using {len(file_paths)} files.")
    if max_clusters is not None:
        print(f"Limiting to a maximum of {max_clusters} clusters.")

    for threshold in tqdm(thresholds, desc="Clustering thresholds", unit="threshold"):
        print(f"\nClustering with similarity threshold: {threshold}%")
        labels = cluster_with_threshold(file_paths, threshold, min_samples, noise_labeling, max_clusters)

        unique_labels = set(labels)
        print(f"Number of clusters: {len([l for l in unique_labels if l >= 0])}")
        if len(file_paths) > 10:
            print(f"Clusters (showing summary due to large number of files):")
            for label in sorted(unique_labels):
                cluster_size = sum(1 for lbl in labels if lbl == label)
                if label >= 0:
                    print(f"Cluster {label}: {cluster_size} files")
                elif label == -1:
                    print(f"Noise: {cluster_size} files")
        else:
            for label in unique_labels:
                cluster_files = [file_paths[i] for i, lbl in enumerate(labels) if lbl == label]
                print(f"Cluster {label}: {len(cluster_files)} files - {cluster_files}")

        plot_clusters(file_paths, labels, threshold, folder_name)

    print("\nPlots saved as PNG files in the current directory.")


if __name__ == "__main__":
    folder_path = "/usr/src/app/ssdeepdata"  # Replace with your folder path
    run_with_varying_thresholds(folder_path, thresholds=[50, 60, 70, 80, 90], min_samples=2, noise_labeling='Ascending', max_files=2000, max_clusters=3)
