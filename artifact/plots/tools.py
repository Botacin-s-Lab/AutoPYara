
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Global font settings
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.weight'] = 600
plt.rcParams['font.size'] = 20

# Font dictionaries
TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 20}
TICK_FONT = {'fontsize': 20, 'fontweight': 'bold'}

def plot_cluster_std_dev_boxplot_static_all_merge(
    dfs,
    drop_smallest_n=0,
    output_file1='cumulative_median_plot.pdf',
    output_file2='sliding_avg_plot.pdf'
):
    if not all(isinstance(df, pd.DataFrame) for df in dfs):
        raise ValueError("All items in input list must be pandas DataFrames")
    if len(dfs) != 5:
        raise ValueError("Expected exactly 5 DataFrames")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    titles = ['Threshold 50', 'Threshold 60', 'Threshold 70', 'Threshold 80', 'Threshold 90']

    # Collect all unique cluster sizes
    all_sizes = set()
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        try:
            sizes = df.columns.astype(int).tolist()
            all_sizes.update(sizes)
        except ValueError:
            continue

    all_sizes = sorted(all_sizes)
    if drop_smallest_n > 0 and len(all_sizes) > drop_smallest_n:
        all_sizes = all_sizes[drop_smallest_n:]
    if not all_sizes:
        raise ValueError("No valid cluster sizes found")

    # Filter DataFrames to only those cluster sizes
    filtered_dfs = []
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        valid_cols = [col for col in df.columns if int(col) in all_sizes]
        filtered_dfs.append(df[valid_cols])

    # Define custom ticks
    tick_sizes = [0, 25, 50, 75, 100, 500]
    tick_positions = []
    for tick in tick_sizes:
        if all_sizes:
            closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
            tick_positions.append(closest_idx + 1)

    # ---------- Plot 1: Cumulative Median ----------
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    for i, df in enumerate(filtered_dfs):
        datasets = [
            (df[size].dropna().astype(float) * 100).tolist() if size in df.columns else []
            for size in all_sizes
        ]
        medians = [np.median(d) if d else np.nan for d in datasets]
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

        if valid_medians:
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            line, = ax1.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, linewidth=2, label=titles[i])
            avg_value = np.mean(cumulative_avg)
            ax1.axhline(y=avg_value, color=line.get_color(), linestyle=':', linewidth=1.5)

    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels([str(t) for t in tick_sizes], **TICK_FONT)
    ax1.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)
    ax1.set_ylabel('True Positive (%)', **AXIS_FONT)
    ax1.set_ylim(0, 100)
    ax1.legend(prop=AXIS_FONT)
    ax1.grid(True, linestyle='--', alpha=0.5)

    fig1.tight_layout()
    fig1.savefig(output_file1, format='pdf', bbox_inches='tight')
    plt.close(fig1)

    # ---------- Plot 2: Sliding Window Average ----------
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    for i, df in enumerate(filtered_dfs):
        datasets = [
            (df[size].dropna().astype(float) * 100).tolist() if size in df.columns else []
            for size in all_sizes
        ]
        medians = [np.median(d) if d else np.nan for d in datasets]
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

        if valid_medians:
            window_size = 5
            sliding_avg = []
            for j in range(len(valid_medians)):
                start = max(0, j - window_size + 1)
                window = valid_medians[start:j + 1]
                sliding_avg.append(np.mean(window))
            line, = ax2.plot(valid_positions[:len(sliding_avg)], sliding_avg, linestyle='--', linewidth=2, label=titles[i])
            avg_value = np.mean(sliding_avg)
            ax2.axhline(y=avg_value, color=line.get_color(), linestyle=':', linewidth=1.5)

    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels([str(t) for t in tick_sizes], **TICK_FONT)
    ax2.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)
    ax2.set_ylabel('True Positive (%)', **AXIS_FONT)
    ax2.set_ylim(0, 100)
    ax2.legend(prop=AXIS_FONT)
    ax2.grid(True, linestyle='--', alpha=0.5)

    fig2.tight_layout()
    fig2.savefig(output_file2, format='pdf', bbox_inches='tight')
    plt.close(fig2)
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Global font settings
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.weight'] = 600
plt.rcParams['font.size'] = 22

# Font dictionaries
TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 900, 'size': 14.0}
TICK_FONT = {'fontsize': 22, 'fontweight': 'bold'}

