from sklearn.cluster import DBSCAN
import ssdeep
import sys, os
from typing import Literal
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocessing import java_to_python_paths

# noise labeling:
# Zeroes: samples not grouped by DBSCAN
NoiseLabelling = Literal['Zeros', 'Ascending']

class AugmentedDBScan():
    def __init__(self, epsilon=0.5, min_samples=5, dbscan_threshold=90, augmented_target_k=None, noise_labeling: NoiseLabelling = 'Ascending'):
        self.epsilon = epsilon
        self.min_samples = min_samples
        self.noise_labeling = noise_labeling
        self.dbscan_threshold = dbscan_threshold

        print(augmented_target_k)
        assert (not augmented_target_k or augmented_target_k >= 2), f"augmented_target_k must be >= 2!"
        self.augmented_target_k = augmented_target_k

    def DBSCAN_Cluster(self, file_paths, similarity_threshold=80, min_samples=2):
        n_files = len(file_paths)

        if n_files < 2:
            raise ValueError("The directory must contain at least two files to perform clustering.")

        if similarity_threshold >= 100:
            similarity_threshold = 99.9 # at large similarity thresholds, approximate

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

    def direct_predict(self, file_paths, final_prediction=True):
        file_paths = java_to_python_paths(file_paths)

        # print("predicting", file_paths)
        clusters = self.DBSCAN_Cluster(
            file_paths,
            similarity_threshold=self.dbscan_threshold,
            min_samples=2,
        )
        if final_prediction:
            for key, value in clusters.items():
                print("cluster", key, value)

        path_to_cluster = {}

        noise_cluster = len(clusters.keys())-1
        for cluster_num, paths in clusters.items():
            # Map each path to its transformed cluster number
            for path in paths:
                if cluster_num == -1: # DBSCAN could not put this into a cluster, we give it its own cluster
                    if self.noise_labeling == "Zeros":
                        transformed_cluster_num = noise_cluster
                    elif self.noise_labeling == "Ascending":
                        transformed_cluster_num = noise_cluster
                        noise_cluster += 1
                    else:
                        raise ValueError(f"invalid noise_labeling format: {self.noise_labeling}")
                else:
                    transformed_cluster_num = cluster_num

                path_to_cluster[path] = transformed_cluster_num

        # Create the predictor_labels list in the same order as file_paths
        predictor_labels = [path_to_cluster[path] for path in file_paths]

        if final_prediction:
            print("predictor labels", predictor_labels)

        return predictor_labels

    def predict(self, file_paths):
        """
        Find optimal clustering parameters using a gradient-like approach to get
        a number of clusters closest to augmented_target_k.
        """
        if self.augmented_target_k is None:
            return self.direct_predict(file_paths)

        # Initial parameters
        current_threshold = 50
        learning_rate = 15.0  # How much to adjust threshold each step
        max_iterations = 20
        tolerance = 0.5  # Stop if we're this close to the target

        largest_error = 99999
        best_threshold = current_threshold
        best_clusters = 0

        for iteration in range(max_iterations):
            # Get current clustering
            self.dbscan_threshold = current_threshold
            labels = self.direct_predict(file_paths, final_prediction=False)
            current_clusters = len(set(labels))

            # Calculate error (distance from target)
            error = current_clusters - self.augmented_target_k

            # Check if we're close enough
            if abs(error) <= tolerance:
                best_threshold = current_threshold
                best_clusters = current_clusters
                break

            if abs(error) < largest_error:
                largest_error = abs(error)
                best_threshold = current_threshold
                best_clusters = current_clusters

                # Calculate direction and step
            # If we have too many clusters, decrease threshold (makes DBSCAN more strict)
            # If we have too few clusters, increase threshold (makes DBSCAN less strict)
            direction = -1 if error > 0 else 1

            # Adjust learning rate based on how far we are from the target
            adaptive_rate = learning_rate * (1.0 / (iteration + 1))

            # Update threshold
            current_threshold += direction * adaptive_rate

            # Ensure threshold stays in valid range
            current_threshold = max(30, min(99, current_threshold))

            print(
                f"Iteration {iteration}: Threshold={current_threshold:.2f}, Clusters={current_clusters}, Target={self.augmented_target_k}")

        # Set final threshold and return labels
        print(f"Iteration final: Threshold={best_threshold:.2f}, Clusters={best_clusters}, Target={self.augmented_target_k}")
        self.dbscan_threshold = best_threshold
        return self.direct_predict(file_paths)