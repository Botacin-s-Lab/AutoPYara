"""Shared plumbing for the ``PlotsSet*.py`` figure scripts.

Every script follows the same two-phase pattern:

1. **Extract** - one independent, CPU/IO-bound call per input (typically
   ``util.Extractor(csv, yar, mr, short)`` on a multi-MB ``.yar`` file). These calls
   are spread over a pool of worker *processes* (``-j/--jobs``). Results are put back
   in task order, so a parallel run is identical to a sequential one.
2. **Plot** - the figure functions run sequentially in the main process, in the
   original order, with the original matplotlib settings.

While plotting, every saved figure's drawn numbers (bar heights, error bars, line
data, labels, texts) are recorded to ``<out-dir>/<script>.values.json``. The claim
checks in ``verify_claims.py`` compare those numbers with the reference values.

This module holds phase 1, the recording, the default paths and the command-line
options shared by all scripts. It contains no plotting or scoring logic.
"""
import argparse
import contextlib
import io
import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

from tqdm import tqdm

PLOTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(PLOTS_DIR))  # artifact/plots -> repository root
# Evaluation data (see artifact/download_data.py); override with AUTOPYARA_DATA_DIR or --data-dir.
DEFAULT_DATA_DIR = os.environ.get('AUTOPYARA_DATA_DIR') or os.path.join(REPO_ROOT, 'data')
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, 'results', 'figures')

# Keep each worker process single-threaded (numexpr/BLAS pools would otherwise
# oversubscribe the CPUs). None of the extraction code uses BLAS; results are unaffected.
_THREAD_ENV_VARS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                    'NUMEXPR_NUM_THREADS')


def _extract(csv_path, yar_path, mr, short, quiet):
    """Worker entry point for ``Task`` (module-level so it can be pickled)."""
    from util import Extractor
    if not quiet:
        return Extractor(csv_path, yar_path, mr=mr, short=short)
    with contextlib.redirect_stdout(io.StringIO()):
        return Extractor(csv_path, yar_path, mr=mr, short=short)


def _call(fn, paths, quiet):
    """Worker entry point for ``PathTask``."""
    if not quiet:
        return fn(*paths)
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*paths)


@dataclass(frozen=True)
class Task:
    """One ``util.Extractor`` call.

    group: name of the dataset list the result is appended to (the variable name
           used in the original notebook-style scripts, e.g. ``df_listSSdeepRTBF``).
    csv, yar: paths relative to the data directory.
    mr: ``max_runs`` - number of rule-generation runs per cluster to average.
    short: True -> per-cluster Series; False -> size-bucketed DataFrame.
    """
    group: str
    csv: str
    yar: str
    mr: int
    short: bool

    @property
    def inputs(self):
        return (self.csv, self.yar)

    def call(self, data_dir, quiet):
        return _extract, (os.path.join(data_dir, self.csv), os.path.join(data_dir, self.yar),
                          self.mr, self.short, quiet)

    def describe(self):
        return f'{self.group:34s} mr={self.mr:<2d} short={self.short!s:5s} {self.csv}  {self.yar}'


@dataclass(frozen=True)
class PathTask:
    """One ``fn(*absolute_paths)`` call, for inputs that ``Extractor`` doesn't handle.

    fn: a module-level function (it is pickled by reference for the workers).
    paths: files or directories, relative to the data directory.
    """
    group: str
    fn: Callable
    paths: tuple

    @property
    def inputs(self):
        return self.paths

    def call(self, data_dir, quiet):
        return _call, (self.fn, tuple(os.path.join(data_dir, p) for p in self.paths), quiet)

    def describe(self):
        return f'{self.group:34s} {self.fn.__name__}({", ".join(self.paths)})'


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


def missing_inputs(tasks, data_dir):
    seen, missing = set(), []
    for t in tasks:
        for rel in t.inputs:
            if rel not in seen:
                seen.add(rel)
                if not os.path.exists(os.path.join(data_dir, rel)):
                    missing.append(rel)
    return missing


def _weight(path):
    return os.path.getsize(path) if os.path.isfile(path) else 0


def run_tasks(tasks, data_dir, jobs=0, quiet=False, desc='Extracting'):
    """Run every task; return results in the order of ``tasks``.

    jobs == 1 runs in-process, one task after another (the original behaviour);
    otherwise a spawn-based process pool is used. Tasks with the largest last input
    file (the ``.yar`` for ``Task``) are submitted first so the slowest ones don't
    end up alone at the tail.
    """
    jobs = resolve_jobs(jobs, len(tasks))
    calls = [t.call(data_dir, quiet) for t in tasks]
    results = [None] * len(tasks)
    bar = tqdm(total=len(tasks), unit='task', desc=f'{desc} [{jobs} worker{"s" * (jobs > 1)}]')
    if jobs == 1:
        for i, (fn, args) in enumerate(calls):
            results[i] = fn(*args)
            bar.update()
    else:
        for var in _THREAD_ENV_VARS:
            os.environ.setdefault(var, '1')  # inherited by the spawned workers
        weights = [_weight(os.path.join(data_dir, t.inputs[-1])) for t in tasks]
        order = sorted(range(len(calls)), key=lambda i: -weights[i])
        # 'spawn' behaves the same on Linux, macOS and Windows and avoids forking a
        # process that has already imported matplotlib.
        with ProcessPoolExecutor(max_workers=jobs, mp_context=mp.get_context('spawn')) as pool:
            futures = {pool.submit(calls[i][0], *calls[i][1]): i for i in order}
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


