# Editing instructions

Read README.md, docs/EDITING_METHOD.md and docs/PLAN_REFERENCE.md. For motion graphics also read docs/HYPERFRAMES.md and use the pinned real HyperFrames CLI. This folder is an independent starter kit. The demo is entirely synthetic; never treat its illustrative words as an actual speaker transcript.

## Workflow

- Use Python 3.12 in this folder's .venv with UTF-8; use FFmpeg for media operations. Do not edit the user's original source. Import via toolkit.py init with a unique ASCII clip name.
- Check for existing segments.json / words.json before transcription/alignment. Retain them. A variant reuses byte-identical footage and its transcript, never repeats API transcription.
- Never print, inspect or share .env or credential values. Internal transcription may consume the local key; if unavailable, ask the user to configure it privately. Do not create custom key-handling scripts.
- Choose cuts based on the speaker's actual words. Explain substantial meaning/order changes. Set captions:false. keep is segment IDs IN PLAYBACK ORDER; IDs must be unique.
- Run render.py then toolkit.py timing. Every visual/SFX anchor comes from words.json mapped to the new pieces. Recompute after every reorder or trim. Keep mapping sorted by output time.
- Plan times are absolute output seconds, except dynamic graphics' type_at, which is local. Do not use a raw timestamp as an output timestamp.
- Use existing assets first; fetch new Commons stills with fetch_commons.py and retain source/license metadata. Verify actual image contents and official logos. Use only assets the user can use legally; do not copy another creator's faces or private material.

## Two styles

- Dynamic (compose.py): face / split / full; jump-cut zooms, short b-roll montages, logo/stamp/comment/text_hook/HUD graphics; up to 3-word captions. Keep captions away from the mouth.
- Real HyperFrames motion cards (compose_hf.py): light/dark theme, scene types counter/window/tiles/chat/stack/strike/checklist/converge/comment; 1–2-word captions with mono/capsule/serif emphasis options. Keep the speaker object for real talking-head work and calibrate it. Never substitute a custom Playwright capture loop or Remotion.
- Source geometry is normalized to 1080x1920; speaker coordinates must be measured there. Full hair/head must remain visible. Card narrower than scaled video; no black sides. Never shrink the face width or change identity for a cover.
- Do not assume the sample crop and zoom values work on new footage. Review mouth/hair positions throughout the clip.

## Required quality checks

- Run toolkit.py validate for the chosen style. Check missing files, layout coverage, scene times, caption order, model availability and card width.
- Before each full composition, dynamic: --preview then extract check PNGs; motion cards: --frames. LOOK at the pictures. Inspect every scene type, montage item, important word and CTA. Fix overlaps/gaps/inaccurate visuals before rendering.
- Use instrumental beds, roughly -16 dB as a starting point, and sidechain ducking. Mastering varies, so listen; keep speech intelligible and SFX restrained.
- After composition normalize the complete mix with toolkit.py finalize. Target -14 LUFS ±.3; decoded true peak ≤ -1 dBTP; full decode must pass. Normalizing narration alone is insufficient.
- final/ is for finished verified MP4s only; previews, frames, plans, reports and thumbnails go elsewhere.
- No uploading/posting without the user's instruction. Show the output file and measured duration, explain the edit briefly.

## Optional covers

Use the person's own original identity photo on every generation/edit; avoid cumulative face drift, wide faces and pale/small hands. Match full-size adult hands to the person's actual skin tone. Keep full head and key headline/subject inside the centered preview crop; inspect 9:16, center square and 3:4 crops. Borrow general readability principles (big logos, concise text), not a creator's exact layout or face. Store under output/thumbnails/. No personal face is bundled.

## Sharing

Never share this working folder after importing a person's media. Use the original clean distribution ZIP, or the allowlisted clean package helper plus privacy review. No footage, transcripts, faces, account records, generated runtime HTML, local paths, logs or secrets belong in a clean starter kit.
