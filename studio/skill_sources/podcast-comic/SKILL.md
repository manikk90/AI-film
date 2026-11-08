---
name: podcast-comic
description: "A podcast clip retold as a 9:16 comic book, like the Raj Shamani “ladke ko kab jaanoge” reel: the guest drawn in the studio below (bookshelf, Break the Cage poster, mic), and a new comic panel slams in on top for every point he makes, with a burst word and Hindi speech-bubble captions. Use when the user asks for a podcast comic or types /podcast-comic with the podcast clip (MP3 or MP4), the transcript in Devanagari, and 1–2 screenshots of the guest and studio."
---

# Podcast comic

A podcast clip retold as a 9:16 comic book, like the Raj Shamani “ladke ko kab jaanoge” reel: the guest drawn in the studio below (bookshelf, Break the Cage poster, mic), and a new comic panel slams in on top for every point he makes, with a burst word and Hindi speech-bubble captions.

**Input:** the podcast clip (MP3 or MP4), the transcript in Devanagari, and 1–2 screenshots of the guest and studio.
**Run it:** `/podcast-comic` and attach or name the files.

## Steps

1. Split the transcript into one row per point, and force-align every word (torchaudio MMS_FA). If a line looks squeezed, re-align it inside its own time window.
2. Draw the guest as a comic character that looks like the screenshot: hair, beard, outfit, and the studio behind him (bookshelf, poster, framed wall, mic). Lip-sync him to the audio and switch his mood per line: calm, smile, angry, sad.
3. Top panel: a new comic panel for every point (TEST #1, TEST #2 … then FINAL VERDICT), each with its own halftone colour, a drawing for that point and a burst word that pops on the key word with a sound effect.
4. Captions: a white speech bubble on the seam between the two panels, 2–3 words, only the spoken word in red, the tail pointing at the guest.
5. Keep everything inside the Instagram safe zone. Render 1080×1920 at 30 fps.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
