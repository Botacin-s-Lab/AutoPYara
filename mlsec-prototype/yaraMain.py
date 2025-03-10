import os
import json
import re
import math
import time

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
def main(opts):
    if opts.generateRule:  # Simplified True check
        print("LOG:-----------------------------------RULE GENERATION SELECTED")
        print("LOG:-----------------------------------BUILDING OBJECT")
        yara_instance = AutoPYara()
        print("result", yara_instance.generate(
            opts.malwarePath,
            opts.bfMalicious,
            opts.bfBenign,
            bicluster_alg="SpectralCoCluster",
            cluster_alg="AugmentedKMeansDBSCANSoft",
            output_format="yara-python",
            augmented_target_k=4,
        ))
    return 0  # Return 0 for success

def parseArgs(argv):
    parser = argparse.ArgumentParser(description="Parse command-line arguments for malware analysis.")

    parser.add_argument('-bfM', '--bfMalicious', type=str, required=True, help='Path to Malicious Bloom Filter.')
    parser.add_argument('-bfB', '--bfBenign', type=str, required=True, help='Path to Benign Bloom Filter.')
    parser.add_argument('-mP', '--malwarePath', type=str, required=True, help='Path to Malicious Files.')
    parser.add_argument('-gR', '--generateRule', type=str2bool, default=False, help='Toggle Rule Generation (True/False, default: False).')
    parser.add_argument('-o', '--outputDirectory', type=str, required=True, help='Directory for output.')

    # if argv is None:
    #     # Manual setup
    #     opts = parser.parse_args([
    #         '--bfMalicious', '/usr/src/app/intermediate/bloom_filters/malicious-bytes',
    #         '--bfBenign', '/usr/src/app/intermediate/bloom_filters/benign-bytes',
    #         '--malwarePath', '/usr/src/app/Honeypots',
    #         '--generateRule', 'True',
    #         '--outputDirectory', '/usr/src/app/TestOuput'
    #     ])
    # else:
    opts = parser.parse_args(argv)
    return opts

if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    print(opts)
    main(opts)