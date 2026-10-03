"""Build the cut from transcript/<clip>/cuts.json and render it, with optional burned-in captions.

cuts.json: {"keep": [1, 2, 4, ...], "edits": {"5": {"start": 22.9}}, "captions": true}
  keep    segment numbers from segments.json, in playback order
  edits   optional per-segment time or text overrides
Usage: python scripts/render.py raw/clip.mp4
Output: output/<clip>_cut.mp4, transcript/<clip>/captions.ass
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAD_BEFORE, PAD_AFTER = 0.10, 0.15  # air around each kept piece, seconds
WORDS_PER_CAPTION = 3


def snap(t, fps):
    return round(t * fps) / fps


def build_pieces(segs, keep, edits, fps, duration):
    by_i = {s["i"]: dict(s) for s in segs}
    for k, v in edits.items():
        by_i[int(k)].update(v)
    if not keep or len(set(keep)) != len(keep):
        raise ValueError("keep must be nonempty and contain unique segment IDs; create a new job for variants")
    if set(keep) - set(by_i):
        raise ValueError("Unknown segment ID in keep")
    kept = [by_i[i] for i in keep]
    # pad, but never reach into the neighbouring segment in the raw (cut or kept)
    order = sorted(by_i.values(), key=lambda s: s["start"])
    pieces = []
    for s in kept:
        idx = order.index(s) if s in order else next(j for j, o in enumerate(order) if o["i"] == s["i"])
        prev_end = order[idx - 1]["end"] if idx > 0 else 0.0
        next_start = order[idx + 1]["start"] if idx + 1 < len(order) else duration
        start = max(s["start"] - PAD_BEFORE, (prev_end + s["start"]) / 2, 0.0)
        end = min(s["end"] + PAD_AFTER, (s["end"] + next_start) / 2, duration)
        if snap(end, fps) <= snap(start, fps):
            raise ValueError("Invalid/empty trimmed segment")
        pieces.append({"i": s["i"], "start": snap(start, fps), "end": snap(end, fps), "text": s["text"],
                       "speech_start": s["start"], "speech_end": s["end"]})
    return pieces


def ass_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_captions(pieces, w, h, path):
    size = round(h * 0.040)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial Black,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,{round(size*0.09)},{round(size*0.05)},2,80,80,{round(h*0.20)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines, t0 = [], 0.0
    for p in pieces:
        words = p["text"].split()
        if words:
            # speech window inside this piece, on the output timeline
            a = t0 + (p["speech_start"] - p["start"])
            b = t0 + (p["speech_end"] - p["start"])
            groups = [words[k:k + WORDS_PER_CAPTION] for k in range(0, len(words), WORDS_PER_CAPTION)]
            total = sum(len(" ".join(g)) for g in groups)
            cur = a
            for g in groups:
                txt = " ".join(g)
                dur = (b - a) * len(txt) / total
                lines.append(f"Dialogue: 0,{ass_time(cur)},{ass_time(cur + dur)},Cap,,0,0,0,,{txt.upper()}")
                cur += dur
        t0 += p["end"] - p["start"]
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return t0


def main():
    clip = Path(sys.argv[1]).resolve()
    job = ROOT / "transcript" / clip.stem
    seg = json.loads((job / "segments.json").read_text(encoding="utf-8"))
    cuts = json.loads((job / "cuts.json").read_text(encoding="utf-8"))
    fps, w, h = seg["fps"], seg["width"], seg["height"]

    pieces = build_pieces(seg["segments"], cuts["keep"], cuts.get("edits", {}), fps, seg["duration"])
    (job / "pieces.json").write_text(json.dumps(pieces, ensure_ascii=False, indent=2), encoding="utf-8")

    parts, labels = [], []
    for n, p in enumerate(pieces):
        parts.append(f"[0:v]trim=start={p['start']:.6f}:end={p['end']:.6f},setpts=PTS-STARTPTS[v{n}]")
        parts.append(f"[0:a]atrim=start={p['start']:.6f}:end={p['end']:.6f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.01,afade=t=out:st={p['end'] - p['start'] - 0.01:.6f}:d=0.01[a{n}]")
        labels.append(f"[v{n}][a{n}]")
    parts.append(f"{''.join(labels)}concat=n={len(pieces)}:v=1:a=1[vc][ac]")

    total = None
    if cuts.get("captions", True):
        total = write_captions(pieces, w, h, job / "captions.ass")
        parts.append("[vc]subtitles=captions.ass[vout]")  # relative: ffmpeg runs inside the job folder
        vout = "[vout]"
    else:
        vout = "[vc]"

    out = ROOT / "output" / f"{clip.stem}_{'cut' if cuts.get('captions', True) else 'clean'}.mp4"
    out.parent.mkdir(exist_ok=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(clip),
           "-filter_complex", ";".join(parts), "-map", vout, "-map", "[ac]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-fps_mode", "passthrough", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, cwd=job, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(r.stderr)

    expected = sum(p["end"] - p["start"] for p in pieces)
    got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True).stdout)
    print(f"{len(pieces)} pieces, raw {seg['duration']:.2f}s -> cut {got:.2f}s (expected {expected:.2f}s)")
    print(out)


if __name__ == "__main__":
    main()
