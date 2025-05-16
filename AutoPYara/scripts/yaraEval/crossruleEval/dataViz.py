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

def plot_cluster_std_dev_boxplot_static_all(dfs, drop_smallest_n=0, output_file='cluster_std_dev_boxplot_all.png'):
    """
    Plot boxplots for standard deviations by cluster size across multiple DataFrames,
    dropping the specified number of smallest cluster sizes, using the same x-axis (cluster sizes) with
    ticks at intervals of 100 applied to all subplots, leaving blank spaces for missing sizes,
    with a shared y-axis scale, and superimpose both the cumulative moving average (red) and a
    sliding window average (window size 5, blue) of the median on the same subplot.

    Parameters:
    - dfs: List of 5 pandas DataFrames
    - drop_smallest_n: Integer, number of smallest cluster sizes to drop (default: 0)
    - output_file: File path to save the output PNG
    """
    # Validate input
    if not all(isinstance(df, pd.DataFrame) for df in dfs):
        raise ValueError("All items in input list must be pandas DataFrames")
    if len(dfs) != 5:
        raise ValueError("Expected exactly 5 DataFrames")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    # Titles for each subplot
    titles = ['Th50', 'Th60', 'Th70', 'Th80', 'Th90']
    
    # Create subplots with shared x and y axes
    fig, axs = plt.subplots(nrows=5, ncols=1, figsize=(12, 18), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.4)

    # Initialize variables to track global y-axis limits
    global_min = float('inf')
    global_max = float('-inf')

    # Collect all unique cluster sizes across all DataFrames
    all_sizes = set()
    for df in dfs:
        # Convert None to NaN and ensure numeric data
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        try:
            sizes = df.columns.astype(int).tolist()
            all_sizes.update(sizes)
        except ValueError:
            continue
    
    # Sort cluster sizes for consistent x-axis
    all_sizes = sorted(list(all_sizes))
    if not all_sizes:
        raise ValueError("No valid cluster sizes found in any DataFrame")

    # Drop the specified number of smallest cluster sizes
    if drop_smallest_n > 0:
        if len(all_sizes) > drop_smallest_n:
            sizes_to_drop = all_sizes[:drop_smallest_n]
            all_sizes = all_sizes[drop_smallest_n:]
            print(f"Dropping the smallest {drop_smallest_n} cluster sizes: {sizes_to_drop}")
        else:
            all_sizes = []
            print(f"Requested to drop {drop_smallest_n} sizes, but only {len(all_sizes)} available; all sizes dropped")
    else:
        print("No cluster sizes dropped (drop_smallest_n=0)")

    if not all_sizes:
        raise ValueError("No cluster sizes remain after dropping")

    # Filter each DataFrame to exclude the dropped cluster sizes
    filtered_dfs = []
    for df in dfs:
        # Convert None to NaN and ensure numeric data
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        # Keep only columns corresponding to remaining cluster sizes
        remaining_columns = [col for col in df.columns if int(col) in all_sizes]
        filtered_df = df[remaining_columns]
        filtered_dfs.append(filtered_df)

    # Determine x-axis ticks at intervals of 100 based on remaining sizes
    max_size = max(all_sizes)
    min_size = min(all_sizes)
    # Start ticks at the nearest multiple of 100 below min_size
    tick_start = (min_size // 100) * 100
    tick_sizes = list(range(tick_start, max_size + 100, 100))  # Step by 100
    # Map ticks to positions (1-based for boxplot, proportional to index in all_sizes)
    tick_positions = []
    for tick in tick_sizes:
        # Find the closest cluster size to the tick
        closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
        tick_positions.append(closest_idx + 1)

    # First pass: Determine global y-axis limits using filtered DataFrames
    for df in filtered_dfs:
        for size in all_sizes:
            if str(size) in df.columns:
                data = df[str(size)].dropna().tolist()
                if data:  # Only consider non-empty datasets
                    global_min = min(global_min, min(data))
                    global_max = max(global_max, max(data))

    # Ensure valid y-axis limits
    if global_min == float('inf') or global_max == float('-inf'):
        global_min, global_max = 0, 1  # Fallback limits if no valid data
    else:
        # Add padding to y-axis limits
        padding = (global_max - global_min) * 0.05
        global_min -= padding
        global_max += padding

    # Second pass: Plotting
    for i, (df, ax) in enumerate(zip(filtered_dfs, axs)):
        # Prepare datasets for all remaining cluster sizes, using empty lists for missing sizes
        datasets = []
        sizes_with_data = []
        for size in all_sizes:
            if str(size) in df.columns:
                data = df[str(size)].dropna().tolist()
                datasets.append(data)
                if data:
                    sizes_with_data.append(size)
            else:
                datasets.append([])  # Empty dataset for missing cluster size

        if not any(datasets):
            ax.set_title(f'{titles[i]}: No valid data')
            ax.set_ylabel('Standard Deviation')
            ax.set_xlabel('Cluster Size (Number of Items)')
            print(f"Subplot {titles[i]}: No valid data to plot")
            continue

        # Debugging: Print sizes with data
        print(f"Subplot {titles[i]}: sizes_with_data = {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")

        # Boxplot: One box per cluster size, empty datasets result in no box
        box = ax.boxplot(datasets, positions=range(1, len(all_sizes) + 1), 
                         labels=[str(s) for s in all_sizes], patch_artist=True)
        
        # Calculate the median for each dataset (only for non-empty datasets)
        medians = [np.median(d) if d else np.nan for d in datasets]
        
        # Compute the cumulative moving average and sliding window average, ignoring NaN medians
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [i + 1 for i, d in enumerate(datasets) if d]
        if valid_medians:
            # Cumulative average (red, solid line with circles)
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            ax.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, color='red', marker='o', 
                    label='Cumulative Avg of Median', linestyle='-', linewidth=2)

            # Sliding window average (window size 5, blue, dashed line with squares)
            window_size = 5
            sliding_avg = []
            for j in range(len(valid_medians)):
                start = max(0, j - window_size + 1)
                window = valid_medians[start:j + 1]
                sliding_avg.append(np.mean(window))
            ax.plot(valid_positions[:len(sliding_avg)], sliding_avg, color='blue', marker='s', 
                    label='Sliding Window Avg (size 5)', linestyle='--', linewidth=2)

            ax.legend()

        ax.set_title(titles[i])
        ax.set_ylabel('Standard Deviation')
        ax.set_xlabel('Cluster Size (Number of Items)')

        # Set y-axis limits
        ax.set_ylim(0, 1)

    # Explicitly set x-ticks on the last subplot (shared across all due to sharex=True)
    if tick_positions:
        axs[-1].set_xticks(tick_positions)
        axs[-1].set_xticklabels([str(tick) for tick in tick_sizes])
        print(f"Setting x-ticks on last subplot: {tick_sizes} (positions: {tick_positions})")
    else:
        print("No valid tick positions found")

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')
    plt.close(fig)


