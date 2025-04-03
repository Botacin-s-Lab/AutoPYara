import os

import statistics 
import argparse


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
        #Minomi Sampling
        MetricArray=[]
        stopmetric=30
        threshold=5
        prs=0
        os.makedirs(opts.outputDirectory, exist_ok=True)
        for i in tqdm(range(100)):
            Flag=False
            path=(os.path.join(opts.outputDirectory,str(i+1)))
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            existing_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            if not existing_files:
                yara_instance = AutoPYara()

                yara_instance.generate(
                    opts.malwarePath,
                    opts.bfMalicious,
                    opts.bfBenign,
                    bicluster_alg=opts.biclusterAlgorithmType,
                    cluster_alg=opts.clusterAlgorithm,
                    output_format=opts.ruleOutputType,output_dir=path)
                try:
                    file = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                    Check=(os.path.join(path,file[0]))
                    tp=extract_tp_rate(Check)
                except:
                    tp=0
                    print("COULD NOT GENERATE RULE SETTING TP To 0")
            else:
                print("PAST RUN FOUND.. LOADING PRECOMPUTED")
                file = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                Check=(os.path.join(path,file[0]))
                tp=extract_tp_rate(Check)


            MetricArray.append(tp)
            if len(MetricArray)>=stopmetric:
                var=statistics.stdev(MetricArray)
                print("LOG:-----------------------------------STD: ",var)
                if abs(prs-var)<threshold:
                    print("LOG:-----------------------------------EARLY STOPPING: ",var)                
                    break
                else:
                    stopmetric+=5
                    threshold=threshold*1.25
                    print("LOG:-----------------------------------STOP METRIC INCREASED: ",stopmetric) 
                    print("LOG:-----------------------------------THRESHOLD INCREASED: ",threshold)                         
            try:
                prs=statistics.stdev(MetricArray)
                print("LOG:-----------------------------------PRS",prs)
            except:
                prs=0    

        var=statistics.stdev(MetricArray)
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
    parser.add_argument( '-rOT', '--ruleOutputType',choices={'yara-python', 'yaramod', 'string'},required=True,help='Output Rule Format')
    parser.add_argument('-k', '--augmentedTarget_k', type=int, default=None)
    
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