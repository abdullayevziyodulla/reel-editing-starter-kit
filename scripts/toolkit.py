"""Reusable job, word-timeline, validation, review-frame and final-mix utilities."""
import argparse
import copy
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)

def job_for(clip):
    return ROOT / 'transcript' / Path(clip).stem

def mapped_words(job, intro=0):
    pieces, words = load(job / 'pieces.json'), load(job / 'words.json')
    output, bounds, offset = [], [], float(intro)
    for p in pieces:
        end = offset + p['end'] - p['start']
        bounds.append({'seg': p['i'], 'start': offset, 'end': end, 'text': p['text']})
        for w in words:
            if w['seg'] == p['i'] and w['start'] < p['end'] and w['end'] > p['start']:
                output.append(dict(w, raw_start=w['start'], raw_end=w['end'],
                                   start=round(offset + max(w['start'], p['start']) - p['start'], 6),
                                   end=round(offset + min(w['end'], p['end']) - p['start'], 6)))
        offset = end
    output.sort(key=lambda w: (w['start'], w['end']))
    return {'duration': offset, 'intro_duration': intro, 'segments': bounds, 'words': output}

def init(a):
    source = Path(a.source).resolve()
    if not source.is_file():
        raise ValueError('Source video does not exist')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', a.name):
        raise ValueError('Use an ASCII job name: letters, digits, underscores and hyphens')
    raw = ROOT / 'raw' / (a.name + source.suffix.lower())
    job = job_for(raw)
    if raw.exists() or job.exists():
        raise ValueError('Job already exists; choose a new name. Nothing was overwritten.')
    if a.reuse:
        old = ROOT / 'transcript' / a.reuse
        original = load(old / 'segments.json')
        # Reuse is valid only for identical source footage, never arbitrary similar clips.
        import hashlib
        previous = Path(original.get('clip', ''))
        if not previous.is_absolute():
            previous = ROOT / previous
        if not previous.is_file():
            matches = list((ROOT / 'raw').glob(a.reuse + '.*'))
            previous = matches[0] if len(matches) == 1 else previous
        digest = lambda p: hashlib.file_digest(p.open('rb'), 'sha256').digest()
        if not previous.is_file() or digest(source) != digest(previous):
            raise ValueError('Reuse requires byte-identical original footage')
        if not (old / 'words.json').exists():
            raise ValueError('Reuse job has no aligned words')
    raw.parent.mkdir(exist_ok=True)
    shutil.copy2(source, raw)
    (job / 'check').mkdir(parents=True)
    if a.reuse:
        for name in ['segments.json', 'words.json', 'audio16k.wav']:
            if (old / name).exists():
                shutil.copy2(old / name, job / name)
        if (old / 'chunks').exists():
            shutil.copytree(old / 'chunks', job / 'chunks')
        data = load(job / 'segments.json')
        data['clip'] = raw.relative_to(ROOT).as_posix()
        save(job / 'segments.json', data)
    print('Created', raw.relative_to(ROOT), 'and', job.relative_to(ROOT))

def audio(a):
    job = job_for(a.clip)
    dest = job / 'audio16k.wav'
    if dest.exists():
        print('Audio already exists; retained')
        return
    job.mkdir(parents=True, exist_ok=True)
    run(['ffmpeg', '-n', '-v', 'error', '-i', str(Path(a.clip).resolve()), '-vn', '-ac', '1', '-ar', '16000', str(dest)])
    print(dest.relative_to(ROOT))

def timing(a):
    job = job_for(a.clip)
    data = mapped_words(job, a.intro)
    save(job / 'timeline.json', data)
    for s in data['segments']:
        print(f"Segment {s['seg']}: {s['start']:.3f}..{s['end']:.3f} {s['text']}")
    print('Word anchors saved in', (job / 'timeline.json').relative_to(ROOT))

def checked_path(value, errors):
    p = Path(value)
    target = (ROOT / p).resolve()
    if p.is_absolute() or not target.is_relative_to(ROOT):
        errors.append('Asset paths must be relative and inside the editing folder: ' + value)
    elif not target.is_file():
        errors.append('Missing asset: ' + value)

