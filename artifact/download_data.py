#!/usr/bin/env python3
"""Download, verify and unpack the evaluation data into ``data/``.

The data are the inputs of the paper's figures (claims 4-9): the malware clustering
CSVs, the evaluated YARA rule sets (each rule annotated with its measured TP rate)
and the threat-hunting results. They are published on Zenodo (see DATA_DOI below);
no malware is included. The layout they unpack to is described in
``artifact/plots/README.md``.

Usage:
    python3 artifact/download_data.py                  # download + verify + unpack into <repo>/data
    python3 artifact/download_data.py --archive FILE   # use an archive you already downloaded
    python3 artifact/download_data.py --verify-only    # re-check an unpacked data/ against its manifest

Every file is checked against the SHA-256 manifest shipped inside the archive.
Exit codes: 0 ok, 1 verification/download error, 2 data not published yet.
"""
import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request

# --------------------------------------------------------------------------------------
# TODO(authors): fill these in once the data archive is on Zenodo
# (build it with artifact/package_data.py, which prints the SHA-256).
# --------------------------------------------------------------------------------------
DATA_DOI = '10.5281/zenodo.TODO'
ARCHIVE_URL = 'https://zenodo.org/records/TODO/files/autopyara-acsac2026-data.tar.gz?download=1'
ARCHIVE_SHA256 = 'TODO'

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MANIFEST_NAME = 'MANIFEST.sha256'


def published():
    return 'TODO' not in ARCHIVE_URL


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    print(f'Downloading {url}')
    with urllib.request.urlopen(url) as resp, open(dest, 'wb') as out:
        total = int(resp.headers.get('Content-Length') or 0)
        done = 0
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f'\r  {done / 1e9:.2f} / {total / 1e9:.2f} GB', end='', flush=True)
    print()


def safe_extract(archive, dest):
    """Extract, refusing absolute paths, '..' components and links."""
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        for m in members:
            parts = m.name.replace('\\', '/').split('/')
            if m.name.startswith('/') or '..' in parts or not (m.isfile() or m.isdir()):
                raise RuntimeError(f'refusing unsafe archive member: {m.name}')
        # Python >= 3.12 (and recent 3.8-3.11 patch releases) ship the 'data' filter,
        # which enforces the same rules; older versions rely on the check above.
        extra = {'filter': 'data'} if hasattr(tarfile, 'data_filter') else {}
        tar.extractall(dest, members=members, **extra)


def verify(data_dir):
    manifest = os.path.join(data_dir, MANIFEST_NAME)
    if not os.path.isfile(manifest):
        print(f'ERROR: {manifest} not found; is {data_dir} an unpacked data archive?', file=sys.stderr)
        return False
    bad = []
    lines = open(manifest).read().splitlines()
    for i, line in enumerate(lines, 1):
        digest, rel = line.split('  ', 1)
        path = os.path.join(data_dir, rel)
        if not os.path.isfile(path) or sha256_file(path) != digest:
            bad.append(rel)
        if i % 1000 == 0 or i == len(lines):
            print(f'\r  verified {i}/{len(lines)} files', end='', flush=True)
    print()
    for rel in bad[:20]:
        print(f'  BAD: {rel}', file=sys.stderr)
    if bad:
        print(f'ERROR: {len(bad)} file(s) missing or corrupted', file=sys.stderr)
    return not bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dest', default=os.path.join(REPO, 'data'),
                    help='where to unpack the data (default: %(default)s)')
    ap.add_argument('--archive', help='use this local archive instead of downloading')
    ap.add_argument('--verify-only', action='store_true', help='only verify an existing --dest')
    args = ap.parse_args()

    if args.verify_only:
        return 0 if verify(args.dest) else 1

    if not args.archive and not published():
        print('The evaluation data archive has not been published yet '
              '(DATA_DOI/ARCHIVE_URL in artifact/download_data.py are placeholders).\n'
              'If you received the archive directly, run:\n'
              '    python3 artifact/download_data.py --archive /path/to/autopyara-acsac2026-data.tar.gz',
              file=sys.stderr)
        return 2

    tmp = None
    archive = args.archive
    try:
        if not archive:
            tmp = tempfile.mkdtemp(prefix='autopyara-data-')
            archive = os.path.join(tmp, 'data.tar.gz')
            download(ARCHIVE_URL, archive)
        if published():
            print('Checking archive SHA-256 ...')
            digest = sha256_file(archive)
            if digest != ARCHIVE_SHA256:
                print(f'ERROR: archive SHA-256 {digest} != expected {ARCHIVE_SHA256}', file=sys.stderr)
                return 1
        os.makedirs(args.dest, exist_ok=True)
        print(f'Unpacking into {args.dest} ...')
        safe_extract(archive, args.dest)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)

    print('Verifying every file against the manifest ...')
    if not verify(args.dest):
        return 1
    print(f'Data ready in {args.dest}  (DOI: {DATA_DOI})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
