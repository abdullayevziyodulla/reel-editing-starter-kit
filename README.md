# Reel Editing Starter Kit

A complete folder for AI-assisted vertical talking-head editing with Python, FFmpeg and the real HyperFrames framework for HTML motion graphics. Unzip anywhere, install the tools, add **your own** footage, and ask your editing assistant to read `CLAUDE.md` or `AGENTS.md`.

This is a clean reusable method, not a copy of someone's media library. It contains no real faces, creator profile photos, private transcripts, channel records, personal prompts, account IDs, API keys or purchased music/SFX packs. The demo uses geometric placeholders, illustrative English text and a test tone rather than a real person or voice.

**Uzbek quick start:** `START_HERE_UZ.md`. **AI handoff prompt:** `PROMPT_FOR_YOUR_AI.md`.

## What is included

- Full pipeline: speech-region detection → Gemini text → Whisper word alignment → cuts → composition → final audio verification.
- Dynamic style: face/split/full b-roll, punch-ins, animated titles, HUD, logo cards, myth/fact stamps, typing CTA, word-timed captions.
- Clean motion-card style: light/dark canvas, 9 scene types, animated browser windows, list tiles, chats, stacks, counters and optional speaker head breakout.
- Font portability: bundled Inter and italic Playfair Display with their OFL license files; no Windows font copying or network font dependency during rendering.
- Pinned HyperFrames CLI, framework-managed Chrome, media timeline, GSAP seeking, snapshots, Studio preview and MP4 rendering.
- Unique job creation and reuse for reordered variants; raw→output word timing export, plan validation and review-frame extraction.
- Generic two-pass final-mix normalization and decoded loudness/true-peak/full-decode checks.
- Empty credential template, tested direct dependency versions, setup scripts, troubleshooting, plan reference, reusable templates, synthetic demo and inspectable example renders.
- Procedurally generated UI sounds, a plain demo logo, placeholder b-roll and a small ambient test bed, all generated for this kit.
- Commons downloader which keeps source/author/license metadata instead of silently losing attribution.

**Not included:** your editing assistant subscription, Gemini account/key, Python/FFmpeg binaries, third-party music packs, real speaker footage, facial cutouts or a pre-downloaded Whisper model. Internet is needed for installation, optional model downloads and new Gemini transcription. Existing/imported transcripts and rendering can run without an API key. This is a local rendering toolkit, not a one-click AI that decides edits by itself: you or your AI write the plans.

## 1. Install

Tested platform: **Windows, Python 3.12, Node.js 22+, FFmpeg on PATH**. Paths/browser/fonts are portable, and `setup.sh` is supplied for macOS/Linux, but that platform setup has not been tested here. Prefer a short folder path such as `C:\Projects\reel-editing-starter-kit`.

Install Node.js 22+ from https://nodejs.org/ (LTS recommended), Python 3.12 from https://www.python.org/downloads/ and FFmpeg using an installation option linked from https://ffmpeg.org/download.html. Make sure `node --version`, `npm --version`, `ffmpeg -version` and `ffprobe -version` work in a new terminal. FFmpeg needs H.264 (`libx264`), AAC, MP3 encoding and the `loudnorm`, `ebur128`, `sidechaincompress`, `subtitles` filters.

From PowerShell inside the unpacked folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

That creates a **new local** `.venv`, installs `requirements.txt` and the locked npm dependencies, ensures the HyperFrames Chrome browser, downloads the optional official selfie segmentation model and runs the environment check. Nothing is installed into another editing folder. The execution-policy flag applies to this invocation. If you do not want the head breakout model yet, use `-SkipModel`. If using only the dynamic renderer, `-SkipBrowser` skips browser setup/check; ensure the HyperFrames browser before using motion cards.

