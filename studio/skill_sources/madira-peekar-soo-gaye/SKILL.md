---
name: madira-peekar-soo-gaye
description: "A famous movie dialogue turned into a comic-book scene, like the Drishyam 3 “madira peekar so gaye” clip from Ye likho ye milega Part 8: one character delivers the line in a speech bubble word by word, then the other explodes in close-up with speed lines and a colour flash. Use when the user asks for a movie dialogue comic scene or types /madira-peekar-soo-gaye with the dialogue audio (MP3) and the words of each line."
---

# Madira peekar soo gaye

A famous movie dialogue turned into a comic-book scene, like the Drishyam 3 “madira peekar so gaye” clip from Ye likho ye milega Part 8: one character delivers the line in a speech bubble word by word, then the other explodes in close-up with speed lines and a colour flash.

**Input:** the dialogue audio (MP3) and the words of each line.
**Run it:** `/madira-peekar-soo-gaye` and attach or name the files.

## Steps

1. Transcribe the dialogue, split it by speaker, and force-align every word so the bubbles fill in exactly as they're said.
2. Draw the scene in a flat comic style: the setting (a wooden hall with pillars and a doorway), and each character as your own bold cartoon with thick outlines and halftone shading.
3. Speaker one: a mid shot with a small gesture (a raised hand), and a white speech bubble that writes the line in word by word.
4. Speaker two: cut to a tight close-up on a green halftone background with radiating speed lines. The bubble grows on every repeated word (CHEE, CHEE CHEE…) and the speed lines pulse.
5. On the last word, flash the background to purple and add a small burst sticker.
6. Render 16:9 and a 9:16 copy.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
