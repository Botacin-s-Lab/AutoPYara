
import sys
import os
import matplotlib.pyplot as plt

import pandas as pd
from util import (
    Extractor,
    rules_to_dataframe)
from tqdm import tqdm


## AutoYara Ember Bloom
csv_files = [
    '../data/clusterCSV/sdhash/Th50.csv',
    '../data/clusterCSV/sdhash/Th60.csv',
    '../data/clusterCSV/sdhash/Th70.csv',
    '../data/clusterCSV/sdhash/Th80.csv',
    '../data/clusterCSV/sdhash/Th90.csv'
]

yara_files = [
    '../data/ruleEval/originalBloomFilters/sdhash/AutoYara/Th50rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoYara/Th60rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoYara/Th70rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoYara/Th80rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoYara/Th90rules/merged_group_1.yar'

]

df_listSdhash = []
mr=[10,10,10,10,10]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSdhash.append(df)


csv_files = [
    '../data/clusterCSV/ssdeep/th50.csv',
    '../data/clusterCSV/ssdeep/th60.csv',
    '../data/clusterCSV/ssdeep/th70.csv',
    '../data/clusterCSV/ssdeep/th80.csv',
    '../data/clusterCSV/ssdeep/th90.csv'
]

yara_files = [
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoYaraBaseline/Th50rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoYaraBaseline/Th60rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoYaraBaseline/Th70rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoYaraBaseline/Th80rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoYaraBaseline/Th90rules/merged_group_1.yar'

]


df_listSSdeep = []
mr=[10,10,10,10,10]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSSdeep.append(df)


csv_files = [
    '../data/clusterCSV/virusTotal/MainVtCluster.csv',
]

yara_files = [
    '../data/ruleEval/originalBloomFilters/virusTotal/AutoyaraBaseline/VirusTotal/merged_group_1.yar',
]

