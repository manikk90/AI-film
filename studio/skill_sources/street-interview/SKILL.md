---
name: street-interview
description: "A funny street interview turned into a cartoon, like the bad day interview: the interviewee drawn as a flat cartoon, night-street background and big caption words on the punchlines. Use when the user asks for a street interview cartoon or types /street-interview with the interview audio (MP3) with both voices."
---

# Street interview

A funny street interview turned into a cartoon, like the bad day interview: the interviewee drawn as a flat cartoon, night-street background and big caption words on the punchlines.

**Input:** the interview audio (MP3) with both voices.
**Run it:** `/street-interview` and attach or name the files.

## Steps

1. Transcribe with speaker labels and force-align every word. Mark the punchlines.
2. Draw a night street: shop shutters, a streetlight, a passing auto, all in flat colours.
3. Draw the interviewee as an original flat cartoon with an expressive face (worried, shocked, laughing), lip-synced, and the interviewer as just a hand holding a mic.
4. On every punchline, slam one big caption word in a bold serif (wake, THIS, why) and zoom in on the face.
5. Use 2–4 word captions for the rest, with the spoken word highlighted.
6. Render 16:9 and 9:16.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
