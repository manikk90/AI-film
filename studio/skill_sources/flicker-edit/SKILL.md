---
name: flicker-edit
description: "The viral flicker edit from How to do this with Claude (Ep 6): two shots from the same tripod spot, one with the model and one of the empty beach, cut against each other about 8 times a second on the beat, so the model appears and vanishes into the sea, with a small zoom to her face every time she comes back. Use when the user asks for a flicker edit or types /flicker-edit with a shot (or photo) of the model, the same frame without her, and the song MP3."
---

# Flicker edit

The viral flicker edit from How to do this with Claude (Ep 6): two shots from the same tripod spot, one with the model and one of the empty beach, cut against each other about 8 times a second on the beat, so the model appears and vanishes into the sea, with a small zoom to her face every time she comes back.

**Input:** a shot (or photo) of the model, the same frame without her, and the song MP3.
**Run it:** `/flicker-edit` and attach or name the files.

## Steps

1. Here are two shots from the same spot: the model on the beach, and the empty beach with only the waves, plus a song. If a reference reel is attached, measure how often it cuts (frame differences); the viral one swaps about every 0.1–0.13 s.
2. Find the beat in the song (librosa). Swap between the model shot and the empty shot every quarter beat, so it flickers about 8 times a second in sync with the music.
3. Open on one beat of the model, and end on the last beat with only the empty beach, so she's gone.
4. Crop both shots to 9:16 with the horizon at the same height, and grade them to one warm sunset look (a little contrast, a warm tint, a soft vignette, fine grain) so the cut is seamless.
5. Every time the model appears, zoom in about 3% towards her face with an ease-out over that quarter beat, on top of a slow 8% push-in over the whole edit. Anchor every zoom on her face so it stays in place.
6. Add a very short soft white flash on the strongest beats, use the song as the audio and export the MP4.

## Every time it runs

- Do the cutting, zooms and grade in code (Python with numpy piped into ffmpeg, or an HTML canvas rendered frame by frame). No CapCut, no manual splits.
- Keep both shots framed exactly the same, so the only thing that changes on a cut is the model.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render 1080×1920 with the song as the audio, plus a 720p copy under 20 MB for WhatsApp.

## Helper scripts

Run from this skill's folder (`.claude/skills/flicker-edit/`).

- `scripts/flicker.py`: the whole edit in numpy piped to FFmpeg: both shots (image or video) cropped to 1080×1920 the same way, one warm grade for both (contrast, warm tint, vignette, grain), a swap every quarter beat (open on the model, end on the empty beach), a 3% ease-out zoom anchored on her face (`--face x,y`, 0–1) on every return over an 8% push-in, and a short white flash on strong beats. Beats come from `--beats beats.json` (`tempo`, `beats`, `downbeats`, `strong`) or a built-in spectral-flux fallback. `--stills 1,4,8` writes preview PNGs; it refuses to overwrite without `--force`.

  ```bash
  python3 scripts/flicker.py model.jpg empty.jpg song.mp3 out.mp4 [--beats beats.json] [--face 0.5,0.4] [--stills 1,4,8] [--force]
  ```

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Trend edits
