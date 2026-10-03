# Troubleshooting

| Problem | What to check |
|---|---|
| Python package/native wheel fails | Use Python 3.12 64-bit and a fresh .venv, then requirements.txt. Avoid mixing another project's environment. |
| ffmpeg/ffprobe not found | Install both and add their bin directory to PATH; reopen the terminal. Check -version. |
| Chromium executable missing | Run python -m playwright install chromium in this venv. No Edge installation is required. |
| Use existing Edge instead | Set HF_BROWSER_CHANNEL=msedge in the process environment. This is optional and only works where Edge is installed. |
| Browser Linux dependency error | Follow Playwright's OS dependency instructions; platform setup outside Windows is not tested in this kit. |
| Font cannot open | Ensure assets/fonts contains Inter.ttf and PlayfairDisplay-Italic.ttf. Don't substitute Windows font paths; OFL files are included. |
| Existing transcript but API/model error | Do not transcribe again. Use existing segments/words, write cuts, render. Pass a current --model only for genuinely new transcription. |
| Gemini model unavailable/rate limit | Verify the current audio-capable model ID and account access; retry later. The script retries three times and avoids logging credential-bearing exception details. |
| Words are misspelled | Correct Gemini segment text and regenerate matching alignment intentionally. Don't adopt Whisper's ASR spelling as authoritative Uzbek. |
| Audio already available but PyAV errors | Alignment already passes FFmpeg numpy audio into Whisper; don't change it back to a PyAV filename path. |
| Caption times are wrong after reorder | Rebuild pieces, export timing and remake plans. Word arrays must be sorted on the new output timeline. |
| Duplicate captions | cuts.json must set captions:false before render. Compose supplies word-timed captions. |
| Unexpected layout/black gap | Layout must cover the actual base duration continuously; toolkit validation detects gaps/overlaps. |
| Missing b-roll | Plan paths are relative to the kit root. Check file case/path and official image contents; use asset logs. |
| Memory explodes | Shorten/resize GIF/video b-roll. Media loads every frame into RAM; don't feed hour-long recordings. |
| White captions on white capsules | This kit fixes capsule text to dark in light/dark/face modes. Keep that fix when editing runtime.js. |
| Cropped head | Lower zoom; measure head_top_src on normalized source; move head_y/card_top; inspect each extreme. |
| Black side edges on speaker card | card_w must be narrower than 1080*scale and video must extend throughout the card height. |
| Head ghost/segmentation crash | Use the official model; mask numpy_view must be copied. Check foreground channel dimensions. Preview hair before a full render. |
| Caption covers mouth | Inspect actual frames. Change face_y/split_y/full_y or HF geometry/caption_y; face mode HF center is 1420 in runtime.js. |
| Short SFX causes negative fade error | Kit clamps fade start/duration; max must be >0. Prefer short clips with gentle fades. |
| Audio measured too loud/peak | Finalize the entire mix, not just voice. Failed outputs remain in output/verification, never final/. |
| Silent demo expected to sound like speech | It uses a test tone. Its labels are illustrative, not transcribed narration. |
| Final filename already exists | Choose a unique name. --replace is explicit and only for intended replacement. |
| Sharer worries about personal files | Send the original distribution ZIP. Do not zip the working folder after adding your footage, faces or .env. |

For dependency troubleshooting, `scripts/bootstrap.py --doctor` tests FFmpeg presence, imports, font loading and an actual Chromium launch. `requirements-lock-windows-py312.txt` records the complete freshly installed test environment as an optional reproducibility reference. Avoid printing environment variables or credential files when diagnosing.
