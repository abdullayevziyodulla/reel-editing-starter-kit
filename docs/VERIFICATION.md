# Release verification — HyperFrames 1.1.1, 2026-10-03

Tested on Windows with Python 3.12.10, Node.js 24.20.0, FFmpeg 9.0.1 and pinned HyperFrames 0.8.114. Python dependencies use the previously verified kit venv. Node dependencies are installed with `npm ci`. The Python lock remains a Windows/Python 3.12 reference.

Passed checks:

- 1.1.1 restores the original Gemini transcription model order. Offline tests cover default/fallback behavior, configuration precedence and cached-transcript reuse. No live Gemini transcription was performed for this patch.

- All Python scripts compile; PowerShell setup parses.
- Required imports, bundled Inter font loading and the actual HyperFrames CLI/browser pass.
- Official optional segmentation model downloads; MediaPipe speaker-card path executes on the synthetic frame (no real face used).
- Six timing regression tests: raw→output reorder, intro offset, clipped words, both caption builders' chronology, padding around neighboring speech, and rejection of duplicate/missing IDs.
- Both plan validators pass on the demo.
- Dynamic half-resolution preview reviewed at six representative points.
- Native HyperFrames lint, runtime, layout and contrast checks pass for both light and dark demos with zero errors or warnings. All nine scene types were visually reviewed in both themes.
- Full 18-second 1080×1920/30fps motion-card render completes through the actual HyperFrames CLI; final encoded video inspected at nine timestamps. The dynamic example is retained from the verified 1.0 release.
- Complete-mix two-pass normalization, decoded ebur128 and full decode pass for both example videos.
- ZIP relocation is checked separately with fresh Node dependencies, timing tests and real HyperFrames snapshots from a folder containing spaces.
- Cached transcription/alignment exit without replacing data or making an ASR/API call.
- Imported reordered variant reuses identical demo footage/transcript; order 9/1/7 maps correctly to a 6-second base.
- Clean repack includes only original audited distribution files, excluding a new variant, unlisted sentinel file and generated runtime HTML.
- Dark capsule captions checked separately in top and face modes; dark text remains readable on white capsules.
- Moving b-roll renders through persistent HyperFrames video clips. Forward/backward/repeated seeking produces identical media pixels; tiny whole-frame text-antialiasing differences were at most two RGB levels.

| Demo | Duration | Integrated loudness | Decoded true peak |
|---|---:|---:|---:|
| Dynamic | 18.000s | -14.0 LUFS | -6.3 dBTP |
| HyperFrames motion cards (1.1) | 18.000s | -14.0 LUFS | -8.0 dBTP |

The demo tone has a different crest factor from speech; these values prove the finalizer/check pipeline, not a music setting for everyone's real recordings. Inspect examples/previews/ for videos, visual review sheets and machine-readable measurements.

The source workspace's footage, finals, faces, transcripts, credentials and existing pipeline scripts were not modified. The kit was prepared separately from reviewed code and generic/new assets. No new ASR call or paid API transcription was used for this release.

Limits: actual Gemini account/model transcription was not exercised; neither was a new Whisper model download/alignment of real speech. Human-head segmentation quality needs inspection on each person's footage. macOS/Linux setup is supplied but has not been tested on an M2. Windows timings do not predict M2 performance. Optional Docker diagnostics may fail without affecting local rendering. The release uses an allowlisted manifest with ZIP integrity, privacy and checksum checks.
