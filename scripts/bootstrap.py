"""Environment check, optional official segmentation model, and synthetic demo creation."""
import argparse
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite'

def run(args):
    subprocess.run(args, check=True)

def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def model():
    dest = ROOT / 'assets/models/selfie_segmenter.tflite'
    if dest.exists():
        print('Model already present; retained')
        return
    data = urllib.request.urlopen(MODEL_URL, timeout=45).read()
    if len(data) < 100000 or data[4:8] != b'TFL3':
        raise RuntimeError('Invalid model response')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    save(dest.with_suffix('.source.json'), {'url': MODEL_URL, 'sha256': hashlib.sha256(data).hexdigest(), 'guide': 'https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter'})
    print('Downloaded official selfie segmenter (optional head breakout)')

def doctor(skip_browser=False):
    failed = []
    print('Python:', sys.version.split()[0], '(tested: 3.12)')
    if sys.version_info[:2] != (3, 12):
        print('NOTICE: use Python 3.12 for the tested dependency set')
    for cmd in ['ffmpeg', 'ffprobe']:
        if not shutil.which(cmd):
            failed.append(cmd + ' missing from PATH')
        else:
            print(cmd + ': found')
    for name in ['numpy', 'PIL', 'google.genai', 'dotenv', 'faster_whisper', 'mediapipe', 'playwright.sync_api']:
        try:
            importlib.import_module(name)
            print(name + ': import OK')
        except Exception as e:
            failed.append(name + ': ' + type(e).__name__)
    try:
        import gfx
        gfx.font('ariblk.ttf', 32)
        print('Bundled font: OK')
        if skip_browser:
            print('Playwright Chromium: skipped; install before using motion cards')
            if failed:
                raise RuntimeError('; '.join(failed))
            return
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content('<p>render check</p>')
            assert page.locator('p').inner_text() == 'render check'
            browser.close()
        print('Playwright Chromium: OK')
    except Exception as e:
        failed.append('Font/browser check: ' + type(e).__name__ + '; run setup and playwright install chromium')
    print('Head breakout model:', 'present' if (ROOT / 'assets/models/selfie_segmenter.tflite').exists() else 'optional; run bootstrap.py --model')
    print('API credentials are not inspected. Demo/imported transcripts do not need an API key.')
    if failed:
        raise RuntimeError('; '.join(failed))

def wav(path, samples, rate=48000):
    import numpy as np
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
        out.writeframes((np.clip(samples, -1, 1) * 32767).astype('<i2').tobytes())

