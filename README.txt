================================================================================
AutoPYara - ACSAC 2026 Artifact
================================================================================

Artifact for the ACSAC 2026 paper on AutoPYara, a framework for automated YARA
rule generation from collections of malware samples (Bloom-filtered byte
n-gram analysis with cluster-aware signature construction).
    Paper:   Mabon Ninan*, Nhat Minh Nguyen*, Soumyajyoti Dutta, Sidharth Anil,
             and Marcus Botacin. "AutoPYara: Next-Gen YARA Rule Generator for
             Malware Family Clustering." To appear, ACSAC 2026.
             (*Equal contribution. BibTeX: metadata.toml, "citation")

Badges sought:  Available, Functional, Reproduced

--------------------------------------------------------------------------------
PUBLIC RELEASE
--------------------------------------------------------------------------------

Everything in this artifact is released publicly. Code is under the MIT
license (LICENSE, license.txt); the evaluation data are published on Zenodo.

    This artifact      https://github.com/Botacin-s-Lab/AutoPYara
                       Zenodo DOI: TODO(authors)
    Evaluation data    Zenodo DOI: 10.5281/zenodo.22665898
                       https://doi.org/10.5281/zenodo.22665898  (fetched by ./loadData.sh;
                       see zenodo/README.md for what each archive contains)
    AutoPYara (tool)   https://github.com/Botacin-s-Lab/AutoPYaraPyPI  (tag v0.1.2)
                       https://pypi.org/project/autopyara/0.1.2/
    Java backend       https://github.com/Botacin-s-Lab/AutoPYaraBackend

Nothing is withheld except the paper's malware corpus, which cannot be
redistributed (section 6).

--------------------------------------------------------------------------------
1. WHAT THIS ARTIFACT CONTAINS
--------------------------------------------------------------------------------

  * The AutoPYara tool, installed pinned from PyPI, plus a synthetic proxy corpus
    to exercise it: claims 1-3 show the tool installs and both rule-generation
    pipelines run end to end.
  * The evaluation data behind the paper's results: the clusterings of the
    malware corpus, every YARA rule generated for every cluster and configuration
    together with the true-positive (TP) rate it achieved, and the threat-hunting
    results (provenance.txt).
  * Scripts that regenerate every figure of the paper from that data and check
    each paper claim against it: claims 4-9 (artifact/plots/).

The rules were generated from a malware corpus that cannot be shared, so
regenerating the rules themselves is out of scope; as agreed with the AEC,
evaluators verify the provided rules and regenerate the paper's figures and
numbers from them.

--------------------------------------------------------------------------------
2. CLAIMS
--------------------------------------------------------------------------------

Every claim has a directory claims/claimN_*/ with claim.txt (the claim and what
is checked), run.sh (runs it and prints PASS/FAIL) and expected/ (reference
output; for claims 4-9 also the reference figures and plotted values).

  Artifact  Paper   Claim                                         Figures (results/...)                  Time
  --------  -----   --------------------------------------------  -------------------------------------  -------
  claim1    -       tool installs, JVM backend starts             -                                      <1 min
  claim2    -       AutoYara preset emits a valid YARA rule       -                                      1-3 min
  claim3    -       AutoPYara preset derives its own K            -                                      1-4 min
  claim4    1       AutoYara's baseline hides the clusters it     Claim1_IncorrectBaseLines/ (2)          ~10 s
                    fails on: 87-91 % on non-zero clusters vs
                    11-34 % over all clusters
  claim5    2       the Bloom filters matter: retrained filters   Claim2_BloomFiltersMatter/ (2)          ~10 s
                    lift both tools (e.g. 11 % -> 93 % SSdeep)
  claim6    3       AutoPYara beats AutoYara on all three         Claim3_YaraVsPYara/ (1)                 ~10 s
                    clusterings
  claim7    4       threshold and K: AutoPYara > AutoYara; best   Claim4_ThresHoldFigures/ (10)           ~15 s
                    K > AutoPYara > worst K; informed K
                    heuristics > AutoYara > uninformed ones
  claim8    5       threat hunting: AutoPYara keeps a higher TP   Claim5_Threathunting/ (2)               ~5 s
                    rate than AutoYara on held-out samples
  claim9    6       all 15 configurations ranked, from AutoYara   Claim6_YaraInAllitsConfigurations/ (1)  ~10 s
                    as released (11 %) to AutoPYara best K (96 %)

  Runtimes are for 8 worker processes (-j 8) on the reference machine.
  TODO(authors): add the paper's figure number for each figure file.

Claims 4-9 regenerate their figures into results/claimN_*/, compare every
plotted number with the reference in claims/claimN_*/expected/values.json
(tolerance 1.0 percentage point; a correct run deviates by exactly 0), and check
the claim's statements on the regenerated numbers. The regenerated PDFs can be
compared side by side with claims/claimN_*/expected/figures/.

--------------------------------------------------------------------------------
3. REQUIREMENTS
--------------------------------------------------------------------------------

  OS        Linux x86-64 (tested: Ubuntu). macOS/Windows untested; use Docker.
  Python    3.11 or 3.12, with the venv module (python3-venv on Debian/Ubuntu)
  Java      JRE 11+ on PATH or JAVA_HOME             (claims 1-3 only)
  RAM       16 GB for claims 1-3 (fixed 14 GB JVM heap); 8 GB for claims 4-9
  CPU       any x86-64; claims 4-9 use all cores (-j N to limit)
  Disk      ~60 GB: evaluation data unpacked (~3.4 GB download; loadData.sh's
            default fetches only the 3 archives claims 4-9 need), 600 MB Bloom
            filters, ~1 GB Python environment, figures
  Network   during installation only
  GPU       not used

