# --------------------------- Imports ---------------------------
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from tqdm import tqdm
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading
import math
import numpy as np
import matplotlib.pyplot as plt


import gc
gc.collect()  # Manually trigger garbage collection


def accumulate(df):
    # Use tqdm with groupby to track progress
    print("GROUPING:")
    grouped = df.groupby(['cluster_name', 'cluster'])
    print("Processing")
    summary_rows = []
    for (cname, cluster_num), group in tqdm(grouped, desc="Processing cluster groups"):
        summary_rows.append({
            'cluster': cluster_num,
            'matches': group['matches'].mean(),
            'total': group['total'].mean(),
            'TPrate': group['TPrate'].mean(),
            'cluster_name': cname
        })
    # Memory cleanup
    del grouped, group
    gc.collect()
    return pd.DataFrame(summary_rows)


def loadData(pickle_file,csv_file):
    """
    Loads a Pickle file containing a dictionary mapping (cluster, rule_id) to DataFrames,
    and returns a concatenated DataFrame.

    Args:
        pickle_file (str): Path to the Pickle file.

    Returns:
        pd.DataFrame: Combined DataFrame with all rule evaluation results.
    """
    pickle_file = Path(pickle_file)
    if not pickle_file.exists():
        raise ValueError(f"Pickle file {pickle_file} does not exist.")

    print(f"Loading Pickle file {pickle_file}...")
    try:
        with open(pickle_file, "rb") as f:
            results_map = pickle.load(f)

        # Flatten the dictionary into a single DataFrame
        rows = []
        for (cluster, rule_id), df in results_map.items():
            df = df.copy()
            df["cluster_name"] = cluster
            df["rule_id"] = rule_id
            rows.append(df)

        full_df = pd.concat(rows, ignore_index=True)
        # Clean up raw_data to free memory
        del rows,results_map
        gc.collect()
        full_df = full_df.sample(frac=0.70, random_state=42)

        print(f"Loaded {len(full_df)} rows from Pickle file.")
        acdf=accumulate(full_df)
        result = acdf.groupby('cluster').agg({
            'matches': 'mean',
            'total': 'mean',
            'TPrate': 'mean'
        }).reset_index()
        result['cluster'] = result['cluster'].astype(int)

        
        # Load and process cluster info
        df1 = pd.read_csv(csv_file)
        labels = df1['Cluster_Label'].dropna().astype(int)
        
        # Count cluster sizes
        cluster_sizes = labels[labels >= 0].value_counts()
        
        # Filter clusters with size >= 2
        filtered_clusters = cluster_sizes[cluster_sizes >= 2]
        
        # Create empty DataFrame with columns = unique cluster sizes
        unique_sizes = sorted(filtered_clusters.unique())
        df_new = pd.DataFrame(columns=unique_sizes)
        
        # Fill df_new with TPrate values
        for cluster, size in filtered_clusters.items():
            if cluster in result['cluster'].values:
                tprate = result.loc[result['cluster'] == cluster, 'TPrate'].iloc[0]
                df_new.loc[cluster, size] = tprate
        del labels, cluster_sizes, df1, result
        gc.collect()  # Free memory after processing cluster sizes and intermediate DataFrames
        # Clean the final DataFrame
        result_df = df_new.apply(lambda col: pd.Series(col.dropna().tolist()), axis=0)
        result_df = result_df.reset_index(drop=True)
        del acdf, df
        gc.collect()
               
        return result_df
    except Exception as e:
        raise ValueError(f"Error loading or processing Pickle file: {e}")


import matplotlib.pyplot as plt



pklpath = [
    "./sdhashYara/sdhashTh50.pkl",
    "./sdhashYara/sdhashTh60.pkl",
    "./sdhashYara/sdhashTh70.pkl",
    "./sdhashYara/sdhashTh80.pkl",
    "./sdhashYara/sdhashTh90.pkl"
]

csvpaths = [
    "/home/mabon/research/Autoyara/YaraResults/clusterCSV/sdhash/th50.csv",
    "/home/mabon/research/Autoyara/YaraResults/clusterCSV/sdhash/th60.csv",
    "/home/mabon/research/Autoyara/YaraResults/clusterCSV/sdhash/th70.csv",
    "/home/mabon/research/Autoyara/YaraResults/clusterCSV/sdhash/th80.csv",
    "/home/mabon/research/Autoyara/YaraResults/clusterCSV/sdhash/th90.csv"
]
df = []

# Create a new directory for saving DataFrames
output_dir = Path("ProcessedDatasdhashRTBFyara")
output_dir.mkdir(exist_ok=True)

df = []
preloaded=True

# Loop through pickle and CSV paths, load DataFrames, and save as CSV
for pkl, csv in zip(pklpath, csvpaths):
    threshold = Path(pkl).stem.replace('SSdeep', '')  # Extract 'th50', 'th60', etc.
    output_csv = output_dir / f"{threshold}.csv"

    if preloaded and output_csv.exists():
        # Load pre-saved CSV
        dataframe = pd.read_csv(output_csv)
        print(f"Loaded pre-saved DataFrame from {output_csv}")
        print(f"DataFrame shape: {dataframe.shape}")
    else:
        # Load the DataFrame using custom logic (e.g., from pickle and raw CSV)
        dataframe = loadData(pkl, csv)

        # Save the DataFrame as CSV
        dataframe.to_csv(output_csv, index=False)
        print(f"Saved DataFrame to {output_csv}")

    df.append(dataframe)

    # Clean up memory
    del dataframe
    gc.collect()

# Replace df_cluster_updated with your actual list of DataFrames
all_data = pd.concat(df, ignore_index=True)

# Flatten and clean the data
values = all_data.values.flatten()
values = values[~pd.isna(values)]  # Remove None/NaN values

# Calculate mean and standard deviation
mean_value = np.mean(values) * 100
std_value = np.std(values) * 100

# Print LaTeX-formatted result
print(f" ${mean_value:.9f} \\pm {std_value:.9f}$")