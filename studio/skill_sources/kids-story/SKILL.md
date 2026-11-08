---
name: kids-story
description: "A bright 60-second kids story like Pyaasi Chidiya: soft rounded characters, a sunny world, Hindi speech bubbles and a little reacting companion in the corner. Use when the user asks for a kids story video or types /kids-story with the story voiceover MP3 (ElevenLabs, Hindi) and the script."
---

# Kids story

A bright 60-second kids story like Pyaasi Chidiya: soft rounded characters, a sunny world, Hindi speech bubbles and a little reacting companion in the corner.

**Input:** the story voiceover MP3 (ElevenLabs, Hindi) and the script.
**Run it:** `/kids-story` and attach or name the files.

## Steps

1. Force-align the voiceover and mark the key moments (problem, idea, solution, moral).
2. Draw a bright, rounded world: green hills, a big sun, clouds, simple props, everything in soft flat colours with dark outlines.
3. Design the main characters to be cute and simple (big eyes, round shapes) and give each one 3–4 poses.
4. Show speech bubbles in Hindi for dialogue, and add question marks, sparkles and hearts for emotions.
5. Add an original companion character in a corner circle who reacts (wow, worried, laughing) to the story.
6. End on a moral card. Render 16:9.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
