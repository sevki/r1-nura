#!/bin/sh
# Run from the repository root on a disposable Linux builder with sudo.
set -eu
root=$(pwd)
python3 tools/fetch_sources.py
python3 tools/check_port.py --pmbootstrap work/pmbootstrap --pmaports work/pmaports
# pmbootstrap requires upstream/main:channels.cfg even when using a fork.
python3 - <<'PY'
import json
import subprocess
from pathlib import Path
source = json.loads(Path('sources.json').read_text())['pmaports-metadata']
subprocess.run(['git', '-C', 'work/pmaports', 'remote', 'add', 'upstream', source['url']], check=True)
subprocess.run(['git', '-C', 'work/pmaports', 'fetch', '--depth', '1', 'upstream',
                source['commit'] + ':refs/remotes/upstream/main'], check=True)
PY
mkdir -p work/pmb-ci
printf '8\n' > work/pmb-ci/version
cat > work/pmb-ci.cfg <<EOF_CONFIG
[pmbootstrap]
aports = $root/work/pmaports
work = $root/work/pmb-ci
device = rabbit-r1
ui = console
systemd = never
jobs = 4
is_default_channel = True

[providers]

[mirrors]
EOF_CONFIG
python3 work/pmbootstrap/pmbootstrap.py -c "$root/work/pmb-ci.cfg" \
	--details-to-stdout -y build --arch aarch64 linux-rabbit-r1 device-rabbit-r1
