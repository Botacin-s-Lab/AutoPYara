import re
from PythonInterface import PythonInterface
import jpype
from typing import Literal
from jpype.types import *
import yara
import yaramod
from augmented_predictor.DBSCAN_SSDEEP import AugmentedDBScan

BiclusterAlgorithmType = Literal['SpectralCoCluster', 'SpectralCoClusterScale']
# SpectralCoCluster: spectral cocluster algorithm using bistochastization normalization
# SpectralCoClusterScale: same spectral cocluster algorithm using scale normalization

ClusterAlgorithmType = Literal[
    'VBGMM', # variational bayesian gaussian mixture model
    'KMeans', # k-means, k can be specified or automatically chosen by the pipeline
    'Random', # designate samples to a random cluster, used to verify correctness of other algorithms and tested as baseline
    'AugmentedKMeansDBSCAN', # augmented kmeans, uses DBSCAN to cluster + SSDEEP distance metric to generate predictor labels
    'AugmentedKMeansDBSCANSoft', # AugmentedKMeansDBSCAN but with mixture assignments (euclidean distance from centroid as weight)
    'AugmentedKMeansVT', # augmented kmeans, uses virustotal labels to generate predictor labels
    'AugmentedKMeansVTSoft', # AugmentedKMeansVT but with mixture assignments (euclidean distance from centroid as weight)
]

RuleOutputType = Literal['yara-python', 'yaramod', 'string']
# yara-python: format using virustotal package, see https://github.com/VirusTotal/yara-python
# yaramod: format useful for evaluations since members can be easily accessed https://github.com/avast/yaramod
# string: yara rule as string format

SelectionHeuristic = Literal['AutoYara', 'PYara']
# AutoYara: uses the old selection heuristic from the original AutoYara code
# PYara: uses the new select heuristic that

augmented_algorithms = ['AugmentedKMeansDBSCAN', 'AugmentedKMeansDBSCANSoft', 'AugmentedKMeansVT', 'AugmentedKMeansVTSoft']

class AutoPYara(PythonInterface):
    def __init__(self, ngram_top_k=1000):
        '''
            ngram_top_k: used by KiloGram to extract the kth most common ngrams during bloom filter generation
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

        # Yara Package Init
        self.yaramod = yaramod.Yaramod(yaramod.Features.AllCurrent)

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

    def generate(self, input_dir, bloom_malicious, bloom_benign,
                 output_dir=None,
                 bicluster_alg: BiclusterAlgorithmType = 'SpectralCoCluster', cluster_alg: ClusterAlgorithmType = 'VBGMM',
                 output_format: RuleOutputType = 'string', predictor_labels=None, k_cluster=0, similarity_threshold=90,
                 rule_name=None, selection_heuristic: SelectionHeuristic = "PYara", bicluster_feature_prune_coverage=50,
                 ):
        '''
            predictor_labels: a list of predicted clusters for each sample given by an external predictor for augmented kmeans
            k_cluster: number of clusters to separate the samples into. Only used by some algorithms that require k
            similarity_threshold: used by augmented kmeans's dbscan
            rule_name: the name of the yara rule, leave empty to automatically generate one
        '''
        input_dirs = self.ArrayList()
        input_dirs.add(self.File(input_dir))
        self.yara_cluster.inDir = input_dirs

        self.yara_cluster.biclusterPipelineAlg = bicluster_alg
        self.yara_cluster.clusterAlg = cluster_alg

        self.yara_cluster.benign_bloom_dir = self.File(bloom_benign)
        self.yara_cluster.malicious_bloom_dir = self.File(bloom_malicious)

        self.yara_cluster.selectionHeuristic = selection_heuristic
        self.yara_cluster.biclusterFeaturePruneCoverage = bicluster_feature_prune_coverage/100

        if rule_name: # if blank, will generate a name
            self.yara_cluster.name = rule_name

        if k_cluster: # Used by KMeans, Random
            self.yara_cluster.k = k_cluster

        if output_dir: # if blank, will not save
            print("setting output file", output_dir)
            self.yara_cluster.out_dir = output_dir

        # file directory filling is done at this point, load the values for preprocessing
        self.yara_cluster.findBestRulePipelineInit() # process the loaded values first

        # we can do preprocessing now
        if cluster_alg in augmented_algorithms and not predictor_labels:
            assert not k_cluster, "you cannot specify k clusters for Augmented Learning clustering"
            print(cluster_alg, "requires a predictor label, generating...")

            # these algorithms require a predictor label and we didn't provide one, we have to generate it
            print(self.yara_cluster.bloomSizes)
            print(self.yara_cluster.targets)

            if cluster_alg:
                augmented_predictor = AugmentedDBScan(dbscan_threshold=similarity_threshold)
            else:
                augmented_predictor = AugmentedDBScan(dbscan_threshold=similarity_threshold)

            predictor_labels = augmented_predictor.predict(self.yara_cluster.targets)
            self.yara_cluster.k = len(set(predictor_labels)) # k is the # of unique labels
            print("PYARA: got k =", self.yara_cluster.k)

        if predictor_labels:
            assert len(predictor_labels) == len(self.yara_cluster.targets), \
                f"predictor labels must be the same size as file corpus! {len(predictor_labels)} =/= {len(self.yara_cluster.targets)}"

            # now that we have the predictors, set it in java
            self.yara_cluster.predictorLabels = predictor_labels

        try:
            yara_out = dict(self.yara_cluster.pythonRun()) # we need to clone since resetYaraState() will wipe the original
            yara_out = self.convert_java_to_python(yara_out) # convert all members into python friendly objects

            # print("getting paths", self.yara_cluster.getPathsPython())

            self.yara_cluster.resetYaraState()
            if output_format == "string":
                yara_out["output"] = yara_out['rule_string']
            elif output_format == "yara-python":
                yara_out["output"] = yara.compile(source=yara_out['rule_string'])
            elif output_format == "yaramod":
                yara_out["output"] = self.yaramod.parse_string(yara_out['rule_string'])
            else:
                raise ValueError(f"invalid output format: {output_format}")

            self.reset_memory()
            return yara_out
        except Exception as e:
            self.yara_cluster.resetYaraState()
            self.reset_memory()
            print(f"Exception during run: {e}")