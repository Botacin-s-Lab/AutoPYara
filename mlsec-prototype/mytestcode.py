import os

import yara
from sympy.series.sequences import SeqExpr
from sympy.strategies.branch import condition
import matplotlib.pyplot as plt

from AutoYara import AutoPYara
from difflib import SequenceMatcher
from utils.clustering import cluster_files_LSH
import yaramod
import random

# Get the directory containing the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define project root relative to script location
# Assuming this script is in the project root or a known location relative to it
PROJECT_ROOT = os.path.join(os.path.dirname(SCRIPT_DIR), "mlsec-prototype")

def get_project_path(*paths):
    """
    Join paths relative to the project root.
    Args:
        *paths: Variable number of path components to join
    Returns:
        str: Absolute path joined with project root
    """
    return os.path.join(PROJECT_ROOT, *paths)

def demo_train():
    myYara = AutoPYara(ngram_top_k=100)

    for i in [8, 16]:  # n-grams
        myYara.train(
            get_project_path("input_training", "benign", "gw1_lite"),
            get_project_path("intermediate", "bloom_filters", "benign"),
            ngram_size=i
        )
        myYara.train(
            get_project_path("input_training", "malicious", "mw1_lite"),
            get_project_path("intermediate", "bloom_filters", "malicious"),
            ngram_size=i
        )


def demo_predict():
    myYara = AutoPYara()
    print("Predictions:")
    yara_obj, output = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign")
    )
    print(output)


def demo_get_signatures():
    myYara = AutoPYara(ngram_top_k=100)
    myList = myYara.build_candidate_set(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        ngram_size=8
    )

    for candidate_dict in myList:
        print(candidate_dict['signature'])
        print(candidate_dict['b_fp'])


def demo_select_bicluster():
    myYara = AutoPYara()
    print("Predictions (spectral):")
    output = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster"
    )
    print(output)

    print("Predictions (spectral scaled):")
    output = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoClusterScale"
    )
    print(output)

def demo_kmeans_vs_VBGMM():
    myYara = AutoPYara()

    print("AutoYara Cluster: (Random)")
    output1 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="Random"
    )
    print(output1)

    print("AutoYara Cluster: (KMeans)")
    output2 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="KMeans"
    )
    print(output2)

    print("AutoYara Cluster: (VBGMM)")
    output3 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="VBGMM"
    )
    print(output3)

    print("Output similarity (Random vs KMeans):", SequenceMatcher(None, output1, output2).ratio())
    print("Output similarity (Random vs VBGMM): ", SequenceMatcher(None, output1, output3).ratio())
    print("Output similarity (KMeans vs VBGMM): ", SequenceMatcher(None, output2, output3).ratio())


# This is deprecated, don't use!
def evaluate_rule(yara_file, rule_name):
    yara_file = yara_file['output']

    if isinstance(yara_file, str):
        print("rule eval for", rule_name)
        print(yara_file)
        return

    if len(yara_file.rules) <= 0:
        print("rule eval for", rule_name, "... has no rule!")
        return

    rule = yara_file.rules[0]  # Since you have one rule per object

    print("rule eval for", rule_name, yara_file.text)
    print({
        'total_rules': 1,
        'string_count': len(rule.strings),
        'condition_text': rule.condition.text
    })

def demo_compare_kmeans_vbgmm_augmented():
    myYara = AutoPYara()

    print("AutoYara Cluster: (VBGMM)")
    yara_obj3 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="VBGMM",
        output_format="string",
    )

    print("AutoYara Cluster: (AugmentedKMeansDBSCAN)")
    yara_obj4 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="AugmentedKMeansDBSCAN",
        output_format="string",
    )

    print("AutoYara Cluster: (Random)")
    yara_obj1 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="Random",
        output_format="string",
    )

    print("AutoYara Cluster: (KMeans)")
    yara_obj2 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="KMeans",
        output_format="string",
    )

    evaluate_rule(yara_obj1, "Random")
    evaluate_rule(yara_obj2, "KMeans")
    evaluate_rule(yara_obj3, "VBGMM")
    evaluate_rule(yara_obj4, "AugmentedKMeansDBSCAN")

def demo_augmented_clustering():
    myYara = AutoPYara()

    print("AutoYara Cluster: (VBGMM)")
    yara_obj3 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="VBGMM",
        output_format="string",
    )

    print("final rule:", yara_obj3)

    print("AutoYara Cluster: (AugmentedKMeansDBSCAN)")
    yara_obj4 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="AugmentedKMeansDBSCAN",
        output_format="string",
    )

    print("final rule:", yara_obj4)
    
