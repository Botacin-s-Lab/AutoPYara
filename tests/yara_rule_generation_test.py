import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
basePath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + '/'

# we import the new framework
from capymoasec.rule_generators import autoyara

# We instantiate our autoyara representation
autoY = autoyara.AutoYara(params=[])
# we train with the reference goodware
autoY.train([])
# we generate the rules for the candidate files
autoY.generate([])

# we here can instantiate a different generator
# from capymoasec.rule_generator import another_generator
# another_generator.gen()
# compare results from autoyara with the other generator