df_listVT = []
mr=[5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listVT.append(df)


## AutoYara Retrain Bloom

csv_files = [
    '../data/clusterCSV/sdhash/Th50.csv',
    '../data/clusterCSV/sdhash/Th60.csv',
    '../data/clusterCSV/sdhash/Th70.csv',
    '../data/clusterCSV/sdhash/Th80.csv',
    '../data/clusterCSV/sdhash/Th90.csv'
]

yara_files = [
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoYara/Th50rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoYara/Th60rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoYara/Th70rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoYara/Th80rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoYara/Th90rules/merged_group_1.yar'

]

df_listSdhashRTBF = []
mr=[5,5,5,5,5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSdhashRTBF.append(df)


csv_files = [
    '../data/clusterCSV/ssdeep/th50.csv',
    '../data/clusterCSV/ssdeep/th60.csv',
    '../data/clusterCSV/ssdeep/th70.csv',
    '../data/clusterCSV/ssdeep/th80.csv',
    '../data/clusterCSV/ssdeep/th90.csv'
]

yara_files = [
    '../data/ruleEval/retrainedBloomFilters/ssdeep/Autoyara/Th50rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/Autoyara/Th60rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/Autoyara/Th70rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/Autoyara/Th80rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/Autoyara/Th90rules/merged_group_1.yar'

]


df_listSSdeepRTBF = []
mr=[5,5,5,5,5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSSdeepRTBF.append(df)


csv_files = [
    '../data/clusterCSV/virusTotal/MainVtCluster.csv',
]

yara_files = [
    '../data/ruleEval/retrainedBloomFilters/virusTotal/AutoYara/merged_group_1.yar',
]

df_listVTRTBF = []
mr=[5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listVTRTBF.append(df)

## AutoPYara Ember Bloom



from tqdm import tqdm
csv_files = [
    '../data/clusterCSV/sdhash/Th50.csv',
    '../data/clusterCSV/sdhash/Th60.csv',
    '../data/clusterCSV/sdhash/Th70.csv',
    '../data/clusterCSV/sdhash/Th80.csv',
    '../data/clusterCSV/sdhash/Th90.csv'
]

yara_files = [
    '../data/ruleEval/originalBloomFilters/sdhash/AutoPYara/Th50rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoPYara/Th60rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoPYara/Th70rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoPYara/Th80rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/sdhash/AutoPYara/Th90rules/merged_group_1.yar'

]

df_listSdhashPyara = []
mr=[10,10,10,10,10]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSdhashPyara.append(df)


csv_files = [
    '../data/clusterCSV/ssdeep/th50.csv',
    '../data/clusterCSV/ssdeep/th60.csv',
    '../data/clusterCSV/ssdeep/th70.csv',
    '../data/clusterCSV/ssdeep/th80.csv',
    '../data/clusterCSV/ssdeep/th90.csv'
]

yara_files = [
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoPYaraBest/Th50rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoPYaraBest/Th60rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoPYaraBest/Th70rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoPYaraBest/Th80rules/merged_group_1.yar',
    '../data/ruleEval/originalBloomFilters/ssdeep/AutoPYaraBest/Th90rules/merged_group_1.yar'

]


df_listSSdeepPyara = []
mr=[10,10,10,10,10]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSSdeepPyara.append(df)


csv_files = [
    '../data/clusterCSV/virusTotal/MainVtCluster.csv',
]

yara_files = [
    '../data/ruleEval/originalBloomFilters/virusTotal/AutoPYara/merged_group_1.yar',
]

df_listVTPyara = []
mr=[5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listVTPyara.append(df)


## AutoPYara Retrained Bloom

csv_files = [
    '../data/clusterCSV/sdhash/Th50.csv',
    '../data/clusterCSV/sdhash/Th60.csv',
    '../data/clusterCSV/sdhash/Th70.csv',
    '../data/clusterCSV/sdhash/Th80.csv',
    '../data/clusterCSV/sdhash/Th90.csv'
]

yara_files = [
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoPYara/Th50rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoPYara/Th60rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoPYara/Th70rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoPYara/Th80rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/sdhash/AutoPYara/Th90rules/merged_group_1.yar'

]

df_listSdhashPyaraRTBF = []
mr=[5,5,5,5,5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSdhashPyaraRTBF.append(df)


csv_files = [
    '../data/clusterCSV/ssdeep/th50.csv',
    '../data/clusterCSV/ssdeep/th60.csv',
    '../data/clusterCSV/ssdeep/th70.csv',
    '../data/clusterCSV/ssdeep/th80.csv',
    '../data/clusterCSV/ssdeep/th90.csv'
]

yara_files = [
    '../data/ruleEval/retrainedBloomFilters/ssdeep/AutoPyara/Th50rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/AutoPyara/Th60rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/AutoPyara/Th70rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/AutoPyara/Th80rules/merged_group_1.yar',
    '../data/ruleEval/retrainedBloomFilters/ssdeep/AutoPyara/Th90rules/merged_group_1.yar'

]


df_listSSdeepPyaraRTBF = []
mr=[5,5,5,5,5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listSSdeepPyaraRTBF.append(df)


csv_files = [
    '../data/clusterCSV/virusTotal/MainVtCluster.csv',
]

yara_files = [
    '../data/ruleEval/retrainedBloomFilters/virusTotal/AutoPYara/merged_group_1.yar',
]

df_listVTPyaraRTBF = []
mr=[5]
for csv_file, yara_file,mr in tqdm(zip(csv_files, yara_files,mr)):
    print(mr)
    df = Extractor(csv_file,yara_file,mr=mr,short=True)
    df_listVTPyaraRTBF.append(df)



import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.weight'] = 600
plt.rcParams['font.size'] = 16

AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 22}
TICK_FONT_SIZE = 22
def plot_bar_with_colored_textures_left_labels(list1, list2, list3, labels=("List 1", "List 2", "List 3"),nans=True, save_path=None):
    def combine_and_flatten(df_list,nans):
        combined = pd.concat(df_list, axis=1)
        values = combined.values.flatten()
        if nans:
            return values[~pd.isna(values)]  # Remove NaNs and zeros
        else:
            return values[~pd.isna(values) & (values != 0)]  # Remove NaNs and zeros
            
        
    data1 = combine_and_flatten(list1,nans)
    data2 = combine_and_flatten(list2,nans)
    data3 = combine_and_flatten(list3,nans)

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



import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.patches import Patch

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.weight'] = 600
plt.rcParams['font.size'] = 28

AXIS_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 28}
TITLE_FONT = {'family': 'DejaVu Sans', 'weight': 600, 'size': 28}
TICK_FONT_SIZE = 28
def plot_side_by_side_bar_with_textures(
    list1, list2, list3, list4, list5, list6,
    labels=("SSdeep", "J-SDhash", "VirusTotal"),head1='',head2='',
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

    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)

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



# Example usage
plot_bar_with_colored_textures_left_labels(
    df_listSSdeep,
    df_listSdhash,
    df_listVT,
    labels=("SSdeep", "J-SDhash", "VirusTotal"),nans=False,
    save_path="Figures/Claim1_IncorrectBaseLines/AutoYara_baselineBoxPlotEMBF.pdf"
)

# Example usage
plot_bar_with_colored_textures_left_labels(
    df_listSSdeep,
    df_listSdhash,
    df_listVT,
    labels=("SSdeep", "J-SDhash", "VirusTotal"),nans=True,
    save_path="Figures/Claim1_IncorrectBaseLines/AutoYara_EMBF.pdf"
)

plot_side_by_side_bar_with_textures(
     df_listSSdeep, df_listSdhash, df_listVT,df_listSSdeepRTBF, df_listSdhashRTBF, df_listVTRTBF,
    labels=("SSdeep", "J-SDhash", "VirusTotal"),head1='Ember Bloom Filters',head2='Retrained Bloom Filters',
    save_path="Figures/Claim2_BloomFiltersMatter/AutoYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf"
)

plot_side_by_side_bar_with_textures(
    df_listSSdeepPyaraRTBF , df_listSdhashPyaraRTBF,df_listVTPyaraRTBF,df_listSSdeepRTBF, df_listSdhashRTBF, df_listVTRTBF, 
    labels=("SSdeep", "J-SDhash", "VirusTotal"),head1='AutoPYara',head2='AutoYara',
    save_path="Figures/Claim3_YaraVsPYara/AutoYaraVSAutoPYaraRTBF.pdf"
)


plot_side_by_side_bar_with_textures(
    df_listSSdeepPyaraRTBF , df_listSdhashPyaraRTBF,df_listVTPyaraRTBF,df_listSSdeepPyara , df_listSdhashPyara,df_listVTPyara,
    labels=("SSdeep", "J-SDhash", "VirusTotal"),head1='Retrained Bloom Filters',head2='Ember Bloom Filters',
    save_path="Figures/Claim2_BloomFiltersMatter/AutoPYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf"
)