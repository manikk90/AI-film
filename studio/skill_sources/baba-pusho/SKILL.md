---
name: baba-pusho
description: "A Puneet Superstar “Baba Pusho” clip as a cartoon class, like Ye likho ye milega Part 8: Pusho preaches from his desk under a big Om, his fixed class of students reacts, and every Hindi line gets a caption plus a scene of its own. Use when the user asks for a Baba Pusho class cartoon or types /baba-pusho with a Puneet Superstar audio clip (MP3)."
---

# Baba Pusho

A Puneet Superstar “Baba Pusho” clip as a cartoon class, like Ye likho ye milega Part 8: Pusho preaches from his desk under a big Om, his fixed class of students reacts, and every Hindi line gets a caption plus a scene of its own.

**Input:** a Puneet Superstar audio clip (MP3).
**Run it:** `/baba-pusho` and attach or name the files.

## Steps

1. Transcribe the Hindi in Devanagari with whisper (large-v3), let me fix any wrong words, then force-align the corrected text.
2. Keep the same cast in every clip: Baba Pusho (long white beard, dark cap, saffron shawl) at a desk, and his students (a footballer in a #7 jersey, a man in a kurta, an old bearded baba, a Greek marble bust).
3. Set the classroom in a warm beige hall with a big golden Om, an hourglass and plants. Pusho's mouth moves with the voice and the students react (shock, laugh, take notes).
4. When a line names a place or a thing, cut to a quick explainer scene for it (a temple, a mosque and a gurudwara lighting up in turn).
5. Add a small “पुशो वाणी” badge top-left, stickers on key words (COPY, RED FLAG) and Hindi captions with the spoken word in yellow on a dark band.
6. Render 16:9 and a 9:16 copy.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Animated videos
