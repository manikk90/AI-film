---
name: mirzapur-video
description: "A web-series dialogue turned into a comic meme, like the Kaalin Bhaiya “chai piyoge?” reel: a bold comic portrait of the don, halftone backgrounds that change on every beat, and a POV caption. Use when the user asks for a web-series dialogue comic meme or types /mirzapur-video with the dialogue audio (MP3) and a POV line for the caption."
---

# Mirzapur video

A web-series dialogue turned into a comic meme, like the Kaalin Bhaiya “chai piyoge?” reel: a bold comic portrait of the don, halftone backgrounds that change on every beat, and a POV caption.

**Input:** the dialogue audio (MP3) and a POV line for the caption.
**Run it:** `/mirzapur-video` and attach or name the files.

## Steps

1. Force-align the dialogue and mark the beats: the pause, the stare, the punchline.
2. Draw the don as your own bold comic caricature: thick outlines, flat colours, halftone shading, and props like shades, a tilak or a chai glass.
3. Swap the background on every beat (green bokeh, cream halftone, purple night) and add radiating speed lines and a HAAN! burst on the punchline.
4. Keep the POV caption in a blue pill at the bottom the whole time.
5. Use small moves only: a slow push-in, an eyebrow raise, shades sliding down, steam rising from the chai.
6. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
