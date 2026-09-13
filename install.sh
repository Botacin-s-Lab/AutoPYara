#!/usr/bin/env bash
#
# One-command setup for the AutoPYara ACSAC 2026 artifact.
#
#   1. picks a Python 3.11/3.12 interpreter and creates ./.venv
#   2. installs the pinned dependencies (artifact/requirements-lock.txt), including
#      the tool itself (autopyara==0.1.2 from PyPI) and the plotting stack
#   3. checks Java                                  (tool claims 1-3 only)
#   4. fetches AutoPYara's Bloom filters, ~600 MB   (tool claims 1-3 only)
#   5. fetches the evaluation data into ./data      (paper claims 4-9)
#   6. verifies the installation
#
# Safe to re-run: finished steps are skipped. Nothing is installed outside the
# repository directory.
#
# Usage:   ./install.sh
#
# Options (environment variables):
#   PYTHON=python3.12      interpreter for the venv (default: python3.12, python3.11 or python3)
#   USE_CONDA=1            use "conda create" instead of "python -m venv", even if a
#                          usable python3 is on PATH (auto-selected anyway when no
#                          python3 -m venv works, e.g. python3-venv isn't installed,
#                          as long as conda or mamba is on PATH)
#   CONDA_PYTHON_VERSION   Python version for the conda env (default: 3.12)
#   SKIP_TOOL=1            skip steps 3-4: set up only the paper claims 4-9 (no Java needed)
#   SKIP_DATA=1            skip step 5: set up only the tool claims 1-3
#   AUTOPYARA_SOURCE=DIR   install the tool from a local checkout of
#                          https://github.com/Botacin-s-Lab/AutoPYaraPyPI instead of PyPI
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HERE/.venv"
LOCK="$HERE/artifact/requirements-lock.txt"

step()  { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
ok()    { printf '    [ok] %s\n' "$*"; }
warn()  { printf '    [warn] %s\n' "$*"; }
fail()  { printf '    [FAIL] %s\n' "$*" >&2; exit 1; }
note()  { printf '    %s\n' "$*"; }

# ------------------------------------------------------------------------------
step "1/6  Python environment"
# ------------------------------------------------------------------------------
# Two ways to get an isolated Python 3.11/3.12 environment at $VENV:
#   venv   (default) - needs a system python3.11/python3.12 with a working venv module
#   conda  (fallback, or forced with USE_CONDA=1) - conda/mamba provisions its own
#          Python, so it works even without python3-venv or a 3.11/3.12 interpreter
# Either way, the rest of this script just uses "python"/"pip" once activated, and
# claims/*/run.sh activate $VENV/bin/activate the same way regardless of which one
# built it (see the wrapper written in the conda branch below).
CONDA_BIN=""
for c in conda mamba; do
    if command -v "$c" >/dev/null 2>&1; then CONDA_BIN="$c"; break; fi
done

if [ -z "${USE_CONDA:-}" ]; then
    if [ -z "${PYTHON:-}" ]; then
        for candidate in python3.12 python3.11 python3; do
            if command -v "$candidate" >/dev/null 2>&1; then PYTHON="$candidate"; break; fi
        done
    fi
    if [ -n "${PYTHON:-}" ]; then
        PY_VER="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
        case "${PY_VER:-}" in
            3.11|3.12) ;;
            *) warn "$PYTHON is Python ${PY_VER:-unknown}; need 3.11 or 3.12."; PYTHON="" ;;
        esac
    fi
    if [ -n "${PYTHON:-}" ] && ! "$PYTHON" -m venv --help >/dev/null 2>&1; then
        warn "$PYTHON found (Python $PY_VER) but its venv module isn't usable (ensurepip missing?)."
        PYTHON=""
    fi
fi