def validate(a):
    job = job_for(a.clip)
    errors, warnings = [], []
    seg = load(job / 'segments.json')
    cuts = load(job / 'cuts.json')
    ids = {s['i'] for s in seg['segments']}
    keep = cuts.get('keep', [])
    if not keep or len(set(keep)) != len(keep) or set(keep) - ids:
        errors.append('keep must contain unique existing segment IDs in playback order')
    if cuts.get('captions') is not False:
        errors.append('Set captions:false when composing, or captions will be burned twice')
    for s in seg['segments']:
        if not (0 <= s['start'] < s['end'] <= seg['duration'] + .001):
            errors.append('Invalid raw segment range: ' + str(s['i']))
    words = load(job / 'words.json')
    for w in words:
        if w['seg'] not in ids or not w['w'].strip() or not (0 <= w['start'] < w['end'] <= seg['duration'] + .1):
            errors.append('Invalid aligned word: ' + str(w))
    plan = load(job / ('edit.json' if a.style == 'dynamic' else 'hf_plan.json'))
    checked_path(plan['base'], errors)
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type', '-of', 'json', str(ROOT / plan['base'])]).stdout)
    duration = float(info['format']['duration'])
    if not any(s['codec_type'] == 'audio' for s in info['streams']):
        errors.append('Base needs an audio stream, even for a silent intro')
    layout = sorted(plan.get('layout', []), key=lambda l: l['start'])
    expected = 0
    modes = {'face', 'split', 'full'} if a.style == 'dynamic' else {'face', 'top'}
    for l in layout:
        if l['mode'] not in modes:
            errors.append('Unknown layout mode: ' + l['mode'])
        if abs(l['start'] - expected) > .04:
            errors.append('Layout gap/overlap at ' + str(l['start']))
        if not (0 <= l['start'] < l['end'] <= duration + .04):
            errors.append('Invalid layout interval')
        if l['mode'] in {'split', 'full'} and not l.get('broll'):
            errors.append('Split/full layout needs broll')
        expected = l['end']
    if not layout or abs(expected - duration) > .05:
        errors.append('Layout must cover the entire base duration')
    assets = {'base', 'broll', 'media', 'file', 'img', 'logo'}
    time_keys = {'t', 'count_at', 'strike_at', 'chips_at', 'merge_at', 'q_t0', 'q_t1', 'a_t0', 'a_t1', 'send_at'}
    def walk(obj, scene=None):
        if isinstance(obj, dict):
            if 'type' in obj and 'start' in obj and 'end' in obj:
                scene = obj
            for key, value in obj.items():
                if key in assets and isinstance(value, str):
                    checked_path(value, errors)
                if key in {'start', 'end'} and 'end' in obj and isinstance(value, (int, float)):
                    if not math.isfinite(value) or value < 0 or value > duration + .05:
                        errors.append('Time outside output timeline: ' + key)
                if key in time_keys or (key == 'type_at' and a.style == 'hf'):
                    if isinstance(value, (int, float)) and (value < 0 or value > duration + .05):
                        errors.append('Output anchor outside timeline: ' + key)
                    elif scene and isinstance(value, (int, float)) and not (scene['start'] <= value < scene['end']):
                        errors.append('Anchor outside its scene: ' + key)
                if key == 'zoom' and (len(value) != 2 or min(value) < 1):
                    errors.append('zoom must have two values >=1')
                if key == 'max' and isinstance(value, (int, float)) and value <= 0:
                    errors.append('SFX max must be positive')
                if key == 'per_char' and value <= 0:
                    errors.append('per_char must be positive')
                walk(value, scene)
            if 'end' in obj and 'start' in obj and obj['end'] <= obj['start']:
                errors.append('Empty scene/graphic interval')
            if obj.get('type') == 'chat' and (obj['q_t1'] <= obj['q_t0'] or obj['a_t1'] <= obj['a_t0']):
                errors.append('Chat typing intervals must increase')
        elif isinstance(obj, list):
            for value in obj:
                walk(value, scene)
    walk(plan)
    if a.style == 'dynamic':
        from gfx import GRAPHICS
        for g in plan.get('graphics', []):
            if g['type'] not in GRAPHICS:
                errors.append('Unknown graphic: ' + g['type'])
    else:
        if plan.get('theme', 'light') not in {'light', 'dark'}:
            errors.append('theme must be light or dark')
        scene_types = {'counter', 'window', 'tiles', 'chat', 'stack', 'strike', 'checklist', 'converge', 'comment'}
        for sc in plan['scenes']:
            if sc['type'] not in scene_types:
                errors.append('Unknown HF scene: ' + sc['type'])
            if sc['type'] == 'checklist' and not sc.get('rows'):
                errors.append('checklist must have rows')
        if plan.get('auto_sfx', True):
            from compose_hf import auto_sfx
            for s in auto_sfx(plan):
                checked_path(s['file'], errors)
        if plan.get('speaker'):
            checked_path('assets/models/selfie_segmenter.tflite', errors)
            cfg = plan['speaker']
            if cfg.get('card_w', int(1080 * cfg.get('scale', .68)) - 8) >= int(1080 * cfg.get('scale', .68)):
                errors.append('Speaker card must be narrower than scaled video')
            warnings.append('Speaker geometry must be calibrated on this footage; inspect hair and mouth')
    from compose import build_captions
    groups = build_captions(job, set())
    for g in groups:
        if g['start'] < -.01 or g['end'] <= g['start'] or g['end'] + plan.get('intro_duration', 0) > duration + .05:
            errors.append('Invalid mapped caption interval')
    report = {'style': a.style, 'duration': duration, 'errors': sorted(set(errors)), 'warnings': sorted(set(warnings))}
    save(job / ('validation_' + a.style + '.json'), report)
    for line in report['errors']:
        print('ERROR:', line)
    for line in report['warnings']:
        print('REVIEW:', line)
    if errors:
        raise ValueError('Validation failed; fix the plan before rendering')
    print('Plan/timeline/assets valid. Visual review is still required.')

