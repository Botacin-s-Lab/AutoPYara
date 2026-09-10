#!/usr/bin/env python3
"""Master runner: regenerate every paper figure from the provided YARA rule sets.

Runs, one after the other and each in its own Python process:
  1. PlotsSet1_Boxplots.py        -> Figures/Claim1_*, Claim2_*, Claim3_*   (5 PDFs)
  2. PlotsSet2_ThresholdPlots.py  -> Figures/Claim4_ThresHoldFigures/      (10 PDFs)

Inside each script the rule-file parsing (the slow part) is spread over ``--jobs``
worker processes; plotting itself is quick and sequential. Separate processes keep
each script's matplotlib settings isolated, exactly as when run by hand.

Examples:
  python run_all_plots.py                 # all CPUs
  python run_all_plots.py -j 8            # 8 worker processes
  python run_all_plots.py -j 1            # fully sequential
  python run_all_plots.py --only set2     # just the Claim 4 figures
  python run_all_plots.py --dry-run       # list inputs, check they exist, run nothing
  python run_all_plots.py -q --log-dir logs   # quiet; full output of each script in logs/

Memory: each worker holds one rule file (largest ~95 MB on disk) plus its parsed
form, i.e. a few hundred MB at peak; lower ``-j`` on small machines.
Requirements: numpy, pandas, matplotlib, tqdm (tested with Python 3.13, numpy 1.26,
pandas 2.2, matplotlib 3.10).
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from plot_common import DEFAULT_DATA_DIR, DEFAULT_OUT_DIR, available_cpus  # noqa: E402

SCRIPTS = {
    'set1': 'PlotsSet1_Boxplots.py',
    'set2': 'PlotsSet2_ThresholdPlots.py',
}


def check_requirements():
    missing = []
    for mod in ('numpy', 'pandas', 'matplotlib', 'tqdm'):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        sys.exit(f'Missing Python packages: {", ".join(missing)}  (pip install {" ".join(missing)})')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-j', '--jobs', '--cores', type=int, default=0, metavar='N',
                        help=f'worker processes per script (0 = all available CPUs '
                             f'[{available_cpus()} here], default 0; 1 = sequential)')
    parser.add_argument('--only', nargs='+', choices=list(SCRIPTS), default=list(SCRIPTS),
                        help='run only these figure sets (default: both)')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='root holding clusterCSV/ and ruleEval/ (default: %(default)s)')
    parser.add_argument('--out-dir', default=DEFAULT_OUT_DIR,
                        help='figure output root (default: %(default)s)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="hide util.py's per-file/per-rule diagnostic prints")
    parser.add_argument('--log-dir', metavar='DIR',
                        help="write each script's full output to DIR/<script>.log instead of the terminal")
    parser.add_argument('--dry-run', action='store_true',
                        help='list every input file each script needs, check they exist, and exit')
    args = parser.parse_args(argv)

    check_requirements()
    if args.log_dir:
        os.makedirs(args.log_dir, exist_ok=True)
    env = dict(os.environ)
    env.setdefault('MPLBACKEND', 'Agg')
    jobs = args.jobs if args.jobs > 0 else available_cpus()
    print(f'Running {", ".join(args.only)} with {jobs} worker process(es) each; '
          f'data: {args.data_dir}; figures: {args.out_dir}', flush=True)

    summary = []
    for name in args.only:
        script = SCRIPTS[name]
        cmd = [sys.executable, os.path.join(HERE, script), '--jobs', str(jobs),
               '--data-dir', args.data_dir, '--out-dir', args.out_dir]
        cmd += ['--quiet'] * args.quiet + ['--dry-run'] * args.dry_run
        print(f'\n=== {script} ===', flush=True)
        t0 = time.perf_counter()
        if args.log_dir:
            log_path = os.path.join(args.log_dir, f'{os.path.splitext(script)[0]}.log')
            with open(log_path, 'w') as log:
                rc = subprocess.run(cmd, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
            print(f'output: {log_path}')
        else:
            rc = subprocess.run(cmd, cwd=HERE, env=env).returncode
        summary.append((script, rc, time.perf_counter() - t0))

    print('\n=== summary ===')
    for script, rc, secs in summary:
        print(f'{script:30s} {"OK" if rc == 0 else f"FAILED (exit {rc})":18s} {secs:8.1f}s')
    if not args.dry_run and os.path.isdir(args.out_dir):
        pdfs = sorted(os.path.relpath(os.path.join(root, f), args.out_dir)
                      for root, _, files in os.walk(args.out_dir) for f in files if f.endswith('.pdf'))
        print(f'{len(pdfs)} PDFs under {args.out_dir}:')
        for p in pdfs:
            print(f'  {p}')
    return 0 if all(rc == 0 for _, rc, _ in summary) else 1


if __name__ == '__main__':
    sys.exit(main())