# $VENV may be left over from a previous run that used the other backend (or
# died mid-setup) - e.g. a conda prefix has bin/python but no bin/activate, so
# blindly trusting its presence is what used to break re-runs. Recognize each
# backend's own env by its real marker file and rebuild anything else from
# scratch; "safe to re-run" (see header) means self-healing, not just skipping.
is_venv()       { [ -f "$1/pyvenv.cfg" ] && [ -x "$1/bin/python" ]; }
is_conda_env()  { [ -d "$1/conda-meta" ] && [ -x "$1/bin/python" ]; }

if [ -n "${USE_CONDA:-}" ] || [ -z "${PYTHON:-}" ]; then
    [ -n "$CONDA_BIN" ] || fail "No usable Python 3.11/3.12 with a working venv module, and no
       conda/mamba on PATH either. Either install python3-venv (Debian/Ubuntu:
       sudo apt-get install python3.12-venv) or install Miniconda/Anaconda, then
       re-run ./install.sh (set USE_CONDA=1 to force conda once it's installed),
       or use the Docker image described in README.md."
    if [ -n "${USE_CONDA:-}" ]; then
        note "Using $CONDA_BIN to provision the environment (USE_CONDA=$USE_CONDA)."
    else
        note "No usable python3 -m venv found; falling back to $CONDA_BIN."
    fi
    CONDA_PY="${CONDA_PYTHON_VERSION:-3.12}"
    if ! is_conda_env "$VENV"; then
        if [ -e "$VENV" ]; then
            warn "$VENV exists but isn't a valid conda environment (left over from a
       different install method or an interrupted run); rebuilding it."
            rm -rf "$VENV"
        fi
        "$CONDA_BIN" create --prefix "$VENV" --yes "python=$CONDA_PY" pip || fail "$CONDA_BIN could not create $VENV."
    fi
    CONDA_BASE_DIR="$("$CONDA_BIN" info --base)"
    # shellcheck disable=SC1091
    . "$CONDA_BASE_DIR/etc/profile.d/conda.sh"
    conda activate "$VENV"
    # A conda env has no bin/activate of its own (that's a venv thing); write one so
    # claims/*/run.sh's ". $VENV/bin/activate" works unmodified in a fresh shell too.
    # Rewritten every run (cheap) so it self-heals if it's ever missing or stale.
    cat > "$VENV/bin/activate" <<EOF
# Generated by install.sh: activates the conda environment for AutoPYara.
# shellcheck disable=SC1091
. "$CONDA_BASE_DIR/etc/profile.d/conda.sh"
conda activate "$VENV"
EOF
    PY_VER="$(python -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    ok "conda environment $VENV (Python $PY_VER)"
else
    if ! is_venv "$VENV"; then
        if [ -e "$VENV" ]; then
            warn "$VENV exists but isn't a valid venv (left over from a different install
       method or an interrupted run); rebuilding it."
            rm -rf "$VENV"
        fi
        "$PYTHON" -m venv "$VENV" || fail "could not create $VENV.
       On Debian/Ubuntu install the venv module: sudo apt-get install python3-venv"
    fi
    # shellcheck disable=SC1091
    . "$VENV/bin/activate"
    ok "virtual environment $VENV (Python $PY_VER)"
fi

# ------------------------------------------------------------------------------
step "2/6  Python packages (pinned)"
# ------------------------------------------------------------------------------
python -m pip install --quiet --upgrade pip
if [ -n "${AUTOPYARA_SOURCE:-}" ]; then
    note "Installing the tool from $AUTOPYARA_SOURCE"
    grep -v '^autopyara==' "$LOCK" > "$VENV/requirements-without-tool.txt"
    python -m pip install --quiet -r "$VENV/requirements-without-tool.txt"
    python -m pip install --quiet --no-deps "$AUTOPYARA_SOURCE"
else
    python -m pip install --quiet -r "$LOCK"
fi
ok "autopyara $(python -c 'import importlib.metadata as m; print(m.version("autopyara"))'), numpy, pandas, matplotlib, tqdm"

# The package downloads its Bloom filters on first import; step 4 does that explicitly.
BLOOMS="$(python -c 'import importlib.util, os; s = importlib.util.find_spec("autopyara"); print(os.path.join(os.path.dirname(s.origin), "data", "blooms"))')"

