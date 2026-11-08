---
name: beat-transition-edit
description: "The trending beat edit from the How to do this with Claude series (Ep 1): your dance or twirl video in smooth slow motion, cutting to your photos on every music hit with a quick zoom-blur dissolve and a warm film grade, copied from any reference reel. Use when the user asks for a beat transition edit or types /beat-transition-edit with your model video, 3+ photos, the song MP3 and the reference reel."
---

# Beat transition edit

The trending beat edit from the How to do this with Claude series (Ep 1): your dance or twirl video in smooth slow motion, cutting to your photos on every music hit with a quick zoom-blur dissolve and a warm film grade, copied from any reference reel.

**Input:** your model video, 3+ photos, the song MP3 and the reference reel.
**Run it:** `/beat-transition-edit` and attach or name the files.

## Steps

1. Here is my model video, my photos, my song MP3 and a reference reel. Analyze the reference reel at 2 frames per second: find every transition, how long each shot stays, the beat it cuts on, and the colour grading.
2. Find the beat and every music hit in the song (librosa). Cut on the same grid as the reference, usually every hit.
3. Play my video in smooth slow motion (half speed; interpolate if it's 30 fps) on one continuous clock, so the motion carries on every time it comes back.
4. Alternate it with my photos on each hit. Each photo keeps its own slow zoom, which continues on every return.
5. Use a short zoom-blur dissolve on each cut and the same colour grade as the reference (for a warm film look: lift the blacks, soften the whites, warm the tint, add a vignette and fine grain).
6. Use the song as the audio, 9:16 at 1080×1920. Show me a contact sheet first, then render.

## Every time it runs

- Transcribe my audio with word-level timings, so every graphic lands on the word I say.
- Keep text out of the top 250 px and the bottom 420 px (Instagram buttons and caption).
- Render a 1080×1920 MP4 at 30 fps with my original audio. Never re-grade or filter my face unless the skill says so.
- Show me 3 snapshots before the final render, and ask before overwriting files.

## Helper scripts

Run from this skill's folder (`.claude/skills/beat-transition-edit/`).

- `scripts/ref_analyze.py`: breaks a reference reel down: frames at 2 fps into a folder, every cut (FFmpeg scene detection), shot lengths, and per shot the black level, white level, mean colour and warm/cool tint. Writes `ref.json` and `ref.md`.

  ```bash
  python3 scripts/ref_analyze.py reference.mp4 out_dir [--threshold 0.3]
  ```

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Trend edits
