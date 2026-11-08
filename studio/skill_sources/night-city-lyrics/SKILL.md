---
name: night-city-lyrics
description: "A dreamy 16:9 lyric video like MITRAZ's Akhiyaan from Ye likho ye milega: an opening drawn eye with the song title, two eyes looking at each other under the moon, two silhouettes walking on a purple hill, gold handwritten lyrics that write themselves along a glowing line through a night city of lit windows, and a pink bokeh sunset where the two silhouettes finally meet. Use when the user asks for a night city lyric video or types /night-city-lyrics with a song MP3 (or a clip of it), its lyrics and the song title + artist."
---

# Night city lyrics

A dreamy 16:9 lyric video like MITRAZ's Akhiyaan from Ye likho ye milega: an opening drawn eye with the song title, two eyes looking at each other under the moon, two silhouettes walking on a purple hill, gold handwritten lyrics that write themselves along a glowing line through a night city of lit windows, and a pink bokeh sunset where the two silhouettes finally meet.

**Input:** a song MP3 (or a clip of it), its lyrics and the song title + artist.
**Run it:** `/night-city-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Find the beats (librosa). Read the lyrics and tell me the love story in one line (who is missing whom, where they meet) before you build.
2. Opening, during the intro: one small star of light in the black that stretches into a thin line, then opens into a big hand-drawn eye with a starry iris and lashes; the song title in thin spaced caps fades in under it. Then two smaller eyes side by side under a full moon, glancing at each other on the first lines.
3. Draw every scene flat, in silhouettes and soft gradients: a purple dusk hill with two small people walking, a night city skyline made of hundreds of tiny lit windows that flicker on one by one, a pink-orange sunset full of soft bokeh circles, and a cream paper page with simple line drawings (two teacups, a polaroid, two hands making a heart) for the memory lines. Pick the scene that fits each line.
4. Lyrics: a handwritten script font in warm gold with a soft glow. Each word writes itself on when it is sung, sitting on a thin glowing line of light that curves through the scene like a path; older words fade a little as new ones come. Keep the words in the empty sky or on the path, never over the people.
5. Story beats: on the chorus the two silhouettes walk toward each other from both sides of the sunset, a tiny eye floats between them, and they stop close on the last line. Slow camera drift and soft crossfades between scenes, light dust and stars drifting.
6. A short fade in and out of the audio, 1920×1080 at 30 fps with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