if [ -n "${SKIP_TOOL:-}" ]; then
    step "3/6  Java               - skipped (SKIP_TOOL=1)"
    step "4/6  Bloom filters      - skipped (SKIP_TOOL=1)"
else
    # --------------------------------------------------------------------------
    step "3/6  Java (tool claims 1-3)"
    # --------------------------------------------------------------------------
    # The rule-generation backend runs inside a JVM. Without a JRE the package
    # installs, but AutoPYara() fails the moment it is constructed.
    if ! command -v java >/dev/null 2>&1 && [ -z "${JAVA_HOME:-}" ]; then
        fail "No Java runtime found. Claims 1-3 need a JRE 11 or newer on PATH (or JAVA_HOME).
       On Debian/Ubuntu:  sudo apt-get install -y default-jre
       To set up only the paper claims 4-9, re-run with SKIP_TOOL=1."
    fi
    ok "$(java -version 2>&1 | head -1 || echo "JAVA_HOME=$JAVA_HOME")"

    # --------------------------------------------------------------------------
    step "4/6  AutoPYara Bloom filters (~600 MB, tool claims 1-3)"
    # --------------------------------------------------------------------------
    if [ -d "$BLOOMS" ]; then
        ok "already present at $BLOOMS"
    else
        note "Downloading - typically 10-20 minutes."
        autopyara-download
        [ -d "$BLOOMS" ] || fail "download finished but $BLOOMS is missing."
        ok "installed at $BLOOMS"
    fi
fi

if [ -n "${SKIP_DATA:-}" ]; then
    step "5/6  Evaluation data    - skipped (SKIP_DATA=1)"
else
    # --------------------------------------------------------------------------
    step "5/6  Evaluation data (paper claims 4-9)"
    # --------------------------------------------------------------------------
    if python "$HERE/artifact/plots/run_all_plots.py" --dry-run -q >/dev/null 2>&1; then
        ok "all inputs of the figure scripts are present in $HERE/data"
    else
        note "Downloading from Zenodo (https://doi.org/10.5281/zenodo.22665898)."
        note "Only the 3 archives claims 4-9 need; ~3.4 GB download, ~60 GB once unpacked."
        set +e
        "$HERE/loadData.sh" --yes
        rc=$?
        set -e
        case "$rc" in
            0) ok "downloaded and verified into $HERE/data" ;;
            *) fail "data download or verification failed (exit $rc); see zenodo/README.md." ;;
        esac
    fi
fi

# ------------------------------------------------------------------------------
step "6/6  Verifying the installation"
# ------------------------------------------------------------------------------
python -c "import numpy, pandas, matplotlib, tqdm" || fail "plotting packages are not importable."
ok "plotting packages import"
if [ -z "${SKIP_TOOL:-}" ]; then
    python - <<'PY' || fail "tool verification failed."
import os
from autopyara import AutoPYara

AutoPYara()                              # starts the JVM; fails loudly if Java is unusable
import autopyara
blooms = os.path.join(os.path.dirname(autopyara.__file__), "data", "blooms")
for flavour in ("ember", "autopyara"):
    for kind in ("benign", "malicious"):
        path = os.path.join(blooms, flavour, kind)
        assert os.path.isdir(path), f"missing Bloom filter directory: {path}"
print("    [ok] JVM started and all four Bloom filter sets are present")
PY
fi

cat <<EOF

================================================================================
Setup complete.

Run every claim (tool claims 1-3, then paper claims 4-9):

    ./run_all_claims.sh -j 8

or individual claims, e.g. the two quick checks:

    ./claims/claim1_install/run.sh                 tool installs, JVM starts   (<1 min)
    ./claims/claim4_incorrect_baselines/run.sh     first paper figure          (~10 s)

The claim scripts activate .venv themselves. See README.md for the claim list.
================================================================================
EOF
