"""Build a self-contained HyperFrames project from an existing hf_plan.json.

Python prepares the speaker matte and audio. The actual HyperFrames CLI owns
the composition timeline, video playback, GSAP seeking, capture and final encode.
"""
import argparse
import hashlib
import html
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from compose import face_zoom, mix_audio, probe
from compose_hf import FPS, H, W, CUT_TOP, Speaker, arch_mask, auto_sfx, background, chunk_captions
from hyperframes_cli import ROOT, command, run as hyperframes


def safe_asset(value):
    source = (ROOT / value).resolve()
    if not source.is_relative_to(ROOT) or not source.is_file():
        raise ValueError('Asset must be a file inside this kit: ' + value)
    return source


def copy_asset(value, project):
    source = safe_asset(value)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    rel = 'assets/' + digest + source.suffix.lower()
    shutil.copy2(source, project / rel)
    return rel


def backdrop(plan, project, duration):
    """Prepare only the footage/card geometry, with no HTML/browser rendering."""
    source = safe_asset(plan['base'])
    keys = ('layout', 'speaker', 'grade', 'theme', 'face_center', 'cut_src_top')
    fingerprint = {'geometry': {key: plan.get(key) for key in keys},
                   'source': [plan['base'], source.stat().st_size, source.stat().st_mtime_ns],
                   'duration': duration, 'pipeline': 1}
    if plan.get('speaker'):
        model = safe_asset('assets/models/selfie_segmenter.tflite')
        fingerprint['model'] = [model.stat().st_size, model.stat().st_mtime_ns]
    cache = project / 'assets/backdrop.json'
    dest = project / 'assets/backdrop.mp4'
    if dest.is_file() and cache.is_file() and json.loads(cache.read_text(encoding='utf-8')) == fingerprint:
        if abs(probe(dest)[2] - duration) < 1 / FPS:
            print('Reusing prepared speaker/background', flush=True)
            return
    grade = plan.get('grade', 'eq=contrast=1.04:saturation=1.06,colorbalance=rs=0.03:gs=0.01:bs=-0.03')
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(safe_asset(plan['base'])),
                            '-vf', f'fps={FPS},scale={W}:{H},{grade}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264',
                            '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(dest)],
                           stdin=subprocess.PIPE)
    bg = background(plan.get('theme', 'light'))
    speaker = Speaker(plan['speaker']) if plan.get('speaker') else None
    mask = arch_mask(W, H - CUT_TOP)
    cx, cy = plan.get('face_center', [540, 780])
    total = int(round(duration * FPS))
    try:
        for i in range(total):
            buf = dec.stdout.read(W * H * 3)
            if len(buf) != W * H * 3:
                raise RuntimeError('Base video ended before its declared duration')
            cam = Image.frombuffer('RGB', (W, H), buf)
            t = i / FPS
            layout = next((item for item in plan['layout'] if item['start'] <= t < item['end']), None)
            if layout is None:
                raise ValueError('Layout does not cover output time ' + str(t))
            z0, z1 = layout.get('zoom', [1, 1])
            z = z0 + (z1 - z0) * (t - layout['start']) / (layout['end'] - layout['start'])
            if layout['mode'] == 'face':
                frame = face_zoom(cam, z, cx, cy)
            elif speaker:
                frame = speaker.draw(bg.copy(), cam, z)
            else:
                frame = bg.copy()
                ch, cw = (H - CUT_TOP) / z, W / z
                x0 = max(0, min(W - cw, cx - cw / 2))
                y0 = plan.get('cut_src_top', 330) + ((H - CUT_TOP) - ch) / 2
                spk = cam.resize((W, H - CUT_TOP), Image.Resampling.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
                frame.paste(spk, (0, CUT_TOP), mask)
            enc.stdin.write(frame.convert('RGB').tobytes())
            if i % 150 == 0:
                print(f'Prepare speaker/background: {i}/{total}', flush=True)
    finally:
        dec.stdout.close()
        dec.wait()
        enc.stdin.close()
        result = enc.wait()
        if speaker:
            speaker.seg.close()
    if dec.returncode or result:
        raise RuntimeError('FFmpeg backdrop preparation failed')
    cache.write_text(json.dumps(fingerprint) + '\n', encoding='utf-8')


def prepare(clip):
    command()  # Fail early if the actual framework is not installed.
    job = ROOT / 'transcript' / clip.stem
    plan = json.loads((job / 'hf_plan.json').read_text(encoding='utf-8'))
    _, _, duration, _ = probe(safe_asset(plan['base']))
    project = job / 'hyperframes'
    (project / 'assets').mkdir(parents=True, exist_ok=True)
    plan['duration'] = duration
    plan['captions'] = chunk_captions(job)
    for caption in plan['captions']:
        caption['start'] += plan.get('intro_duration', 0)
        caption['end'] += plan.get('intro_duration', 0)
    plan.setdefault('caption_y', 990)
    plan['emphasis'] = [word.lower() for word in plan.get('emphasis', [])]
    media_html = []
    for i, scene in enumerate(plan['scenes']):
        for holder in [scene] + scene.get('items', []) + scene.get('cards', []):
            for key in ('img', 'logo'):
                if key in holder:
                    holder[key] = copy_asset(holder[key], project)
        if scene.get('media'):
            source = safe_asset(scene['media'])
            media_id = 'scene-media-' + str(i)
            scene['media_id'] = media_id
            seconds = scene['end'] - scene['start']
            if source.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.svg'}:
                src = copy_asset(scene['media'], project)
                tag = 'img'
                extra = ''
            else:
                src = 'assets/' + media_id + '.mp4'
                subprocess.run(['ffmpeg', '-y', '-v', 'error', '-stream_loop', '-1',
                                '-ss', str(scene.get('from', 0)), '-i', str(source), '-t', str(seconds),
                                '-vf', 'scale=960:-2:force_original_aspect_ratio=decrease,fps=30', '-an',
                                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p',
                                '-movflags', '+faststart', str(project / src)], check=True)
                tag, extra = 'video', 'muted playsinline preload="auto"'
            # Persistent media DOM: HyperFrames owns visibility, decoding and time.
            media_html.append(f'<div id="{media_id}" class="media-slot"><{tag} id="{media_id}-clip" class="clip" '
                              f'data-start="{scene["start"]}" data-duration="{seconds}" data-track-index="1" '
                              f'src="{html.escape(src, quote=True)}" {extra}></{tag}></div>')
    backdrop(plan, project, duration)
    sounds = ([] if plan.get('auto_sfx', True) is False else auto_sfx(plan)) + plan.get('sfx', [])
    mix_audio({'music': plan.get('music'), 'sfx': sounds}, safe_asset(plan['base']), duration, project / 'assets/mix.m4a')
    for font in ('Inter.ttf', 'PlayfairDisplay-Italic.ttf'):
        shutil.copy2(ROOT / 'assets/fonts' / font, project / 'assets' / font)
    shutil.copy2(ROOT / 'node_modules/gsap/dist/gsap.min.js', project / 'gsap.min.js')
    shutil.copy2(ROOT / 'scripts/hf/runtime.js', project / 'runtime.js')
    page = (ROOT / 'scripts/hf/page.html').read_text(encoding='utf-8')
    page = (page.replace('__PLAN__', json.dumps(plan, ensure_ascii=False).replace('</', '<\\/'))
            .replace('__FONT_BASE__', 'assets').replace('__DURATION__', str(duration))
            .replace('__MEDIA__', '\n'.join(media_html)))
    (project / 'index.html').write_text(page, encoding='utf-8')
    (project / 'hyperframes.json').write_text(json.dumps({'name': clip.stem, 'version': '1.0.0'}) + '\n', encoding='utf-8')
    (job / 'hf_sfx.json').write_text(json.dumps(sounds, indent=2) + '\n', encoding='utf-8')
    hyperframes(['lint', project, '--json'])
    print('HyperFrames project:', project, flush=True)
    return job, project, duration


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('clip', type=Path)
    parser.add_argument('--prepare', action='store_true', help='Build/lint an editable HyperFrames project without capture')
    parser.add_argument('--preview', action='store_true', help='Render a draft and resize the delivery to 540x960')
    parser.add_argument('--frames', help='Comma-separated output seconds for real HyperFrames snapshots')
    parser.add_argument('--workers', type=int, default=1, help='HyperFrames capture workers; 1 suits a MacBook Air')
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error('--workers must be positive')
    job, project, duration = prepare(args.clip.resolve())
    if args.frames:
        times = [float(value) for value in args.frames.split(',')]
        if any(not math.isfinite(value) or not 0 <= value < duration for value in times):
            parser.error('--frames times must be finite and inside the output duration')
        dest = job / 'check/hyperframes'
        hyperframes(['snapshot', project, '--at', args.frames, '--no-end', '--describe', 'false', '--output', dest])
        print('Review HyperFrames PNGs:', dest)
    elif not args.prepare:
        out = ROOT / 'output' / f'{args.clip.stem}_nick{"_preview" if args.preview else ""}.mp4'
        render_out = project / 'draft.mp4' if args.preview else out
        hyperframes(['render', project, '--fps', FPS, '--workers', args.workers,
                     '--quality', 'draft' if args.preview else 'high', '--output', render_out])
        if args.preview:
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(render_out), '-vf', 'scale=540:960',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-c:a', 'copy',
                            '-movflags', '+faststart', str(out)], check=True)
        print('HyperFrames rendered:', out)
        print('Normalize/verify the complete mix with toolkit.py finalize before delivery.')


if __name__ == '__main__':
    main()
