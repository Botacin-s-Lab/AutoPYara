import re
import pandas as pd
import matplotlib.pyplot as plt
from fractions import Fraction
import plotly.graph_objects as go
import numpy as np
from matplotlib.ticker import ScalarFormatter, LogLocator
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import matplotlib.cm



def plot_tprates_ratioComp(tprateAutoyaraBase_Train_df, tprateAutoyaraBase_Test, tprateAutoPYara_Train, tprateAutoPYara_Test, df_root,filename,thv):
    """
    Plot eight subplots (4x2 grid), one row per dataset (AutoYaraBase Train/Test, AutoPYara Train/Test),
    with the left column showing sliding window average (window size 5) and the right column showing
    cumulative moving average of TP rates against cluster sizes (from df_root) for three ratio thresholds
    (0.25, 0.5, 0.75). Uses shared x-axis (cluster sizes, ticks at intervals of 100) and y-axis (0 to 1).
    Saves as a PDF.

    Parameters:
    - tprateAutoyaraBase_Train_df: List of 3 DataFrames (Ratios 0.25, 0.5, 0.75)
    - tprateAutoyaraBase_Test: List of 3 DataFrames
    - tprateAutoPYara_Train: List of 3 DataFrames
    - tprateAutoPYara_Test: List of 3 DataFrames
    - df_root: DataFrame with 'File_Path', 'SHA256', 'SSDeep', 'Cluster_Label', 'Threshold' columns
    """
    # Validate input
    dfs_lists = [
        tprateAutoyaraBase_Train_df,
        tprateAutoyaraBase_Test,
        tprateAutoPYara_Train,
        tprateAutoPYara_Test
    ]
    titles = ['AutoYaraBase Train', 'AutoYaraBase Test', 'AutoPYara Train', 'AutoPYara Test']
    colormaps = ['Blues', 'Oranges', 'Greens', 'Reds']
    ratios = ['0.25', '0.5', '0.75']
    if not all(isinstance(df_list, list) and len(df_list) == 3 and all(isinstance(df, pd.DataFrame) for df in df_list) for df_list in dfs_lists):
        raise ValueError("Each input must be a list of exactly 3 pandas DataFrames")
    if not isinstance(df_root, pd.DataFrame):
        raise ValueError("df_root must be a pandas DataFrame")

    # Compute cluster sizes from df_root for Threshold=50
    cluster_sizes = df_root[df_root['Threshold'] == thv].groupby('Cluster_Label').size().reset_index(name='Cluster_Size')
    cluster_size_map = dict(zip(cluster_sizes['Cluster_Label'], cluster_sizes['Cluster_Size']))

    # Collect all unique cluster sizes across all DataFrames
    all_cluster_sizes = set()
    for df_list in dfs_lists:
        for df in df_list:
            df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
            clusters = df['Cluster'].dropna().astype(int).tolist()
            sizes = [cluster_size_map.get(cluster, 0) for cluster in clusters if cluster in cluster_size_map]
            all_cluster_sizes.update(sizes)
    
    # Sort cluster sizes for consistent x-axis
    all_cluster_sizes = sorted(list(all_cluster_sizes))
    if not all_cluster_sizes:
        raise ValueError("No valid cluster sizes found")

    # Create 4x2 subplot grid
    fig, axs = plt.subplots(nrows=4, ncols=2, figsize=(12, 16), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.4, wspace=0.2)

    # Determine x-axis ticks at intervals of 100
    max_size = max(all_cluster_sizes)
    min_size = min(all_cluster_sizes)
    tick_start = (min_size // 100) * 100
    tick_sizes = list(range(tick_start, max_size + 100, 100))
    tick_positions = []
    for tick in tick_sizes:
        closest_idx = min(range(len(all_cluster_sizes)), key=lambda i: abs(all_cluster_sizes[i] - tick))
        tick_positions.append(closest_idx + 1)

    # Process each dataset
    for idx, (df_list, title, cmap) in enumerate(zip(dfs_lists, titles, colormaps)):
        ax_sliding = axs[idx, 0]  # Left column: sliding window
        ax_cumulative = axs[idx, 1]  # Right column: cumulative average
        # Define color shades for each ratio
        color_shades = [
            matplotlib.cm.get_cmap(cmap)(0.4),  # Light shade for Ratio_0.25
            matplotlib.cm.get_cmap(cmap)(0.6),  # Medium shade for Ratio_0.5
            matplotlib.cm.get_cmap(cmap)(0.8)   # Dark shade for Ratio_0.75
        ]

        # Process each ratio
        for df, ratio, color in zip(df_list, ratios, color_shades):
            df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
            # Map clusters to sizes and compute TP rates
            tprates = []
            sizes_with_data = []
            for size in all_cluster_sizes:
                clusters_for_size = [c for c, s in cluster_size_map.items() if s == size]
                data = df[df['Cluster'].isin(clusters_for_size)]['TP_Rate'].dropna().tolist()
                if data:
                    tprates.append(np.median(data))  # Median if multiple clusters have same size
                    sizes_with_data.append(size)
                else:
                    tprates.append(np.nan)

            if not sizes_with_data:
                print(f"{title} (Ratio {ratio}): No valid data to plot")
                continue

            # Debugging: Print sizes with data
            print(f"{title} (Ratio {ratio}): sizes_with_data = {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")

            # Compute averages
            valid_tprates = [t for t in tprates if not np.isnan(t)]
            valid_positions = [i + 1 for i, t in enumerate(tprates) if not np.isnan(t)]
            if valid_tprates:
                # Sliding window average (left subplot)
                window_size = 5
                sliding_avg = []
                for j in range(len(valid_tprates)):
                    start = max(0, j - window_size + 1)
                    window = valid_tprates[start:j + 1]
                    sliding_avg.append(np.mean(window))
                ax_sliding.plot(valid_positions[:len(sliding_avg)], sliding_avg, color=color, marker='s',
                                label=f'Ratio {ratio}', linestyle='--', linewidth=2)

                # Cumulative average (right subplot)
                cumulative_avg = np.cumsum(valid_tprates) / np.arange(1, len(valid_tprates) + 1)
                ax_cumulative.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, color=color, marker='o',
                                  label=f'Ratio {ratio}', linestyle='-', linewidth=2)

        # Configure subplots
        ax_sliding.set_title(f'{title} (Sliding Avg)')
        ax_sliding.set_ylabel('TP Rate')
        ax_sliding.legend()
        ax_sliding.grid(True, linestyle='--', alpha=0.7)

        ax_cumulative.set_title(f'{title} (Cumulative Avg)')
        ax_cumulative.set_ylabel('TP Rate')
        ax_cumulative.legend()
        ax_cumulative.grid(True, linestyle='--', alpha=0.7)

        if idx >= 3:  # Bottom row
            ax_sliding.set_xlabel('Cluster Size (Number of Files)')
            ax_cumulative.set_xlabel('Cluster Size (Number of Files)')

    # Set y-axis limits
    for ax in axs.flat:
        ax.set_ylim(0, 1)

    # Set x-ticks on bottom subplots (shared)
    if tick_positions:
        for ax in axs[3, :]:
            ax.set_xticks(tick_positions)
            ax.set_xticklabels([str(tick) for tick in tick_sizes])
        print(f"Setting x-ticks: {tick_sizes} (positions: {tick_positions})")
    else:
        print("No valid tick positions found")

    plt.tight_layout()
    fig.savefig(filename, format='pdf')
    plt.close(fig)
