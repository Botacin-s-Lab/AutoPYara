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
matches = match_yara_rule(yara_rules, directory)

# Print the results
for file, matched_rules in matches.items():
    print(f"File: {file}")
    if matched_rules:
        print(f"  Matched rules: {', '.join(matched_rules)}")
    else:
        print("  No matches")