You can also run each step yourself:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
npm ci
.venv/Scripts/python.exe -X utf8 scripts/hyperframes_cli.py browser ensure
.venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --model
.venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --doctor
```

For macOS/Linux, install Python 3.12, Node.js 22+ and FFmpeg first, then `sh setup.sh`. Use `.venv/bin/python` instead of `.venv/Scripts/python.exe`. HyperFrames Chrome may require OS libraries on Linux; follow its diagnostics. A GPU is not required. Whisper uses CPU/int8. Start with one capture worker and short 1080p projects on a MacBook Air; this kit has not yet been benchmarked on an M2.

## 2. Test without private footage or API calls

`raw/demo.mp4` and `transcript/demo/` are included. Their words are explicitly **illustrative**, not an actual ASR transcript. The source is 18 seconds, 1080×1920, 30 fps, with a test tone. It demonstrates all three dynamic layouts, all six graphic types and all nine HTML scene types. No real portrait is present; the demo intentionally omits `speaker`.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/render.py raw/demo.mp4
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py timing raw/demo.mp4
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py validate raw/demo.mp4 --style dynamic
.venv/Scripts/python.exe -X utf8 scripts/compose.py raw/demo.mp4 --preview
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py frames raw/demo.mp4 output/demo_edit_preview.mp4 --times 0.6,2.6,4.6,6.6,12.6,17
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py validate raw/demo.mp4 --style hf
.venv/Scripts/python.exe -X utf8 scripts/compose_hf.py raw/demo.mp4 --frames 0.6,2.6,4.8,7.4,8.7,11,12.8,15.3,17.3
```

Open the HyperFrames PNGs under `transcript/demo/check/hyperframes/` (dynamic frames are directly under `check/`) and **look at them**. The packaged example renders/review sheets are under `examples/previews/` so you can compare before spending time on a full render. To test dark mode, copy `examples/hf_all_scenes_dark.json` into `transcript/demo/hf_plan.json`. Restore the light example afterward if desired.

After inspection:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/compose.py raw/demo.mp4
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py finalize output/demo_edit.mp4 demo-dynamic
```

Or run `compose_hf.py` without `--frames`/`--preview` and finalize `output/demo_nick.mp4`. The `_nick` suffix is retained for pipeline compatibility; the generic style is called clean motion cards in this kit. Only a normalized, verified video is promoted to `final/`.

## 3. Create your own editing job

Jobs are keyed by the **clip filename stem**, not the title in a plan. Use a unique ASCII name for each clip or variant. Start with portrait 9:16 footage with clear speech and sufficient room above the head. Both compositors work on a normalized 1080×1920 canvas at 30 fps; non-9:16 source is stretched, so prepare portrait footage first.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py init "D:\My Videos\take.mp4" my_clip
```

This copies your video into `raw/my_clip.mp4`, creates `transcript/my_clip/check/`, and refuses to overwrite an existing job. Your original remains untouched.

### New transcription

Create your own Gemini API key through https://aistudio.google.com/ and keep it locally. Copy `.env.example` to `.env` and fill **only the new local file**. Do not upload it, print it, paste it in chat or share a working folder containing it. Alternatively set `GEMINI_API_KEY` in your process environment. Transcription defaults to `gemini-3.5-flash`, then tries `gemini-3.8-flash` and `gemini-flash-latest` after retries. This restores the original project's model order. Blank `GEMINI_MODEL`, or its bundled value `gemini-3.5-flash`, uses that chain. A different `GEMINI_MODEL` selects only that model; `--model` overrides all settings and also selects only that model. Availability depends on your account; see https://ai.google.dev/gemini-api/docs/models.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/transcribe.py raw/my_clip.mp4 --language "Uzbek (Latin script)"
.venv/Scripts/python.exe -X utf8 scripts/align.py raw/my_clip.mp4 --language uz
```

Gemini writes the spelling; Whisper supplies estimated word times. Review unusual names and low-confidence timing yourself. Alignment is heuristic character matching and can interpolate missing words; it is not guaranteed exact. The `small` Whisper model downloads on first use; `--model` can point to a compatible local model. See https://github.com/SYSTRAN/faster-whisper.

New Gemini transcription sends audio to Google's API and may incur charges. Existing `segments.json`/`words.json` are retained unless `--force` is explicitly supplied. Never retranscribe just to make an edit variant.

### Already have a transcript?

Place your **own** `segments.json` and `words.json` in `transcript/my_clip/`, following `docs/PLAN_REFERENCE.md`. If only sentence text is available, prepare audio, then align:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py audio raw/my_clip.mp4
.venv/Scripts/python.exe -X utf8 scripts/align.py raw/my_clip.mp4 --language uz
```

