import re
import yara
import os
import tqdm

def test_rule(yaraRule, pathlist):
    # Runs the rule on all samples in a directory
    matches = 0
    total = 0
    for i in tqdm(pathlist):
        try:
            # Attempt to match the YARA rule against the file
            if yaraRule.match(i):
                matches += 1
            total += 1
        except Exception as e:
            print(f"Error processing {i}: {str(e)}")
            total += 1
            continue
    
    return matches, total



def parse_yara_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            
        # Extract rule name
        rule_name_match = re.search(r'rule\s+([^{]+)\s*{', content)
        rule_name = rule_name_match.group(1).strip() if rule_name_match else "Unknown"
        
        # Extract strings section
        strings_section = re.search(r'strings:(.+?)condition:', content, re.DOTALL)
        strings = []
        if strings_section:
            strings_content = strings_section.group(1)
            # Find all string definitions
            string_matches = re.finditer(r'\$x\d+\s*=\s*{([^}]+)}', strings_content)
            for match in string_matches:
                string_data = match.group(1).strip()
                strings.append({
                    'id': match.group(0).split('=')[0].strip(),
                    'data': string_data
                })
        
        # Extract condition
        condition_match = re.search(r'condition:(.+?)}', content, re.DOTALL)
        condition = condition_match.group(1).strip() if condition_match else "None"
        
        # Extract comments
        comments = []
        comment_matches = re.finditer(r'//(.+)', content)
        for match in comment_matches:
            comments.append(match.group(1).strip())
        
        return {
            'rule_name': rule_name,
            'strings': strings,
            'condition': condition,
            'comments': comments
        }
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None



def compile(strings_data, rule_name="example_rule", condition="any of them"):
    """
    Convert a list of string dictionaries into a valid YARA rule string.
    
    Args:
        strings_data: List of dictionaries containing 'id' and 'data' keys
        rule_name: Name of the YARA rule (default: "example_rule")
        condition: Condition for the YARA rule (default: "any of them")
    
    Returns:
        Compiled YARA rule object
    """
    try:
        # Construct the YARA rule string
        if not re.match(r'^[a-zA-Z_]', rule_name):
            rule_name = f"rule_{rule_name}"
                
        # Construct the YARA rule string
        yara_rule = f"rule {rule_name} {{\n"
        # Add strings section
        yara_rule += "    strings:\n"
        for string_entry in strings_data:
            string_id = string_entry['id']
            string_data = string_entry['data']
            # Ensure the hex string is properly formatted
            yara_rule += f"        {string_id} = {{ {string_data} }}\n"
        
        # Add condition
        yara_rule += f"    condition:\n        {condition}\n"
        yara_rule += "}"
        
        # Compile the rule
        compiled_rule = yara.compile(source=yara_rule)
        return compiled_rule
    
    except yara.SyntaxError as e:
        print(f"YARA Syntax Error: {str(e)}")
        return None
    except Exception as e:
        print(f"Error creating YARA rule: {str(e)}")
        return None



def main():
    data=parse_yara_file(rulePath)
    YaraRule=compile(data['strings'], rule_name=data['rule_name'], condition=data['condition'])
    test_rule(YaraRule, pathlist)
    return 1
    
if __name__ == '__main__':
