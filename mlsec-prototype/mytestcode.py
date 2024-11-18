import jpype
import jpype.imports
from jpype.types import *
import os
import gc
from AutoYara import AutoYara

# parent directory containing folders input_testing, input_training, intermediate, output
parent_directory = "/home/vboxuser/Desktop/github-mlsec-python/CapyMOASec/mlsec-prototype"

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
    myYara.generate(from_directory("input_testing/malicious"), from_directory("output"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"))

def demo_train():
    # this example shows how to generate new bloom files (WIP)
    myYara = AutoYara(top_k=100)

    for i in [8, 16]: # n-grams
        myYara.train(from_directory("input_training/benign/gw1_lite"), from_directory("intermediate/bloom_filters/benign"),
                     ngram_size=i)
        myYara.train(from_directory("input_training/malicious/mw1_lite"), from_directory("intermediate/bloom_filters/malicious"),
                     ngram_size=i)

def demo_predict():
    # this example shows how to genreate new yara rules (WIP)
    myYara = AutoYara()
    print("Predictions:")
    myYara.generate(from_directory("input_testing/malicious/mw2_lite"), from_directory("output"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"))


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
    myYara.generate(from_directory("input_testing/malicious/mw2_lite"), from_directory("output/spectral"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"), bicluster_alg="SpectralCoCluster")

    print("Predictions (spectral scaled):")
    myYara.generate(from_directory("input_testing/malicious/mw2_lite"), from_directory("output/spectral_scaled"),
                    from_directory("intermediate/bloom_filters/malicious"),
                    from_directory("intermediate/bloom_filters/benign"), bicluster_alg="SpectralCoClusterScale")

print("starting test code")
demo_get_signatures()
