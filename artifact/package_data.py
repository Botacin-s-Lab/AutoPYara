#!/usr/bin/env python3
"""Build the evaluation-data archive for the Zenodo upload (authors only).

Evaluators do not need this script; they fetch the published archive with
``artifact/download_data.py``.

It collects exactly the inputs the figure scripts read, and nothing else from
``data/``:

  * every clustering CSV and merged ``.yar`` rule file listed in the task tables of
    ``artifact/plots/PlotsSet{1,2,4}_*.py``;
  * for each threat-hunting folder in ``PlotsSet3_ThreatHunting.py``, only the six
    required files of each ``cluster_*`` sub-folder (never whole folders, so nothing
    else that may sit next to them is published by accident).

Output (default ``release/``, which is gitignored):

    autopyara-acsac2026-data.tar.gz          deterministic archive (fixed mtimes/owners)
    autopyara-acsac2026-data.tar.gz.sha256   SHA-256 of the archive
    (inside the archive) MANIFEST.sha256     SHA-256 of every file, relative to data/

Usage:
    python3 artifact/package_data.py --list     # print what would be packaged, check it exists
    python3 artifact/package_data.py            # build release/autopyara-acsac2026-data.tar.gz

After uploading the archive to Zenodo, copy the record URL, the DOI and the printed
archive SHA-256 into the constants at the top of ``artifact/download_data.py``.
"""
import argparse
import gzip
import hashlib
import io
import os
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'plots'))

ARCHIVE_NAME = 'autopyara-acsac2026-data.tar.gz'
MANIFEST_NAME = 'MANIFEST.sha256'
FIXED_MTIME = 0  # deterministic archive: same bytes for the same inputs


def figure_inputs(data_dir):
    """Relative paths (under data_dir) of every file the four figure scripts read."""
    import PlotsSet1_Boxplots
    import PlotsSet2_ThresholdPlots
    import PlotsSet3_ThreatHunting
    import PlotsSet4_yaraBigPicture

    files = set()
    for mod in (PlotsSet1_Boxplots, PlotsSet2_ThresholdPlots, PlotsSet4_yaraBigPicture):
        for task in mod.TASKS:
            files.update(task.inputs)
    missing_dirs = []
    for task in PlotsSet3_ThreatHunting.TASKS:
        for rel_dir in task.inputs:
            root = os.path.join(data_dir, rel_dir)
            if not os.path.isdir(root):
                missing_dirs.append(rel_dir)
                continue
            for cluster in sorted(os.listdir(root)):
                if not cluster.startswith('cluster_'):
                    continue
                for name in PlotsSet3_ThreatHunting.required_files:
                    rel = os.path.join(rel_dir, cluster, name)
                    if os.path.isfile(os.path.join(data_dir, rel)):
                        files.add(rel)
    return sorted(files), missing_dirs


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _tarinfo(name, size):
    info = tarfile.TarInfo(name)
    info.size = size
    info.mtime = FIXED_MTIME
    info.mode = 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ''
    return info


def build(data_dir, out_dir, files):
    os.makedirs(out_dir, exist_ok=True)
    archive = os.path.join(out_dir, ARCHIVE_NAME)
    manifest = []
    for i, rel in enumerate(files, 1):
        manifest.append(f'{sha256_file(os.path.join(data_dir, rel))}  {rel}\n')
        if i % 500 == 0 or i == len(files):
            print(f'  hashed {i}/{len(files)} files', flush=True)
    manifest_bytes = ''.join(manifest).encode()

    with open(archive, 'wb') as raw, \
            gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=FIXED_MTIME) as gz, \
            tarfile.open(fileobj=gz, mode='w', format=tarfile.PAX_FORMAT) as tar:
        tar.addfile(_tarinfo(MANIFEST_NAME, len(manifest_bytes)), io.BytesIO(manifest_bytes))
        for i, rel in enumerate(files, 1):
            path = os.path.join(data_dir, rel)
            with open(path, 'rb') as fh:
                tar.addfile(_tarinfo(rel.replace(os.sep, '/'), os.path.getsize(path)), fh)
            if i % 500 == 0 or i == len(files):
                print(f'  archived {i}/{len(files)} files', flush=True)

    digest = sha256_file(archive)
    with open(archive + '.sha256', 'w') as fh:
        fh.write(f'{digest}  {ARCHIVE_NAME}\n')
    return archive, digest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data-dir', default=os.path.join(REPO, 'data'),
                    help='local data root (default: %(default)s)')
    ap.add_argument('--out-dir', default=os.path.join(REPO, 'release'),
                    help='where the archive is written (default: %(default)s)')
    ap.add_argument('--list', action='store_true', help='only list the files that would be packaged')
    args = ap.parse_args()

    files, missing_dirs = figure_inputs(args.data_dir)
    missing = [f for f in files if not os.path.isfile(os.path.join(args.data_dir, f))]
    missing += [d + '/' for d in missing_dirs]
    total = sum(os.path.getsize(os.path.join(args.data_dir, f)) for f in files if f not in missing)
    if args.list:
        for f in files:
            print(f)
    print(f'{len(files)} files, {total / 1e9:.2f} GB, {len(missing)} missing (data dir: {args.data_dir})')
    for m in missing:
        print(f'MISSING: {m}', file=sys.stderr)
    if missing:
        return 2
    if args.list:
        return 0

    archive, digest = build(args.data_dir, args.out_dir, files)
    print(f'\nwrote {archive} ({os.path.getsize(archive) / 1e9:.2f} GB)')
    print(f'archive SHA-256: {digest}')
    print('Next: upload it to Zenodo, then set DATA_DOI, ARCHIVE_URL and ARCHIVE_SHA256 '
          'in artifact/download_data.py.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
