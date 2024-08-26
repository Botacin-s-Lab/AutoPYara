import jpype
import jpype.imports
from jpype.types import *
import os

# Import the AutoYaraCluster class
AutoYaraCluster = jpype.JPackage("edu.lps.acs.ml.autoyara").AutoYaraPython
Bytes2Bloom = jpype.JPackage("edu.lps.acs.ml.autoyara").Bytes2Bloom
File = jpype.JClass("java.io.File")
ArrayList = jpype.JClass("java.util.ArrayList")
Integer = jpype.JClass("java.lang.Integer")

class AutoYara:
    def __init__(self, top_k=1000):
        # Create an instance of the Java class
        self.yaraCluster = AutoYaraCluster()
        self.byte2Bloom = Bytes2Bloom()

        # Set the parameters
        self.yaraCluster.max_filter_size = 100000
        self.byte2Bloom.tooKeep = top_k

    def buildCandidateSet(self, target_dir, bloom_mal_dir, bloom_beg_dir, ngram_size=8):
        print("buildCandidateSet directories", target_dir, bloom_beg_dir, bloom_mal_dir)
        return self.yaraCluster.buildCandidateSet(File(target_dir), ngram_size, File(bloom_beg_dir), File(bloom_mal_dir))

    def train(self, input_dir, output_dir, ngram_size=8):
        input_file = File(input_dir)
        output_file = File(output_dir)

        # Set the parameters
        self.byte2Bloom.inDir = input_file
        self.byte2Bloom.gramSizes = ArrayList()
        self.byte2Bloom.gramSizes.add(Integer(ngram_size))
        self.byte2Bloom.outDir = output_file

        # Run the Java method
        try:
            print("starting bloom filter training")
            self.byte2Bloom.run()
            print(f"{ngram_size}-gram extraction complete for {input_dir}")
        except Exception as e:
            print(f"Exception during {ngram_size}-gram extraction: {e}")

    def predict(self, inputDir, outputDir, bloomMalicious, bloomBenign):
        input_dirs = ArrayList()
        input_dirs.add(File(inputDir))  # Provide the correct path to your input directory
        self.yaraCluster.inDir = input_dirs

        # Set the bloom filter directories
        self.yaraCluster.benign_bloom_dir = File(bloomBenign)
        self.yaraCluster.malicious_bloom_dir = File(bloomMalicious)

        # Set the output file
        self.yaraCluster.out_file = File(outputDir)

        # Call the run method
        try:
            print("starting testing")
            self.yaraCluster.run()
            print("testing complete")
        except Exception as e:
            print(f"Exception during run: {e}")

#myYara = AutoYara()
#print(myYara.train().stdout)
#print(myYara.predict().stdout)