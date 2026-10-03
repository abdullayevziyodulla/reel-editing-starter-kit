"""Run the kit's pinned, real HyperFrames CLI without a global npm installation."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command():
    node = shutil.which('node')
    package = ROOT / 'node_modules/hyperframes/package.json'
    if not node or not package.is_file():
        raise RuntimeError('Install Node.js 22+ and run npm ci in the kit folder first.')
    metadata = json.loads(package.read_text(encoding='utf-8'))
    required = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))['dependencies']['hyperframes']
    if metadata['version'] != required:
        raise RuntimeError('HyperFrames version differs from the kit lock; run npm ci.')
    return [node, str(package.parent / metadata['bin']['hyperframes'])]


def run(args, cwd=None):
    env = dict(os.environ, HYPERFRAMES_NO_UPDATE_CHECK='1', DO_NOT_TRACK='1', CI='1')
    # A local render never needs an API key. Do not let snapshot invoke optional AI analysis.
    env.pop('GEMINI_API_KEY', None)
    return subprocess.run(command() + list(map(str, args)), cwd=cwd or ROOT, env=env, check=True)


if __name__ == '__main__':
    run(sys.argv[1:])
