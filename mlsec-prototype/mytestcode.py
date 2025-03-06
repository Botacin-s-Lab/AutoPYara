import os
import json
import re
import math
import time

import yara
#from CommandNotFound.db.creator import measure
from sympy import ceiling
from sympy.series.sequences import SeqExpr
from sympy.strategies.branch import condition
import matplotlib.pyplot as plt
import numpy as np

from AutoPYara import AutoPYara
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

def load_box_plot_data_from_file(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No saved data found at: {filename}")
        return None

def load_box_plot_data(dataset_series, container_directory="graphs"):
    filename = get_project_path("output", container_directory, dataset_series, "Evaluation Results.json")

    return load_box_plot_data_from_file(filename)

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

def get_rule_fp_bar(box_plot_set, series_name="Generic", save_path=None):
    fp_global = []
    fp_small = []
    fp_medium = []
    fp_large = []

    fp_global_good = []

    label_algorithm = []

    width = 0.2

    def average(list):
        return sum(list) / len(list)

    for algorithm, dataset in box_plot_set.items(): # we just need this to get the list of metrics
        fp_global.append(average(dataset['FP Labeled Global (malware)']))
        fp_small.append(average(dataset['FP Labeled Small (malware)']))
        fp_medium.append(average(dataset['FP Labeled Medium (malware)']))
        fp_large.append(average(dataset['FP Labeled Large (malware)']))
        fp_global_good.append(average(dataset['FP Labeled Global (benign)']))
        label_algorithm.append(algorithm)

    # Set up the plot
    setup_plot_style()

    # malicious bar graph
    plt.figure(figsize=(12, 6), dpi=300)

    x = np.arange(len(label_algorithm))
    plt.bar(x-width*0.75, fp_small, width=width*0.5)
    plt.bar(x-width*0.25, fp_medium, width=width*0.5)
    plt.bar(x+width*0.25, fp_large, width=width*0.5)
    plt.bar(x+width*0.75, fp_global, width=width*0.5)

    # Customize the plot
    plt.title(f"Malicious FP: {series_name}")
    plt.xlabel("Samples")
    plt.ylabel("Average FP")
    plt.grid(True, axis='y', alpha=0.7)
    plt.xticks(x, label_algorithm)
    plt.legend(["Small", "Medium", "Large", "Global Malware"])

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Save the plot
    save_plot(save_path + " Malicious")

    # benign bar graph
    plt.figure(figsize=(12, 6), dpi=300)

    x = np.arange(len(label_algorithm))
    plt.bar(x, fp_global_good, width=width)

    # Customize the plot
    plt.title(f"Benign FP: {series_name}")
    plt.xlabel("Samples")
    plt.ylabel("Average FP")
    plt.grid(True, axis='y', alpha=0.7)
    plt.xticks(x, label_algorithm)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Save the plot
    save_plot(save_path + " Benign")

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
    bars = plt.bar(labels, frequencies, width=1, align='center')

    # Customize the plot
    plt.title("Distribution of Cluster Sizes")
    plt.xlabel("Cluster Size")
    plt.ylabel("Frequency")
    plt.grid(True, axis='y', alpha=0.7)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height,
                f'{height}',
                ha='center', va='bottom')

    # Rotate x-axis labels for better readability
    # plt.xticks(rotation=90)

    # Save the plot
    save_plot(save_path)

def normalize_number_list(list, min_val, max_val):
    if not list:
        return []

    # Avoid division by zero if all numbers are the same
    if max_val == min_val:
        return [50] * len(list)  # Or another default value

    return [((x - min_val) / (max_val - min_val)) * 100 for x in list]

