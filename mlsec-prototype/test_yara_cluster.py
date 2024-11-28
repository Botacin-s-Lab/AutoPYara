from utils.clustering import *
from utils.matching import *

# Define YARA rules as strings
yara_rules = [
    """
    rule TestRule1 {
        strings:
            $a = "a"
        condition:
            $a
    }
    """,
    """
    rule TestRule2 {
        strings:
            $b = "b"
        condition:
            $b
    }
    """
]

# Directory containing files to scan
directory = "/tmp/malware/"

# Test the YARA rules
matches = test_yara_rule(yara_rules, directory)

clusters = cluster_samples_by_yara(matches)
print(clusters)