def demo_test_ordering_bug():
    myYara = AutoPYara()
    myYara2 = AutoPYara()

    # print("AutoYara Cluster: (Random)")
    # output1 = myYara.generate(
    #     get_project_path("input_testing", "malicious", "mw2"),
    #     get_project_path("intermediate", "bloom_filters", "malicious-bytes"),
    #     get_project_path("intermediate", "bloom_filters", "benign-bytes"),
    #     bicluster_alg="SpectralCoCluster",
    #     cluster_alg="Random"
    # )
    # print(output1)

    print("AutoYara Cluster: (AugmentedKMeansDBSCAN)")
    yara_obj3, raw_string = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious-bytes"),
        get_project_path("intermediate", "bloom_filters", "benign-bytes"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="AugmentedKMeansDBSCAN",
        output_format="string",
    )
    print(yara_obj3)
    print("type", type(yara_obj3))

    # print("AutoYara Cluster: (AugmentedKMeansDBSCAN)")
    # yara_obj3B = myYara2.generate(
    #     get_project_path("input_testing", "malicious", "mw2"),
    #     get_project_path("intermediate", "bloom_filters", "malicious-bytes"),
    #     get_project_path("intermediate", "bloom_filters", "benign-bytes"),
    #     bicluster_alg="SpectralCoCluster",
    #     cluster_alg="AugmentedKMeansDBSCAN",
    #     output_format="string",
    # )
    # print(yara_obj3B)

def demo_test_realworld():
    myYara = AutoPYara()

    for cluster_folder in ["Cluster0_Size134", "Cluster10_Size10"]:
        # print("AutoYara Cluster: (AugmentedKMeansDBSCAN)")
        yara_obj3 = myYara.generate(
            get_project_path("input_testing", "malicious", "output_preprocessed", cluster_folder),
            get_project_path("intermediate", "bloom_filters", "malicious-bytes"),
            get_project_path("intermediate", "bloom_filters", "benign-bytes"),
            output_dir=get_project_path("output", cluster_folder),
            bicluster_alg="SpectralCoCluster",
            cluster_alg="AugmentedKMeansDBSCAN",
            output_format="string",
        )
        # print(yara_obj3)
        # print("type", type(yara_obj3))

        # print("AutoYara Cluster: (VBGMM)")
        yara_obj4 = myYara.generate(
            get_project_path("input_testing", "malicious", "output_preprocessed", cluster_folder),
            get_project_path("intermediate", "bloom_filters", "malicious-bytes"),
            get_project_path("intermediate", "bloom_filters", "benign-bytes"),
            output_dir=get_project_path("output", cluster_folder),
            bicluster_alg="SpectralCoCluster",
            cluster_alg="VBGMM",
            output_format="string",
        )
        # print(yara_obj4)
        # print("type", type(yara_obj4))

        for k in range(2, 40, 2):
            yara_obj = myYara.generate(
                get_project_path("input_testing", "malicious", "output_preprocessed", cluster_folder),
                get_project_path("intermediate", "bloom_filters", "malicious-bytes"),
                get_project_path("intermediate", "bloom_filters", "benign-bytes"),
                output_dir=get_project_path("output", cluster_folder),
                bicluster_alg="SpectralCoCluster",
                cluster_alg="KMeans",
                output_format="string",
                k_cluster=k,
            )
            # print(f"K-Means (k = {k}):", yara_obj)

