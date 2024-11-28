import os
import ssdeep
import numpy as np
from sklearn.cluster import DBSCAN

def cluster_malware_samples_LSH(directory, similarity_threshold=80, min_samples=2):
    # List all files in the directory
    file_paths = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
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
