# Release verification — 2026-10-03

Tested on Windows with Python 3.12.10 and a newly created venv installed from this kit's requirements. `pip check` reports no broken requirements. The complete resolved package list is provided separately as a Windows/Python 3.12 lock reference.

Passed checks:

- All Python scripts compile; PowerShell setup parses.
- Required imports, bundled Inter font loading and a real Playwright Chromium launch pass.
- Official optional segmentation model downloads; MediaPipe speaker-card path executes on the synthetic frame (no real face used).
- Six timing regression tests: raw→output reorder, intro offset, clipped words, both caption builders' chronology, padding around neighboring speech, and rejection of duplicate/missing IDs.
- Both plan validators pass on the demo.
- Dynamic half-resolution preview reviewed at six representative points.
- All nine motion-card scene types reviewed individually in both light and dark themes; light capsules including full-face mode and dark mono captions are readable.
- Full 18-second dynamic and motion-card renders complete.
- Complete-mix two-pass normalization, decoded ebur128 and full decode pass for both example videos.
- ZIP extracted to a separate folder containing spaces; scripts compile and tests pass there, both renderers' plan validation works, and local-font Chromium frames render correctly.
- Cached transcription/alignment exit without replacing data or making an ASR/API call.
- Imported reordered variant reuses identical demo footage/transcript; order 9/1/7 maps correctly to a 6-second base.
- Clean repack includes only original audited distribution files, excluding a new variant, unlisted sentinel file and generated runtime HTML.
- Dark capsule captions checked separately in top and face modes; dark text remains readable on white capsules.

| Demo | Duration | Integrated loudness | Decoded true peak |
|---|---:|---:|---:|
| Dynamic | 18.000s | -14.0 LUFS | -6.3 dBTP |
| Clean motion cards | 18.000s | -14.0 LUFS | -4.8 dBTP |

The demo tone has a different crest factor from speech; these values prove the finalizer/check pipeline, not a music setting for everyone's real recordings. Inspect examples/previews/ for videos, visual review sheets and machine-readable measurements.

The source workspace's footage, finals, faces, transcripts, credentials and existing pipeline scripts were not modified. The kit was prepared separately from reviewed code and generic/new assets. No new ASR call or paid API transcription was used for this release.

Limits: actual Gemini account/model transcription was not exercised; neither was a new Whisper model download/alignment of real speech. Those paths are configurable and retain the original text/alignment method. Human-head segmentation quality still needs inspection on each person's own footage. macOS/Linux setup is supplied but not tested here. The release uses an allowlisted manifest with ZIP integrity, privacy and checksum checks.
