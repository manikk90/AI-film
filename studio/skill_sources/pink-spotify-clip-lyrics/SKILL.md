---
name: pink-spotify-clip-lyrics
description: "A poetic 16:9 lyric video like the Alfaaz (Hamza Malik × Zain Zohaib) video: a tilted pink Spotify lyrics card, then motion graphics that follow the meaning of each line (a rose that draws itself, letters cut out of the clip, a cinema letterbox, a dotted footstep path with the words along it, and a split screen for the last line), with my emotional clips playing softly behind the lyrics so both the video and the words stay readable. Use when the user asks for a pink Spotify-card lyric video with clips or types /pink-spotify-clip-lyrics with a song MP3 (or a clip of it), its lyrics, 1–3 emotional video clips (with the start time for each), a cover image and the Spotify logo PNG."
---

# Pink Spotify clip lyrics

A poetic 16:9 lyric video like the Alfaaz (Hamza Malik × Zain Zohaib) video: a tilted pink Spotify lyrics card, then motion graphics that follow the meaning of each line (a rose that draws itself, letters cut out of the clip, a cinema letterbox, a dotted footstep path with the words along it, and a split screen for the last line), with my emotional clips playing softly behind the lyrics so both the video and the words stay readable.

**Input:** a song MP3 (or a clip of it), its lyrics, 1–3 emotional video clips (with the start time for each), a cover image and the Spotify logo PNG.
**Run it:** `/pink-spotify-clip-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track. Find the beats (librosa). Read the lyrics for meaning and propose one visual idea per line or pair of lines (rose, path, kiss, stars, split), plus the section times.
2. Prepare the clips: trim each from my start time, slow them to fit their section and turn them into numbered frames so every film frame has an exact clip frame. Keep them dim and soft (darker gradient on the text side, slight blur), never brighter than the lyrics.
3. Spotify card in pink: a pink card with the cover art, song title, artists and my Spotify logo, lyrics in big Inter bold. Tilt the card in 3D with a slow camera drift and blur the lines far from the sung one. Each word fades to white as it is sung, with a soft glow and a few spark particles.
4. Rose section: a neon pink line-art rose that draws itself stroke by stroke beside stacked lyric blocks, mixing Great Vibes script, Inter bold caps and Instrument Serif italic, each word blurring in on its sung time.
5. Clip sections: Spotify-style lyrics over the first clip, then big Inter 900 words with the clip showing only inside the letters (knockout text), ending with the camera flying through one letter into the full clip.
6. Story sections: a cinema letterbox with subtitles and one key word in pink script, then a dotted footstep path across the frame with the lyric's letters placed along it, and a soft pink glow on words like kiss or love.
7. Last line as a split screen: the clip on one side with the first half of the line, an empty dark side with the second half turning to dust.
8. Soft blur or light-leak transitions between sections, a short fade in and out of the audio, and 1920×1080 at 30 fps with the song (plus a 4K copy if I ask).

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
