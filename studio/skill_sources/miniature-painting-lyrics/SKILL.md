---
name: miniature-painting-lyrics
description: "A seamless 16:9 lyric video like the Khat video: an Indian miniature painting that comes alive, flowing from paper flowers to a diya, a pop-up blue house, her eye, a field of blue flowers and a flying letter with no visible cuts, and Hindi lyrics that move with their meaning. It includes the real Gemini image prompts and Google Flow video prompts. Use when the user asks for a miniature painting lyric video or types /miniature-painting-lyrics with a song MP3 (a 60–75 s cut works), its lyrics in Devanagari, the song title and the artist name."
---

# Miniature painting lyrics

A seamless 16:9 lyric video like the Khat video: an Indian miniature painting that comes alive, flowing from paper flowers to a diya, a pop-up blue house, her eye, a field of blue flowers and a flying letter with no visible cuts, and Hindi lyrics that move with their meaning. It includes the real Gemini image prompts and Google Flow video prompts.

**Input:** a song MP3 (a 60–75 s cut works), its lyrics in Devanagari, the song title and the artist name.
**Run it:** `/miniature-painting-lyrics` and attach or name the files.

## Steps

1. Separate the vocals (demucs) and force-align every word of my lyrics on the vocal track, exactly as I wrote them. Find the beats with librosa. Read the lyrics and write the story in one line, then a table of which picture belongs to each lyric line, and show it to me.
2. Give me the 3 Gemini image prompts below. I'll make each one at the highest quality and save them as sheet-1.png, sheet-2.png and sheet-3.png. Cut each sheet along its grid into 4 separate 1920×1080 frames and name them A to L. All the people are on sheet 1, so they stay consistent without separate character images.
3. Give me the 4 round 1 Flow prompts below, one at a time, with the two frames to attach to each. I'll use Frames to Video at 16:9 with 2 outputs, on a Veo model that takes a first and last frame. Tell me to run clip 3 first, because it's the hardest and shows quickly whether two scenes fit in one clip, and to re-roll if a face melts, a hard cut appears or text shows up.
4. When the 4 clips are back, watch where they feel slow or empty. Cut the first and last frames for the 4 round 2 prompts at the times listed and give me those prompts. These add the big moments: the ink vine to the temple, the pop-up house, the couple together, and the letter flying over the town.
5. Re-cut all 8 clips into about 11 shots that run close to real speed, so nothing looks stretched. Mute the Flow audio. Flow doesn't always land on the exact last frame, so drop any part where a person's look changes. Time each shot to its lyric line and hide the joins with a zoom through an object, a glow from the flame, a soft fade, or a watercolour bloom that spreads across the frame.
6. Lyrics: Devanagari in Tiro Devanagari Hindi with Kalam for the handwritten words, a few words at a time, in the empty part of each shot. Each word appears exactly when it is sung, and each line gets an effect that matches its meaning: words about writing are written on stroke by stroke, the prayer rises out of the diya flame, the house line folds up like the pop-up house, the blue paint line is revealed with a dry-brush stroke, the flower line blows in on the wind, and the khat line is written on the envelope and moves with it. Put a torn paper slip behind any word on a busy shot so it stays readable.
7. Open on the title in Caladea with the artist name small below it, over the hands folding flowers, and fade it out before the first line. End on the hand lifting the letter at the blue door, then fade out. Add light paper grain, 1920×1080 at 30 fps with the song.

## Every time it runs

- The only generated images and clips are the ones I make from your prompts. Do the cutting, joins, lyrics and render in code (an HTML canvas rendered frame by frame in headless Chrome, encoded with ffmpeg).
- Time every word with forced alignment (torchaudio MMS_FA). Never guess timings.
- If a frame or clip is missing, ask me for it. Never use a placeholder.
- Show me a contact sheet of stills before the full render, and ask before overwriting files.
- Render the MP4 with the original audio, plus a 720p copy under 20 MB for WhatsApp.

## Prompts (from the Khat video)

The prompts below are the real ones from the Khat video. For Khat, give them to me word for word. For any other song, keep the style lines, the 2x2 grid and the two-part clip structure, and change only the people, places and objects to fit my lyrics.

### Gemini image prompts (3 images, each a 2x2 grid = 12 frames)

#### Sheet 1, the people (TOP LEFT = C, TOP RIGHT = F, BOTTOM LEFT = H, BOTTOM RIGHT = I)