# --------------------------------------------------------------------------------------
# Recording of the plotted numbers (read-only; the figures themselves are unchanged)
# --------------------------------------------------------------------------------------
def _floats(values):
    return [float(v) for v in values]


def plotted_data(fig):
    """Numbers drawn in ``fig``, one entry per Axes.

    bars:  one entry per bar series (``ax.bar`` call): bar centres ``x``, ``bottom``,
           ``height`` and, if drawn, the half-length ``err`` of each error bar;
    lines: every Line2D (curves and ``axhline`` reference lines) with its colour and
           x/y data;
    xticks: [position, label] of each fixed x tick (bar names), when the axis has
            explicit labels;
    texts: every text/annotation drawn inside the Axes.
    """
    from matplotlib.colors import to_hex
    from matplotlib.container import BarContainer
    from matplotlib.ticker import FixedFormatter, FixedLocator, FuncFormatter

    def xticks(ax):
        # Pure reads: the fixed locations and the label the formatter gives each one.
        locator, fmt = ax.xaxis.get_major_locator(), ax.xaxis.get_major_formatter()
        if not isinstance(locator, FixedLocator) or not isinstance(fmt, (FixedFormatter, FuncFormatter)):
            return []
        return [[float(loc), str(fmt(loc, i))] for i, loc in enumerate(locator.locs)]

    axes = []
    for ax in fig.axes:
        bars = []
        for c in ax.containers:
            if not isinstance(c, BarContainer):
                continue
            err = None
            if c.errorbar is not None and c.errorbar.lines[2]:
                segments = c.errorbar.lines[2][0].get_segments()
                err = [float(abs(s[1][1] - s[0][1]) / 2) for s in segments]
            bars.append({
                'x': [float(p.get_x() + p.get_width() / 2) for p in c.patches],
                'bottom': _floats(p.get_y() for p in c.patches),
                'height': _floats(p.get_height() for p in c.patches),
                'err': err,
            })
        lines = [{'label': str(line.get_label()), 'color': to_hex(line.get_color()),
                  'x': _floats(line.get_xdata()), 'y': _floats(line.get_ydata())}
                 for line in ax.get_lines()]
        axes.append({
            'bars': bars,
            'lines': lines,
            'xticks': xticks(ax),
            'texts': [t.get_text() for t in ax.texts],
        })
    return axes


def install_recorder(out_dir):
    """Wrap ``Figure.savefig`` so each saved figure's numbers are captured first.

    Returns the dict that fills up as figures are saved:
    {path relative to out_dir: plotted_data(fig)}.
    """
    import matplotlib.figure

    original = matplotlib.figure.Figure.savefig
    records = {}

    def savefig(self, fname, *args, **kwargs):
        if isinstance(fname, (str, os.PathLike)):
            rel = os.path.relpath(os.path.abspath(fname), os.path.abspath(out_dir))
            records[rel.replace(os.sep, '/')] = plotted_data(self)
        return original(self, fname, *args, **kwargs)

    matplotlib.figure.Figure.savefig = savefig
    return records


def build_arg_parser(description):
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-j', '--jobs', '--cores', type=int, default=0, metavar='N',
                        help='worker processes for the extraction phase '
                             '(0 = all available CPUs [default]; 1 = sequential, in-process)')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='root holding the input data (default: %(default)s)')
    parser.add_argument('--out-dir', default=DEFAULT_OUT_DIR,
                        help='where the Claim*/ figure folders are written (default: %(default)s)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="hide the extraction code's per-file/per-rule diagnostic prints")
    parser.add_argument('--dry-run', action='store_true',
                        help='list the extraction tasks, check that every input exists, and exit')
    return parser


def script_main(description, tasks, make_figures, argv=None):
    """Shared ``main()``: parse args, preflight inputs, extract in parallel, plot.

    ``make_figures(datasets, out_dir)`` receives ``group_results(...)`` and must
    return the list of PDF paths it wrote. The plotted numbers of those figures are
    written to ``<out_dir>/<script name>.values.json``.
    """
    args = build_arg_parser(description).parse_args(argv)
    missing = missing_inputs(tasks, args.data_dir)
    if args.dry_run:
        for t in tasks:
            print(t.describe())
        print(f'{len(tasks)} tasks, data dir {args.data_dir}, {len(missing)} missing inputs')
    for rel in missing:
        print(f'MISSING INPUT: {os.path.join(args.data_dir, rel)}', file=sys.stderr)
    if missing:
        if not os.path.isdir(args.data_dir):
            print(f'The data directory {args.data_dir} does not exist; fetch the data with '
                  f'./loadData.sh (see README.md).', file=sys.stderr)
        return 2
    if args.dry_run:
        return 0

    import matplotlib.pyplot as plt
    plt.switch_backend('Agg')  # figures are only saved, never shown

    t0 = time.perf_counter()
    results = run_tasks(tasks, args.data_dir, args.jobs, args.quiet)
    t1 = time.perf_counter()
    records = install_recorder(args.out_dir)
    written = make_figures(group_results(tasks, results), args.out_dir)
    t2 = time.perf_counter()

    name = os.path.splitext(os.path.basename(sys.modules['__main__'].__file__))[0]
    values_path = os.path.join(args.out_dir, f'{name}.values.json')
    os.makedirs(args.out_dir, exist_ok=True)
    with open(values_path, 'w') as fh:
        json.dump(records, fh, indent=1)
    print(f'extraction {t1 - t0:.1f}s, plotting {t2 - t1:.1f}s; wrote {len(written)} figures:')
    for path in written:
        print(f'  {path}')
    print(f'plotted values: {values_path}')
    return 0
