import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import os
import time

def loadSimScores(path,thresholdVal):
    # Read the file line by line
    with open(path, "r") as file:
        lines = file.readlines()

    # Split data into columns
    df = pd.DataFrame([line.strip().split("|") for line in lines], columns=["File1", "File2", "Similarity", "Value1", "Value2", "Value3" ])

    # Drop "Value1" and "Value2" columns
    df = df.drop(columns=["Value1", "Value2", "Value3"])
    # Assuming your DataFrame is called 'df'
    prefix = "/usr/src/app/datacopy/tempfile/"

    # Method 1: Using str.replace()
    df['File1'] = df['File1'].str.replace(prefix, '')
    df['File2'] = df['File2'].str.replace(prefix, '') 
    df["Similarity"] = pd.to_numeric(df["Similarity"], errors="coerce")
    df["Similarity"].fillna(0, inplace=True)
    df["Similarity"] = df["Similarity"].astype(int)

    # Drop rows where Similarity is less than the threshold
    df = df[df["Similarity"] >= thresholdVal]
    return df


def loadCSV(csv_path = "/usr/src/app/Dev/output/merged_csv.csv"):
    dfPath = pd.read_csv(csv_path)
    if 'File_Name' not in dfPath.columns or 'Full_Path' not in dfPath.columns:
        raise ValueError("CSV must contain 'File_Name' and 'Full_Path' columns")

    file_paths = dfPath['File_Name'].tolist()
    return file_paths

def create_distance_matrix(file_paths, df, file_col1='File1', file_col2='File2', sim_col='Similarity'):
    # Use the provided file_paths list instead of deriving from DataFrame
    n_files = len(file_paths)
    
    # Create a mapping of file paths to indices
    file_to_idx = {file: idx for idx, file in enumerate(file_paths)}
    
    # Initialize empty distance matrix
    distance_matrix = np.ones((n_files, n_files))

    count=0
    # Fill the matrix with similarity values from DataFrame
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Building distance matrix"):
        file1 = row[file_col1]
        file2 = row[file_col2]
        similarity = row[sim_col]
        
        # Check if both files exist in file_paths
        if file1 in file_to_idx and file2 in file_to_idx:
            idx1 = file_to_idx[file1]
            idx2 = file_to_idx[file2]
            
            # Fill both symmetric positions with actual similarity
            distance_matrix[idx1, idx2] =  1 - (similarity/100)
            distance_matrix[idx2, idx1] =  1 - (similarity/100)
            count+=1

            continue
    
    return distance_matrix,count

def computeScan(savepath,path='matchth60',thresholdVal=60,pcd=False):
    df=loadSimScores(path,thresholdVal)
    file_paths=loadCSV()
    if pcd==True:
        loaded_data = np.load(savepath)
        distance_matrix = loaded_data['distance_matrix']
    else:
        distance_matrix,count=create_distance_matrix(file_paths, df, file_col1='File1', file_col2='File2', sim_col='Similarity')
        np.savez(savepath, distance_matrix=distance_matrix)
        print("SANTY",count)


    return distance_matrix,file_paths


def DbSCAN(distance_matrix,file_paths):
    # Define DBSCAN parameters
    min_samples=2
    eps = 1 - (60 / 100.0)
    db = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = db.fit_predict(distance_matrix)

    path_to_cluster = {}
    noise_cluster = max(labels) + 1 if max(labels) >= 0 else 0
    noise_labeling = 'Ascending'

    for idx, (file, label) in tqdm(enumerate(zip(file_paths, labels)), 
                                    total=len(file_paths), 
                                    desc="Processing file labels"):
        if label == -1:
            if noise_labeling == "Zeros":
                transformed_cluster_num = 0
            elif noise_labeling == "Ascending":
                transformed_cluster_num = noise_cluster
                noise_cluster += 1
            else:
                raise ValueError(f"Invalid noise_labeling: {noise_labeling}")
        else:
            transformed_cluster_num = label
        path_to_cluster[file] = transformed_cluster_num
        max_clusters=None
        if max_clusters is not None:
            cluster_sizes = {}
            for label in path_to_cluster.values():
                cluster_sizes[label] = cluster_sizes.get(label, 0) + 1
            
            if noise_labeling == "Zeros" and 0 in cluster_sizes:
                del cluster_sizes[0]
            sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)
            
            if len(sorted_clusters) > max_clusters:
                allowed_clusters = set(c[0] for c in sorted_clusters[:max_clusters])
                for file in path_to_cluster:
                    if path_to_cluster[file] not in allowed_clusters:
                        path_to_cluster[file] = -1
    return [path_to_cluster[file] for file in file_paths]


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
def plot_clusters(file_paths, labels, similarity_threshold, csv_name, output_dir):
    """Generate and save a histogram of cluster sizes."""
    cluster_sizes = {label: labels.count(label) for label in set(labels) if label >= 0}
    
    if not cluster_sizes:
        return

    sizes = list(cluster_sizes.values())
    plt.figure(figsize=(10, 6))
    plt.hist(sizes, bins=range(min(sizes), max(sizes) + 2), align='left', rwidth=0.8, color='skyblue', edgecolor='black')
    plt.xlabel("Cluster Size")
    plt.ylabel("Frequency")
    plt.title(f"Threshold {similarity_threshold}% - {csv_name}")
    plt.grid(True, alpha=0.3)
    plot_path = os.path.join(output_dir, f"cluster_histogram_threshold_{similarity_threshold}_{time.strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(plot_path)
    plt.close()
        
def main():
    threshold=60
    output_dir = "newtest/sdhash/"
    csv_name='merge'
    distance_matrix,file_paths=computeScan(savepath='newtest/sdhash/distanceth60Mt.npz',path='sdhashexp/matchth60',thresholdVal=threshold,pcd=True)
    labels=DbSCAN(distance_matrix,file_paths)
    save_cluster_info(file_paths, labels, threshold, csv_name, output_dir)
    plot_clusters(file_paths, labels, threshold, csv_name, output_dir)


if __name__ == "__main__":
    main()