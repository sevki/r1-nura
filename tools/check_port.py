#!/usr/bin/env python3
"""Validate local aports with the pinned pmbootstrap and pmaports checkouts."""
import argparse
import hashlib
from pathlib import Path
import sys
import shutil
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pmbootstrap', type=Path, required=True)
    parser.add_argument('--pmaports', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(args.pmbootstrap.resolve()))
    import pmb.parse
    from pmb.core.config import Config, SystemdConfig
    from pmb.core.context import Context, set_context
    from pmb.helpers import logging
    from pmb.parse.deviceinfo import Deviceinfo
    from pmb.parse.kconfig import check_config

    config = Config()
    # The supplied checkout is a disposable staging tree. Keep work/ out of
    # pmaports' recursive package discovery.
    for package in (root / 'device/testing').iterdir():
        if package.is_dir():
            shutil.copytree(package, args.pmaports / 'device/testing' / package.name, dirs_exist_ok=True)
    config.aports = [args.pmaports.resolve()]
    config.device = 'rabbit-r1'
    config.systemd = SystemdConfig.NEVER
    config.work = root / 'work' / 'checks'
    config.work.mkdir(parents=True, exist_ok=True)
    set_context(Context(config))
    logging.init(config.work / 'check-port.log', verbose=False)
    pins = json.loads((root / 'sources.json').read_text())
    for path in sorted((root / 'device/testing').glob('*/APKBUILD')):
        aport = pmb.parse.apkbuild(path)
        print(f"Parsed {aport['pkgname']} {aport['pkgver']}")
        if aport['pkgname'] == 'linux-rabbit-r1' and pins['kernel']['commit'] not in ' '.join(aport['source']):
            raise ValueError('Kernel recipe does not match sources.json')
        tokens = aport['sha512sums'].split()
        if len(tokens) % 2:
            raise ValueError(f'Invalid checksum manifest: {path}')
        expected_names = {url.split('::')[0] if '::' in url else Path(url).name
                          for url in aport['source']}
        if set(tokens[1::2]) != expected_names or len(set(tokens[1::2])) != len(tokens[1::2]):
            raise ValueError(f'Incomplete or duplicate source checksums: {path}')
        for digest, name in zip(tokens[::2], tokens[1::2]):
            source = path.parent / name
            if source.exists():
                actual = hashlib.sha512(source.read_bytes()).hexdigest()
                if actual != digest:
                    raise ValueError(f'Checksum mismatch: {source}')
            elif not any('::' in url and url.split('::')[0] == name
                         for url in aport['source']):
                raise ValueError(f'Missing local source: {source}')
    info = Deviceinfo(root / 'device/testing/device-rabbit-r1/deviceinfo')
    if str(info.arch) != 'aarch64' or info.codename != 'rabbit-r1':
        raise ValueError('Unexpected device identity')
    if info.flash_method != 'none' or info.generate_bootimg != 'false':
        raise ValueError('Boot/flash integration is still unverified; update validation when implementing it')
    kernel_config = root / 'device/testing/linux-rabbit-r1/config-rabbit-r1.aarch64'
    if not check_config(kernel_config, 'aarch64', '4.19.191', [], details=True):
        raise ValueError('postmarketOS kernel configuration checks failed')
    print('Port metadata, local checksums and default kernel rules passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
