---
name: red-silhouette-lyrics
description: "A still, cinematic 16:9 lyric video like the Afsos video: flat orange-red silhouettes of a guitarist and a standing man on a charcoal-green film background, cutting between wide, medium and close shots on the beat, with one small serif lyric phrase in the centre and dry-brush strokes of light sweeping through. Use when the user asks for a red silhouette lyric video or types /red-silhouette-lyrics with a song MP3 (a 40–60 s cut works), its lyrics with | marks where you want each phrase to split, and the song title."
---

# Red silhouette lyrics

A still, cinematic 16:9 lyric video like the Afsos video: flat orange-red silhouettes of a guitarist and a standing man on a charcoal-green film background, cutting between wide, medium and close shots on the beat, with one small serif lyric phrase in the centre and dry-brush strokes of light sweeping through.

**Input:** a song MP3 (a 40–60 s cut works), its lyrics with | marks where you want each phrase to split, and the song title.
**Run it:** `/red-silhouette-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Split the lyrics at my | marks into short phrases, and show one phrase at a time. Find the beats (librosa) and write a shot table: phrase, shot, and any brush stroke.
2. Background: flat charcoal green (#1F2622) with a faint soft light in the middle, old-film dust specks, thin vertical scratches that flicker for a frame or two, and fine grain on everything. No gradients on the figures and no other colours.
3. Figures: draw two ORIGINAL silhouettes in code, a guitarist playing and a man standing still, in flat orange-red (#E0462E) with a light paper grain and the guitar body slightly darker. Never trace a real person or a frame from another video. They stand apart and never touch.
4. Shots: hard cuts on the beat, no fades and no camera moves. Use a small set of framings: both figures wide, guitarist medium, man medium in profile, guitarist close, a very close shot of the guitar neck and strings. Leave some phrases completely empty, just the text on the green, so the figures feel like they come and go.
5. Lyrics: one small line of serif type (EB Garamond, about 54 px) in off-white, always in the centre of the frame, even when it sits over a figure. It cuts on with its sung phrase and cuts off at the end of it, with no animation at all.
6. Light strokes: a few times in the video, a dry-brush stroke of green, pink or red paint sweeps across the frame on a strong beat, drawn on along its length with rough bristle edges, then gone. Keep them rare so each one feels like an event.
7. Ending: the last phrase sits alone on the green, a final silhouette holds, and the audio fades out over half a second. 1920×1080 at 24 fps with the song.

## Every time it runs

- Draw everything in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg). No stock footage or image generators, so the look is the same every time.
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
