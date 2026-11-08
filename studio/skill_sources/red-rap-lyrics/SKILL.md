---
name: red-rap-lyrics
description: "A fast rap lyric video in one red grade, like the Hola Amigo (KR$NA ft. Seedhe Maut) video: a red glass lyrics card that peels in like a page over a tilted wall of lyric words, then neon words standing on a rainy street with ripple reflections, then the rapper's photo turned into a monochrome particle portrait with stacked italic lyrics lighting up word by word, and a 3D tower of words where the camera eases to every new word, ending on a DAMN! slam. Use when the user asks for a red rap lyric video or types /red-rap-lyrics with a rap song MP3 (or a clip of it), its lyrics (Hindi in Devanagari works), one photo of the rapper and your reference reels for each section."
---

# Red rap lyrics

A fast rap lyric video in one red grade, like the Hola Amigo (KR$NA ft. Seedhe Maut) video: a red glass lyrics card that peels in like a page over a tilted wall of lyric words, then neon words standing on a rainy street with ripple reflections, then the rapper's photo turned into a monochrome particle portrait with stacked italic lyrics lighting up word by word, and a 3D tower of words where the camera eases to every new word, ending on a DAMN! slam.

**Input:** a rap song MP3 (or a clip of it), its lyrics (Hindi in Devanagari works), one photo of the rapper and your reference reels for each section.
**Run it:** `/red-rap-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Find the beats and kicks (librosa). Split the song into 4 sections and tell me which lines go in each.
2. Analyze each reference reel at 2 frames per second and write down its fonts, sizes, colours, how words appear and the exact ease of every camera move, so each section copies its reference.
3. Section 1, lyrics card: a dark red glass card (cover art, song title, artists, star and dots icons) that unfolds from a page curl at the corner. Behind it, a huge tilted wall of the lyric words in deep red, drifting slowly. The lines scroll up with an ease-in-out and each word goes from dim red to glowing white exactly when it is sung.
4. Section 2, rainy street: a dark red night street with city blocks, street lamps and their light cones, rain streaks and splash ripples. Each line stands on the ground as 2–3 rows (a big bold condensed row, then a smaller row in red neon that flickers on), word by word on the voice, with a rippling reflection on the wet road below. Slow push-in.
5. Section 3, particle portrait: remove the photo background and turn the rapper into 20–35k white stipple dots (local contrast + edges so the face reads) on a deep red-black glow. The dots fly in, breathe with the beat and drift off the edges with red and white embers. Beside him, each line as stacked italic condensed rows (Teko), each row scaled to a similar width, all words dim grey first and flashing white (keywords red) when sung.
6. Section 4, word tower: place every word in 3D on a corner, front-face words right-aligned to the corner and some words on the side face, key words big and red. On every sung word, move the camera (target, yaw, pitch, roll, distance) to that word with a smooth ease-in-out, then pull back to show the whole tower at the end of the verse.
7. End on the last ad-lib as a huge white condensed word (DAMN!) that slams in with a shake and red echo trails. Mask and mute any swear words I name: show the first letter plus *** and replace only the voice with the instrumental stem at that moment, so the beat keeps playing.
8. Red flash or zoom-blur cuts between sections, grain and a vignette on everything, 30 fps with the song. Render 9:16 1080×1920 and 16:9 1920×1080.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
