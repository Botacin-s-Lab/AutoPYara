#!/usr/bin/env bash
#
# Download and unpack the AutoPYara ACSAC 2026 evaluation data from Zenodo
# (https://doi.org/10.5281/zenodo.22665898) into data/.
#
# By default this fetches only the THREE archives the artifact evaluation
# (claims 4-9) actually reads: AutoPYaraClusters.zip, ProcessedRules.zip and
# ThreatHunting.zip. yaraRules.zip is NOT one of them -- it's the complete,
# unmerged rule set (10M+ files); the scripts only ever read the smaller,
# merged/annotated rules in ProcessedRules.zip. See zenodo/README.md for the
# full breakdown of every archive.
#
# WARNING: this takes a while and the unzipped data is dramatically bigger
# than the download. Measured against the actual archives:
#
#     archive                 download   unzips to        notes
#     ----------------------  ---------  ---------------  ------------------
#     AutoPYaraClusters.zip   2.60 GB    ~8.2 GB
#     ProcessedRules.zip      726 MB     ~49.7 GB          737 files
#     ThreatHunting.zip       68 MB      ~112 MB           110,000+ files
#     (--all only, below)
#     yaraRules.zip           5.17 GB    ~6 GB on paper,   10.2 MILLION files;
#                                        ~43 GB on disk    counts against disk
#                                                          quotas/inodes too
#     RawDataWithSimilarityHashes.zip  9.69 GB  unknown, likely large
#     EmberBloomFliters.zip            108 MB   comparable to download
#     AutoPYaraBloomFliters.zip        107 MB   comparable to download
#
# So the *default* (AE-only) run needs roughly 3.4 GB of download and about
# 58 GB of free disk once unpacked; --all needs a good deal more (tens of GB
# more download, 100+ GB unpacked, and 10M+ extra inodes) and can take hours
# on a slow connection or disk.
#
# Usage:
#   ./loadData.sh                  # AE mode (default): the 3 required archives
#   ./loadData.sh --all            # also fetch the 4 supplementary archives
#   ./loadData.sh --data-dir DIR   # unpack into DIR instead of ./data
#   ./loadData.sh --yes            # skip the confirmation prompt
#   ./loadData.sh --force          # re-download/re-extract even if already done
#   ./loadData.sh --keep-download  # don't delete the .zip after a successful extract
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECORD_ID=22665898
API_BASE="https://zenodo.org/api/records/${RECORD_ID}/files"

DATA_DIR="$HERE/data"
MODE=ae
ASSUME_YES=0
FORCE=0
KEEP_DOWNLOAD=0

note()  { printf '    %s\n' "$*"; }
step()  { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
fail()  { printf '    [FAIL] %s\n' "$*" >&2; exit 1; }

usage() {
  sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --all) MODE=all ;;
    --data-dir) DATA_DIR="$2"; shift ;;
    --yes|-y) ASSUME_YES=1 ;;
    --force) FORCE=1 ;;
    --keep-download) KEEP_DOWNLOAD=1 ;;
    -h|--help) usage 0 ;;
    *) echo "Unknown option: $1" >&2; usage 1 ;;
  esac
  shift
done

for cmd in curl unzip md5sum; do
  command -v "$cmd" >/dev/null 2>&1 || fail "$cmd is required but not found on PATH."
done

# name | compressed size | md5 | ae|all | unzipped size (informational only)
ARCHIVES='
AutoPYaraClusters.zip|2.60 GB|62d60a1757005bc9268e37f35511edf8|ae|~8.2 GB
ProcessedRules.zip|726.47 MB|a3b456b76f9f9cdd88179e10280a4241|ae|~49.7 GB
ThreatHunting.zip|67.76 MB|1181a15e44d40e19790706e8b867b737|ae|~112 MB, 110k+ files
RawDataWithSimilarityHashes.zip|9.69 GB|1698556a179db33fc9a2a056d08e720c|all|unknown, likely large
yaraRules.zip|5.17 GB|223d10dad36e9732333357bc169b92bf|all|~43 GB on disk, 10.2M files
EmberBloomFliters.zip|107.69 MB|a36dbbdc2801f7d8e699c0323e9c0b79|all|comparable to download
AutoPYaraBloomFliters.zip|107.30 MB|de3fe6f533693a1d9f1d1bb37bfea847|all|comparable to download
'

