"""Figure set 1: mean True-Positive-rate bar charts (paper Claims 1-3).

For every (clustering, YARA rule set) pair, ``util.Extractor(..., short=True)`` parses
the ``// Input TP Rate: X/Y`` comment of each generated rule and returns one value per
cluster: its TP rate averaged over ``mr`` generation runs. Each bar below is the mean
(error bar = population std) of all those per-cluster values, pooled over the five
similarity thresholds (50..90) of a clustering, and shown in percent.

Figures written (under ``--out-dir``, default ``<repo>/results/figures``):

====================================================================================  =============================================
File                                                                                  Bars
====================================================================================  =============================================
Claim1_IncorrectBaseLines/AutoYara_baselineBoxPlotEMBF.pdf                             AutoYara, Ember blooms; zero-TP clusters dropped
Claim1_IncorrectBaseLines/AutoYara_EMBF.pdf                                            same, zero-TP clusters kept
Claim2_BloomFiltersMatter/AutoYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf        AutoYara: Ember (light) vs retrained (dark)
Claim3_YaraVsPYara/AutoYaraVSAutoPYaraRTBF.pdf                                         retrained: AutoPYara (light) vs AutoYara (dark)
Claim2_BloomFiltersMatter/AutoPYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf       AutoPYara: retrained (light) vs Ember (dark)
====================================================================================  =============================================

Each chart has three bar groups: SSdeep, J-SDhash (sdhash) and VirusTotal clusterings.

Inputs (relative to ``--data-dir``, default ``<repo>/data``):
  clusterCSV/{sdhash/Th<t>.csv, ssdeep/th<t>.csv, virusTotal/MainVtCluster.csv}
  ruleEval/{originalBloomFilters,retrainedBloomFilters}/.../merged_group_1.yar
The exact list is ``TASKS`` below (``--dry-run`` prints it and checks every file exists).

Usage:
  python PlotsSet1_Boxplots.py            # all CPUs
  python PlotsSet1_Boxplots.py -j 8       # 8 worker processes
  python PlotsSet1_Boxplots.py -j 1       # sequential (original behaviour)
  python PlotsSet1_Boxplots.py --help

Refactor notes (no change to data, statistics or figure content):
  * The 12 copy-pasted load loops are the table ``TASKS``; the dataset names are the
    original variable names, the paths/``mr`` values/order are unchanged.
  * The original defined the font constants twice (16/22, then 28) before any plot was
    drawn. Python reads globals at call time, so *both* functions rendered with the
    second set; only those effective values are kept here.
  * Figures are closed after saving; the backend is forced to Agg (save-only).
"""
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from plot_common import Task, script_main, threshold_tasks

# --------------------------------------------------------------------------------------
# Extraction tasks. Group names = the original variable names.
# Ember = the original (pre-trained) bloom filters shipped with AutoYara ("originalBloomFilters");
# RTBF  = bloom filters retrained on our data ("retrainedBloomFilters").
# --------------------------------------------------------------------------------------
SDHASH_CSV = 'clusterCSV/sdhash/Th{t}.csv'
SSDEEP_CSV = 'clusterCSV/ssdeep/th{t}.csv'
VT_CSV = 'clusterCSV/virusTotal/MainVtCluster.csv'
RULES = 'ruleEval/{bloom}/{hash}/{tool}/Th{{t}}rules/merged_group_1.yar'

TASKS = [
    # ---- AutoYara, Ember bloom filters ----
    *threshold_tasks('df_listSdhash', SDHASH_CSV,
                     RULES.format(bloom='originalBloomFilters', hash='sdhash', tool='AutoYara'), mr=10, short=True),
    *threshold_tasks('df_listSSdeep', SSDEEP_CSV,
                     RULES.format(bloom='originalBloomFilters', hash='ssdeep', tool='AutoYaraBaseline'), mr=10, short=True),
    Task('df_listVT', VT_CSV,
         'ruleEval/originalBloomFilters/virusTotal/AutoyaraBaseline/VirusTotal/merged_group_1.yar', mr=5, short=True),
    # ---- AutoYara, retrained bloom filters ----
    *threshold_tasks('df_listSdhashRTBF', SDHASH_CSV,
                     RULES.format(bloom='retrainedBloomFilters', hash='sdhash', tool='AutoYara'), mr=5, short=True),
    *threshold_tasks('df_listSSdeepRTBF', SSDEEP_CSV,
                     RULES.format(bloom='retrainedBloomFilters', hash='ssdeep', tool='Autoyara'), mr=5, short=True),
    Task('df_listVTRTBF', VT_CSV,
         'ruleEval/retrainedBloomFilters/virusTotal/AutoYara/merged_group_1.yar', mr=5, short=True),
    # ---- AutoPYara, Ember bloom filters ----
    *threshold_tasks('df_listSdhashPyara', SDHASH_CSV,
                     RULES.format(bloom='originalBloomFilters', hash='sdhash', tool='AutoPYara'), mr=10, short=True),
    *threshold_tasks('df_listSSdeepPyara', SSDEEP_CSV,
                     RULES.format(bloom='originalBloomFilters', hash='ssdeep', tool='AutoPYaraBest'), mr=10, short=True),
    Task('df_listVTPyara', VT_CSV,
         'ruleEval/originalBloomFilters/virusTotal/AutoPYara/merged_group_1.yar', mr=5, short=True),
    # ---- AutoPYara, retrained bloom filters ----
    *threshold_tasks('df_listSdhashPyaraRTBF', SDHASH_CSV,
                     RULES.format(bloom='retrainedBloomFilters', hash='sdhash', tool='AutoPYara'), mr=5, short=True),
    *threshold_tasks('df_listSSdeepPyaraRTBF', SSDEEP_CSV,
                     RULES.format(bloom='retrainedBloomFilters', hash='ssdeep', tool='AutoPyara'), mr=5, short=True),
    Task('df_listVTPyaraRTBF', VT_CSV,
         'ruleEval/retrainedBloomFilters/virusTotal/AutoPYara/merged_group_1.yar', mr=5, short=True),
]

