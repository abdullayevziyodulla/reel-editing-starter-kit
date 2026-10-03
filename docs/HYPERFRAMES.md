# Real HyperFrames rendering

This kit uses **hyperframes 0.8.114**, installed from npm with a committed lockfile. `compose_hf.py` invokes its actual CLI for lint, snapshots and full MP4 rendering. It no longer renders HTML through a custom Playwright screenshot loop.

## Install

Install Python 3.12, Node.js 22+ (LTS recommended) and FFmpeg. Run `setup.ps1` on Windows or `sh setup.sh` on macOS/Linux. Manual Node/browser setup:

```sh
npm ci
python scripts/hyperframes_cli.py browser ensure
python scripts/hyperframes_cli.py doctor
```

Use your kit's `.venv` Python for all Python commands. Node dependencies live in this kit's `node_modules/`, which is excluded from distribution. HyperFrames manages its own Chrome cache. The wrapper disables automatic version upgrades so the tested lock stays authoritative. No HeyGen subscription or API key is needed for local rendering. Optional AI authoring/transcription providers have their own costs.

## Pipeline

1. Keep the existing transcript, cuts, word mapping and `hf_plan.json` workflow.
2. Python prepares a muted speaker/background MP4 and the complete narration/music/SFX mix. Head breakout still uses the optional local MediaPipe model. This preparation contains no HTML capture.
3. The plan generates `transcript/<clip>/hyperframes/index.html`, a registered paused GSAP timeline, persistent media clips, local fonts and assets.
4. HyperFrames owns the composition clock, media visibility/playback, timeline seeking, snapshots, frame capture, audio assembly and final video encoding.
5. `toolkit.py finalize` normalizes and verifies the complete final mix.

The HTML root declares `data-composition-id="reel"`, duration, dimensions and fps. Timed media declare `class="clip"`, start, duration and track. The GSAP timeline is registered as `window.__timelines['reel']`. The bundled scene renderer uses a GSAP-controlled value to reconstruct the same graphics at any timestamp, including backward/random seeks. JavaScript never plays or seeks the videos itself.

## Author and review

```sh
python scripts/compose_hf.py raw/my_clip.mp4 --prepare
python scripts/hyperframes_cli.py preview transcript/my_clip/hyperframes
python scripts/hyperframes_cli.py lint transcript/my_clip/hyperframes
python scripts/hyperframes_cli.py check transcript/my_clip/hyperframes --at 0.5,3,7
python scripts/compose_hf.py raw/my_clip.mp4 --frames 0.5,3,7
python scripts/compose_hf.py raw/my_clip.mp4 --workers 1
```

Choose timestamps inside your actual video. Open and inspect the PNGs, listen to the audio, then render. `check` diagnoses runtime, layout and contrast but does not replace visual review. Decorative overlaps may need interpretation; fix actual unreadable or clipped content.

After editing generated HTML/JS directly, render with `hyperframes_cli.py render <project> --workers 1 --output output/my_clip_nick.mp4`. Rerunning the plan wrapper regenerates those files. Keep durable reusable changes in `scripts/hf/` or your own source templates.

Other official CLI capabilities are available through the wrapper, such as `catalog`, `add`, `timeline`, `keyframes`, `snapshot`, or `preview`; consult the installed command's `--help`. For custom authoring, your assistant can install the official agent skills with `npx skills add heygen-com/hyperframes` in the kit folder. Those optional skills are maintained upstream; the packaged renderer remains pinned. Installed Catalog items retain their upstream licenses and should be reviewed before redistributing. The original clean kit does not include another creator's assets or generated user projects.

## MacBook Air M2 / 16 GB

Start with short 1080×1920/30fps jobs and one capture worker (the wrapper default). Preview/frame checks avoid repeated full renders. Background preparation is reused when its footage and geometry are unchanged. More workers can increase RAM use. `--preview` captures full-size draft frames then downsizes the video; it is not half-size browser capture. macOS setup is supplied but has not been tested on an M2 in this Windows release.

## Official references

- Repository and license: https://github.com/heygen-com/hyperframes (Apache 2.0).
- Quick start: https://hyperframes.heygen.com/quickstart
- Composition contract: https://hyperframes.heygen.com/concepts/compositions
- GSAP animation: https://hyperframes.heygen.com/guides/gsap-animation
- CLI reference: https://hyperframes.heygen.com/packages/cli

Missing Node/package: run `npm ci` in the kit. Missing browser: run `hyperframes_cli.py browser ensure`. A render failure: run `doctor`, `lint`, and `check`, then retain the first exact error. Doctor may report unavailable optional Docker tools; Docker is not required for local rendering. Never place credentials in the composition or upload a project containing private footage without authorization.
