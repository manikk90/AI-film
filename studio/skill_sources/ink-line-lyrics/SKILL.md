---
name: ink-line-lyrics
description: "A fast lyric video drawn as ONE glowing ink line that never breaks, like the Main Aur Tu reel: the line morphs into a new drawing on every key word, with the camera punching on every kick. Use when the user asks for a one-line ink lyric video or types /ink-line-lyrics with a song MP3 and its lyrics, one sung line per row."
---

# Ink line lyrics

A fast lyric video drawn as ONE glowing ink line that never breaks, like the Main Aur Tu reel: the line morphs into a new drawing on every key word, with the camera punching on every kick.

**Input:** a song MP3 and its lyrics, one sung line per row.
**Run it:** `/ink-line-lyrics` and attach or name the files.

## Steps

1. Separate the vocals with demucs, force-align every word, and find the beat grid and kicks with librosa.
2. Plan one drawing per key word from the lyric's meaning (a heart, a chase, a road, an eye with a star, two figures colliding, a constellation), all built from a single continuous line.
3. Morph the line from one drawing to the next in about 0.3 s, right on the sung word, with a glowing pen nib riding the wave of the redraw.
4. Add the rush: the camera punches and shakes on every kick, speed streaks on chase shots, and the background tint shifts section by section (navy, indigo, plum, crimson).
5. Captions: 2–3 word chunks that slam in on each word, the sung word in gold, and one big keyword per line that pops and fades.
6. Render 9:16 inside the Instagram safe area, plus a 16:9 version with keywords in the side columns.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
