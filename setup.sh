#!/usr/bin/env sh
# Portable setup; Windows/Python 3.12 is the tested platform. Requires FFmpeg on PATH.
set -eu
cd "$(dirname "$0")"
export PYTHONUTF8=1
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/bootstrap.py --model
.venv/bin/python scripts/bootstrap.py --doctor