if __name__ == '__main__':
    pklpath = [
        "../BestYaraCrossEval/ssdeep/th50.pkl",
        "../BestYaraCrossEval/ssdeep/th60.pkl",
        "../BestYaraCrossEval/ssdeep/th70.pkl",
        "../BestYaraCrossEval/ssdeep/th80.pkl",
        "../BestYaraCrossEval/ssdeep/th90.pkl"
    ]
    
    csvpaths = [
        "/home/mabon/research/Autoyara/YaraResults/clusterCSV/ssdeep/th50.csv",
        "/home/mabon/research/Autoyara/YaraResults/clusterCSV/ssdeep/th60.csv",
        "/home/mabon/research/Autoyara/YaraResults/clusterCSV/ssdeep/th70.csv",
        "/home/mabon/research/Autoyara/YaraResults/clusterCSV/ssdeep/th80.csv",
        "/home/mabon/research/Autoyara/YaraResults/clusterCSV/ssdeep/th90.csv"
    ]

    df = []
    
    # Create a new directory for saving DataFrames
    output_dir = Path("ProcessedData")
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
    plot_cluster_std_dev_boxplot_static_all(df,drop_smallest_n=0, output_file='ssdeep_BestYaraCross.pdf')
    plot_cluster_std_dev_boxplot_static_all(df,drop_smallest_n=25, output_file='ssdeep_BestYaraCross_dropsmall.pdf')
