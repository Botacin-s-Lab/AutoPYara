
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
    ax2.set_ylabel('True Positive (%)', **TICK_FONT)
    ax2.set_ylim(50, 100)
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
