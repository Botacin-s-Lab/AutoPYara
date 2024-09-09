import jpype
import jpype.imports
from jpype.types import *
import os
import gc

# parent directory containing folders input_testing, input_training, intermediate, output
parent_directory = "/home/nick/Desktop/github mlsec-prototype/CapyMOASec/mlsec-prototype"

# directory containing the autoyara jar file, i recommend to point it directly to the maven package output location
autoyara_jar_directory = "/home/nick/Desktop/github mlsec-java/CapyMOASec/target/AutoYara-1.0-SNAPSHOT.jar"#"AutoYara-1.0-SNAPSHOT.jar"

# Function to start JVM
def start_jvm():
    jvm_options = [
        "-Xmx14g",
        #"-verbose:gc",
        #"-XX:+PrintGCDetails",
        "-XX:+HeapDumpOnOutOfMemoryError",
        "-XX:HeapDumpPath=src/python/heapdump",
    ]

    jpype.startJVM(
        classpath=[autoyara_jar_directory],
        convertStrings=True, *jvm_options)
    global AutoYara, MemoryMonitor
    import AutoYara
    MemoryMonitor = jpype.JClass("edu.lps.acs.ml.autoyara.MemoryMonitor")

# Function to shutdown JVM
def shutdown_jvm():
    if jpype.isJVMStarted():
        jpype.shutdownJVM()

def print_memory_usage(label="Memory"):
    used_memory = MemoryMonitor.getUsedMemory() / (1024 * 1024)  # Convert to MB
    free_memory = MemoryMonitor.getFreeMemory() / (1024 * 1024)  # Convert to MB
    total_memory = MemoryMonitor.getTotalMemory() / (1024 * 1024)  # Convert to MB
    max_memory = MemoryMonitor.getMaxMemory() / (1024 * 1024)  # Convert to MB
    print(f"{label}")
    print(f"\tUsed Memory: {used_memory:.2f} MB")
    print(f"\tFree Memory: {free_memory:.2f} MB")
    print(f"\tTotal Memory: {total_memory:.2f} MB")
    print(f"\tMax Memory: {max_memory:.2f} MB")

def fromDirectory(subdirectory):
    return parent_directory + "/" + subdirectory

def train(myYara=None):
    if myYara is None:
        myYara = AutoYara.AutoYara(top_k=100)

    for i in [8, 16]: # n-grams
        print_memory_usage("MEMORY BEFORE")
        myYara.train(fromDirectory("input_training/benign"), fromDirectory("intermediate/bloom_filters/benign"),
                     ngram_size=i)
        print_memory_usage("MEMORY AFTER")
        print("Forcing garbage collection...")
        gc.collect()
        jpype.java.lang.System.gc()

        print_memory_usage()
        myYara.train(fromDirectory("input_training/malicious"), fromDirectory("intermediate/bloom_filters/malicious"),
                     ngram_size=i)
        print(f"completed training of n-gram {i}")
        gc.collect()
        jpype.java.lang.System.gc()

def predict(myYara=None):
    if myYara is None:
        myYara = AutoYara.AutoYara(top_k=100)

    print("Predictions:")
    myYara.predict(fromDirectory("input_testing/malicious"), fromDirectory("output"),
                   fromDirectory("intermediate/bloom_filters/malicious"),
                   fromDirectory("intermediate/bloom_filters/benign"))

def train_and_predict(myYara=None):
    if myYara is None:
        myYara = AutoYara.AutoYara(top_k=100)

    train(myYara)
    predict(myYara)

def get_signature(myYara=None):
    if myYara is None:
        myYara = AutoYara.AutoYara(top_k=100)

    myList = myYara.buildCandidateSet(fromDirectory("input_testing/malicious/mw2_lite"),
                   fromDirectory("intermediate/bloom_filters/malicious"),
                   fromDirectory("intermediate/bloom_filters/benign"))

    myPyList = list(myList)
    for sigCandidateJavaObject in myList:
        print(sigCandidateJavaObject.getSignature())

def main():
    start_jvm()
    #train_and_predict()
    print("starting test code")

    myYara = AutoYara.AutoYara(top_k=100)

    train(myYara)
    predict(myYara)
    get_signature(myYara)

    print("test code ran, shutting down jvm")
    shutdown_jvm()

main()