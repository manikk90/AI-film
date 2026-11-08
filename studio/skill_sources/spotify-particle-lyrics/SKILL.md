---
name: spotify-particle-lyrics
description: "A 16:9 lyric video in four looks, like the Kalyani (ARJN × KDS × Fifty4 × Ronn ft. Shreya Ghoshal) video: a tilted Spotify lyrics card where every sung word lights up with glowing sparks, then the artists' photo turned into a monochrome particle portrait that morphs into a second photo while red-and-white lyrics pop on the right and dance on the beat, then gold motion-graphic lyrics with fast blur word changes for the singer's part, and a black-and-white rain-on-glass music player to end. Use when the user asks for a Spotify-card particle lyric video or types /spotify-particle-lyrics with a song MP3 (or a clip of it), its lyrics, 1–2 photos (the artists, and a second photo to morph into), the Spotify logo PNG and a reference reel for the motion-graphic part."
---

# Spotify particle lyrics

A 16:9 lyric video in four looks, like the Kalyani (ARJN × KDS × Fifty4 × Ronn ft. Shreya Ghoshal) video: a tilted Spotify lyrics card where every sung word lights up with glowing sparks, then the artists' photo turned into a monochrome particle portrait that morphs into a second photo while red-and-white lyrics pop on the right and dance on the beat, then gold motion-graphic lyrics with fast blur word changes for the singer's part, and a black-and-white rain-on-glass music player to end.

**Input:** a song MP3 (or a clip of it), its lyrics, 1–2 photos (the artists, and a second photo to morph into), the Spotify logo PNG and a reference reel for the motion-graphic part.
**Run it:** `/spotify-particle-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track. Find the beat and the kicks (librosa). Tell me which lines are rap and which are sung, and propose the sections: Spotify card → particles → Spotify again → motion graphics → rain ending.
2. Analyze the reference reel at 2 frames per second and write down its fonts, colours, word timing, transitions and camera moves, so the motion-graphic part copies that style.
3. Spotify card: a deep maroon card with the cover art, song title, artists and my Spotify logo (white behind its transparent bars), lyrics in big Inter bold. Tilt the card in 3D with a slow camera drift and blur the lines far from the sung one. Each word fades from dark to white with an ease-in-out as it is sung, with a soft glow, a burst of spark particles from across the word, small cross glints and a light point that rides along the word.
4. Particle portrait: remove the photo backgrounds, then turn each one into 20–25k stipple dots (local contrast + edges so the faces read) in white on near-black. Dots breathe with the beat and drift with red and white embers. On a chosen word, morph every dot from the first photo into the second with a fast staggered swirl and a flash ring. At the end, blow the dots apart. No artist names on screen.
5. Right-side lyrics during the particles, like the Let Me Love You kinetic video: rows alternating Inter 900 white caps and Instrument Serif italic red, each word popping in with a small overshoot on its sung time, letters bouncing on every beat, and each block blurring out before the next.
6. Motion graphics for the sung part in the reference style: gold serif words stacked and changing fast with a blur in and out, a moon on a starfield, and a curved lyric wall that turns like a cylinder. Show each lyric only once on screen, never a duplicate big word.
7. Rain ending: a blurred black-and-white music player (cover card, progress bar, lyric rows lighting up as sung) seen through glass, with hundreds of small water drops that each refract the scene, a few running drops with trails, grain and a vignette.
8. White flash or blur cuts between sections, a short fade in and out of the audio, and 1920×1080 at 30 fps with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
