---
name: red-sun-lyrics
description: "A quiet, aching 16:9 lyric video like the Kaisey Jiyun video: crumpled indigo paper, a huge crimson disc in the sky, a bare black tree that loses one red leaf for every line, a lonely figure sitting under it, one small black line drawing inside the disc for each line, and red calligraphy lyrics that blur in word by word. Use when the user asks for a red sun lyric video or types /red-sun-lyrics with a song MP3 (a 30–60 s cut works), its lyrics, the song title and the artist name."
---

# Red sun lyrics

A quiet, aching 16:9 lyric video like the Kaisey Jiyun video: crumpled indigo paper, a huge crimson disc in the sky, a bare black tree that loses one red leaf for every line, a lonely figure sitting under it, one small black line drawing inside the disc for each line, and red calligraphy lyrics that blur in word by word.

**Input:** a song MP3 (a 30–60 s cut works), its lyrics, the song title and the artist name.
**Run it:** `/red-sun-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Read every line and pick one tiny picture that means it (a tear, two people holding hands, a rain cloud, a heart, a sunrise, a crescent, a broken heart, a shooting star, a question mark), then show me the list.
2. Background: crumpled indigo paper (deep blue #141A78 to #0D1158) with soft fold lines and light beams drifting slowly across it. A huge crimson disc (#E5334A with a warmer glowing centre) rises in the first seconds and pulses very slightly with the song.
3. The tree: a bare black tree grows from the ground line in front of the disc during the title, branch by branch. A small hunched figure sits under it in thin line art. Red leaves sit on the branches, and one falls on every lyric line and settles on the ground, so the tree is nearly empty by the end.
4. Inside the disc, the picture for each line draws itself in thin black ink as the line is sung, holds, and fades before the next one. Keep each drawing small and simple, so it reads like a thought.
5. Lyrics: flowing red calligraphy (Great Vibes) in the empty side of the frame, a small line above and the key word bigger below, in a lighter pink for the small words. Each word blurs in exactly when it is sung. The title opens in the same script with the artist name under it in thin condensed capitals (Saira Extra Condensed), and fades out before the first line.
6. Ending: the last leaf falls, the lyrics clear, and everything fades slowly to black. Light paper grain on everything, a short fade in and out of the audio, 1920×1080 at 30 fps with the song, plus a 9:16 version with the disc and tree on top and the lyrics below.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
