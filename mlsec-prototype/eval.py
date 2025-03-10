
def eval_test():
    myYara = AutoPYara()

    def eval1():
        return myYara.generate(
            get_project_path("input_testing", "malicious", "mw2"),
            get_project_path("intermediate", "bloom_filters", "malicious"),
            get_project_path("intermediate", "bloom_filters", "benign"),
            output_dir=get_project_path("output", "TestOutput"),
            bicluster_alg="SpectralCoCluster",
            cluster_alg="AugmentedKMeansDBSCAN",
            output_format="string",
        )

    def eval2():
        return myYara.generate(
            get_project_path("input_testing", "malicious", "mw2"),
            get_project_path("intermediate", "bloom_filters", "malicious"),
            get_project_path("intermediate", "bloom_filters", "benign"),
            output_dir=get_project_path("output", "TestOutput"),
            bicluster_alg="SpectralCoCluster",
            cluster_alg="VBGMM",
            output_format="string",
        )

    box_plot_set = {}
    box_plot_set['VBGMM'] = extract_box_plot(eval2, count=10)
    box_plot_set['AugmentedKMeansDBSCAN'] = extract_box_plot(eval1, count=10)

def get_integer_interval(start, max, count):
    # Adjust count if there aren't enough numbers in range
    available_numbers = max - start + 1  # Count of numbers from min to max
    count = min(count, available_numbers)

    if count <= 0:
        return []

    if count == 1:
        return [start]

    # Generate evenly spaced indices
    indices = [i * (available_numbers - 1) // (count - 1) for i in range(count)]

    # Convert indices to actual numbers in range [min, max]
    result = [start + i for i in indices]

    return result

def count_files_in_directory(directory_path):
    # Using list comprehension to count only files (not directories)
    return len([f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))])

def eval_kmeans_sweep(algorithm_tries=10):
    myYara = AutoPYara()
    input_directory = get_project_path("input_testing", "malicious", "output_preprocessed")

    for dataset_series in os.listdir(input_directory):
        match = re.match(r'Cluster\d+_Size(\d+)', dataset_series)
        if match:
            size = int(match.group(1))
            if size <= 4:
                continue

        directory_path = get_project_path("input_testing", "malicious", "output_preprocessed", dataset_series)
        bloom_filter_malicious_path = "/usr/src/app/intermediate/bloom_filters/malicious-bytes/" 
        bloom_filter_benign_path = "/usr/src/app/intermediate/bloom_filters/benign-bytes/" 

        file_count = count_files_in_directory(directory_path)
        box_plot_set = {}

        loaded_box_plot = load_box_plot_data(dataset_series, container_directory="kmeans")
        if loaded_box_plot:
            print(f"already generated results for {dataset_series}! skipping experiment... updating plots...")
            # generate_fullscale_plots(loaded_box_plot, dataset_series, file_count, container_directory="kmeans")
            #box_plot_set = loaded_box_plot
            continue

        k_interval = [2, 3, 4, 5, 6, 7, 9, 12, 16, 21, 28, 35, 45, 60, 85, 120]
        if file_count not in k_interval:
            k_interval.append(file_count)
            k_interval = sorted(k_interval)

        random_k_estimate = 0
        for k in k_interval: # get the largest k possible for this file size, but also consider the set intervals
            if k <= file_count:
                random_k_estimate = k

        for k in k_interval:
            if k > file_count:
                continue

            def kmeans():
                return myYara.generate(
                    directory_path,
                    bloom_filter_malicious_path,
                    bloom_filter_benign_path,
                    bicluster_alg="SpectralCoCluster",
                    cluster_alg="KMeansSoft",
                    output_format="string",
                    k_cluster=k,
                )

            start_time = time.time()
            box_plot_set[f"K-Means(k={k})"] = extract_box_plot(kmeans, count=algorithm_tries)
            print(f"Completed k={k}! Took {round(time.time() - start_time, 2)} seconds!")

        print("PLOTTING", box_plot_set)
        save_box_plot_data(box_plot_set, dataset_series, container_directory="kmeans")
        generate_fullscale_plots(box_plot_set, dataset_series, file_count, container_directory="kmeans")