def plot_cluster_std_dev_boxplot_static_all_merge_zoom(
    dfs,
    drop_smallest_n=0,
    output_file1='cumulative_median_plot.pdf',
    output_file2='sliding_avg_plot.pdf'
):
    if not all(isinstance(df, pd.DataFrame) for df in dfs):
        raise ValueError("All items in input list must be pandas DataFrames")
    if len(dfs) != 5:
        raise ValueError("Expected exactly 5 DataFrames")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    titles = ['Threshold 50', 'Threshold 60', 'Threshold 70', 'Threshold 80', 'Threshold 90']

    # Collect all unique cluster sizes
    all_sizes = set()
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        try:
            sizes = df.columns.astype(int).tolist()
            all_sizes.update(sizes)
        except ValueError:
            continue

    all_sizes = sorted(all_sizes)
    if drop_smallest_n > 0 and len(all_sizes) > drop_smallest_n:
        all_sizes = all_sizes[drop_smallest_n:]
    if not all_sizes:
        raise ValueError("No valid cluster sizes found")

    # Filter DataFrames to only those cluster sizes
    filtered_dfs = []
    for df in dfs:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        valid_cols = [col for col in df.columns if int(col) in all_sizes]
        filtered_dfs.append(df[valid_cols])

    # Define custom ticks
    tick_sizes = [0, 25, 50, 75, 100, 500]
    tick_positions = []
    for tick in tick_sizes:
        if all_sizes:
            closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
            tick_positions.append(closest_idx + 1)

    # ---------- Plot 1: Cumulative Median ----------
    fig1, ax1 = plt.subplots(figsize=(15, 6))
    for i, df in enumerate(filtered_dfs):
        datasets = [
            (df[size].dropna().astype(float) * 100).tolist() if size in df.columns else []
            for size in all_sizes
        ]
        medians = [np.median(d) if d else np.nan for d in datasets]
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

        if valid_medians:
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            line, = ax1.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, linewidth=2, label=titles[i])
            avg_value = np.mean(cumulative_avg)
            ax1.axhline(y=avg_value, color=line.get_color(), linestyle=':', linewidth=1.5)

    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels([str(t) for t in tick_sizes], **TICK_FONT)
    ax1.set_xlabel('Cluster Size (Number of Items)', **TICK_FONT)
    ax1.set_ylabel('True Positive (%)', **TICK_FONT)
    ax1.set_ylim(60, 100)
    ax1.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.02),
        ncol=5,
        prop=AXIS_FONT,
        frameon=False
    )
    ax1.grid(True, linestyle='--', alpha=0.5)

    fig1.subplots_adjust(top=0.8)
    fig1.savefig(output_file1, format='pdf', bbox_inches='tight')
    plt.close(fig1)

    # ---------- Plot 2: Sliding Window Average ----------
    fig2, ax2 = plt.subplots(figsize=(15, 6))
    for i, df in enumerate(filtered_dfs):
        datasets = [
            (df[size].dropna().astype(float) * 100).tolist() if size in df.columns else []
            for size in all_sizes
        ]
        medians = [np.median(d) if d else np.nan for d in datasets]
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

        if valid_medians:
            window_size = 5
            sliding_avg = []
            for j in range(len(valid_medians)):
                start = max(0, j - window_size + 1)
                window = valid_medians[start:j + 1]
                sliding_avg.append(np.mean(window))
            line, = ax2.plot(valid_positions[:len(sliding_avg)], sliding_avg, linestyle='--', linewidth=2, label=titles[i])
            avg_value = np.mean(sliding_avg)
            ax2.axhline(y=avg_value, color=line.get_color(), linestyle=':', linewidth=1.5)

    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels([str(t) for t in tick_sizes], **TICK_FONT)
    ax2.set_xlabel('Cluster Size (Number of Items)', **TICK_FONT)
    ax2.set_ylabel('True Positive (%)', **TICK_FONT)
    ax2.set_ylim(0, 100)
    ax2.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.02),
        ncol=5,
        prop=AXIS_FONT,
        frameon=False
    )
    ax2.grid(True, linestyle='--', alpha=0.5)

    fig2.subplots_adjust(top=0.8)
    fig2.savefig(output_file2, format='pdf', bbox_inches='tight')
    plt.close(fig2)

