import jpype
import jpype.imports
from jpype.types import *
import os
import gc

from sympy.series.sequences import SeqExpr

from AutoYara import AutoYara
from difflib import SequenceMatcher

# parent directory containing folders input_testing, input_training, intermediate, output
home = os.path.expanduser("~")
parent_directory = os.path.join(home, "Desktop/github-mlsec-python/CapyMOASec/mlsec-prototype")
# parent_directory = "/home/vboxuser/Desktop/github-mlsec-python/CapyMOASec/mlsec-prototype"

def from_directory(subdirectory):
    return parent_directory + "/" + subdirectory

def demo_train_and_predict_debug():
    # this demo is used to debug the train/predict pipeline (WIP)
    myYara = AutoYara(top_k=100)

    for i in [8, 16]: # n-grams
        myYara.print_memory_usage("MEMORY BEFORE")
        myYara.train(from_directory("input_training/benign"), from_directory("intermediate/bloom_filters/benign"),
                     ngram_size=i)
        myYara.print_memory_usage("MEMORY AFTER")
        print("Forcing garbage collection...")
        gc.collect()
        jpype.java.lang.System.gc()

        myYara.print_memory_usage()
        myYara.train(from_directory("input_training/malicious"), from_directory("intermediate/bloom_filters/malicious"),
                     ngram_size=i)
        print(f"completed training of n-gram {i}")
        gc.collect()
        jpype.java.lang.System.gc()

    myYara = AutoYara()
    print("Predictions:")
    output = myYara.generate(from_directory("input_testing/malicious"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"))
    print(output)

def demo_train():
    # this example shows how to generate new bloom files (WIP)
    myYara = AutoYara(top_k=100)

    for i in [8, 16]: # n-grams
        myYara.train(from_directory("input_training/benign/gw1_lite"), from_directory("intermediate/bloom_filters/benign"),
                     ngram_size=i)
        myYara.train(from_directory("input_training/malicious/mw1_lite"), from_directory("intermediate/bloom_filters/malicious"),
                     ngram_size=i)

def demo_predict():
    # this example shows how to generate new yara rules (WIP)
    myYara = AutoYara()
    print("Predictions:")
    output = myYara.generate(from_directory("input_testing/malicious/mw2"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"))
    print(output)


def demo_get_signatures():
    # this example shows how to retrieve the n-gram byte candidates selected (WIP)
    myYara = AutoYara(top_k=100)
    myList = myYara.build_candidate_set(from_directory("input_testing/malicious/mw2_lite"),
                                        from_directory("intermediate/bloom_filters/malicious"),
                                        from_directory("intermediate/bloom_filters/benign"), ngram_size=8)

    # Now candidate_dicts is a list of Python dictionaries
    for candidate_dict in myList:
        # You can work with each candidate_dict as a normal Python dictionary
        print(candidate_dict['signature'])
        print(candidate_dict['b_fp'])

def demo_select_bicluster():
    # this demonstrates how bicluster selection works
    myYara = AutoYara()
    print("Predictions (spectral):")
    output = myYara.generate(from_directory("input_testing/malicious/mw2_lite"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"), bicluster_alg="SpectralCoCluster")
    print(output)

    print("Predictions (spectral scaled):")
    output = myYara.generate(from_directory("input_testing/malicious/mw2_lite"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"), bicluster_alg="SpectralCoClusterScale")
    print(output)

def demo_compare_new_old():
    # compare results between new autoyara and old
    # Note: we route the legacy call to the new pipeline
    # for a true legacy call to the original AutoYara, please download AutoYara and call it via CLI

    myYara = AutoYara()
    print("Predictions (new):")
    output = myYara.generate(from_directory("input_testing/malicious/mw2"),
                    from_directory("intermediate/bloom_filters/malicious-bytes"),
                    from_directory("intermediate/bloom_filters/benign-bytes"))
    print(output)

    print("Predictions (legacy):")
    output = myYara.generate(from_directory("input_testing/malicious/mw2"),
                    from_directory("intermediate/bloom_filters/malicious-bytes"),
                    from_directory("intermediate/bloom_filters/benign-bytes"), bicluster_alg="SpectralCoCluster", cluster_alg="VBGMM")
    print(output)

def demo_kmeans_vs_VBGMM():
    # use spectral coclustering with kmeans or VBGMM for comparison
    # the demo will output a score betwen 0-1 for similiarity between the output of the two methods

    myYara = AutoYara()

    print("Predictions (Random):")
    output1 = myYara.generate(from_directory("input_testing/malicious/mw2_lite"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"), bicluster_alg="SpectralCoCluster", cluster_alg="Random")
    print(output1)

    print("Predictions (KMeans):")
    output2 = myYara.generate(from_directory("input_testing/malicious/mw2_lite"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"), bicluster_alg="SpectralCoCluster", cluster_alg="KMeans")
    print(output2)

    print("Predictions (VBGMM):")
    output3 = myYara.generate(from_directory("input_testing/malicious/mw2_lite"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"), bicluster_alg="SpectralCoCluster", cluster_alg="VBGMM")
    print(output3)

    print("Output similarity (Random vs KMeans):", SequenceMatcher(None, output1, output2).ratio())
    print("Output similarity (Random vs VBGMM): ", SequenceMatcher(None, output1, output3).ratio())
    print("Output similarity (KMeans vs VBGMM): ", SequenceMatcher(None, output2, output3).ratio())

print("starting test code")
demo_kmeans_vs_VBGMM()
