import os
import random
from pathlib import Path
import math

def read_binary_file(file_path, max_size=1024 * 1024):
    """Safely read binary file with size limit"""
    try:
        with open(file_path, 'rb') as f:
            return f.read(max_size)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def create_split_directories(input_dir, files, base_output_dir, dataset_name, split_num, train_ratio):
    """
    Create and populate split directories for a given ratio

    Args:
        input_dir: Source directory containing files
        files: List of files to split
        base_output_dir: Base output directory
        dataset_name: Name of the dataset (e.g., 'Cluster2_Size100')
        split_num: Split iteration number
        train_ratio: Ratio for training set (e.g., 0.5 for 50/50 split)
    """
    # Calculate split sizes
    total_files = len(files)
    train_size = math.floor(total_files * train_ratio) # we floor train_size so that test_size is always > 0

    # Create directory names
    train_ratio_str = str(int(train_ratio * 100))
    test_ratio_str = str(int((1 - train_ratio) * 100))
    dir_suffix = f"{train_ratio_str}_{test_ratio_str}_{split_num}"

    # Create directories
    train_dir = os.path.join(base_output_dir, f"{dataset_name}_{dir_suffix}", "Train")
    test_dir = os.path.join(base_output_dir, f"{dataset_name}_{dir_suffix}", "Test")

    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    # Split files
    random.shuffle(files)
    train_files = files[:train_size]
    test_files = files[train_size:]

    # Copy files to respective directories
    for src_file in train_files:
        src_path = Path(src_file)
        dst_path = Path(train_dir) / src_path.name
        content = read_binary_file(str(src_path))
        if content:
            with open(dst_path, 'wb') as f:
                f.write(content)

    for src_file in test_files:
        src_path = Path(src_file)
        dst_path = Path(test_dir) / src_path.name
        content = read_binary_file(str(src_path))
        if content:
            with open(dst_path, 'wb') as f:
                f.write(content)


def main():
    # Define directories
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.join(project_root, "mlsec-prototype")

    input_base_dir = os.path.join(project_root, "input_testing", "malicious", "output_preprocessed")
    validation_dir = os.path.join(project_root, "input_testing", "malicious", "split_validation")

    # Create base validation directory
    os.makedirs(validation_dir, exist_ok=True)

    # Dataset configurations
    datasets = ["Cluster0_Size134", "Cluster2_Size100", "Cluster3_Size53", "Cluster10_Size10"]

    for dataset in datasets:
        input_dir = os.path.join(input_base_dir, dataset)

        # Collect all files
        exe_files = []
        for file_path in Path(input_dir).glob('*'):
            content = read_binary_file(str(file_path))
            if content:
                exe_files.append(str(file_path))

        if not exe_files:
            print(f"No files found in {input_dir}")
            continue

        print(f"Processing {dataset}: Found {len(exe_files)} files")

        # Create 5 iterations of 50/50 splits
        for i in range(5):
            create_split_directories(input_dir, exe_files.copy(), validation_dir,
                                     dataset, i+1, train_ratio=0.5)

        # Create 5 iterations of 10/90 splits
        for i in range(5):
            create_split_directories(input_dir, exe_files.copy(), validation_dir,
                                     dataset, i+1, train_ratio=0.1)

if __name__ == "__main__":
    main()