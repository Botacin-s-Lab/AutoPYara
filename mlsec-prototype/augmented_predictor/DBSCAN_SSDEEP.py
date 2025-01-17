from sklearn.cluster import DBSCAN
import ssdeep
import sys, os
from typing import Literal
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocessing import java_to_python_paths

# noise labeling:
# Zeroes: samples not grouped by DBSCAN
NoiseLabelling = Literal['Zeroes', 'Ascending']

class AugmentedDBScan():
    def __init__(self, epsilon=0.5, min_samples=5):
        self.epsilon = epsilon
        self.min_samples = min_samples

    def DBSCAN_Cluster(self, file_paths, similarity_threshold=80, min_samples=2):
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

    def predict(self, file_paths):
        file_paths = java_to_python_paths(file_paths)

        print("predicting", file_paths)
        clusters = self.DBSCAN_Cluster(
            file_paths,
            similarity_threshold=30,
            min_samples=2,
        )
        print("clusters", clusters)
        for key, value in clusters.items():
            print("cluster", key, value)

        path_to_cluster = {}
        for cluster_num, paths in clusters.items():
            # Transform -1 to 0 and shift other numbers up by 1
            transformed_cluster_num = 0 if cluster_num == -1 else cluster_num + 1

            # Map each path to its transformed cluster number
            for path in paths:
                path_to_cluster[path] = transformed_cluster_num

        # Create the predictor_labels list in the same order as file_paths
        predictor_labels = [path_to_cluster[path] for path in file_paths]
        print("predictor labels", predictor_labels)

        return predictor_labels