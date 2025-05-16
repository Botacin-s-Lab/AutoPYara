import argparse
import pandas as pd
import os
from tqdm import tqdm




def delete_file(file_path):
    try:
        # Check if file exists
        if os.path.exists(file_path):
            # Delete the file
            os.remove(file_path)

            
    except PermissionError:
        #print(f"Error: Permission denied to delete '{file_path}'")
        return -1


def get_yara_files(cluster, base_path,rule='.yara'):
    yara_files = []
    cluster_path = os.path.join(base_path, f'cluster_{cluster}')
    # Check if cluster directory exists
    if not os.path.exists(cluster_path):
        return yara_files  # Return empty list if cluster doesn't exist
    #print(cluster_path)
    # Loop through possible X values (e.g., 1 to 30 or more)
    x = 1
    while True:
        subfolder = os.path.join(cluster_path, f'{x}')
        if not os.path.exists(subfolder):
            break  # Stop if folder doesn't exist
        
        # Look for all .yara files in this subfolder
        for file_name in os.listdir(subfolder):
            if file_name.endswith(rule):
                full_path = os.path.join(subfolder, file_name)
                yara_files.append(full_path)
        x += 1
    
    return yara_files

def get_files_by_all_clusters(df):

    # Group by Cluster_Label and get lists of File_Path
    clustered_files = df.groupby('Cluster_Label')['File_Path'].apply(list).to_dict()
    
    # Sort by length of file lists and create new ordered dictionary
    sorted_items = sorted(clustered_files.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items)

def process_file(input_file_path, output_file_path, new_rule_name):
    try:
        # Read the original file content
        with open(input_file_path, 'r') as file:
            content = file.read()

        # Remove square brackets
        modified_content = content.replace('[', '').replace(']', '')

        # Extract the old rule name
        # Find text between "rule" and first "{"
        start_idx = modified_content.find("rule") + 5  # +5 to skip "rule "
        end_idx = modified_content.find("{")
        if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
            raise ValueError("Could not find rule name in the file")
        
        old_rule_name = modified_content[start_idx:end_idx].strip()
        new_rule_text = f"rule {new_rule_name}"

        # Replace the old rule definition with new one
        modified_content = modified_content.replace(
            f"rule {old_rule_name}", new_rule_text
        )

        # Write the modified content to the output file
        with open(output_file_path, 'w') as file:
            file.write(modified_content)

        # print(f"File processed successfully. Output saved to {output_file_path}")
        # print(f"Replaced rule name '{old_rule_name}' with '{new_rule_name}'")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def merge_files(file_list, output_filename):
    """
    Merge multiple text files into a single output file.
    
    Args:
        file_list (list): List of file paths to be merged
        output_filename (str): Name/path of the output file
    
    Returns:
        bool: True if successful, False if an error occurred
    """
    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            for file_path in file_list:
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        # Read content from input file and write to output file
                        outfile.write(infile.read())
                        # Add a newline between files for separation
                        outfile.write('\n')
                except FileNotFoundError:
                    print(f"Warning: File not found - {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    return False
        return True
    
    except Exception as e:
        print(f"Error creating output file {output_filename}: {str(e)}")
        return False
def process_clusters(csv_file,thv,clean=False):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    mainbase='/usr/src/app/YaraTest/'
    all_cluster_files = get_files_by_all_clusters(df)
    valid_clusters= {k: v for k, v in all_cluster_files.items() if len(v) >= 2}

    if clean==True:
        print("CLAING")
        # Process each cluster
        for cluster_rule, file_list_rule in valid_clusters.items():
            bp=os.path.join(mainbase, f'Th{thv}')
            rulesPath=get_yara_files(cluster_rule, base_path=bp,rule='.yara')
            for i in range(len(rulesPath)):
                new_rule_name=f'Cluster{cluster_rule}_{i+1}'
                output=os.path.join(bp, f'cluster_{cluster_rule}',f'{i+1}','yaraRule.yar')
                process_file(rulesPath[i], output, new_rule_name)
                delete_file(rulesPath[i])
    else:
        # Process each cluster
        length=0
        count=0
        for cluster_rule, file_list_rule in valid_clusters.items():
            bp=os.path.join(mainbase, f'Th{thv}')
            rulesPath=get_yara_files(cluster_rule, base_path=bp,rule='.yar')
            length+=len(rulesPath)

            # print(f"Processing Rules from Cluster {cluster_rule}")
            merge_files(rulesPath, f'C{cluster_rule}.yar')
            count+=1
        print(length)
        print(count)

def parse_args():
    parser = argparse.ArgumentParser(description="Process clustered files from a CSV and run yaraMain.py for each cluster.")
    parser.add_argument(
        '--csv-file', 
        type=str, 
        required=True, 
        help='Path to the CSV file containing cluster data (must have File_Path and Cluster_Label columns)'
    )

    parser.add_argument(
        '--thv', 
        type=str, 
        required=True, 
        help='threshold Val'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    process_clusters(args.csv_file,args.thv)