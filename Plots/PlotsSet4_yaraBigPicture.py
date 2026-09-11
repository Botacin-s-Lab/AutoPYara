"""Figure set 4: every AutoYara/AutoPYara configuration in one chart (paper Claim 6).

A single "ladder" bar chart ranks the mean TP rate of 15 configurations, all on the
SSdeep clusterings (thresholds 50..90 pooled). ``util.Extractor(..., short=True)``
gives the per-cluster TP rate averaged over ``mr`` runs (see README / util.py).

Bars (label -> dataset, i.e. rule directory under ``ruleEval/<bloom>/ssdeep/``):

==============  ==========================================  ===  ===========================
Label           Rules                                       mr   Notes
==============  ==========================================  ===  ===========================
APY B WF        retrained / BestKyara                       1    zero-TP clusters dropped
APY B           retrained / BestKyara                       1
APY OH: M       retrained / Heuristics/maxk                 1    red stacked part, see below
APY OH: R       retrained / Heuristics/randomK              1    red stacked part
APY OH:  Mo     retrained / Heuristics/avgk                 1    red stacked part
APY SH: M       retrained / Heuristics/BAD/Max              1    zero-TP clusters dropped
APY SH: Me      retrained / Heuristics/BAD/Mean             1    zero-TP clusters dropped
APY SH:R        retrained / Heuristics/BAD/Random           1    zero-TP clusters dropped
APY             retrained / AutoPyara                       5
APY Wk          retrained / WorstPyara                      1
AY RTBF         retrained / Autoyara                        5
APY EBF WF      original (Ember) / AutoPYaraBest            10   zero-TP clusters dropped
AY EBF WF       original (Ember) / AutoYaraBaseline         10   zero-TP clusters dropped
APY EBF         original (Ember) / AutoPYaraBest            10
AY EBF          original (Ember) / AutoYaraBaseline         10
==============  ==========================================  ===  ===========================

(APY = AutoPYara, AY = AutoYara, EBF = Ember bloom filters, RTBF / retrained =
retrained bloom filters.)

Bar height = mean of all per-cluster TP rates (in %), pooled over the thresholds;
missing values count as 0 unless the bar drops zeros. For the three ``OH`` bars, a
red stacked segment shows how much the mean rises if every cluster the heuristic
failed on (TP 0 or missing) takes the AutoPYara (``APY``) value instead.

Bars <= 84 % are drawn, sorted, on the left panel (y 0..84); bars > 84 % on the right
panel (y 84..100), like a broken axis. Five bars carry call-out annotations.

Figure written (under ``--out-dir``, default ``Plots/Figures``):
  Claim6_YaraInAllitsConfigurations/BigPicutre.pdf

Usage:
  python PlotsSet4_yaraBigPicture.py            # all CPUs
  python PlotsSet4_yaraBigPicture.py -j 8       # 8 worker processes
  python PlotsSet4_yaraBigPicture.py --help

Refactor notes (no change to data, statistics or figure content):
  * The 13 copy-pasted load loops are the table ``TASKS``. The original also loaded
    ``df_listYaraBaseRTBFF`` (retrained Autoyara, twice), which the figure never
    uses; those 10 extraction calls are dropped.
  * The unused ``tools`` import (it only set font rcParams that this script
    overrides anyway, and pulled in scipy) and the no-op ``plt.show()`` were removed.
"""
import os
import sys

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_common import script_main, threshold_tasks

# --------------------------------------------------------------------------------------
# Extraction tasks (all: SSdeep clusters, per-cluster Series). Group names = the
# original variable names.
# --------------------------------------------------------------------------------------
SSDEEP_CSV = 'clusterCSV/ssdeep/th{t}.csv'
RULES = 'ruleEval/{bloom}/ssdeep/{variant}/Th{{t}}rules/merged_group_1.yar'

