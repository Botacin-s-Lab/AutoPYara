================================================================================
artifact/ - the artifact's code
================================================================================

WHAT IS IN THIS DIRECTORY
--------------------------------------------------------------------------------

    plots/                  regenerates the paper's 18 figures from the evaluation
                            data and verifies claims 4-9 (plots/README.md)
        run_all_plots.py        all four figure sets (-j N worker processes)
        PlotsSet1..4_*.py       one script per figure set
        verify_claims.py        regenerate + compare + check one claim (used by
                                claims/claim4..9/run.sh)
        plot_common.py, util.py shared code: parallel extraction, rule parsing,
                                recording of the plotted numbers

    download_data.py        downloads the evaluation data from Zenodo, verifies
                            every file against its SHA-256 manifest, unpacks it
                            into ../data
    package_data.py         (authors only) builds that archive from exactly the
                            files the figure scripts read

    make_proxy_corpus.py    generates the synthetic sample corpus of claims 1-3:
                            pseudo-random binaries in families that share a large
                            contiguous core. Deterministic (fixed seed); contains
                            no malicious code. Usage:
                                python3 make_proxy_corpus.py --out /tmp/corpus --report

    requirements-lock.txt   pinned Python dependencies (Python 3.11/3.12), used by
                            ../install.sh and ../Dockerfile

WHERE THE AUTOPYARA TOOL'S SOURCE LIVES
--------------------------------------------------------------------------------

The tool is not copied into this repository; install.sh installs the released
package, pinned, so evaluators run exactly the published version.

    Python frontend     autopyara==0.1.2 on PyPI
                        https://github.com/Botacin-s-Lab/AutoPYaraPyPI (tag v0.1.2)
        autopyara/core.py                 generate() and train(); the main API
        autopyara/interface.py            JVM lifecycle, Java<->Python conversion
        autopyara/augmented_predictor/    ssdeep + DBSCAN pre-clustering
        autopyara/jars/AutoYara.jar       the compiled Java backend

    Java backend        https://github.com/Botacin-s-Lab/AutoPYaraBackend
        To rebuild the jar:  git clone ...; cd AutoPYaraBackend && mvn -B package

    Documentation       https://botacin-s-lab.github.io/AutoPYaraPyPI/

To evaluate a local checkout of the frontend instead of the PyPI release:

    AUTOPYARA_SOURCE=/path/to/AutoPYaraPyPI ./install.sh

DATA
--------------------------------------------------------------------------------

    AutoPYara's Bloom filters (~600 MB, claims 1-3) are downloaded by install.sh
    (autopyara-download) from https://github.com/Botacin-s-Lab/AutoPYaraPyPI/tree/data-branch

    The evaluation data (claims 4-9) are downloaded by download_data.py from
    Zenodo into ../data. Layout: plots/README.md; provenance: ../provenance.txt.
