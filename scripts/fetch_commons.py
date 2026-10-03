"""Fetch Commons b-roll with provenance. Review each image and its actual license."""
import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {'User-Agent': 'reel-editing-starter-kit/1.0 (Wikimedia Commons image research)'}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read()

def plain(value):
    return html.unescape(re.sub('<[^>]+>', '', value or '')).strip()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('name'); ap.add_argument('query'); ap.add_argument('n', nargs='?', type=int, default=3)
    a = ap.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+', a.name) or not 1 <= a.n <= 10:
        raise ValueError('Use a safe ASCII name and n between 1 and 10')
    api = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': 6, 'gsrsearch': a.query + ' filetype:bitmap', 'gsrlimit': 20, 'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata', 'iiurlwidth': 1600})
    pages = sorted(json.loads(get(api)).get('query', {}).get('pages', {}).values(), key=lambda p: p['index'])
    out = ROOT / 'assets/broll'; out.mkdir(parents=True, exist_ok=True)
    log = out / 'commons_sources.json'
    sources = json.loads(log.read_text(encoding='utf-8')) if log.exists() else []
    got = 0
    for p in pages:
        ii = p['imageinfo'][0]
        if ii['width'] < 1000:
            continue
        meta = ii.get('extmetadata', {})
        value = lambda k: plain(meta.get(k, {}).get('value', ''))
        url = ii.get('thumburl') or ii['url']
        suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
        if suffix not in {'.jpg', '.jpeg', '.png', '.webp'}:
            continue
        dest = out / f'wc_{a.name}_{got+1}{suffix}'
        if dest.exists():
            raise ValueError('Asset already exists; use a new name instead of replacing it')
        dest.write_bytes(get(url))
        sources.append({'file': dest.relative_to(ROOT).as_posix(), 'title': p['title'], 'page': ii['descriptionurl'], 'download': url, 'author': value('Artist'), 'license': value('LicenseShortName'), 'license_url': value('LicenseUrl'), 'attribution': value('Attribution'), 'credit': value('Credit'), 'query': a.query})
        log.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')
        print(dest.name, '|', p['title'], '|', value('LicenseShortName') or 'UNKNOWN: check before use')
        got += 1
        if got >= a.n: break
        time.sleep(1.2)
    if not got:
        print('No suitable images. Try a different query.')

if __name__ == '__main__': main()
