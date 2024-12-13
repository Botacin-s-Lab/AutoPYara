from PythonInterface import PythonInterface
import jpype
from typing import Literal
from jpype.types import *
import yara

# Define a custom type for the algorithm options
BiclusterAlgorithmType = Literal['SpectralCoCluster', 'SpectralCoClusterScale']
ClusterAlgorithmType = Literal['VBGMM', 'KMeans', 'Random', 'AugmentedKMeans']

class AutoYara(PythonInterface):
    def __init__(self, ngram_top_k=1000):
        '''
            ngram_top_k: used by KiloGram to extract the kth most common ngrams for bloom filters
        '''
        super().__init__()

        # Import Java classes
        self.AutoYaraCluster = jpype.JPackage("edu.lps.acs.ml.autoyara").AutoYaraCluster
        self.AutoYaraPython = jpype.JPackage("edu.lps.acs.ml.autoyara").AutoYaraPython
        self.Bytes2Bloom = jpype.JPackage("edu.lps.acs.ml.autoyara").Bytes2Bloom
        self.File = jpype.JClass("java.io.File")
        self.ArrayList = jpype.JClass("java.util.ArrayList")
        self.Integer = jpype.JClass("java.lang.Integer")

        # Create instances of the Java classes
        self.yara_cluster_legacy = self.AutoYaraCluster()
        self.yara_cluster = self.AutoYaraPython()
        self.bytes2bloom = self.Bytes2Bloom()

        # Set the parameters
        self.yara_cluster.max_filter_size = 10000000
        self.yara_cluster_legacy.max_filter_size = 10000000
        self.bytes2bloom.tooKeep = ngram_top_k

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

    def legacy_generate(self, input_dir, output_dir, bloom_malicious, bloom_benign,
                 bicluster_alg: BiclusterAlgorithmType = 'SpectralCoCluster', cluster_alg: ClusterAlgorithmType = 'VBGMM'):
        input_dirs = self.ArrayList()
        input_dirs.add(self.File(input_dir))
        self.yara_cluster.inDir = input_dirs

        self.yara_cluster.biclusterPipelineAlg = bicluster_alg
        self.yara_cluster.clusterAlg = cluster_alg

        self.yara_cluster.benign_bloom_dir = self.File(bloom_benign)
        self.yara_cluster.malicious_bloom_dir = self.File(bloom_malicious)
        self.yara_cluster.out_file = self.File(output_dir)

        try:
            self.yara_cluster.run()
        except Exception as e:
            print(f"Exception during run: {e}")

    def generate(self, input_dir, bloom_malicious, bloom_benign,
                 bicluster_alg: BiclusterAlgorithmType = 'SpectralCoCluster', cluster_alg: ClusterAlgorithmType = 'VBGMM',
                 predictor_labels=None, k_cluster=0, rule_name=None):
        '''
            predictor_labels: a list of predicted clusters for each sample given by an external predictor for augmented kmeans
            k_cluster: number of clusters to separate the samples into. Only used by some algorithms that require k
        '''
        input_dirs = self.ArrayList()
        input_dirs.add(self.File(input_dir))
        self.yara_cluster.inDir = input_dirs

        self.yara_cluster.biclusterPipelineAlg = bicluster_alg
        self.yara_cluster.clusterAlg = cluster_alg

        self.yara_cluster.benign_bloom_dir = self.File(bloom_benign)
        self.yara_cluster.malicious_bloom_dir = self.File(bloom_malicious)

        if k_cluster:
            self.yara_cluster.k = k_cluster
        if predictor_labels:
            self.yara_cluster.predictorLabels = predictor_labels

        try:
            yara_string = self.yara_cluster.pythonRun()
            return yara.compile(source=yara_string), yara_string
        except Exception as e:
            print(f"Exception during run: {e}")