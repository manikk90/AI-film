---
name: night-glow-lyrics
description: "A 16:9 lyric video that makes people feel the song, like the Dooron Dooron (Paresh Pahuja ft. Harleen Sethi) video: one night-blue look with glowing white light, emotional clips that follow the story of each line, an Instagram post that dives into the title, and lyrics that change style with the music (small tracked caps + one huge serif word for the key lines, simple bottom lines in between), ending with the last line turning to light. Use when the user asks for a night-blue glowing lyric video or types /night-glow-lyrics with a song MP3 (or a clip of it), its lyrics, 2–4 emotional video clips (glowing / dreamy couple clips work best) and the song title + artists."
---

# Night glow lyrics

A 16:9 lyric video that makes people feel the song, like the Dooron Dooron (Paresh Pahuja ft. Harleen Sethi) video: one night-blue look with glowing white light, emotional clips that follow the story of each line, an Instagram post that dives into the title, and lyrics that change style with the music (small tracked caps + one huge serif word for the key lines, simple bottom lines in between), ending with the last line turning to light.

**Input:** a song MP3 (or a clip of it), its lyrics, 2–4 emotional video clips (glowing / dreamy couple clips work best) and the song title + artists.
**Run it:** `/night-glow-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track. Find the beats (librosa). Read the lyrics for meaning and the feeling of the song, and tell me the story in one line before you build.
2. Watch every clip at 2 frames per second and list each usable moment (time range + what happens: holding hands, looking from behind, reaching, alone). Map each lyric line to the moment that matches its meaning in a shot table, and never use the same moment twice.
3. One look for the whole video: night blue grade, glowing whites, soft light motes drifting, slow push-ins and crossfades between shots. Keep one font family: Inter 300 tracked caps for small words and Instrument Serif italic for the lyrics, white with a soft blue glow and a dark shadow under the text so it reads over bright clips.
4. Opening: the first clip quiet with no text, then an Instagram post of the second clip (likes, the lyric as the caption, a hashtag) that the camera dives into, landing on the song title in big glowing serif with the artists in small caps.
5. Lyric variety, timed to the voice: for the key lines a hierarchy block placed in the empty space beside the people (a small caps row, one huge serif key word, a medium row), entering with a smooth slide, rise, scale or letter-by-letter fade on the sung words. For the in-between lines a simple centred line at the bottom. Mix both so it never looks like captions.
6. Meaning moments: split lines like mitti / pari into a grey dusty word and a glowing word with sparkles, let words like dooron dooron drift apart letter by letter, and make the last line (kahan main) dissolve into light.
7. Dim any blown-out clip moment (brightness + contrast per shot) so the text always wins. Short fade in and out of the audio, 1920×1080 at 30 fps with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