def plot_cluster_std_dev_boxplot_single(
    df,
    drop_smallest_n=0,
    output_file1='single_cumulative_median_plot.pdf',
    output_file2='single_sliding_avg_plot.pdf',
    label='VirusTotal Clusters'
):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    # Convert columns to numeric (int) if possible
    df = df.replace('None', np.nan)
    df.columns = pd.to_numeric(df.columns, errors='coerce')
    df = df.apply(pd.to_numeric, errors='coerce')

    # Remove NaN columns
    all_sizes = sorted([col for col in df.columns if not pd.isna(col)])
    if drop_smallest_n > 0 and len(all_sizes) > drop_smallest_n:
        all_sizes = all_sizes[drop_smallest_n:]

    df = df[all_sizes]

    # Custom ticks
    tick_sizes = [0, 25, 50, 75, 100, 500]
    tick_positions = []
    for tick in tick_sizes:
        if all_sizes:
            closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
            tick_positions.append(closest_idx + 1)

    # Scale all data to percentage by multiplying by 100
    df = df * 100

    # Compute median values
    datasets = [df[size].dropna().tolist() for size in all_sizes]
    medians = [np.median(d) if d else np.nan for d in datasets]
    valid_medians = [m for m in medians if not np.isnan(m)]
    valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

    # --- Plot 1: Cumulative Median ---
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    if valid_medians:
        cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
        line, = ax1.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, linewidth=2, label=label)
        ax1.axhline(y=np.mean(cumulative_avg), color=line.get_color(), linestyle=':', linewidth=1.5)

    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels([str(t) for t in tick_sizes], **TICK_FONT)
    ax1.set_xlabel('Cluster Size (Number of Items)', **TICK_FONT)
    ax1.set_ylabel('True Positive (%)', **TICK_FONT)
    ax1.set_ylim(0, 100)
    ax1.set_yticks(np.arange(0, 101, 10))  # y ticks from 0 to 100 by 10
    ax1.legend(prop=AXIS_FONT)
    ax1.grid(True, linestyle='--', alpha=0.5)
    fig1.tight_layout()
    fig1.savefig(output_file1, format='pdf', bbox_inches='tight')
    plt.close(fig1)

    # --- Plot 2: Sliding Window Average ---
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    if valid_medians:
        window_size = 5
        sliding_avg = []
        for j in range(len(valid_medians)):
            start = max(0, j - window_size + 1)
            window = valid_medians[start:j + 1]
            sliding_avg.append(np.mean(window))
        line, = ax2.plot(valid_positions[:len(sliding_avg)], sliding_avg, linestyle='--', linewidth=2, label=label)
        ax2.axhline(y=np.mean(sliding_avg), color=line.get_color(), linestyle=':', linewidth=1.5)

    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels([str(t) for t in tick_sizes], **TICK_FONT)
    ax2.set_xlabel('Cluster Size (Number of Items)', **TICK_FONT)
    ax2.set_ylabel('True Positive (%)', **TICK_FONT)
    ax2.set_ylim(0, 100)
    ax2.set_yticks(np.arange(0, 101, 10))  # y ticks from 0 to 100 by 10
    ax2.legend(prop=AXIS_FONT)
    ax2.grid(True, linestyle='--', alpha=0.5)
    fig2.tight_layout()
    fig2.savefig(output_file2, format='pdf', bbox_inches='tight')
    plt.close(fig2)





import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.patches import Patch

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.weight'] = 600
plt.rcParams['font.size'] = 16

AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 18}
TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
TICK_FONT_SIZE = 16
def plot_side_by_side_bar_with_textures(
    list1, list2, list3, list4, list5, list6,
    labels=("SSdeep", "J-SDhash", "VirusTotal"),
    save_path=None
):
    def combine_and_flatten(df_list):
        combined = pd.concat(df_list, axis=1)
        values = combined.values.flatten()
        return values[~pd.isna(values)]  # Remove NaNs

    # Flatten all lists
    data_primary = [combine_and_flatten(lst) for lst in [list1, list2, list3]]
    data_secondary = [combine_and_flatten(lst) for lst in [list4, list5, list6]]

    # Compute stats and convert to percentage
    means_primary = [np.mean(d)*100 for d in data_primary]
    stds_primary = [np.std(d)*100 for d in data_primary]
    means_secondary = [np.mean(d)*100 for d in data_secondary]
    stds_secondary = [np.std(d)*100 for d in data_secondary]

    x = np.arange(len(labels))
    width = 0.35

    # Colors and hatches
    base_colors = ['#4C72B0', '#55A868', '#C44E52']        # Light - retrained
    retrain_colors = ['#1C3D63', '#2E5C3C', '#802D33']     # Dark - original
    hatches = ['//', 'xx', 'oo']

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # Retrained bars (lighter, left)
    bars_primary = ax.bar(
        x - width/2, means_primary, width=width, yerr=stds_primary, capsize=10,
        color=base_colors, edgecolor='black', linewidth=1.5
    )
    for bar, hatch in zip(bars_primary, hatches):
        bar.set_hatch(hatch)

    # Original bars (darker, right)
    bars_secondary = ax.bar(
        x + width/2, means_secondary, width=width, yerr=stds_secondary, capsize=10,
        color=retrain_colors, edgecolor='black', linewidth=1.5
    )
    for bar, hatch in zip(bars_secondary, hatches):
        bar.set_hatch(hatch)

    # Add text annotations
    for i, (mu1, std1, mu2, std2) in enumerate(zip(means_primary, stds_primary, means_secondary, stds_secondary)):
        ax.text(x[i] - width/2, mu1 + 2, f"μ={mu1:.1f}\nσ={std1:.1f}", fontsize=10, ha='right', fontweight='bold')
        ax.text(x[i] + width/2, mu2 + 2, f"μ={mu2:.1f}\nσ={std2:.1f}", fontsize=10, ha='left', fontweight='bold')

    # Axis formatting
    ax.set_ylim(0, 100)
    ax.set_ylabel("True Positive Rate (%)", **AXIS_FONT)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=TICK_FONT_SIZE, fontweight='bold')
    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_yticklabels([f"{y}" for y in np.arange(0, 101, 10)], fontsize=TICK_FONT_SIZE, fontweight='bold')
    ax.tick_params(axis='both', which='major', labelsize=TICK_FONT_SIZE)
    ax.grid(True, axis='y', linestyle='--', alpha=0.5)

    # Custom legend patches
    legend_elements = [
        Patch(facecolor=base_colors[0], edgecolor='black', hatch='//', label=''),
        Patch(facecolor=base_colors[1], edgecolor='black', hatch='xx', label='Retrained Bloom Filters'),
        Patch(facecolor=base_colors[2], edgecolor='black', hatch='oo', label=''),
        Patch(facecolor=retrain_colors[0], edgecolor='black', hatch='//', label=''),
        Patch(facecolor=retrain_colors[1], edgecolor='black', hatch='xx', label='Ember Bloom Filters'),
        Patch(facecolor=retrain_colors[2], edgecolor='black', hatch='oo', label=''),
    ]

    ax.legend(
        handles=legend_elements,
        loc='upper right',
        fontsize=14,
        frameon=False,
        ncol=2,
        borderpad=1,
        labelspacing=0.5
    )

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.show()


def plot_cluster_std_dev_boxplot_static_single(df, drop_smallest_n=0, output_file='cluster_std_dev_boxplot.pdf', title='Cluster Standard Deviation'):
    """
    Plot a boxplot for standard deviations by cluster size for a single DataFrame,
    dropping the specified number of smallest cluster sizes, with x-axis ticks forced to include 500,
    and superimpose both the cumulative moving average (red) and a sliding window average (blue) of the median.
    """
    # Global font settings
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.weight'] = 600
    plt.rcParams['font.size'] = 20

    # Font dictionaries
    TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
    AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 20}
    TICK_FONT = {'labelsize': 20}
    TICK_LABEL_FONT = {'size': 20, 'weight': 'bold'}

    # Validate input
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    # Create a single subplot
    fig, ax = plt.subplots(figsize=(14, 6))

    # Convert DataFrame values to numeric, replacing 'None' with NaN
    df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')

    # Scale the data to [0, 100]
    df = df * 100

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
        ax.set_title(f'{title}: No valid data', **TITLE_FONT)
        ax.set_ylabel('True Positive', **AXIS_FONT)
        ax.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)
        ax.tick_params(axis='x', **TICK_FONT)
        ax.tick_params(axis='y', **TICK_FONT)
        ax.set_yticklabels(ax.get_yticklabels(), **TICK_LABEL_FONT)
        print(f"No valid data to plot")
        plt.tight_layout()
        fig.savefig(output_file, format='pdf')
        plt.close(fig)
        return

    print(f"Sizes with data: {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")
    print(f"All sizes: {all_sizes[:10]}... (length: {len(all_sizes)})")

    # Boxplot with filled boxes
    box_positions = range(1, len(all_sizes) + 1)  # 1-indexed positions for boxplots
    box = ax.boxplot(datasets, positions=box_positions, 
                     labels=[str(s) for s in all_sizes], patch_artist=True)
    
    # Apply filled box style with specified color and hatch
    for patch in box['boxes']:
        patch.set(facecolor='#2E5C3C', edgecolor='black', hatch='xx')

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

    # Set y-axis limits
    ax.set_ylim(0, 100)

    # Set plot attributes with font settings
    ax.set_title(title, **TITLE_FONT)
    ax.set_ylabel('True Positive (%)', **AXIS_FONT)
    ax.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)

    # Force x-axis ticks to include 500, ensuring correct order
    tick_sizes = [0, 25, 50, 75, 100, 500]
    size_to_pos = {size: idx + 1 for idx, size in enumerate(all_sizes)}  # 1-indexed positions
    max_size = max(all_sizes) if all_sizes else 100
    max_position = len(all_sizes)  # Last boxplot position

    tick_positions = []
    tick_labels = []

    for tick in tick_sizes:
        if tick in size_to_pos:
            tick_positions.append(size_to_pos[tick])
            tick_labels.append(str(tick))
        elif tick <= 500:
            if tick == 500:
                scaled_pos = max_position + (500 - max_size) / max_size * 10
                tick_positions.append(scaled_pos)
                tick_labels.append('500')
            elif tick == 0:
                tick_positions.append(0)
                tick_labels.append('0')
            else:
                continue

    # Ensure ticks are sorted by value for correct order
    sorted_pairs = sorted(zip(tick_labels, tick_positions), key=lambda x: int(x[0]))
    tick_labels, tick_positions = zip(*sorted_pairs) if sorted_pairs else ([], [])

    print(f"Tick sizes: {list(tick_labels)}")
    print(f"Tick positions: {list(tick_positions)}")

    # Set ticks and adjust x-axis limits with font settings
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, **TICK_LABEL_FONT)
    ax.tick_params(axis='y', **TICK_FONT)
    ax.set_yticklabels(ax.get_yticklabels(), **TICK_LABEL_FONT)
    ax.set_xlim(-0.5, max(tick_positions) + 0.5)

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')



