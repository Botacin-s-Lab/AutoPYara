import os
import json
import re
import math
import time

import yara
from sympy import ceiling
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

def save_box_plot_data(box_plot_set, dataset_series, container_directory="graphs"):
    # Create output directory if it doesn't exist
    os.makedirs(get_project_path("output", container_directory), exist_ok=True)
    os.makedirs(get_project_path("output", container_directory, dataset_series), exist_ok=True)

    # Create filename with dataset series name
    filename = get_project_path("output", container_directory, dataset_series, "Evaluation Results.json")

    # Convert any numpy arrays to lists for JSON serialization
    serializable_data = {}
    for algorithm, metrics in box_plot_set.items():
        serializable_data[algorithm] = {
            metric: list(values) if hasattr(values, '__iter__') else values
            for metric, values in metrics.items()
        }

    # Save to file with nice formatting
    with open(filename, 'w') as f:
        json.dump(serializable_data, f, indent=4)

    print(f"Saved box plot data to: {filename}")

def load_box_plot_data(dataset_series, container_directory="graphs"):
    filename = get_project_path("output", container_directory, dataset_series, "Evaluation Results.json")

    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No saved data found at: {filename}")
        return None

def save_plot(save_path=None):
    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save or display the plot
    if save_path:
        # Save as PDF for vector graphics
        if not save_path.endswith('.pdf'):
            save_path = save_path.rsplit('.', 1)[0] + '.pdf'

        plt.savefig(save_path,
                    format='pdf',
                    bbox_inches='tight',  # Ensures no labels are cut off
                    pad_inches=0.1,  # Adds small padding around the plot
                    dpi=300)  # High DPI for quality
    else:
        plt.show()

    # Close the figure to free memory
    plt.close()

def setup_plot_style():
    # Update plot to be LaTex friendly
    # plt.rcParams.update({
    #     "text.usetex": True,
    #     "font.family": "serif",
    #     "font.serif": ["Computer Modern Roman"],
    # })

    # Use a paper style
    plt.style.use('seaborn-v0_8-paper')

    # Increase font sizes
    plt.rcParams.update({
        'font.size': 14,          # Base font size
        'axes.titlesize': 16,     # Title font size
        'axes.labelsize': 14,     # Axis label size
        'xtick.labelsize': 12,    # X-axis tick label size
        'ytick.labelsize': 12,    # Y-axis tick label size
        'legend.fontsize': 12,    # Legend font size
        'figure.titlesize': 18    # Figure title size
    })

def human_readable_formatter(x, p):
    """Convert bytes to human readable string"""
    if x < 2**10:
        return f"{x:.0f}B"
    elif x < 2**20:
        return f"{x/2**10:.0f}KB"
    elif x < 2**30:
        return f"{x/2**20:.0f}MB"
    else:
        return f"{x/2**30:.0f}GB"