One wide 16:9 image divided into a 2x2 grid of four separate paintings. Each panel is its own full 16:9 scene, all four the same size, separated only by a thin straight black line. No outer margin. No text, numbers, labels, letters or signatures anywhere. All four panels share one style: Traditional Indian miniature painting, Rajasthani-Mughal gouache on handmade paper, fine brush outlines, soft paper grain, jewel colours of ultramarine blue, rose pink and marigold yellow with cream highlights, strong colour contrast, tender emotional mood.

The same two people appear across the panels. He is a gentle young Indian man in his early 20s with soft curly black hair and kind tired eyes, in a pale yellow cotton kurta with rolled sleeves and a thin red thread on his right wrist. She is a young Indian woman in her early 20s with a long black braid, a small bindi and a warm bright smile, in a deep blue cotton salwar suit, rose pink dupatta, small silver jhumkas and glass bangles.

TOP LEFT: Night. He sits cross-legged at a low wooden desk in a small room with deep indigo walls, writing a letter with a reed pen. Folded pink and yellow paper flowers lie around him. On the right, an arched window shows yellow stars and a distant white temple spire, with a small lit clay diya in the window niche. The letter shows only faint wavy lines.

TOP RIGHT: Bright morning. He is seen from three-quarter back in an empty unfinished room, holding a wide brush. The left third of the white wall is painted wet ultramarine blue. A paint pot and ladder stand nearby. Yellow sunlight and pink bougainvillea come through an open doorway.

BOTTOM LEFT: Pink and gold evening on a rooftop terrace. She sits on a low parapet, laughing, holding out one small blue flower, her pink dupatta lifting in the breeze. Behind her are yellow marigold garlands, pots of blue flowers and a distant old town.

BOTTOM RIGHT: Extreme close-up of her eye filling the panel: fine lashes, kajal, warm brown iris, with a tiny field of blue flowers reflected in the iris.

#### Sheet 2, the covers (TOP LEFT = B, TOP RIGHT = E, BOTTOM LEFT = G, BOTTOM RIGHT = J)

One wide 16:9 image divided into a 2x2 grid of four separate paintings. Each panel is its own full 16:9 scene, all four the same size, separated only by a thin straight black line. No outer margin. No text, numbers, labels, letters or signatures anywhere. All four panels share one style: Traditional Indian miniature painting, Rajasthani-Mughal gouache on handmade paper, fine brush outlines, soft paper grain, jewel colours of ultramarine blue, rose pink and marigold yellow with cream highlights, strong colour contrast, tender emotional mood.

Each panel is filled completely edge to edge, with no background, no people and no other objects.

TOP LEFT: Hundreds of folded paper flowers packed tightly together, in rose pink and marigold yellow with a few ultramarine ones.

TOP RIGHT: Pure warm white-gold light with only a faint paper texture.

BOTTOM LEFT: Wet ultramarine blue paint with soft visible brush strokes and a slight shine.

BOTTOM RIGHT: Close-up delicate ultramarine and sky blue five-petal flowers with yellow centres, packed tightly with no sky and no ground.

#### Sheet 3, the objects (TOP LEFT = A, TOP RIGHT = D, BOTTOM LEFT = K, BOTTOM RIGHT = L)

One wide 16:9 image divided into a 2x2 grid of four separate paintings. Each panel is its own full 16:9 scene, all four the same size, separated only by a thin straight black line. No outer margin. No text, numbers, labels, letters or signatures anywhere. All four panels share one style: Traditional Indian miniature painting, Rajasthani-Mughal gouache on handmade paper, fine brush outlines, soft paper grain, jewel colours of ultramarine blue, rose pink and marigold yellow with cream highlights, strong colour contrast, tender emotional mood.

TOP LEFT: A single sheet of handmade cream paper fills the panel, softly lit, with faint fibres. One small folded rose pink paper flower and one marigold yellow paper flower rest near the centre. Nothing else.

TOP RIGHT: Extreme close-up of one small clay diya with a single large golden flame in the exact centre, against deep indigo darkness with a soft warm glow.

BOTTOM LEFT: Dense indigo night sky with gold stars and curling miniature-style clouds. One small folded cream letter tied with pink thread, a single blue flower tucked under the thread, floats in the exact centre.

BOTTOM RIGHT: Dawn. A small house with an ultramarine blue wall and an open wooden door, pink bougainvillea above, yellow marigolds along the path. At the threshold, a woman's hand with glass bangles lifts a folded letter tied with pink thread, a blue flower on it. Only her hand, forearm and the edge of a rose pink dupatta are visible. A thin painted floral border in blue, pink and yellow runs around this panel on handmade cream paper.

### Flow video prompts, round 1 (Frames to Video, first frame + last frame)

