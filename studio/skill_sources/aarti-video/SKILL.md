---
name: aarti-video
description: "A devotional aarti video full of fire and light, like the Shiv aarti: glowing diyas, flames, a damru rhythm and the aarti lines in Devanagari. Use when the user asks for a devotional aarti video or types /aarti-video with the aarti MP3 and its lines in Devanagari."
---

# Aarti video

A devotional aarti video full of fire and light, like the Shiv aarti: glowing diyas, flames, a damru rhythm and the aarti lines in Devanagari.

**Input:** the aarti MP3 and its lines in Devanagari.
**Run it:** `/aarti-video` and attach or name the files.

## Steps

1. Force-align the aarti lines and find the bell and damru hits.
2. Set a temple scene with warm light: rows of diyas, a big aarti thali, flames that flicker with the music, smoke and floating embers.
3. Show the deity in a respectful illustrated style with a soft halo glow, never a photo.
4. Write each line in a bold Devanagari font with a gold glow, the key word bigger, appearing on its sung time.
5. Pulse the flames and do a gentle camera push on every bell hit, with a flower-petal shower at the end.
6. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