def eval_full_algorithm_test1(algorithm_tries=10):
    myYara = AutoPYara()

    for dataset_series in ["Cluster5_Size23"] or list(reversed([
        "Cluster0_Size134",
        "Cluster1_Size111",
        "Cluster2_Size100",
        "Cluster3_Size53",
        "Cluster5_Size23",
        "Cluster10_Size10",
        "Cluster46_Size4",
    ])):
        directory_path = get_project_path("input_testing", "malicious", "output_preprocessed", dataset_series)
        bloom_filter_malicious_path = "/usr/src/app/intermediate/bloom_filters/malicious-bytes/" 
        bloom_filter_benign_path = "/usr/src/app/intermediate/bloom_filters/benign-bytes/" 

        file_count = count_files_in_directory(directory_path)
        box_plot_set = {}

        loaded_box_plot = load_box_plot_data(dataset_series)
        if loaded_box_plot:
            print(f"already generated results for {dataset_series}! skipping experiment... updating plots...")
            generate_fullscale_plots(loaded_box_plot, dataset_series, file_count)
            box_plot_set = loaded_box_plot
            continue

        k_interval = [2, 3, 4, 5, 6, 7, 9]
        random_k_estimate = 0
        for k in k_interval: # get the largest k possible for this file size, but also consider the set intervals
            if k <= file_count:
                random_k_estimate = k

        for k in k_interval:
            if k > file_count:
                continue

            def kmeans():
                return myYara.generate(
                    directory_path,
                    bloom_filter_malicious_path,
                    bloom_filter_benign_path,
                    bicluster_alg="SpectralCoCluster",
                    cluster_alg="KMeans",
                    output_format="string",
                    k_cluster=k,
                )

            start_time = time.time()
            box_plot_set[f"K-Means(k={k})"] = extract_box_plot(kmeans, count=algorithm_tries)
            print(f"Completed k={k}! Took {round(time.time() - start_time, 2)} seconds!")

        def random_cluster():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="Random",
                output_format="string",
                k_cluster=random_k_estimate,
            )

        def random_cluster2():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="Random",
                output_format="string",
                k_cluster=2,
            )

        def vbgmm():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="VBGMM",
                output_format="string",
            )

        start_time = time.time()
        box_plot_set[f"Random(k={2})"] = extract_box_plot(random_cluster2, count=algorithm_tries)
        print(f"Completed Random(k={2})! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        box_plot_set[f"Random(k={random_k_estimate})"] = extract_box_plot(random_cluster, count=algorithm_tries)
        print(f"Completed Random(k={random_k_estimate})! Took {round(time.time() - start_time, 2)} seconds!")

        for threshold in [80, 81, 83, 85, 87, 90]:#[80, 80.5, 81, 81.5, 82, 82.5, 83, 85, 88, 90, 92, 95, 98]:
            def augmented_DBSCAN():
                return myYara.generate(
                    directory_path,
                    bloom_filter_malicious_path,
                    bloom_filter_benign_path,
                    bicluster_alg="SpectralCoCluster",
                    cluster_alg="AugmentedKMeansDBSCAN",
                    output_format="string",
                    similarity_threshold=threshold
                )

            start_time = time.time()
            box_plot_set[f'AugmentedKMeans\nDBSCAN(similarity={threshold})'] = extract_box_plot(augmented_DBSCAN, count=algorithm_tries)
            print(f"Completed threshold={threshold}! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        box_plot_set['VBGMM'] = extract_box_plot(vbgmm, count=algorithm_tries)
        print(f"Completed VBGMM! Took {round(time.time() - start_time, 2)} seconds!")

        print("PLOTTING", box_plot_set)
        save_box_plot_data(box_plot_set, dataset_series)
        generate_fullscale_plots(box_plot_set, dataset_series, file_count)

def eval_random_vs_vbgmm_vs_augmented(algorithm_tries=10):
    myYara = AutoPYara()

    container_directory = "full_experiment5_cov_range"
    test_fp = True

    input_directory = get_project_path("input_testing", "malicious", "output_preprocessed")

    target_k_value = {
        'Cluster34_Size5': 2,
        'Cluster33_Size6': 3,
        'Cluster17_Size8': 2,
        'Cluster10_Size10': 1,
        'Cluster5_Size23': 1,
        'Cluster4_Size48': 2,
        'Cluster3_Size53': 21,
        'Cluster2_Size100': 35,
        'Cluster0_Size134': 45
    }

    for dataset_series in ['Cluster34_Size5', 'Cluster33_Size6', 'Cluster17_Size8', 'Cluster10_Size10', 'Cluster5_Size23', 'Cluster4_Size48', 'Cluster3_Size53', 'Cluster2_Size100', 'Cluster0_Size134'] or os.listdir(input_directory):
        match = re.match(r'Cluster\d+_Size(\d+)', dataset_series)
        if match:
            size = int(match.group(1))
            if size <= 4:
                continue

        directory_path = get_project_path("input_testing", "malicious", "output_preprocessed", dataset_series)
        bloom_filter_malicious_path = "/usr/src/app/intermediate/bloom_filters/malicious-bytes/" 
        bloom_filter_benign_path = "/usr/src/app/intermediate/bloom_filters/benign-bytes/" 

        file_count = count_files_in_directory(directory_path)
        box_plot_set = {}

        loaded_box_plot = load_box_plot_data(dataset_series, container_directory=container_directory)
        if loaded_box_plot:
            print(f"already generated results for {dataset_series}! skipping experiment... updating plots...")
            #generate_fullscale_plots(loaded_box_plot, dataset_series, file_count, container_directory=container_directory, measure_fp=test_fp)
            #box_plot_set = loaded_box_plot
            continue

        def vbgmm():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="VBGMM",
                output_format="yara-python",
                selection_heuristic="AutoYara",
            )

        # this is the best derived heuristic, we cannot use for a fair comparison between VBGMM and augmented
        target_k = math.ceil(file_count * 2/10) # we do this since we did a kmeans sweep
        if file_count > 25:
            target_k = math.ceil(file_count * 21/50)
        elif file_count > 100:
            target_k = math.ceil(file_count * 45/134)

        target_k = target_k_value[dataset_series]
        print("target k", target_k)

        start_time = time.time()
        # box_plot_set[f"Random(k={2})"] = extract_box_plot(random_cluster2, dataset_series=dataset_series, count=algorithm_tries, measure_fp=test_fp)
        print(f"Completed Random(k={2})! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        # box_plot_set[f"Random(k={random_k_estimate})"] = extract_box_plot(random_cluster, dataset_series=dataset_series, count=algorithm_tries, measure_fp=test_fp)
        print(f"Completed Random(k={9})! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        # box_plot_set[f'VBGMM(cov={50})'] = extract_box_plot(vbgmm, dataset_series=dataset_series, count=algorithm_tries, measure_fp=test_fp)
        print(f"Completed VBGMM! Took {round(time.time() - start_time, 2)} seconds!")

        # def augmented_DBSCAN(target_k):
        #     return myYara.generate(
        #         directory_path,
        #         bloom_filter_malicious_path,
        #         bloom_filter_benign_path,
        #         bicluster_alg="SpectralCoCluster",
        #         cluster_alg="AugmentedKMeansDBSCANSoft",
        #         output_format="yara-python",
        #         augmented_target_k=target_k,
        #         bicluster_feature_prune_coverage=50,
        #     )
        # start_time = time.time()
        # box_plot_set[f'AKMS(same k, cov={50})'] = extract_box_plot(
        #     augmented_DBSCAN, dataset_series=dataset_series, count=algorithm_tries, measure_fp=test_fp, use_k=box_plot_set[f'VBGMM(cov={50})']['Estimated K'])
        # print(f"Completed before! Took {round(time.time() - start_time, 2)} seconds!")

        # def augmented_DBSCAN2():
        #     return myYara.generate(
        #         directory_path,
        #         bloom_filter_malicious_path,
        #         bloom_filter_benign_path,
        #         bicluster_alg="SpectralCoCluster",
        #         cluster_alg="AugmentedKMeansDBSCANSoft",
        #         output_format="yara-python",
        #         augmented_target_k=target_k,
        #         bicluster_feature_prune_coverage=50,
        #     )
        #
        # start_time = time.time()
        # box_plot_set[f'AKMS(k est)'] = extract_box_plot(
        #     augmented_DBSCAN2, dataset_series = dataset_series, count = algorithm_tries, measure_fp = test_fp)
        # print(f"Completed after! Took {round(time.time() - start_time, 2)} seconds!")

        for prune_factor in [70, 90]:
            def augmented_DBSCAN():
                return myYara.generate(
                    directory_path,
                    bloom_filter_malicious_path,
                    bloom_filter_benign_path,
                    bicluster_alg="SpectralCoCluster",
                    cluster_alg="AugmentedKMeansDBSCANSoft",
                    output_format="yara-python",
                    augmented_target_k=target_k,
                    bicluster_feature_prune_coverage=prune_factor,
                )

            def vbgmm2():
                return myYara.generate(
                    directory_path,
                    bloom_filter_malicious_path,
                    bloom_filter_benign_path,
                    bicluster_alg="SpectralCoCluster",
                    cluster_alg="VBGMM",
                    output_format="yara-python",
                    selection_heuristic="AutoYara",
                    bicluster_feature_prune_coverage=prune_factor,
                )

            # start_time = time.time()
            # box_plot_set[f'VBGMM(cov={prune_factor})'] = extract_box_plot(
            #     vbgmm2, dataset_series=dataset_series, count=algorithm_tries, measure_fp=test_fp)
            # print(f"Completed after! Took {round(time.time() - start_time, 2)} seconds!")

            start_time = time.time()
            box_plot_set[f'AKMS(k est, cov={prune_factor})'] = extract_box_plot(
                augmented_DBSCAN, dataset_series=dataset_series, count=algorithm_tries, measure_fp=test_fp)
            print(f"Completed after! Took {round(time.time() - start_time, 2)} seconds!")

        print("PLOTTING", box_plot_set)
        save_box_plot_data(box_plot_set, dataset_series, container_directory=container_directory)
        generate_fullscale_plots(box_plot_set, dataset_series, file_count, container_directory=container_directory, measure_fp=test_fp)

def eval_cross_validation(algorithm_tries=10):
    myYara = AutoPYara()

    for dataset_series in ["Cluster2_Size100"] or list(reversed([
        "Cluster0_Size134",
        # "Cluster1_Size111",
        "Cluster2_Size100",
        "Cluster3_Size53",
        "Cluster4_Size48",
        "Cluster5_Size23",
        "Cluster6_Size23",
        "Cluster7_Size14",
        "Cluster10_Size10",
        "Cluster46_Size4",
        "Cluster169_Size2",
    ])):
        directory_path = get_project_path("input_testing", "malicious", "output_preprocessed", dataset_series)
        bloom_filter_malicious_path = "/usr/src/app/intermediate/bloom_filters/malicious-bytes/" 
        bloom_filter_benign_path = "/usr/src/app/intermediate/bloom_filters/benign-bytes/"

        file_count = count_files_in_directory(directory_path)
        box_plot_set = {}

        loaded_box_plot = load_box_plot_data(dataset_series)
        if loaded_box_plot:
            print(f"already generated results for {dataset_series}! skipping experiment... updating plots...")
            generate_fullscale_plots(loaded_box_plot, dataset_series, file_count)
            box_plot_set = loaded_box_plot
            continue

        k_interval = [2, 3, 4, 5, 6, 7, 9]
        random_k_estimate = 0
        for k in k_interval: # get the largest k possible for this file size, but also consider the set intervals
            if k <= file_count:
                random_k_estimate = k

        def random_cluster():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="Random",
                output_format="yara-python",
                k_cluster=random_k_estimate,
            )

        def random_cluster2():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="Random",
                output_format="yara-python",
                k_cluster=2,
            )

        def vbgmm():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="VBGMM",
                output_format="yara-python",
            )

        start_time = time.time()
        box_plot_set[f"Random(k={2})"] = extract_box_plot(random_cluster2, dataset_series=dataset_series, count=algorithm_tries)
        print(f"Completed Random(k={2})! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        box_plot_set[f"Random(k={random_k_estimate})"] = extract_box_plot(random_cluster, dataset_series=dataset_series, count=algorithm_tries)
        print(f"Completed Random(k={random_k_estimate})! Took {round(time.time() - start_time, 2)} seconds!")

        # for threshold in [80, 81, 85, 92]: # no reason to waste additional time/resources on the inferior implementation
        #     def augmented_DBSCAN():
        #         return myYara.generate(
        #             directory_path,
        #             bloom_filter_malicious_path,
        #             bloom_filter_benign_path,
        #             bicluster_alg="SpectralCoCluster",
        #             cluster_alg="AugmentedKMeansDBSCAN",
        #             output_format="yara-python",
        #             similarity_threshold=threshold
        #         )
        #
        #     start_time = time.time()
        #     box_plot_set[f'AugmentedKMeans\nDBSCAN(similarity={threshold})'] = extract_box_plot(augmented_DBSCAN, count=algorithm_tries)
        #     print(f"Completed threshold={threshold}! Took {round(time.time() - start_time, 2)} seconds!")

        for prune_factor in (50, 90):
            for threshold in [80, 81, 85, 92]:
                def augmented_DBSCAN():
                    return myYara.generate(
                        directory_path,
                        bloom_filter_malicious_path,
                        bloom_filter_benign_path,
                        bicluster_alg="SpectralCoCluster",
                        cluster_alg="AugmentedKMeansDBSCANSoft",
                        output_format="yara-python",
                        similarity_threshold=threshold,
                        bicluster_feature_prune_coverage=prune_factor,
                    )

                start_time = time.time()
                box_plot_set[f'AugmentedKMeansSoft\nDBSCAN(similarity={threshold}, prune={prune_factor})'] = extract_box_plot(
                    augmented_DBSCAN, dataset_series=dataset_series, count=algorithm_tries)
                print(f"Completed threshold={threshold}! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        box_plot_set['VBGMM'] = extract_box_plot(vbgmm, dataset_series=dataset_series, count=algorithm_tries)
        print(f"Completed VBGMM! Took {round(time.time() - start_time, 2)} seconds!")

        print("PLOTTING", box_plot_set)
        save_box_plot_data(box_plot_set, dataset_series)
        generate_fullscale_plots(box_plot_set, dataset_series, file_count)



def eval_get_k_difference():
    experiment3 = get_all_results(
        get_project_path("output", "full_experiment3")
    )

    total_difference = 0
    count = 0

    for cluster_name, directory_data in experiment3.items():
        # Extract the estimated k values for each algorithm
        vbgmm_k_values = []
        akms_k_values = []

        for algorithm, algorithm_results in directory_data['data'].items():
            for metric, output_list in algorithm_results.items():
                if metric == "Estimated K":
                    if algorithm == "VBGMM":
                        vbgmm_k_values = output_list
                    elif algorithm == "AKMS(cov=50)":
                        akms_k_values = output_list

        print("Comparing", cluster_name)
        print("VBGMM", vbgmm_k_values)
        print("AKMS ", akms_k_values)

        # Make sure we have the same number of k values for both algorithms
        if len(vbgmm_k_values) == len(akms_k_values):
            # Compute the differences for this cluster (VBGMM - AKMS)

            differences = [vbgmm_k - akms_k for vbgmm_k, akms_k in zip(vbgmm_k_values, akms_k_values)]

            # Sum up the differences
            cluster_total_difference = sum(differences)
            count += len(differences)
            total_difference += cluster_total_difference
            print("")

    # Compute the overall average difference
    average_difference = total_difference / count if count > 0 else 0
    print(f"Overall average k difference (VBGMM - AKMS): {average_difference}")


def eval_get_global_averages_akms_vbgmm():
    algorithm1 = "AKMS(k est, cov=50)"
    algorithm2 = "AKMS(k est, cov=90)"

    experiment3 = get_all_results(
        get_project_path("output", "full_experiment4_targetted_k_Old")
    )
    kmeans_sweep = get_all_results(
        get_project_path("output", "kmeans")
    )

    # Dictionaries to store aggregated metrics for each algorithm
    vbgmm_metrics = {}
    akms_metrics = {}

    cluster_names = []

    # Process all data
    for cluster_name, directory_data in experiment3.items():
        cluster_names.append(directory_data['cluster_name'])
        for algorithm, algorithm_results in directory_data['data'].items():
            if algorithm == algorithm1:
                target_dict = vbgmm_metrics
            elif algorithm == algorithm2:
                target_dict = akms_metrics
            else:
                continue  # Skip other algorithms if present

            for metric, output_list in algorithm_results.items():
                if len(output_list) == 0:
                    continue  # Skip empty lists

                # Initialize the metric in the target dictionary if not already present
                if metric not in target_dict:
                    target_dict[metric] = {
                        'sum': 0,
                        'count': 0,
                        'all_averages': []
                    }

                # Calculate average for this output_list
                list_avg = sum(output_list) / len(output_list)

                # Add this average to the list of all averages for this metric
                target_dict[metric]['all_averages'].append(list_avg)

                # Update the sum and count for global average calculation
                target_dict[metric]['sum'] += sum(output_list)
                target_dict[metric]['count'] += len(output_list)

    # Calculate and print the results
    print("=" * 50)
    print(f"GLOBAL AVERAGES FOR {algorithm1} VS {algorithm2}")
    print("=" * 50)

    # Print table headers
    print(f"{'Metric':<30} | {algorithm1:<15} | {algorithm2:<15}")
    print("-" * 64)

    # Get all unique metrics from both algorithms
    all_metrics = set(list(vbgmm_metrics.keys()) + list(akms_metrics.keys()))

    # Print each metric
    for metric in sorted(all_metrics):
        vbgmm_avg = "N/A"
        akms_avg = "N/A"

        # Calculate VBGMM average if data exists
        if metric in vbgmm_metrics and vbgmm_metrics[metric]['count'] > 0:
            # Method 1: Global average of all values
            vbgmm_avg_1 = vbgmm_metrics[metric]['sum'] / vbgmm_metrics[metric]['count']

            # Method 2: Average of the averages (one avg per cluster)
            vbgmm_avg_2 = sum(vbgmm_metrics[metric]['all_averages']) / len(vbgmm_metrics[metric]['all_averages'])

            vbgmm_avg = f"{vbgmm_avg_2:.4f}"

        # Calculate AKMS average if data exists
        if metric in akms_metrics and akms_metrics[metric]['count'] > 0:
            # Method 1: Global average of all values
            akms_avg_1 = akms_metrics[metric]['sum'] / akms_metrics[metric]['count']

            # Method 2: Average of the averages (one avg per cluster)
            akms_avg_2 = sum(akms_metrics[metric]['all_averages']) / len(akms_metrics[metric]['all_averages'])

            akms_avg = f"{akms_avg_2:.4f}"

        print(f"{metric:<30} | {vbgmm_avg:<15} | {akms_avg:<15}")

    print("=" * 64)
    print("Note: These are averages of individual cluster averages (Method 2)")

    # Print detailed per-cluster averages for each metric
    print("\nPER-CLUSTER AVERAGES:")
    for algorithm, metrics_dict in [(algorithm1, vbgmm_metrics), (algorithm2, akms_metrics)]:
        print(f"\n{algorithm} DETAILED AVERAGES:")
        print("-" * 50)

        for metric, data in sorted(metrics_dict.items()):
            if len(data['all_averages']) > 0:
                print(f"{metric}:")
                for i, avg in enumerate(data['all_averages']):
                    print(f"  {cluster_names[i]}: {avg:.4f}")
                print(f"  AVERAGE: {sum(data['all_averages']) / len(data['all_averages']):.4f}")
                print()


def eval_get_global_average_best_k():
    experiment3 = get_all_results(
        get_project_path("output", "kmeans")
    )

    all_best_tp_averages = []
    cluster_results = []

    for cluster_name, directory_data in experiment3.items():
        best_algorithm = None
        best_avg_tp = -1

        # Find the algorithm with the highest average TP for this cluster
        for algorithm, algorithm_results in directory_data['data'].items():
            # Check if this is a K-Means algorithm
            if not algorithm.startswith("K-Means(k="):
                continue

            # Extract the k value from the algorithm name
            try:
                k_value = int(algorithm.split("K-Means(k=")[1].split(")")[0])
            except:
                continue

            # Find the TP metric for this algorithm
            for metric, output_list in algorithm_results.items():
                if metric == "TP":
                    # Calculate average TP
                    if output_list and len(output_list) > 0:
                        avg_tp = sum(output_list) / len(output_list)

                        # Check if this is the best so far
                        if avg_tp > best_avg_tp:
                            best_avg_tp = avg_tp
                            best_algorithm = algorithm

        # If we found a best algorithm for this cluster, add its average TP to our list
        if best_avg_tp > -1:
            all_best_tp_averages.append(best_avg_tp)

            # Extract cluster ID and size from the full path
            cluster_id = None
            try:
                # Extract just the filename part (Cluster35_Size5)
                filename = cluster_name.split('/')[-1]
                cluster_id = int(filename.split('Cluster')[1].split('_')[0])
            except:
                cluster_id = 999  # Default high value for sorting if extraction fails

            # Store results for sorted output
            cluster_results.append((cluster_id, filename, best_algorithm, best_avg_tp))

    # Sort results by cluster ID
    cluster_results.sort(key=lambda x: x[0])

    # Print results in sorted order with shortened cluster names
    for _, short_name, algorithm, avg_tp in cluster_results:
        print(f"Cluster: {short_name}, Best algorithm: {algorithm}, Avg TP: {avg_tp}")

    # Calculate global average of best TP values
    if all_best_tp_averages:
        global_avg_best_tp = sum(all_best_tp_averages) / len(all_best_tp_averages)
        print(f"Global average of best TP: {global_avg_best_tp}")
        return global_avg_best_tp
    else:
        print("No valid TP values found")
        return None


def eval_get_global_averages_akms_vbgmm_bestk():
    experiment3 = get_all_results(
        get_project_path("output", "full_experiment3")
    )
    kmeans_sweep = get_all_results(
        get_project_path("output", "kmeans")
    )

    # Extract cluster identifiers from the directory paths
    def extract_cluster_id(directory_path):
        # Extract the cluster name (e.g., 'Cluster3' from 'Cluster3_Size53')
        parts = directory_path.split('/')[-1].split('_')[0]  # Gets 'Cluster3' from 'Cluster3_Size53'
        return parts

    # Extract numeric part from cluster ID for sorting
    def get_cluster_number(cluster_id):
        return int(''.join(filter(str.isdigit, cluster_id)))

    # Get all directories and extract cluster identifiers
    experiment3_clusters = {extract_cluster_id(directory): directory for directory in experiment3.keys()}
    kmeans_sweep_clusters = {extract_cluster_id(directory): directory for directory in kmeans_sweep.keys()}

    # Find common clusters based on cluster IDs
    common_cluster_ids = set(experiment3_clusters.keys()) & set(kmeans_sweep_clusters.keys())

    print(f"Experiment3 clusters: {', '.join(experiment3_clusters.keys())}")
    print(f"KMeans sweep clusters: {', '.join(kmeans_sweep_clusters.keys())}")
    print(f"Common clusters found: {', '.join(sorted(common_cluster_ids, key=get_cluster_number))}")

    # Results dictionaries to store metrics for each algorithm
    results = {
        "estimated_k": {"VBGMM": [], "AKMS": [], "best_kmeans": []},
        "best_kmeans_models": [],
        "tp": {"VBGMM": [], "AKMS": [], "best_kmeans": []},
        "fp": {"VBGMM": [], "AKMS": [], "best_kmeans": []}
    }

    # Store per-cluster results for detailed comparison
    cluster_results = {}

    # Process each common cluster in numerical order
    for cluster_id in sorted(common_cluster_ids, key=get_cluster_number):
        print(f"\nProcessing cluster: {cluster_id}")

        # Get the full directory paths for this cluster
        experiment3_dir = experiment3_clusters[cluster_id]
        kmeans_sweep_dir = kmeans_sweep_clusters[cluster_id]

        # Get the cluster data from each dataset
        experiment3_cluster_data = experiment3[experiment3_dir]['data']
        kmeans_sweep_cluster_data = kmeans_sweep[kmeans_sweep_dir]['data']

        # Extract VBGMM and AKMS metrics
        vbgmm_data = experiment3_cluster_data.get("VBGMM", {})
        akms_data = experiment3_cluster_data.get("AKMS(cov=50)", {})

        if not vbgmm_data or not akms_data:
            print(f"  Missing VBGMM or AKMS data for {cluster_id}, skipping")
            continue

        vbgmm_est_k = vbgmm_data.get("Estimated K", [])
        vbgmm_tp = vbgmm_data.get("TP", [])
        vbgmm_fp = vbgmm_data.get("FP Labeled Global (malware)", [])

        akms_est_k = akms_data.get("Estimated K", [])
        akms_tp = akms_data.get("TP", [])
        akms_fp = akms_data.get("FP Labeled Global (malware)", [])

        # Find the best K-Means model based on TP rate
        best_kmeans_model = None
        best_kmeans_tp_values = []
        best_kmeans_est_k_values = []
        best_kmeans_fp_values = []
        highest_avg_tp = float('-inf')

        for kmeans_model, kmeans_metrics in kmeans_sweep_cluster_data.items():
            if kmeans_model.startswith("K-Means(k="):
                tp_values = kmeans_metrics.get("TP", [])

                if tp_values:
                    avg_tp = sum(tp_values) / len(tp_values) if tp_values else 0

                    if avg_tp > highest_avg_tp:
                        highest_avg_tp = avg_tp
                        best_kmeans_model = kmeans_model

                        best_kmeans_tp_values = tp_values
                        best_kmeans_est_k_values = kmeans_metrics.get("Estimated K", [])
                        best_kmeans_fp_values = kmeans_metrics.get("FP Labeled Global (malware)", [])

        if not best_kmeans_model:
            print(f"  No K-Means models found for {cluster_id}, skipping")
            continue

        # Extract the k value from the best k-means model name
        best_k_value = int(best_kmeans_model.split('=')[1].split(')')[0])

        # Calculate average metrics for this cluster
        vbgmm_avg_est_k = sum(vbgmm_est_k) / len(vbgmm_est_k) if vbgmm_est_k else 0
        akms_avg_est_k = sum(akms_est_k) / len(akms_est_k) if akms_est_k else 0
        best_kmeans_avg_est_k = sum(best_kmeans_est_k_values) / len(
            best_kmeans_est_k_values) if best_kmeans_est_k_values else 0

        vbgmm_avg_tp = sum(vbgmm_tp) / len(vbgmm_tp) if vbgmm_tp else 0
        akms_avg_tp = sum(akms_tp) / len(akms_tp) if akms_tp else 0
        best_kmeans_avg_tp = sum(best_kmeans_tp_values) / len(best_kmeans_tp_values) if best_kmeans_tp_values else 0

        # Store per-cluster results
        cluster_results[cluster_id] = {
            "VBGMM": {
                "estimated_k": vbgmm_avg_est_k,
                "tp": vbgmm_avg_tp
            },
            "AKMS": {
                "estimated_k": akms_avg_est_k,
                "tp": akms_avg_tp
            },
            "best_kmeans": {
                "model": best_kmeans_model,
                "k_value": best_k_value,
                "estimated_k": best_kmeans_avg_est_k,
                "tp": best_kmeans_avg_tp
            }
        }

        print(f"  Best K-Means model for {cluster_id}: {best_kmeans_model} (k={best_k_value})")
        print(
            f"  Average Estimated K: VBGMM={vbgmm_avg_est_k:.1f}, AKMS={akms_avg_est_k:.1f}, Best K-Means={best_kmeans_avg_est_k:.1f}")
        print(
            f"  Difference from best k: VBGMM={vbgmm_avg_est_k - best_k_value:.1f}, AKMS={akms_avg_est_k - best_k_value:.1f}")
        print(f"  Average TP: VBGMM={vbgmm_avg_tp:.1f}, AKMS={akms_avg_tp:.1f}, Best K-Means={best_kmeans_avg_tp:.1f}")

        # Store the results for this cluster
        results["estimated_k"]["VBGMM"].extend(vbgmm_est_k)
        results["estimated_k"]["AKMS"].extend(akms_est_k)
        results["estimated_k"]["best_kmeans"].extend(best_kmeans_est_k_values)
        results["best_kmeans_models"].append(best_kmeans_model)

        results["tp"]["VBGMM"].extend(vbgmm_tp)
        results["tp"]["AKMS"].extend(akms_tp)
        results["tp"]["best_kmeans"].extend(best_kmeans_tp_values)

        results["fp"]["VBGMM"].extend(vbgmm_fp)
        results["fp"]["AKMS"].extend(akms_fp)
        results["fp"]["best_kmeans"].extend(best_kmeans_fp_values)

    # Print side-by-side comparison of all clusters
    print("\n\nSide-by-Side Cluster Comparison:")
    print("=" * 80)
    print(
        f"{'Cluster':<10} | {'Best K-Means':<12} | {'VBGMM Est K':<12} | {'AKMS Est K':<12} | {'VBGMM TP':<10} | {'AKMS TP':<10} | {'K-Means TP':<10}")
    print("-" * 80)

    for cluster_id in sorted(cluster_results.keys(), key=get_cluster_number):
        data = cluster_results[cluster_id]
        best_k = data["best_kmeans"]["k_value"]
        vbgmm_k = data["VBGMM"]["estimated_k"]
        akms_k = data["AKMS"]["estimated_k"]

        print(
            f"{cluster_id:<10} | {best_k:<12} | {vbgmm_k:<12.1f} | {akms_k:<12.1f} | {data['VBGMM']['tp']:<10.1f} | {data['AKMS']['tp']:<10.1f} | {data['best_kmeans']['tp']:<10.1f}")

    # Calculate global averages
    print("\nGlobal Averages:")

    # Estimated K
    avg_vbgmm_est_k = sum(results["estimated_k"]["VBGMM"]) / len(results["estimated_k"]["VBGMM"]) if \
        results["estimated_k"]["VBGMM"] else 0
    avg_akms_est_k = sum(results["estimated_k"]["AKMS"]) / len(results["estimated_k"]["AKMS"]) if \
        results["estimated_k"]["AKMS"] else 0
    avg_kmeans_est_k = sum(results["estimated_k"]["best_kmeans"]) / len(results["estimated_k"]["best_kmeans"]) if \
        results["estimated_k"]["best_kmeans"] else 0

    print("Estimated K:")
    print(f"  VBGMM: {avg_vbgmm_est_k:.1f}")
    print(f"  AKMS: {avg_akms_est_k:.1f}")
    print(f"  Best K-Means: {avg_kmeans_est_k:.1f}")
    print(f"  Best K-Means Models: {', '.join(results['best_kmeans_models'])}")

    # TP
    avg_vbgmm_tp = sum(results["tp"]["VBGMM"]) / len(results["tp"]["VBGMM"]) if results["tp"]["VBGMM"] else 0
    avg_akms_tp = sum(results["tp"]["AKMS"]) / len(results["tp"]["AKMS"]) if results["tp"]["AKMS"] else 0
    avg_kmeans_tp = sum(results["tp"]["best_kmeans"]) / len(results["tp"]["best_kmeans"]) if results["tp"][
        "best_kmeans"] else 0

    print("\nTrue Positives (TP):")
    print(f"  VBGMM: {avg_vbgmm_tp:.1f}")
    print(f"  AKMS: {avg_akms_tp:.1f}")
    print(f"  Best K-Means: {avg_kmeans_tp:.1f}")

    # FP
    avg_vbgmm_fp = sum(results["fp"]["VBGMM"]) / len(results["fp"]["VBGMM"]) if results["fp"]["VBGMM"] else 0
    avg_akms_fp = sum(results["fp"]["AKMS"]) / len(results["fp"]["AKMS"]) if results["fp"]["AKMS"] else 0
    avg_kmeans_fp = sum(results["fp"]["best_kmeans"]) / len(results["fp"]["best_kmeans"]) if results["fp"][
        "best_kmeans"] else 0

    print("\nFalse Positives (FP):")
    print(f"  VBGMM: {avg_vbgmm_fp:.1f}")
    print(f"  AKMS: {avg_akms_fp:.1f}")
    print(f"  Best K-Means: {avg_kmeans_fp:.1f}")

    # K-differences
    print("\nEstimated K Differences:")
    print(f"  VBGMM - AKMS: {avg_vbgmm_est_k - avg_akms_est_k:.1f}")
    print(f"  VBGMM - Best K-Means: {avg_vbgmm_est_k - avg_kmeans_est_k:.1f}")
    print(f"  AKMS - Best K-Means: {avg_akms_est_k - avg_kmeans_est_k:.1f}")

    # Return dictionaries for further analysis if needed
    return {
        "VBGMM": {
            "estimated_k": avg_vbgmm_est_k,
            "tp": avg_vbgmm_tp,
            "fp": avg_vbgmm_fp
        },
        "AKMS": {
            "estimated_k": avg_akms_est_k,
            "tp": avg_akms_tp,
            "fp": avg_akms_fp
        },
        "best_kmeans": {
            "estimated_k": avg_kmeans_est_k,
            "tp": avg_kmeans_tp,
            "fp": avg_kmeans_fp,
            "models": results["best_kmeans_models"]
        },
        "cluster_results": cluster_results
    }