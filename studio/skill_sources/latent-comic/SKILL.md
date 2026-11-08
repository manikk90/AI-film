---
name: latent-comic
description: "An India's Got Latent clip retold as a 9:16 comic book, like the MC Stan episode reels: Samay Raina and the judges at the show's desk on top, a close-up of whoever is talking below with a gag for every line, halftone dots, bursts and speech-bubble captions. Use when the user asks for a latent-style comic reel or types /latent-comic with the show clip (MP4, plus the MP3 if you have it) and the transcript, if you have one."
---

# Latent comic

An India's Got Latent clip retold as a 9:16 comic book, like the MC Stan episode reels: Samay Raina and the judges at the show's desk on top, a close-up of whoever is talking below with a gag for every line, halftone dots, bursts and speech-bubble captions.

**Input:** the show clip (MP4, plus the MP3 if you have it) and the transcript, if you have one.
**Run it:** `/latent-comic` and attach or name the files.

## Steps

1. Make a contact sheet of the clip, find every camera cut with ffmpeg scene detection, and work out who says each line from who holds the mic and whose mouth moves. Write the lines as SPEAKER|text.
2. Force-align every word (torchaudio MMS_FA). If a line looks squeezed, re-align it inside its own time window, and cap words that stretch over a pause.
3. Draw each judge as a comic caricature that looks like them from my screenshots: hair, glasses or shades, beard, outfit, and the show's blue cube mic. Lip-sync only the person talking. The others look at the speaker and laugh on the audience laughs.
4. Top panel: the show's desk (dark curtain with a blue and red glow, phones, juice cartons, the red buzzer). Switch between the three-judge shot and the wide five-judge shot exactly where the original cuts.
5. Bottom panel: the speaker's close-up slams in fresh for every line, with a gag drawn for that line (a calendar for “3 saal baad”, a drunk globe, a range meter, a pile of shoes) and a burst word like WAAH! or HAHAHA!.
6. Captions: a comic speech bubble on the seam, 2–4 words, the tail pointing at the speaker and the spoken word in their colour. Keep everything inside the Instagram safe zone. Render 1080×1920 at 30 fps.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
