import os

import statistics 
import argparse

import csv
import yara
from sympy import ceiling
from sympy.series.sequences import SeqExpr
from sympy.strategies.branch import condition
import matplotlib.pyplot as plt
import numpy as np

from AutoPYara import AutoPYara
from difflib import SequenceMatcher
import sys
from tqdm import tqdm
sys.path.append(os.path.abspath('./utils')) 
from utils.utils import str2bool,extract_tp_rate
from statistics import StatisticsError



# Ensure content is serializable
def serialize(obj):
    """Convert non-serializable objects to JSON-friendly formats."""
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize(v) for v in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)  # Convert unknown objects to string
def main(opts):
    if opts.generateRule:  # Simplified True check
        print("LOG:-----------------------------------RULE GENERATION SELECTED")
        print("LOG:-----------------------------------RULE Type: ",opts.ruleOutputType)

        print("LOG:-----------------------------------BUILDING OBJECT")
        yara_instance = AutoPYara()

        print("LOG:-----------------------------------Bicluster Algorithm: ",opts.biclusterAlgorithmType)
        print("LOG:-----------------------------------Cluster Algorithm: ",opts.clusterAlgorithm)
        print("LOG:-----------------------------------Using K Value : ",opts.augmentedTarget_k)

        #Generate content
        content = yara_instance.generate(
            opts.malwarePath,
            opts.bfMalicious,
            opts.bfBenign,
            bicluster_alg=opts.biclusterAlgorithmType,
            cluster_alg=opts.clusterAlgorithm,
            output_format=opts.ruleOutputType,
            augmented_target_k=opts.augmentedTarget_k,output_dir=opts.outputDirectory
        )
    else: 
        print("LOG:-----------------------------------EVALUTAION SELECTED")
        print("LOG:-----------------------------------RULE Type: ",opts.ruleOutputType)

        print("LOG:-----------------------------------BUILDING OBJECT")
       

        print("LOG:-----------------------------------Bicluster Algorithm: ",opts.biclusterAlgorithmType)
        print("LOG:-----------------------------------Cluster Algorithm: ",opts.clusterAlgorithm)
        print("LOG:-----------------------------------Using K Value : ",opts.augmentedTarget_k)
        augmented_target_k=opts.augmentedTarget_k
        print("LOG:-----------------------------------Getting K Values: ",augmented_target_k)
        
        #Minomi Sampling
        MetricArray=[]
        stopmetric=10
        threshold=5
        prs=None
        os.makedirs(opts.outputDirectory, exist_ok=True)
        csv_path = os.path.join(opts.outputDirectory, "k_values.csv")
        print("LOG:-----------------------------------CSV PATH SET",csv_path)
        if not os.path.exists(csv_path):
            print("LOG:-----------------------------------CREATING",csv_path)

            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['k_clusters', 'run_number'])  # Header row
        else:
            print("LOG:-----------------------------------CSV Already Exsist",csv_path)

        for i in tqdm(range(100)):
            # ktarget_kval=augmented_target_k[i]
            Flag=False
            path=(os.path.join(opts.outputDirectory,str(i+1)))
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                Flag=True
            # existing_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            if Flag==True:
                if i==0:
                    yara_instance = AutoPYara()
                if augmented_target_k is not None:
                    print("LOG:-----------------------------------Using K Value : ",ktarget_kval)
                    # a = yara_instance.generate(
                    #     opts.malwarePath,
                    #     opts.bfMalicious,
                    #     opts.bfBenign,
                    #     bicluster_alg=opts.biclusterAlgorithmType,
                    #     cluster_alg=opts.clusterAlgorithm,
                    #     output_format=opts.ruleOutputType,output_dir=path,
                    #     augmented_target_k=ktarget_kval, 
                    #     bicluster_feature_prune_coverage=50,
                    #     selection_heuristic="PYara",
                    # )
                    exit()
                else:
                    
                    a = yara_instance.generate(
                        opts.malwarePath,
                        opts.bfMalicious,
                        opts.bfBenign,
                        bicluster_alg=opts.biclusterAlgorithmType,
                        cluster_alg=opts.clusterAlgorithm,
                        output_format=opts.ruleOutputType,output_dir=path,
                        bicluster_feature_prune_coverage=50,
                        selection_heuristic="AutoYara",
                    )
                # Append k_clusters and run number to CSV
                if a is not None and "k_clusters" in a:  # Check if a is valid and has k_clusters
                    print(f"Run {i+1}: k_clusters = {a['k_clusters']}")
                    # Append k_clusters and run number to CSV
                    with open(csv_path, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([a["k_clusters"], str(i+1)])
                else:
                    print(f"Run {i+1}: Warning - generate() returned None or missing k_clusters")
                    # Optionally log this failure to the CSV with a placeholder
                    with open(csv_path, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(["FAILED", str(i+1)])
                try:
                    file = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                    Check=(os.path.join(path,file[0]))
                    tp=extract_tp_rate(Check)
                except:
                    tp=0
                    print("COULD NOT GENERATE RULE SETTING TP To 0")
            else:
                print("PAST RUN FOUND.. LOADING PRECOMPUTED")
                try:
                    file = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                    Check=(os.path.join(path,file[0]))
                    tp=extract_tp_rate(Check)
                except:
                    tp=0
                    print("COULD NOT GENERATE RULE SETTING TP To 0")

            MetricArray.append(tp)
            if len(MetricArray) >= stopmetric:
                try:
                    var = statistics.stdev(MetricArray)
                except statistics.StatisticsError:
                    var = 0
                
                print("LOG:-----------------------------------STD: ", var)
                
                if prs is not None and abs(prs - var) < threshold:
                    print("LOG:-----------------------------------EARLY STOPPING: ", var)
                    break
                else:
                    stopmetric += 5
                    threshold *= 1.25
                    print("LOG:-----------------------------------STOP METRIC INCREASED: ", stopmetric)
                    print("LOG:-----------------------------------THRESHOLD INCREASED: ", threshold)

                prs = var  # update prs after comparison
        print("LOG:-----------------------------------STD: ",var)                
    return 0 


def parseArgs(argv):
    parser = argparse.ArgumentParser(description="Parse command-line arguments for malware analysis.")

    parser.add_argument('-bfM', '--bfMalicious', type=str, required=True, help='Path to Malicious Bloom Filter.')
    parser.add_argument('-bfB', '--bfBenign', type=str, required=True, help='Path to Benign Bloom Filter.')
    parser.add_argument('-mP', '--malwarePath', type=str, required=True, help='Path to Malicious Files.')
    parser.add_argument('-gR', '--generateRule', type=str2bool, default=False, help='Toggle Rule Generation (True/False, default: False).')
    parser.add_argument( '-bCT', '--biclusterAlgorithmType',choices={'SpectralCoCluster', 'SpectralCoClusterScale'},required=True,help='Bicluster algorithm type: SpectralCoCluster or SpectralCoClusterScale')

    parser.add_argument(
        '-cA', '--clusterAlgorithm',
        choices={
            'VBGMM',
            'KMeans',
            'KMeansSoft',
            'Random',
            'AugmentedKMeansDBSCAN',
            'AugmentedKMeansDBSCANSoft',
            'AugmentedKMeansVT',
            'AugmentedKMeansVTSoft'
        },
        required=True,
        help='Cluster algorithm: VBGMM, KMeans, KMeansSoft, Random, '
            'AugmentedKMeansDBSCAN, AugmentedKMeansDBSCANSoft, '
            'AugmentedKMeansVT, or AugmentedKMeansVTSoft'
    )

    #SelectionHeuristic = "PYara", AutoYara
    parser.add_argument( '-rOT', '--ruleOutputType',choices={'yara-python', 'yaramod', 'string'},required=True,help='Output Rule Format')
    parser.add_argument('-k', '--augmentedTarget_k', type=int, nargs='*', default=None)    
    parser.add_argument('-o', '--outputDirectory', type=str, required=True, help='Directory for output.')
 
    if argv is None:
        opts = parser.parse_args()
    else:
        opts = parser.parse_args(argv)
    
    # If malwarePath contains commas, split it into a list
    if ',' in opts.malwarePath:
        opts.malwarePath = [path.strip() for path in opts.malwarePath.split(',')]
    
    return opts
if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    print(opts)
    main(opts)