"""Transcribe a raw clip: FFmpeg finds the pauses (exact timing), Gemini writes the Uzbek text.

Usage: python scripts/transcribe.py raw/clip.mp4 [--noise -35] [--min-silence 0.30]
Output: transcript/<clip>/segments.json  (never re-transcribes if it exists; use --force)
"""
import argparse
import os
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from dotenv import dotenv_values
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODELS = ("gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest")
MODELS = list(DEFAULT_MODELS)


def select_models(model=None, config=None):
    """Use the original fallback chain unless the user chooses a custom model."""
    if model and model.strip():
        return [model.strip()]
    config = config or {}
    configured = (os.environ.get("GEMINI_MODEL") or "").strip()
    configured = configured or (config.get("GEMINI_MODEL") or "").strip()
    if configured and configured != DEFAULT_MODELS[0]:
        return [configured]
    return list(DEFAULT_MODELS)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,r_frame_rate,width,height",
               "-of", "json", str(path)]).stdout
    info = json.loads(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = map(int, v["r_frame_rate"].split("/"))
    return {"duration": float(info["format"]["duration"]), "fps": num / den, "fps_str": v["r_frame_rate"],
            "width": v["width"], "height": v["height"]}


def find_speech(wav, duration, noise, min_sil):
    log = run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", f"silencedetect=noise={noise}dB:d={min_sil}",
               "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    silences = list(zip(starts, ends + [duration] * (len(starts) - len(ends))))
    speech, cur = [], 0.0
    for s, e in silences:
        if s - cur > 0.15:
            speech.append((round(cur, 3), round(s, 3)))
        cur = e
    if duration - cur > 0.15:
        speech.append((round(cur, 3), round(duration, 3)))
    return speech, silences


def cut_audio(wav, start, end, dest):
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start}", "-to", f"{end}", "-i", str(wav),
         "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "64k", str(dest)])
    return dest.read_bytes()


PROMPT = """You are transcribing raw talking-head footage for a video editor. The speaker is speaking {language}, possibly mixed with other languages.
You get {n} short audio pieces, each labelled "Segment <i>". Transcribe each one EXACTLY as spoken:
- Keep filler sounds (ee, aa, mm, hmm), false starts, repeated words and cut-off words. Mark cut-off words with "-".
- Write Uzbek in Latin script with correct o', g', sh, ch spelling. Keep Russian/English words as spoken.
- If a piece has no speech (breath, noise, music), return "".
- Do NOT merge, translate or fix grammar.
Return JSON only: [{{"i": 1, "text": "..."}}, ...] with exactly {n} items."""


def transcribe(client, chunks):
    parts = [PROMPT.format(n=len(chunks), language=os.environ.get("TRANSCRIPT_LANGUAGE", "Uzbek (Latin script)"))]
    for i, data in enumerate(chunks, 1):
        parts.append(f"Segment {i}:")
        parts.append(types.Part.from_bytes(data=data, mime_type="audio/mp3"))
    last_err = None
    for model in MODELS:
        for attempt in range(3):
            try:
                r = client.models.generate_content(
                    model=model, contents=parts,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
                items = json.loads(r.text)
                texts = {int(x["i"]): x["text"] for x in items}
                return [texts.get(i, "") for i in range(1, len(chunks) + 1)], model
            except Exception as e:  # rate limit or model unavailable: retry, then fall back
                last_err = e
                time.sleep(5 * (attempt + 1))
    sys.exit(f"Gemini failed after retries ({type(last_err).__name__}); check your model, account access and network. Credentials are not logged.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--noise", type=float, default=-35)
    ap.add_argument("--min-silence", type=float, default=0.30)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", help="Use only this Gemini model; otherwise 3.5 Flash with fallbacks")
    ap.add_argument("--language", default="Uzbek (Latin script)")
    a = ap.parse_args()
    os.environ["TRANSCRIPT_LANGUAGE"] = a.language

    clip = Path(a.clip).resolve()
    job = ROOT / "transcript" / clip.stem
    out = job / "segments.json"
    if out.exists() and not a.force:
        print(f"Already transcribed: {out}")
        return
    config = dotenv_values(ROOT / ".env")
    MODELS[:] = select_models(a.model, config)
    (job / "chunks").mkdir(parents=True, exist_ok=True)

    info = probe(clip)
    wav = job / "audio16k.wav"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(clip), "-vn", "-ac", "1", "-ar", "16000", str(wav)])

    speech, silences = find_speech(wav, info["duration"], a.noise, a.min_silence)
    if not speech:
        sys.exit("No speech regions found; adjust --noise or --min-silence.")
    chunks = [cut_audio(wav, s, e, job / "chunks" / f"{i:03d}.mp3") for i, (s, e) in enumerate(speech, 1)]

    key = (os.environ.get("GEMINI_API_KEY") or config.get("GEMINI_API_KEY", "")).strip().strip("\"'")
    if not key:
        sys.exit("Set your own GEMINI_API_KEY locally. Never paste it into chat.")
    texts, model = transcribe(genai.Client(api_key=key), chunks)

    result = {"clip": str(clip), "model": model, **info,
              "silence": {"noise_db": a.noise, "min_silence": a.min_silence},
              "segments": [{"i": i, "start": s, "end": e, "text": t}
                           for i, ((s, e), t) in enumerate(zip(speech, texts), 1)]}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for seg in result["segments"]:
        print(f'{seg["i"]:>3}  {seg["start"]:7.2f}-{seg["end"]:7.2f}  {seg["text"]}')
    print(f"\n{len(speech)} segments, model {model} -> {out}")


if __name__ == "__main__":
    main()
