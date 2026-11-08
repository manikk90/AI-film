---
name: minimal-love-lyrics
description: "A calm, minimal 16:9 lyric video like Ashu Shukla's Tumhare Aane Se from Ye likho ye milega: a dark maroon page with soft grain, every line set as stacked type (a small white script row, one big coral serif word, a small row below) and a tiny white line icon that draws itself beside the words (a door that opens, a sun, hearts, a paper plane flying a dotted path, a clock). Use when the user asks for a minimal love lyric video or types /minimal-love-lyrics with a song MP3 (or a clip of it), its lyrics and the song title + artist."
---

# Minimal love lyrics

A calm, minimal 16:9 lyric video like Ashu Shukla's Tumhare Aane Se from Ye likho ye milega: a dark maroon page with soft grain, every line set as stacked type (a small white script row, one big coral serif word, a small row below) and a tiny white line icon that draws itself beside the words (a door that opens, a sun, hearts, a paper plane flying a dotted path, a clock).

**Input:** a song MP3 (or a clip of it), its lyrics and the song title + artist.
**Run it:** `/minimal-love-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Find the beats (librosa). For every line pick the one key word that carries the feeling, and one small icon that shows it.
2. Page: a dark maroon background with a soft lighter glow in the centre, a strong vignette, fine film grain and a few slow drifting specks of dust. Nothing else; the words are the video.
3. Opening: the song title in a coral script font fades in, then the artist name in small thin spaced caps, then both fade out before the first word.
4. Lyrics as a stacked block in the centre: the lead-in words in a small white handwritten script, the key word huge in a coral serif italic (like Abril Fatface or Playfair Italic), and the rest of the line in a medium white serif below. Every word blurs in and rises a little exactly when it is sung, and the whole block breathes slightly on the beat.
5. Icons: one thin white line icon per line, drawn on stroke by stroke beside the block (a door that swings open on 'aane', a sun on 'din', two hearts, a paper plane flying a dotted arc, a clock, a couple holding hands). Keep them small and simple, like doodles in a diary.
6. Between lines the block blurs out and the next one blurs in. A short fade in and out of the audio, 1920×1080 at 30 fps with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
