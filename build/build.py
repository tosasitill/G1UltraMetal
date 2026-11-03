#!/usr/bin/env python3
"""Build X9PanVK<N> and X9GeneralMetal<N> and package them for the mailbox.

    python3 -I build/build.py --revision 243 --name rev243

Steps (same order as ios_plj110's `build.py plugins`):
  1. build/prepare-local.py --check      (.local inputs and maintained-source links)
  2. PanVK: build-panvk-native-ios.py (full: configure + build) or
     build-panvk-incremental.py (ninja only, when already configured)
  3. package-panvk-native.py --revision N
  4. build-general-metal.py --revision N
  5. package-plugins.py --revision N --out out/<name>
     -> out/<name>/plugin-package/ and out/<name>/x9_render_external_manifest.h
No device access. Copy the header to ios_plj110's x9/kernel/generated/ before
building the kernel that must accept this package.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'build'
WORK = ROOT / '.local/x9/work/x9-metal-render'


def run(cmd, label, env):
    print(f'== {label}', flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    if r.returncode:
        sys.exit(f'!! {label} failed with exit code {r.returncode}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--revision', type=int, required=True, help='plugin revision N (X9GeneralMetal<N>/X9PanVK<N>)')
    ap.add_argument('--name', help='output directory name under out/ (default rev<N>)')
    ap.add_argument('--panvk', choices=['auto', 'incremental', 'full', 'skip'], default='auto',
                    help='auto = incremental if build-panvk-native-ios is configured, else full')
    a = ap.parse_args()
    if not 170 <= a.revision <= 9999:
        sys.exit('--revision must be 170..9999')
    local = HERE / 'local.json'
    cfg = json.loads(local.read_text()) if local.is_file() else {}
    env = dict(os.environ, X9_HOMEBREW=cfg.get('homebrew') or '/opt/homebrew')
    py = [sys.executable, '-I']
    out = ROOT / 'out' / (a.name or f'rev{a.revision}')
    out.mkdir(parents=True, exist_ok=True)
    rev = ['--revision', str(a.revision)]
    run(py + [str(HERE / 'prepare-local.py'), '--check'], 'prepare-local --check', env)
    configured = (WORK / 'build-panvk-native-ios/build.ninja').is_file()
    if a.panvk == 'full' or (a.panvk == 'auto' and not configured):
        run(py + [str(HERE / 'scripts/build-panvk-native-ios.py')], 'PanVK full build', env)
    elif a.panvk != 'skip':
        run(py + [str(HERE / 'scripts/build-panvk-incremental.py')], 'PanVK incremental build', env)
    run(py + [str(HERE / 'scripts/package-panvk-native.py')] + rev, 'package X9PanVK', env)
    run(py + [str(HERE / 'scripts/build-general-metal.py')] + rev, 'build X9GeneralMetal', env)
    run(py + [str(HERE / 'scripts/package-plugins.py')] + rev + ['--out', str(out)], 'package plugins + allowlist', env)
    print(f'output: {out}')


if __name__ == '__main__':
    main()