#### Clip 1, first frame A, last frame D

Hand-painted Indian miniature painting coming gently to life. Two parts in one continuous shot, with no hard cuts. Slow, soft, dreamlike movement. Keep the painted paper texture and colours. No text, no speech, no music. Part 1: gentle hands in pale yellow sleeves fold paper flowers on the page, and more flowers gather until they fill the whole frame. Part 2: the flowers fall away to reveal a young man in a yellow kurta from behind, writing at a low desk at night. The camera glides past him to a window niche and pushes in until the diya flame fills the frame.

#### Clip 2, first frame D, last frame G

Hand-painted Indian miniature painting coming gently to life. Two parts in one continuous shot, with no hard cuts. Slow, soft, dreamlike movement. Keep the painted paper texture and colours. No text, no speech, no music. Part 1: the flame flickers and the camera pulls back to two cupped hands in yellow sleeves folded in prayer around the diya, then the flame brightens until warm light fills the frame. Part 2: the light settles into a bright empty room where the young man, seen from behind, paints a white wall with long strokes. The blue spreads and the camera pushes in until wet blue paint fills the whole frame.

#### Clip 3, first frame H, last frame J

Hand-painted Indian miniature painting coming gently to life. Two parts in one continuous shot, with no hard cuts. Slow, soft, dreamlike movement. Keep the painted paper texture and colours. No text, no speech, no music. Part 1: she laughs and speaks softly, tucks a strand of hair behind her ear, and the camera slowly pushes into her eye until it fills the frame. Part 2: her eye blinks once, the reflected blue flowers grow, and the camera passes through the iris into a swaying field of blue flowers until they fill the whole frame.

#### Clip 4, first frame J, last frame L

Hand-painted Indian miniature painting coming gently to life. Two parts in one continuous shot, with no hard cuts. Slow, soft, dreamlike movement. Keep the painted paper texture and colours. No text, no speech, no music. Part 1: the flowers part from the centre to reveal a folded letter tied with pink thread. A breeze lifts it and it drifts up into a starry indigo night. Part 2: the letter drifts down as the sky brightens to pink dawn and lands at the door of a blue house. The door opens and a hand with glass bangles lifts the letter.

### Flow video prompts, round 2 (first and last frames are cut from the round 1 clips)

#### Extra clip 1, Pen to temple and back (frames from clip 1 at 6.4 s and 8.4 s)

Hand-painted Indian miniature painting coming to life, matching the style, paper texture and colours of the first frame. One continuous, flowing camera move with no hard cuts. Confident and fast, but graceful. No text, no speech, no music. The camera swoops down to his pen nib. Blue ink flows off the page as a living vine with small blue flowers, races across the desk, up the wall and out of the window into the night. The camera follows it over dark rooftops to a white temple spire under yellow stars, then turns away and glides back through the window to the lit diya in its wall niche.

#### Extra clip 2, The house builds itself (frames from clip 2 at 4.6 s and 5.6 s)

Hand-painted Indian miniature painting coming to life, matching the style, paper texture and colours of the first frame. One continuous, flowing camera move with no hard cuts. Confident and fast, but graceful. No text, no speech, no music. The light flares to pure white, then settles on a sheet of cream paper. A small blue house folds itself up from the paper like a pop-up book: walls rise, shutters open, the roof lands, pink bougainvillea climbs over it. The camera flies fast toward the open door and through it into a bright empty room, where the man stands with his brush.

#### Extra clip 3, The memory together (frames from clip 3 at 2.4 s and 4.8 s)

Hand-painted Indian miniature painting coming to life, matching the style, paper texture and colours of the first frame. One continuous, flowing camera move with no hard cuts. Confident and fast, but graceful. No text, no speech, no music. She laughs and turns, pointing at something. The camera sweeps back to reveal a rose pink evening terrace with pots of blue flowers, and a young man in a yellow kurta beside her, seen from behind, watching her. A blue petal floats past. The camera then rushes smoothly back to her face and into her eye until it fills the frame.

#### Extra clip 4, The letter's journey (frames from clip 4 at 4.4 s and 6.8 s)

Hand-painted Indian miniature painting coming to life, matching the style, paper texture and colours of the first frame. One continuous, flowing camera move with no hard cuts. Confident and fast, but graceful. No text, no speech, no music. The letter dives and the camera chases it as it swoops over a sleeping old town, past windows glowing with diyas, along a river of floating diyas and through a drifting cloud of paper flowers. It climbs again as the sky turns from indigo to pink dawn, arriving above a blue roof.

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Lyric videos
