---
name: bairan-style
description: "A romantic lyric video like the Bairan reel: watercolour-painted characters cut out like paper stickers, polaroids, a sunflower and a beating heart popping in, every move fast in and slowly settling. Use when the user asks for a bairan-style romantic lyric video or types /bairan-style with a song MP3 and its lyrics (Hindi or Haryanvi, one sung line per row)."
---

# Bairan style

A romantic lyric video like the Bairan reel: watercolour-painted characters cut out like paper stickers, polaroids, a sunflower and a beating heart popping in, every move fast in and slowly settling.

**Input:** a song MP3 and its lyrics (Hindi or Haryanvi, one sung line per row).
**Run it:** `/bairan-style` and attach or name the files.

## Steps

1. Read every lyric line and tell me the feeling and one picture for it, then separate the vocals and force-align every word.
2. Paint everything in watercolour: uneven pigment, darker dried edges, granulation and paper texture. Then cut each piece out with a white paper border and a soft drop shadow.
3. Make two original characters (a boy and a girl) with live eyes that look and blink. Use big face close-ups, a thinking pose, an extreme eye close-up, and memories as polaroids, torn paper strips and thought clouds.
4. Give every move the same feel: fast in, then a long slow settle (exponential ease-out), never a bounce. Each cut glides in with a small push and drift.
5. Painted wall backgrounds that change per scene (sky blue, grey, park green, beige). Gold 3D title at the start, a glass-shatter transition near the end.
6. Captions bottom-centre in a Devanagari serif, each word fading up on its sung time. Show me stills before rendering, then render 1920×1080 with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
