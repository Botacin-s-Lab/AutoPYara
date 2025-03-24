import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import Literal
import subprocess
import pandas as pd
import hashlib
import time
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import tempfile
from sklearn.cluster import DBSCAN


def verify_sdhash_installed():
    """Verify that sdhash is installed and accessible."""
    try:
        subprocess.run(['sdhash', '--version'], capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise ImportError("sdhash is not installed or not found in PATH. "
                          "Please install it (e.g., 'apt-get install sdhash' or from source).")

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


def generate_sdbf(file_path, output_sdbf):
    """Generate an SDBF file from a given file path."""
    try:
        result = subprocess.run(
            ["sdhash", "-r", file_path, "-o", output_sdbf, "-p", "8"], 
            check=True, capture_output=True, text=True
        )
        #print(f"Generated SDBF for {file_path}: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating SDBF for {file_path}: {e.stderr}")
        raise 

def compare_sdhf(temp_file_i, temp_file_j, threshold=None):
    """Compare two SDBF files and return the similarity score (0-1)."""
    cmd = ["sdhash", "-c", temp_file_i+".sdbf", temp_file_j+".sdbf","-t", str(threshold)]
    try:
        result = subprocess.run(
            cmd,
            check=True, capture_output=True, text=True
        )
        parts = result.stdout.strip().split("|")

        try:
            return(int(parts[2]))
        except:
            return(0)
    except subprocess.CalledProcessError as e:
        print(f"Error comparing {temp_file_i} and {temp_file_j}: {e.stderr}")
        return 0

def process_file(file_path, temp_dir):
    """Function to process a single file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return file_path, None  # Return None for missing files

    temp_sdbf = os.path.join(temp_dir, os.path.basename(file_path))
    generate_sdbf(file_path, temp_sdbf)
    return file_path, temp_sdbf


def process_file(file_path, temp_dir):
    """Function to process a single file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return file_path, None  # Return None for missing files

    temp_sdbf = os.path.join(temp_dir, os.path.basename(file_path))
    generate_sdbf(file_path, temp_sdbf)
    return file_path, temp_sdbf

def compute_distance_matrix(file_paths, threshold=1):
    """Compute pairwise distance matrix efficiently with a similarity threshold."""
    n_files = len(file_paths)
    distance_matrix = np.zeros((n_files, n_files), dtype=np.float32)

    # Generate SDBF files in a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a ThreadPoolExecutor for multithreading
        with ThreadPoolExecutor(max_workers=16) as executor:
            # Use `tqdm` to show progress bar
            results = list(tqdm(executor.map(lambda file_path: process_file(file_path, temp_dir), file_paths), 
                                total=len(file_paths), desc="Processing files"))

        # Create a dictionary of successfully processed SDBF files
        sdbf_files = {file_path: temp_sdbf for file_path, temp_sdbf in results if temp_sdbf is not None}


        # Compute distances for upper triangle and mirror to lower
        total_comparisons = (n_files * (n_files - 1)) // 2
        with tqdm(total=total_comparisons, desc="Computing distances", unit="comparison", leave=False) as pbar:
            for i in range(n_files):
                for j in range(i + 1, n_files):
                    file_i = file_paths[i]
                    file_j = file_paths[j]
                    if file_i in sdbf_files and file_j in sdbf_files:
                        similarity = compare_sdhf(sdbf_files[file_i], sdbf_files[file_j], threshold)
                        try:
                            distance = 1 - (similarity/100)  # Convert similarity (0-1) to distance (0-1)
                        except:
                            distance=1
                        distance_matrix[i, j] = distance
                        distance_matrix[j, i] = distance
                    pbar.update(1)

        print(f"Temporary files cleaned up from {temp_dir}")
    return distance_matrix





def cluster_with_threshold(file_paths,threshold,min_samples=2,noise_labeling = 'Ascending',max_clusters=None):
# Compute distance matrix and run DBSCAN
    distance_matrix = compute_distance_matrix(file_paths, threshold=threshold)
    eps = 1 - (threshold / 100.0)
    db = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = db.fit_predict(distance_matrix)

    # Transform labels based on noise_labeling
    result = []
    noise_cluster = max(labels) + 1 if max(labels) >= 0 else 0
    for label in labels:
        if label == -1:
            if noise_labeling == "Zeros":
                result.append(0)
            else:  # Ascending
                result.append(noise_cluster)
                noise_cluster += 1
        else:
            result.append(label)

    # Apply max_clusters constraint if specified
    if max_clusters is not None and max_clusters > 0:
        cluster_sizes = {}
        for label in result:
            cluster_sizes[label] = cluster_sizes.get(label, 0) + 1

        # Exclude noise cluster 0 from consideration if using Zeros
        if noise_labeling == "Zeros" and 0 in cluster_sizes:
            del cluster_sizes[0]

        if len(cluster_sizes) > max_clusters:
            # Sort clusters by size and select top max_clusters
            sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)
            allowed_clusters = set(c[0] for c in sorted_clusters[:max_clusters])
            # Reassign non-allowed clusters to -1
            result = [label if label in allowed_clusters else -1 for label in result]
    
    return result


def save_cluster_info(file_paths, labels, threshold, csv_name, output_dir):
    """Save cluster assignments to a CSV file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    data = {
        'File_Path': file_paths,
        'Cluster_Label': labels,
        'Threshold': [threshold] * len(file_paths)
    }
    df = pd.DataFrame(data)
    
    csv_path = os.path.join(output_dir, f"cluster_results_{csv_name}_threshold_{threshold}_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(csv_path, index=False)


if __name__ == "__main__":
    folder_path = ""
    csv_path = "/usr/src/app/Dev/output/merged_csv.csv"
    csv_name='temp.csv'
    output_dir='temp'
    threshold=50
    file_paths = get_files_from_csv(folder_path, csv_path=csv_path, max_files=50)
    #df=compute_distance_matrix(file_paths, threshold=50)\
    labels=cluster_with_threshold(file_paths,threshold)
    save_cluster_info(file_paths, labels, threshold, csv_name, output_dir)

    print()