import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline

def plot_cluster_std_dev_static_single_accumilatedAVG(df, drop_smallest_n=0, output_file='cluster_std_dev_plot.pdf', title='Cluster Standard Deviation'):
    """
    Plot a smooth curve representing the cumulative average of the median with a shaded accumulated standard deviation band
    centered on and surrounding the cumulative average, where the band is based on the cumulative standard deviation of the
    cumulative average, dropping the specified number of smallest cluster sizes, with x-axis ticks forced to include 500, and
    the shaded band extending to both edges, curving and trending with the cumulative average in a decreasing trend.
    """
    # Global font settings
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.weight'] = 600
    plt.rcParams['font.size'] = 14

    # Font dictionaries
    TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 16}
    AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 14}
    TICK_FONT = {'labelsize': 14}
    TICK_LABEL_FONT = {'size': 14, 'weight': 'bold'}

    # Marker and line settings
    plt.rcParams['lines.markersize'] = 3

    # Validate input
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")

    # Create a single subplot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Convert DataFrame values to numeric, replacing 'None' with NaN
    df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')

    # Scale the data to [0, 100]
    df = df * 100

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

    # Prepare data
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
        ax.set_title(f'{title}: No valid data', **TITLE_FONT)
        ax.set_ylabel('True Positive (%)', **AXIS_FONT)
        ax.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)
        ax.tick_params(axis='x', **TICK_FONT)
        ax.tick_params(axis='y', **TICK_FONT)
        ax.set_yticklabels(ax.get_yticklabels(), **TICK_LABEL_FONT)
        print(f"No valid data to plot")
        plt.tight_layout()
        fig.savefig(output_file, format='pdf')
        plt.close(fig)
        return

    print(f"Sizes with data: {sizes_with_data[:10]}... (length: {len(sizes_with_data)})")
    print(f"All sizes: {all_sizes[:10]}... (length: {len(all_sizes)})")

    # Calculate medians
    medians = [np.median(d) if d else np.nan for d in datasets]
    valid_medians = [m for m in medians if not np.isnan(m)]
    valid_positions = [i + 1 for i, d in enumerate(datasets) if d]

    # Calculate cumulative average and cumulative standard deviations
    if valid_medians:
        cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
        cumulative_std_devs = [np.std(cumulative_avg[:i+1]) if i > 0 else 0 for i in range(len(cumulative_avg))]

        # Plot cumulative average (red, smooth line)
        ax.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, color='red', marker='o', 
                label='Cumulative Avg of Median', linestyle='-', linewidth=2)

        # Smooth cumulative average and cumulative standard deviation curves with spline interpolation
        smoothed_cumulative_std_devs = [s * np.exp(-0.005 * i) for i, s in enumerate(cumulative_std_devs)]

        # Extend the positions for smoother curves
        extended_positions = np.linspace(0, max(valid_positions) + (500 - max(all_sizes)) / max(all_sizes) * 10, 200)

        # Spline interpolation for cumulative average
        spline_cumulative_avg = make_interp_spline(valid_positions[:len(cumulative_avg)], cumulative_avg, k=3)
        extended_cumulative_avg = spline_cumulative_avg(extended_positions)

        # Spline interpolation for cumulative standard deviation
        spline_std = make_interp_spline(valid_positions[:len(smoothed_cumulative_std_devs)], smoothed_cumulative_std_devs, k=3)
        extended_cumulative_std_devs = spline_std(extended_positions)

        # Ensure standard deviation doesn't go negative and scale for visibility
        extended_cumulative_std_devs = np.maximum(extended_cumulative_std_devs * 1.5, 0)

        # Add accumulated standard deviation band centered on cumulative average
        lower_bound = [extended_cumulative_avg[i] - extended_cumulative_std_devs[i] for i in range(len(extended_cumulative_avg))]
        upper_bound = [extended_cumulative_avg[i] + extended_cumulative_std_devs[i] for i in range(len(extended_cumulative_avg))]
        ax.fill_between(extended_positions, lower_bound, upper_bound, 
                        color='blue', alpha=0.2, label='Accumulated Std-Dev Band')

        ax.legend(loc="lower center", ncol=3)

    # Set y-axis limits
    ax.set_ylim(0, 100)

    # Set plot attributes with font settings
    ax.set_title(title, **TITLE_FONT)
    ax.set_ylabel('True Positive (%)', **AXIS_FONT)
    ax.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)

    # Force x-axis ticks to include 500
    tick_sizes = [0, 25, 50, 75, 100, 500]
    size_to_pos = {size: idx + 1 for idx, size in enumerate(all_sizes)}
    max_size = max(all_sizes) if all_sizes else 100
    max_position = len(all_sizes)

    tick_positions = []
    tick_labels = []

    for tick in tick_sizes:
        if tick in size_to_pos:
            tick_positions.append(size_to_pos[tick])
            tick_labels.append(str(tick))
        elif tick <= 500:
            if tick == 500:
                scaled_pos = max_position + (500 - max_size) / max_size * 10
                tick_positions.append(scaled_pos)
                tick_labels.append('500')
            elif tick == 0:
                tick_positions.append(0)
                tick_labels.append('0')
            else:
                continue

    # Ensure ticks are sorted by value
    sorted_pairs = sorted(zip(tick_labels, tick_positions), key=lambda x: int(x[0]))
    tick_labels, tick_positions = zip(*sorted_pairs) if sorted_pairs else ([], [])

    print(f"Tick sizes: {list(tick_labels)}")
    print(f"Tick positions: {list(tick_positions)}")

    # Set ticks and adjust x-axis limits
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, **TICK_LABEL_FONT)
    ax.tick_params(axis='y', **TICK_FONT)
    ax.set_yticklabels(ax.get_yticklabels(), **TICK_LABEL_FONT)
    ax.set_xlim(-0.5, max(tick_positions) + 0.5)

    # Add grid
    ax.grid(axis='both')

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')
    plt.show()    


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline

