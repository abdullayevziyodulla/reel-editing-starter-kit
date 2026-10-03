"""Real HyperFrames motion-card entry point and reusable speaker/caption helpers.
Off-white/dark canvas, HTML cards, segmented speaker, word-timed captions and UI sounds.

Plan: transcript/<clip>/hf_plan.json   Usage: python scripts/compose_hf.py raw/clip.mp4 [--preview] [--frames 0.5,3.2]
"""
import random
import sys
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parent.parent
HF = Path(__file__).parent / "hf"
W, H, FPS = 1080, 1920, 30
CUT_TOP = 980  # speaker cutout starts here in "top" mode


def background(theme='light'):
    if theme == 'dark':
        return Image.new('RGB', (W, H), '#0E0F12')
    bg = Image.new("RGB", (W, H), (247, 246, 243))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((-200, -300, W + 200, 1300), fill=255)
    bg = Image.composite(Image.new("RGB", (W, H), (252, 252, 250)), bg, glow.filter(ImageFilter.GaussianBlur(220)))
    leaves = Image.new("L", (W, H), 0)  # soft plant shadows, top right
    d = ImageDraw.Draw(leaves)
    rnd = random.Random(7)
    for _ in range(14):
        x, y = rnd.randint(650, 1150), rnd.randint(-100, 650)
        d.ellipse((x - 140, y - 38, x + 140, y + 38), fill=255)
    leaves = leaves.rotate(-28, center=(900, 250)).filter(ImageFilter.GaussianBlur(28))
    shade = Image.new("RGB", (W, H), (205, 203, 196))
    return Image.composite(shade, bg, leaves.point(lambda v: int(v * 0.16)))


def arch_mask(w, h, r=120):
    m = Image.new("L", (w, h + r), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h + r - 1), r, fill=255)
    return m.crop((0, 0, w, h))


def rounded(img, r):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255)
    return m


class Speaker:
    """Speaker in a narrower rounded card; the head breaks out above the card's top edge (person segmentation)."""

    def __init__(self, cfg):
        self.s = cfg.get("scale", 0.68)              # source -> screen scale
        self.head_src = cfg.get("head_top_src", 370)  # head top in the source frame
        self.head_y = cfg.get("head_y", 975)          # where the head top lands on screen
        self.card_top = cfg.get("card_top", 1090)
        self.card_w = cfg.get("card_w", int(W * self.s) - 8)  # narrower than the video, never wider (black edges)
        self.r = cfg.get("radius", 64)
        x0 = (W - self.card_w) // 2
        self.card_box = (x0, self.card_top, x0 + self.card_w, H + self.r)
        self.card_mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(self.card_mask).rounded_rectangle(self.card_box, self.r, fill=255)
        self.above = Image.new("L", (W, H), 0)
        ImageDraw.Draw(self.above).rectangle((0, 0, W, self.card_top + self.r), fill=255)
        sh = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sh).rounded_rectangle((x0, self.card_top + 14, x0 + self.card_w, H + 200), self.r, fill=70)
        self.shadow = sh.filter(ImageFilter.GaussianBlur(28))
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mpt.BaseOptions(model_asset_path=str(ROOT / "assets/models/selfie_segmenter.tflite")),
            output_confidence_masks=True))
        self.prev = None

    def person(self, cam):
        m = self.seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(cam))).confidence_masks[0]
        m = m.numpy_view()[..., 0].copy()
        self.prev = m if self.prev is None else 0.8 * m + 0.2 * self.prev  # temporal smoothing, no flicker
        return Image.fromarray((np.clip((self.prev - 0.5) / 0.25, 0, 1) * 255).astype(np.uint8))

    def draw(self, frame, cam, z=1.0):
        s = self.s * z
        sw, shh = int(W * s), int(H * s)
        px, py = (W - sw) // 2, int(self.head_y - self.head_src * s - (z - 1) * 120)
        spk = cam.resize((sw, shh), Image.BILINEAR)
        frame.paste((198, 196, 190), (0, 0, W, H), self.shadow)
        layer = Image.new("RGB", (W, H))
        layer.paste(spk, (px, py))
        frame.paste(layer, (0, 0), self.card_mask)
        pm = Image.new("L", (W, H), 0)
        pm.paste(self.person(cam).resize((sw, shh), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.5)), (px, py))
        frame.paste(layer, (0, 0), Image.fromarray(np.minimum(np.asarray(pm), np.asarray(self.above))))
        return frame


def chunk_captions(job):
    from toolkit import mapped_words
    words = [dict(w, s=w['start'], e=w['end']) for w in mapped_words(job)['words']]
    caps, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        long_ = len(w["w"]) >= 9 or (nxt and len(nxt["w"]) >= 9)
        if len(cur) == 2 or w["w"][-1] in ".,!?" or long_ or not nxt or nxt["seg"] != w["seg"]:
            caps.append({"start": cur[0]["s"], "end": cur[-1]["e"], "words": [c["w"] for c in cur]})
            cur = []
    for c, n in zip(caps, caps[1:]):
        if n["start"] - c["end"] < 0.45:
            c["end"] = n["start"]
    return caps


def auto_sfx(plan):
    S = "assets/sfx/"
    out = []
    add = lambda t, f, db, mx=None: out.append({"t": round(t, 3), "file": S + f, "db": db, **({"max": mx} if mx else {})})
    for sc in plan["scenes"]:
        k = sc["type"]
        add(sc["start"], "ui_appear.mp3" if k in ("window", "converge") else "pop.mp3", -9)
        for i, it in enumerate(sc.get("items", [])):
            add(it["t"], "pop2.mp3" if i % 2 else "pop.mp3", -9)
        for c in sc.get("cards", [])[1:]:
            add(c["t"], "pop.mp3", -8)
        for r in sc.get("rows", []):
            add(r["t"], "click3.mp3", -8)
        if k == "checklist":
            add(sc["rows"][-1]["t"] + 0.15, "sparkle.wav", -16, 1.0)
        for c in sc.get("cursor", []):
            add(c["t"], "click3.mp3", -5)
        if k == "chat":
            add(sc["q_t0"], "keyboard.mp3", -15, round(sc["q_t1"] - sc["q_t0"], 2))
            add(sc["a_t0"], "pop2.mp3", -10)
        if k == "strike":
            add(sc["strike_at"], "swipe.mp3", -5)
        if k == "converge":
            add(sc["merge_at"], "whoosh_fast.mp3", -10)
        if k == "comment":
            add(sc["type_at"], "keyboard.mp3", -10, round(len(sc["text"]) * sc["per_char"] + 0.1, 2))
            add(sc["send_at"], "ui_click.mp3", -6)
    prev = None
    for L in plan["layout"]:
        if L["mode"] == "face" and prev != "face":
            add(L["start"], "whoosh.mp3", -14)
        prev = L["mode"]
    return sorted(out, key=lambda s: s["t"])


def main():
    from hyperframes_pipeline import main as compose_with_hyperframes
    compose_with_hyperframes()


if __name__ == "__main__":
    main()