DATASETS = [  # (group name, bloom-filter folder, rule directory, mr)
    ('df_listYaraBaseOGBF', 'originalBloomFilters', 'AutoYaraBaseline', 10),
    ('df_listYaraBaseRTBF', 'retrainedBloomFilters', 'Autoyara', 5),
    ('df_listPYaraBaseOGBF', 'originalBloomFilters', 'AutoPYaraBest', 10),
    ('df_listPYaraBaseRTBF', 'retrainedBloomFilters', 'AutoPyara', 5),
    ('df_listPYaraWORSTKRTBF', 'retrainedBloomFilters', 'WorstPyara', 1),
    ('df_listPYaraBESTKRTBF', 'retrainedBloomFilters', 'BestKyara', 1),
    ('df_listPYaraHeuAvg', 'retrainedBloomFilters', 'Heuristics/avgk', 1),
    ('df_listPYaraHeumaxk', 'retrainedBloomFilters', 'Heuristics/maxk', 1),
    ('df_listPYaraHeurandomK', 'retrainedBloomFilters', 'Heuristics/randomK', 1),
    ('df_listPYaraBadMax', 'retrainedBloomFilters', 'Heuristics/BAD/Max', 1),
    ('df_listPYaraBadMean', 'retrainedBloomFilters', 'Heuristics/BAD/Mean', 1),
    ('df_listPYaraBadRandom', 'retrainedBloomFilters', 'Heuristics/BAD/Random', 1),
]
TASKS = [task for group, bloom, variant, mr in DATASETS
         for task in threshold_tasks(group, SSDEEP_CSV, RULES.format(bloom=bloom, variant=variant),
                                     mr=mr, short=True)]

# --------------------------------------------------------------------------------------
# Style
# --------------------------------------------------------------------------------------
RC_PARAMS = {'text.usetex': False,  # Explicitly disable LaTeX rendering
             'font.family': 'DejaVu Sans', 'font.weight': 1000, 'font.size': 24}
AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 1000, 'size': 26}
TICK_FONT_SIZE = 24


def fill_source_from_target(source: pd.Series, target: pd.Series):
    """Copy ``target`` into the clusters where ``source`` is NaN/0 and ``target`` isn't."""
    updated_source = source.copy()
    clusters_replaced = []
    for cluster in source.index:
        src_val = source.loc[cluster]
        tgt_val = target.loc[cluster]
        if (pd.isna(src_val) or src_val == 0) and (not pd.isna(tgt_val) and tgt_val != 0):
            updated_source.loc[cluster] = tgt_val
            clusters_replaced.append(cluster)
    return updated_source, clusters_replaced