def frames(a):
    src = Path(a.video).resolve()
    job = job_for(a.clip)
    out = job / 'check'
    out.mkdir(parents=True, exist_ok=True)
    duration = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(src)]).stdout)
    for value in a.times.split(','):
        t = float(value)
        if not 0 <= t < duration:
            raise ValueError('Frame time outside video')
        dest = out / f'review_{t:06.2f}.png'
        run(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-i', str(src), '-frames:v', '1', '-vf', 'scale=360:640', str(dest)])
        print(dest.relative_to(ROOT))

def finalize(a):
    src = Path(a.video).resolve()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', a.name):
        raise ValueError('Final name must be ASCII, e.g. 2026-10-03_topic_dynamic')
    final = ROOT / 'final' / (a.name + '.mp4')
    report = ROOT / 'output/verification' / (a.name + '.json')
    staged = ROOT / 'output/verification' / (a.name + '_normalized.mp4')
    if final.exists() and not a.replace:
        raise ValueError('Final already exists; choose a new name or use --replace explicitly')
    staged.parent.mkdir(parents=True, exist_ok=True)
    analysis = run(['ffmpeg', '-hide_banner', '-i', str(src), '-vn', '-af', 'loudnorm=I=-14:TP=-1.8:LRA=11:print_format=json', '-f', 'null', '-'])
    stats = json.loads(analysis.stderr[analysis.stderr.rfind('{'):analysis.stderr.rfind('}') + 1])
    if not all(math.isfinite(float(stats[k])) for k in ['input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset']):
        raise ValueError('Cannot normalize silent/invalid audio')
    filt = 'loudnorm=I=-14:TP=-1.8:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset},aresample=48000'.format(**stats)
    run(['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-af', filt, '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(staged)])
    measured = run(['ffmpeg', '-hide_banner', '-i', str(staged), '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'])
    report.with_suffix('.log').write_text(measured.stderr, encoding='utf-8')
    summary = measured.stderr[measured.stderr.rfind('Summary:'):]
    loud = float(re.search(r'I:\s+(-?[\d.]+) LUFS', summary).group(1))
    peak = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', summary).group(1))
    run(['ffmpeg', '-v', 'error', '-i', str(staged), '-f', 'null', '-'])
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height', '-of', 'json', str(staged)]).stdout)
    passed = abs(loud + 14) <= .3 and peak <= -1
    result = {'file': final.relative_to(ROOT).as_posix(), 'duration': float(info['format']['duration']), 'lufs': loud, 'true_peak_dbtp': peak, 'decode_passed': True, 'loudness_passed': passed}
    save(report, result)
    if not passed:
        raise ValueError('Loudness failed; retained in output for repair. Nothing delivered to final.')
    final.parent.mkdir(exist_ok=True)
    shutil.copy2(staged, final)
    print(json.dumps(result, indent=2))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='Copy own source into a unique job, never overwrite')
    p.add_argument('source'); p.add_argument('name'); p.add_argument('--reuse', help='Existing transcript job with identical footage'); p.set_defaults(fn=init)
    p = sub.add_parser('audio', help='Prepare 16k mono WAV for an imported transcript')
    p.add_argument('clip'); p.set_defaults(fn=audio)
    p = sub.add_parser('timing', help='Map aligned raw words to reordered output times')
    p.add_argument('clip'); p.add_argument('--intro', type=float, default=0); p.set_defaults(fn=timing)
    p = sub.add_parser('validate', help='Check timeline, layout, captions and referenced assets')
    p.add_argument('clip'); p.add_argument('--style', choices=['dynamic', 'hf'], required=True); p.set_defaults(fn=validate)
    p = sub.add_parser('frames', help='Extract review PNGs from a preview or final')
    p.add_argument('clip'); p.add_argument('video'); p.add_argument('--times', required=True); p.set_defaults(fn=frames)
    p = sub.add_parser('finalize', help='Two-pass complete-mix normalization, verify, then deliver')
    p.add_argument('video'); p.add_argument('name'); p.add_argument('--replace', action='store_true'); p.set_defaults(fn=finalize)
    a = ap.parse_args()
    a.fn(a)

if __name__ == '__main__':
    main()
