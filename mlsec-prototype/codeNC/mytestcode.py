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
import numpy as np

from AutoPYara import AutoPYara
from difflib import SequenceMatcher
#from utils.clustering import cluster_files_LSH
#import yaramod
#import random


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


if __name__ == "__main__":
    print("starting test code")

    yara = AutoPYara()
    bloom_filter_malicious_path = "/usr/src/app/intermediate/bloom_filters/malicious-bytes" #get_project_path("intermediate", "bloom_filters", "malicious-bytes")
    bloom_filter_benign_path = "/usr/src/app/intermediate/bloom_filters/benign-bytes"#get_project_path("intermediate", "bloom_filters", "benign-bytes")

    print("result", yara.generate(
        "/usr/src/app/Honeypots",
        bloom_filter_malicious_path,
        bloom_filter_benign_path,
        bicluster_alg="SpectralCoCluster",
        cluster_alg="AugmentedKMeansDBSCANSoft",
        output_format="yara-python",
        augmented_target_k=4,
    ))
    # yara = AutoPYara()
    # bloom_filter_malicious_path = "/usr/src/app/intermediate/bloom_filters/malicious-bytes/"
    # bloom_filter_benign_path = "/usr/src/app/intermediate/bloom_filters/benign-bytes/"

    # print("result", yara.generate(
    #     get_project_path("input_testing", "malicious", "output_preprocessed", "Cluster5_Size23"),
    #     bloom_filter_malicious_path,
    #     bloom_filter_benign_path,
    #     bicluster_alg="SpectralCoCluster",
    #     cluster_alg="AugmentedKMeansDBSCANSoft",
    #     output_format="yara-python",
    #     augmented_target_k=4,
    # ))
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

   #eval_random_vs_vbgmm_vs_augmented(algorithm_tries=21)

    # eval_get_global_averages_akms_vbgmm_bestk()
    # eval_get_k_difference()
    # eval_get_global_averages_akms_vbgmm()