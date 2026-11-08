---
name: rap-video
description: "A full-energy cartoon rap video like Boom Shaka: the rapper drawn as a bold cartoon, BOOM bursts, speed lines and lyrics that slam in on every beat. Use when the user asks for a cartoon rap video or types /rap-video with a rap song MP3, its lyrics, and 1–2 photos of the rapper's look."
---

# Rap video

A full-energy cartoon rap video like Boom Shaka: the rapper drawn as a bold cartoon, BOOM bursts, speed lines and lyrics that slam in on every beat.

**Input:** a rap song MP3, its lyrics, and 1–2 photos of the rapper's look.
**Run it:** `/rap-video` and attach or name the files.

## Steps

1. Separate the vocals, force-align every word, and find the beats and kicks with librosa.
2. Draw the rapper as your own bold cartoon caricature (outfit, shades, chain, haircut from the photos) with 4–5 poses: arms spread, pointing, leaning in, jumping.
3. Change the pose and background on the beat: colour-block walls, radial speed lines, city at night.
4. Slam the lyrics in word by word in heavy condensed caps, the hook words in red, with a BOOM or POW burst on the biggest words.
5. Camera punch and shake on every kick, a white flash on the drop.
6. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
