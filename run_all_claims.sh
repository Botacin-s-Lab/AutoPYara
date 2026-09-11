#!/usr/bin/env bash
#
# Run every claim of the AutoPYara ACSAC 2026 artifact and print a PASS/FAIL table.
#
# Usage:
#   ./run_all_claims.sh              claims 1-9
#   ./run_all_claims.sh -j 8         pass "-j 8" (worker processes) to claims 4-9
#   ./run_all_claims.sh --paper      only the paper claims 4-9 (need the evaluation data)
#   ./run_all_claims.sh --tool       only the tool claims 1-3 (need Java and 16 GB RAM)
#
# Full output of each claim goes to results/logs/<claim>.log (and to the terminal).
#
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS="$HERE/results/logs"
mkdir -p "$LOGS"

FIRST=1 LAST=9 ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --paper) FIRST=4 ;;
        --tool)  LAST=3 ;;
        -j|--jobs) ARGS+=("-j" "$2"); shift ;;
        -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
    shift
done

declare -a NAMES RCS SECS
for n in $(seq "$FIRST" "$LAST"); do
    dir="$(ls -d "$HERE"/claims/claim"$n"_* 2>/dev/null | head -1)"
    [ -n "$dir" ] || { echo "claim $n not found" >&2; exit 2; }
    name="$(basename "$dir")"
    echo
    echo "################################################################################"
    echo "# $name"
    echo "################################################################################"
    start=$SECONDS
    if [ "$n" -ge 4 ]; then
        bash "$dir/run.sh" ${ARGS[@]+"${ARGS[@]}"} 2>&1 | tee "$LOGS/$name.log"
    else
        bash "$dir/run.sh" 2>&1 | tee "$LOGS/$name.log"
    fi
    RCS+=("${PIPESTATUS[0]}")
    NAMES+=("$name")
    SECS+=("$((SECONDS - start))")
done

echo
echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
failed=0
for i in "${!NAMES[@]}"; do
    if [ "${RCS[$i]}" -eq 0 ]; then verdict="PASS"; else verdict="FAIL (exit ${RCS[$i]})"; failed=$((failed + 1)); fi
    printf '  %-34s %-16s %6ss\n' "${NAMES[$i]}" "$verdict" "${SECS[$i]}"
done
echo "Logs: $LOGS"
exit $(( failed > 0 ))