## 4. Decide cuts and create the new timeline

Write `transcript/my_clip/cuts.json` from `templates/cuts.json`. `keep` contains segment numbers **in playback order**, not sorted raw order. `captions:false` prevents duplicate captions during composition. Do not repeat a segment ID in one job: the core caption mapper expects unique IDs.

```json
{"keep": [3, 1, 2, 5], "captions": false, "edits": {}}
```

Optional `edits` can override a segment's raw start/end/text. Text changes require corresponding word data; never assume old word times match a rewritten sentence. Padding is limited by neighboring raw speech and rounded to the source frame grid.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/render.py raw/my_clip.mp4
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py timing raw/my_clip.mp4
```

`render.py` writes `pieces.json` and `output/my_clip_clean.mp4`. `timing` writes `timeline.json` containing every kept word on the NEW output timeline.

**Every card, caption, b-roll cut and sound effect must use these mapped word anchors:**

`output time = accumulated previous piece duration + raw word time − current piece.start`

After any reorder or trim, render the clean base again, export timing again, and rebuild all dependent plans. Copying old scene times makes the wrong visuals appear on the new sentences. `docs/EDITING_METHOD.md` explains the method.

## 5. Add your assets and plan

Use short, descriptive relative paths under `assets/`. Do not download random face references. Add your own cleared screen recordings, logos and short GIFs/video/stills. Verify official logos before use. For Commons still images:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fetch_commons.py plane "airliner flight" 3
```

Inspect the downloaded images. The filename or search result is not proof of what's depicted. License/source records are stored in `assets/broll/commons_sources.json`; satisfy attribution and any other applicable terms. The kit's procedural demo assets can be used or replaced freely under the kit's license. Purchased packs are intentionally not bundled.

Copy the appropriate template to your job and write its actual times:

- Dynamic: `templates/edit.json` → `transcript/my_clip/edit.json`.
- Motion cards: `templates/hf_plan.json` → `transcript/my_clip/hf_plan.json`.

Replace every `CLIP` and placeholder duration. Use the example plans as syntax references, **not** timing templates. All scene/graphic times are output seconds. Dynamic graphic `type_at` is a local offset; HTML comment `type_at` is an absolute output time. Full field details: `docs/PLAN_REFERENCE.md`.

The `speaker` object lets the segmented head emerge above a narrow rounded card. Keep it for a real clean-card job, and calibrate it to the actual frame. The included coordinates are an example on the **scaled 1080×1920 source**, not a universally safe crop. Never crop hair to fill the card. `card_w` must be smaller than `1080 * scale`; inspect mouth/caption separation and all zoom extremes. Use `bootstrap.py --model` before rendering with `speaker`. Omitting `speaker` uses a simpler arched crop.

## 6. Preview, inspect, then render

```powershell
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py validate raw/my_clip.mp4 --style dynamic
.venv/Scripts/python.exe -X utf8 scripts/compose.py raw/my_clip.mp4 --preview
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py frames raw/my_clip.mp4 output/my_clip_edit_preview.mp4 --times 0.5,3,7
```

Choose frame times which actually exist in your video; inspect each scene, transition, emphasized word and CTA. Check full head visibility, captions away from the mouth, no black edges, no empty windows, accurate images, readable dark cards and clean safe margins. Listen to the mix as well. Validation can detect file/timeline mistakes, but cannot judge visual or semantic correctness.

