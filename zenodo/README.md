# AutoPYara — ACSAC 2026 Evaluation Data

This is the data record behind the ACSAC 2026 paper **"AutoPYara: Next-Gen YARA
Rule Generator for Malware Family Clustering"** and its accompanying artifact,
[Botacin-s-Lab/AutoPYara](https://github.com/Botacin-s-Lab/AutoPYara). It holds
the clusterings, generated YARA rules, threat-hunting results, and supporting
raw data the paper's figures and claims are computed from. **No malware or
other executable sample is included** — see [What is NOT included](#what-is-not-included).

This file is kept under version control in the artifact repository at
[`zenodo/README.md`](https://github.com/Botacin-s-Lab/AutoPYara/blob/main/zenodo/README.md)
and is also published as part of this Zenodo record.

## Citation

If you use this data, please cite the paper:

> Mabon Ninan\*, Nhat Minh Nguyen\*, Soumyajyoti Dutta, Sidharth Anil, and Marcus Botacin.
> **"AutoPYara: Next-Gen YARA Rule Generator for Malware Family Clustering."** *Annual Computer Security Applications Conference (ACSAC 2026)*, to appear.
> \*Equal contribution. Texas A&M University — {ninanmm, nmnguy29, soumyajyoti1998, sid.anil, botacin}@tamu.edu

```bibtex
@inproceedings{autopyara2026,
  title     = {AutoPYara: Next-Gen YARA Rule Generator for Malware Family Clustering},
  author    = {Ninan, Mabon and Nguyen, Nhat Minh and Dutta, Soumyajyoti and Anil, Sidharth and Botacin, Marcus},
  booktitle = {Proceedings of the Annual Computer Security Applications Conference (ACSAC)},
  year      = {2026},
  note      = {To appear}
}
```

Please also consider citing this dataset itself via its Zenodo DOI:

```bibtex
@dataset{autopyara2026data,
  title     = {AutoPYara: Next-Gen YARA Rule Generator for Malware Family Clustering -- Evaluation Data},
  author    = {Ninan, Mabon and Nguyen, Nhat Minh and Dutta, Soumyajyoti and Anil, Sidharth and Botacin, Marcus},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {TODO(authors): fill in once this record is published}
}
```

AutoPYara builds on the original AutoYara project; if you use the `AutoYara`
baseline results in this data, please also cite:

> Edward Raff, Richard Zak, Gary Lopez Munoz, William Fleming, Hyrum S. Anderson, Bobby Filar, Charles Nicholas, and James Holt.
> **"Automatic Yara Rule Generation Using Biclustering."** *13th ACM Workshop on Artificial Intelligence and Security (AISec '20)*, 2020.
> [doi:10.1145/3411508.3421372](https://doi.org/10.1145/3411508.3421372) · [arXiv:2009.03779](https://arxiv.org/abs/2009.03779)

## Contents

| File | Size | MD5 | Needed for artifact evaluation? |
|---|---|---|---|
| `AutoPYaraClusters.zip` | 2.60 GB | `62d60a1757005bc9268e37f35511edf8` | **Yes** |
| `ProcessedRules.zip` | 726.47 MB | `a3b456b76f9f9cdd88179e10280a4241` | **Yes** |
| `ThreatHunting.zip` | 67.76 MB | `1181a15e44d40e19790706e8b867b737` | **Yes** |
| `RawDataWithSimilarityHashes.zip` | 9.69 GB | `1698556a179db33fc9a2a056d08e720c` | No — supplementary |
| `yaraRules.zip` | 5.17 GB | `223d10dad36e9732333357bc169b92bf` | No — supplementary |
| `EmberBloomFliters.zip` | 107.69 MB | `a36dbbdc2801f7d8e699c0323e9c0b79` | No — supplementary |
| `AutoPYaraBloomFliters.zip` | 107.30 MB | `de3fe6f533693a1d9f1d1bb37bfea847` | No — supplementary |

(File names and MD5s above are as uploaded; `EmberBloomFliters`/`AutoPYaraBloomFliters`
keep that spelling for consistency with the uploaded archive names.)

### What the artifact evaluation needs

The AutoPYara artifact (claims 4-9; see the
[artifact README](https://github.com/Botacin-s-Lab/AutoPYara/blob/main/README.txt))
regenerates every paper figure from three archives. Unzip each into the
matching subfolder of the artifact's `data/` directory (created by
`./install.sh` / `artifact/download_data.py`):

| Archive | Unzips into | Contents |
|---|---|---|
| `AutoPYaraClusters.zip` | `data/clusterCSV/` | 11 clustering CSVs: `sdhash/Th{50,60,70,80,90}.csv`, `ssdeep/th{50,60,70,80,90}.csv`, `virusTotal/MainVtCluster.csv`. One row per sample with its cluster label (`Cluster_Label`); samples are identified only by file name/hash. |
| `ProcessedRules.zip` | `data/ruleEval/` | The 84 merged YARA rule files (`merged_group_1.yar`) generated for every clustering/tool/configuration, each rule annotated with the true-positive rate it achieved (`// Input TP Rate: X/Y`). Covers `originalBloomFilters/` (Ember-trained filters) and `retrainedBloomFilters/` (retrained on this corpus). |
| `ThreatHunting.zip` | `data/ThreatHunting/` | The three threat-hunting experiments (`IdealStream_HEU`, `NonIdealStream_RDM`, `RealWorldStream_PHeu`), each split by similarity threshold (`Th50`-`Th90`) and train/test ratio, with per-cluster train/test file lists and TP-rate files for AutoPYara and AutoYara. |

Full field-by-field detail is in
[`artifact/plots/README.md`](https://github.com/Botacin-s-Lab/AutoPYara/blob/main/artifact/plots/README.md)
and [`provenance.txt`](https://github.com/Botacin-s-Lab/AutoPYara/blob/main/provenance.txt)
in the artifact repository. `artifact/download_data.py` is being updated to
fetch and verify these three files automatically once this record is
published; until then, download and verify them manually (see
[Verifying a download](#verifying-a-download) below) and unzip them into the
paths above.

### Supplementary archives

These four archives are published for completeness and transparency (and to
let others extend this work) but are **not** required to reproduce the
paper's figures or claims:

- **`RawDataWithSimilarityHashes.zip`** (9.69 GB) — the full per-sample
  similarity-hash data (fuzzy hashes) and associated metadata the clusterings
  in `AutoPYaraClusters.zip` were computed from. Very large; samples are
  referenced only by file name/hash, never by content.
- **`yaraRules.zip`** (5.17 GB) — the complete, unmerged set of YARA rules
  generated across every clustering, tool, configuration and run, before the
  merging/annotation step that produced the smaller `ProcessedRules.zip`
  actually used by the figures.
- **`EmberBloomFliters.zip`** / **`AutoPYaraBloomFliters.zip`** (~108 MB
  each) — the trained benign/malicious Bloom filters (Ember-based and
  retrained-on-this-corpus, respectively) used to generate the rules. Useful
  for regenerating rules from scratch; not needed to reproduce the paper's
  numbers from the rules already provided.

## What is NOT included

No malware, or any other executable sample, is included in this record or in
the artifact repository. The paper's malware corpus cannot be redistributed
for legal and ethical reasons. Everything here is a derived result: cluster
assignments, generated YARA rules with their measured TP rates, threat-hunting
TP rates, and similarity-hash fingerprints. Samples appear only as identifiers
(file names/hashes), never as content. See
[`ethics.txt`](https://github.com/Botacin-s-Lab/AutoPYara/blob/main/ethics.txt)
and [`use.txt`](https://github.com/Botacin-s-Lab/AutoPYara/blob/main/use.txt)
in the artifact repository.

## Verifying a download

Each archive's MD5 is listed in [Contents](#contents) above. After
downloading, verify with:

```bash
md5sum AutoPYaraClusters.zip ProcessedRules.zip ThreatHunting.zip
# compare against the table above
```

## License

Creative Commons Attribution 4.0 International (CC BY 4.0).

## Related resources

| | |
|---|---|
| Artifact repository | https://github.com/Botacin-s-Lab/AutoPYara |
| AutoPYara (tool, Python) | https://github.com/Botacin-s-Lab/AutoPYaraPyPI · https://pypi.org/project/autopyara/ |
| AutoPYara (Java backend) | https://github.com/Botacin-s-Lab/AutoPYaraBackend |

## Contact

Authors (Texas A&M University), in citation order:

| Author | Email |
|---|---|
| Mabon Ninan\* (corresponding) | ninanmm@tamu.edu |
| Nhat Minh Nguyen\* | nmnguy29@tamu.edu |
| Soumyajyoti Dutta | soumyajyoti1998@tamu.edu |
| Sidharth Anil | sid.anil@tamu.edu |
| Marcus Botacin | botacin@tamu.edu |

\*Equal contribution.
