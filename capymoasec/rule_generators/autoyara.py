# we here implement capymoa to use its engine as our backengine
#from capymoa import biclustering # our patch there

class AutoYara:
    def __init__(self, params):
        # our classifiers/clustering/datastructures will be the ones from capymoa
        #self.clustering = BiClustering()
        self.params = params

    def train(self, goodware_files):
        return True

    def generate(self, malware_files):
        # add all the autoyara code here
        # but whenever we need ML, we call capymoa one
        #self.clustering.do_something_with_data(malware_files)
        return True