def plot_yara_metrics(box_plot_set, targeted_metric="TP", save_path=None, series_name="Generic", yscale="linear", file_count=0, measure_fp=False):
    if not measure_fp and re.match("FP Label", targeted_metric):
        return

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

        ticks = [1, 8, 16, 32, 64, 128, 256, 512, 1024]
        plt.yticks(ticks, [str(i) for i in ticks])

    #if targeted_metric == "TP":
        #plt.ylim(0, 105)

    plt.title(f"YARA Rules {targeted_metric} Distribution ({series_name} dataset)", pad=20)
    plt.ylabel("TP % Coverage" if targeted_metric == "TP" else "Execution Time (s)" if targeted_metric == "Execution Time" else targeted_metric)
    plt.grid(True, axis='y', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    save_plot(save_path)

def plot_yara_metrics_bar(box_plot_set, targeted_metric="TP", save_path=None, series_name="Generic", yscale="linear", file_count=0, measure_fp=False):
    if not measure_fp and re.match("FP Label", targeted_metric):
        return

    setup_plot_style()

    # Set up the plot with higher DPI for better quality
    plt.figure(figsize=(12, 6), dpi=300)

    box_plot_data = []
    for algorithm, data in box_plot_set.items():
        value_list = normalize_number_list(
                data[targeted_metric],
                0,
                file_count
            ) if targeted_metric == "TP" else data[targeted_metric]

        box_plot_data.append(sum(value_list) / len(value_list))

    # Create box plots
    plt.bar(
        box_plot_set.keys(), box_plot_data,
    )

    # Customize the plot
    if yscale == "log2":
        plt.yscale("log", base=2)
        plt.yticks([1, 8, 16, 32, 64, 128, 256, 512, 1024])

    #if targeted_metric == "TP":
        #plt.ylim(0, 105)

    plt.title(f"YARA Rules {targeted_metric} Distribution ({series_name} dataset)", pad=20)
    plt.ylabel("TP % Coverage" if targeted_metric == "TP" else targeted_metric)
    plt.grid(True, axis='y', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    save_plot(save_path)

def generate_fullscale_plots(box_plot_set, series_name, file_count, container_directory="graphs", measure_fp=False):
    get_directory_size_histogram(
        get_project_path("input_testing", "malicious", "output_preprocessed", series_name),
        series_name=series_name,
        save_path=get_project_path("output", container_directory, series_name, f"Directory Size"),
    )

    if measure_fp:
        get_rule_fp_bar(
            box_plot_set,
            series_name=series_name,
            save_path=get_project_path("output", container_directory, series_name, f"FP Bar"),
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
                measure_fp=measure_fp,
            )
        break

def test_rule(yara_python_rule, directory, exe_only=True):
    # Runs the rule on all samples in a directory
    matches = 0
    total = 0

    for sample_directory in os.listdir(directory):
        if exe_only and sample_directory.endswith(".exe") or not exe_only:
            match = yara_python_rule.match(os.path.join(directory, sample_directory))
            total += 1
            if match:
                matches += 1

    # print(directory, "matched", matches, "out of", total)
    return matches/total

def extract_box_plot(f, dataset_series=None, count=21, measure_fp=False, use_k=None):
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

    # FP Labeled ...: how the rule performed on labeled malware/goodware it was not supposed to detect
    # ideally, should be 0 for all
    # in practice, FPs tend to be higher for other malware files (~1%), FPs tend to be low (<0.1%) for benign files

    data_dict = {
        'TP': [],
        'Conditions Count': [],
        'Average Strings per Condition': [],
        'Average Condition Ratio': [],
        'Gram Size': [],
        'Strings Generated': [],
        'Estimated K': [],
        'Conditions per File Count': [],

        'FP Labeled Large (malware)': [], # family sizes of 25+
        'FP Labeled Medium (malware)': [], # family sizes 6-25
        'FP Labeled Small (malware)': [], # family sizes of 5 or less
        'FP Labeled Global (malware)': [], # compare against all malware family sizes
        'FP Labeled Global (benign)': [], # compare against benign exe files

        'Execution Time': [], # compare against benign exe files
    }

    # Collect data from multiple runs
    for i in range(count):
        start_time = time.time()
        if use_k:
            yara_out = f(use_k[i])
        else:
            yara_out = f()

        if i > 0: # we don't consider the first run since it extract bytes and caches them
            data_dict['Execution Time'].append(time.time() - start_time)

        if not yara_out:
            for entry, list in data_dict.items():
                list.append(0 if entry != "Gram Size" else 1)
            continue

        if dataset_series and measure_fp:
            yara_rule = yara_out['output']

            goodware_file_list = get_project_path("input_testing", "benign", "goodware")
            for validation_dataset in os.listdir(goodware_file_list):
                ratio = test_rule(yara_python_rule=yara_rule, directory=os.path.join(goodware_file_list, validation_dataset))
                data_dict['FP Labeled Global (benign)'].append(ratio)

            malware_file_list = get_project_path("input_testing", "malicious", "output_preprocessed")
            for validation_dataset in os.listdir(malware_file_list):
                if validation_dataset == dataset_series:
                    continue # we don't validate with ourself

                match = re.match(r'Cluster(\d+)_Size(\d+)', validation_dataset)
                if match:
                    id = int(match.group(1))
                    size = int(match.group(2))
                    if size <= 2 or id < 0:
                        continue # we don't test on small datasets or the mega 7k dataset

                    ratio = test_rule(yara_python_rule=yara_rule, directory=os.path.join(malware_file_list, validation_dataset))

                    data_dict['FP Labeled Global (malware)'].append(ratio)
                    if size <= 5:
                        data_dict['FP Labeled Small (malware)'].append(ratio)
                    elif size <= 25:
                        data_dict['FP Labeled Medium (malware)'].append(ratio)
                    else:
                        data_dict['FP Labeled Large (malware)'].append(ratio)

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
        bloom_filter_malicious_path = get_project_path("intermediate", "bloom_filters", "malicious-bytes")
        bloom_filter_benign_path = get_project_path("intermediate", "bloom_filters", "benign-bytes")

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

def merge_dictionaries(parent_dict, child_dict):
    for key, value in child_dict:
        if not key in parent_dict:
            parent_dict[key] = value
        elif isinstance(value, list):
            parent_dict[key] += value
        elif isinstance(value, dict):
            merge_dictionaries(parent_dict[key], value)
        else:
            print("merge anomaly! expected a list or a dictionary", key, value)

def normalize_data(data, file_count):
    for algorithm, result in data.items():
        for metric, list in result.items():
            result[metric] = normalize_number_list(
                result[metric],
                0,
                file_count
            ) if metric == "TP" else result[metric]

def get_all_results(parent_directory):
    global_plot = {}

    for cluster_directory in os.listdir(parent_directory):
        match = re.match(r'Cluster(\d+)_Size(\d+)', cluster_directory)
        if match:
            cluster_id = int(match.group(1))
            file_count = int(match.group(2))

            full_cluster_directory = os.path.join(parent_directory, cluster_directory)
            for file in os.listdir(full_cluster_directory):
                if file.endswith(".json"):
                    file_path = os.path.join(full_cluster_directory, file)
                    data = load_box_plot_data_from_file(file_path)

                    normalize_data(data, file_count)
                    global_plot[full_cluster_directory] = {
                        'data': data,
                        'cluster_name': cluster_directory,
                        'cluster_id': cluster_id,
                        'file_count': file_count,
                    }

    return global_plot

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

if __name__ == "__main__":
    print("starting test code")


    yara = AutoPYara()
    bloom_filter_malicious_path = get_project_path("intermediate", "bloom_filters", "malicious-bytes")
    bloom_filter_benign_path = get_project_path("intermediate", "bloom_filters", "benign-bytes")

    print("result", yara.generate(
        get_project_path("input_testing", "malicious", "output_preprocessed", "Cluster5_Size23"),
        bloom_filter_malicious_path,
        bloom_filter_benign_path,
        bicluster_alg="SpectralCoCluster",
        cluster_alg="AugmentedKMeansDBSCANSoft",
        output_format="yara-python",
        augmented_target_k=4,
    ))
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
    # eval_cross_validation(algorithm_tries=21) # use an odd number so that the median doesn't have to be averaged

    eval_random_vs_vbgmm_vs_augmented(algorithm_tries=21)

    # eval_get_global_averages_akms_vbgmm_bestk()
    # eval_get_k_difference()
    # eval_get_global_averages_akms_vbgmm()