def demo(assets_only=False):
    import numpy as np
    from PIL import Image, ImageDraw
    import gfx
    if (ROOT / 'raw/demo.mp4').exists() and not assets_only:
        print('Demo already exists; retained. Choose another job for your own footage.')
        return
    for name in ['raw', 'transcript/demo/check', 'output', 'final', 'assets/sfx', 'assets/music', 'assets/broll', 'assets/gfx']:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    # Procedural assets only: no real person, voice, third-party music pack or borrowed screenshot.
    for i, color in enumerate(['#0a84ff', '#28a878', '#dc8540'], 1):
        img = Image.new('RGB', (960, 540), '#101b2b')
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((45, 45, 915, 495), 35, fill=color)
        d.rounded_rectangle((350, 140, 610, 400), 36, fill='#101b2b')
        d.text((480, 210), 'EXAMPLE ' + str(i), anchor='mt', fill='white', font=gfx.font('ariblk.ttf', 32))
        d.text((480, 280), 'YOUR B-ROLL', anchor='mt', fill='#c3dbed', font=gfx.font('segoeuib.ttf', 23))
        img.save(ROOT / 'assets/broll' / f'demo_{i}.png')
    logo = Image.new('RGBA', (256, 256))
    d = ImageDraw.Draw(logo); d.rounded_rectangle((8, 8, 248, 248), 55, fill='#0a84ff')
    d.polygon([(92, 64), (192, 128), (92, 192)], fill='white')
    logo.save(ROOT / 'assets/gfx/demo_logo.png')
    image = Image.new('RGB', (1080, 1920), '#344052')
    d = ImageDraw.Draw(image)
    for y in range(0, 1920, 120):
        d.line((0, y, 1080, y), fill='#3e4c60', width=2)
    d.rounded_rectangle((90, 520, 990, 1750), 90, fill='#202938', outline='#6d829b', width=8)
    d.text((540, 700), 'DEMO', anchor='mt', font=gfx.font('ariblk.ttf', 135), fill='white')
    d.text((540, 950), 'YOUR FOOTAGE', anchor='mt', font=gfx.font('ariblk.ttf', 74), fill='#96caff')
    d.text((540, 1060), 'GOES HERE', anchor='mt', font=gfx.font('ariblk.ttf', 74), fill='#96caff')
    d.text((540, 1590), 'Synthetic visual - no real person', anchor='mt', font=gfx.font('segoeuib.ttf', 38), fill='#b2c0d3')
    image.save(ROOT / 'assets/broll/demo_source.png')
    sr = 48000
    rng = np.random.default_rng(42)
    for i, name in enumerate(['pop', 'pop2', 'click3', 'keyboard', 'swipe', 'whoosh_fast', 'ui_click', 'whoosh', 'ui_appear', 'shutter', 'logo_appear', 'buildup', 'sparkle']):
        length = 1.4 if name == 'keyboard' else .75 if 'whoosh' in name or name in ['swipe', 'buildup', 'sparkle'] else .2
        t = np.arange(int(sr * length)) / sr
        envelope = np.minimum(t / .008, 1) * np.exp(-t / max(.025, length / 5))
        if 'whoosh' in name or name == 'swipe':
            sound = rng.normal(0, .12, t.shape) * np.sin(np.pi * t / length) ** 2
        else:
            sound = (.15 * np.sin(2 * np.pi * (520 + 80 * i) * t) + rng.normal(0, .025, t.shape)) * envelope
        temp = ROOT / 'output' / (name + '_generated.wav')
        wav(temp, sound)
        dest = ROOT / 'assets/sfx' / (name + ('.wav' if name == 'sparkle' else '.mp3'))
        if dest.suffix == '.wav':
            shutil.copy2(temp, dest)
        else:
            run(['ffmpeg', '-y', '-v', 'error', '-i', str(temp), '-c:a', 'libmp3lame', '-b:a', '128k', str(dest)])
    t = np.arange(sr * 18) / sr
    # Test tone bed replaces narration; timing text is illustrative, NOT a real transcript.
    voice = .12 * np.sin(2 * np.pi * 220 * t) * (.65 + .35 * np.sin(2 * np.pi * 2.2 * t))
    wav(ROOT / 'output/demo_tone.wav', voice)
    music = sum(.035 * np.sin(2 * np.pi * f * t) for f in [130.81, 164.81, 196]) * np.sin(np.pi * t / 18) ** 2
    wav(ROOT / 'assets/music/demo_ambient.wav', music)
    if assets_only:
        return
    run(['ffmpeg', '-n', '-v', 'error', '-loop', '1', '-i', str(ROOT / 'assets/broll/demo_source.png'), '-i', str(ROOT / 'output/demo_tone.wav'), '-t', '18', '-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', str(ROOT / 'raw/demo.mp4')])
    phrases = ['Start with words.', 'Show the screen.', 'List clear examples.', 'Ask a question.', 'Stack useful cards.', 'Remove a myth.', 'Check the facts.', 'Bring it together.', 'One simple action.']
    segments = [{'i': i + 1, 'start': i * 2, 'end': (i + 1) * 2, 'text': text} for i, text in enumerate(phrases)]
    words = []
    for s in segments:
        tokens = s['text'].split()
        for j, w in enumerate(tokens):
            st = s['start'] + .15 + j * 1.6 / len(tokens)
            words.append({'seg': s['i'], 'w': w, 'start': round(st, 4), 'end': round(st + 1.5 / len(tokens), 4)})
    job = ROOT / 'transcript/demo'
    save(job / 'segments.json', {'clip': 'raw/demo.mp4', 'duration': 18, 'fps': 30, 'fps_str': '30/1', 'width': 1080, 'height': 1920, 'model': 'synthetic-demo-NOT-ASR', 'segments': segments})
    save(job / 'words.json', words)
    save(job / 'cuts.json', {'keep': list(range(1, 10)), 'captions': False})
    dynamic = {'base': 'output/demo_clean.mp4', 'face_center': [540, 850], 'split_face_top': 300, 'grade': 'eq=contrast=1:saturation=1',
               'caption_style': {'size': 64, 'accent': '#65caff', 'pill': True, 'font': 'Inter.ttf', 'face_y': 1622, 'split_y': 960, 'full_y': 1450},
               'highlight': ['WORDS', 'FACTS', 'ACTION'], 'music': {'file': 'assets/music/demo_ambient.wav', 'db': -16, 'start': 0}, 'layout': [], 'graphics': [], 'sfx': []}
    for i in range(9):
        mode = ['face', 'split', 'full'][i % 3]
        l = {'start': i * 2, 'end': (i + 1) * 2, 'mode': mode, 'zoom': [1, 1.02]}
        if mode != 'face':
            l.update(broll=f'assets/broll/demo_{i % 3 + 1}.png', kb=[1, 1.04])
        dynamic['layout'].append(l)
    dynamic['graphics'] = [
        {'type': 'text_hook', 'start': 0, 'end': 2, 'text': 'WORD-TIMED EDITS', 'size': 66, 'y': 300},
        {'type': 'title', 'start': 2, 'end': 4, 'text': 'DEMO', 'sub': 'Your project', 'logo': 'assets/gfx/demo_logo.png', 'y': 300},
        {'type': 'hud', 'start': 4, 'end': 6},
        {'type': 'logo_card', 'start': 6, 'end': 8, 'logo': 'assets/gfx/demo_logo.png', 'tag': 'EXAMPLE', 'y': 350},
        {'type': 'stamp', 'start': 12, 'end': 14, 'text': 'FACT', 'kind': 'check', 'y': 350},
        {'type': 'comment', 'start': 16, 'end': 18, 'text': 'GUIDE', 'type_at': .2, 'per_char': .08, 'y': 330}]
    dynamic['sfx'] = [{'t': i * 2, 'file': 'assets/sfx/pop.mp3', 'db': -12} for i in range(9)]
    save(job / 'edit.json', dynamic)
    logo = 'assets/gfx/demo_logo.png'
    scenes = [
        {'type': 'counter', 'start': 0, 'end': 2, 'logo': logo, 'number': 3, 'unit': 'steps', 'title': 'Example workflow', 'count_at': .2},
        {'type': 'window', 'start': 2, 'end': 4, 'media': 'assets/broll/demo_1.png', 'title': 'Your demonstration', 'cursor': [{'t': 3, 'from': [40, 40], 'x': 450, 'y': 220}]},
        {'type': 'tiles', 'start': 4, 'end': 6, 'items': [{'t': 4.15 + i * .3, 'img': f'assets/broll/demo_{i+1}.png', 'label': 'Example ' + str(i+1)} for i in range(3)]},
        {'type': 'chat', 'start': 6, 'end': 8, 'title': 'Example chat', 'q': 'What can I try?', 'a': 'Start with one clear example.', 'q_t0': 6.1, 'q_t1': 6.65, 'a_t0': 7, 'a_t1': 7.75},
        {'type': 'stack', 'start': 8, 'end': 10, 'cards': [{'t': 8.1, 'kind': 'github', 'owner': 'example', 'repo': 'sample-project', 'chips': ['Demo', 'Open source']}, {'t': 8.5, 'kind': 'logo', 'img': logo, 'h': 110, 'tag': 'EXAMPLE'}]},
        {'type': 'strike', 'start': 10, 'end': 12, 'title': 'Example myth', 'sub': 'Verify before publishing', 'strike_at': 10.8},
        {'type': 'checklist', 'start': 12, 'end': 14, 'title': 'Review', 'rows': [{'t': 12.15, 'icon': '✓', 'name': 'Timing', 'desc': 'Words first'}, {'t': 12.5, 'icon': '✓', 'name': 'Audio', 'desc': 'Clear voice'}]},
        {'type': 'converge', 'start': 14, 'end': 16, 'media': 'assets/broll/demo_2.png', 'title': 'One workflow', 'chips_at': 14.1, 'merge_at': 15, 'chips': [{'x': 190, 'y': 180, 'label': 'Words'}, {'x': 900, 'y': 740, 'label': 'Visuals'}]},
        {'type': 'comment', 'start': 16, 'end': 18, 'title': 'One clear action', 'placeholder': 'Write a comment...', 'text': 'GUIDE', 'type_at': 16.2, 'per_char': .08, 'send_at': 17.2}]
    hf = {'base': 'output/demo_clean.mp4', 'name': 'demo-motion-cards', 'theme': 'light', 'caption_style': 'capsule', 'caption_y': 900, 'emphasis': ['words', 'facts'], 'face_center': [540, 850], 'cut_src_top': 330,
          'layout': [{'start': 0, 'end': 16, 'mode': 'top', 'zoom': [1, 1]}, {'start': 16, 'end': 18, 'mode': 'face', 'zoom': [1, 1]}], 'scenes': scenes, 'music': {'file': 'assets/music/demo_ambient.wav', 'db': -16, 'start': 0}, 'sfx': []}
    save(job / 'hf_plan.json', hf)
    save(ROOT / 'examples/hf_all_scenes_light.json', hf)
    save(ROOT / 'examples/hf_all_scenes_dark.json', dict(hf, theme='dark', caption_style='mono'))
    save(ROOT / 'examples/dynamic_all_graphics.json', dynamic)
    save(ROOT / 'templates/cuts.json', {'keep': [1, 2, 3], 'captions': False, 'edits': {}})
    save(ROOT / 'templates/speaker.json', {'scale': .68, 'head_top_src': 370, 'head_y': 1015, 'card_top': 1130, 'card_w': 720, 'radius': 64})
    save(ROOT / 'templates/edit.json', {'base': 'output/CLIP_clean.mp4', 'face_center': [540, 800], 'split_face_top': 350, 'caption_style': {'size': 72, 'accent': '#65caff', 'pill': False, 'font': 'Inter.ttf', 'face_y': 1622}, 'highlight': [], 'music': None, 'layout': [{'start': 0, 'end': 1, 'mode': 'face', 'zoom': [1, 1]}], 'graphics': [], 'sfx': []})
    save(ROOT / 'templates/hf_plan.json', {'base': 'output/CLIP_clean.mp4', 'name': 'topic-clean', 'theme': 'light', 'caption_y': 900, 'caption_style': 'mono', 'emphasis': [], 'face_center': [540, 800], 'cut_src_top': 350, 'speaker': {'scale': .68, 'head_top_src': 370, 'head_y': 1015, 'card_top': 1130, 'card_w': 720, 'radius': 64}, 'music': None, 'layout': [{'start': 0, 'end': 1, 'mode': 'top', 'zoom': [1, 1]}], 'scenes': [], 'sfx': []})
    print('Created an 18-second synthetic demo and reusable generated assets. No ASR/API call.')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--doctor', action='store_true'); ap.add_argument('--model', action='store_true'); ap.add_argument('--demo', action='store_true')
    ap.add_argument('--skip-browser', action='store_true', help='Doctor skips browser launch for dynamic-only setup')
    a = ap.parse_args()
    if a.model: model()
    if a.demo: demo()
    if a.doctor: doctor(skip_browser=a.skip_browser)
    if not any([a.model, a.demo, a.doctor]): ap.print_help()
