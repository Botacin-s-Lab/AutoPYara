#!/usr/bin/env python3
"""Regenerate the figures behind one paper claim and verify them (artifact claims 4-9).

For artifact claim N (= paper claim N-3) this script

  1. regenerates the claim's figures from the evaluation data with run_all_plots.py
     (into results/<claim>/ unless --out-dir is given);
  2. compares every plotted number with the reference values in
     claims/<claim>/expected/values.json, within TOL percentage points;
  3. checks the claim's statements (claims/<claim>/claim.txt) on the regenerated
     numbers;
  4. prints "CLAIM N: PASS" or "CLAIM N: FAIL" and exits 0 or 1.

Usage:
  verify_claims.py N [-j JOBS] [--data-dir DIR] [--out-dir DIR] [--no-run]
  verify_claims.py N --update-expected --from DIR     (authors: refresh claims/<claim>/expected
                                                       from a verified run in DIR)
"""
import argparse
import glob
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from plot_common import DEFAULT_DATA_DIR  # noqa: E402

TOL = 1.0  # percentage points; a correct run deviates by 0.00
LABELS = ('SSdeep', 'J-SDhash', 'VirusTotal')
THRESHOLDS = (50, 60, 70, 80, 90)
TOOL_BY_COLOR = {'#9467bd': 'AutoPYara', '#8c564b': 'AutoYara'}  # Set 3 line colours

C1, C2, C3 = 'Claim1_IncorrectBaseLines/', 'Claim2_BloomFiltersMatter/', 'Claim3_YaraVsPYara/'
C4, C5, C6 = 'Claim4_ThresHoldFigures/', 'Claim5_Threathunting/', 'Claim6_YaraInAllitsConfigurations/'
FIG7 = {  # claim 7: configuration -> figure
    'AutoYara': 'AutoYara_SSdeepAVG_ZoomRTBF.pdf',
    'AutoPYara': 'AutoPYara_SSdeepAVG_ZoomRTBF.pdf',
    'best K': 'AutoPYaraBestK_SSdeepAVG_ZoomRTBF.pdf',
    'worst K': 'AutoPYaraWorstK_SSdeepAVG_ZoomRTBF.pdf',
    'informed mode K': 'AutoPYaraHEUModeK_SSdeepAVG_ZoomRTBF.pdf',
    'informed max K': 'AutoPYaraHEUMaxK_SSdeepAVG_ZoomRTBF.pdf',
    'informed random K': 'AutoPYaraHEURandomK_SSdeepAVG_ZoomRTBF.pdf',
    'uninformed mean K': 'AutoPYaraUninformedHEUMeanK_SSdeepAVG_ZoomRTBF.pdf',
    'uninformed max K': 'AutoPYaraUninformedHEUMaxK_SSdeepAVG_ZoomRTBF.pdf',
    'uninformed random K': 'AutoPYaraUninformedHEURandomK_SSdeepAVG_ZoomRTBF.pdf',
}


# --------------------------------------------------------------------------------------
# Readers of the recorded values (<script>.values.json, see plot_common.plotted_data)
# --------------------------------------------------------------------------------------
def bar_series(values, fig, series):
    """{bar label: height} of one bar series of a SSdeep/J-SDhash/VirusTotal chart."""
    ax = values[fig][0]
    return dict(zip([label for _, label in ax['xticks']], ax['bars'][series]['height']))


def curve_means(values, fig):
    """{threshold: mean of that threshold's curve} (the dotted line after each curve)."""
    lines = values[fig][0]['lines']
    return {int(line['label'].split()[1]): lines[i + 1]['y'][0]
            for i, line in enumerate(lines)
            if line['label'].startswith('Threshold ') and i + 1 < len(lines)}


def hunting_means(values, fig):
    """{(tool, 'train' | 'test'): curve mean} of a mirrored threat-hunting figure."""
    lines = values[fig][0]['lines']
    out = {}
    for i, line in enumerate(lines):
        if len(line['x']) > 2 and i + 1 < len(lines) and line['color'] in TOOL_BY_COLOR:
            side = 'train' if sum(line['x']) < 0 else 'test'
            out[(TOOL_BY_COLOR[line['color']], side)] = lines[i + 1]['y'][0]
    return out


def ladder_totals(values, fig):
    """{bar label: base + red stacked segment} of the ladder chart."""
    out = {}
    for ax in values[fig]:
        if not ax['bars']:
            continue
        names = {round(x, 6): label for x, label in ax['xticks']}
        base = ax['bars'][0]
        fills = {round(b['x'][0], 6): b['height'][0] for b in ax['bars'][1:]}
        for x, h in zip(base['x'], base['height']):
            out[names[round(x, 6)]] = h + fills.get(round(x, 6), 0.0)
    return out


