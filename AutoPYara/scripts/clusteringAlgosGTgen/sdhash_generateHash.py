import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import Literal


def get_files_from_csv(folder_path="/usr/src/app/sdhashdata", csv_path="path.csv", max_files=100):
    """Retrieve up to max_files file paths from a CSV file or folder, with path mapping."""
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path)
        if 'File_Name' not in df.columns or 'Full_Path' not in df.columns:
            raise ValueError("CSV must contain 'File_Name' and 'Full_Path' columns")
        
        host_path = "/mnt/data_disk1/mabon/datacopy"
        docker_path = "/usr/src/app/datacopy"
        df['Full_Path'] = df['Full_Path'].str.replace(host_path, docker_path, regex=False)

        file_paths = df['Full_Path'].tolist()
    else:
        if not os.path.isdir(folder_path):
            raise ValueError(f"'{folder_path}' is not a valid directory.")
        file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                      if os.path.isfile(os.path.join(folder_path, f))]

    valid_paths = [path for path in file_paths if os.path.isfile(path) and os.path.getsize(path) > 0]
    if len(valid_paths) < 2:
        raise ValueError("At least two valid non-empty files required for clustering.")
    return valid_paths[:max_files] if max_files else valid_paths

import shutil
def process_file(file_path, temp_dir):
    """Copy file to temp directory and return new path."""
    dest_path = os.path.join(temp_dir, os.path.basename(file_path))
    shutil.copy(file_path, dest_path)
    return dest_path

import subprocess
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

import shutil
import os
from contextlib import contextmanager
import pandas as pd

@contextmanager
def fixed_temp_dir(path):
    """Create a fixed temporary directory and delete it on exit."""
    os.makedirs(path, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path)


def compute_distance_matrix(file_paths, threshold=1):
    """Compute pairwise distance matrix efficiently with a similarity threshold."""
    # Set your fixed temporary directory path
    temp_dir_path = '/usr/src/app/datacopy/tempfile'
    
    # Use the fixed_temp_dir context manager so the directory is cleaned up after use.
    with fixed_temp_dir(temp_dir_path) as temp_dir:
        with ThreadPoolExecutor(max_workers=64) as executor:
            processed_files = list(tqdm(
                executor.map(lambda file_path: process_file(file_path, temp_dir), file_paths),
                total=len(file_paths), desc="Copying files"
            ))
        # cmd=[ "sdhash", "-r", temp_dir, "/>t.txt",]
        # print(cmd)
            output_file = os.path.join(temp_dir, "t.txt")  # Temporary output file

        # Run sdhash and redirect output properly
        with open(output_file, "w") as f:
            result = subprocess.run(
                 ["sdhash", "-r", temp_dir, "-p", "80"],  # Added "-p 32" for multithreading,  
                check=True,
                stdout=f,  # Redirect output to t.txt
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode != 0:
            print("Error:", result.stderr)

        # Define the destination path in the script's directory
        dest_file = os.path.join(os.getcwd(), "t.txt")  # Copies to script directory

        # Copy t.txt from temp_dir to the script directory
        shutil.copy(output_file, dest_file)
        

        # result = subprocess.run(
        #         ["sdhash", "-c t.txt>match -p 32"],
        #         check=True,
        #         capture_output=True,
        #         text=True
        #     )

    return 1
    
def cluster_with_threshold(file_paths,threshold,min_samples=2,noise_labeling = 'Ascending',max_clusters=None):
# Compute distance matrix and run DBSCAN
    distance_matrix = compute_distance_matrix(file_paths, threshold=threshold)
 
    return -1

import csv

def remove_empty_lines(input_file, output_file):
    removed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            if line.strip():  # Check if line is not empty
                outfile.write(line)
            else:
                removed_count += 1
    
    print(f"Number of lines removed: {removed_count}")

# Example usage

if __name__ == "__main__":
    folder_path = ""
    csv_path = "/usr/src/app/Dev/output/merged_csv.csv"
    csv_name='sdhash'
    output_dir='newtest/sdhash'
    threshold=70
    print(threshold)
    file_paths = get_files_from_csv(folder_path, csv_path=csv_path, max_files=None)
    labels=cluster_with_threshold(file_paths,threshold)
    valid_hashes = []
    count=0
    count2=0
    with open("t.txt", "r") as f:
        for line in tqdm(f, desc="Processing lines"):
            if "sdbf:" in line:  # Only keep valid SDBF lines
                valid_hashes.append(line)
                count2+=1
            else:
                count+=1
    print(count,count2)
    with open("t_clean.txt", "w") as f:
        f.writelines(valid_hashes)
