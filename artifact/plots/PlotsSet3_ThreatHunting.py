"""Figure set 3: threat-hunting train/test comparison (paper Claim 5).

Each threat-hunting cluster folder holds the rules' measured TP rates on the cluster's
training samples and on held-out test samples, for AutoPYara and AutoYara:

    ThreatHunting/<experiment>/Th<t>/Ratio_0.75/cluster_<n>/
        train_files.txt, test_files.txt,
        tprateAutoPYara_Train.txt, tprateAutoPYara_Test.txt,
        tprateAutoyaraBase_Train.txt, tprateAutoyaraBase_Test.txt

Each ``tprate*.txt`` contains a line like ``TP Rate: 0.4737 (9/19)``. A cluster is
used only if all six files exist. The folders of the five thresholds (50..90) are
pooled.

Figure layout (``plot_cluster_std_dev_mirrored``): a mirrored line plot with
training clusters on the left (x < 0) and test clusters on the right (x > 0).
  * x = cluster size = number of samples a rule was evaluated on (the ``19`` above),
    placed by rank of the distinct sizes (not a linear scale), mirrored around the
    smallest size at x = 0;
  * y = running (cumulative) mean of the per-size *median* TP rate, in %; sizes
    whose median is 0 are skipped;
  * purple = AutoPYara, brown = AutoYara; the dotted lines are each curve's mean;
  * the y-axis is zoomed to 50..100 %.

Figures written (under ``--out-dir``, default ``<repo>/results/figures``):

=================================================================  ================================
File                                                               Experiment folder
=================================================================  ================================
Claim5_Threathunting/sdhash_WithHeuOnly_IdealPlot.pdf              ThreatHunting/IdealStream_HEU
Claim5_Threathunting/sdhash_WithNOHeuOnly_IdealPlot.pdf            ThreatHunting/NonIdealStream_RDM
Claim5_Threathunting/sdhash_RealWorldStream_PHeuPlot.pdf           ThreatHunting/RealWorldStream_PHeu
=================================================================  ================================

Usage:
  python PlotsSet3_ThreatHunting.py            # all CPUs
  python PlotsSet3_ThreatHunting.py -j 4       # 4 worker processes
  python PlotsSet3_ThreatHunting.py --help

Refactor notes (no change to data, statistics or figure content):
  * The two copy-pasted load loops are the table ``EXPERIMENTS`` (one folder read per
    task, run in parallel); the plot function is unchanged.
  * The ``try/except NameError`` around the plot calls was dropped: it could only
    hide real errors.
"""
import os
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_common import PathTask, script_main

# List of required files for a valid cluster
required_files = [
    "test_files.txt",
    "tprateAutoPYara_Test.txt",
    "tprateAutoPYara_Train.txt",
    "tprateAutoyaraBase_Test.txt",
    "tprateAutoyaraBase_Train.txt",
    "train_files.txt"
]

# The tprate files we're interested in (order = order of check_and_extract's result)
tprate_files = {
    "AutoPYara_Test": "tprateAutoPYara_Test.txt",
    "AutoPYara_Train": "tprateAutoPYara_Train.txt",
    "AutoyaraBase_Test": "tprateAutoyaraBase_Test.txt",
    "AutoyaraBase_Train": "tprateAutoyaraBase_Train.txt"
}


def parse_tp_rate(line):
    # Parse line like "TP Rate: 0.4737 (9/19)"
    match = re.search(r"TP Rate: (\d+\.\d+) \((\d+)/(\d+)\)", line.strip())
    if match:
        tp_rate = float(match.group(1))
        tp = int(match.group(2))
        total = int(match.group(3))
        return tp_rate, tp, total
    return None, None, None


def check_and_extract(folder_path):
    """Read one ``Th<t>/Ratio_0.75`` folder.

    Returns four DataFrames (columns cluster, tp_rate, tp, total), in the order of
    ``tprate_files``: AutoPYara_Test, AutoPYara_Train, AutoyaraBase_Test,
    AutoyaraBase_Train. Clusters missing any of ``required_files`` are skipped.
    """
    # Get list of cluster folders
    cluster_folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f)) and f.startswith("cluster_")]

    # Initialize lists for each dataframe
    data = {key: [] for key in tprate_files.keys()}

    # Check each cluster folder
    for cluster in cluster_folders:
        cluster_path = os.path.join(folder_path, cluster)
        # Check if all required files exist
        all_files_present = all(os.path.isfile(os.path.join(cluster_path, file)) for file in required_files)

        if all_files_present:
            # Extract data from each tprate file
            for df_name, file_name in tprate_files.items():
                file_path = os.path.join(cluster_path, file_name)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        tp_rate, tp, total = parse_tp_rate(content)
                        if tp_rate is not None:
                            data[df_name].append({
                                'cluster': cluster,
                                'tp_rate': tp_rate,
                                'tp': tp,
                                'total': total
                            })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue

    # Create dataframes
    dataframes = [pd.DataFrame(data[name]) for name in tprate_files.keys()]

    return dataframes


