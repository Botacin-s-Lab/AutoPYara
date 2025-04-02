def evaluate_clustering(ssdeep_clusters, yara_clusters):
    # Reverse the yara_clusters to map samples to their YARA cluster IDs
    sample_to_yara_cluster = {}
    for cluster_id, samples in yara_clusters.items():
        for sample in samples:
            sample_to_yara_cluster[sample] = cluster_id

    correct_samples_global = 0
    total_samples_global = 0
    cluster_accuracies = {}

    # Iterate through each SSDeep cluster
    for ssdeep_cluster_id, ssdeep_samples in ssdeep_clusters.items():
        correct_samples_in_cluster = 0
        incorrect_samples_in_yara = 0

        # Track which YARA clusters the SSDeep samples belong to
        yara_clusters_for_ssdeep_samples = []
        
        for sample in ssdeep_samples:
            if sample in sample_to_yara_cluster:
                yara_clusters_for_ssdeep_samples.append(sample_to_yara_cluster[sample])

        # If all samples belong to the same YARA cluster
        yara_cluster_set = set(yara_clusters_for_ssdeep_samples)
        
        # Metric 1: Check if all samples belong to the same YARA cluster
        if len(yara_cluster_set) == 1:
            correct_samples_in_cluster = len(ssdeep_samples)
            cluster_accuracy = 100  # All samples in the SSDeep cluster are correctly matched
        else:
            correct_samples_in_cluster = len(yara_cluster_set)  # Correct samples are those in the correct yara clusters
            cluster_accuracy = (correct_samples_in_cluster / len(ssdeep_samples)) * 100  # Metric 1

        # Metric 2: Check for extra samples in YARA clusters
        yara_samples_in_cluster = set()
        for yara_cluster_id in yara_cluster_set:
            yara_samples_in_cluster.update(yara_clusters[yara_cluster_id])

        # Metric 2: Extra samples that don't belong to SSDeep cluster
        extra_samples = yara_samples_in_cluster - set(ssdeep_samples)
        incorrect_samples_in_yara = len(extra_samples)

        # Update the cluster accuracy results
        cluster_accuracies[ssdeep_cluster_id] = {
            "correct_samples": correct_samples_in_cluster,
            "total_samples": len(ssdeep_samples),
            "accuracy_with_extras": cluster_accuracy,
            "extra_samples_in_yara": incorrect_samples_in_yara,
            "accuracy_without_extras": (correct_samples_in_cluster / (len(ssdeep_samples) + incorrect_samples_in_yara)) * 100 if len(ssdeep_samples) + incorrect_samples_in_yara > 0 else 0
        }

        # Update global counters
        correct_samples_global += correct_samples_in_cluster
        total_samples_global += len(ssdeep_samples)

    # Calculate the global accuracy
    global_accuracy = (correct_samples_global / total_samples_global) * 100 if total_samples_global > 0 else 0

    return global_accuracy, cluster_accuracies
