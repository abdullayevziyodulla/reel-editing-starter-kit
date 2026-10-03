# Third-party notices and provenance

The kit does not redistribute Python, Node.js, FFmpeg, HyperFrames Chrome, Whisper models, MediaPipe models or another creator's media. Setup installs/downloads tools from their providers. The requirements and npm lock files identify packages; use their upstream licenses.

| Component | Source / terms |
|---|---|
| Inter variable font | https://github.com/google/fonts/tree/main/ofl/inter ; assets/fonts/Inter-OFL.txt (SIL OFL 1.1) |
| Playfair Display italic variable font | https://github.com/google/fonts/tree/main/ofl/playfairdisplay ; assets/fonts/PlayfairDisplay-OFL.txt (SIL OFL 1.1) |
| FFmpeg | https://ffmpeg.org/legal.html ; license depends on the selected distribution/build |
| Pillow | https://github.com/python-pillow/Pillow/blob/main/LICENSE |
| NumPy | https://github.com/numpy/numpy/blob/main/LICENSE.txt |
| google-genai | https://github.com/googleapis/python-genai |
| python-dotenv | https://github.com/theskumar/python-dotenv |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper ; includes separate upstream model/dependency terms |
| MediaPipe | https://github.com/google-ai-edge/mediapipe ; model reference: https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter |
| HyperFrames 0.8.114 | https://github.com/heygen-com/hyperframes ; Apache 2.0; installed from npm, not bundled |
| GSAP 3.14.2 | https://gsap.com/community/standard-license/ ; installed from npm; copied only into the user's generated local projects |
| Chrome Headless Shell | Downloaded/managed by HyperFrames; browser distributions have separate notices |

The optional model URL is https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite and bootstrap.py records the downloaded SHA-256. It is deliberately not bundled in the ZIP; consult provider/model terms when using it.

Demo graphics, play-button logo, source video, illustrative words, music test bed and SFX were procedurally authored for this kit by scripts/bootstrap.py. These generated media assets contain no real faces, voices, accounts or external footage and are covered by the kit's MIT license. The runtime's GitHub repository card includes a GitHub mark for identifying that service; GitHub branding retains its owner's rights and is not relicensed by this kit (https://github.com/logos). Font upstream notices are preserved verbatim. Font SHA-256 checksums are recorded in DISTRIBUTION_MANIFEST.json alongside the other distribution files.