def plot_yara_metrics(box_plot_set, targeted_metric="TP", save_path=None, series_name="Generic"):
    # Set up the plot
    plt.figure(figsize=(12, 6))

    box_plot_data = []
    for algorithm, data in box_plot_set.items():
        box_plot_data.append(data[targeted_metric])

    # Create box plots
    plt.boxplot(
        box_plot_data,
        tick_labels=list(box_plot_set.keys()),
    )

    # Customize the plot
    plt.title(f"YARA Rules {targeted_metric} Distribution ({series_name} dataset)", pad=20)
    plt.ylabel(targeted_metric)
    plt.grid(True, axis='y', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save or display the plot
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def generate_fullscale_plots(series_name, box_plot_set):
    for algorithm, dataset in box_plot_set.items():
        for metric, list in dataset.items():
            plot_yara_metrics(
                box_plot_set,
                targeted_metric=metric,
                save_path=get_project_path("output", "graphs", series_name, f"{metric}.png"),
                series_name=series_name,
            )
        break

def extract_box_plot(f, count=20):
    # Run function f() COUNT times and collect metrics for box plot visualization

    # Initialize lists to store metrics

    # suppose we have
    # testrule =
    # strings: $x1, $x2, $x3, $x4, $x5
    # conditions: (2 of $x1, $x2, $x3) or (3 of $x1, $x2, $x4, $x5)

    # TP: true positive rate based on the given dataset and the rule generated from it
    # Higher TP tend to be better. Do not rely on this metric alone as it can be overfitted (model COULD generate 1000 rules and get a perfect match)

    # Conditions Count: number of OR conditions in the rule, testrule would have 2 OR conditions
    # Conditions count tend to indicate the model's best estimation of the number of sub-communities in the dataset

    # Average Strings per Condition: number of strings within each condition, testrule has 3 and 4, averaging 3.5
    # Generally, smaller is better since it's more readable by a human

    # Average Condition Ratio: how much of the % of the min is required to match the condition, testrule has 2/3 and 3/4, totaling 17/12 and averaging 17/24
    # The ratio tends to indicate "confidence". The higher the ratio, the more sure the algorithm is that this set of strings is known to be malicious.

    # Gram Size: gram size of the strings (AutoYara/AutoPYara forces all strings to be of the same ngram)
    # Higher gram size tend to be better (less false positives).

    # Strings Generated: # of strings generated, testrule has 5
    # Less strings generated tend to be better as long as TP is the same.

    # Estimated K: estimated # of clusters
    # K will depend on the size and complexity of the dataset. It is used only to compare with kmeans.

    data_dict = {
        'TP': [],
        'Conditions Count': [],
        'Average Strings per Condition': [],
        'Average Condition Ratio': [], #
        'Gram Size': [],
        'Strings Generated': [],
        'Estimated K': [],
    }

    # Collect data from multiple runs
    for i in range(count):
        yara_out = f()
        if not yara_out:
            for entry, list in data_dict.items():
                list.append(0)
            continue

        condition_ratios = []
        for i in range(len(yara_out['conditions_max'])):
            condition_ratios.append(yara_out['conditions_min'][i] / yara_out['conditions_max'][i])

        # Extract and store metrics
        data_dict['TP'].append(yara_out['TP'])
        data_dict['Conditions Count'].append(len(yara_out['conditions_max']))
        data_dict['Average Strings per Condition'].append(sum(yara_out['conditions_max']) / len(yara_out['conditions_max']))
        data_dict['Average Condition Ratio'].append(sum(condition_ratios) / len(condition_ratios))
        data_dict['Gram Size'].append(yara_out['gram_size'])
        data_dict['Strings Generated'].append(yara_out['strings'])
        data_dict['Estimated K'].append(yara_out['k_clusters'])

    # Return dictionary with collected metrics
    return data_dict

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

def eval_full_algorithm_test1(algorithm_tries=10):
    myYara = AutoPYara()

    for dataset_series in ["Cluster10_Size10", "Cluster0_Size134"]:
        directory_path = get_project_path("input_testing", "malicious", "output_preprocessed", dataset_series)
        bloom_filter_malicious_path = get_project_path("intermediate", "bloom_filters", "malicious-bytes")
        bloom_filter_benign_path = get_project_path("intermediate", "bloom_filters", "benign-bytes")

        def eval1():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="AugmentedKMeansDBSCAN",
                output_format="string",
            )

        def eval2():
            return myYara.generate(
                directory_path,
                bloom_filter_malicious_path,
                bloom_filter_benign_path,
                bicluster_alg="SpectralCoCluster",
                cluster_alg="VBGMM",
                output_format="string",
            )

        box_plot_set = {}
        box_plot_set['VBGMM'] = extract_box_plot(eval2, count=algorithm_tries)
        box_plot_set['AugmentedKMeansDBSCAN'] = extract_box_plot(eval1, count=algorithm_tries)

        file_count = count_files_in_directory(directory_path)

        for k in get_integer_interval(2, min(file_count, 50), 12):
            def eval3():
                return myYara.generate(
                    directory_path,
                    bloom_filter_malicious_path,
                    bloom_filter_benign_path,
                    bicluster_alg="SpectralCoCluster",
                    cluster_alg="KMeans",
                    output_format="string",
                    k_cluster=k,
                )
            box_plot_set[f"K-Means(k={k})"] = extract_box_plot(eval3, count=algorithm_tries)

        print("PLOTTING", box_plot_set)
        generate_fullscale_plots(dataset_series, box_plot_set)

if __name__ == "__main__":
    print("starting test code")
    # demo_augmented_clustering()
    # demo_compare_kmeans_vbgmm_augmented()

    # demo_test_realworld()

    eval_full_algorithm_test1(algorithm_tries=10)