def plot_cluster_std_dev_static_dual_MASTER(df1, df2, drop_smallest_n=0, window_size=5, output_file='cluster_std_dev_plot.pdf', title='Cluster Standard Deviation'):
    """
    Plot smooth curves representing the cumulative average of the median for two DataFrames on the same figure, each with a
    shaded windowed standard deviation band centered on and surrounding its cumulative average. Each band is based on the
    standard deviation of the cumulative average over a sliding window (default size 5), dropping the specified number of
    smallest cluster sizes, with x-axis ticks forced to [0, 25, 50, 75, 100, 500, 1000]. All DataFrame values are scaled by 100 to represent True
    Positive (%) on the y-axis. Curves and bands extend to the last valid cluster size without clipping. The shaded
    band's color is a lighter shade of the corresponding line's color using alpha transparency.
    """
    # Global font settings
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.weight'] = 600
    plt.rcParams['font.size'] = 22

    # Font dictionaries
    TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
    AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
    TICK_FONT = {'labelsize': 22}
    TICK_LABEL_FONT = {'size': 22, 'weight': 'bold'}

    # Marker and line settings
    plt.rcParams['lines.markersize'] = 3

    # Validate inputs
    if not isinstance(df1, pd.DataFrame) or not isinstance(df2, pd.DataFrame):
        raise ValueError("Both inputs must be pandas DataFrames")
    if not isinstance(drop_smallest_n, int) or drop_smallest_n < 0:
        raise ValueError("drop_smallest_n must be a non-negative integer")
    if not isinstance(window_size, int) or window_size < 1:
        raise ValueError("window_size must be a positive integer")

    # Create a single subplot
    try:
        fig, ax = plt.subplots(figsize=(18, 8))
    except Exception as e:
        raise RuntimeError(f"Failed to create subplot: {e}")

    # Process DataFrames
    dfs = [df1, df2]
    datasets_list = []
    sizes_with_data_list = []
    valid_medians_list = []
    cumulative_avg_list = []
    windowed_std_devs_list = []

    # Get all cluster sizes from both DataFrames
    all_sizes = set()
    for idx, df in enumerate(dfs):
        try:
            df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
            # Scale all values by 100 to represent True Positive (%)
            df = df * 100
            sizes = sorted([int(col) for col in df.columns if col != 'None' and pd.notna(col)])
            all_sizes.update(sizes)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error processing DataFrame {idx + 1}: Column names must be convertible to integers representing cluster sizes. Error: {e}")
    all_sizes = sorted(list(all_sizes))

    if not all_sizes:
        raise ValueError("No valid cluster sizes found in either DataFrame")

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

    # Process each DataFrame
    for idx, df in enumerate(dfs):
        # Filter DataFrame to include only the remaining cluster sizes
        remaining_columns = [col for col in df.columns if col != 'None' and pd.notna(col) and int(col) in all_sizes]
        filtered_df = df[remaining_columns]

        # Prepare data
        datasets = []
        sizes_with_data = []
        for size in all_sizes:
            col = next((c for c in df.columns if c != 'None' and pd.notna(c) and int(c) == size), None)
            if col is not None:
                data = filtered_df[col].dropna().tolist()
                datasets.append(data)
                if data:
                    sizes_with_data.append(size)
            else:
                datasets.append([])  # Empty dataset for missing size

        datasets_list.append(datasets)
        sizes_with_data_list.append(sizes_with_data)

        # Calculate medians
        try:
            medians = [np.median(d) if d else np.nan for d in datasets]
            valid_medians = [m for m in medians if not np.isnan(m)]
        except Exception as e:
            raise ValueError(f"Error calculating medians for DataFrame {idx + 1}: {e}")
        valid_medians_list.append(valid_medians)

        # Calculate cumulative average and windowed standard deviations
        if valid_medians:
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            windowed_std_devs = [np.std(cumulative_avg[max(0, i - window_size + 1):i + 1]) if i > 0 else 0 for i in range(len(cumulative_avg))]
        else:
            cumulative_avg = []
            windowed_std_devs = []

        cumulative_avg_list.append(cumulative_avg)
        windowed_std_devs_list.append(windowed_std_devs)

    # Check if there's any valid data
    if not any(sizes_with_data_list[0]) and not any(sizes_with_data_list[1]):
        ax.set_title(f'{title}: No valid data', **TITLE_FONT)
        ax.set_ylabel('True Positive (%)', **AXIS_FONT)
        ax.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)
        ax.tick_params(axis='x', **TICK_FONT)
        ax.tick_params(axis='y', **TICK_FONT)
        ax.set_yticklabels(ax.get_yticklabels(), **TICK_LABEL_FONT)
        print("No valid data to plot")
        try:
            plt.tight_layout()
            fig.savefig(output_file, format='pdf')
            plt.close(fig)
        except Exception as e:
            raise RuntimeError(f"Failed to save plot: {e}")
        return

    # Map cluster sizes to positions (1-based indexing for plotting)
    valid_positions = list(range(1, len(all_sizes) + 1))

    # Plot curves for both DataFrames
    colors = [('red', 'AutoYara'), ('green', 'AutoPYara')]
    for idx, (cumulative_avg, windowed_std_devs, color_info, label) in enumerate(zip(cumulative_avg_list, windowed_std_devs_list, [c[0] for c in colors], [c[1] for c in colors])):
        if len(cumulative_avg) > 0:  # Check if cumulative_avg is non-empty
            try:
                # Plot cumulative average
                valid_positions_subset = valid_positions[:len(cumulative_avg)]
                ax.plot(valid_positions_subset, cumulative_avg, color=color_info, marker='o', 
                        label=f'{label}', linestyle='-', linewidth=2)

                # Smooth windowed standard deviation curves with spline interpolation
                smoothed_windowed_std_devs = [s * np.exp(-0.005 * i) for i, s in enumerate(windowed_std_devs)]

                # Extend positions to the maximum cluster size
                extended_positions = np.linspace(min(valid_positions), max(valid_positions), 200)

                # Pad cumulative_avg and windowed_std_devs if necessary to match max cluster size
                if len(valid_positions_subset) < len(valid_positions):
                    last_avg = cumulative_avg[-1] if len(cumulative_avg) > 0 else 0
                    last_std = windowed_std_devs[-1] if len(windowed_std_devs) > 0 else 0
                    cumulative_avg_padded = np.pad(cumulative_avg, (0, len(valid_positions) - len(cumulative_avg)), mode='constant', constant_values=last_avg)
                    smoothed_windowed_std_devs_padded = np.pad(smoothed_windowed_std_devs, (0, len(valid_positions) - len(smoothed_windowed_std_devs)), mode='constant', constant_values=last_std)
                else:
                    cumulative_avg_padded = cumulative_avg
                    smoothed_windowed_std_devs_padded = smoothed_windowed_std_devs

                # Spline interpolation for cumulative average
                spline_cumulative_avg = make_interp_spline(valid_positions[:len(cumulative_avg_padded)], cumulative_avg_padded, k=3)
                extended_cumulative_avg = spline_cumulative_avg(extended_positions)

                # Spline interpolation for windowed standard deviation
                spline_std = make_interp_spline(valid_positions[:len(smoothed_windowed_std_devs_padded)], smoothed_windowed_std_devs_padded, k=3)
                extended_windowed_std_devs = spline_std(extended_positions)

                # Ensure standard deviation doesn't go negative and scale for visibility
                extended_windowed_std_devs = np.maximum(extended_windowed_std_devs * 1.5, 0)

                # Add windowed standard deviation band centered on cumulative average
                ax.fill_between(extended_positions, 
                                [extended_cumulative_avg[i] - extended_windowed_std_devs[i] for i in range(len(extended_cumulative_avg))],
                                [extended_cumulative_avg[i] + extended_windowed_std_devs[i] for i in range(len(extended_cumulative_avg))],
                                color=color_info, alpha=0.2)
            except Exception as e:
                raise RuntimeError(f"Error plotting data for DataFrame {idx + 1}: {e}")

    ax.legend(loc="upper center", ncol=2)

    # Set y-axis limits
    ax.set_ylim(0, 120)

    # Set plot attributes with font settings
    ax.set_ylabel('True Positive (%)', **AXIS_FONT)
    ax.set_xlabel('Cluster Size (Number of Items)', **AXIS_FONT)

    # Force x-axis ticks to include 500
    tick_sizes = [0, 25, 50, 75, 100, 500]
    size_to_pos = {size: idx + 1 for idx, size in enumerate(all_sizes)}
    max_size = max(all_sizes) if all_sizes else 100
    max_position = len(all_sizes)

    tick_positions = []
    tick_labels = []

    for tick in tick_sizes:
        if tick in size_to_pos:
            tick_positions.append(size_to_pos[tick])
            tick_labels.append(str(tick))
        elif tick <= 500:
            if tick == 500:
                scaled_pos = max_position + (500 - max_size) / max_size * 10
                tick_positions.append(scaled_pos)
                tick_labels.append('500')
            elif tick == 0:
                tick_positions.append(0)
                tick_labels.append('0')
            else:
                continue

    # Ensure ticks are sorted by value
    sorted_pairs = sorted(zip(tick_labels, tick_positions), key=lambda x: int(x[0]))
    tick_labels, tick_positions = zip(*sorted_pairs) if sorted_pairs else ([], [])

    print(f"Tick sizes: {list(tick_labels)}")
    print(f"Tick positions: {list(tick_positions)}")

    # Set ticks and adjust x-axis limits
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, **TICK_LABEL_FONT)
    ax.tick_params(axis='y', **TICK_FONT)
    ax.set_yticklabels(ax.get_yticklabels(), **TICK_LABEL_FONT)
    ax.set_xlim(-0.5, max(tick_positions) + 0.5)

    # Add grid
    ax.grid(axis='both')

    plt.tight_layout()
    fig.savefig(output_file, format='pdf')
    plt.show()


# import numpy as np
# import pandas as pd

# def shift_non_nan_up(col):
#     # Extract non-NaN values, preserving order
#     non_nan = [x for x in col if not pd.isna(x)]
#     # Pad with NaN to maintain original column length
#     return pd.Series(non_nan + [np.nan] * (len(col) - len(non_nan)), index=col.index)

# for i in range(5):
#     # Step 1: Replace 0.0 with NaN
#     df_listSSdeep[i] = df_listSSdeep[i].replace(0.0, np.nan)
#     # Step 2: Shift non-NaN values up for each column
#     df_listSSdeep[i] = df_listSSdeep[i].apply(shift_non_nan_up, axis=0)
