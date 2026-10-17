#!/usr/bin/env python3
"""Fetch pinned reference checkouts into work/; defaults to packaging tools."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def fetch(name, source):
    target = ROOT / 'work' / name
    commit = source['commit']
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError(f'Invalid commit for {name}')
    if not target.exists():
        subprocess.run(['git', 'init', str(target)], check=True)
        subprocess.run(['git', '-C', str(target), 'remote', 'add', 'origin', source['url']], check=True)
    if subprocess.check_output(['git', '-C', str(target), 'status', '--porcelain'], text=True).strip():
        raise ValueError(f'{target} has local changes; use a fresh checkout')
    subprocess.run(['git', '-C', str(target), 'fetch', '--depth', '1', source['url'], commit], check=True)
    subprocess.run(['git', '-C', str(target), 'checkout', '--detach', commit], check=True)


def main():
    sources = json.loads((ROOT / 'sources.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('names', nargs='*')
    args = parser.parse_args()
    names = args.names or ['pmbootstrap', 'pmaports']
    for name in names:
        if name not in sources:
            parser.error(f'Unknown source: {name}')
        fetch(name, sources[name])


if __name__ == '__main__':
    main()
