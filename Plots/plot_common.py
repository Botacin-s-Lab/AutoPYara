"""Shared plumbing for ``PlotsSet1_Boxplots.py`` and ``PlotsSet2_ThresholdPlots.py``.

Both scripts follow the same two-phase pattern:

1. **Extract** - call ``util.Extractor(csv, yar, mr, short)`` once per
   (clustering CSV, YARA rule file) pair. These calls are independent and CPU-bound
   (regex parsing of multi-MB ``.yar`` files + pandas), so they are spread over a
   pool of worker *processes* (``-j/--jobs``). Results are put back in task order,
   so the parallel run is identical to the sequential one.
2. **Plot** - the figure functions run sequentially in the main process, in the
   original order, with the original matplotlib settings.

This module holds phase 1, the default paths and the command-line options shared by
both scripts. It contains no plotting or scoring logic.
"""
import argparse
import contextlib
import io
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass

from tqdm import tqdm

PLOTS_DIR = os.path.dirname(os.path.abspath(__file__))
# The scripts historically used the relative paths '../data/...' and 'Figures/...'
# from inside Plots/. These defaults reproduce that layout from any working directory.
DEFAULT_DATA_DIR = os.path.normpath(os.path.join(PLOTS_DIR, '..', 'data'))
DEFAULT_OUT_DIR = os.path.join(PLOTS_DIR, 'Figures')

# Keep each worker process single-threaded (numexpr/BLAS pools would otherwise
# oversubscribe the CPUs). None of the extraction code uses BLAS; results are unaffected.
_THREAD_ENV_VARS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                    'NUMEXPR_NUM_THREADS')


@dataclass(frozen=True)
class Task:
    """One ``Extractor`` call.

    group: name of the dataset list the result is appended to (the variable name
           used in the original notebook-style scripts, e.g. ``df_listSSdeepRTBF``).
    csv, yar: paths relative to the data directory.
    mr: ``max_runs`` - number of rule-generation runs per cluster to average.
    short: True -> per-cluster Series (Set1); False -> size-bucketed DataFrame (Set2).
    """
    group: str
    csv: str
    yar: str
    mr: int
    short: bool


def threshold_tasks(group, csv_fmt, yar_fmt, mr, short, thresholds=(50, 60, 70, 80, 90)):
    """Tasks for the usual five similarity thresholds; ``{t}`` in the formats is the threshold."""
    return [Task(group, csv_fmt.format(t=t), yar_fmt.format(t=t), mr, short) for t in thresholds]


def available_cpus():
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:  # macOS / Windows
        return os.cpu_count() or 1


def resolve_jobs(jobs, n_tasks):
    """``jobs`` <= 0 means all available CPUs; never more workers than tasks."""
    if not jobs or jobs <= 0:
        jobs = available_cpus()
    return max(1, min(jobs, n_tasks))


def _extract(csv_path, yar_path, mr, short, quiet):
    """Worker entry point (module-level so it can be pickled for the process pool)."""
    from util import Extractor
    if not quiet:
        return Extractor(csv_path, yar_path, mr=mr, short=short)
    with contextlib.redirect_stdout(io.StringIO()):
        return Extractor(csv_path, yar_path, mr=mr, short=short)


def missing_inputs(tasks, data_dir):
    seen, missing = set(), []
    for t in tasks:
        for rel in (t.csv, t.yar):
            if rel not in seen:
                seen.add(rel)
                if not os.path.isfile(os.path.join(data_dir, rel)):
                    missing.append(rel)
    return missing


def run_tasks(tasks, data_dir, jobs=0, quiet=False, desc='Extracting'):
    """Run every task's ``Extractor`` call; return results in the order of ``tasks``.

    jobs == 1 runs in-process, one task after another (the original behaviour);
    otherwise a spawn-based process pool is used. Largest ``.yar`` files are
    submitted first so the slowest tasks don't end up alone at the tail.
    """
    jobs = resolve_jobs(jobs, len(tasks))
    calls = [(os.path.join(data_dir, t.csv), os.path.join(data_dir, t.yar), t.mr, t.short, quiet)
             for t in tasks]
    results = [None] * len(tasks)
    bar = tqdm(total=len(tasks), unit='file', desc=f'{desc} [{jobs} worker{"s" * (jobs > 1)}]')
    if jobs == 1:
        for i, call in enumerate(calls):
            results[i] = _extract(*call)
            bar.update()
    else:
        for var in _THREAD_ENV_VARS:
            os.environ.setdefault(var, '1')  # inherited by the spawned workers
        order = sorted(range(len(calls)), key=lambda i: -os.path.getsize(calls[i][1]))
        # 'spawn' behaves the same on Linux, macOS and Windows and avoids forking a
        # process that has already imported matplotlib.
        with ProcessPoolExecutor(max_workers=jobs, mp_context=mp.get_context('spawn')) as pool:
            futures = {pool.submit(_extract, *calls[i]): i for i in order}
            for fut in as_completed(futures):
                results[futures[fut]] = fut.result()
                bar.update()
    bar.close()
    return results


def group_results(tasks, results):
    """{group: [result, ...]} with each list in task order (i.e. threshold order)."""
    datasets = {}
    for task, result in zip(tasks, results):
        datasets.setdefault(task.group, []).append(result)
    return datasets


def build_arg_parser(description):
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-j', '--jobs', '--cores', type=int, default=0, metavar='N',
                        help='worker processes for the extraction phase '
                             '(0 = all available CPUs [default]; 1 = sequential, in-process)')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='root holding clusterCSV/ and ruleEval/ (default: %(default)s)')
    parser.add_argument('--out-dir', default=DEFAULT_OUT_DIR,
                        help='where the Claim*/ figure folders are written (default: %(default)s)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="hide util.py's per-file/per-rule diagnostic prints")
    parser.add_argument('--dry-run', action='store_true',
                        help='list the extraction tasks, check that every input exists, and exit')
    return parser


def script_main(description, tasks, make_figures, argv=None):
    """Shared ``main()``: parse args, preflight inputs, extract in parallel, plot.

    ``make_figures(datasets, out_dir)`` receives ``group_results(...)`` and must
    return the list of PDF paths it wrote.
    """
    args = build_arg_parser(description).parse_args(argv)
    missing = missing_inputs(tasks, args.data_dir)
    if args.dry_run:
        for t in tasks:
            print(f'{t.group:34s} mr={t.mr:<2d} short={t.short!s:5s} {t.csv}  {t.yar}')
        print(f'{len(tasks)} tasks, data dir {args.data_dir}, {len(missing)} missing inputs')
    for rel in missing:
        print(f'MISSING INPUT: {os.path.join(args.data_dir, rel)}', file=sys.stderr)
    if missing:
        return 2
    if args.dry_run:
        return 0

    import matplotlib.pyplot as plt
    plt.switch_backend('Agg')  # figures are only saved, never shown

    t0 = time.perf_counter()
    results = run_tasks(tasks, args.data_dir, args.jobs, args.quiet)
    t1 = time.perf_counter()
    written = make_figures(group_results(tasks, results), args.out_dir)
    t2 = time.perf_counter()
    print(f'extraction {t1 - t0:.1f}s, plotting {t2 - t1:.1f}s; wrote {len(written)} figures:')
    for path in written:
        print(f'  {path}')
    return 0
