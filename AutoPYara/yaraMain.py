import os

import statistics 
import argparse
import shutil

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
import random


def FUNCTIONHARDK(opts):
    Ksearch = []
    target_size = 10

    if opts.HardKPike:
        print("LOG:-----------------------------------Need to find K")
        Ksearch = random.sample(range(0, 21), target_size)
    else:
        augmented_target_k = opts.augmentedTarget_k
        print("LOG:-----------------------------------Getting K Values: ", augmented_target_k)

        kmin = min(augmented_target_k)
        kmax = max(augmented_target_k)

        # Step 1: Add all integers from kmin to kmax inclusive
        Ksearch = list(range(kmin, kmax + 1))

        # Step 2: Add values alternately to the left and right until Ksearch reaches target_size
        left = kmin - 1
        right = kmax + 1

        while len(Ksearch) < target_size:
            if left > 0:
                Ksearch.insert(0, left)
                left -= 1
                if len(Ksearch) == target_size:
                    break
            Ksearch.append(right)
            right += 1

    print("Final Ksearch:", Ksearch)
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



    for i in tqdm(range(target_size)):
        ktarget_kval=Ksearch[i]
        path=(os.path.join(opts.outputDirectory,str(i+1)+"_"+"iKsearch"))
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        # existing_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if i==0:
            yara_instance = AutoPYara()
        print("LOG:-----------------------------------Using K Value : ",ktarget_kval)
        a = yara_instance.generate(
            opts.malwarePath,
            opts.bfMalicious,
            opts.bfBenign,
            bicluster_alg=opts.biclusterAlgorithmType,
            cluster_alg=opts.clusterAlgorithm,
            output_format=opts.ruleOutputType,output_dir=path,
            augmented_target_k=ktarget_kval, 
            bicluster_feature_prune_coverage=50,
            selection_heuristic="PYara",
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

    # Store TP and K pairs for sorting
    k_tp_pairs = []
    f=True
    print("LOG:-----------------------------------Finding Best K")
    # Iterate through the Ksearch values and find the highest TP
    for i in tqdm(range(target_size)):
        ktarget_kval = Ksearch[i]
        path = os.path.join(opts.outputDirectory, str(i + 1) + "_" + "iKsearch")

        try:
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            tp_list = []

            for f in files:
                check_path = os.path.join(path, f)
                try:
                    tp_val = extract_tp_rate(check_path)
                except:
                    tp_val = 0
                tp_list.append(tp_val)

            tp = max(tp_list) if tp_list else 0
            
        except Exception as e:
            tp = 0
            f = False
            print(f"COULD NOT GENERATE RULE FOR {path}. SETTING TP TO 0. Error: {e}")

        k_tp_pairs.append((ktarget_kval, tp))
    if f==False:
        exit(-1)
    # Sort by TP in descending order
    k_tp_pairs.sort(key=lambda x: x[1], reverse=True)

    # Try top 2 K values sequentially
    print(f"LOG:-----------------------------------VALIDATING Top 2 K Values")
    for k, original_tp in k_tp_pairs[:3]:  # Try top 2 K values one at a time
        print(f"\nTesting K: {k} with original TP: {original_tp}")
        print(f"LOG:-----------------------------------VALIDATING: {k}")
        
        # Use temporary folder name
        temp_path = os.path.join(opts.outputDirectory, "TOP_K_CANDIATE" + str(k))
        if not os.path.exists(temp_path):
            os.makedirs(temp_path, exist_ok=True)
        
        print(f"LOG:-----------------------------------Using K Value: {k}")
        try:
            a = yara_instance.generate(
                opts.malwarePath,
                opts.bfMalicious,
                opts.bfBenign,
                bicluster_alg=opts.biclusterAlgorithmType,
                cluster_alg=opts.clusterAlgorithm,
                output_format=opts.ruleOutputType,
                output_dir=temp_path,
                augmented_target_k=k,
                bicluster_feature_prune_coverage=50,
                selection_heuristic="PYara",
            )

            # Process all files to compute new TP
            print(f"LOG:-----------------------------------Processing files in {temp_path}")
            files = [f for f in os.listdir(temp_path) if os.path.isfile(os.path.join(temp_path, f))]
            tp_list = []
            for f in files:
                check_path = os.path.join(temp_path, f)
                try:
                    tp_val = extract_tp_rate(check_path)
                except:
                    tp_val = 0
                tp_list.append(tp_val)
            
            new_tp = max(tp_list) if tp_list else 0
            print(f"LOG:-----------------------------------Computed New TP: {new_tp} for K: {k}")
            
            # Check if TP matches within threshold
            if abs(new_tp - original_tp) < 0.0001:  # TP matches within small tolerance
                # Rename folder to TrueBEST_K_
                final_path = os.path.join(opts.outputDirectory, "TrueBEST_K_" + str(k))
                if os.path.exists(final_path):
                    shutil.rmtree(final_path)  # Remove existing folder if any
                os.rename(temp_path, final_path)
                print(f"LOG:-----------------------------------Success: TP matches for K = {k}. Renamed folder to {final_path}")
                best_k, best_tp = k, new_tp
                break
            else:
                print(f"LOG:-----------------------------------TP mismatch for K = {k}. Keeping temp folder {temp_path}. Trying next K if available.")
                # Keep temp folder as is
                
        except Exception as e:
            print(f"COULD NOT VALIDATE RULE FOR {temp_path}. Error: {e}")
            continue
    else:  # If loop completes without breaking (no success)
        best_k, best_tp = k_tp_pairs[0] if k_tp_pairs else (None, 0)
        print(f"\nNo matching TPs found. Defaulting to highest original K: {best_k} with TP: {best_tp}")

    if best_k is not None:
        print(f"\nFinal Best K: {best_k} with TP: {best_tp}")
    else:
        print("\nNo valid K values found.")



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

        HardK=opts.HardK
        if HardK==True:
            print("LOG:-----------------------------------Hard K Value Selected")
            FUNCTIONHARDK(opts)
        else:
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
                ktarget_kval=augmented_target_k[i]
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
                        a = yara_instance.generate(
                            opts.malwarePath,
                            opts.bfMalicious,
                            opts.bfBenign,
                            bicluster_alg=opts.biclusterAlgorithmType,
                            cluster_alg=opts.clusterAlgorithm,
                            output_format=opts.ruleOutputType,output_dir=path,
                            augmented_target_k=ktarget_kval, 
                            bicluster_feature_prune_coverage=50,
                            selection_heuristic="PYara",
                        )
                        
                    else:
                        exit(-1)
                        # a = yara_instance.generate(
                        #     opts.malwarePath,
                        #     opts.bfMalicious,
                        #     opts.bfBenign,
                        #     bicluster_alg=opts.biclusterAlgorithmType,
                        #     cluster_alg=opts.clusterAlgorithm,
                        #     output_format=opts.ruleOutputType,output_dir=path,
                        #     bicluster_feature_prune_coverage=50,
                        #     selection_heuristic="AutoYara",
                        # )
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

    parser.add_argument('-hk', '--HardK', type=str2bool, default=False, help='THIS IS FOR OPTIMAL K SELECTION. IF TRUE, THE K VALUE WILL BE HARD SET. IF FALSE, THE K VALUE WILL BE SOFT SET. DEFAULT: FALSE')
    parser.add_argument('-hkP', '--HardKPike', type=str2bool, default=False, help='IF NO Neighborhood K, we will find K')

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