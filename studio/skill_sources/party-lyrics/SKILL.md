---
name: party-lyrics
description: "A loud party-anthem lyric video, like Honey Singh's Casa Tupka: gold and gem 3D lettering, red curtains and lavender smoke, confetti on every beat, and a cartoon of the singer in their signature look. Use when the user asks for a party-anthem lyric video or types /party-lyrics with a song MP3 and its lyrics."
---

# Party lyrics

A loud party-anthem lyric video, like Honey Singh's Casa Tupka: gold and gem 3D lettering, red curtains and lavender smoke, confetti on every beat, and a cartoon of the singer in their signature look.

**Input:** a song MP3 and its lyrics.
**Run it:** `/party-lyrics` and attach or name the files.

## Steps

1. Separate the vocals, force-align the verse, and use windowed alignment for the hook (party vocals confuse whisper). Find every beat.
2. Set the stage: red velvet curtains, lavender smoke and a soft spotlight.
3. Write each line in chunky 3D display letters: gold for brand words, ruby, emerald and sapphire for the rest, each popping in on its word.
4. Give special words their own gag: tequila glasses beside TEQUILA, a gold chain under GOLD, a 24K badge on CARAT.
5. In the hook, bring in a cartoon caricature of the singer (white suit, shades, mic) and build a wall of the chanted word on every beat, with confetti bursts.
6. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