# --------------------------------------------------------------------------------------
# Claim statements (each returns printable rows and a list of (statement, holds))
# --------------------------------------------------------------------------------------
def check_4(v):
    nonzero = bar_series(v, C1 + 'AutoYara_baselineBoxPlotEMBF.pdf', 0)
    allc = bar_series(v, C1 + 'AutoYara_EMBF.pdf', 0)
    rows = [f'{lab:10s}  non-zero clusters {nonzero[lab]:6.2f} %   all clusters {allc[lab]:6.2f} %'
            f'   gap {nonzero[lab] - allc[lab]:6.2f} pp' for lab in LABELS]
    checks = [(f'{lab}: all-cluster mean is >= 30 pp below the non-zero-cluster mean',
               nonzero[lab] - allc[lab] >= 30) for lab in LABELS]
    return rows, checks


def check_5(v):
    ay_fig = C2 + 'AutoYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf'
    apy_fig = C2 + 'AutoPYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf'
    data = {  # tool -> (Ember, retrained); the two figures draw them in opposite order
        'AutoYara': (bar_series(v, ay_fig, 0), bar_series(v, ay_fig, 1)),
        'AutoPYara': (bar_series(v, apy_fig, 1), bar_series(v, apy_fig, 0)),
    }
    rows, checks = [], []
    for tool, (ember, retrained) in data.items():
        for lab in LABELS:
            gain = retrained[lab] - ember[lab]
            rows.append(f'{tool:9s} {lab:10s}  Ember {ember[lab]:6.2f} %  ->  retrained '
                        f'{retrained[lab]:6.2f} %   ({gain:+6.2f} pp)')
            checks.append((f'{tool} {lab}: retrained filters beat Ember filters', gain > 0))
            if lab != 'VirusTotal':
                checks.append((f'{tool} {lab}: gain is at least 50 pp', gain >= 50))
    return rows, checks


def check_6(v):
    fig = C3 + 'AutoYaraVSAutoPYaraRTBF.pdf'
    apy, ay = bar_series(v, fig, 0), bar_series(v, fig, 1)
    rows = [f'{lab:10s}  AutoPYara {apy[lab]:6.2f} %   AutoYara {ay[lab]:6.2f} %'
            f'   ({apy[lab] - ay[lab]:+5.2f} pp)' for lab in LABELS]
    checks = [(f'{lab}: AutoPYara > AutoYara', apy[lab] > ay[lab]) for lab in LABELS]
    return rows, checks


def check_7(v):
    m = {name: curve_means(v, C4 + fig) for name, fig in FIG7.items()}
    rows = ['threshold            ' + ''.join(f'{t:>8d}' for t in THRESHOLDS)]
    rows += [f'{name:20s} ' + ''.join(f'{m[name][t]:8.2f}' for t in THRESHOLDS) for name in FIG7]
    informed = [n for n in FIG7 if n.startswith('informed')]
    uninformed = [n for n in FIG7 if n.startswith('uninformed')]
    checks = [
        ('a. AutoPYara > AutoYara at every threshold',
         all(m['AutoPYara'][t] > m['AutoYara'][t] for t in THRESHOLDS)),
        ('b. best K > AutoPYara > worst K at every threshold',
         all(m['best K'][t] > m['AutoPYara'][t] > m['worst K'][t] for t in THRESHOLDS)),
        ('c. every informed heuristic > AutoYara at every threshold',
         all(m[n][t] > m['AutoYara'][t] for n in informed for t in THRESHOLDS)),
        ('d. every uninformed heuristic < AutoYara at every threshold',
         all(m[n][t] < m['AutoYara'][t] for n in uninformed for t in THRESHOLDS)),
    ]
    return rows, checks


def check_8(v):
    rows, checks = [], []
    for name, fig in (('with heuristics only', 'sdhash_WithHeuOnly_IdealPlot.pdf'),
                      ('without heuristics', 'sdhash_WithNOHeuOnly_IdealPlot.pdf'),
                      ('real-world stream', 'sdhash_RealWorldStream_PHeuPlot.pdf')):
        h = hunting_means(v, C5 + fig)
        rows.append(f'{name:21s} train: AutoPYara {h["AutoPYara", "train"]:6.2f} %  AutoYara '
                    f'{h["AutoYara", "train"]:6.2f} %   test: AutoPYara {h["AutoPYara", "test"]:6.2f} %'
                    f'  AutoYara {h["AutoYara", "test"]:6.2f} %')
        checks.append((f'{name}: AutoPYara > AutoYara on held-out test samples',
                       h['AutoPYara', 'test'] > h['AutoYara', 'test']))
    return rows, checks


