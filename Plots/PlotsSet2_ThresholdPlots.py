"""Figure set 2: TP rate vs. cluster size per similarity threshold (paper Claim 4).

All inputs are the SSdeep clusterings (thresholds 50..90) with rules generated using
the *retrained* bloom filters. ``util.Extractor(..., mr=1, short=False)`` returns, per
threshold, a DataFrame with one column per cluster size holding the TP rate of every
cluster of that size (one rule-generation run).

Each figure has one line per threshold. Reading a line from left to right:
  * the x-axis walks through the distinct cluster sizes in increasing order (one
    position per size, i.e. rank, not a linear scale); tick labels 0/25/50/75/100/500
    sit at the position of the nearest existing size;
  * y = running (cumulative) mean of the per-size *median* TP rate, in %;
  * the dotted horizontal line in the same colour is the mean of that curve.
The y-axis is zoomed to 50..100 %.

Figures written (under ``--out-dir``, default ``Plots/Figures``), all in
``Claim4_ThresHoldFigures/``:

==========================================================  =====================================
File                                                        Rule generator / K heuristic
==========================================================  =====================================
AutoYara_SSdeepAVG_ZoomRTBF.pdf                             AutoYara
AutoPYara_SSdeepAVG_ZoomRTBF.pdf                            AutoPYara
AutoPYaraBestK_SSdeepAVG_ZoomRTBF.pdf                       AutoPYara, best K
AutoPYaraWorstK_SSdeepAVG_ZoomRTBF.pdf                      AutoPYara, worst K
AutoPYaraHEUModeK_SSdeepAVG_ZoomRTBF.pdf                    informed heuristic: avg/mode K  (*)
AutoPYaraHEUMaxK_SSdeepAVG_ZoomRTBF.pdf                     informed heuristic: max K       (*)
AutoPYaraHEURandomK_SSdeepAVG_ZoomRTBF.pdf                  informed heuristic: random K    (*)
AutoPYaraUninformedHEUMeanK_SSdeepAVG_ZoomRTBF.pdf          uninformed heuristic: mean K
AutoPYaraUninformedHEUMaxK_SSdeepAVG_ZoomRTBF.pdf           uninformed heuristic: max K
AutoPYaraUninformedHEURandomK_SSdeepAVG_ZoomRTBF.pdf        uninformed heuristic: random K
==========================================================  =====================================

(*) These three datasets are post-processed before plotting (see ``DROP_ZERO_GROUPS``):
``util.ensure_columns`` aligns them to sizes 1..max, then TP values of exactly 0 become
NaN and all-NaN size columns are dropped.

Inputs (relative to ``--data-dir``, default ``../data``):
  clusterCSV/ssdeep/th<t>.csv and ruleEval/retrainedBloomFilters/ssdeep/.../merged_group_1.yar
The exact list is ``TASKS`` below (``--dry-run`` prints it and checks every file exists).

Usage:
  python PlotsSet2_ThresholdPlots.py            # all CPUs
  python PlotsSet2_ThresholdPlots.py -j 8       # 8 worker processes
  python PlotsSet2_ThresholdPlots.py -j 1       # sequential (original behaviour)
  python PlotsSet2_ThresholdPlots.py --help

Refactor notes (no change to data, statistics or figure content):
  * The 10 copy-pasted load loops are the table ``TASKS``; the dataset names are the
    original variable names, the paths/``mr`` values/order are unchanged.
  * ``numpy`` is imported up front: the notebook-derived original used ``np`` ~130
    lines before importing it and stopped with a NameError when run as a script.
  * Figures are closed after saving; the backend is forced to Agg (save-only).
"""
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_common import script_main, threshold_tasks
from util import ensure_columns

# --------------------------------------------------------------------------------------
# Extraction tasks (all: SSdeep clusters, retrained bloom filters, mr=1, full frames).
# Group names = the original variable names.
# --------------------------------------------------------------------------------------
SSDEEP_CSV = 'clusterCSV/ssdeep/th{t}.csv'
RULES = 'ruleEval/retrainedBloomFilters/ssdeep/{variant}/Th{{t}}rules/merged_group_1.yar'

VARIANTS = [  # (group name, rule directory under retrainedBloomFilters/ssdeep/)
    ('df_listSSdeep', 'Autoyara'),                          # AutoYara
    ('df_listSSdeepPyara', 'AutoPyara'),                    # AutoPYara
    ('df_listSSdeepPyaraBestK', 'BestKyara'),               # AutoPYara, best K
    ('df_listSSdeepPyaraWorstK', 'WorstPyara'),             # AutoPYara, worst K
    ('df_listSSdeepPyaraModeK', 'Heuristics/avgk'),         # heuristic: mode/avg K
    ('df_listSSdeepPyaraMaxK', 'Heuristics/maxk'),          # heuristic: max K
    ('df_listSSdeepPyaraRandomK', 'Heuristics/randomK'),    # heuristic: random K
    ('df_listSSdeepPyaraBadHEUMeanK', 'Heuristics/BAD/Mean'),      # uninformed: mean K
    ('df_listSSdeepPyaraBadHEUMaxK', 'Heuristics/BAD/Max'),        # uninformed: max K
    ('df_listSSdeepPyaraBadHEURandomK', 'Heuristics/BAD/Random'),  # uninformed: random K
]
TASKS = [task for group, variant in VARIANTS
         for task in threshold_tasks(group, SSDEEP_CSV, RULES.format(variant=variant), mr=1, short=False)]

