import re
import yara
import os
from tqdm import tqdm
import argparse
import sys
import csv


def test_rule(yaraRule, pathlist):
    # Runs the rule on all samples in a directory
    matches = 0
    total = 0
    for i in pathlist:
        try:
            # Attempt to match the YARA rule against the file
            if yaraRule.match(i):
                matches += 1
            total += 1
        except Exception as e:
            #print(f"Error processing {i}: {str(e)}")
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
        # print(f"Error: File '{file_path}' not found")
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
        # Sanitize rule_name: replace invalid characters with underscores
        rule_name = re.sub(r'[^a-zA-Z0-9_]', '_', rule_name)
        if not re.match(r'^[a-zA-Z_]', rule_name):
            rule_name = f"rule_{rule_name}"
                
        # Construct the YARA rule string
            yara_rule = f"rule {rule_name} {{\n"
        yara_rule += "    strings:\n"
        for string_entry in strings_data:
            string_id = string_entry['id']
            string_data = string_entry['data']
            # Ensure string_id starts with $ and is properly formatted
            if not string_id.startswith('$'):
                string_id = f"${string_id}"
            yara_rule += f"        {string_id} = {{ {string_data} }}\n"
        
        # Add condition
        yara_rule += f"    condition:\n        {condition}\n"
        yara_rule += "}"
        
        # Print the rule for debugging
        #print("Generated YARA Rule:\n", yara_rule)
        
        # Compile the rule
        compiled_rule = yara.compile(source=yara_rule)
        return compiled_rule
    
    except yara.SyntaxError as e:
        print(f"YARA Syntax Error: {e}")
        return None
    except Exception as e:
        #print(f"Error compiling rule: {e}")
        return None

def evalIndividaul(rulePath,pathlist):
    data=parse_yara_file(rulePath)
    if data==None:
        print("LOG:-----------------------------------ERROR DATA LOAD")
        return -1
    YaraRule=compile(data['strings'], rule_name=data['rule_name'], condition=data['condition'])
    if YaraRule==None:
        print("LOG:-----------------------------------ERROR RULE COMPILE")
        return -1
    matches, total=test_rule(YaraRule, pathlist)
    print(matches/total)


def evalbatch(ruleCluster,rulePath,evalCluster,pathlist,saveCSV):

    data=parse_yara_file(rulePath)
    if data==None:
        print("LOG:-----------------------------------ERROR DATA LOAD")
        with open(saveCSV, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([ruleCluster,rulePath,evalCluster,"FAILED_Norule","FAILED_Norule","FAILED_Norule"])
        return -1
    YaraRule=compile(data['strings'], rule_name=data['rule_name'], condition=data['condition'])
    if YaraRule==None:
        print("LOG:-----------------------------------ERROR RULE COMPILE")
        with open(saveCSV, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([ruleCluster,rulePath,evalCluster,"FAILED_RuleFail","FAILED_RuleFail","FAILED_RuleFail"])
        return -1
    matches, total=test_rule(YaraRule, pathlist)
    Score=matches/total
    with open(saveCSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([ruleCluster,rulePath,evalCluster,matches,total,Score])
        

def main(opts):
    if opts.eval=="evalIndividaul":
        print("LOG:-----------------------------------INIDIVIDUAL EVAL")
        pathlist = []
        for filename in os.listdir(opts.directory):
            full_path = os.path.join(opts.directory, filename)
            if os.path.isfile(full_path):
                pathlist.append(full_path)
        print("LOG:-----------------------------------TOTAL FILES: ",len(pathlist))
        evalIndividaul(opts.rulePath,pathlist)
    else:
        # print("LOG:-----------------------------------BATCH EVAL")
        pathlist=opts.directory
        
        # print("LOG:-----------------------------------CSV PATH SET",opts.output)
        if not os.path.exists(opts.output):
            # print("LOG:-----------------------------------CREATIGN",opts.output)
            with open(opts.output, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ruleCluster','rulePath','evalCluster', 'matches','total','Score'])  # Header row
        else:
            print("LOG:-----------------------------------CSV Already Exsist",opts.output)

        for rules in opts.rulePath:
            evalbatch(opts.ruleCluster,rules, opts.evalCluster,pathlist,saveCSV=opts.output)
    return 1
    
def parserArgs(argv):
    parser = argparse.ArgumentParser(description="Parse command-line arguments for malware analysis.")

    parser.add_argument('-rp', '--rulePath', type=str, required=True, help='Path to Benign Bloom Filter.')
    parser.add_argument('-dr', '--directory', type=str, required=True, help='Path to Files.')
    parser.add_argument( '-eval', '--eval',choices={'evalIndividaul', 'batchEval'},required=True,help='Batch eval or inidividaul')
    parser.add_argument('-o', '--output', type=str, required=True, help='Directory for output.')
    parser.add_argument('-rc', '--ruleCluster', type=str, required=False, help='ruleCluster')
    parser.add_argument('-ec', '--evalCluster', type=str, required=False, help='evalCluster')

    if argv is None:
        opts = parser.parse_args()
    else:
        opts = parser.parse_args(argv)
    
    # If Path contains commas, split it into a list
    if ',' in opts.directory:
        opts.directory = [path.strip() for path in opts.directory.split(',')]

    if ',' in opts.rulePath:
        opts.rulePath = [path.strip() for path in opts.rulePath.split(',')]
       
    return opts


if __name__ == '__main__':
    opts = parserArgs(sys.argv[1:])
    main(opts)