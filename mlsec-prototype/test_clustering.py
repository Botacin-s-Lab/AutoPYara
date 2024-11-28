from utils.clustering import *

# Directory containing malware files
directory = "/tmp/malware/"

# Cluster samples with a similarity threshold of 80% and a minimum of 2 samples per cluster
clusters = cluster_malware_samples_LSH(directory, similarity_threshold=80, min_samples=2)

# Display the results
for cluster_id, files in clusters.items():
    if cluster_id == -1:
        print("Noise files (not clustered):")
    else:
        print(f"Cluster {cluster_id}:")
    for file in files:
        print(f"  {file}")
