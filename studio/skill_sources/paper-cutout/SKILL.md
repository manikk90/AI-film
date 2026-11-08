---
name: paper-cutout
description: "A paper-cutout music video like Jaadoo: hand-cut paper characters, floating islands and lyric tags that pop on their words, moving in 15 fps stop-motion. Use when the user asks for a paper-cutout music video or types /paper-cutout with a song MP3 and its lyrics."
---

# Paper cutout

A paper-cutout music video like Jaadoo: hand-cut paper characters, floating islands and lyric tags that pop on their words, moving in 15 fps stop-motion.

**Input:** a song MP3 and its lyrics.
**Run it:** `/paper-cutout` and attach or name the files.

## Steps

1. Separate the vocals and force-align every word.
2. Build every character and set from cut paper: flat colours, slightly rough edges, a drop shadow under each piece and a fibre texture.
3. Animate in 15 fps stop-motion steps so it feels handmade. Characters walk, wave and float between scenes like islands in the sky.
4. Put each lyric word on its own little paper tag that pops in on its sung time and bounces on the beat.
5. Add grain and a soft vignette. Show streaming badges (Spotify, Apple Music) in a corner early on.
6. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