def check_9(v):
    tot = ladder_totals(v, C6 + 'BigPicutre.pdf')
    ranked = sorted(tot, key=tot.get)
    rows = [f'{i:2d}. {label!r:15s} {tot[label]:6.2f} %' for i, label in enumerate(ranked, 1)]
    chain = ['AY EBF', 'AY RTBF', 'APY OH: M', 'APY B', 'APY B WF']
    checks = [
        ('the two Ember-filter bars (AY EBF, APY EBF) are the lowest, both below 20 %',
         set(ranked[:2]) == {'AY EBF', 'APY EBF'} and max(tot['AY EBF'], tot['APY EBF']) < 20),
        ('AutoYara reality < AutoYara configured < AutoPYara reality < AutoPYara best K <= ideal case',
         all(tot[a] < tot[b] for a, b in zip(chain[:-2], chain[1:-1])) and tot['APY B'] <= tot['APY B WF']),
        ("the ideal case ('APY B WF') is the highest of the 15 bars", ranked[-1] == 'APY B WF'),
    ]
    return rows, checks


CLAIMS = {
    4: dict(dir='claim4_incorrect_baselines', paper=1, set='set1', check=check_4,
            title="AutoYara's baseline numbers hide the clusters it fails on",
            figures=[C1 + 'AutoYara_baselineBoxPlotEMBF.pdf', C1 + 'AutoYara_EMBF.pdf']),
    5: dict(dir='claim5_bloom_filters_matter', paper=2, set='set1', check=check_5,
            title='the Bloom filters matter',
            figures=[C2 + 'AutoYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf',
                     C2 + 'AutoPYara_EmberBloomFiltersVSRetrainedBloomfilters.pdf']),
    6: dict(dir='claim6_autopyara_vs_autoyara', paper=3, set='set1', check=check_6,
            title='AutoPYara outperforms AutoYara', figures=[C3 + 'AutoYaraVSAutoPYaraRTBF.pdf']),
    7: dict(dir='claim7_thresholds_and_k', paper=4, set='set2', check=check_7,
            title='similarity threshold and choice of K', figures=[C4 + f for f in FIG7.values()]),
    8: dict(dir='claim8_threat_hunting', paper=5, set='set3', check=check_8,
            title='threat hunting on held-out samples',
            figures=[C5 + 'sdhash_WithHeuOnly_IdealPlot.pdf', C5 + 'sdhash_WithNOHeuOnly_IdealPlot.pdf',
                     C5 + 'sdhash_RealWorldStream_PHeuPlot.pdf']),
    9: dict(dir='claim9_all_configurations', paper=6, set='set4', check=check_9,
            title='AutoYara and AutoPYara in all their configurations', figures=[C6 + 'BigPicutre.pdf']),
}


# --------------------------------------------------------------------------------------
# Comparison with the reference values
# --------------------------------------------------------------------------------------
def load_values(directory):
    values = {}
    for path in sorted(glob.glob(os.path.join(directory, '*.values.json'))):
        with open(path) as fh:
            values.update(json.load(fh))
    return values


def compare(actual, expected, tol):
    """Compare plotted numbers figure by figure. Returns (count, max deviation, problems)."""
    count, worst, problems = 0, 0.0, []

    def number(a, b, where):
        nonlocal count, worst
        count += 1
        if a != a and b != b:  # both NaN
            return
        dev = abs(a - b) if (a == a and b == b) else math.inf
        worst = max(worst, dev)
        if dev > tol:
            problems.append(f'{where}: {a:.4f} vs reference {b:.4f}')

    def numbers(a, b, where):
        if len(a) != len(b):
            problems.append(f'{where}: {len(a)} values vs {len(b)} in the reference')
            return
        for i, (x, y) in enumerate(zip(a, b)):
            number(x, y, f'{where}[{i}]')

    for fig, ref_axes in expected.items():
        if fig not in actual:
            problems.append(f'{fig}: not regenerated')
            continue
        act_axes = actual[fig]
        if len(act_axes) != len(ref_axes):
            problems.append(f'{fig}: {len(act_axes)} panels vs {len(ref_axes)} in the reference')
            continue
        for k, (act, ref) in enumerate(zip(act_axes, ref_axes)):
            where = f'{fig} panel {k}'
            if [lab for _, lab in act['xticks']] != [lab for _, lab in ref['xticks']]:
                problems.append(f'{where}: bar labels differ')
            if len(act['bars']) != len(ref['bars']) or len(act['lines']) != len(ref['lines']):
                problems.append(f'{where}: different number of bar series or lines')
                continue
            for j, (ab, rb) in enumerate(zip(act['bars'], ref['bars'])):
                for key in ('x', 'bottom', 'height'):
                    numbers(ab[key], rb[key], f'{where} bars{j}.{key}')
                if rb['err'] is not None:
                    numbers(ab['err'] or [], rb['err'], f'{where} bars{j}.err')
            for j, (al, rl) in enumerate(zip(act['lines'], ref['lines'])):
                numbers(al['x'], rl['x'], f'{where} line{j}.x')
                numbers(al['y'], rl['y'], f'{where} line{j}.y')
    return count, worst, problems


