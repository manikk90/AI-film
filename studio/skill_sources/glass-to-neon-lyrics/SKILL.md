---
name: glass-to-neon-lyrics
description: "An emotional 16:9 lyric video that keeps changing mood with the song, like the Arz Kiya Hai (Anuv Jain × Lost Stories) video: a red glass Apple-Music-style lyrics card over a wall of giant red words that cracks and shatters, then full-screen clips with the lyrics standing in the empty space (a starry red field with twinkling and shooting stars, a sunny hill, a man against the clouds), a key line cut out as giant letters with fire burning inside them, and a pink neon ending where lyrics fall in, splash and reflect in water while it rains. Use when the user asks for a glass to neon lyric video or types /glass-to-neon-lyrics with a song MP3 (or a clip of it), its lyrics, the cover art, and 4–6 clips or photos with the mood you want for each part."
---

# Glass to neon lyrics

An emotional 16:9 lyric video that keeps changing mood with the song, like the Arz Kiya Hai (Anuv Jain × Lost Stories) video: a red glass Apple-Music-style lyrics card over a wall of giant red words that cracks and shatters, then full-screen clips with the lyrics standing in the empty space (a starry red field with twinkling and shooting stars, a sunny hill, a man against the clouds), a key line cut out as giant letters with fire burning inside them, and a pink neon ending where lyrics fall in, splash and reflect in water while it rains.

**Input:** a song MP3 (or a clip of it), its lyrics, the cover art, and 4–6 clips or photos with the mood you want for each part.
**Run it:** `/glass-to-neon-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Find the beats (librosa). Read the lyrics for meaning and split the song into parts: card, clips, key line, neon ending. Tell me which clip goes with which lines and use every clip only once.
2. Part 1, glass card: a dark red frosted-glass card (cover art, song title, artists) like the Apple Music lyrics screen, tilted slightly in 3D. Each word fills from dim to bright exactly when it is sung, the next line waits blurred below, and a soft shine sweeps across on every line change. Behind it, a slow scrolling wall of the lyric words in giant deep-red caps.
3. At the end of part 1, crack the card with thin light lines, then shatter it into glass shards that fly toward the camera with a red bloom into the next part.
4. Part 2, clips: each clip full-screen in its natural colours, with a slow push-in. Place the lyrics in the empty space of each shot (above the person or below the horizon, never over a face): a small tracked caps row, one big Inter 800 caps row and one word in red Great Vibes script that writes itself on, all word by word on the voice. On a still photo (like a starry field), make it alive: twinkling stars, a few shooting stars and light drifting.
5. Key line: cut the words out of black as giant Inter 900 letters so a fire (or any bright clip) burns only inside the letters, then let the letters grow until the clip fills the screen. Soft white flashes or red burns between shots.
6. Part 3, pink neon ending: all clips in a pink duotone, darker at the bottom. Neon lyric words drop in one by one with a small bounce, flicker on like a sign, and land with a splash ripple and drops on a wet floor that mirrors them. Add light rain and a few drops on glass. On the last word, hold the frame and fade out.
7. Grain and a soft vignette on everything, a short fade in and out of the audio, 1920×1080 at 30 fps with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
