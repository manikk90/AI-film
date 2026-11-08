---
name: neon-lyrics
description: "A synthwave rap lyric video like KR$NA's “I Guess”: a neon grid, a big retro sun, a cartoon of the rapper in a varsity jacket and glowing Hindi lyrics. Use when the user asks for a synthwave neon lyric video or types /neon-lyrics with a song MP3, its lyrics, and photos of the rapper's look."
---

# Neon lyrics

A synthwave rap lyric video like KR$NA's “I Guess”: a neon grid, a big retro sun, a cartoon of the rapper in a varsity jacket and glowing Hindi lyrics.

**Input:** a song MP3, its lyrics, and photos of the rapper's look.
**Run it:** `/neon-lyrics` and attach or name the files.

## Steps

1. Separate the vocals, force-align the lyrics and find the beats.
2. Set the synthwave world: a purple-to-pink sky, a striped retro sun, a scrolling neon grid floor and a city skyline.
3. Draw the rapper as your own cartoon caricature in their signature outfit, with poses that change every few lines.
4. Write each lyric line in glowing neon (Hindi and English as sung), the key word in yellow, flickering on like a neon sign.
5. Pulse the sun and the grid on the beat, with a chromatic glitch on the hook.
6. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
