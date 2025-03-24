from utils.clustering import *
from utils.matching import *
from utils.evaluation import *

# Directory containing malware files
directory = "/tmp/malware/"

# Cluster samples with a similarity threshold of 80% and a minimum of 2 samples per cluster
s_clusters = cluster_files_LSH(directory, similarity_threshold=80, min_samples=2)

print(s_clusters)

# Define YARA rules as strings
yara_rules = [
    """
    rule TestRule1 {
        strings:
            $a = "a"
        condition:
            $a
    }
    """,
    """
    rule TestRule2 {
        strings:
            $b = "b"
        condition:
            $b
    }
    """
]

# Test the YARA rules
matches = match_yara_rule(yara_rules, directory)
print(matches)

y_clusters = cluster_samples_by_yara(matches)
print(y_clusters)

global_accuracy, cluster_accuracies = evaluate_clustering(s_clusters, y_clusters)

print(f"Global Clustering Accuracy: {global_accuracy}%")
print("Cluster-by-cluster Accuracy:")
for cluster_id, accuracies in cluster_accuracies.items():
    print(f"SSDeep Cluster {cluster_id}:")
    print(f"    Correct samples: {accuracies['correct_samples']}/{accuracies['total_samples']} - Accuracy with extras: {accuracies['accuracy_with_extras']:.2f}%")
    print(f"    Extra samples in YARA: {accuracies['extra_samples_in_yara']}")
    print(f"    Accuracy without extras: {accuracies['accuracy_without_extras']:.2f}%")

