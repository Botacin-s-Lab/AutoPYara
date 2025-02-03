import os

import yara
from sympy.series.sequences import SeqExpr
from AutoYara import AutoYara
from difflib import SequenceMatcher
from utils.clustering import cluster_files_LSH
import yaramod

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

def evaluate_rule(yara_file, rule_name):
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

def demo_train():
    myYara = AutoYara(ngram_top_k=100)

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
    myYara = AutoYara()
    print("Predictions:")
    yara_obj, output = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign")
    )
    print(output)


def demo_get_signatures():
    myYara = AutoYara(ngram_top_k=100)
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
    myYara = AutoYara()
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
    myYara = AutoYara()

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

def demo_compare_kmeans_vbgmm_augmented():
    myYara = AutoYara()

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

    evaluate_rule(yara_obj1, "Random")
    evaluate_rule(yara_obj2, "KMeans")
    evaluate_rule(yara_obj3, "VBGMM")
    evaluate_rule(yara_obj4, "AugmentedKMeansDBSCAN")

def demo_augmented_clustering():
    myYara = AutoYara()

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

def demo_test_evaluation():
    result = cluster_files_LSH(
        get_project_path("input_testing", "malicious", "mw2_lite"),
    )

    print(result)

if __name__ == "__main__":
    print("starting test code")
    demo_augmented_clustering()
    # demo_compare_kmeans_vbgmm_augmented()