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
def Extractor(csv_file,file_path,mr):
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

    