import os
import sys
import shutil
import argparse
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
import ssdeep

def read_binary_file(file_path, max_size=1024 * 1024):
    """Safely read binary file with size limit"""
    try:
        with open(file_path, 'rb') as f:
            return f.read(max_size)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def progress_bar(current, total, bar_length=50):
    fraction = current / total
    filled = int(fraction * bar_length)
    bar = '█' * filled + '-' * (bar_length - filled)
    percent = int(fraction * 100)
    sys.stdout.write(f'\rProgress: |{bar}| {percent}% ({current}/{total})')
    sys.stdout.flush()

def DBSCAN_Cluster(file_paths, similarity_threshold=80, min_samples=2):
    n_files = len(file_paths)

    if n_files < 2:
        raise ValueError("The directory must contain at least two files to perform clustering.")

    # Compute ssdeep hashes for all files
    hashes = {file: ssdeep.hash_from_file(file) for file in file_paths}

    # Build the pairwise distance matrix
    distance_matrix = np.zeros((n_files, n_files))

    for i in range(n_files):
        for j in range(i + 1, n_files):
            similarity = ssdeep.compare(hashes[file_paths[i]], hashes[file_paths[j]]) / 100.0
            distance = 1 - similarity
            distance_matrix[i, j] = distance
            distance_matrix[j, i] = distance  # Symmetric matrix

    # Configure DBSCAN
    eps = 1 - (similarity_threshold / 100.0)
    db = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = db.fit_predict(distance_matrix)

    # Group files by cluster
    clusters = {}
    for file, label in zip(file_paths, labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(file)

    return clusters

def cluster_files(input_dir, output_dir, similarity_threshold=80, min_samples=2, max_files=100000):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=False)

    # Collect all exe files
    exe_files = []

    print("Reading files...")

    current_files = 0
    for file_path in Path(input_dir).glob('*'):
        content = read_binary_file(str(file_path))
        if content:
            exe_files.append(str(file_path))
            current_files += 1

            if current_files % 1000 == 0:
                print(f"Read {current_files} files!")
            if current_files >= max_files:
                break

    if not exe_files:
        print("No .exe files found in input directory")
        return

    print(f"Read {len(exe_files)} files...")

    print(f"Begin DBSCAN clustering")
    clusters = DBSCAN_Cluster(exe_files, similarity_threshold, min_samples)
    print(f"DBSCAN clustering complete!")

    print(f"Sorting and reassigning clusters...")
    # Create a list of (cluster_id, paths) tuples, excluding noise (-1)
    # Note that cluster -1 for Noise is dropped
    sorted_clusters = [(cid, paths) for cid, paths in clusters.items() if cid == -1]
    # Sort by cluster size in descending order
    sorted_clusters.sort(key=lambda x: len(x[1]), reverse=True)

    # Create new clusters dictionary with reassigned IDs
    new_clusters = {}
    for new_id, (_, paths) in enumerate(sorted_clusters):
        new_clusters[new_id] = paths

    print(f"Assigning clusters...")
    # Create clusters and copy files
    for cluster_id, paths in new_clusters.items():
        cluster_dir = os.path.join(
            output_dir,
            f"Cluster{cluster_id}_Size{len(paths)}"
        )
        os.makedirs(cluster_dir, exist_ok=False)

        # Copy files to cluster directory
        for path in paths:
            dst_path = os.path.join(
                cluster_dir,
                os.path.basename(path)
            )
            try:
                shutil.copy2(path, dst_path)
            except Exception as e:
                print(f"Error copying {path}: {e}")

    print("Clustering complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Cluster malware files using DBSCAN'
    )
    parser.add_argument(
        '--input-dir',
        required=True,
        help='Directory containing .exe files'
    )
    parser.add_argument(
        '--output-dir',
        required=True,
        help='Directory to store clustered files'
    )
    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=80,
        help='DBSCAN eps parameter (0-1)'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=2,
        help='Minimum samples to form a cluster'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        default=100000,
        help='Process this many files, then quit'
    )

    args = parser.parse_args()

    cluster_files(
        args.input_dir,
        args.output_dir,
        args.similarity_threshold,
        args.min_samples,
        args.max_files
    )

if __name__ == "__main__":
    main()