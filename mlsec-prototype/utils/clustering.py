import os
import ssdeep
import numpy as np
from sklearn.cluster import DBSCAN

def cluster_files_LSH(directory, similarity_threshold=80, min_samples=2):
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

from collections import defaultdict

def cluster_samples_by_yara(yara_matches):
    # Step 1: Group samples by the set of rules they match
    rule_to_samples = defaultdict(list)

    for sample, rules in yara_matches.items():
        # Convert the list of rules to a frozenset (immutable set) for proper comparison
        rule_set = frozenset(rules)
        rule_to_samples[rule_set].append(sample)

    # Step 2: Assign a cluster ID to each set of rules and cluster the samples
    clusters = {}
    cluster_id = 0
    for rule_set, samples in rule_to_samples.items():
        # Assign a unique cluster ID to this set of rules
        for sample in samples:
            clusters[sample] = cluster_id
        cluster_id += 1

    # Step 3: Group samples by their cluster IDs
    cluster_dict = defaultdict(list)
    for sample, cluster_id in clusters.items():
        cluster_dict[cluster_id].append(sample)

    return cluster_dict