# --------------------------------------------------------------------------------------
# Extraction tasks: one folder per (experiment, threshold).
# --------------------------------------------------------------------------------------
THRESHOLDS = (50, 60, 70, 80, 90)
EXPERIMENTS = [  # (experiment folder under ThreatHunting/, output figure)
    ('IdealStream_HEU', 'Claim5_Threathunting/sdhash_WithHeuOnly_IdealPlot.pdf'),
    ('NonIdealStream_RDM', 'Claim5_Threathunting/sdhash_WithNOHeuOnly_IdealPlot.pdf'),
    ('RealWorldStream_PHeu', 'Claim5_Threathunting/sdhash_RealWorldStream_PHeuPlot.pdf'),
]
TASKS = [PathTask(exp, check_and_extract, (f'ThreatHunting/{exp}/Th{t}/Ratio_0.75',))
         for exp, _ in EXPERIMENTS for t in THRESHOLDS]

# --------------------------------------------------------------------------------------
# Style
# --------------------------------------------------------------------------------------
RC_PARAMS = {'font.family': 'DejaVu Sans', 'font.weight': 900, 'font.size': 22}
TICK_FONT = {'fontsize': 22, 'fontweight': 'bold'}


def plot_cluster_std_dev_mirrored(
    auto_pyara_train_s3, autoyara_base_train_s3,
    auto_pyara_test_s3, autoyara_base_test_s3,
    output_file='mirrored_sdhash_0.75.pdf'
):
    """
    Plot mirrored cumulative average true positive rates for AutoPYara and AutoYara
    on the Ratio_0.75 training (left) and test (right) datasets.

    Parameters:
    - auto_pyara_train_s3: List of DataFrames for AutoPYara train data (one per threshold)
    - autoyara_base_train_s3: List of DataFrames for AutoYara train data
    - auto_pyara_test_s3: List of DataFrames for AutoPYara test data
    - autoyara_base_test_s3: List of DataFrames for AutoYara test data
    - output_file: File path to save the plot (default: 'mirrored_sdhash_0.75.pdf')
    """
    # Define datasets for training and test (only threshold 0.75)
    datasets = [
        ('AutoPYara 0.75', pd.concat(auto_pyara_train_s3, ignore_index=True), '#9467bd', 'train'),  # Purple
        ('AutoYara 0.75', pd.concat(autoyara_base_train_s3, ignore_index=True), '#8c564b', 'train'),  # Brown
        ('AutoPYara 0.75', pd.concat(auto_pyara_test_s3, ignore_index=True), '#9467bd', 'test'),   # Purple
        ('AutoYara 0.75', pd.concat(autoyara_base_test_s3, ignore_index=True), '#8c564b', 'test')    # Brown
    ]

    # Collect all unique cluster sizes across all datasets
    all_sizes = set()
    min_sizes = {}  # Store minimum cluster size per dataset
    for dataset_name, df, _, data_type in datasets:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        try:
            sizes = df['total'].dropna().astype(int).tolist()
            if sizes:
                all_sizes.update(sizes)
                min_sizes[dataset_name + '_' + data_type] = min(sizes)
        except (ValueError, KeyError) as e:
            print(f"Error processing {dataset_name} ({data_type}): {e}")
            continue

    if not all_sizes:
        raise ValueError("No valid cluster sizes found in the provided datasets")

    # Sort cluster sizes
    all_sizes = sorted(all_sizes)
    global_min_cluster_size = min(all_sizes)
    all_sizes = [size for size in all_sizes if size >= global_min_cluster_size]

    # Define custom ticks, starting from global_min_cluster_size
    tick_sizes = [global_min_cluster_size, 25, 50, 75, 100, 1000]
    tick_sizes = [t for t in tick_sizes if t >= global_min_cluster_size]
    tick_positions = []
    for tick in tick_sizes:
        if all_sizes:
            closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
            tick_positions.append(closest_idx + 1)

    # Adjust tick positions to place first tick at x=0
    first_tick_pos = tick_positions[0]
    adjusted_positions = [0] + [p - first_tick_pos for p in tick_positions[1:]]
    adjusted_sizes = tick_sizes

    # Create figure and single subplot
    fig, ax = plt.subplots(figsize=(16, 6))
    ax_test = ax.twiny()  # Twin x-axis for test data

    # Combined handles and labels for legend
    handles = []
    labels = []
    plotted_labels = set()

    # Plot for all datasets
    for dataset_name, df, color, data_type in datasets:
        df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
        dataset_min_size = min_sizes.get(dataset_name + '_' + data_type, global_min_cluster_size)
        dataset_sizes = [size for size in all_sizes if size >= dataset_min_size]
        if not dataset_sizes:
            print(f"No valid sizes for {dataset_name} ({data_type})")
            continue
        datasets_per_threshold = [
            (df[df['total'] == size]['tp_rate'].dropna().astype(float) * 100).tolist()
            if len(df[df['total'] == size]) > 0 else [0]
            for size in all_sizes
        ]
        medians = [np.median(d) if d else np.nan for d in datasets_per_threshold]
        valid_medians = [m for m in medians if not np.isnan(m) and m > 0]
        valid_positions = [j + 1 for j, d in enumerate(datasets_per_threshold) if d and np.median(d) > 0]
        dataset_min_index = all_sizes.index(dataset_min_size) + 1 if dataset_min_size in all_sizes else 1
        valid_positions = [p for p in valid_positions if p >= dataset_min_index]
        valid_medians = [medians[p-1] for p in valid_positions]

        if valid_medians:
            # Adjust positions for mirrored plot
            plot_positions = [-(p - first_tick_pos) for p in valid_positions] if data_type == 'train' else [p - first_tick_pos for p in valid_positions]
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            line, = ax.plot(plot_positions[:len(cumulative_avg)], cumulative_avg,
                           linewidth=2, color=color)
            avg_value = np.mean(cumulative_avg)
            ax.axhline(y=avg_value, color=color, linestyle=':', linewidth=1.5)
            if dataset_name not in plotted_labels:
                handles.append(line)
                labels.append(dataset_name)
                plotted_labels.add(dataset_name)

    # Configure axes
    ax.spines['left'].set_position(('axes', 0))  # Move y-axis to left edge
    ax.spines['right'].set_color('none')
    ax.spines['bottom'].set_position(('data', 50))
    ax.spines['top'].set_color('none')

    # Set symmetric x-axis limits
    max_pos = max([abs(p) for p in adjusted_positions]) + 1
    ax.set_xlim(-max_pos, max_pos)
    ax_test.set_xlim(max_pos, -max_pos)  # Reverse for mirroring

    # Set x-axis ticks and labels
    ax.set_xticks([-p for p in adjusted_positions[1:]] + [0] + adjusted_positions[1:])
    ax.set_xticklabels([str(s) for s in adjusted_sizes[1:]] + [str(adjusted_sizes[0])] + [str(s) for s in adjusted_sizes[1:]], **TICK_FONT)
    ax_test.set_xticks([])  # Hide test x-axis ticks

    # Label axes
    ax.set_ylabel('True Positive (%)', **TICK_FONT)
    ax.set_xlabel(' <-- Train             Cluster Size            Test -->', **TICK_FONT, x=0.5)
    ax.set_ylim(50, 100)

    # Add legend
    ax.legend(
        handles, labels,
        loc='upper center',
        bbox_to_anchor=(0.5, .15),
        ncol=2,  # Adjusted for fewer datasets
        prop={'size': 22, 'family': 'DejaVu Sans', 'weight': 'bold'},
        frameon=False
    )

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.5)

    # Save plot
    fig.subplots_adjust(top=0.85, left=0.15)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    fig.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.close(fig)


def make_figures(d, out_dir):
    """Draw one mirrored figure per experiment from ``d`` = {experiment: [4 DataFrames per folder]}."""
    plt.rcParams.update(RC_PARAMS)
    written = []
    for exp, rel_path in EXPERIMENTS:
        # per folder: [AutoPYara_Test, AutoPYara_Train, AutoyaraBase_Test, AutoyaraBase_Train]
        autopyar_test, autopyara_train, autoyar_test, autoyara_train = (list(x) for x in zip(*d[exp]))
        path = os.path.join(out_dir, rel_path)
        plot_cluster_std_dev_mirrored(
            autopyara_train, autoyara_train,
            autopyar_test, autoyar_test,
            output_file=path
        )
        plt.close('all')
        written.append(path)
    return written


if __name__ == '__main__':
    sys.exit(script_main('Figure set 3 (Claim 5): threat-hunting train/test comparison. '
                         'See module docstring.', TASKS, make_figures))
