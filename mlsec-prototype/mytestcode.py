import os
from sympy.series.sequences import SeqExpr
from AutoYara import AutoYara
from difflib import SequenceMatcher

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
    yara_obj, output = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster"
    )
    print(output)

    print("Predictions (spectral scaled):")
    yara_obj, output = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoClusterScale"
    )
    print(output)

def demo_kmeans_vs_VBGMM():
    myYara = AutoYara()

    print("Predictions (Random):")
    yara_obj, output1 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="Random"
    )
    print(output1)

    print("Predictions (KMeans):")
    yara_obj, output2 = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="KMeans"
    )
    print(output2)

    print("Predictions (VBGMM):")
    yara_obj, output3 = myYara.generate(
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

def demo_test_augmented_kmeans():
    myYara = AutoYara()

    print("Predictions (AugmentedKMeans):")
    yara_obj, yara_string = myYara.generate(
        get_project_path("input_testing", "malicious", "mw2_lite"),
        get_project_path("intermediate", "bloom_filters", "malicious"),
        get_project_path("intermediate", "bloom_filters", "benign"),
        bicluster_alg="SpectralCoCluster",
        cluster_alg="VBGMM",
        predictor_labels= [0] * 11
    )
    print("yara object:", yara_obj)
    print("yara string:", yara_string)

if __name__ == "__main__":
    print("starting test code")
    demo_test_augmented_kmeans()