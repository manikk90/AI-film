---
name: woof-woof
description: "A streamer's live moment as a cartoon, like the IShowSpeed “woof woof” clip from Ye likho ye milega Part 8: he stares into the camera, then barks on every beat while WOOF! bursts fly, the live chat floods with woofs and the viewer count shoots up. Use when the user asks for a streamer bark cartoon or types /woof-woof with the clip audio (MP3), or just tell me when each bark happens."
---

# Woof woof

A streamer's live moment as a cartoon, like the IShowSpeed “woof woof” clip from Ye likho ye milega Part 8: he stares into the camera, then barks on every beat while WOOF! bursts fly, the live chat floods with woofs and the viewer count shoots up.

**Input:** the clip audio (MP3), or just tell me when each bark happens.
**Run it:** `/woof-woof` and attach or name the files.

## Steps

1. Find every bark (or shout) in the audio and use those times as the beat. If there's no audio, bark every 0.42 s after a short stare.
2. Draw a streamer room: a deep purple wall with halftone dots, an RGB light strip that cycles colour, a shelf with toys and a LIVE badge with the viewer count top-left.
3. Draw the streamer as your own cartoon (big curly hair, a red #7 jersey). He stares, then on each bark his mouth opens wide, his head jerks and his hands go up.
4. On every bark, pop a WOOF! comic burst in a new spot and give the camera a small shake.
5. Fill a live chat panel on the right that scrolls faster and faster with messages (WOOF WOOF 🐶, bro is barking 💀, clip it 😂), and make the viewer count jump on each bark.
6. Render 16:9 and a 9:16 copy.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
