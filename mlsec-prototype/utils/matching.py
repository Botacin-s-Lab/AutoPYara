import os
import yara

def test_yara_rule(rules, directory):
    # Create a dictionary for rule sources
    rule_sources = {}
    for idx, rule_str in enumerate(rules):
        rule_sources[f"rule_{idx}"] = rule_str

    try:
        # Compile the rules into a single YARA ruleset
        combined_rules = yara.compile(sources=rule_sources)
    except yara.SyntaxError as e:
        raise ValueError(f"Syntax error in one of the rules: {e}")

    # Dictionary to hold matches
    matches = {}

    # Scan files in the directory
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            try:
                # Match the file against the combined ruleset
                match = combined_rules.match(file_path)
                matches[file_path] = [m.rule for m in match]  # Extract rule names
            except yara.Error as e:
                print(f"Error scanning file {file_path}: {e}")
                matches[file_path] = []

    return matches
