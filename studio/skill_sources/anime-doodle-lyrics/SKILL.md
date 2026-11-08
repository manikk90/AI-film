---
name: anime-doodle-lyrics
description: "A moody 16:9 lyric video like Eden's Echo's Parvah Nahi from Ye likho ye milega: your anime clips graded deep navy, every cut blooming from line-art into colour, white marker doodles that add the hidden meaning of each line (cupped hands under a comet, a question mark that turns into a heart, a stitched heart that heals, a red thread between two hands), and lyrics drawn as outlines that trace themselves and then fill. Use when the user asks for an anime doodle lyric video or types /anime-doodle-lyrics with a song MP3 (or a clip of it), its lyrics and 3–6 horizontal anime clips (with the start time for each)."
---

# Anime doodle lyrics

A moody 16:9 lyric video like Eden's Echo's Parvah Nahi from Ye likho ye milega: your anime clips graded deep navy, every cut blooming from line-art into colour, white marker doodles that add the hidden meaning of each line (cupped hands under a comet, a question mark that turns into a heart, a stitched heart that heals, a red thread between two hands), and lyrics drawn as outlines that trace themselves and then fill.

**Input:** a song MP3 (or a clip of it), its lyrics and 3–6 horizontal anime clips (with the start time for each).
**Run it:** `/anime-doodle-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track. Find the beats (librosa). Read every line for its deeper meaning and write me one doodle idea per line before you build.
2. Watch every clip at 2 frames per second and list the usable moments (time range + what happens). Map each lyric line to the moment that matches it in a shot table, and never use the same moment twice. Use horizontal clips only; never pillarbox a vertical clip.
3. Grade all footage the same: a soft deep-navy multiply so the doodles and text glow on top. At every cut, start from an edge-detected line-art version of the new shot and bloom it into full colour over half a second.
4. Doodles: white marker lines with a slightly shaky hand-drawn feel, drawn on stroke by stroke with a pen dot, placed next to the subject and never over a face. Make each one show the meaning of its line: hands cupping a falling comet, a question mark that morphs into a heart, rain that grows flowers, a stitched heart that heals while band-aids float away, a red thread that ties two hands, a heartbeat line that ends in a heart.
5. Lyrics: each word is an outline (Cormorant italic for small rows, Kaushan Script for the key word) that traces itself with a pen dot exactly when it is sung, then fills in white or warm pink. Keep lyrics mid-frame on the left, centre or right in the empty space, never at the bottom where phone players cover them.
6. Soft light leaks and floating dust, a gentle push-in on every shot, a short fade in and out of the audio, 1920×1080 at 30 fps with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
