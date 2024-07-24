# Adjust path for running the tests
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
basePath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + '/'

# we import the new framework
from capymoasec.datasets.drebin import *
from capymoasec.detectors.andropermbin import *

# instantiate the dataset and model
dataset = DREBIN()
detector = ANDROPERMBIN(classifier='ARF')

# Batch testing
# BatchEvaluator(detector,dataset)

# Temporal evaluation
# TemporalEvaluator(datector, dataset)
