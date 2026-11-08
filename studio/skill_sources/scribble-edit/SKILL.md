---
name: scribble-edit
description: "Your own clip covered in live marker doodles, like the Justin Bieber “Where Are Ü Now” video from How to do this with Claude (Ep 5): the wall behind you fills with hand-drawn stars, rockets, cats and lightning, crowns and shades stick to your face as you move, a neon line traces your body, and the whole look changes on every beat. Use when the user asks for a scribble doodle edit or types /scribble-edit with a 9:16 clip of you moving (a plain wall behind you works best) and the song MP3."
---

# Scribble edit

Your own clip covered in live marker doodles, like the Justin Bieber “Where Are Ü Now” video from How to do this with Claude (Ep 5): the wall behind you fills with hand-drawn stars, rockets, cats and lightning, crowns and shades stick to your face as you move, a neon line traces your body, and the whole look changes on every beat.

**Input:** a 9:16 clip of you moving (a plain wall behind you works best) and the song MP3.
**Run it:** `/scribble-edit` and attach or name the files.

## Steps

1. Track me on every frame with MediaPipe: a person mask split into body, hair and clothes (selfie multiclass), face landmarks and pose landmarks (wrists, elbows, knees). Smooth the points over a few frames so the doodles don't jitter.
2. Find the beat and every music hit in the song (librosa). Give the video a new doodle look on every hit and never hold one look longer than 7 frames, so it changes at least 4 times a second.
3. Wall: for every look, fill the background with 15–25 marker doodles on a loose grid so there is no empty space (stars, hearts, rockets, cats, cactus, lightning, planets, mushrooms, music notes, bombs, eyes, speech bubbles with short words like BOOM or NAH). Draw them on a layer cut out by my person mask so they sit behind me.
4. Face: draw 1–3 doodles in face space, scaled by my face width and turning with my head: crown, horns, halo, round shades, glowing eyes, skull, flower crown, beard, mask, rainbow mouth.
5. Body: most looks get a glowing neon outline around me in one bright colour, a pattern drawn on my shirt clipped to the clothes mask (ribcage, stripes, grid) and a colourful scribble clipped to my hair. Some looks swap the whole background for a full crayon backdrop (rainbow waves, stripes, op-art, galaxy, a white burst) with me pasted back on top.
6. Props: when my hands or knees do something (air guitar, a throw, a kick), draw a matching prop that follows them, like a guitar between my wrists or a ball in a parabola, with a word like ELECTRIC next to it.
7. Make it feel hand-drawn: thick wobbly marker lines in bright colours, every line redrawn slightly differently every 1–2 frames so it boils. Put my handle small in a corner.

## Every time it runs

- Draw every doodle in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No image generators, so the marker look is the same every time.
- Never cover my face: face doodles sit on top of it (crown, shades, horns), never instead of it.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render 1080×1920 at 30 fps with the song as the audio, plus a 720p copy under 20 MB for WhatsApp. Check the render for black or empty frames before you give it to me.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Trend edits
