# AutoPYara — ACSAC 2026 Artifact

This repository is the companion artifact for a research paper about **AutoPYara**, a
tool that automatically writes [YARA](https://virustotal.github.io/yara/) rules —
the pattern files antivirus and security tools use to detect malware — by looking at a
*whole family* of related malware samples at once, instead of one sample at a time.
Analyzing samples together lets it find the patterns that are shared across an entire
family, which produces more accurate detection rules than older tools that only look
at one sample.

This repository lets you:

1. **Install the tool** and watch it run on safe, synthetic example data.
2. **Reproduce every number and figure** from the paper, using the real evaluation
   data we collected (the actual malware samples themselves cannot be shared — see
   [Scope, limitations and known difficulties](#6-scope-limitations-and-known-difficulties)).

> **Paper:** Mabon Ninan\*, Nhat Minh Nguyen\*, Soumyajyoti Dutta, Sidharth Anil, and
> Marcus Botacin. *"AutoPYara: Next-Gen YARA Rule Generator for Malware Family
> Clustering."* To appear, ACSAC 2026.
> (\*Equal contribution. BibTeX citation: `metadata.toml`, field `citation`.)
>
> **Badges sought:** Available, Functional, Reproduced

---

## Quick start (TL;DR)

If you just want to see it work, this is all you need:

```bash
git clone https://github.com/Botacin-s-Lab/AutoPYara.git
cd AutoPYara
./install.sh                                     # one-time setup, ~10-25 minutes
./claims/claim1_install/run.sh                    # check 1: the tool installs and runs
./claims/claim4_incorrect_baselines/run.sh -j 8   # check 2: reproduce a real paper figure
```

Both checks print `PASS` or `FAIL`. If they pass, everything is working. The full
walkthrough (including a Docker option that needs nothing but Docker) is in
[Getting started](#4-getting-started) below.

---

## Public release

Everything in this artifact is released publicly. The code is under the MIT license
(`LICENSE`, `license.txt`); the evaluation data is published separately on Zenodo, a
free, long-term archive for research data.

| What | Where |
| --- | --- |
| This artifact | <https://github.com/Botacin-s-Lab/AutoPYara> — Zenodo DOI: TODO(authors) |
| Evaluation data | Zenodo DOI [10.5281/zenodo.22665898](https://doi.org/10.5281/zenodo.22665898) — fetched automatically by `./loadData.sh`; see `zenodo/README.md` for what each archive contains |
| AutoPYara (the tool) | <https://github.com/Botacin-s-Lab/AutoPYaraPyPI> (tag `v0.1.2`) and <https://pypi.org/project/autopyara/0.1.2/> |
| Java backend | <https://github.com/Botacin-s-Lab/AutoPYaraBackend> |

The only thing *not* included is the paper's malware corpus itself, which cannot be
redistributed for legal and ethical reasons (see [section 6](#6-scope-limitations-and-known-difficulties)).

---

## 1. What this artifact contains

- **The AutoPYara tool**, installed exactly as released on PyPI, plus a small
  synthetic "proxy corpus" (fake, harmless data shaped like malware families) so you
  can watch both of its rule-generation pipelines run start to finish. This is
  **claims 1-3**.
- **The evaluation data behind the paper's results**: how the real malware corpus was
  grouped into families (clusters), every YARA rule generated for every cluster and
  configuration, the detection ("true-positive") rate each rule achieved, and the
  threat-hunting results (`provenance.txt` explains how this data was produced).
- **Scripts that regenerate every figure in the paper** from that data, and check each
  of the paper's claims against it. This is **claims 4-9** (in `artifact/plots/`).

The rules were generated from a real malware corpus that we are not able to share, so
regenerating the *rules themselves* from raw malware is out of scope for this
artifact — that was agreed with the Artifact Evaluation Committee in advance. Instead,
evaluators verify the rules we already generated and regenerate the paper's figures
and numbers directly from them.

---

## 2. Claims

A "claim" here is one specific, checkable statement from the paper (or about the tool
itself). Each claim has its own folder, `claims/claimN_*/`, containing:

- `claim.txt` — what the claim says and how it's checked
- `run.sh` — runs the check and prints `PASS` or `FAIL`
- `expected/` — the reference output to compare against (for claims 4-9, also the
  reference figures and the exact numbers that were plotted)

| Artifact claim | Paper claim | What it checks | Figures produced | Time |
| --- | --- | --- | --- | --- |
| `claim1` | — | The tool installs and its Java backend starts | — | < 1 min |
| `claim2` | — | The AutoYara preset emits a valid YARA rule | — | 1-3 min |
| `claim3` | — | The AutoPYara preset derives its own cluster count (K) | — | 1-4 min |
| `claim4` | 1 | AutoYara's usual "headline" number hides the clusters it fails on: 87-91% on the clusters where it has *any* success, vs. only 11-34% averaged over *all* clusters | `Claim1_IncorrectBaseLines/` (2 figures) | ~10 s |
| `claim5` | 2 | The Bloom filters matter: retraining them lifts both tools' scores a lot (e.g. 11% → 93% on the SSdeep clustering) | `Claim2_BloomFiltersMatter/` (2 figures) | ~10 s |
| `claim6` | 3 | AutoPYara beats AutoYara on all three clustering methods | `Claim3_YaraVsPYara/` (1 figure) | ~10 s |
| `claim7` | 4 | AutoPYara beats AutoYara at every similarity threshold; the best choice of K beats AutoPYara's automatic choice, which beats the worst K; smarter ("informed") ways of picking K beat AutoYara, dumber ("uninformed") ones don't | `Claim4_ThresHoldFigures/` (10 figures) | ~15 s |
| `claim8` | 5 | In simulated threat hunting, AutoPYara keeps a higher detection rate than AutoYara on samples neither tool has seen before | `Claim5_Threathunting/` (2 figures) | ~5 s |
| `claim9` | 6 | Ranking all 15 configurations from worst to best: AutoYara as released (11%) up to AutoPYara with the best K (96%) | `Claim6_YaraInAllitsConfigurations/` (1 figure) | ~10 s |

*Runtimes are measured with 8 worker processes (`-j 8`) on our reference machine.*
*TODO(authors): add the paper's figure number for each figure file.*

For claims 4-9, the script regenerates the figures into `results/claimN_*/`, compares
every plotted number against the reference in `claims/claimN_*/expected/values.json`
(allowing 1.0 percentage point of tolerance — a correct run typically matches
exactly), and checks the claim's actual statements against the regenerated numbers.
You can also visually compare the regenerated PDFs side by side with the reference
figures in `claims/claimN_*/expected/figures/`.

---

## 3. Requirements

You don't need all of these if you use Docker — see the note below the table.

| Requirement | Details |
| --- | --- |
| OS | Linux, x86-64 (tested on Ubuntu). macOS/Windows are untested — use Docker instead. |
| Python | 3.11 or 3.12, with the `venv` module (`python3-venv` on Debian/Ubuntu). If that's not available, `install.sh` automatically falls back to using `conda create` instead, as long as `conda` or `mamba` is on your `PATH` (or force this with `USE_CONDA=1`). |
| Java | A JRE 11 or newer, on your `PATH` or via `JAVA_HOME` — **only needed for claims 1-3.** |
| RAM | 16 GB for claims 1-3 (the tool reserves a fixed 14 GB of memory for its Java backend); 8 GB is enough for claims 4-9. |
| CPU | Any x86-64 processor. Claims 4-9 use all your CPU cores by default (pass `-j N` to limit that). |
| Disk | About 60 GB free: the evaluation data once unpacked (a ~3.4 GB download — `loadData.sh`'s default only fetches the 3 archives claims 4-9 actually need), 600 MB of Bloom filters, ~1 GB for the Python environment, plus the generated figures. |
| Network | Only needed while installing (to download packages, Bloom filters, and data). |
| GPU | Not used. |

Prefer not to install anything locally? Use **Docker** instead (see
[Getting started](#4-getting-started)) — it only needs Docker itself and 16 GB of RAM.

This also runs fine on public research infrastructure: any standard
[CloudLab](https://www.cloudlab.us/) or [Chameleon](https://www.chameleoncloud.org/)
x86-64 node works out of the box. Google Colab is **not** suitable for claims 1-3 (see
`infrastructure/constraints.txt`). Full details: `infrastructure/resources.txt`.

---

## 4. Getting started

### Option A — install directly

```bash
git clone https://github.com/Botacin-s-Lab/AutoPYara.git
cd AutoPYara
./install.sh               # 10-25 min: sets up .venv, packages, Bloom filters, data
```

**Kick the tires** (about 1 minute total):

```bash
./claims/claim1_install/run.sh                   # the tool installs and works
./claims/claim4_incorrect_baselines/run.sh -j 8  # a real paper figure is reproduced
```

**Run everything** (about 10 minutes):

```bash
./run_all_claims.sh -j 8
```

Useful options (set as environment variables before the command):

| Option | Effect |
| --- | --- |
| `SKIP_TOOL=1 ./install.sh` | Only set up claims 4-9 (no Java needed at all) |
| `SKIP_DATA=1 ./install.sh` | Only set up claims 1-3 |
| `USE_CONDA=1 ./install.sh` | Use conda instead of a Python `venv` (this is chosen automatically already if `python3 -m venv` doesn't work but conda/mamba does) |
| `./run_all_claims.sh --paper` | Run only the paper claims (4-9) |
| `./run_all_claims.sh --tool` | Run only the tool claims (1-3) |

### Option B — Docker (no local Python/Java setup needed)

```bash
docker build -t autopyara-artifact .
mkdir -p data results
docker run --rm -v "$PWD/data:/opt/artifact/data" autopyara-artifact \
    ./loadData.sh --yes
docker run --rm -it --memory=16g -v "$PWD/data:/opt/artifact/data" \
    -v "$PWD/results:/opt/artifact/results" autopyara-artifact ./run_all_claims.sh -j 8
```

### Regenerating all figures at once

Outside of the claim checks, you can regenerate all 18 figures from the paper in one
go:

```bash
.venv/bin/python artifact/plots/run_all_plots.py -j 8    # figures land in results/figures/
```

---

## 5. Directory layout

```
README.md              this file
install.sh              one-command setup
loadData.sh             fetch + verify the evaluation data from Zenodo
                        (called automatically by install.sh; --all also fetches
                        the supplementary archives — see zenodo/README.md)
run_all_claims.sh       runs claims 1-9 and prints a PASS/FAIL summary
Dockerfile              a ready-made environment (Python 3.12, OpenJDK 17, pinned)
metadata.toml           ACSAC/artmeta packaging metadata
use.txt                 intended use and limitations
license.txt, LICENSE    licenses
provenance.txt          how the evaluation data were produced
ethics.txt              ethical considerations
zenodo/README.md        description of every archive in the Zenodo data record

artifact/               the artifact's code (see artifact/README.txt)
  plots/                figure scripts, claim verification (verify_claims.py)
  download_data.py      older single-archive fetcher; superseded by ../loadData.sh,
                        not currently used by install.sh
  package_data.py       (authors only) builds the data archive published on Zenodo
  make_proxy_corpus.py  synthetic corpus used by claims 1-3
  requirements-lock.txt pinned Python dependencies

claims/claimN_*/        one directory per claim: claim.txt, run.sh, expected/
infrastructure/         resources.txt (requirements, runtimes), constraints.txt
data/                   evaluation data (downloaded here; not tracked in git)
results/                everything the claims generate (not tracked in git)
```

---

## 6. Scope, limitations and known difficulties

- **The malware corpus itself is not included** (legal and ethical reasons), so the
  rules cannot be regenerated from scratch here. Claims 4-9 instead start from the
  already-generated rules and their recorded detection rates, and reproduce every
  figure and number in the paper from that data.
- **Claims 1-3 run on a synthetic corpus** that contains no real malware. Their rules
  are valid YARA syntax but not meaningful detection signatures, and the numbers they
  print aren't a real benchmark — both pipelines simply saturate at 6/6 on this toy
  data.
- **Claim 3's pipeline uses an unseeded random number generator**, so its exact output
  differs a little between runs; that check is structural (it checks the *shape* of
  the output, not exact values) rather than exact-match. Claims 4-9 are fully
  deterministic and will match exactly.
- **The Java backend reserves a fixed 14 GB of memory**, so claims 1-3 need at least
  16 GB of RAM to run.
- The figure-generation scripts intentionally preserve a few small quirks from the
  original paper's plotting code — see "Notes and known quirks" in
  `artifact/plots/README.md` for details.

---

## 7. Building on this artifact

- **Generate rules for your own samples:**

  ```bash
  python -c "from autopyara import AutoPYara; print(AutoPYara().generate(
      input_files='DIR', preset='AutoPYara', output_format='string')['rule_string'])"
  ```

  Full documentation: <https://botacin-s-lab.github.io/AutoPYaraPyPI/>

- **Evaluate a new rule set with the same figures:** place it in the `data/` layout
  described in `artifact/plots/README.md`, then run
  `artifact/plots/run_all_plots.py`.

---

## 8. Contact

Authors (Texas A&M University), in citation order:

| Name | Email |
| --- | --- |
| Mabon Ninan\* | ninanmm@tamu.edu |
| Nhat Minh Nguyen\* | nmnguy29@tamu.edu |
| Soumyajyoti Dutta | soumyajyoti1998@tamu.edu |
| Sidharth Anil | sid.anil@tamu.edu |
| Marcus Botacin | botacin@tamu.edu |

\* Equal contribution.

**Corresponding author:** Mabon Ninan — ninanmm@tamu.edu
**Found a bug or have a question?** Open an issue: <https://github.com/Botacin-s-Lab/AutoPYara/issues>

Related thesis: Nhat Minh Nguyen. *"AutoPYara: A Python/Java Framework for Automatic
YARA Rule Generation Using Semi-Supervised Clustering."* M.S. Thesis, Texas A&M
University, Spring 2025.
