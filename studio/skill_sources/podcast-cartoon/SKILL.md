---
name: podcast-cartoon
description: "A famous podcast moment turned into a gag: the podcast clip plays, then an original cheeky cartoon kid pops in as a sticker and asks the big question, and you react, like the “maut ke baare mein sochte ho?” reel. Use when the user asks for a podcast cartoon gag or types /podcast-cartoon with the podcast clip (MP4), your voiceover MP3, and 3–4 photos of you reacting (smile, think, shock, laugh) with transparent backgrounds."
---

# Podcast cartoon

A famous podcast moment turned into a gag: the podcast clip plays, then an original cheeky cartoon kid pops in as a sticker and asks the big question, and you react, like the “maut ke baare mein sochte ho?” reel.

**Input:** the podcast clip (MP4), your voiceover MP3, and 3–4 photos of you reacting (smile, think, shock, laugh) with transparent backgrounds.
**Run it:** `/podcast-cartoon` and attach or name the files.

## Steps

1. Force-align the voiceover and mark three beats: the podcast setup, the kid's question, and your reply.
2. Play the podcast clip during the setup, timed so its most dramatic frame lands just before the question.
3. Design an ORIGINAL cartoon kid (never copy an existing cartoon character): give them their own hairstyle, glasses or outfit, and a mischievous raised eyebrow. Show them as a white die-cut sticker that slides up over the clip.
4. Lip-sync the kid to their line and pop speech bubbles on the key words (the question, the nickname).
5. On your reply, slide your own reaction cutouts in from the side (shock on the scary word, laugh on the punchline) and add one prop gag, like an EMI DUE bill flying up.
6. Captions: 2–3 words with the spoken word highlighted. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
