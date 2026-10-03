# Copy this message to your editing assistant

I want you to edit my vertical talking-head footage in this folder. Read AGENTS.md, CLAUDE.md and README.md first. Use the existing pipeline and my own media, not a new unrelated toolchain.

Source: raw/REPLACE_WITH_MY_CLIP.mp4
Language: REPLACE_WITH_LANGUAGE (default Uzbek Latin script)
Style: choose dynamic, clean motion cards light, or clean motion cards dark based on the content.
Goal: a natural short vertical edit with a clear hook, useful demonstration, readable captions and one CTA.

First check whether this clip already has segments.json and words.json. Reuse them. Do not retranscribe or realign unless absent, or unless I explicitly ask. Never print/read .env or expose credentials; the transcription script may consume my local key internally if needed. Keep my originals intact and create unique jobs for variants.

Make the cut order coherent and propose the meaningful editorial cuts. Run render.py, then toolkit.py timing. Build all card, b-roll, caption and SFX times from mapped words on this new output timeline. Pick actual relevant assets and record provenance. Don't claim a test/result I didn't demonstrate. Don't use placeholder demo images in the finished edit.

Validate the plan. Before every full render, render representative check frames and LOOK at them. Fix cropped hair, captions over my mouth, empty gaps, incorrect images, unreadable text and black card edges. Keep the speaker card narrower than the scaled source; calibrate head and mouth positions to my footage. Listen to the mix and choose instrumental music with ducking.

After composition, finalize the whole mix at -14 LUFS and decoded true peak ≤ -1 dBTP using toolkit.py finalize. Keep only completed verified videos in final/. Deliver the video path, measured duration/loudness and a concise explanation of the edit. Do not post/upload anything unless I ask.