def sanity_h(tprateAutoyaraBase_Train_df, tprateAutoyaraBase_Test, tprateAutoPYara_Train, tprateAutoPYara_Test, df_root,thv):
    """
    Compute the smallest cluster size with valid TP rate data from the input DataFrame lists.

    Parameters:
    - tprateAutoyaraBase_Train_df: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoyaraBase_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Train: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - df_root: DataFrame with 'File_Path', 'SHA256', 'SSDeep', 'Cluster_Label', 'Threshold' columns

    Returns:
    - Smallest cluster size with valid data (integer)
    """
    # Validate input
    dfs_lists = [
        tprateAutoyaraBase_Train_df,
        tprateAutoyaraBase_Test,
        tprateAutoPYara_Train,
        tprateAutoPYara_Test
    ]
    if not all(isinstance(df_list, list) and all(isinstance(df, pd.DataFrame) for df in df_list) for df_list in dfs_lists):
        raise ValueError("All inputs must be lists of pandas DataFrames")
    if not isinstance(df_root, pd.DataFrame):
        raise ValueError("df_root must be a pandas DataFrame")

    # Compute cluster sizes from df_root for Threshold=50
    cluster_sizes = df_root[df_root['Threshold'] == thv].groupby('Cluster_Label').size().reset_index(name='Cluster_Size')
    cluster_size_map = dict(zip(cluster_sizes['Cluster_Label'], cluster_sizes['Cluster_Size']))

    # Collect all clusters with valid TP rate data
    valid_clusters = set()
    for df_list in dfs_lists:
        for df in df_list:
            df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
            clusters = df['Cluster'].dropna().astype(int).tolist()
            valid_clusters.update(clusters)

    # Map valid clusters to their sizes
    valid_sizes = [cluster_size_map.get(cluster, float('inf')) for cluster in valid_clusters if cluster in cluster_size_map]
    
    if not valid_sizes:
        raise ValueError("No valid cluster sizes found with TP rate data")
    
    # Return the smallest cluster size
    smallest_size = int(min(valid_sizes))
    print(smallest_size)
    