# --------------------------------------------------------------------------------------
def update_expected(claim, src):
    exp_dir = os.path.join(REPO, 'claims', claim['dir'], 'expected')
    values = load_values(src)
    missing = [f for f in claim['figures'] if f not in values]
    if missing:
        sys.exit(f'{src} lacks: {missing}')
    os.makedirs(exp_dir, exist_ok=True)
    with open(os.path.join(exp_dir, 'values.json'), 'w') as fh:
        json.dump({f: values[f] for f in claim['figures']}, fh, indent=1)
    for fig in claim['figures']:
        dest = os.path.join(exp_dir, 'figures', fig)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(os.path.join(src, fig), dest)
    print(f'updated {exp_dir} from {src}')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('claim', type=int, choices=sorted(CLAIMS), help='artifact claim number (4-9)')
    ap.add_argument('-j', '--jobs', '--cores', type=int, default=0, metavar='N',
                    help='worker processes for the regeneration (0 = all CPUs, default)')
    ap.add_argument('--data-dir', default=DEFAULT_DATA_DIR, help='evaluation data (default: %(default)s)')
    ap.add_argument('--out-dir', help='where to regenerate the figures (default: results/<claim>)')
    ap.add_argument('--no-run', action='store_true', help='verify figures already in --out-dir')
    ap.add_argument('--update-expected', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--from', dest='from_dir', help=argparse.SUPPRESS)
    args = ap.parse_args()

    claim = CLAIMS[args.claim]
    if args.update_expected:
        return update_expected(claim, args.from_dir)

    out_dir = os.path.abspath(args.out_dir or os.path.join(REPO, 'results', claim['dir']))
    exp_dir = os.path.join(REPO, 'claims', claim['dir'], 'expected')
    bar = '=' * 80
    print(bar)
    print(f"CLAIM {args.claim} (paper claim {claim['paper']}) - {claim['title']}")
    print(bar)

    failures = []

    def report(ok, label, detail=''):
        print(f"  [{'ok' if ok else 'FAIL'}]{' ' if ok else ''} {label}" + (f' -- {detail}' if detail else ''))
        if not ok:
            failures.append(label)

    if not args.no_run:
        print(f"\n1. Regenerating the figures ({claim['set']}) into {out_dir}")
        cmd = [sys.executable, os.path.join(HERE, 'run_all_plots.py'), '--only', claim['set'],
               '-j', str(args.jobs), '--data-dir', os.path.abspath(args.data_dir), '--out-dir', out_dir,
               '-q', '--log-dir', os.path.join(out_dir, 'logs')]
        rc = subprocess.run(cmd).returncode
        report(rc == 0, 'figures regenerated from the evaluation data',
               'ok' if rc == 0 else f'run_all_plots.py exited {rc}; see {out_dir}/logs')
        if rc != 0:
            print(f"\n{bar}\nCLAIM {args.claim}: FAIL -- the figures could not be regenerated\n{bar}")
            return 1

    print('\n2. Figures')
    for fig in claim['figures']:
        path = os.path.join(out_dir, fig)
        report(os.path.isfile(path), fig, 'written' if os.path.isfile(path) else f'missing: {path}')

    print(f'\n3. Plotted numbers vs. the reference (expected/values.json, tolerance {TOL} pp)')
    with open(os.path.join(exp_dir, 'values.json')) as fh:
        expected = json.load(fh)
    count, worst, problems = compare(load_values(out_dir), expected, TOL)
    report(not problems, f'{count} plotted numbers match the reference',
           f'max deviation {worst:.2g}' if not problems else f'{len(problems)} mismatch(es)')
    for p in problems[:10]:
        print(f'         {p}')

    print('\n4. Claim statements, on the regenerated numbers')
    try:
        rows, checks = claim['check'](load_values(out_dir))
    except (KeyError, IndexError) as exc:
        rows, checks = [], [('the claim numbers could be read from the figures', False)]
        print(f'         could not read {exc}')
    for row in rows:
        print(f'     {row}')
    for label, ok in checks:
        report(ok, label)

    print(f'\n{bar}')
    if failures:
        print(f"CLAIM {args.claim}: FAIL -- {len(failures)} check(s) failed")
    else:
        print(f"CLAIM {args.claim}: PASS -- paper claim {claim['paper']} reproduced from the provided data")
    print(bar)
    print(f'Figures: {out_dir}   Reference: {exp_dir}/figures')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
