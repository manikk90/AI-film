---
name: sketch-doodle-edit
description: "One photo turned into the trending sketch doodle edit from How to do this with Claude (Ep 4): the people flicker between the real photo and a pencil sketch on the beat, white wind lines swoosh across the sky, a scribble outline draws around them and a handwritten line writes itself in. Use when the user asks for a sketch doodle edit or types /sketch-doodle-edit with one photo (people against an open sky works best), its pencil-sketch version from Gemini, and the song MP3."
---

# Sketch doodle edit

One photo turned into the trending sketch doodle edit from How to do this with Claude (Ep 4): the people flicker between the real photo and a pencil sketch on the beat, white wind lines swoosh across the sky, a scribble outline draws around them and a handwritten line writes itself in.

**Input:** one photo (people against an open sky works best), its pencil-sketch version from Gemini, and the song MP3.
**Run it:** `/sketch-doodle-edit` and attach or name the files.

## Steps

1. First give me a Gemini prompt that turns only the people in my photo into a clean pencil sketch and keeps the background exactly the same. I'll make the sketch in Gemini and give it back to you.
2. Line the sketch up with the photo and use the sketch only where Gemini changed the people (a difference mask), so the sky and background stay the real photo. Paint over Gemini's sparkle watermark with the photo.
3. Fit the photo to 9:16: scale it up, crop the sides, and extend the sky smoothly at the top if it's too short. Never mirror the sky, it looks repeated.
4. Find the beat in the song (librosa). On the opening beats, flicker the people between the photo and the sketch, one switch per beat.
5. Then draw white doodle wind lines swooshing across the sky, a white scribble outline that traces around the people, and a handwritten line (like “Your time on Earth is limited! Live it!”) that writes itself in word by word.
6. Make it feel hand-drawn: wobbly white marker lines that are redrawn slightly differently every 2 frames so they boil.

## Every time it runs

- Draw the doodles, outlines and handwriting in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). The only generated image is the pencil sketch I give you.
- Keep text out of the top 250 px and the bottom 420 px (Instagram buttons and caption).
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render a 1080×1920 MP4 with the song as the audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Trend edits
