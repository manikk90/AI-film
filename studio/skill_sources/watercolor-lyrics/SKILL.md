---
name: watercolor-lyrics
description: "A soft lyric video like Ashu Shukla's Phir Se Shuru from Ye likho ye milega Part 7: the camera pans right across warm paper while autumn watercolour scenes of one couple draw themselves in (ink lines first, then the wash blooms), leaves fall, and the lyric lines write on word by word. Use when the user asks for a watercolour lyric video or types /watercolor-lyrics with a song MP3, its lyrics, and 10–14 watercolour images of the same couple (I can write the image prompts for you)."
---

# Watercolor lyrics

A soft lyric video like Ashu Shukla's Phir Se Shuru from Ye likho ye milega Part 7: the camera pans right across warm paper while autumn watercolour scenes of one couple draw themselves in (ink lines first, then the wash blooms), leaves fall, and the lyric lines write on word by word.

**Input:** a song MP3, its lyrics, and 10–14 watercolour images of the same couple (I can write the image prompts for you).
**Run it:** `/watercolor-lyrics` and attach or name the files.

## Steps

1. Read the lyrics and plan one scene per line or pair of lines. Write me image prompts for each scene that keep the same couple and outfits (her mustard sweater and maroon scarf, his brown corduroy jacket) in an autumn watercolour style.
2. Separate the vocals and force-align every word. Find the chorus repeats so they reuse the same timing.
3. Lay the scenes along one long sheet of warm textured paper and move the camera slowly and constantly to the right.
4. Reveal every image like a painting: the ink lines draw in first, then the watercolour wash blooms outward from the middle. Add a few maple leaves falling across the frame.
5. Write each lyric block in Amatic SC next to its scene, wiping on word by word as it is sung. Place each block where it doesn't cover a face.
6. Render 16:9 1920×1080 with the song as the audio, in chunks if it is long.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
