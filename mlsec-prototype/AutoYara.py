from PythonInterface import PythonInterface
import jpype
from typing import Literal
from jpype.types import *

# Define a custom type for the algorithm options
BiclusterAlgorithmType = Literal['SpectralCoCluster', 'SpectralCoClusterScale']

class AutoYara(PythonInterface):
    def __init__(self, top_k=1000):
        super().__init__()

        # Import Java classes
        self.AutoYaraPython = jpype.JPackage("edu.lps.acs.ml.autoyara").AutoYaraPython
        self.Bytes2Bloom = jpype.JPackage("edu.lps.acs.ml.autoyara").Bytes2Bloom
        self.File = jpype.JClass("java.io.File")
        self.ArrayList = jpype.JClass("java.util.ArrayList")
        self.Integer = jpype.JClass("java.lang.Integer")

        # Create instances of the Java classes
        self.yara_cluster = self.AutoYaraPython()
        self.bytes2bloom = self.Bytes2Bloom()

        # Set the parameters
        self.yara_cluster.max_filter_size = 100000
        self.bytes2bloom.tooKeep = top_k

    def build_candidate_set(self, target_dir, bloom_mal_dir, bloom_beg_dir, ngram_size=8):
        return self.yara_cluster.buildCandidateSet(
            self.File(target_dir), ngram_size, self.File(bloom_beg_dir), self.File(bloom_mal_dir))

    def train(self, input_dir, output_dir, ngram_size=8):
        input_file = self.File(input_dir)
        output_file = self.File(output_dir)

        self.bytes2bloom.inDir = input_file
        self.bytes2bloom.gramSizes = self.ArrayList()
        self.bytes2bloom.gramSizes.add(self.Integer(ngram_size))
        self.bytes2bloom.outDir = output_file

        try:
            print("Starting bloom filter training")
            self.bytes2bloom.run()
            print(f"{ngram_size}-gram extraction complete for {input_dir}")
        except Exception as e:
            print(f"Exception during {ngram_size}-gram extraction: {e}")

        self.reset_memory()

    def generate(self, input_dir, output_dir, bloom_malicious, bloom_benign,
                 bicluster_alg: BiclusterAlgorithmType = 'SpectralCoCluster'):
        input_dirs = self.ArrayList()
        input_dirs.add(self.File(input_dir))
        self.yara_cluster.inDir = input_dirs

        self.yara_cluster.biclusterAlg = bicluster_alg

        self.yara_cluster.benign_bloom_dir = self.File(bloom_benign)
        self.yara_cluster.malicious_bloom_dir = self.File(bloom_malicious)
        self.yara_cluster.out_file = self.File(output_dir)

        try:
            print("Starting testing")
            self.yara_cluster.run()
            print("Testing complete")
        except Exception as e:
            print(f"Exception during run: {e}")