# --------------------------------------------------------------------------------------
# Style (values in effect when the original script drew its figures).
# --------------------------------------------------------------------------------------
RC_PARAMS = {'font.family': 'DejaVu Sans', 'font.weight': 600, 'font.size': 28}
AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 28}
TICK_FONT_SIZE = 28


def plot_bar_with_colored_textures_left_labels(list1, list2, list3, labels=("List 1", "List 2", "List 3"), nans=True, save_path=None):
    """One bar per dataset list: mean +- std of all pooled per-cluster TP rates, in %.

    Each ``listN`` is a list of per-cluster Series (one per threshold); they are
    concatenated side by side and flattened, NaNs (clusters absent at a threshold)
    are always dropped. ``nans=True`` keeps clusters whose TP rate is exactly 0;
    ``nans=False`` also drops them (the name is historical: it is about zeros).
    The mu/sigma of each bar is written to its upper left.
    """
    def combine_and_flatten(df_list, nans):
        combined = pd.concat(df_list, axis=1)
        values = combined.values.flatten()
        if nans:
            return values[~pd.isna(values)]  # Remove NaNs only (zeros kept)
        else:
            return values[~pd.isna(values) & (values != 0)]  # Remove NaNs and zeros

    data1 = combine_and_flatten(list1, nans)
    data2 = combine_and_flatten(list2, nans)
    data3 = combine_and_flatten(list3, nans)

    data = [data1, data2, data3]
    means = [np.mean(d)*100 for d in data]  # Convert to percentage
    stds = [np.std(d)*100 for d in data]    # Convert to percentage

    x = np.arange(len(labels))
    colors = ['#4C72B0', '#55A868', '#C44E52']  # Blue, Green, Red
    hatches = ['//', 'xx', 'oo']

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    bars = ax.bar(
        x, means, yerr=stds, capsize=10,
        color=colors, edgecolor='black', linewidth=1.5
    )

    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    # Place stats to the LEFT of the bars, aligned with bar height
    x_offset = -0.15  # left of bar
    y_offset = 1.0    # slightly above bar height (adjust as needed)

    for i, (mean, std) in enumerate(zip(means, stds)):
        ax.text(
            i + x_offset, mean + y_offset,
            f"μ={mean:.1f}\nσ={std:.1f}",
            ha='right', va='bottom', fontsize=16, fontweight='bold'
        )

    # Fix y-axis limits strictly 0 to 100, no autoscaling
    ax.set_ylim(0, 100)

    ax.set_ylabel("True Positive Rate (%)", **AXIS_FONT)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=TICK_FONT_SIZE, fontweight='bold')
    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_yticklabels([f"{y}" for y in np.arange(0, 101, 10)], fontsize=TICK_FONT_SIZE, fontweight='bold')
    ax.tick_params(axis='both', which='major', labelsize=TICK_FONT_SIZE)
    ax.grid(True, axis='y', linestyle='--', alpha=0.5)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)


