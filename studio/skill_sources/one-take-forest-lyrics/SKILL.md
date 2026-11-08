---
name: one-take-forest-lyrics
description: "A seamless 16:9 lyric video like the Iss Tarah video: Google Flow clips joined into one take with no visible cuts, Hinglish lines with big Hindi hero words sitting behind the characters in the forest, every word moving with its meaning, and a sad ending where she turns to gold particles. Make the clips with the Google Flow prompts, then run this skill to do the whole edit. Use when the user asks for a one-take forest lyric video or types /one-take-forest-lyrics with the song MP3, the lyrics and your Flow clips."
---

# One-take forest lyrics

A seamless 16:9 lyric video like the Iss Tarah video: Google Flow clips joined into one take with no visible cuts, Hinglish lines with big Hindi hero words sitting behind the characters in the forest, every word moving with its meaning, and a sad ending where she turns to gold particles. Make the clips with the Google Flow prompts, then run this skill to do the whole edit.

**Input:** the song MP3, the lyrics and your Flow clips.
**Run it:** `/one-take-forest-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Find the true tempo and the bars, and check it by ear because beat trackers can be off by a few BPM.
2. Look at contact sheets of every clip and list the moments that matter. Retime each clip with a piecewise map so its events land on the words, with optical-flow in-betweens for the slow parts. Skip any bad frames at the start or end of a clip, such as a reference sheet or a jump to another shot.
3. Make a person matte for every frame (u2net human seg) and a camera track of the background. Draw the lyrics between the forest and the people, so characters walk in front of the words, and lock the words to the world so they move with the camera.
4. Fonts: Rozha One for the big Hindi hero words, Playfair Display Italic for the Hinglish lines. Cream text with a two-pass dark shadow, so it reads on the bright sky. Measure where the bodies stand from the mattes before placing any word, and keep lines off faces.
5. Give each hero word its own move from its meaning: दुआ rises from his open hands, सजदा bows flat to the ground, मीरा splits into मी and रा and opens around her, jhanke shakes on the beat, agar trembles, जाना burns into the light, and bhar lo rotates in a ring around them.
6. Joins: every clip change must keep the same object in the same place. Measure the TV or his face on both sides of the join, then move and scale each shot so it stays locked through the join and eases back afterwards. Hide what is left with dust, petals or a flash.
7. देखा moment: freeze the TV frame, turn her into pixel particles while the screen goes white with the word on it, zoom into the screen, then zoom out of the blank TV in the next clip as she climbs out.
8. Ending: keep the music on the beat if the clips need extra seconds, by reusing the instrumental from whole bars earlier. Finish on his small smile, then fade to white with the song title.

## Every time it runs

- The only generated images and clips are the ones I make in Google Flow. Do the retiming, joins, lyrics and render in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg).
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- Never change the colour grade of my clips.
- If a clip is missing, ask me for it. Never use a placeholder.
- Show me a contact sheet of stills, and frame strips across every join, before the full render. Ask before overwriting files.
- Render the MP4 with the song, plus a smaller copy for WhatsApp.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
