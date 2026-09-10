# Plots — paper figures from the provided YARA rules

This directory regenerates all 15 figures behind the paper's Claims 1–4. You do not
need to generate any rules. The rule sets are provided under `data/ruleEval/`, and each
rule carries a comment with its measured true-positive (TP) rate. These scripts
parse those comments, aggregate them per cluster, and plot the results.

## Quick start

```bash
cd Plots
pip install numpy pandas matplotlib tqdm
python run_all_plots.py --dry-run    # check that all 94 extraction tasks find their inputs
python run_all_plots.py -j 8         # generate every figure with 8 worker processes
```

The figures are written to `Plots/Figures/` (see [Figures](#figures)).

Tested with Python 3.13.5, numpy 1.26.4, pandas 2.2.3, matplotlib 3.10.0 and tqdm 4.67.1.

## Files

| File | Role |
|---|---|
| `run_all_plots.py` | Master runner. Runs both figure scripts, each in its own process, and prints a summary. |
| `PlotsSet1_Boxplots.py` | Figure set 1 (Claims 1–3): mean TP-rate bar charts. |
| `PlotsSet2_ThresholdPlots.py` | Figure set 2 (Claim 4): TP rate vs. cluster size, one line per similarity threshold. |
| `plot_common.py` | Code shared by the two scripts: parallel extraction, input preflight check, command-line options. |
| `util.py` | Parses the rule files and CSVs (`Extractor`, `rules_to_dataframe`, `ensure_columns`, ...). |
| `tools.py` | Older plotting helpers. The scripts above don't use it. |

## Options

```text
python run_all_plots.py [-j N] [--only set1 set2] [--data-dir DIR] [--out-dir DIR]
                        [-q] [--log-dir DIR] [--dry-run]
```

| Option | Default | Meaning |
|---|---|---|
| `-j N`, `--jobs N`, `--cores N` | `0` (all CPUs) | Worker processes per script. Use `1` for a fully sequential run. |
| `--only set1 set2` | both | Run only the listed figure sets. |
| `--data-dir DIR` | `../data` (next to `Plots/`) | Root directory that holds `clusterCSV/` and `ruleEval/`. |
| `--out-dir DIR` | `Plots/Figures` | Where the `Claim*/` folders are written. |
| `-q`, `--quiet` | off | Hide `util.py`'s per-file and per-rule diagnostic prints. |
| `--log-dir DIR` | off | Send each script's full output to `DIR/<script>.log` instead of the terminal. |
| `--dry-run` | off | List the inputs, report any missing file, and exit without plotting. |

Each figure script also runs on its own with the same `-j`, `--data-dir`, `--out-dir`,
`-q` and `--dry-run` options:

```bash
python PlotsSet2_ThresholdPlots.py -j 4
```

Default paths are resolved relative to this directory, so the commands work from any
working directory.

## Figures

All paths are relative to `--out-dir`.

| Figure | Claim | Contents | Script |
|---|---|---|---|
| `Claim1_IncorrectBaseLines/AutoYara_baselineBoxPlotEMBF.pdf` | 1 | AutoYara with Ember bloom filters; clusters with TP = 0 excluded | Set 1 |
| `Claim1_IncorrectBaseLines/AutoYara_EMBF.pdf` | 1 | Same, clusters with TP = 0 included | Set 1 |
| `Claim2_BloomFiltersMatter/AutoYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf` | 2 | AutoYara: Ember (light) vs. retrained (dark) bloom filters | Set 1 |
| `Claim2_BloomFiltersMatter/AutoPYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf` | 2 | AutoPYara: retrained (light) vs. Ember (dark) bloom filters | Set 1 |
| `Claim3_YaraVsPYara/AutoYaraVSAutoPYaraRTBF.pdf` | 3 | Retrained filters: AutoPYara (light) vs. AutoYara (dark) | Set 1 |
| `Claim4_ThresHoldFigures/AutoYara_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoYara | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYara_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoPYara | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraBestK_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoPYara, best K | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraWorstK_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoPYara, worst K | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraHEUModeK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Informed heuristic: mode/average K | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraHEUMaxK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Informed heuristic: max K | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraHEURandomK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Informed heuristic: random K | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraUninformedHEUMeanK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Uninformed heuristic: mean K | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraUninformedHEUMaxK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Uninformed heuristic: max K | Set 2 |
| `Claim4_ThresHoldFigures/AutoPYaraUninformedHEURandomK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Uninformed heuristic: random K | Set 2 |

Each Set 1 chart has one bar group per clustering: SSdeep, J-SDhash (sdhash) and
VirusTotal. Each Set 2 figure uses the SSdeep clusterings and rules built with the
retrained bloom filters.

## Input data

The scripts read 11 clustering CSVs and 84 merged rule files, about 2.1 GB in total. Directory
names must match the casing below exactly (for example `Autoyara` vs. `AutoYara`).
Run `--dry-run` to list every file.

```text
data/
├── clusterCSV/
│   ├── sdhash/Th{50,60,70,80,90}.csv
│   ├── ssdeep/th{50,60,70,80,90}.csv
│   └── virusTotal/MainVtCluster.csv
└── ruleEval/
    ├── originalBloomFilters/                 # "Ember" bloom filters
    │   ├── sdhash/{AutoYara,AutoPYara}/Th<t>rules/merged_group_1.yar
    │   ├── ssdeep/{AutoYaraBaseline,AutoPYaraBest}/Th<t>rules/merged_group_1.yar
    │   └── virusTotal/{AutoyaraBaseline/VirusTotal,AutoPYara}/merged_group_1.yar
    └── retrainedBloomFilters/                # bloom filters retrained on our data
        ├── sdhash/{AutoYara,AutoPYara}/Th<t>rules/merged_group_1.yar
        ├── ssdeep/<variant>/Th<t>rules/merged_group_1.yar
        │     variant ∈ Autoyara, AutoPyara, BestKyara, WorstPyara,
        │               Heuristics/{avgk,maxk,randomK}, Heuristics/BAD/{Mean,Max,Random}
        └── virusTotal/{AutoYara,AutoPYara}/merged_group_1.yar
```

- **CSV:** only the `Cluster_Label` column is used. Labels below 0 (noise) and empty
  labels are ignored.
- **Rules:** each rule is named `Cluster<i>_<run>` and carries a comment
  `// Input TP Rate: X/Y` (the shorter form `//X/Y` also works).

## How the numbers are computed

1. **Per rule:** TP rate = X / Y from the comment. A rule with no comment, or with
   Y = 0, counts as 0.
2. **Per cluster** (`util.Extractor`): the mean over runs `1..mr`.
   - If a run is missing for some clusters, it is filled with that run's median over all clusters.
   - If a run is missing for every cluster, it counts as 0.
   - Clusters in the CSV with at least 2 members but no rules count as 0.
   - Rule cluster `i` is matched to CSV label `i`.
   - `mr` is 10 for Ember rule sets, 5 for retrained and VirusTotal rule sets, and 1 in Set 2.
3. **Set 1 (bars):** per-cluster values are pooled over the five thresholds (VirusTotal
   has a single clustering). The bar shows the mean, the error bar the population
   standard deviation, both in %.
4. **Set 2 (lines):** for each threshold, the scripts take the median TP rate of the clusters of
   each size, then plot the running mean of these medians as cluster size increases.
   - The x-axis is the rank of the cluster size, not a linear scale. The tick labels 0/25/50/75/100/500 mark the nearest existing size.
   - The dotted line shows the mean of each curve.
   - The y-axis is zoomed to 50–100 %.
   - For the three informed-heuristic datasets, TP = 0 is treated as missing.

## Performance and memory

Parsing the rule files is the slow part. It is spread over `-j` worker processes, and
the results are put back in their original order before plotting, so every `-j` value
produces the same figures. Plotting runs sequentially in the main process.

Measured on a 12-CPU server with the full dataset:

| Version | Wall time |
|---|---|
| Scripts before this refactor (single core) | ~32 min (Set 1: 7.6 min, Set 2: 24.2 min) |
| `run_all_plots.py -j 8` | 23 s |

The single-process runs peaked at 0.5–0.6 GB of RSS. A worker handles one rule file at a time
(the largest is about 95 MB on disk), so budget roughly that much per worker and lower `-j` on
machines with little memory.

## Reproducibility

- **Refactor check:** on the full dataset, all 15 PDFs are byte-identical to the output of the
  scripts before this refactor, apart from the embedded creation date. The refactor
  changes no data, statistics or figure content.
- **Byte-identical reruns:** a PDF normally embeds its creation time. For byte-identical
  PDFs across runs, set a fixed timestamp:

  ```bash
  SOURCE_DATE_EPOCH=0 python run_all_plots.py -j 8
  ```

## Notes and known quirks

These quirks are deliberate: fixing any of them would change the published figures.

- **Parser skips a rule on the first line.** `util.extract_rule_tp_rates` splits a file at
  each newline followed by `rule`. If a `.yar` file starts directly with `rule` (no header
  line before it), the parser skips that first rule.
- **`nans` flag refers to zeros.** In Set 1, `nans=True` keeps clusters with TP = 0;
  `nans=False` drops them. Missing values are always dropped.
- **Misleading function name.** `plot_cluster_std_dev_boxplot_static_all_merge_zoom`
  draws line plots, not boxplots. The name is historical.
- **Set 1 font size.** Set 1's charts render with font size 28. The original script
  defined the font settings twice, and the second set is the one in effect.
