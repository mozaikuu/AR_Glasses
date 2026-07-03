#!/usr/bin/env python3
"""
Run-all script placed inside the `deliverables` folder. It verifies checksums for files
inside the folder and runs the demo using only artifacts present in the same folder.

Usage (from repository root):
  python deliverables/run_all.py

Or change directory into `deliverables` and run:
  python run_all.py
"""
import sys
import os
from pathlib import Path
import hashlib
import subprocess


BASE = Path(__file__).resolve().parent


def read_checksums(path: Path):
    text = None
    for enc in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be'):
        try:
            text = path.read_text(encoding=enc)
            break
        except Exception:
            continue
    if text is None:
        raise RuntimeError(f'Could not read {path} with common encodings')
    mapping = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split()
        if len(parts) >= 2:
            hashv = parts[0]
            name = ' '.join(parts[1:]).strip()
            if name.startswith('./'):
                name = name[2:]
            mapping[name] = hashv
    return mapping


def sha256_of_file(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest().upper()


def verify():
    checksums = BASE / 'checksums.sha256'
    if not checksums.exists():
        print('No checksums.sha256 found; skipping verification')
        return True
    expected = read_checksums(checksums)
    mismatches = []
    for name, expected_hash in expected.items():
        candidate = BASE / name
        if not candidate.exists():
            mismatches.append((name, 'MISSING', expected_hash))
            continue
        actual = sha256_of_file(candidate)
        if actual.upper() != expected_hash.upper():
            mismatches.append((name, actual, expected_hash))
    if mismatches:
        print('Checksum verification failed:')
        for m in mismatches:
            print(' ', m)
        return False
    print('All checksums match for files in deliverables.')
    return True


def run():
    if not verify():
        print('Aborting due to checksum failures.')
        return 2

    docker_tar = BASE / 'docker_image.tar'
    binary = BASE / 'bin' / 'app_demo.exe'
    py_entry = BASE / 'src_minimal' / 'entrypoint.py'

    docker = shutil_which('docker')
    if docker and docker_tar.exists():
        print('Loading Docker image...')
        subprocess.run([docker, 'load', '-i', str(docker_tar)], check=True)
        print('Running container (port 8000)...')
        subprocess.run([docker, 'run', '--rm', '-p', '8000:8000', '--name', 'smartglasses_demo', 'smartglasses:deliverable'], check=True)
        return 0

    if binary.exists():
        print('Running binary fallback...')
        subprocess.run([str(binary), '--demo-mode'], check=True)
        return 0

    if py_entry.exists():
        print('Running Python fallback entrypoint...')
        pyexe = sys.executable or shutil_which('python') or shutil_which('python3')
        if not pyexe:
            print('No Python executable found.')
            return 3
        env = os.environ.copy()
        env['PYTHONPATH'] = str(BASE)
        subprocess.run([pyexe, str(py_entry)], check=True, env=env, cwd=str(BASE))
        return 0

    print('No runnable artifact found in deliverables.')
    return 4


def shutil_which(name):
    # small local wrapper to avoid importing shutil at top-level for readability
    from shutil import which
    return which(name)


if __name__ == '__main__':
    try:
        rc = run()
        sys.exit(rc if isinstance(rc, int) else 0)
    except subprocess.CalledProcessError as e:
        print('Subprocess failed:', e)
        sys.exit(10)
