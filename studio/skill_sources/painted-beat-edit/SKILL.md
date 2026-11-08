---
name: painted-beat-edit
description: "A viral footage edit remade with no footage at all, like the Shiv aarti reel from How to do this with Claude (Ep 2): Claude paints the images in code in an acrylic mural style and cuts between them on every half-beat with a slow zoom. Use when the user asks for a painted beat edit or types /painted-beat-edit with the song MP3 and the reference reel."
---

# Painted beat edit

A viral footage edit remade with no footage at all, like the Shiv aarti reel from How to do this with Claude (Ep 2): Claude paints the images in code in an acrylic mural style and cuts between them on every half-beat with a slow zoom.

**Input:** the song MP3 and the reference reel.
**Run it:** `/painted-beat-edit` and attach or name the files.

## Steps

1. Here is a song MP3 and a reference reel. Analyze the reference at 2 frames per second: note every cut, how long each shot holds and which beat it lands on.
2. Rebuild the same edit, but instead of footage, paint the images in code in an acrylic mural style with visible brush strokes. For the Shiv aarti: a blue Lord Shiva face with the crescent moon and tilak, and a priest doing aarti with fire.
3. Cut between them on every half-beat, with a slow continuous zoom and a little fire and glow that moves.
4. Save one big moment for the drop: open Shiva's eyes exactly on it.
5. No text. 9:16, 1080×1920, with the song as the audio.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Trend edits