def plot_ladder_graph(
    list1, list2, list3, list4, list5, list6, list7, list8, list9, list10, list11, list12,
    list13, list14, list15,
    save_path=None
):
    """Draw the two-panel ladder chart; ``listN`` = 5 per-cluster Series (one per
    threshold) for bar N in the order of ``labels_map``. See the module docstring."""
    # --- 1. Data Preparation ---
    all_lists = [list1, list2, list3, list4, list5, list6, list7, list8, list9, list10, list11, list12, list13, list14, list15]

    labels_map = [
        "APY B WF", "APY B", "APY OH: M",
        "APY OH: R", "APY OH:  Mo",
        "APY SH: M", "APY SH: Me",
        "APY SH:R ", "APY", "APY Wk",
        "AY RTBF", "APY EBF WF", "AY EBF WF",
        "APY EBF", "AY EBF"
    ]

    base_colors = [
        '#17becf', '#1f77b4', '#2ca02c', '#2ca02c', '#2ca02c',
        '#ff7f0e', '#ff7f0e', '#ff7f0e', '#1f77b4', '#1f77b4',
        '#7f7f7f', '#17becf', '#17becf', '#1f77b4', '#7f7f7f'
    ]
    hatches = ['xx', '**', 'oo', 'oo', 'oo', 'oo', 'oo', 'oo', '**', '**', '**', 'xx', 'xx', '**', '**']

    use_flattenB = {0, 5, 6, 7, 11, 12}  # bars that drop zero-TP clusters
    stacked_indices = {2, 3, 4}          # bars with a red "filled from list9" segment

    aggregated_base_data = [[] for _ in range(15)]
    aggregated_fill_data = [[] for _ in range(15)]

    for section in range(5):
        target_series = list9[section]
        current_fill_contribs = {}
        for idx, lst_arg in zip([2,3,4], [list3, list4, list5]):
            source_series = lst_arg[section]
            _, replaced = fill_source_from_target(source_series, target_series)
            fill_contrib = pd.Series(0.0, index=source_series.index)
            for cl in replaced:
                fill_contrib.loc[cl] = target_series.loc[cl]
            current_fill_contribs[idx] = fill_contrib

        for i, lst in enumerate(all_lists):
            df = lst[section]
            values = df.values.flatten() if isinstance(df, pd.DataFrame) else df.values
            values = np.nan_to_num(values, nan=0.0)
            if i in use_flattenB:
                values = values[values != 0]
            aggregated_base_data[i].extend(values * 100)

            if i in stacked_indices:
                f_values = current_fill_contribs[i].values
                f_values = np.nan_to_num(f_values, nan=0.0)
                if i in use_flattenB:
                    f_values = f_values[f_values != 0]
                aggregated_fill_data[i].extend(f_values * 100)

    plot_items = []
    for i in range(15):
        base_arr = np.array(aggregated_base_data[i])
        base_mean = np.mean(base_arr) if len(base_arr) > 0 else 0.0
        fill_mean = np.mean(aggregated_fill_data[i]) if (i in stacked_indices and len(aggregated_fill_data[i]) > 0) else 0.0

        plot_items.append({
            'label': labels_map[i],
            'base_mean': base_mean,
            'fill_mean': fill_mean,
            'total_height': base_mean + fill_mean,
            'color': base_colors[i],
            'hatch': hatches[i]
        })

    # --- 2. Grouping Logic ---
    split_point = 84

    group_low = [x for x in plot_items if x['total_height'] <= split_point]
    group_high = [x for x in plot_items if x['total_height'] > split_point]

    group_low.sort(key=lambda x: x['total_height'])
    group_high.sort(key=lambda x: x['total_height'])

    # --- 3. Plotting ---
    counts = [len(group_low), len(group_high)]
    width_ratios = [c if c > 0 else 1 for c in counts]

    fig = plt.figure(figsize=(17, 12), dpi=600)
    gs = gridspec.GridSpec(1, 2, width_ratios=width_ratios, wspace=0.15)

    ax1 = plt.subplot(gs[0])
    ax2 = plt.subplot(gs[1])

    bar_width = 0.8

    def plot_group(ax, items, y_min, y_max, is_left=False):
        if not items:
            ax.axis('off')
            return

        x_pos = np.arange(len(items))
        bases = [x['base_mean'] for x in items]
        fills = [x['fill_mean'] for x in items]
        colors = [x['color'] for x in items]
        hatches_local = [x['hatch'] for x in items]
        labels = [x['label'] for x in items]

        bars = ax.bar(x_pos, bases, width=bar_width, color=colors, edgecolor='black', linewidth=1.5)
        for bar, h in zip(bars, hatches_local):
            bar.set_hatch(h)

        for i, f_val in enumerate(fills):
            if f_val > 0:
                ax.bar(x_pos[i], f_val, width=bar_width, bottom=bases[i],
                       color='#FF0000', edgecolor='black', linewidth=1.5, hatch=hatches_local[i] + '/')

        ax.set_ylim(y_min, y_max)
        ax.set_xticks(x_pos)

        short_labels = [l.replace('AutoPYara', 'AP').replace('AutoYara', 'AY').replace('Unrealistic', 'Unr.') for l in labels]
        ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=20, fontweight='bold')
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)

        if is_left:
            ax.spines['right'].set_visible(True)
            ax.set_ylabel("True Positive Rate (%) -->", **AXIS_FONT, labelpad=15)
        else:
            ax.spines['left'].set_visible(True)
            ax.spines['left'].set_linewidth(1.5)
            ax.yaxis.tick_left()

            ticks = np.arange(int(y_min), int(y_max) + 1, 2)
            ax.set_yticks(ticks)

        ax.tick_params(axis='y', labelsize=TICK_FONT_SIZE, length=6, width=1.5)
        for label in ax.get_yticklabels():
            label.set_fontweight('bold')

    # Plot Groups
    plot_group(ax1, group_low, 0, 84, is_left=True)
    plot_group(ax2, group_high, 84, 100, is_left=False)

    # Titles
    ax1.text(0.5, 1.02, "",transform=ax1.transAxes, ha='center', fontsize=22, fontweight='bold')
    ax2.text(0.5, 1.02, "",transform=ax2.transAxes, ha='center', fontsize=22, fontweight='bold')

    # Diagonal Cuts
    d = .015
    kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False, linewidth=1.5)

    ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs)
    ax1.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

    # --- 4. Annotations ---
    # 'y_offset' / 'x_offset' move the text box only; the arrow always points at the bar.
    annotations_req = [
        {
            "target_labels": ["APY B WF"],
            "text": "AutoPYara\nBest k\nIdeal Case",
            "y_offset": .5,

        },
        {
            "target_labels": ["APY B"],
            "text": "AutoPYara\nBest k",
            "y_offset": -1,
            "x_offset": -0.5,

        },
        {
            "target_labels": ["APY OH: M"],
            "text": "AutoPYara\nReality",
            "x_offset": -1.2,
            "y_offset": -1.5
        },
        {
            "target_labels": ["AY RTBF"],
            "text": "AutoYara\nConfigured",
            "x_offset": -0.5
        },
        {
            "target_labels": ["AY EBF"],
            "text": "AutoYara\nReality"
        }
    ]

    def add_annotation(ax, group_items, targets, text, y_offset=0, x_offset=0):
        # Find indices of bars belonging to target labels
        indices = [i for i, item in enumerate(group_items) if item['label'] in targets]
        if not indices:
            return

        # True bar center (DO NOT OFFSET)
        min_idx = min(indices)
        max_idx = max(indices)
        arrow_x = (min_idx + max_idx) / 2

        # Text position (OFFSET ALLOWED)
        text_x = arrow_x + x_offset

        # Max bar height
        max_h = max(group_items[i]['total_height'] for i in indices)

        # Y scaling
        y_min, y_max = ax.get_ylim()
        y_range = y_max - y_min

        # Text Y position
        text_y = max_h + (y_range * 0.15) + y_offset
        if text_y > y_max:
            text_y = y_max - (y_range * 0.02)

        ax.annotate(
            text,
            xy=(arrow_x, max_h),          # <-- ALWAYS bar center
            xycoords='data',
            xytext=(text_x, text_y),      # <-- offset text only
            textcoords='data',
            arrowprops=dict(
                arrowstyle="->",
                color='black',
                lw=2.5,
                connectionstyle="arc3,rad=0.2"
            ),
            ha='center',
            va='bottom',
            fontsize=20,
            fontweight='bold',
            color='black',
            bbox=dict(
                boxstyle="round,pad=0.4",
                fc="white",
                ec="black",
                lw=2
            )
        )

    # Apply annotations (each lands on whichever panel holds its bar)
    for req in annotations_req:
        add_annotation(
            ax1,
            group_low,
            req['target_labels'],
            req['text'],
            y_offset=req.get('y_offset', 0),
            x_offset=req.get('x_offset', 0)
        )

        add_annotation(
            ax2,
            group_high,
            req['target_labels'],
            req['text'],
            y_offset=req.get('y_offset', 0),
            x_offset=req.get('x_offset', 0)
        )

    # Save
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=600)


def make_figures(d, out_dir):
    """Draw the ladder chart from ``d`` = {group name: [5 per-cluster Series]}."""
    plt.rcParams.update(RC_PARAMS)
    path = os.path.join(out_dir, 'Claim6_YaraInAllitsConfigurations/BigPicutre.pdf')
    plot_ladder_graph(
        d['df_listPYaraBESTKRTBF'], d['df_listPYaraBESTKRTBF'], d['df_listPYaraHeumaxk'],
        d['df_listPYaraHeurandomK'], d['df_listPYaraHeuAvg'], d['df_listPYaraBadMax'],
        d['df_listPYaraBadMean'], d['df_listPYaraBadRandom'], d['df_listPYaraBaseRTBF'],
        d['df_listPYaraWORSTKRTBF'], d['df_listYaraBaseRTBF'],
        d['df_listPYaraBaseOGBF'], d['df_listYaraBaseOGBF'], d['df_listPYaraBaseOGBF'], d['df_listYaraBaseOGBF'],
        save_path=path
    )
    plt.close('all')
    return [path]


if __name__ == '__main__':
    sys.exit(script_main('Figure set 4 (Claim 6): all configurations in one ladder chart. '
                         'See module docstring.', TASKS, make_figures))
