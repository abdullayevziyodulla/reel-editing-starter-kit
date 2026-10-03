"""Repackage only the original audited distribution inventory; exclude all new user material."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('destination', help='ZIP path OUTSIDE this kit folder')
    a = ap.parse_args()
    dest = Path(a.destination).resolve()
    if dest.is_relative_to(ROOT) or dest.exists():
        raise ValueError('Choose a new ZIP path outside the kit; existing files are never overwritten')
    manifest = json.loads((ROOT / 'DISTRIBUTION_MANIFEST.json').read_text(encoding='utf-8'))
    files = []
    for item in manifest['files']:
        rel = item['path']
        p = (ROOT / rel).resolve()
        if Path(rel).is_absolute() or not p.is_relative_to(ROOT) or not p.is_file() or p.is_symlink():
            raise ValueError('Unsafe/missing distribution member: ' + rel)
        if '.env' in p.name and p.name != '.env.example':
            raise ValueError('Credential file cannot be packaged')
        if hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Distribution file changed; review before sharing: ' + rel)
        if p.suffix.lower() in {'.py', '.md', '.json', '.js', '.html', '.txt', '.ps1', '.sh'} or p.name == '.env.example':
            text = p.read_text(encoding='utf-8')
            if re.search(r'AIza[0-9A-Za-z_-]{25,}|sk-[0-9A-Za-z_-]{24,}|(?:[A-Z]:[\\/]Users[\\/])', text):
                raise ValueError('Potential secret/local user path: ' + rel)
        files.append((p, rel))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for p, rel in files:
            archive.write(p, ROOT.name + '/' + rel)
        archive.write(ROOT / 'DISTRIBUTION_MANIFEST.json', ROOT.name + '/DISTRIBUTION_MANIFEST.json')
    with zipfile.ZipFile(dest) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('ZIP integrity check failed')
    print('Clean distribution:', dest.name, 'files:', len(files) + 1)

if __name__ == '__main__': main()