selected=()
while IFS='|' read -r name size md5 tag unzipped; do
  [ -z "$name" ] && continue
  if [ "$tag" = ae ] || [ "$MODE" = all ]; then
    selected+=("$name|$size|$md5|$unzipped")
  fi
done <<< "$ARCHIVES"

step "AutoPYara evaluation data (Zenodo record ${RECORD_ID}, https://doi.org/10.5281/zenodo.${RECORD_ID})"
note "Mode: $MODE  ->  ${#selected[@]} archive(s) into $DATA_DIR"
note ""
printf '    %-34s %10s   %s\n' "archive" "download" "unzips to (approx.)"
for entry in "${selected[@]}"; do
  IFS='|' read -r name size md5 unzipped <<< "$entry"
  printf '    %-34s %10s   %s\n' "$name" "$size" "$unzipped"
done
note ""
note "This downloads several GB and takes real time on a slow link; unzipping"
note "takes real time too, especially for archives with huge file counts"
note "(ProcessedRules.zip alone unpacks to roughly 50 GB from a 726 MB"
note "download; --all's yaraRules.zip unpacks to over 10 million files)."
if [ "$MODE" = ae ]; then
  note "This is AE mode: only the 3 archives claims 4-9 actually read. Use"
  note "--all to also fetch the 4 supplementary archives (not needed to"
  note "reproduce any figure) -- see zenodo/README.md."
fi

if [ "$ASSUME_YES" != 1 ]; then
  printf '\nProceed? [y/N] '
  read -r reply
  case "$reply" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
fi

mkdir -p "$DATA_DIR"
MARK_DIR="$DATA_DIR/.loadData"
mkdir -p "$MARK_DIR"

for entry in "${selected[@]}"; do
  IFS='|' read -r name size md5 unzipped <<< "$entry"
  zip_path="$DATA_DIR/$name"
  mark="$MARK_DIR/$name.done"

  step "$name ($size)"

  if [ "$FORCE" != 1 ] && [ -f "$mark" ] && [ "$(cat "$mark" 2>/dev/null)" = "$md5" ]; then
    note "already downloaded and extracted (matches recorded md5) -- skipping. Use --force to redo."
    continue
  fi

  if [ "$FORCE" = 1 ] || [ ! -f "$zip_path" ] || [ "$(md5sum "$zip_path" | cut -d' ' -f1)" != "$md5" ]; then
    note "downloading from $API_BASE/$name/content ..."
    curl -fL --progress-bar -o "$zip_path" "$API_BASE/$name/content" \
      || fail "download failed for $name"
  else
    note "$zip_path already present and verified -- skipping download."
  fi

  note "verifying md5 ..."
  actual_md5="$(md5sum "$zip_path" | cut -d' ' -f1)"
  [ "$actual_md5" = "$md5" ] || fail "$name: md5 mismatch (got $actual_md5, expected $md5) -- delete and re-run."

  note "unzipping into $DATA_DIR ..."
  unzip -q -o "$zip_path" -d "$DATA_DIR" || fail "unzip failed for $name"

  echo "$md5" > "$mark"

  if [ "$KEEP_DOWNLOAD" != 1 ]; then
    rm -f "$zip_path"
    note "removed $name after a verified extract (pass --keep-download to keep zips)."
  fi
done

step "Done"
note "Data is in $DATA_DIR. See zenodo/README.md for what each archive contains"
note "and artifact/plots/README.md for the exact data/ layout the figures read."
if [ "$MODE" = ae ]; then
  note "Next: ./install.sh (if you haven't already), then e.g."
  note "  ./claims/claim4_incorrect_baselines/run.sh -j 8"
fi
