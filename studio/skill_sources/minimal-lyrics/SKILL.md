---
name: minimal-lyrics
description: "A quiet, minimal lyric video like Bayaan's Safar from Ye likho ye milega Part 7: a flat horizon, a lone silhouette walking, wind drawn as sweeping streak lines, and a sky whose colour follows the mood of each line, with one small serif lyric line at the bottom. Use when the user asks for a minimal lyric video or types /minimal-lyrics with a song MP3 and its lyrics (one sung line per row)."
---

# Minimal lyrics

A quiet, minimal lyric video like Bayaan's Safar from Ye likho ye milega Part 7: a flat horizon, a lone silhouette walking, wind drawn as sweeping streak lines, and a sky whose colour follows the mood of each line, with one small serif lyric line at the bottom.

**Input:** a song MP3 and its lyrics (one sung line per row).
**Run it:** `/minimal-lyrics` and attach or name the files.

## Steps

1. Read every lyric line and give each one a mood colour (dusty rose, slate grey night, warm gold dawn), then separate the vocals and force-align every word.
2. Draw a minimal world: one flat horizon line, low hills, a sun or moon, and a single silhouette figure who keeps walking across the frame. Add one landmark when a line needs it (a tall ruin, a road).
3. Draw the wind as hundreds of thin streak lines sweeping across the sky, moving with the music, faster on the loud parts.
4. Crossfade the sky and ground colours to each line's mood colour as the song moves.
5. Show only the current line, small and centred near the bottom in a serif (Cormorant), white, with the sung word turning gold.
6. Keep everything slow and calm: no shakes, no pops. Render 16:9 1920×1080 and a 9:16 version with the song as the audio.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