def truncate_string(text, max_length=20, suffix='...'):
    """Cuts off strings if they're too long"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_directory_size_histogram(directory_path, series_name="Generic", save_path=None):
    sizes = []
    names = []
    for file_name in os.listdir(directory_path):
        sizes.append(os.path.getsize(os.path.join(directory_path, file_name)))
        names.append(truncate_string(file_name, 15))

    print("name before", names)
    sizes, names = zip(*sorted(zip(sizes, names)))
    sizes = list(sizes)
    names = list(names)

    # Set up the plot
    setup_plot_style()
    plt.figure(figsize=(12, 6), dpi=300)

    # Create the bar plot
    # Using bar instead of hist to avoid interpolation
    print("labels", names)
    print("values", sizes)
    plt.bar(names, sizes, width=1, align='center')

    # Customize the plot
    plt.title(f"Size distribution of {series_name} dataset")
    plt.xlabel("Sample")
    plt.ylabel("File Size")
    plt.grid(True, axis='y', alpha=0.7)
    plt.yscale("log", base=2)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Set custom y-axis formatter
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(human_readable_formatter))

    # Save the plot
    save_plot(save_path)

def get_global_clusters_average_size(directory_path, save_path=None):
    # Get all directory names
    directories = os.listdir(directory_path)

    # For each cluster's average size box plot
    cluster_index = []
    size_dataset = []

    # For average file size per cluster

    for dir_name in directories:
        # Pattern matches "ClusterN_SizeX" and captures X
        match = re.match(r'Cluster\d+_Size(\d+)', dir_name)
        if match:
            index = match.group(0)
            cluster_index.append(str(index))

        file_sizes = []
        directory_files_path = os.path.join(directory_path, dir_name)
        directory_files = os.listdir(directory_files_path)
        for file in directory_files:
            size = os.path.getsize(os.path.join(directory_files_path, file))
            # file_sizes.append(size)
            size_dataset.append(size)

        # size_dataset.append(file_sizes)

    # Set up the plot
    setup_plot_style()
    plt.figure(figsize=(12, 6), dpi=300)

    # Create box plots
    plt.boxplot(
        size_dataset,
        # tick_labels=cluster_index,
    )

    # Customize the plot
    plt.title("Average File Size per Cluster")
    plt.xlabel("Cluster Index")
    plt.ylabel("File Size")
    plt.grid(True, axis='y', alpha=0.7)
    plt.yscale("log", base=2)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Set custom y-axis formatter
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(human_readable_formatter))

    # Save the plot
    save_plot(save_path)

def get_clusters_histogram(directory_path, save_path=None):
    # Get all directory names
    directories = os.listdir(directory_path)

    # For frequency histogram
    size_counts = {}
    bin_keys = []

    # For average file size per cluster

    for dir_name in directories:
        # Pattern matches "ClusterN_SizeX" and captures X
        match = re.match(r'Cluster\d+_Size(\d+)', dir_name)
        if match:
            size = int(match.group(1))
            if not str(size) in size_counts:
                size_counts[str(size)] = 0
                bin_keys.append(size)
            size_counts[str(size)] += 1

    # Sort sizes and counts for plotting
    # Converting to sorted lists to ensure proper ordering
    labels = [str(key) for key in sorted(bin_keys)]  # Sizes for x-axis
    frequencies = [size_counts[str(size)] for size in sorted(bin_keys)]  # Frequencies for y-axis

    # Set up the plot
    setup_plot_style()
    plt.figure(figsize=(12, 6), dpi=300)

    # Create the bar plot
    # Using bar instead of hist to avoid interpolation
    print("labels", labels)
    print("frequencies", frequencies)
    plt.bar(labels, frequencies, width=1, align='center')

    # Customize the plot
    plt.title("Distribution of Cluster Sizes")
    plt.xlabel("Cluster Size")
    plt.ylabel("Frequency")
    plt.grid(True, axis='y', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Save the plot
    save_plot(save_path)

def normalize_number_list(list, min_val, max_val):
    if not list:
        return []

    # Avoid division by zero if all numbers are the same
    if max_val == min_val:
        return [50] * len(list)  # Or another default value

    return [((x - min_val) / (max_val - min_val)) * 100 for x in list]

def plot_yara_metrics(box_plot_set, targeted_metric="TP", save_path=None, series_name="Generic", yscale="linear", file_count=0):
    setup_plot_style()

    # Set up the plot with higher DPI for better quality
    plt.figure(figsize=(12, 6), dpi=300)

    box_plot_data = []
    for algorithm, data in box_plot_set.items():
        box_plot_data.append(
            normalize_number_list(
                data[targeted_metric],
                0,
                file_count
            ) if targeted_metric == "TP" else data[targeted_metric]
        )

    # Create box plots
    plt.boxplot(
        box_plot_data,
        tick_labels=list(box_plot_set.keys()),
    )

    # Customize the plot
    if yscale == "log2":
        plt.yscale("log", base=2)
        tick_values = [1, 8, 16, 32, 64, 128, 256, 512, 1024]
        plt.yticks(tick_values, tick_values)

    if targeted_metric == "TP":
        plt.ylim(0, 105)

    plt.title(f"YARA Rules {targeted_metric} Distribution ({series_name} dataset)", pad=20)
    plt.ylabel("TP % Coverage" if targeted_metric == "TP" else targeted_metric)
    plt.grid(True, axis='y', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    save_plot(save_path)

def generate_fullscale_plots(box_plot_set, series_name, file_count, container_directory="graphs"):
    get_directory_size_histogram(
        get_project_path("input_testing", "malicious", "output_preprocessed", series_name),
        series_name=series_name,
        save_path=get_project_path("output", container_directory, series_name, f"Directory Size"),
    )

    for algorithm, dataset in box_plot_set.items(): # we just need this to get the list of metrics
        for metric, list in dataset.items():
            plot_yara_metrics(
                box_plot_set,
                targeted_metric=metric,
                save_path=get_project_path("output", container_directory, series_name, f"{metric}"),
                series_name=series_name,
                yscale='log2' if metric == "Gram Size" else 'linear',
                file_count=file_count,
            )
        break

def extract_box_plot(f, count=21):
    # Run function f() COUNT times and collect metrics for box plot visualization
    # count defaults to 21 to allow for a smooth median

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

    # Conditions per File Count: number of conditions per number of files
    # for small file count, it's fine if the number is 1, for large file sizes, values >= 1 might indicate overfitting or poor rule quality

    data_dict = {
        'TP': [],
        'Conditions Count': [],
        'Average Strings per Condition': [],
        'Average Condition Ratio': [],
        'Gram Size': [],
        'Strings Generated': [],
        'Estimated K': [],
        'Conditions per File Count': [],
    }

    # Collect data from multiple runs
    for i in range(count):
        yara_out = f()
        if not yara_out:
            for entry, list in data_dict.items():
                list.append(0 if entry != "Gram Size" else 1)
            continue

        # print("got rule", yara_out['output'])
        condition_ratios = []
        for i in range(len(yara_out['conditions_max'])):
            condition_ratios.append(yara_out['conditions_min'][i] / yara_out['conditions_max'][i])

        # Extract and store metrics
        data_dict['TP'].append(yara_out['TP'])
        data_dict['Conditions Count'].append(len(yara_out['conditions_max']))
        data_dict['Average Strings per Condition'].append(sum(yara_out['conditions_max']) / max(1, len(yara_out['conditions_max'])))
        data_dict['Average Condition Ratio'].append(sum(condition_ratios) / max(1, len(condition_ratios)))
        data_dict['Gram Size'].append(yara_out['gram_size'])
        data_dict['Strings Generated'].append(yara_out['strings'])
        data_dict['Estimated K'].append(yara_out['k_clusters'])
        data_dict['Conditions per File Count'].append(len(yara_out['conditions_max']) / yara_out['file_count'])

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
        bloom_filter_malicious_path = get_project_path("intermediate", "bloom_filters", "malicious-bytes")
        bloom_filter_benign_path = get_project_path("intermediate", "bloom_filters", "benign-bytes")

        file_count = count_files_in_directory(directory_path)
        box_plot_set = {}

        loaded_box_plot = load_box_plot_data(dataset_series, container_directory="kmeans")
        if loaded_box_plot:
            print(f"already generated results for {dataset_series}! skipping experiment... updating plots...")
            #generate_fullscale_plots(loaded_box_plot, dataset_series, file_count, container_directory="kmeans")
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
                    cluster_alg="KMeans",
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
        bloom_filter_malicious_path = get_project_path("intermediate", "bloom_filters", "malicious-bytes")
        bloom_filter_benign_path = get_project_path("intermediate", "bloom_filters", "benign-bytes")

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

    for dataset_series in ["Cluster2_Size100"] ["Cluster46_Size4", "Cluster10_Size10", "Cluster5_Size23", "Cluster3_Size53", "Cluster2_Size100", "Cluster0_Size134"] or list(reversed([
        "Cluster0_Size134",
        "Cluster1_Size111",
        "Cluster2_Size100",
        "Cluster3_Size53",
        "Cluster5_Size23",
        "Cluster10_Size10",
        "Cluster46_Size4",
    ])):
        directory_path = get_project_path("input_testing", "malicious", "output_preprocessed", dataset_series)
        bloom_filter_malicious_path = get_project_path("intermediate", "bloom_filters", "malicious-bytes")
        bloom_filter_benign_path = get_project_path("intermediate", "bloom_filters", "benign-bytes")

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
                selection_heuristic="AutoYara",
            )

        start_time = time.time()
        box_plot_set[f"Random(k={2})"] = extract_box_plot(random_cluster2, count=algorithm_tries)
        print(f"Completed Random(k={2})! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        box_plot_set[f"Random(k={random_k_estimate})"] = extract_box_plot(random_cluster, count=algorithm_tries)
        print(f"Completed Random(k={random_k_estimate})! Took {round(time.time() - start_time, 2)} seconds!")

        for threshold in [80, 90, 95]:
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

        for prune_factor in (50, 90):
            for threshold in [80, 81, 85, 92]:
                def augmented_DBSCAN():
                    return myYara.generate(
                        directory_path,
                        bloom_filter_malicious_path,
                        bloom_filter_benign_path,
                        bicluster_alg="SpectralCoCluster",
                        cluster_alg="AugmentedKMeansDBSCANSoft",
                        output_format="string",
                        similarity_threshold=threshold,
                        bicluster_feature_prune_coverage=prune_factor,
                    )

                start_time = time.time()
                box_plot_set[f'AugmentedKMeansSoft\nDBSCAN(similarity={threshold}, prune={prune_factor})'] = extract_box_plot(augmented_DBSCAN,
                                                                                                    count=algorithm_tries)
                print(f"Completed threshold={threshold}! Took {round(time.time() - start_time, 2)} seconds!")

        start_time = time.time()
        box_plot_set['VBGMM'] = extract_box_plot(vbgmm, count=algorithm_tries)
        print(f"Completed VBGMM! Took {round(time.time() - start_time, 2)} seconds!")

        print("PLOTTING", box_plot_set)
        save_box_plot_data(box_plot_set, dataset_series)
        generate_fullscale_plots(box_plot_set, dataset_series, file_count)

if __name__ == "__main__":
    print("starting test code")
    # demo_augmented_clustering()
    # demo_compare_kmeans_vbgmm_augmented()

    # demo_test_realworld()

    # get_clusters_histogram(
    #     get_project_path("input_testing", "malicious", "output_preprocessed"),
    #     save_path=get_project_path("output", "graphs", "supplementary_graphs", "cluster_histogram")
    # )
    # get_clusters_global_average_size(
    #     get_project_path("input_testing", "malicious", "output_preprocessed"),
    #     save_path=get_project_path("output", "graphs", "supplementary_graphs", "cluster_average_size")
    # )
    # eval_kmeans_sweep(algorithm_tries=21) # use an odd number so that the median doesn't have to be averaged

    eval_random_vs_vbgmm_vs_augmented(algorithm_tries=21) # use an odd number so that the median doesn't have to be averaged