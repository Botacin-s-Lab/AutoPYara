import os
import json
import re
import math
import time
import json

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

sys.path.append(os.path.abspath('./utils')) 
from utils.utils import str2bool


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

        # Generate content
        content = yara_instance.generate(
            opts.malwarePath,
            opts.bfMalicious,
            opts.bfBenign,
            bicluster_alg=opts.biclusterAlgorithmType,
            cluster_alg=opts.clusterAlgorithm,
            output_format=opts.ruleOutputType,
            augmented_target_k=opts.augmentedTarget_k,
        )

        content = serialize(content)  # Apply conversion

        # Define output directory and file path
        output_directory = opts.outputDirectory
        file_path = os.path.join(output_directory, "config.json")

        # Ensure the directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Save to file in JSON format
        with open(file_path, "w") as f:
            json.dump(content, f, indent=4)
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
    parser.add_argument('-k', '--augmentedTarget_k', type=int, default=4)
    
    parser.add_argument('-o', '--outputDirectory', type=str, required=True, help='Directory for output.')
 
    opts = parser.parse_args(argv)
    return opts

if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    print(opts)
    main(opts)