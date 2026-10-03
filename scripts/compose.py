"""Compose the final edit from transcript/<clip>/edit.json: layouts (face / split / full b-roll),
punch-in zooms, animated graphics, keyword captions, music bed with ducking and SFX.

Usage: python scripts/compose.py raw/clip.mp4 [--preview]   (--preview renders at half resolution, fast)
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import gfx  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,nb_frames:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return s["width"], s["height"], float(j["format"]["duration"]), int(s.get("nb_frames") or 0)


class Media:
    """A b-roll source: still image or animated GIF/video, decoded once at native size."""

    def __init__(self, path):
        self.path = ROOT / path
        if self.path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            self.frames = [Image.open(self.path).convert("RGB")]
            self.fps = 1
            return
        w, h, dur, n = probe(self.path)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.path), "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-fps_mode", "passthrough", "-"], capture_output=True, check=True).stdout
        arr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
        self.frames = [Image.fromarray(f) for f in arr]
        self.fps = len(self.frames) / dur if dur else 10

    def get(self, t):
        return self.frames[int(t * self.fps) % len(self.frames)]


def cover(img, bw, bh, zoom=1.0, fx=0.5, fy=0.5):
    """Crop img to the box aspect (zoomed, focus point fx, fy) and resize to bw x bh."""
    iw, ih = img.size
    s = max(bw / iw, bh / ih) * zoom
    cw, ch = bw / s, bh / s
    x = clamp((iw - cw) * fx, 0, iw - cw)
    y = clamp((ih - ch) * fy, 0, ih - ch)
    return img.resize((bw, bh), Image.BILINEAR, box=(x, y, x + cw, y + ch))


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, p):
    return a + (b - a) * p


def face_zoom(frame, z, cx, cy):
    cw, ch = W / z, H / z
    x = clamp(cx - cw / 2, 0, W - cw)
    y = clamp(cy - ch / 2, 0, H - ch)
    return frame.resize((W, H), Image.BILINEAR, box=(x, y, x + cw, y + ch))


def build_captions(job, highlight):
    """Caption groups (max 3 words, broken at punctuation) on the output timeline, from words.json."""
    from toolkit import mapped_words
    words = mapped_words(job)['words']
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append({"w": w["w"].upper(), "start": w["start"], "end": w["end"],
                    "seg": w["seg"]})
        nxt = words[i + 1] if i + 1 < len(words) else None
        if len(cur) == 3 or w["w"][-1] in ".,!?" or nxt is None or nxt["seg"] != w["seg"]:
            groups.append({"start": cur[0]["start"], "end": cur[-1]["end"], "words": [c["w"] for c in cur]})
            cur = []
    for g, n in zip(groups, groups[1:]):  # hold each group until the next one if the gap is short
        if n["start"] - g["end"] < 0.4:
            g["end"] = n["start"]
    return groups


def mix_audio(e, base, dur, out):
    ins = ["-i", str(base)]
    music = e.get("music")
    filt = [f"[0:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,asplit=2[voice][vsc]"]
    mixes = ["[voice]"]
    k = 1
    if music:
        ins += ["-stream_loop", "-1", "-i", str(ROOT / music["file"])]
        st = music.get("start", 0)
        filt.append(f"[{k}:a]atrim={st}:{st + dur},asetpts=PTS-STARTPTS,aresample=48000,volume={music['db']}dB,"
                    f"afade=t=in:d={min(.6, dur / 2)},afade=t=out:st={max(0, dur - 1.5)}:d={min(1.5, dur)}[mraw]")
        filt.append("[mraw][vsc]sidechaincompress=threshold=0.02:ratio=5:attack=15:release=350[music]")
        mixes.append("[music]")
        k += 1
    for s in e.get("sfx", []):
        ins += ["-i", str(ROOT / s["file"])]
        ms = int(s["t"] * 1000)
        trim = f"atrim=0:{s['max']}," if "max" in s else ""
        fade = f"afade=t=out:st={max(0, s['max'] - 0.15)}:d={min(.15, s['max'])}," if "max" in s else ""
        filt.append(f"[{k}:a]{trim}{fade}aresample=48000,volume={s.get('db', -6)}dB,adelay={ms}|{ms}[s{k}]")
        mixes.append(f"[s{k}]")
        k += 1
    filt.append(f"{''.join(mixes)}amix=inputs={len(mixes)}:normalize=0:duration=first,"
                f"alimiter=limit=0.89:level=false[out]")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(filt), "-map", "[out]",
                        "-c:a", "aac", "-b:a", "192k", str(out)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)


def main():
    clip = Path(sys.argv[1]).resolve()
    preview = "--preview" in sys.argv
    job = ROOT / "transcript" / clip.stem
    e = json.loads((job / "edit.json").read_text(encoding="utf-8"))
    base = ROOT / e["base"]
    _, _, dur, _ = probe(base)
    n_frames = int(round(dur * FPS))

    media = {}
    for L in e["layout"]:
        if L.get("broll") and L["broll"] not in media:
            media[L["broll"]] = Media(L["broll"])
    highlight = {w.upper() for w in e.get("highlight", [])}
    caps = build_captions(job, highlight)
    intro = e.get('intro_duration', 0)
    for c in caps:
        c['start'] += intro
        c['end'] += intro
    cap_style = e.get('caption_style', {})
    face_cx, face_cy = e.get("face_center", [540, 800])
    split_y = e.get("split_face_top", 300)
    grade = e.get("grade", "eq=contrast=1.06:saturation=1.12:brightness=0.01")

    t_audio = time.time()
    audio = job / "mix.m4a"
    mix_audio(e, base, dur, audio)
    print(f"audio mixed in {time.time() - t_audio:.1f}s")

    out = ROOT / "output" / f"{clip.stem}_edit{'_preview' if preview else ''}.mp4"
    ow, oh = (W // 2, H // 2) if preview else (W, H)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(base), "-vf", f"fps={FPS},scale={W}:{H},{grade}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}",
                            "-r", str(FPS), "-i", "-", "-i", str(audio), "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "veryfast" if preview else "medium",
                            "-crf", "23" if preview else "17", "-pix_fmt", "yuv420p", "-c:a", "copy",
                            "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)

    t_start = time.time()
    for i in range(n_frames):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        t = i / FPS
        cam = Image.frombuffer("RGB", (W, H), buf)
        L = next((l for l in e["layout"] if l["start"] <= t < l["end"]), {"mode": "face", "zoom": [1, 1]})
        p = (t - L.get("start", 0)) / max(1e-6, L.get("end", dur) - L.get("start", 0))
        lt = t - L.get("start", 0)
        enter = 1 + 0.07 * (1 - gfx.ease_out(lt / 0.2)) if L.get("enter", True) else 1.0  # scale-in on cut
        mode = L["mode"]
        if mode == "face":
            z0, z1 = L.get("zoom", [1, 1])
            frame = face_zoom(cam, lerp(z0, z1, p), face_cx, face_cy)
        else:
            m = media[L["broll"]]
            kb0, kb1 = L.get("kb", [1.0, 1.08])
            src = m.get(L.get("from", 0) + lt)
            fx, fy = L.get("focus", [0.5, 0.5])
            if mode == "full":
                frame = cover(src, W, H, lerp(kb0, kb1, p) * enter, fx, fy)
            else:  # split: b-roll on top, face below
                frame = Image.new("RGB", (W, H))
                frame.paste(cover(src, W, H // 2, lerp(kb0, kb1, p) * enter, fx, fy), (0, 0))
                frame.paste(cam.crop((0, split_y, W, split_y + H // 2)), (0, H // 2))
                frame.paste((255, 255, 255), (0, H // 2 - 3, W, H // 2 + 3))
        frame = frame.convert("RGBA")

        for g in e.get("graphics", []):
            if g["start"] <= t < g["end"]:
                res = gfx.GRAPHICS[g["type"]](t - g["start"], g["end"] - g["start"], g)
                if res:
                    img, x, y = res
                    frame.alpha_composite(img, (max(0, x), max(0, y)),
                                          (max(0, -x), max(0, -y)) if x < 0 or y < 0 else (0, 0))

        cap = next((c for c in caps if c["start"] <= t < c["end"]), None)
        if cap:
            img = gfx.caption_img(cap["words"], frozenset(highlight), cap_style.get('size', 76),
                                  cap_style.get('accent', '#ffd400'), cap_style.get('pill', False),
                                  cap_style.get('font', 'ariblk.ttf'))
            ct = t - cap["start"]
            s = 0.88 + 0.12 * gfx.ease_back(ct / 0.12) if ct < 0.12 else 1.0
            if s != 1.0:
                img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
            cy = cap_style.get(mode + '_y', {"split": H // 2, "full": int(H * 0.76)}.get(mode, int(H * 0.845)))
            frame.alpha_composite(img, ((W - img.width) // 2, cy - img.height // 2))

        if preview:
            frame = frame.resize((ow, oh), Image.BILINEAR)
        enc.stdin.write(frame.convert("RGB").tobytes())
        if i % 150 == 0:
            print(f"frame {i}/{n_frames}  {time.time() - t_start:.0f}s", flush=True)

    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("FFmpeg encoding failed")
    dec.terminate()
    print(f"done in {time.time() - t_start:.0f}s -> {out}")


if __name__ == "__main__":
    main()