def plot_side_by_side_bar_with_textures(
    list1, list2, list3, list4, list5, list6,
    labels=("SSdeep", "J-SDhash", "VirusTotal"), head1='', head2='',
    save_path=None
):
    """Paired bars per clustering: lists 1-3 (light, left, legend ``head1``) vs
    lists 4-6 (dark, right, legend ``head2``).

    Same statistic as above with NaNs dropped and zeros kept. The legend shows the
    three light swatches (middle one labelled ``head1``) in the left column and the
    three dark swatches (``head2``) in the right column.
    """
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
    base_colors = ['#4C72B0', '#55A868', '#C44E52']        # Light - lists 1-3 (head1)
    retrain_colors = ['#1C3D63', '#2E5C3C', '#802D33']     # Dark - lists 4-6 (head2)
    hatches = ['//', 'xx', 'oo']

    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)

    # Lists 1-3 (lighter, left)
    bars_primary = ax.bar(
        x - width/2, means_primary, width=width, yerr=stds_primary, capsize=10,
        color=base_colors, edgecolor='black', linewidth=1.5
    )
    for bar, hatch in zip(bars_primary, hatches):
        bar.set_hatch(hatch)

    # Lists 4-6 (darker, right)
    bars_secondary = ax.bar(
        x + width/2, means_secondary, width=width, yerr=stds_secondary, capsize=10,
        color=retrain_colors, edgecolor='black', linewidth=1.5
    )
    for bar, hatch in zip(bars_secondary, hatches):
        bar.set_hatch(hatch)

    # Add text annotations
    for i, (mu1, std1, mu2, std2) in enumerate(zip(means_primary, stds_primary, means_secondary, stds_secondary)):
        ax.text(x[i] - width/1.5, mu1 + 0.4, f"μ={mu1:.1f}\nσ={std1:.1f}", fontsize=12, ha='right', fontweight='bold')
        ax.text(x[i] + width/1.5, mu2 + 0.4, f"μ={mu2:.1f}\nσ={std2:.1f}", fontsize=12, ha='left', fontweight='bold')

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
        Patch(facecolor=base_colors[1], edgecolor='black', hatch='xx', label=head1),
        Patch(facecolor=base_colors[2], edgecolor='black', hatch='oo', label=''),
        Patch(facecolor=retrain_colors[0], edgecolor='black', hatch='//', label=''),
        Patch(facecolor=retrain_colors[1], edgecolor='black', hatch='xx', label=head2),
        Patch(facecolor=retrain_colors[2], edgecolor='black', hatch='oo', label=''),
    ]

    ax.legend(
        handles=legend_elements,
        loc='upper center',
        bbox_to_anchor=(0.5, 1.15),  # move above the axes
        fontsize=18,
        frameon=False,
        ncol=2,
        borderpad=1,
        labelspacing=0.1
    )

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)


def make_figures(d, out_dir):
    """Draw the five figures (original order) from ``d`` = {group name: [per-cluster Series]}."""
    plt.rcParams.update(RC_PARAMS)
    labels = ("SSdeep", "J-SDhash", "VirusTotal")
    figures = [
        (plot_bar_with_colored_textures_left_labels,
         (d['df_listSSdeep'], d['df_listSdhash'], d['df_listVT']),
         dict(labels=labels, nans=False),
         'Claim1_IncorrectBaseLines/AutoYara_baselineBoxPlotEMBF.pdf'),
        (plot_bar_with_colored_textures_left_labels,
         (d['df_listSSdeep'], d['df_listSdhash'], d['df_listVT']),
         dict(labels=labels, nans=True),
         'Claim1_IncorrectBaseLines/AutoYara_EMBF.pdf'),
        (plot_side_by_side_bar_with_textures,
         (d['df_listSSdeep'], d['df_listSdhash'], d['df_listVT'],
          d['df_listSSdeepRTBF'], d['df_listSdhashRTBF'], d['df_listVTRTBF']),
         dict(labels=labels, head1='Ember Bloom Filters', head2='Retrained Bloom Filters'),
         'Claim2_BloomFiltersMatter/AutoYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf'),
        (plot_side_by_side_bar_with_textures,
         (d['df_listSSdeepPyaraRTBF'], d['df_listSdhashPyaraRTBF'], d['df_listVTPyaraRTBF'],
          d['df_listSSdeepRTBF'], d['df_listSdhashRTBF'], d['df_listVTRTBF']),
         dict(labels=labels, head1='AutoPYara', head2='AutoYara'),
         'Claim3_YaraVsPYara/AutoYaraVSAutoPYaraRTBF.pdf'),
        (plot_side_by_side_bar_with_textures,
         (d['df_listSSdeepPyaraRTBF'], d['df_listSdhashPyaraRTBF'], d['df_listVTPyaraRTBF'],
          d['df_listSSdeepPyara'], d['df_listSdhashPyara'], d['df_listVTPyara']),
         dict(labels=labels, head1='Retrained Bloom Filters', head2='Ember Bloom Filters'),
         'Claim2_BloomFiltersMatter/AutoPYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf'),
    ]
    written = []
    for plot_fn, lists, kwargs, rel_path in figures:
        path = os.path.join(out_dir, rel_path)
        plot_fn(*lists, save_path=path, **kwargs)
        plt.close('all')
        written.append(path)
    return written


if __name__ == '__main__':
    sys.exit(script_main('Figure set 1 (Claims 1-3): mean TP-rate bar charts. See module docstring.',
                         TASKS, make_figures))
