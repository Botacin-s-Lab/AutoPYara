# artifact/plots — the paper's figures and claim checks

This directory regenerates all 18 figures behind the paper's claims 1–6 (artifact
claims 4–9) from the evaluation data, and checks each claim against the regenerated
numbers. No rules are generated here. The rule sets are provided under
`data/ruleEval/`, each rule carrying a comment with its measured true-positive (TP)
rate, and the threat-hunting results are provided under `data/ThreatHunting/`. The
scripts parse those results, aggregate them per cluster, and plot them.

## Quick start

From the repository root, after `./install.sh` (which creates `.venv` and fetches
the data into `data/`):

```bash
.venv/bin/python artifact/plots/run_all_plots.py --dry-run   # check that all 164 extraction tasks find their inputs
.venv/bin/python artifact/plots/run_all_plots.py -j 8        # regenerate all 18 figures with 8 worker processes
```

The figures are written to `results/figures/` (see [Figures](#figures)), next to
one `<script>.values.json` per script with every plotted number.

To check one paper claim the way the AEC does, use its claim script, for example
`claims/claim4_incorrect_baselines/run.sh -j 8`. That runs
`verify_claims.py 4`, which regenerates the figures, compares them with the
reference, and checks the claim's statements.

## Files

| File | Role |
|---|---|
| `run_all_plots.py` | Master runner. Runs the four figure scripts, each in its own process, and prints a summary. |
| `PlotsSet1_Boxplots.py` | Figure set 1 (paper claims 1–3): mean TP-rate bar charts. |
| `PlotsSet2_ThresholdPlots.py` | Figure set 2 (paper claim 4): TP rate vs. cluster size, one line per similarity threshold. |
| `PlotsSet3_ThreatHunting.py` | Figure set 3 (paper claim 5): threat hunting, TP rate on training vs. held-out test samples. |
| `PlotsSet4_yaraBigPicture.py` | Figure set 4 (paper claim 6): all AutoYara/AutoPYara configurations ranked in one chart. |
| `verify_claims.py` | Checks one artifact claim (4–9): regenerate, compare with `claims/claimN_*/expected/`, check the statements. |
| `plot_common.py` | Code shared by the scripts: parallel extraction, input preflight check, recording of plotted numbers, command-line options. |
| `util.py` | Parses the rule files and CSVs (`Extractor`, `rules_to_dataframe`, `ensure_columns`, ...). |
| `tools.py` | Older plotting helpers. The scripts above don't use it. |

## Options

```text
run_all_plots.py [-j N] [--only set1 set2 set3 set4] [--data-dir DIR] [--out-dir DIR]
                 [-q] [--log-dir DIR] [--dry-run]
```

| Option | Default | Meaning |
|---|---|---|
| `-j N`, `--jobs N`, `--cores N` | `0` (all CPUs) | Worker processes per script. Use `1` for a fully sequential run. |
| `--only set1 ...` | all four | Run only the listed figure sets. |
| `--data-dir DIR` | `<repo>/data`, or `$AUTOPYARA_DATA_DIR` | Root directory that holds `clusterCSV/`, `ruleEval/` and `ThreatHunting/`. |
| `--out-dir DIR` | `<repo>/results/figures` | Where the `Claim*/` folders and the `*.values.json` files are written. |
| `-q`, `--quiet` | off | Hide the per-file and per-rule diagnostic prints. |
| `--log-dir DIR` | off | Send each script's full output to `DIR/<script>.log` instead of the terminal. |
| `--dry-run` | off | List the inputs, report any missing file, and exit without plotting. |

Each figure script also runs on its own with the same `-j`, `--data-dir`, `--out-dir`,
`-q` and `--dry-run` options, for example
`.venv/bin/python artifact/plots/PlotsSet2_ThresholdPlots.py -j 4`.

## Figures

All paths are relative to `--out-dir`. The folder names carry the paper's claim
numbers; the artifact claim that checks them is in the last column.

| Figure | Paper claim | Contents | Script | Artifact claim |
|---|---|---|---|---|
| `Claim1_IncorrectBaseLines/AutoYara_baselineBoxPlotEMBF.pdf` | 1 | AutoYara with Ember bloom filters; clusters with TP = 0 excluded | Set 1 | 4 |
| `Claim1_IncorrectBaseLines/AutoYara_EMBF.pdf` | 1 | Same, clusters with TP = 0 included | Set 1 | 4 |
| `Claim2_BloomFiltersMatter/AutoYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf` | 2 | AutoYara: Ember (light) vs. retrained (dark) bloom filters | Set 1 | 5 |
| `Claim2_BloomFiltersMatter/AutoPYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf` | 2 | AutoPYara: retrained (light) vs. Ember (dark) bloom filters | Set 1 | 5 |
| `Claim3_YaraVsPYara/AutoYaraVSAutoPYaraRTBF.pdf` | 3 | Retrained filters: AutoPYara (light) vs. AutoYara (dark) | Set 1 | 6 |
| `Claim4_ThresHoldFigures/AutoYara_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoYara | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYara_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoPYara | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraBestK_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoPYara, best K | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraWorstK_SSdeepAVG_ZoomRTBF.pdf` | 4 | AutoPYara, worst K | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraHEUModeK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Informed heuristic: mode/average K | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraHEUMaxK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Informed heuristic: max K | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraHEURandomK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Informed heuristic: random K | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraUninformedHEUMeanK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Uninformed heuristic: mean K | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraUninformedHEUMaxK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Uninformed heuristic: max K | Set 2 | 7 |
| `Claim4_ThresHoldFigures/AutoPYaraUninformedHEURandomK_SSdeepAVG_ZoomRTBF.pdf` | 4 | Uninformed heuristic: random K | Set 2 | 7 |
| `Claim5_Threathunting/sdhash_WithHeuOnly_IdealPlot.pdf` | 5 | Threat hunting (`IdealStream_HEU`): train (left) vs. test (right), AutoPYara vs. AutoYara | Set 3 | 8 |
| `Claim5_Threathunting/sdhash_WithNOHeuOnly_IdealPlot.pdf` | 5 | Same for `NonIdealStream_RDM` | Set 3 | 8 |
| `Claim5_Threathunting/sdhash_RealWorldStream_PHeuPlot.pdf` | 5 | Same for `RealWorldStream_PHeu` | Set 3 | 8 |
| `Claim6_YaraInAllitsConfigurations/BigPicutre.pdf` | 6 | Mean TP rate of 15 AutoYara/AutoPYara configurations, ranked | Set 4 | 9 |

Each Set 1 chart has one bar group per clustering: SSdeep, J-SDhash (sdhash) and
VirusTotal. Sets 2 and 4 use the SSdeep clusterings; Set 3 uses the sdhash
threat-hunting experiments.

## Input data

The scripts read 11 clustering CSVs, 84 merged rule files (about 2.1 GB in total) and
15 threat-hunting result folders. `artifact/download_data.py` fetches them into
`data/`. Directory names must match the casing below exactly (for example
`Autoyara` vs. `AutoYara`). Run `--dry-run` to list every input.

```text
data/
├── clusterCSV/
│   ├── sdhash/Th{50,60,70,80,90}.csv
│   ├── ssdeep/th{50,60,70,80,90}.csv
│   └── virusTotal/MainVtCluster.csv
├── ruleEval/
│   ├── originalBloomFilters/                 # "Ember" bloom filters
│   │   ├── sdhash/{AutoYara,AutoPYara}/Th<t>rules/merged_group_1.yar
│   │   ├── ssdeep/{AutoYaraBaseline,AutoPYaraBest}/Th<t>rules/merged_group_1.yar
│   │   └── virusTotal/{AutoyaraBaseline/VirusTotal,AutoPYara}/merged_group_1.yar
│   └── retrainedBloomFilters/                # bloom filters retrained on our data
│       ├── sdhash/{AutoYara,AutoPYara}/Th<t>rules/merged_group_1.yar
│       ├── ssdeep/<variant>/Th<t>rules/merged_group_1.yar
│       │     variant ∈ Autoyara, AutoPyara, BestKyara, WorstPyara,
│       │               Heuristics/{avgk,maxk,randomK}, Heuristics/BAD/{Mean,Max,Random}
│       └── virusTotal/{AutoYara,AutoPYara}/merged_group_1.yar
└── ThreatHunting/
    └── {IdealStream_HEU,NonIdealStream_RDM,RealWorldStream_PHeu}/Th<t>/Ratio_0.75/cluster_<n>/
          train_files.txt, test_files.txt, tprate{AutoPYara,AutoyaraBase}_{Train,Test}.txt
```

- **CSV:** only the `Cluster_Label` column is used. Labels below 0 (noise) and empty
  labels are ignored.
- **Rules:** each rule is named `Cluster<i>_<run>` and carries a comment
  `// Input TP Rate: X/Y` (the shorter form `//X/Y` also works).
- **Threat hunting:** each `tprate*.txt` holds a line such as `TP Rate: 0.4737 (9/19)`.
  A cluster folder is used only if all six files are present.

## How the numbers are computed

1. **Per rule:** TP rate = X / Y from the comment. A rule with no comment, or with
   Y = 0, counts as 0.
2. **Per cluster** (`util.Extractor`, Sets 1, 2 and 4): the mean over runs `1..mr`.
   - If a run is missing for some clusters, it is filled with that run's median over all clusters.
   - If a run is missing for every cluster, it counts as 0.
   - Clusters in the CSV with at least 2 members but no rules count as 0.
   - Rule cluster `i` is matched to CSV label `i`.
   - `mr` is 10 for Ember rule sets, 5 for retrained and VirusTotal rule sets, and 1 for
     the best/worst-K and heuristic rule sets.
3. **Set 1 (bars):** per-cluster values are pooled over the five thresholds (VirusTotal
   has a single clustering). The bar shows the mean, the error bar the population
   standard deviation, both in %.
4. **Set 2 (lines):** for each threshold, the scripts take the median TP rate of the clusters of
   each size, then plot the running mean of these medians as cluster size increases.
   - The x-axis is the rank of the cluster size, not a linear scale. The tick labels 0/25/50/75/100/500 mark the nearest existing size.
   - The dotted line shows the mean of each curve.
   - The y-axis is zoomed to 50–100 %.
   - For the three informed-heuristic datasets, TP = 0 is treated as missing.
5. **Set 3 (mirrored lines):** the five thresholds are pooled. Cluster size is the number
   of samples a rule was evaluated on (the `19` in `9/19`). The chart shows the running
   mean of per-size median TP rates, with training samples on the left and held-out
   test samples on the right; sizes with a median of 0 are skipped.
6. **Set 4 (ladder chart):** each bar is the mean of all per-cluster TP rates, pooled over
   the five thresholds. Bars marked "WF" drop clusters with TP = 0. For the three
   heuristic bars, a red segment shows how much the mean rises if every cluster the
   heuristic failed on takes AutoPYara's value instead. Bars at or below 84 % go on the
   left panel (0–84 %), the rest on the right panel (84–100 %). The module docstring of
   `PlotsSet4_yaraBigPicture.py` maps every bar label to its rule set.

## Recorded values and claim checks

Just before each figure is saved, `plot_common` reads back what the figure draws.
This is read-only: the PDFs are byte-identical with or without it. It stores the
numbers in `<out-dir>/<script>.values.json`, keyed by figure path. For each panel it records:

- `bars`: every bar series (centres, bottoms, heights, error-bar half-lengths);
- `lines`: every curve and reference line (colour, x and y data);
- `xticks`: the bar names;
- `texts`: the annotations.

`verify_claims.py N` compares these numbers with `claims/claimN_*/expected/values.json`
(tolerance 1.0 percentage point) and evaluates the claim's statements on them. The
reference files were produced with `verify_claims.py N --update-expected --from DIR`
from a verified run.

## Performance and memory

Parsing the inputs is the slow part. It is spread over `-j` worker processes, and the
results are put back in their original order before plotting, so every `-j` value
produces the same figures. Plotting runs sequentially in the main process.

Measured on a 12-CPU server with the full dataset:

| Script | Paper's original scripts (single core) | `-j 8` |
|---|---|---|
| Set 1 | 7.6 min | 7 s |
| Set 2 | 24.2 min | 13 s |
| Set 3 | 2 s | 2 s |
| Set 4 | 26 s (already used the faster `util.py`) | 11 s |
| **All four** | ≈ 32 min | **33 s** (single core: ~1.0 min) |

Single processes peaked at 0.5–0.7 GB of RSS. A worker handles one input at a time
(the largest rule file is about 95 MB on disk), so budget roughly that much per worker
and lower `-j` on machines with little memory.

## Reproducibility

- **Refactor check:** on the full dataset, all 18 PDFs are byte-identical to the output of
  the paper's original plotting scripts, apart from the embedded creation date. The
  refactor changes no data, statistics or figure content.
- **Byte-identical reruns:** a PDF normally embeds its creation time. For byte-identical
  PDFs across runs, set a fixed timestamp:

  ```bash
  SOURCE_DATE_EPOCH=0 .venv/bin/python artifact/plots/run_all_plots.py -j 8
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
- **Figure file name.** `BigPicutre.pdf` (sic) keeps its original spelling.
