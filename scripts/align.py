"""Word-level timing: Whisper listens for WHEN words are said; Gemini's text stays the source of truth for spelling.

Usage: python scripts/align.py raw/clip.mp4 [--model small]
Reads transcript/<clip>/segments.json + chunks/, writes transcript/<clip>/words.json:
  [{"seg": 2, "w": "samolyotlar,", "start": 5.62, "end": 6.31}, ...]   (raw clip seconds)
"""
import argparse
import difflib
import json
import re
from pathlib import Path

import subprocess

import numpy as np
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("ʻ", "").replace("’", "").replace("'", ""))


def align_segment(gem_words, whis, seg_start, seg_end):
    """Map Gemini words onto Whisper word times by character-level alignment of the two word streams."""
    g_str, g_owner = "", []
    for i, w in enumerate(gem_words):
        n = norm(w) or "_"
        g_str += n
        g_owner += [i] * len(n)
    w_str, w_time = "", []
    for ww in whis:
        n = norm(ww.word)
        if not n:
            continue
        step = (ww.end - ww.start) / len(n)
        for k in range(len(n)):
            w_str += n[k]
            w_time.append(ww.start + k * step)
    times = [[None, None] for _ in gem_words]
    sm = difflib.SequenceMatcher(None, g_str, w_str, autojunk=False)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            i = g_owner[a + k]
            t = w_time[b + k]
            if times[i][0] is None:
                times[i][0] = t
            times[i][1] = t
    # fill gaps by interpolating between known neighbours, weighted by word length
    known = [i for i, t in enumerate(times) if t[0] is not None]
    if not known:
        span = seg_end - seg_start
        lens = [len(w) + 1 for w in gem_words]
        cur = seg_start
        out = []
        for w, L in zip(gem_words, lens):
            d = span * L / sum(lens)
            out.append((cur, cur + d))
            cur += d
        return out
    for i, t in enumerate(times):
        if t[0] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            a = times[prev][1] if prev is not None else seg_start
            b = times[nxt][0] if nxt is not None else seg_end
            lo = prev + 1 if prev is not None else 0
            hi = nxt if nxt is not None else len(times)
            lens = [len(gem_words[k]) + 1 for k in range(lo, hi)]
            pos = sum(lens[: i - lo])
            times[i] = [a + (b - a) * pos / sum(lens), a + (b - a) * (pos + lens[i - lo]) / sum(lens)]
    out = []
    for i, (s, e) in enumerate(times):
        nxt_start = times[i + 1][0] if i + 1 < len(times) else seg_end
        e = max(e + 0.06, s + 0.08)  # last matched char is the start of the last letter
        out.append((max(seg_start, s), min(e, nxt_start, seg_end)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default="uz", help="Whisper language code, e.g. uz or en")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    job = ROOT / "transcript" / Path(a.clip).stem
    if (job / "words.json").exists() and not a.force:
        print("Already aligned; use --force to replace word times.")
        return
    seg = json.loads((job / "segments.json").read_text(encoding="utf-8"))
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    words = []
    for s in seg["segments"]:
        gem = s["text"].split()
        if not gem:
            continue
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(s["start"]), "-to", str(s["end"]),
                              "-i", str(job / "audio16k.wav"), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                             capture_output=True, check=True).stdout
        res, _ = model.transcribe(np.frombuffer(pcm, np.float32), language=a.language, word_timestamps=True, initial_prompt=s["text"],
                                  vad_filter=False, beam_size=5)
        whis = [w for r in res for w in (r.words or [])]
        for w, (st, en) in zip(gem, align_segment(gem, whis, 0.0, s["end"] - s["start"])):
            words.append({"seg": s["i"], "w": w, "start": round(s["start"] + st, 3), "end": round(s["start"] + en, 3)})
        print(f"seg {s['i']}: {len(whis)} whisper words -> {len(gem)} words")
    (job / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {job / 'words.json'}")


if __name__ == "__main__":
    main()