# Groups whose zero TP rates are treated as missing before plotting (see docstring).
DROP_ZERO_GROUPS = ('df_listSSdeepPyaraModeK', 'df_listSSdeepPyaraMaxK', 'df_listSSdeepPyaraRandomK')

# --------------------------------------------------------------------------------------
# Style
# --------------------------------------------------------------------------------------
RC_PARAMS = {'font.family': 'DejaVu Sans', 'font.weight': 600, 'font.size': 22}
AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 900, 'size': 14.0}   # legend
TICK_FONT = {'fontsize': 22, 'fontweight': 'bold'}                  # ticks + axis labels


def drop_zero_scores(df_list):
    """Post-processing of the three informed-heuristic datasets (unchanged from the original)."""
    df_list = ensure_columns(df_list)
    # Replace 0 with NaN and drop all-NaN columns, per DataFrame in the list
    return [
        df.replace(0, np.nan).dropna(axis=1, how='all')
        for df in df_list
    ]


def plot_cluster_std_dev_boxplot_static_all_merge_zoom(
    dfs,
    drop_smallest_n=0,
    output_file1='cumulative_median_plot.pdf',
):
    """Cumulative-median line plot of TP rate vs. cluster size, one line per threshold.

    (The name is historical: no boxplot is drawn.)

    dfs: exactly five DataFrames (thresholds 50, 60, 70, 80, 90), columns = cluster
         sizes, values = TP rates in [0, 1] (None/'None'/NaN = no cluster).
    drop_smallest_n: skip the n smallest cluster sizes (0 in every call here).
    output_file1: PDF path; parent folders are created.
    """
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

    # Define custom ticks: x position (1-based rank) of the size closest to each label
    tick_sizes = [0, 25, 50, 75, 100, 500]
    tick_positions = []
    for tick in tick_sizes:
        if all_sizes:
            closest_idx = min(range(len(all_sizes)), key=lambda i: abs(all_sizes[i] - tick))
            tick_positions.append(closest_idx + 1)

    # ---------- Plot 1: Cumulative Median ----------
    fig1, ax1 = plt.subplots(figsize=(15, 6))
    for i, df in enumerate(filtered_dfs):
        # TP rates (in %) of every cluster of each size
        datasets = [
            (df[size].dropna().astype(float) * 100).tolist() if size in df.columns else []
            for size in all_sizes
        ]
        medians = [np.median(d) if d else np.nan for d in datasets]
        valid_medians = [m for m in medians if not np.isnan(m)]
        valid_positions = [j + 1 for j, d in enumerate(datasets) if d]

        if valid_medians:
            # Running mean of the per-size medians, plus its overall mean as a dotted line
            cumulative_avg = np.cumsum(valid_medians) / np.arange(1, len(valid_medians) + 1)
            line, = ax1.plot(valid_positions[:len(cumulative_avg)], cumulative_avg, linewidth=2, label=titles[i])
            avg_value = np.mean(cumulative_avg)
            ax1.axhline(y=avg_value, color=line.get_color(), linestyle=':', linewidth=1.5)

    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels([str(t) for t in tick_sizes], **TICK_FONT)
    ax1.set_xlabel('Cluster Size (Number of Items)', **TICK_FONT)
    ax1.set_ylabel('True Positive (%)', **TICK_FONT)
    ax1.set_ylim(50, 100)
    ax1.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.02),
        ncol=5,
        prop=AXIS_FONT,
        frameon=False
    )
    ax1.grid(True, linestyle='--', alpha=0.5)
    if output_file1:
        os.makedirs(os.path.dirname(output_file1), exist_ok=True)
        fig1.subplots_adjust(top=0.8)
        fig1.savefig(output_file1, format='pdf', bbox_inches='tight')


FIGURES = [  # (group name, output file), in the original order
    ('df_listSSdeep', 'AutoYara_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyara', 'AutoPYara_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraBestK', 'AutoPYaraBestK_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraWorstK', 'AutoPYaraWorstK_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraModeK', 'AutoPYaraHEUModeK_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraMaxK', 'AutoPYaraHEUMaxK_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraRandomK', 'AutoPYaraHEURandomK_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraBadHEUMeanK', 'AutoPYaraUninformedHEUMeanK_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraBadHEUMaxK', 'AutoPYaraUninformedHEUMaxK_SSdeepAVG_ZoomRTBF.pdf'),
    ('df_listSSdeepPyaraBadHEURandomK', 'AutoPYaraUninformedHEURandomK_SSdeepAVG_ZoomRTBF.pdf'),
]


def make_figures(d, out_dir):
    """Post-process and draw the ten figures from ``d`` = {group name: [5 DataFrames]}."""
    for group in DROP_ZERO_GROUPS:
        d[group] = drop_zero_scores(d[group])
    plt.rcParams.update(RC_PARAMS)
    written = []
    for group, name in FIGURES:
        path = os.path.join(out_dir, 'Claim4_ThresHoldFigures', name)
        plot_cluster_std_dev_boxplot_static_all_merge_zoom(d[group], drop_smallest_n=0, output_file1=path)
        plt.close('all')
        written.append(path)
    return written


if __name__ == '__main__':
    sys.exit(script_main('Figure set 2 (Claim 4): TP rate vs. cluster size per threshold. '
                         'See module docstring.', TASKS, make_figures))