For motion cards:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py validate raw/my_clip.mp4 --style hf
.venv/Scripts/python.exe -X utf8 scripts/compose_hf.py raw/my_clip.mp4 --frames 0.5,3,7
```

Run the chosen composer without preview flags only after fixing the review frames. Music starts around -16 dB in the examples, but source mastering varies: instrumental only, listen and adjust, retain sidechain ducking. No single dB setting guarantees a good mix. The dynamic compositor decodes GIFs/videos into RAM, so keep those assets short. HyperFrames handles motion-card media playback and capture; its wrapper defaults to one worker. Full renders can take minutes; use frame checks first.

### Edit the real HyperFrames project directly

`compose_hf.py` builds a self-contained project under `transcript/my_clip/hyperframes/`. Its HTML has a HyperFrames composition root, timed video/audio clips and a registered paused GSAP timeline. HyperFrames owns playback, capture and output encoding; Python prepares the speaker/background and complete audio mix. Fonts, GSAP and media are local. Rendering does not require an API key.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/compose_hf.py raw/my_clip.mp4 --prepare
.venv/Scripts/python.exe -X utf8 scripts/hyperframes_cli.py preview transcript/my_clip/hyperframes
.venv/Scripts/python.exe -X utf8 scripts/hyperframes_cli.py check transcript/my_clip/hyperframes --at 0.5,3,7
.venv/Scripts/python.exe -X utf8 scripts/hyperframes_cli.py render transcript/my_clip/hyperframes --workers 1 --output output/my_clip_nick.mp4
```

Edit generated `index.html` and `runtime.js` with your AI or HyperFrames Studio. After direct HTML edits, snapshot/render that project with the CLI: rerunning `compose_hf.py` rebuilds generated files from the JSON plan. `--preview` captures a draft then resizes the output to 540×960; capture itself remains 1080×1920. See `docs/HYPERFRAMES.md`.

## 7. Normalize and deliver

```powershell
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py finalize output/my_clip_edit.mp4 2026-10-03_topic_dynamic
# Motion cards: use output/my_clip_nick.mp4 as the input instead.
```

Finalization normalizes the **complete mix**, retains video without re-encoding, uses AAC headroom, measures decoded `ebur128` true peak, checks integrated loudness within ±0.3 LUFS of -14 and peak ≤ -1 dBTP, then performs a full decode check. Reports/logs are under `output/verification/`. It will not overwrite a previous final without `--replace` and will not promote a failed verification.

`final/` contains only finished videos. Thumbnail assets belong under `output/thumbnails/`, not `final/`.

## Variants without retranscribing

```powershell
.venv/Scripts/python.exe -X utf8 scripts/toolkit.py init raw/my_clip.mp4 my_clip_v2 --reuse my_clip
```

This validates identical source footage and copies the existing transcript/alignment/audio/chunks to a new job. It does **not** reuse the old cut map or visual plans. Write new `cuts.json`, render, map words again, and build a new plan. Vary hook/order, useful length, visual treatment, instrumental bed and caption look. Do not promise any platform's repost detection can be bypassed.

## Sharing and troubleshooting

Send the original clean kit ZIP, not your working folder after adding footage and credentials. `scripts/package_clean.py` uses an explicit allowlist and refuses to package unreviewed files. Check `docs/PRIVACY_AND_ASSETS.md`. See `docs/TROUBLESHOOTING.md` for setup, fonts, timing, captions, memory, browser and audio problems. The Python test suite is `python -m unittest discover -s tests -v`.

License: source code, docs and procedural demo assets are MIT; bundled fonts keep their separate OFL licenses. External libraries/models/assets keep their upstream terms. See `LICENSE` and `THIRD_PARTY_NOTICES.md`. This toolkit is independent of FFmpeg, Google, HeyGen/HyperFrames and any reference creator; no affiliation is implied.
