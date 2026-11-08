---
name: shadow-puppet
description: "A kids story told like tholu bommalata shadow puppets: black cut-out characters with pin joints moving against a glowing orange screen. Use when the user asks for a shadow-puppet story or types /shadow-puppet with the story voiceover MP3 and the script."
---

# Shadow puppet

A kids story told like tholu bommalata shadow puppets: black cut-out characters with pin joints moving against a glowing orange screen.

**Input:** the story voiceover MP3 and the script.
**Run it:** `/shadow-puppet` and attach or name the files.

## Steps

1. Force-align the voiceover and split the story into scenes.
2. Draw every character and prop as a flat black silhouette with small cut-out holes for patterns, and add pin joints so arms, legs and jaws swing.
3. Light the screen from behind: a warm orange glow with a soft hot spot, a faint lamp flicker, and the fabric texture of the screen.
4. Move the puppets with a slight wobble as if held by sticks, and let characters come closer to the screen (sharper) or move back (softer) for emphasis.
5. Put the Hindi narration line at the bottom in a clean Devanagari font, with the key word in red.
6. Render 16:9.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