Or use Docker (section 4), which needs only Docker and 16 GB of RAM.
Public infrastructure: any standard CloudLab or Chameleon x86-64 node works.
Google Colab is not suitable for claims 1-3 (infrastructure/constraints.txt).
Details: infrastructure/resources.txt.

--------------------------------------------------------------------------------
4. GETTING STARTED
--------------------------------------------------------------------------------

    git clone https://github.com/Botacin-s-Lab/AutoPYara.git
    cd AutoPYara
    ./install.sh               # 10-25 min: .venv, pinned packages, Bloom filters, data

  Kick the tires (about 1 minute):

    ./claims/claim1_install/run.sh                   # the tool works
    ./claims/claim4_incorrect_baselines/run.sh -j 8  # a paper figure is reproduced

  Everything (about 10 minutes):

    ./run_all_claims.sh -j 8

  Options: SKIP_TOOL=1 ./install.sh sets up only claims 4-9 (no Java needed);
  SKIP_DATA=1 only claims 1-3. ./run_all_claims.sh --paper / --tool runs one group.

  Docker instead of install.sh:

    docker build -t autopyara-artifact .
    mkdir -p data results
    docker run --rm -v "$PWD/data:/opt/artifact/data" autopyara-artifact \
        ./loadData.sh --yes
    docker run --rm -it --memory=16g -v "$PWD/data:/opt/artifact/data" \
        -v "$PWD/results:/opt/artifact/results" autopyara-artifact ./run_all_claims.sh -j 8

  To regenerate all 18 figures at once (outside the claim checks):

    .venv/bin/python artifact/plots/run_all_plots.py -j 8    # -> results/figures/

--------------------------------------------------------------------------------
5. DIRECTORY LAYOUT
--------------------------------------------------------------------------------

    README.txt            this file
    install.sh            one-command setup
    loadData.sh           fetch + verify the evaluation data from Zenodo (called
                          by install.sh; --all also fetches the supplementary
                          archives; see zenodo/README.md)
    run_all_claims.sh     runs claims 1-9, prints a PASS/FAIL summary
    Dockerfile            contained environment (Python 3.12, OpenJDK 17, pinned)
    metadata.toml         ACSAC/artmeta packaging metadata
    use.txt               intended use and limitations
    license.txt, LICENSE  licenses
    provenance.txt        how the evaluation data were produced
    ethics.txt            ethical considerations
    zenodo/README.md      description of every archive in the Zenodo data record

    artifact/             the artifact's code (see artifact/README.txt)
        plots/                figure scripts, claim verification (verify_claims.py)
        download_data.py      older single-archive fetcher; superseded by
                              ../loadData.sh, not currently used by install.sh
        package_data.py       (authors) build the data archive for Zenodo
        make_proxy_corpus.py  synthetic corpus for claims 1-3
        requirements-lock.txt pinned dependencies
    claims/claimN_*/      one directory per claim: claim.txt, run.sh, expected/
    infrastructure/       resources.txt (requirements, runtimes), constraints.txt
    data/                 evaluation data (downloaded; not in git)
    results/              everything the claims generate (not in git)

--------------------------------------------------------------------------------
6. SCOPE, LIMITATIONS AND KNOWN DIFFICULTIES
--------------------------------------------------------------------------------

  * The malware corpus is not included (legal and ethical reasons), so the rules
    cannot be regenerated here. Claims 4-9 start from the generated rules and
    their recorded TP rates and reproduce every figure and number from them.
  * Claims 1-3 run on a synthetic corpus that contains no malware. Their rules
    are valid YARA but not meaningful signatures, and the numbers they print are
    not a benchmark (both pipelines saturate at 6/6).
  * The augmented pipeline (claim 3) uses an unseeded random number generator,
    so its output differs between runs; the check is structural. Claims 4-9 are
    deterministic.
  * The JVM backend reserves a fixed 14 GB heap: claims 1-3 need 16 GB of RAM.
  * The figure scripts keep a few quirks of the paper's plotting code on purpose
    (artifact/plots/README.md, "Notes and known quirks").

--------------------------------------------------------------------------------
7. BUILDING ON THIS ARTIFACT
--------------------------------------------------------------------------------

  * Generate rules for your own samples: python -c "from autopyara import
    AutoPYara; print(AutoPYara().generate(input_files='DIR', preset='AutoPYara',
    output_format='string')['rule_string'])"   (docs:
    https://botacin-s-lab.github.io/AutoPYaraPyPI/)
  * Evaluate new rule sets with the same figures: place them in the data/ layout
    described in artifact/plots/README.md and run artifact/plots/run_all_plots.py.

--------------------------------------------------------------------------------
8. CONTACT
--------------------------------------------------------------------------------

Authors (Texas A&M University), in citation order:
  Mabon Ninan*         ninanmm@tamu.edu
  Nhat Minh Nguyen*    nmnguy29@tamu.edu
  Soumyajyoti Dutta    soumyajyoti1998@tamu.edu
  Sidharth Anil        sid.anil@tamu.edu
  Marcus Botacin       botacin@tamu.edu
  (*equal contribution)

Corresponding author: Mabon Ninan - ninanmm@tamu.edu
Issues: https://github.com/Botacin-s-Lab/AutoPYara/issues

Related thesis: Nhat Minh Nguyen. "AutoPYara: A Python/Java Framework for
Automatic YARA Rule Generation Using Semi-Supervised Clustering." M.S.
Thesis, Texas A&M University, Spring 2025.
