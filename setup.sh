#!/usr/bin/env sh
# Portable setup; Windows/Python 3.12 is the tested platform. Requires FFmpeg on PATH.
set -eu
cd "$(dirname "$0")"
export PYTHONUTF8=1
export HYPERFRAMES_NO_UPDATE_CHECK=1
command -v node >/dev/null
command -v npm >/dev/null
node -e "if (Number(process.versions.node.split('.')[0]) < 22) process.exit(1)"
npm ci --no-audit --no-fund
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/hyperframes_cli.py browser ensure
.venv/bin/python scripts/bootstrap.py --model
.venv/bin/python scripts/bootstrap.py --doctor
