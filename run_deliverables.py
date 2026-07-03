#!/usr/bin/env python3
"""
Single runner for the deliverables package.
Usage: python run_deliverables.py

What it does:
- Finds `deliverables.zip` in the repo root
- Unpacks to `./deliverables_run`
- Verifies SHA256 against `checksums.sha256`
- If `docker_image.tar` found, loads and runs the image (port 8000)
- Else if `bin/app_demo.exe` found, executes it
- Else if `src_minimal/entrypoint.py` found, runs it with the venv python
"""
import sys
import os
from pathlib import Path
import zipfile
import hashlib
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
ZIP_PATH = ROOT / 'deliverables.zip'
RUN_DIR = ROOT / 'deliverables_run'


def read_checksums(path: Path):
    # try utf-8 then utf-16
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
            # remove any leading './' only (preserve leading dotfiles like .gitignore)
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


def main():
    if not ZIP_PATH.exists():
        print('deliverables.zip not found in repo root. Run packaging first.')
        return 2

    if RUN_DIR.exists():
        print('Removing existing', RUN_DIR)
        shutil.rmtree(RUN_DIR)
    RUN_DIR.mkdir()

    print('Unpacking', ZIP_PATH, '->', RUN_DIR)
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(RUN_DIR)

    checksums_file = RUN_DIR / 'checksums.sha256'
    if not checksums_file.exists():
        print('checksums.sha256 not found inside the package; skipping verification')
    else:
        expected = read_checksums(checksums_file)
        mismatches = []
        for name, expected_hash in expected.items():
            candidate = RUN_DIR / name
            if not candidate.exists():
                mismatches.append((name, 'MISSING', expected_hash, ''))
                continue
            actual = sha256_of_file(candidate)
            if actual.upper() != expected_hash.upper():
                mismatches.append((name, actual, expected_hash, 'MISMATCH'))
        if mismatches:
            print('Checksum verification FAILED:')
            for m in mismatches:
                print(' ', m)
            print('Aborting run for safety.')
            return 3
        print('All checksums match.')

    # runnable choices
    docker_tar = RUN_DIR / 'docker_image.tar'
    binary = RUN_DIR / 'bin' / 'app_demo.exe'
    py_entry = RUN_DIR / 'src_minimal' / 'entrypoint.py'

    docker = shutil.which('docker')
    if docker and docker_tar.exists():
        print('Loading docker image from', docker_tar)
        subprocess.run([docker, 'load', '-i', str(docker_tar)], check=True)
        print('Running container on port 8000')
        subprocess.run([docker, 'run', '--rm', '-p', '8000:8000', '--name', 'smartglasses_demo', 'smartglasses:deliverable'], check=True)
        return 0

    if binary.exists():
        print('Running binary fallback')
        subprocess.run([str(binary), '--demo-mode'], check=True)
        return 0

    if py_entry.exists():
        print('Running Python fallback entrypoint')
        pyexe = sys.executable or shutil.which('python') or shutil.which('python3')
        if not pyexe:
            print('No Python executable found to run the demo.')
            return 4
        env = os.environ.copy()
        # ensure the unpacked folder is on PYTHONPATH so `src_minimal` imports resolve
        env['PYTHONPATH'] = str(RUN_DIR)
        subprocess.run([pyexe, str(py_entry)], check=True, env=env)
        return 0

    print('No runnable artifact found inside package. See deliverables/README.md')
    return 5


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print('Subprocess failed:', e)
        sys.exit(10)