def plot_tprates_base_h(tprateAutoyaraBase_Train_df, tprateAutoyaraBase_Test, tprateAutoPYara_Train, tprateAutoPYara_Test, df_root,fileName,thv):
    """
    Plot the cumulative moving average and sliding window average (window size 5) of median TP rates
    against cluster sizes (derived from df_root) across four lists of DataFrames, using a shared x-axis
    (cluster sizes with ticks at intervals of 100) and a shared y-axis (0 to 1). Saves the plot as a PDF.

    Parameters:
    - tprateAutoyaraBase_Train_df: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoyaraBase_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Train: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - df_root: DataFrame with 'File_Path', 'SHA256', 'SSDeep', 'Cluster_Label', 'Threshold' columns
    """
    # Validate input
    dfs_lists = [
        tprateAutoyaraBase_Train_df,
        tprateAutoyaraBase_Test,
        tprateAutoPYara_Train,
        tprateAutoPYara_Test
    ]
    titles = ['AutoYaraBase Train', 'AutoYaraBase Test', 'AutoPYara Train', 'AutoPYara Test']
    if not all(isinstance(df_list, list) and all(isinstance(df, pd.DataFrame) for df in df_list) for df_list in dfs_lists):
        raise ValueError("All inputs must be lists of pandas DataFrames")
    if not isinstance(df_root, pd.DataFrame):
        raise ValueError("df_root must be a pandas DataFrame")

    # Compute cluster sizes from df_root for the specified threshold (assuming Threshold=50)
    cluster_sizes = df_root[df_root['Threshold'] == thv].groupby('Cluster_Label').size().reset_index(name='Cluster_Size')
    cluster_size_map = dict(zip(cluster_sizes['Cluster_Label'], cluster_sizes['Cluster_Size']))

    # Collect all unique cluster sizes across all DataFrames
    all_cluster_sizes = set()
    for df_list in dfs_lists:
        for df in df_list:
            df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
            clusters = df['Cluster'].dropna().astype(int).tolist()
            # Map clusters to sizes
            sizes = [cluster_size_map.get(cluster, 0) for cluster in clusters if cluster in cluster_size_map]
            all_cluster_sizes.update(sizes)
    
    # Sort cluster sizes for consistent x-axis
    all_cluster_sizes = sorted(list(all_cluster_sizes))
    if not all_cluster_sizes:
        raise ValueError("No valid cluster sizes found")

    # Create subplots with shared x and y axes
    fig, axs = plt.subplots(nrows=4, ncols=1, figsize=(12, 14), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.4)

    # Determine x-axis ticks at intervals of 100
    max_size = max(all_cluster_sizes)
    min_size = min(all_cluster_sizes)
    tick_start = (min_size // 100) * 100
    tick_sizes = list(range(tick_start, max_size + 100, 100))
    tick_positions = []
    for tick in tick_sizes:
        closest_idx = min(range(len(all_cluster_sizes)), key=lambda i: abs(all_cluster_sizes[i] - tick))
        tick_positions.append(closest_idx + 1)

    # Process each dataset (list of DataFrames)
    for i, (df_list, ax) in enumerate(zip(dfs_lists, axs)):
        # Combine all DataFrames in the list
        combined_df = pd.concat([df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce') for df in df_list], ignore_index=True)
        
        # Map clusters to sizes and prepare median TP rates
        medians = []
        sizes_with_data = []
        for size in all_cluster_sizes:
            # Find clusters corresponding to this size
            clusters_for_size = [c for c, s in cluster_size_map.items() if s == size]
            data = combined_df[combined_df['Cluster'].isin(clusters_for_size)]['TP_Rate'].dropna().tolist()
            if data:
                medians.append(np.median(data))
                sizes_with_data.append(size)
            else:
                medians.append(np.nan)

        if not sizes_with_data:
            ax.set_title(f'{titles[i]}: No valid data')
            ax.set_ylabel('TP Rate')
            ax.set_xlabel('Cluster Size (Number of Files)')
            print(f"Subplot {titles[i]}: No valid data to plot")
            continue

        # Debugging: Print sizes with data
        print(f"Subplot {titles[i]}: sizes_with_data = {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")

        # Compute cumulative and sliding window averages, ignoring NaN medians
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [i + 1 for i, m in enumerate(medians) if not np.isnan(m)]
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
        ax.set_ylabel('TP Rate')
        ax.set_xlabel('Cluster Size (Number of Files)')

        # Set y-axis limits
        ax.set_ylim(0, 1)

    # Set x-ticks on the last subplot (shared across all due to sharex=True)
    if tick_positions:
        axs[-1].set_xticks(tick_positions)
        axs[-1].set_xticklabels([str(tick) for tick in tick_sizes])
        print(f"Setting x-ticks on last subplot: {tick_sizes} (positions: {tick_positions})")
    else:
        print("No valid tick positions found")

    plt.tight_layout()
    fig.savefig(fileName, format='pdf')
    plt.close(fig)




def collect_tprate_data(base_path,name):
    # Initialize lists to store data
    cluster_numbers = []
    tp_rates = []
    
    # Pattern to match cluster folders (cluster_*)
    folder_pattern = os.path.join(base_path, 'cluster_*')
    
    # Find all matching folders
    for folder in glob.glob(folder_pattern):
        # Extract cluster number from folder name
        cluster_num = os.path.basename(folder).replace('cluster_', '')
        
        # Path to tprateAutoPYara_Train.txt
        file_path = os.path.join(folder,name)
        
        # Check if file exists
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    # Extract TP rate using regex
                    match = re.search(r'TP Rate: (\d+\.\d+)', content)
                    if match:
                        tp_rate = float(match.group(1))
                        cluster_numbers.append(cluster_num)
                        tp_rates.append(tp_rate)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Create DataFrame
    df = pd.DataFrame({
        'Cluster': cluster_numbers,
        'TP_Rate': tp_rates
    })
    
    # Sort by cluster number if needed
    df['Cluster'] = df['Cluster'].astype(int)
    df = df.sort_values('Cluster').reset_index(drop=True)
    
    return df



def plot_tprates_cmp_h(tprateAutoyaraBase_Train_df, tprateAutoyaraBase_Test, tprateAutoPYara_Train, tprateAutoPYara_Test, df_root,fileName,thv):
    """
    Plot two subfigures: one for sliding window average (window size 5) and one for cumulative moving
    average of median TP rates against cluster sizes (derived from df_root) for four datasets, using a
    shared x-axis (cluster sizes with ticks at intervals of 100) and y-axis (0 to 1). All datasets are
    plotted on the same subfigure with different colors. Saves the plot as a PDF.

    Parameters:
    - tprateAutoyaraBase_Train_df: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoyaraBase_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Train: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - df_root: DataFrame with 'File_Path', 'SHA256', 'SSDeep', 'Cluster_Label', 'Threshold' columns
    """
    # Validate input
    dfs_lists = [
        tprateAutoyaraBase_Train_df,
        tprateAutoyaraBase_Test,
        tprateAutoPYara_Train,
        tprateAutoPYara_Test
    ]
    titles = ['AutoYaraBase Train', 'AutoYaraBase Test', 'AutoPYara Train', 'AutoPYara Test']
    colors = ['blue', 'orange', 'green', 'red']
    if not all(isinstance(df_list, list) and all(isinstance(df, pd.DataFrame) for df in df_list) for df_list in dfs_lists):
        raise ValueError("All inputs must be lists of pandas DataFrames")
    if not isinstance(df_root, pd.DataFrame):
        raise ValueError("df_root must be a pandas DataFrame")

    # Compute cluster sizes from df_root for Threshold=50
    cluster_sizes = df_root[df_root['Threshold'] == thv].groupby('Cluster_Label').size().reset_index(name='Cluster_Size')
    cluster_size_map = dict(zip(cluster_sizes['Cluster_Label'], cluster_sizes['Cluster_Size']))

    # Collect all unique cluster sizes across all DataFrames
    all_cluster_sizes = set()
    for df_list in dfs_lists:
        for df in df_list:
            df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
            clusters = df['Cluster'].dropna().astype(int).tolist()
            sizes = [cluster_size_map.get(cluster, 0) for cluster in clusters if cluster in cluster_size_map]
            all_cluster_sizes.update(sizes)
    
    # Sort cluster sizes for consistent x-axis
    all_cluster_sizes = sorted(list(all_cluster_sizes))
    if not all_cluster_sizes:
        raise ValueError("No valid cluster sizes found")

    # Create two subfigures (2 rows, 1 column) with shared x and y axes
    fig, (ax_sliding, ax_cumulative) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.3)

    # Determine x-axis ticks at intervals of 100
    max_size = max(all_cluster_sizes)
    min_size = min(all_cluster_sizes)
    tick_start = (min_size // 100) * 100
    tick_sizes = list(range(tick_start, max_size + 100, 100))
    tick_positions = []
    for tick in tick_sizes:
        closest_idx = min(range(len(all_cluster_sizes)), key=lambda i: abs(all_cluster_sizes[i] - tick))
        tick_positions.append(closest_idx + 1)

    # Process each dataset
    for df_list, title, color in zip(dfs_lists, titles, colors):
        # Combine all DataFrames in the list
        combined_df = pd.concat([df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce') for df in df_list], ignore_index=True)
        
        # Map clusters to sizes and compute median TP rates
        medians = []
        sizes_with_data = []
        for size in all_cluster_sizes:
            clusters_for_size = [c for c, s in cluster_size_map.items() if s == size]
            data = combined_df[combined_df['Cluster'].isin(clusters_for_size)]['TP_Rate'].dropna().tolist()
            if data:
                medians.append(np.median(data))
                sizes_with_data.append(size)
            else:
                medians.append(np.nan)

        if not sizes_with_data:
            print(f"{title}: No valid data to plot")
            continue

        # Debugging: Print sizes with data
        print(f"{title}: sizes_with_data = {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")

        # Compute averages
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [i + 1 for i, m in enumerate(medians) if not np.isnan(m)]
        if valid_medians:
            # Sliding window average (window size 5, top subfigure)
            window_size = 5
            sliding_avg = []
            for j in range(len(valid_medians)):
                start = max(0, j - window_size + 1)
                window = valid_medians[start:j + 1]
                sliding_avg.append(np.mean(window))
            ax_sliding.plot(valid_positions[:len(sliding_avg)], sliding_avg, color=color, marker='s', 
                            label=f'{title} (Sliding Avg)', linestyle='--', linewidth=2)

            # Cumulative average (bottom subfigure)
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            ax_cumulative.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, color=color, marker='o', 
                              label=f'{title} (Cumulative Avg)', linestyle='-', linewidth=2)

    # Configure subfigures
    ax_sliding.set_title('Sliding Window Average (Window Size 5)')
    ax_sliding.set_ylabel('TP Rate')
    ax_sliding.legend()
    ax_sliding.grid(True, linestyle='--', alpha=0.7)

    ax_cumulative.set_title('Cumulative Moving Average')
    ax_cumulative.set_ylabel('TP Rate')
    ax_cumulative.set_xlabel('Cluster Size (Number of Files)')
    ax_cumulative.legend()
    ax_cumulative.grid(True, linestyle='--', alpha=0.7)

    # Set y-axis limits
    ax_sliding.set_ylim(0, 1)
    ax_cumulative.set_ylim(0, 1)

    # Set x-ticks on the bottom subfigure (shared)
    if tick_positions:
        ax_cumulative.set_xticks(tick_positions)
        ax_cumulative.set_xticklabels([str(tick) for tick in tick_sizes])
        print(f"Setting x-ticks: {tick_sizes} (positions: {tick_positions})")
    else:
        print("No valid tick positions found")

    plt.tight_layout()
    fig.savefig(fileName, format='pdf')
    plt.close(fig)
def plot_cluster_std_dev_boxplot_static_all_merge_log(
    dfs, drop_smallest_n=0, output_file='cluster_std_dev_boxplot_all.pdf'
):
    """
    Plot boxplots for standard deviations by cluster size across multiple DataFrames,
    dropping the specified number of smallest cluster sizes, using the same x-axis (cluster sizes) with
    ticks at intervals of 100 applied to all subplots, leaving blank spaces for missing sizes,
    with a shared y-axis scale, and superimpose either the cumulative moving average (top) or
    the sliding window average (bottom) of the median on separate subplots.

    Parameters:
    - dfs: List of 5 pandas DataFrames
    - drop_smallest_n: Integer, number of smallest cluster sizes to drop (default: 0)
    - output_file: File path to save the output PDF
    """
    if not all(isinstance(df, pd.DataFrame) for df in dfs):
        raise ValueError("All items in input list must be pandas DataFrames")
    if len(dfs) != 5:
        raise ValueError("Expected exactly 5 DataFrames")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    titles = ['Heurstic', 'Autoyara', 'AutoPyara', 'BestKyara', 'WorstPyara']

    # Collect all unique cluster sizes
    all_sizes = set()
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        try:
            sizes = df.columns.astype(int).tolist()
            all_sizes.update(sizes)
        except ValueError:
            continue

    all_sizes = sorted(list(all_sizes))
    if not all_sizes:
        raise ValueError("No valid cluster sizes found in any DataFrame")

    if drop_smallest_n > 0:
        if len(all_sizes) > drop_smallest_n:
            all_sizes = all_sizes[drop_smallest_n:]
        else:
            all_sizes = []
    if not all_sizes:
        raise ValueError("No cluster sizes remain after dropping")

    # Filter DataFrames
    filtered_dfs = []
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        remaining_columns = [col for col in df.columns if int(col) in all_sizes]
        filtered_df = df[remaining_columns]
        filtered_dfs.append(filtered_df)

    # X-axis ticks
    max_size = max(all_sizes)
    min_size = min(all_sizes)
    tick_start = (min_size // 100) * 100
    tick_sizes = list(range(tick_start, max_size + 100, 100))
    tick_positions = []
    for tick in tick_sizes:
        closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
        tick_positions.append(closest_idx + 1)

    # Global y-axis limits
    global_min = float('inf')
    global_max = float('-inf')
    for df in filtered_dfs:
        for size in all_sizes:
            if size in df.columns:
                data = df[size].dropna().tolist()
                if data:
                    global_min = min(global_min, min(data))
                    global_max = max(global_max, max(data))
    if global_min == float('inf') or global_max == float('-inf'):
        global_min, global_max = 0, 1
    else:
        padding = (global_max - global_min) * 0.05
        global_min -= padding
        global_max += padding

    # Create two stacked subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, sharey=True)

    for i, df in enumerate(filtered_dfs):
        datasets = []
        for size in all_sizes:
            if size in df.columns:
                data = df[size].dropna().tolist()
                datasets.append(data)
            else:
                datasets.append([])

        medians = [np.median(d) if d else np.nan for d in datasets]
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

        # Cumulative median (top plot)
        if valid_medians:
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            ax1.plot(
                valid_positions[:len(cumulative_avg)],
                cumulative_avg,
                linestyle='-',
                linewidth=2,
                label=f'{titles[i]} - Cumulative Median'
            )

        # Sliding window average (bottom plot)
        if valid_medians:
            window_size = 5
            sliding_avg = []
            for j in range(len(valid_medians)):
                start = max(0, j - window_size + 1)
                window = valid_medians[start:j + 1]
                sliding_avg.append(np.mean(window))
            ax2.plot(
                valid_positions[:len(sliding_avg)],
                sliding_avg,
                linestyle='--',
                linewidth=2,
                label=f'{titles[i]} - Sliding Avg'
            )

    # Set x-ticks and labels
    
    for ax in [ax1, ax2]:
        ax.set_xscale('log')
        ax.set_xlabel('Cluster Size (Number of Items)')
        ax.set_ylim(global_min, global_max)
        ax.grid(axis='x', linestyle=':', color='gray', alpha=0.5)
        # Optionally, set ticks as above for clarity
    


    ax1.set_title('Cumulative Median of Cluster Standard Deviations')
    ax1.set_ylabel('True Positive')
    ax1.legend()

    ax2.set_title('Sliding Window Average (Window=5) of Cluster Standard Deviations')
    ax2.set_ylabel('True Positive')
    ax2.legend()

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')
    plt.close(fig)





def plot_cluster_std_dev_boxplot_static_all_merge(
    dfs, drop_smallest_n=0, output_file='cluster_std_dev_boxplot_all.pdf'
):
    """
    Plot boxplots for standard deviations by cluster size across multiple DataFrames,
    dropping the specified number of smallest cluster sizes, using the same x-axis (cluster sizes) with
    ticks at intervals of 100 applied to all subplots, leaving blank spaces for missing sizes,
    with a shared y-axis scale, and superimpose either the cumulative moving average (top) or
    the sliding window average (bottom) of the median on separate subplots.

    Parameters:
    - dfs: List of 5 pandas DataFrames
    - drop_smallest_n: Integer, number of smallest cluster sizes to drop (default: 0)
    - output_file: File path to save the output PDF
    """
    if not all(isinstance(df, pd.DataFrame) for df in dfs):
        raise ValueError("All items in input list must be pandas DataFrames")
    if len(dfs) != 5:
        raise ValueError("Expected exactly 5 DataFrames")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    titles = ['Heurstic', 'Autoyara', 'AutoPyara', 'BestKyara', 'WorstPyara']

    # Collect all unique cluster sizes
    all_sizes = set()
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        try:
            sizes = df.columns.astype(int).tolist()
            all_sizes.update(sizes)
        except ValueError:
            continue

    all_sizes = sorted(list(all_sizes))
    if not all_sizes:
        raise ValueError("No valid cluster sizes found in any DataFrame")

    if drop_smallest_n > 0:
        if len(all_sizes) > drop_smallest_n:
            all_sizes = all_sizes[drop_smallest_n:]
        else:
            all_sizes = []
    if not all_sizes:
        raise ValueError("No cluster sizes remain after dropping")

    # Filter DataFrames
    filtered_dfs = []
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        remaining_columns = [col for col in df.columns if int(col) in all_sizes]
        filtered_df = df[remaining_columns]
        filtered_dfs.append(filtered_df)

    # X-axis ticks
    max_size = max(all_sizes)
    min_size = min(all_sizes)
    tick_start = (min_size // 100) * 100
    tick_sizes = list(range(tick_start, max_size + 100, 100))
    tick_positions = []
    for tick in tick_sizes:
        closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
        tick_positions.append(closest_idx + 1)

    # Global y-axis limits
    global_min = float('inf')
    global_max = float('-inf')
    for df in filtered_dfs:
        for size in all_sizes:
            if size in df.columns:
                data = df[size].dropna().tolist()
                if data:
                    global_min = min(global_min, min(data))
                    global_max = max(global_max, max(data))
    if global_min == float('inf') or global_max == float('-inf'):
        global_min, global_max = 0, 1
    else:
        padding = (global_max - global_min) * 0.05
        global_min -= padding
        global_max += padding

    # Create two stacked subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, sharey=True)

    for i, df in enumerate(filtered_dfs):
        datasets = []
        for size in all_sizes:
            if size in df.columns:
                data = df[size].dropna().tolist()
                datasets.append(data)
            else:
                datasets.append([])

        medians = [np.median(d) if d else np.nan for d in datasets]
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

        # Cumulative median (top plot)
        if valid_medians:
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            ax1.plot(
                valid_positions[:len(cumulative_avg)],
                cumulative_avg,
                linestyle='-',
                linewidth=2,
                label=f'{titles[i]} - Cumulative Median'
            )

        # Sliding window average (bottom plot)
        if valid_medians:
            window_size = 5
            sliding_avg = []
            for j in range(len(valid_medians)):
                start = max(0, j - window_size + 1)
                window = valid_medians[start:j + 1]
                sliding_avg.append(np.mean(window))
            ax2.plot(
                valid_positions[:len(sliding_avg)],
                sliding_avg,
                linestyle='--',
                linewidth=2,
                label=f'{titles[i]} - Sliding Avg'
            )

    # Set x-ticks and labels
    for ax in [ax1, ax2]:
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([str(tick) for tick in tick_sizes])
        ax.set_xlabel('Cluster Size (Number of Items)')
        ax.set_ylim(global_min, global_max)

    ax1.set_title('Cumulative Median of Cluster Standard Deviations')
    ax1.set_ylabel('True Positive')
    ax1.legend()

    ax2.set_title('Sliding Window Average (Window=5) of Cluster Standard Deviations')
    ax2.set_ylabel('True Positive')
    ax2.legend()

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')
    plt.close(fig)

def plot_cluster_std_dev_boxplot_static(df, drop_smallest_n=0, output_file='cluster_std_dev_boxplot.pdf', title='Cluster Standard Deviation'):
    """
    Plot a boxplot for standard deviations by cluster size for a single DataFrame,
    dropping the specified number of smallest cluster sizes, with no x-axis ticks,
    and superimpose both the cumulative moving average (red) and a sliding window average (window size 5, blue) of the median.

    Parameters:
    - df: pandas DataFrame
    - drop_smallest_n: Integer, number of smallest cluster sizes to drop (default: 0)
    - output_file: File path to save the output PDF
    - title: Title for the plot (default: 'Cluster Standard Deviation')
    """
    # Validate input
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    # Create a single subplot
    fig, ax = plt.subplots(figsize=(12, 4))

    # Convert DataFrame values to numeric, replacing 'None' with NaN
    df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')

    # Get cluster sizes from column names
    try:
        all_sizes = sorted([int(col) for col in df.columns])
    except ValueError:
        raise ValueError("Column names must be convertible to integers representing cluster sizes")

    if not all_sizes:
        raise ValueError("No valid cluster sizes found in the DataFrame")

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

    # Filter DataFrame to include only the remaining cluster sizes
    remaining_columns = [col for col in df.columns if int(col) in all_sizes]
    filtered_df = df[remaining_columns]

    # Prepare data for boxplot
    datasets = []
    sizes_with_data = []
    for size in all_sizes:
        col = next((c for c in df.columns if int(c) == size), None)
        if col is not None:
            data = filtered_df[col].dropna().tolist()
            datasets.append(data)
            if data:
                sizes_with_data.append(size)

    if not any(datasets):
        ax.set_title(f'{title}: No valid data')
        ax.set_ylabel('True Possitive')
        ax.set_xlabel('Cluster Size (Number of Items)')
        print(f"No valid data to plot")
        plt.tight_layout()
        fig.savefig(output_file, format='pdf')
        plt.close(fig)
        return

    print(f"Sizes with data: {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")

    # Boxplot
    box = ax.boxplot(datasets, positions=range(1, len(all_sizes) + 1), 
                     labels=[str(s) for s in all_sizes], patch_artist=True)

    # Calculate medians
    medians = [np.median(d) if d else np.nan for d in datasets]
    valid_medians = [m for m in medians if not np.isnan(m)]
    valid_positions = [i + 1 for i, d in enumerate(datasets) if d]

    # Plot averages
    if valid_medians:
        # Cumulative average (red)
        cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
        ax.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, color='red', marker='o', 
                label='Cumulative Avg of Median', linestyle='-', linewidth=2)

        # Sliding window average (blue)
        window_size = 5
        sliding_avg = []
        for j in range(len(valid_medians)):
            start = max(0, j - window_size + 1)
            window = valid_medians[start:j + 1]
            sliding_avg.append(np.mean(window))
        ax.plot(valid_positions[:len(sliding_avg)], sliding_avg, color='blue', marker='s', 
                label='Sliding Window Avg (size 5)', linestyle='--', linewidth=2)

        ax.legend()

    # Set y-axis limits with padding
    global_min = min(min(d) for d in datasets if d) if any(datasets) else 0
    global_max = max(max(d) for d in datasets if d) if any(datasets) else 1
    padding = (global_max - global_min) * 0.05
    ax.set_ylim(0, 1)

    # Set plot attributes
    ax.set_title(title)
    ax.set_ylabel('True Possitive')
    ax.set_xlabel('Cluster Size (Number of Items)')

    # Turn off x-axis ticks
    ax.set_xticks([])

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')
    plt.close(fig)
def plot_cluster_std_dev_boxplot_static_two(dfs, drop_smallest_n=0, output_file='cluster_std_dev_boxplot_two.pdf'):
    """
    Plot boxplots for standard deviations by cluster size for two DataFrames,
    dropping the specified number of smallest cluster sizes, using the same x-axis (cluster sizes)
    with ticks at intervals of 100 applied to both subplots, leaving blank spaces for missing sizes,
    with a shared y-axis scale, and superimpose both the cumulative moving average (red) and a
    sliding window average (window size 5, blue) of the median on the same subplot.

    Parameters:
    - dfs: List of 2 pandas DataFrames
    - drop_smallest_n: Integer, number of smallest cluster sizes to drop (default: 0)
    - output_file: File path to save the output PDF
    """
    # Validate input
    if not all(isinstance(df, pd.DataFrame) for df in dfs):
        raise ValueError("All items in input list must be pandas DataFrames")
    if len(dfs) != 2:
        raise ValueError("Expected exactly 2 DataFrames")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    # Titles for each subplot
    titles = ['Orginial BloomFilter Sdhash TH60', 'Retrained BloomFilter Sdhash TH60']
    
    # Create subplots with shared x and y axes
    fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.4)

    # Initialize variables to track global y-axis limits
    global_min = float('inf')
    global_max = float('-inf')

    # Collect all unique cluster sizes across both DataFrames
    all_sizes = set()
    for df in dfs:
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
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        remaining_columns = [col for col in df.columns if int(col) in all_sizes]
        filtered_df = df[remaining_columns]
        filtered_dfs.append(filtered_df)

    # Determine x-axis ticks at intervals of 100 based on remaining sizes
    max_size = max(all_sizes)
    min_size = min(all_sizes)
    tick_start = (min_size // 100) * 100
    tick_sizes = list(range(tick_start, max_size + 100, 100))
    tick_positions = []
    for tick in tick_sizes:
        closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
        tick_positions.append(closest_idx + 1)

    # First pass: Determine global y-axis limits
    for df in filtered_dfs:
        for size in all_sizes:
            if size in df.columns:
                data = df[size].dropna().tolist()
                if data:
                    global_min = min(global_min, min(data))
                    global_max = max(global_max, max(data))

    # Ensure valid y-axis limits
    if global_min == float('inf') or global_max == float('-inf'):
        global_min, global_max = 0, 1
    else:
        padding = (global_max - global_min) * 0.05
        global_min -= padding
        global_max += padding

    # Second pass: Plotting
    for i, (df, ax) in enumerate(zip(filtered_dfs, axs)):
        datasets = []
        sizes_with_data = []
        for size in all_sizes:
            if size in df.columns:
                data = df[size].dropna().tolist()
                datasets.append(data)
                if data:
                    sizes_with_data.append(size)
            else:
                datasets.append([])

        if not any(datasets):
            ax.set_title(f'{titles[i]}: No valid data')
            ax.set_ylabel('True Possitive')
            ax.set_xlabel('Cluster Size (Number of Items)')
            print(f"Subplot {titles[i]}: No valid data to plot")
            continue

        print(f"Subplot {titles[i]}: sizes_with_data = {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")

        # Boxplot
        box = ax.boxplot(datasets, positions=range(1, len(all_sizes) + 1), 
                         labels=[str(s) for s in all_sizes], patch_artist=True)
        
        # Calculate medians
        medians = [np.median(d) if d else np.nan for d in datasets]
        
        # Compute averages
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [i + 1 for i, d in enumerate(datasets) if d]
        if valid_medians:
            # Cumulative average (red)
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            ax.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, color='red', marker='o', 
                    label='Cumulative Avg of Median', linestyle='-', linewidth=2)

            # Sliding window average (blue)
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
        ax.set_ylabel('True Possitive')
        ax.set_xlabel('Cluster Size (Number of Items)')
        ax.set_ylim(global_min, global_max)

    # Set x-ticks on the last subplot
    if tick_positions:
        axs[-1].set_xticks(tick_positions)
        axs[-1].set_xticklabels([str(tick) for tick in tick_sizes])
        print(f"Setting x-ticks on last subplot: {tick_sizes} (positions: {tick_positions})")
    else:
        print("No valid tick positions found")

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')
    plt.close(fig)
def plot_cluster_std_dev_boxplot_static_all(dfs, drop_smallest_n=0, output_file='cluster_std_dev_boxplot_all.pdf'):
    """
    Plot boxplots for standard deviations by cluster size across multiple DataFrames,
    dropping the specified number of smallest cluster sizes, using the same x-axis (cluster sizes) with
    ticks at intervals of 100 applied to all subplots, leaving blank spaces for missing sizes,
    with a shared y-axis scale, and superimpose both the cumulative moving average (red) and a
    sliding window average (window size 5, blue) of the median on the same subplot.

    Parameters:
    - dfs: List of 5 pandas DataFrames
    - drop_smallest_n: Integer, number of smallest cluster sizes to drop (default: 0)
    - output_file: File path to save the output PDF
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
    titles =['Heurstic', 'Autoyara','AutoPyara','BestKyara','WorstPyara']
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
            if size in df.columns:
                data = df[size].dropna().tolist()
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
            if size in df.columns:
                data = df[size].dropna().tolist()
                datasets.append(data)
                if data:
                    sizes_with_data.append(size)
            else:
                datasets.append([])  # Empty dataset for missing cluster size

        if not any(datasets):
            ax.set_title(f'{titles[i]}: No valid data')
            ax.set_ylabel('True Possitive')
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
        ax.set_ylabel('True Possitive')
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
    
def extract_rule_tp_rates(file_path):
    """
    Extracts rule names and their TP rates from a YARA rule file.
    Returns a dictionary mapping rule names to TP rates (as floats).
    """
    rule_tp_map = {}
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # Split content into rules, capturing rule name and content
            rules = re.split(r'\n\s*rule\s+([^\s{]+)', content.strip())
            # Pair rule names with their content (name, content, name, content, ...)
            rules = [(rules[i], rules[i+1]) for i in range(1, len(rules), 2)]
            
            for rule_name, rule_content in rules:
                # Validate rule name
                if not rule_name or not re.match(r'^\w+$', rule_name):
                    print(f"Skipping invalid rule name: {rule_name}")
                    continue
                
                # Extract TP rate from comments
                # Match either "//Input TP Rate: X/Y" or standalone "//X/Y"
                tp_match = re.search(
                    r'//\s*(?:Input\s+TP\s+Rate\s*:\s*)?(\d+)\s*/\s*(\d+)', 
                    rule_content, 
                    re.MULTILINE | re.IGNORECASE
                )
                if tp_match:
                    numerator, denominator = map(int, tp_match.groups())
                    tp_rate = Fraction(numerator, denominator) if denominator != 0 else 0
                    rule_tp_map[rule_name] = float(tp_rate)
                else:
                    rule_tp_map[rule_name] = None
                    print(f"Warning: No TP rate found for rule {rule_name}")
                    print(f"Rule content preview:\n{rule_content[:200]}...\n")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return rule_tp_map
def rules_to_dataframe(rule_tp_map, max_runs=15, max_cluster_num=8874):
    """
    Converts a rule-to-TP-rate map into a DataFrame with clusters as rows and runs as columns.
    Includes all clusters from Cluster0 to Cluster{max_cluster_num}, filling missing rows with 0.
    Sorts rows by the numeric part of cluster names (e.g., Cluster0, Cluster1, Cluster2).
    
    Args:
        rule_tp_map (dict): Dictionary mapping rule names (e.g., 'Cluster0_1') to TP rates.
        max_runs (int): Maximum number of runs (default: 30).
        max_cluster_num (int): Maximum cluster number (default: 9000).
    
    Returns:
        pd.DataFrame: DataFrame with clusters as rows, runs as columns, and TP rates as values.
    """
    # Extract clusters and runs
    print("LOG:max_cluster_num ",max_cluster_num)
    data = []
    for rule, tp_rate in rule_tp_map.items():
        try:
            cluster, run = rule.rsplit('_', 1)
            run = int(run)
            data.append({'cluster': cluster, 'run': run, 'tp_rate': tp_rate if tp_rate is not None else 0})
        except ValueError:
            print(f"Skipping invalid rule format: {rule}")
            continue

    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Pivot to get clusters as rows and runs as columns
    pivot_df = df.pivot(index='cluster', columns='run', values='tp_rate')
    
    # Ensure all columns from 1 to max_runs exist
    columns = list(range(1, max_runs + 1))
    #pivot_df = pivot_df.reindex(columns=columns, fill_value=0)
    # Reindex without fill_value first
    pivot_df = pivot_df.reindex(columns=columns)
    
    # Then fill missing values with the median
    pivot_df = pivot_df.fillna(pivot_df.median())

    # Fill NaN values (missing TP rates) with 0
    pivot_df = pivot_df.fillna(0)
    
    # Create index with all clusters from Cluster0 to Cluster{max_cluster_num}
    all_clusters = [f'Cluster{i}' for i in range(max_cluster_num + 1)]
    pivot_df = pivot_df.reindex(index=all_clusters, fill_value=0)
    
    # Sort index by numeric part of cluster name
    def extract_cluster_number(cluster_name):
        try:
            number = int(re.search(r'\d+', cluster_name).group())
            return number
        except (AttributeError, ValueError):
            print(f"Warning: Could not extract number from cluster name: {cluster_name}")
            return float('inf')
    
    pivot_df = pivot_df.sort_index(key=lambda x: [extract_cluster_number(name) for name in x])
    
    return pivot_df
def ensure_columns(dataframes):

    # Step 1: Handle single DataFrame by wrapping in a list
    if isinstance(dataframes, pd.DataFrame):
        dataframes = [dataframes]
    elif not isinstance(dataframes, list):
        raise ValueError("Input must be a pandas DataFrame or a list of DataFrames")
    
    # Step 2: First, make sure all column names are integers
    for i, df in enumerate(dataframes):
        try:
            df.columns = [int(col) for col in df.columns]
            dataframes[i] = df
        except (ValueError, TypeError):
            raise ValueError("All column names must be convertible to integers")
    
    # Step 3: Find the maximum cluster size
    max_size = 0
    for df in dataframes:
        if df.columns.size > 0:
            max_size = max(max_size, max(df.columns))
    
    # Step 4: Make full cluster list
    cluster_list = list(range(1, max_size + 1))  # IMPORTANT: 1 to max_size
    
    # Step 5: Make sure all DataFrames have all clusters
    for i, df in enumerate(dataframes):
        # Find missing clusters
        existing_clusters = set(df.columns)
        required_clusters = set(cluster_list)
        missing_clusters = required_clusters - existing_clusters
    
        # Add missing clusters
        for cluster_id in missing_clusters:
            df[cluster_id] = None
    
        # Reorder columns numerically
        dataframes[i] = df.reindex(columns=cluster_list)
    
    # Step 6: Return single DataFrame if only one input
    return dataframes[0] if len(dataframes) == 1 else dataframes
def Extractor(csv_file,file_path,mr,short=False):
    df1 = pd.read_csv(csv_file)
    labels = df1['Cluster_Label'].dropna().astype(int).tolist()  # Ensure integers
    cluster_sizes = {label: labels.count(label) for label in set(labels) if label >= 0}
    
    # Filter for clusters with size >= 2 (keep the key-value pairs)
    data = {label: size for label, size in cluster_sizes.items() if size >= 2}
    unique_vals =sorted(set(data.values()))
    df_new  = pd.DataFrame(columns=unique_vals)
    
    
    result = extract_rule_tp_rates(file_path)
    # for rule_name, tp_rate in result.items():
    #     print(f"Rule: {rule_name}, TP Rate: {tp_rate}")
    df_cluster = rules_to_dataframe(result, max_runs=mr,max_cluster_num=len(data))
    df_cluster=df_cluster.transpose()
    df_cluster=df_cluster.mean(numeric_only=True)
    if short:
        print("Short mode enabled")
        return df_cluster
    # Step 3: Populate the new DataFrame
    for cluster_name, score in df_cluster.items():
        # Extract the key (e.g., Cluster0 → 0)
        key = int(cluster_name.replace('Cluster', ''))
        if key in data:
            col = data[key]
            # Find first available empty row index (or append a new one)
            row_idx = df_new.index[df_new[col].isna()].min() if col in df_new.columns and not df_new.empty else None
            if pd.isna(row_idx):
                row_idx = len(df_new)
                df_new.loc[row_idx] = [None] * len(df_new.columns)
            df_new.at[row_idx, col] = score
    return df_new
from matplotlib.backends.backend_pdf import PdfPages
def plot_cluster_std_dev_boxplot_static(df, output_file='cluster_std_dev_boxplot.pdf'):
    """
    Generate a static Matplotlib boxplot of standard deviations for each cluster size.
    Saves the output as a machine-readable PDF.

    Parameters:
    - df: pandas DataFrame with cluster sizes as column headers and standard deviations as values
    - output_file: file path to save the PDF
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    # Sort and clean data
    sizes = sorted(df.columns.astype(int).tolist())
    datasets = [df[size].dropna().tolist() for size in sizes]

    # Filter out sizes with no data
    sizes_with_data = [s for s, d in zip(sizes, datasets) if d]
    datasets_with_data = [d for d in datasets if d]

    if not sizes_with_data:
        print("No cluster sizes with valid data found.")
        return

    # Create a single boxplot
    fig, ax = plt.subplots(figsize=(max(10, len(sizes_with_data) * 0.5), 6))
    ax.boxplot(datasets_with_data, labels=[str(s) for s in sizes_with_data], patch_artist=True)
    ax.set_title('Boxplot of Standard Deviations by Cluster Size')
    ax.set_xlabel('Cluster Size (Number of Items)')
    ax.set_ylabel('Standard Deviation of Cluster Averages')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save to PDF
    fig.savefig(output_file, format='pdf')
    plt.close(fig)

    print(f"Static PDF plot saved to {output_file}")

    