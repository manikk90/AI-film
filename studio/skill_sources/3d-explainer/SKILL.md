---
name: 3d-explainer
description: "A 3D animated news explainer built in Blender, like the Professor of Claude ISRO and Cyclone Arnab reels: Claude builds every 3D shot in code (rockets on launch pads, a 3D India map with pins, a storm spiralling over the sea, Earth from space), cuts the camera on your words and pops the numbers in as you say them. Use when the user asks for a 3D news explainer or types /3d-explainer with your voiceover MP3 and the topic (2–3 article links)."
---

# 3D explainer

A 3D animated news explainer built in Blender, like the Professor of Claude ISRO and Cyclone Arnab reels: Claude builds every 3D shot in code (rockets on launch pads, a 3D India map with pins, a storm spiralling over the sea, Earth from space), cuts the camera on your words and pops the numbers in as you say them.

**Input:** your voiceover MP3 and the topic (2–3 article links).
**Run it:** `/3d-explainer` and attach or name the files.

## Steps

1. Check that Blender (free from blender.org) is installed and that Blender -b runs from the terminal. Install it if it's missing.
2. Transcribe my voiceover and force-align every word. Split it into 6–9 shots, one idea per shot, and tell me the shot list before building.
3. Build each shot as clean, simple 3D models in its own area of one Blender scene: soft studio light, a slow camera push or orbit, and a bloom glow on lights, flames and glowing pins.
4. Cut to each shot's camera on the exact word that starts its idea. Keep any 3D text in English, because Blender can't draw Devanagari.
5. Pop big numbers and labels in as they're spoken (4 LAUNCH PADS, 2029, 125 KM/H), and add word-by-word captions with the key word in orange, outside the top 250 px and the bottom 420 px.
6. Mix my voice with small sound effects: a whoosh on every cut, a low rumble under launches and wind under storms.

## Every time it runs

- Build every shot in Blender with Python (bpy) and render it headless (Blender -b) with EEVEE. No stock footage or image generators, so the look is the same every time.
- Time every camera cut, number and caption with forced alignment (torchaudio MMS_FA). Never guess timings.
- For any map of India, use the official Natural Earth India point-of-view boundary. Never draw the outline by hand.
- Show me one still of every shot before the full render, and ask before overwriting files.
- Render a 1080×1920 MP4 with my voice, plus a 720p copy under 20 MB for WhatsApp.

## Helper scripts

Run from this skill's folder (`.claude/skills/3d-explainer/`).

- `scripts/shots_template.py`: a bpy skeleton that builds every shot from `shots.json` (`id`, `start`, `end`, `kind`: rocket, map, storm, earth or text, `label`) in its own area of one scene, with a slow-push camera per shot, soft studio light and EEVEE bloom (a compositor Glare node on Blender 4.2+), and renders 1080×1920 frames per shot. Add `--stills` after the out dir to render one middle frame per shot for the preview.

  ```bash
  blender -b -P scripts/shots_template.py -- shots.json out_dir [--stills]
  ```

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
