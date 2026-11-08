---
name: glow-lyrics
description: "A dreamy lyric video like MITRAZ's Khwahish from Ye likho ye milega Part 7: flat vector scenes at purple dusk, silhouettes that tell the story (a boy alone on a bench, the girl he misses glowing inside a golden birdcage), soft bloom on every light, and the lyric line glowing in word by word. Use when the user asks for a dreamy glowing lyric video or types /glow-lyrics with a song MP3 and its lyrics (one sung line per row)."
---

# Glow lyrics

A dreamy lyric video like MITRAZ's Khwahish from Ye likho ye milega Part 7: flat vector scenes at purple dusk, silhouettes that tell the story (a boy alone on a bench, the girl he misses glowing inside a golden birdcage), soft bloom on every light, and the lyric line glowing in word by word.

**Input:** a song MP3 and its lyrics (one sung line per row).
**Run it:** `/glow-lyrics` and attach or name the files.

## Steps

1. Read every lyric line and tell me the feeling and one picture for it, then separate the vocals and force-align every word.
2. Paint flat vector scenes in a dusk palette (deep purple, violet, magenta, a pale pink horizon): layered clouds that drift slowly, a calm sea with thin light lines, a beach.
3. Tell the story with silhouettes and glowing figures: the singer as a dark silhouette, the person he misses as a soft white glowing figure, and one strong symbol (a golden birdcage on puppet strings) that comes back through the song.
4. Add bloom to every light source and glowing figure, plus fine grain over the whole frame. Move the camera slowly between scenes with soft cross-dissolves, never hard cuts.
5. Show the sung line at the top in a rounded font (Quicksand), each word fading in white with a soft glow exactly when it is sung.
6. Render 16:9 1920×1080 and a 9:16 version with the song as the audio.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
