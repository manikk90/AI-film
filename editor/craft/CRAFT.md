# Mann's craft rulebook

98 rules in 15 domains; 30 are checked automatically by `craft-check` (also run by `storyboard` and `qc`), the rest are Mann's frame-by-frame checklist. Thresholds live in `editor/rules.json`; owner corrections change them there.

Contents: [Cuts](#cuts) · [Transitions](#transitions) · [Continuity](#continuity) · [Eyelines and eye-trace](#eyelines-and-eye-trace) · [Shot composition](#shot-composition) · [Shot sizes, angles and moves](#shot-sizes-angles-and-moves) · [Pacing and rhythm](#pacing-and-rhythm) · [Typography hierarchy](#typography-hierarchy) · [Colour](#colour) · [Safe zones and grids](#safe-zones-and-grids) · [Sound](#sound) · [Motion graphics](#motion-graphics) · [VFX and effects](#vfx-and-effects) · [Story structure for short video](#story-structure-for-short-video) · [Accessibility](#accessibility) · [Safe zones](#safe-zone-profiles) · [Type scale](#type-scale) · [Font pairings](#font-pairings) · [Colour themes](#colour-themes) · [Sources](#sources)

## Cuts

### Hard (straight) cut `hard-cut` · auto-checked

- **What:** Instant change from one shot to the next.
- **When:** The default. Use it unless another cut has a reason.
- **How (Mann):** `transition_in: cut` (or omit).
- **Avoid:** Replacing it with transitions for decoration.

### Jump cut `jump-cut` · auto-checked

- **What:** Cut within the same shot that skips time.
- **When:** Talking heads, vlogs, compressing a process; signals energy and honesty.
- **How (Mann):** Consecutive clips from one source with a gap; alternate a punch-in (`zoom` 1.1-1.25) so it reads as intentional.
- **Avoid:** Same framing on both sides without a size change (reads as a mistake).

### Match cut (graphic match) `match-cut`

- **What:** Cut between two shots that share a shape, colour, movement or composition.
- **When:** Transitions in time or place, loop endings, poetic links.
- **How (Mann):** Pick in/out so the matching element sits in the same screen position; check both frames side by side on the storyboard.
- **Avoid:** Near-misses where the match is off-position.

### Match on action (cut on action) `cut-on-action`

- **What:** Cut in the middle of a movement so it continues into the next shot.
- **When:** Any physical action across two angles.
- **How (Mann):** Out point 2-4 frames into the motion, in point at the same moment of motion on the next angle.
- **Avoid:** Cutting before or after the action; repeating the action.

### J-cut `j-cut`

- **What:** The next shot's audio starts before its picture.
- **When:** Leading into a new scene or speaker; smoother dialogue.
- **How (Mann):** Use a picture insert (`inserts`) over the end of the previous clip, or start the music/SFX early with `sfx.at`.
- **Avoid:** Overlaps so long the viewer loses who is speaking.

### L-cut `l-cut`

- **What:** The previous shot's audio continues over the next picture.
- **When:** Reactions, B-roll over speech, ending a scene softly.
- **How (Mann):** B-roll `inserts` over a talking clip keep its voice running underneath.
- **Avoid:** Leaving the viewer without the speaker's face for too long in emotional moments.

### Cutaway `cutaway`

- **What:** A shot of something else related, then back.
- **When:** Hide a jump, show what is being talked about, add context.
- **How (Mann):** `inserts` from B-roll sources.
- **Avoid:** Cutaways unrelated to the words.

### Cut-in / insert `cut-in`

- **What:** A closer shot of a detail within the same scene.
- **When:** Show hands, objects, reactions, text on screens.
- **How (Mann):** A clip from a detail source, or a punch-in `zoom` of 1.5+ on high-resolution footage.
- **Avoid:** Punch-ins that drop below delivery resolution (soft image).

### Cross-cut (parallel editing) `cross-cut`

- **What:** Alternating between two actions happening at once.
- **When:** Tension, deadlines, contrast between two lives.
- **How (Mann):** Interleave clips from two sources; shorten shots as the threads converge.
- **Avoid:** Losing which thread is which; give each a distinct look or sound.

### Smash cut `smash-cut`

- **What:** Abrupt cut from a high-intensity moment to its opposite (or vice versa).
- **When:** Comedy, shock, a sudden twist.
- **How (Mann):** Hard cut with an audio change (loud to silence or the reverse) on the same frame.
- **Avoid:** Softening it with a transition.

### Invisible (hidden) cut `invisible-cut`

- **What:** A cut hidden in a whip, a dark frame or an object crossing the lens.
- **When:** One-take illusions, seamless transitions.
- **How (Mann):** Cut on the frame of maximum blur or darkness; a 0.2-0.3 s `smoothleft`/`dissolve` can soften the join.
- **Avoid:** Audio jumps at the join; keep ambience continuous.

### Shot / reverse shot `shot-reverse-shot`

- **What:** Alternating angles of two people facing each other.
- **When:** Conversations, confrontations.
- **How (Mann):** Keep both sides on the same side of the 180-degree line with matching eyelines and similar shot sizes.
- **Avoid:** Mismatched sizes without a reason; crossing the line.

### Reaction cut `reaction-cut`

- **What:** Cut to a listener's reaction.
- **When:** Land a joke or a revelation; give the audience permission to feel.
- **How (Mann):** Hold the reaction a beat longer than feels necessary on emotional lines.
- **Avoid:** Cutting away before the reaction peaks.

### Sound bridge `sound-bridge`

- **What:** A sound that carries across a cut to connect two scenes.
- **When:** Time or place jumps, transitions without visual effects.
- **How (Mann):** Music or SFX that starts before and ends after the cut (`audio.music`, `sfx`).
- **Avoid:** Bridges that hide the speaker's words.

### Flash cut `flash-cut` · auto-checked

- **What:** A cut through a frame or two of white (or a very short shot).
- **When:** Memory flashes, impacts, music hits.
- **How (Mann):** `fx: flash` on the incoming clip.
- **Avoid:** More than three flashes in any second (photosensitivity).

### Punch-in (digital zoom cut) `punch-in` · auto-checked

- **What:** A cut to a tighter crop of the same shot.
- **When:** Emphasis in talking heads; fake second angle.
- **How (Mann):** `zoom: {from: 1.15, to: 1.15}` on alternate clips; at least a 20 % size change.
- **Avoid:** Small changes (under 20 %) that look like a glitch.

### Speed-ramp cut `speed-ramp-cut`

- **What:** Speed up into the cut and slow down out of it (or reverse).
- **When:** Action, sports, velocity edits, travel transitions.
- **How (Mann):** Alternate `speed` between clips (e.g. 1.8 then 0.6) with the cut on the fast part.
- **Avoid:** Ramping dialogue.

### Whip-pan cut `whip-cut`

- **What:** Cut hidden inside fast pans on both shots.
- **When:** Energetic scene changes.
- **How (Mann):** Cut at peak blur; `smoothleft` 0.15-0.25 s if the footage has no real whip.
- **Avoid:** Whips in opposite directions on the two sides.

### Cut on the beat `beat-cut`

- **What:** Cut points aligned with the music's beats or bars.
- **When:** Montages, music videos, hype edits.
- **How (Mann):** `beats` gives the grid; autocut `beat_sync`; cut on downbeats for big changes, off-beats for energy.
- **Avoid:** Every cut on every beat for minutes (monotony): vary with bars and half-bars.

### Montage (metric, rhythmic, tonal, overtonal, intellectual) `montage-types`

- **What:** Eisenstein's montage methods: by fixed length, by movement in the frame, by emotional tone, by all of these, and by ideas colliding.
- **When:** Compressing time, building a feeling, making an argument with images.
- **How (Mann):** Metric: fixed clip length on the bar. Rhythmic: cut on movement. Intellectual: alternate two images to create a third meaning.
- **Avoid:** Random shot order; every montage needs a direction.

## Transitions

### Every transition is motivated `transition-motivated` · auto-checked

- **What:** Dissolves mean time passing or memory; fades mean endings; wipes and slides are graphic and playful.
- **When:** Only when the meaning fits.
- **How (Mann):** Keep non-cut transitions to 30 % of cuts or less, and at most two types in one film.
- **Avoid:** A different transition on every cut.

### Dip to black / white `dip-to-black`

- **What:** Fade out and in through a colour.
- **When:** Chapter breaks, big time jumps, before a reveal (black) or a memory (white).
- **How (Mann):** `fadeblack` / `fadewhite`, 0.3-0.8 s.
- **Avoid:** Using it inside a scene.

### Dissolve length `dissolve-length`

- **What:** Short dissolves (0.2-0.4 s) feel smooth; long ones (0.8-2 s) feel dreamy.
- **When:** Match the length to the tempo.
- **How (Mann):** `transition_in.duration`.
- **Avoid:** Dissolves through busy frames (muddy double exposure).

## Continuity

### 180-degree rule `180-rule`

- **What:** Keep the camera on one side of the line between two subjects so left and right stay consistent.
- **When:** Any dialogue or action between two subjects.
- **How (Mann):** Check on the storyboard that A always looks right and B always looks left (or vice versa).
- **Avoid:** Crossing the line without a neutral shot or a visible camera move.

### 30-degree rule `30-degree-rule` · auto-checked

- **What:** Between two shots of the same subject, change the angle by at least 30 degrees or the size clearly.
- **When:** Every cut on the same subject.
- **How (Mann):** For one-camera footage, alternate punch-ins of at least 20 %.
- **Avoid:** Near-identical framing (unintended jump cut).

### Screen direction `screen-direction`

- **What:** A subject moving left-to-right keeps that direction across cuts.
- **When:** Journeys, chases, walks.
- **How (Mann):** Check motion direction on adjacent storyboard frames.
- **Avoid:** Flipping direction unless the character turns back.

### Props, wardrobe and position `props-wardrobe`

- **What:** Objects, clothes and positions match across cuts.
- **When:** Every cut inside a scene.
- **How (Mann):** Compare adjacent frames for hands, cups, hair, sleeves.
- **Avoid:** Cutting between takes with visible differences without a cutaway.

### Light and colour continuity `light-continuity` · auto-checked

- **What:** Shots of one scene share light direction and colour.
- **When:** Mixing takes or cameras.
- **How (Mann):** One grade per scene; per-clip `grade` only to match or to mark a story change.
- **Avoid:** More than two looks without a story reason.

### Room tone continuity `room-tone`

- **What:** Background sound stays continuous under cuts.
- **When:** Dialogue edits, jump cuts.
- **How (Mann):** Keep source audio or a room-tone bed; never digital silence under picture unless deliberate.
- **Avoid:** Audible drops or hum jumps at cuts.

### Audio-video sync `av-sync`

- **What:** Lips and hits must line up.
- **When:** Every speech and impact.
- **How (Mann):** Do not trim audio separately from picture; speed changes keep pitch (atempo).
- **Avoid:** Audio late by more than about 125 ms or early by more than about 45 ms (ITU-R BT.1359).

## Eyelines and eye-trace

### Eyeline match `eyeline-match`

- **What:** When a character looks off-screen, the next shot shows what they see, from the matching direction.
- **When:** Looks, reveals, POV.
- **How (Mann):** Character looks frame-right, so the object appears as if seen from frame-left in the next shot.
- **Avoid:** Eyelines that point at the wrong place.

### Eye-trace (Murch) `eye-trace`

- **What:** Place the next shot's point of interest where the viewer's eye already is.
- **When:** Fast cutting, Shorts, montages.
- **How (Mann):** Compare the subject position at the out frame and the in frame on the storyboard; keep them within the same third.
- **Avoid:** Making the eye jump across the frame on every fast cut.

### Look room (nose room) `look-room`

- **What:** Leave space in the direction a subject is looking or moving.
- **When:** Profiles, three-quarter shots, movement.
- **How (Mann):** Subject on the third opposite the look direction; on 9:16 reframes, shift the crop toward the look.
- **Avoid:** Faces pressed against the frame edge they look at.

### Eyes on the upper third `eye-height`

- **What:** Eyes sit near the upper third line in medium and close shots.
- **When:** Talking heads, interviews.
- **How (Mann):** On 9:16, eyes around 30-38 % of the height so captions at 60-72 % stay clear.
- **Avoid:** Eyes centred or too low with headroom wasted.

### Direct address `direct-address`

- **What:** Looking into the lens speaks to the viewer.
- **When:** Hosts, creators, confessions.
- **How (Mann):** Keep direct-to-lens shots for the hook and the call to action.
- **Avoid:** Mixing to-lens and off-lens looks in one answer.

## Shot composition

### Rule of thirds `rule-of-thirds`

- **What:** Place subjects on the thirds lines and their crossings.
- **When:** Most shots.
- **How (Mann):** Overlay a thirds grid on storyboard frames when judging reframes.
- **Avoid:** Centring everything without a symmetrical intent.

### Centre and symmetry `symmetry`

- **What:** Centred subjects and mirrored frames feel formal, iconic or uncanny.
- **When:** Wes Anderson-style, hero shots, one-point perspective.
- **How (Mann):** Use deliberately; keep the centre line exact.
- **Avoid:** Almost-symmetric frames (look like mistakes).

### Golden ratio / phi grid `golden-ratio`

- **What:** A slightly tighter alternative to thirds (lines at 38.2 % and 61.8 %).
- **When:** Elegant, cinematic framing.
- **How (Mann):** Same as thirds with the phi grid.
- **Avoid:** Treating it as a rule rather than a guide.

### Headroom `headroom`

- **What:** Space above the head.
- **When:** Every person shot.
- **How (Mann):** Small headroom in close-ups (the top of the head may crop); more in wides.
- **Avoid:** Too much headroom (subject sinks) or cropping the chin.

### Leading lines `leading-lines`

- **What:** Lines (roads, rails, walls) that lead the eye to the subject.
- **When:** Wides, establishing shots.
- **How (Mann):** Choose crops that keep the lines' vanishing point near the subject.
- **Avoid:** Lines that lead out of the frame.

### Frame within a frame `frame-within-frame`

- **What:** Doors, windows, arches frame the subject.
- **When:** Isolation, voyeurism, Indian architecture.
- **How (Mann):** Keep the inner frame intact in reframes.
- **Avoid:** Cropping the inner frame's edges.

### Depth: foreground, middle, background `depth-layers`

- **What:** Layers create depth.
- **When:** B-roll, establishing shots.
- **How (Mann):** Prefer shots with a foreground element; slow push-ins (`zoom`) add parallax feeling.
- **Avoid:** Flat frames against walls when depth is available.

### Negative space `negative-space`

- **What:** Empty space that gives a subject weight or loneliness, or room for text.
- **When:** Emotional beats, title placements.
- **How (Mann):** Put titles in the negative space, not over faces.
- **Avoid:** Text over eyes or mouths.

### Avoid tangents and joint crops `tangents`

- **What:** Do not crop people at joints (neck, elbows, knees, ankles) and avoid edges that just touch.
- **When:** Every reframe and punch-in.
- **How (Mann):** Crop between joints; check punch-ins on the storyboard.
- **Avoid:** Cutting off hands, chins or feet.

### Level horizon `horizon`

- **What:** Horizons are level unless the tilt is deliberate (Dutch angle).
- **When:** Wides, travel, drones.
- **How (Mann):** Rotate in pre-processing if needed.
- **Avoid:** Slight accidental tilts.

### Reframing 16:9 to 9:16 `vertical-reframe`

- **What:** Vertical crops keep about a third of a 16:9 frame.
- **When:** Every horizontal source in a vertical film.
- **How (Mann):** Set `reframe: auto` (clip or `format`): the crop follows the tracked face smoothly. Check each storyboard frame for cut-off hands and text; split-screen or `fit: contain` when two subjects matter.
- **Avoid:** Centre-cropping by default when the subject is off-centre.

### Subject in frame after reframing `subject-in-frame` · auto-checked

- **What:** After a 16:9 to 9:16 (or any) reframe, the main face stays inside the frame, near the upper third, and clear of the captions.
- **When:** Every clip with `reframe: auto`.
- **How (Mann):** Face tracking (OpenCV) moves the crop; craft-check measures where the tracked face lands: centre between 20 % and 80 % of the width, 15 % and 55 % of the height, and above the caption band.
- **Avoid:** Centre crops that cut the speaker out; faces under the captions.

### Nothing over the face `face-clear` · auto-checked

- **What:** No text item or overlay is drawn on the speaker's face while the face is on screen.
- **When:** Every edit with reframing or declared treatments, for every text item and overlay.
- **How (Mann):** craft-check maps the reframe face track onto the timeline (reframe plan, or the frame's fit and zoom), grows each face box by `face_box_pad`, and fails when a text box or an overlay's `bbox` (or its measured alpha) covers more than `face_overlap_max_share` of it. Cover beats and insert spans are skipped.
- **Avoid:** Lower thirds across the chin, centred titles on the eyes, stickers on the mouth.

## Shot sizes, angles and moves

### Shot sizes `shot-sizes`

- **What:** Extreme wide (place), wide (body in place), full, medium, medium close-up, close-up (emotion), extreme close-up (detail), insert.
- **When:** Wide to establish, close for emotion, inserts for information.
- **How (Mann):** Vary sizes across cuts; tighten as tension rises.
- **Avoid:** Three cuts in a row at the same size on different subjects without a pattern.

### Angles `angles`

- **What:** Eye level (neutral), high (smaller, weaker), low (power), Dutch (unease), overhead (pattern, god's view), POV, over-the-shoulder.
- **When:** Angle carries meaning; choose it on purpose.
- **How (Mann):** Low angles for hero and mass styles; overhead for process and food.
- **Avoid:** Random angle changes.

### Camera moves `moves`

- **What:** Pan, tilt, dolly/push, truck, crane, handheld, gimbal, whip.
- **When:** Push-ins add intensity; pull-outs reveal; handheld adds urgency.
- **How (Mann):** Simulate slow pushes with `zoom` (1.0 to 1.08-1.15 over the clip).
- **Avoid:** Cutting mid-move from one move into an opposite move.

### Lens feel `lens-feel`

- **What:** Wide lenses exaggerate depth and speed; long lenses compress and isolate.
- **When:** Choose footage for the feeling.
- **How (Mann):** Prefer long-lens shots for emotion, wides for energy.
- **Avoid:** Wide lenses close to faces (distortion) in beauty or emotion.

## Pacing and rhythm

### Murch's rule of six `rule-of-six`

- **What:** A cut should serve, in order: emotion 51 %, story 23 %, rhythm 10 %, eye-trace 7 %, 2D screen plane 5 %, 3D space 4 %.
- **When:** Choosing between cut points.
- **How (Mann):** Never give up a higher criterion to save a lower one.
- **Avoid:** Keeping perfect continuity at the cost of emotion.

### Short-form tempo `shorts-tempo` · auto-checked

- **What:** A visual change every 1.5-3 s, hook in the first second, no dead air over 1 s.
- **When:** Reels and Shorts.
- **How (Mann):** QC checks shot length, hook and dead air (editor/rules.json).
- **Avoid:** Uniform shot lengths: vary 0.6-3 s.

### Hold for emotion `hold-for-emotion`

- **What:** Let important moments breathe longer than the average shot.
- **When:** Reveals, reactions, the turn.
- **How (Mann):** One longer shot before the payoff; a deliberate silence (`deliberate_silences`).
- **Avoid:** Cutting away from tears or laughter at the peak.

### Shot variety `variety` · auto-checked

- **What:** Vary shot size, angle and length.
- **When:** Always.
- **How (Mann):** Avoid four clips in a row from one source at one framing.
- **Avoid:** Monotone sequences.

### Re-hooks `rehook`

- **What:** A new question or reveal every 20-40 s in long form, every 8-12 s in Shorts.
- **When:** Retention dips.
- **How (Mann):** Mark re-hook beats in `beat` notes and check them on the storyboard.
- **Avoid:** Long explanatory stretches without a new question.

### Loop ending `loop-ending`

- **What:** The last frame or line leads back into the first.
- **When:** Shorts and Reels built to replay.
- **How (Mann):** Match cut the last frame to the first; end the music on an upbeat.
- **Avoid:** Outros, logos and 'thanks for watching' at the end of a Short.

### Speaker, overlay or cover per line `speaker-overlay-cover` · auto-checked

- **What:** Every spoken line is shown one of three ways: the speaker alone, the speaker with a transparent overlay (a keyword, a number, a list), or a cover (an opaque full frame of B-roll while the voice runs on).
- **When:** Talking-head edits, interviews, explainers and shorts cut from long videos. Declare it with `treatment: speaker|overlay|cover` (and an overlay's `timing: lead|sync|wait`) on each EDL beat.
- **How (Mann):** `suggest` drafts the table from the transcript. craft-check: open and close on the speaker, no speaker-only stretch over `speaker_run_max_seconds`, covers between `cover_min_seconds` and `cover_max_seconds`, at least `face_between_covers_min_seconds` of speaker between covers (inserts count as covers). Overlays lead structure by `overlay_lead_frames`, land numbers on their spoken word, and make punchlines wait for the revealing word.
- **Avoid:** A long unbroken head; covers so short they flicker or so long the speaker is lost; text that invents figures nobody said.

## Typography hierarchy

### Four levels `type-levels` · auto-checked

- **What:** Title (hook, 1-4 words), headline (section or key line), body/caption (spoken words), label (names, dates, sources).
- **When:** Every film with on-screen text.
- **How (Mann):** Give text items a `role`; sizes come from the type scale.
- **Avoid:** Everything the same size and weight.

### Type scale `type-scale` · auto-checked

- **What:** Each level at least 1.2x the one below (default scale 1.414).
- **When:** Setting sizes.
- **How (Mann):** Defaults as a fraction of frame height: label 0.028, caption 0.042, headline 0.06, title 0.085.
- **Avoid:** Sizes too close to tell apart (under 1.2x).

### Two families maximum `two-families` · auto-checked

- **What:** One display face and one text face; use weights for more contrast.
- **When:** Always.
- **How (Mann):** Choose a `typography.pairing`; individual `font` overrides count as families.
- **Avoid:** Three or more families.

### Minimum size on phones `min-size` · auto-checked

- **What:** Text smaller than about 3 % of the frame height is hard to read on a phone.
- **When:** All text.
- **How (Mann):** craft-check flags text under `text_min_height_ratio`.
- **Avoid:** Small labels as the only carrier of key information.

### Reading time `reading-time` · auto-checked

- **What:** On-screen text needs about 1 s per 3 words plus 0.5 s (default).
- **When:** Titles, callouts, quotes.
- **How (Mann):** craft-check compares each text item's duration with its word count.
- **Avoid:** Text that disappears before it can be read.

### Caption rules `caption-rules` · auto-checked

- **What:** Reading speed, line length, lines and minimum duration (Netflix guides: 42 characters per line, 2 lines, at least 5/6 s; speed varies by language, 17-20 cps for adults).
- **When:** Burned subtitles and captions.
- **How (Mann):** craft-check: `caption_max_cps`, `caption_min_seconds`, characters per line by aspect, `caption_max_lines`.
- **Avoid:** Full sentences on a phone screen; captions over faces.

### Text contrast `contrast` · auto-checked

- **What:** Text needs contrast with what is behind it (WCAG: 4.5:1, 3:1 for large text).
- **When:** Every text item.
- **How (Mann):** craft-check samples the frame behind the text; use `box: true`, an outline or a darker grade there.
- **Avoid:** White text on bright sky without a box or shadow.

### One emphasis per line `emphasis`

- **What:** Highlight one key word by colour or weight, not several.
- **When:** Captions and titles.
- **How (Mann):** Split the key word into its own caption or colour it.
- **Avoid:** Rainbow captions.

### Case and tracking `tracking-case`

- **What:** Uppercase Latin text needs a little extra letter-spacing (about +5-10 %); never letter-space Devanagari (it breaks the shirorekha line).
- **When:** Titles and labels.
- **How (Mann):** In Hyperframes use CSS `letter-spacing` only on Latin uppercase.
- **Avoid:** Uppercase body text; tracked Devanagari.

### Devanagari specifics `devanagari` · auto-checked

- **What:** Devanagari needs a font with conjunct shaping and usually 10-15 % more size than Latin for the same legibility (default).
- **When:** Hindi text.
- **How (Mann):** Use a pairing with Devanagari support; all burned text goes through the `ass` filter with complex shaping (drawtext and the subtitles filter mis-place pre-base matras like ि in this FFmpeg build); check matras and conjuncts on the storyboard.
- **Avoid:** Latin-only fonts (Inter, Montserrat, Bebas Neue, Playfair Display, Anton have no Devanagari) and faux bold.

### Alignment and grid `alignment`

- **What:** Align text to the safe-zone grid; centre for captions, left for lists and data.
- **When:** Motion graphics and titles.
- **How (Mann):** Hyperframes compositions use the 12-column grid inside the safe zone.
- **Avoid:** Text placed by eye at random positions.

## Colour

### Colour harmonies `harmonies`

- **What:** Complementary (opposites, energy: teal and orange), analogous (neighbours, calm), triadic (playful), split-complementary (balanced contrast), monochrome (mood).
- **When:** Choosing the grade and the graphics palette.
- **How (Mann):** Pick a `colour_theme`; graphics use its accent, the grade supports its base.
- **Avoid:** Many unrelated accents.

### 60-30-10 `60-30-10`

- **What:** About 60 % dominant, 30 % secondary, 10 % accent.
- **When:** Graphics, titles, set and wardrobe.
- **How (Mann):** Accent only on the key word, the CTA or the subject.
- **Avoid:** Accent colour everywhere (loses its pull).

### Temperature and meaning `temperature-meaning`

- **What:** Warm reads as nostalgia, comfort or heat; cool as night, tech, distance or fear; desaturated as documentary or grim.
- **When:** Setting the grade per act.
- **How (Mann):** A colour script: one temperature per act, change it at the turn.
- **Avoid:** Random temperature changes between shots of one scene.

### Protect skin tones `skin-tones`

- **What:** Skin should look natural after grading; on a vectorscope it sits near the skin-tone (I) line.
- **When:** Every grade with people.
- **How (Mann):** Check faces on storyboard frames; ease saturation or orange push if skin turns red or grey.
- **Avoid:** Teal-orange so strong that skin goes orange.

### Grade consistency `consistency` · auto-checked

- **What:** Shots in one scene match; looks change only with the story.
- **When:** Multi-camera, mixed sources, AI clips.
- **How (Mann):** One global `grade`; per-clip grades only to match or mark a change.
- **Avoid:** More than two distinct looks without a reason.

### Cultural colour (India) `cultural-colour`

- **What:** Commonly: saffron for devotion and courage, red for weddings and celebration, green for nature and prosperity, gold for festivity, white often for purity and in many communities mourning.
- **When:** Indian stories, festivals, myth.
- **How (Mann):** Check the meaning with the researcher's notes for the specific community and story.
- **Avoid:** White-dominated palettes for celebrations without checking.

### Do not rely on colour alone `accessibility-colour`

- **What:** Information shown only by colour is lost for colour-blind viewers.
- **When:** Charts, comparisons, highlights.
- **How (Mann):** Add labels, icons or position as well as colour.
- **Avoid:** Red vs green as the only difference.

## Safe zones and grids

### Title and action safe (16:9) `title-safe` · auto-checked

- **What:** SMPTE ST 2046-1: title safe 90 %, action safe 93 % of the frame.
- **When:** Horizontal delivery, TV, YouTube long form.
- **How (Mann):** craft-check keeps text within the 90 % box for 16:9 and 1:1.
- **Avoid:** Text touching the edges.

### Vertical platform UI zones `vertical-safe` · auto-checked

- **What:** Reels, Shorts and TikTok overlay the top, the bottom (captions, buttons) and the right side (icons). No single official spec; sources differ.
- **When:** All 9:16 delivery.
- **How (Mann):** `standard` profile (default): clear the top 12.5 %, bottom 25 %, left 6 %, right 13 %. `strict` (ads, Shorts-safe): top 15 %, bottom 35 %, left 4.5 %, right 18 %. Set `safe_zone_profile` in editor/rules.json.
- **Avoid:** Captions and faces in the bottom quarter or under the right-side icons.

### 12-column grid for graphics `grid-12`

- **What:** A 12-column grid with gutters inside the safe zone keeps graphics aligned.
- **When:** Motion graphics, lists, data.
- **How (Mann):** Hyperframes compositions: CSS grid of 12 columns inside the safe-zone box.
- **Avoid:** Graphics that do not line up between scenes.

### Centre-cut protection `centre-cut`

- **What:** When one master feeds 16:9 and 9:16, keep key action in the centre third.
- **When:** Shooting or editing for multiple aspects.
- **How (Mann):** Check the 9:16 crop of 16:9 storyboard frames.
- **Avoid:** Key action at the edges.

## Sound

### Voice first `voice-first` · auto-checked

- **What:** Speech must be clear above everything.
- **When:** Any film with words.
- **How (Mann):** Music at least 10 dB under the voice (duck 10-12 dB); carve 2-5 kHz out of the music when needed.
- **Avoid:** Music fighting the voice.

### Loudness target `loudness-target` · auto-checked

- **What:** -14 LUFS integrated, true peak -1 dBTP for YouTube and Spotify-style normalisation; Instagram and TikTok publish no exact spec.
- **When:** Every master.
- **How (Mann):** Two-pass loudnorm in render; QC measures.
- **Avoid:** Masters louder than -12 LUFS (turned down and squashed).

### Four layers `layers`

- **What:** Dialogue, music, SFX, ambience.
- **When:** Every film.
- **How (Mann):** Plan all four on the storyboard's sound plan.
- **Avoid:** Missing ambience (sounds empty) or missing SFX on visible actions.

### Silence as a tool `silence` · auto-checked

- **What:** A short silence before a reveal makes it hit harder.
- **When:** Turns, punchlines, drops.
- **How (Mann):** List it in `deliberate_silences` so QC does not flag it.
- **Avoid:** Accidental dead air.

### Click-free edits `click-free`

- **What:** Audio cuts need short fades (about 10-20 ms) to avoid clicks.
- **When:** Every audio cut.
- **How (Mann):** Transitions use acrossfade; hard cuts are trimmed at low-energy points.
- **Avoid:** Cuts mid-syllable or mid-waveform peak.

## Motion graphics

### Easing `easing`

- **What:** Nothing moves linearly: ease-out for entrances, ease-in for exits, ease-in-out for moves.
- **When:** Every animation.
- **How (Mann):** GSAP `power2`-`power4` eases in Hyperframes.
- **Avoid:** Linear motion (robotic).

### Timing `timing`

- **What:** UI-style moves 0.2-0.5 s; big reveals 0.6-1.2 s; stagger lists by 30-80 ms (default).
- **When:** Titles, lists, callouts.
- **How (Mann):** Land the end of a move on a beat.
- **Avoid:** Everything moving at once.

### Animation principles `principles`

- **What:** Anticipation, follow-through, overlapping action, squash and stretch (lightly), arcs, secondary action.
- **When:** Characterful graphics.
- **How (Mann):** A small anticipation before a big move; overshoot on settle.
- **Avoid:** Overdone bounces in serious content.

### Direction logic `direction-logic`

- **What:** Things enter from where they come from and exit the way they go; forward is left-to-right in Latin layouts.
- **When:** Lists, timelines, maps.
- **How (Mann):** Keep one direction per film.
- **Avoid:** Elements flying in from random sides.

## VFX and effects

### Effects need a reason `motivated-fx`

- **What:** Shake for impact, flash for a hit or memory, glitch for tech or breakdown, grain for era.
- **When:** Only where the story or style asks.
- **How (Mann):** Per-clip `fx`; style defaults from the catalog.
- **Avoid:** Effects on every clip.

### Photosensitivity `flash-safety` · auto-checked

- **What:** No more than three flashes in any one second (WCAG 2.3.1).
- **When:** Flash cuts, strobes, glitches.
- **How (Mann):** craft-check counts `flash` effects per second.
- **Avoid:** Strobe sequences.

### Clean speed ramps `speed-ramp-quality`

- **What:** Slow motion looks smooth only from high frame-rate sources.
- **When:** Slow motion under 0.5x.
- **How (Mann):** Prefer sources at 50-120 fps for slow motion; otherwise keep 0.6x or faster.
- **Avoid:** Stuttery slow motion from 24/30 fps footage.

## Story structure for short video

### Hook in the first second `hook-first` · auto-checked

- **What:** The first frame and the first words must create a question.
- **When:** Every short.
- **How (Mann):** QC checks the first cut; the storyboard's first frame is the hook.
- **Avoid:** Logos, intros, greetings first.

### Open loops `open-loop`

- **What:** Raise a question early and pay it off late.
- **When:** Every story.
- **How (Mann):** Mark the question and payoff beats in `beat` notes.
- **Avoid:** Answering the hook in the first 5 s.

### Payoff and button `payoff`

- **What:** End on the strongest beat, then a short button (a line, a reaction, a loop).
- **When:** Endings.
- **How (Mann):** Trim everything after the button.
- **Avoid:** Trailing endings.

## Accessibility

### Captions for speech `captions-on` · auto-checked

- **What:** Most viewers watch muted on phones; captions carry the words.
- **When:** Short-form with speech.
- **How (Mann):** QC requires subtitles for short-form when `short_form_requires_subtitles` is on.
- **Avoid:** Speech-only key information.

### Readable contrast and size `readable-contrast` · auto-checked

- **What:** See typography contrast and minimum size.
- **When:** All text.
- **How (Mann):** craft-check.
- **Avoid:** Low-contrast stylised text for key information.

## Safe zone profiles

Fractions of the frame kept clear of text and faces. Choose with `safe_zone_profile` in `editor/rules.json`.

| Aspect | Profile | Top | Bottom | Left | Right |
|---|---|---|---|---|---|
| 9:16 | standard | 12.5% | 25.0% | 6.0% | 13.0% |
| 9:16 | strict | 15.0% | 35.0% | 4.5% | 18.0% |
| 4:5 | standard | 8.0% | 15.0% | 6.0% | 6.0% |
| 4:5 | strict | 10.0% | 20.0% | 6.0% | 10.0% |
| 1:1 | standard | 5.0% | 5.0% | 5.0% | 5.0% |
| 1:1 | strict | 7.0% | 10.0% | 7.0% | 7.0% |
| 16:9 | standard | 5.0% | 5.0% | 5.0% | 5.0% |
| 16:9 | strict | 5.0% | 12.0% | 5.0% | 5.0% |

## Type scale

Ratio x1.414 between levels. Sizes as a fraction of the frame height; set a text item's `role` and Mann sizes it.

| Role | Size | Weight |
|---|---|---|
| title | 8.5% | 800 |
| headline | 6.0% | 700 |
| caption | 4.2% | 700 |
| body | 4.2% | 400 |
| label | 2.8% | 500 |

## Font pairings

Set `"typography": {"pairing": "<id>"}` in the EDL; install with `fonts-install --pairing <id>`. Devanagari support verified on the npm registry (@fontsource, 2026-11-02).

| Id | Display | Text | Devanagari | Mood | Use |
|---|---|---|---|---|---|
| `poppins-hind` | Poppins 700 | Hind 600 | yes | clean, modern, creator-friendly; safest Hindi/English default | captions, explainers, social |
| `mukta-tiro` | Mukta 800 | Tiro Devanagari Hindi 400 | yes | contemporary sans titles with a literary serif for quotes | history, poetry, documentaries |
| `rozha-hind` | Rozha One 400 | Hind 600 | yes | high-contrast editorial display, film-poster drama | trailers, titles, Bollywood energy |
| `yatra-mukta` | Yatra One 400 | Mukta 600 | yes | hand-lettered, festive, Indian signage | festivals, food, travel, culture |
| `teko-rajdhani` | Teko 700 | Rajdhani 600 | yes | condensed, sporty, technical | sports, gaming, hype, data |
| `khand-hind` | Khand 700 | Hind 600 | yes | bold condensed headlines, news energy | news shorts, listicles |
| `baloo-poppins` | Baloo 2 800 | Poppins 500 | yes | rounded, friendly, playful | kids, comedy, lifestyle, UGC |
| `eczar-martel` | Eczar 700 | Martel 400 | yes | bookish serif pair, warm and literary | mythology, essays, storytelling |
| `kalam-hind` | Kalam 700 | Hind 500 | yes | handwritten notes over clean text | vlogs, journals, productivity, soft aesthetic |
| `noto-serif-sans` | Noto Serif Devanagari 700 | Noto Sans Devanagari 500 | yes | neutral, very complete coverage, institutional | long subtitles, formal explainers |
| `sarpanch-rajdhani` | Sarpanch 800 | Rajdhani 500 | yes | wide, futuristic, tech | tech, glitch, sci-fi |
| `amita-karma` | Amita 700 | Karma 500 | yes | calligraphic display with a gentle text face | weddings, devotional, romance |
| `laila-kurale` | Laila 700 | Kurale 400 | yes | classic Indian publishing feel | literature, heritage, period pieces |
| `latin-only-note` | Bebas Neue 400 | Inter 600 | **no** | popular English-only pair (no Devanagari) | English-only films |

## Colour themes

Set `"typography": {"theme": "<id>"}`; `mg-new` puts the theme into the Hyperframes composition and the grade preset matches it.

| Id | Name | Harmony | Colours | Grade | Use |
|---|---|---|---|---|---|
| `teal-orange` | Teal and orange | complementary | `#0f3d4a` `#1f7a8c` `#f2a65a` `#f7e1c4` `#111111` | `teal-orange` | blockbuster, travel, hero |
| `saffron-heritage` | Saffron heritage | analogous | `#ff9933` `#c8551b` `#7a2e0e` `#f6e7c8` `#2b1a10` | `warm-film` | history, devotion, culture |
| `monsoon-noir` | Monsoon noir | monochrome + accent | `#0b0f14` `#1d2a35` `#5b7083` `#c9d6df` `#e63946` | `cool-night` | crime, mystery, rain, city |
| `neon-mumbai` | Neon Mumbai | split-complementary | `#0a0014` `#ff2e88` `#00e5ff` `#7cff4f` `#f5f5f5` | `neon-night` | night life, romance, music |
| `pastel-storybook` | Pastel storybook | analogous | `#f6c1c7` `#f9e0ae` `#b8e0d2` `#95b8d1` `#5d4e6d` | `pastel` | whimsy, symmetry, kids |
| `earth-doc` | Earth documentary | analogous | `#2f2a24` `#6b5b4b` `#a68a64` `#d9c9a3` `#c44536` | `desat-doc` | documentary, true crime, rural |
| `royal-rajasthan` | Royal Rajasthan | triadic | `#7b1e3a` `#e0a100` `#1b4f72` `#f4e1c1` `#2d1b0e` | `golden-hour` | weddings, palaces, festivals |
| `clean-tech` | Clean tech | monochrome + accent | `#0b0b0f` `#1f2933` `#e4e7eb` `#ffffff` `#3e7bfa` | `bright-clean` | explainers, tech, productivity |
| `retro-poster` | Retro Bollywood poster | triadic | `#d7263d` `#f46036` `#ffd23f` `#1b998b` `#2e294e` | `faded-vintage` | nostalgia, comedy, retro |
| `kerala-green` | Kerala green | analogous | `#0b3d20` `#2d6a4f` `#74c69d` `#d8f3dc` `#e9c46a` | `warm-film` | nature, travel, food |
| `cyber-glitch` | Cyber glitch | complementary | `#050505` `#00ffd1` `#ff00a8` `#7b2cff` `#e0e0e0` | `neon-night` | tech, gaming, glitch |
| `mono-accent` | Mono with one accent | monochrome + accent | `#111111` `#444444` `#bbbbbb` `#f5f5f5` `#ffcc00` | `bw-contrast` | captions-first creator edits, noir |

## Sources

- **smpte:** SMPTE ST 2046-1:2009 safe areas: action safe 93 %, title safe 90 % of the production aperture (https://pub.smpte.org/doc/st2046-1/20091123-pub/st2046-1-2009.pdf)
- **netflix:** Netflix Timed Text Style Guides: 42 characters per line, 2 lines maximum, minimum event 5/6 s; reading speed varies by language (e.g. 17 cps adult in the Slovak guide, 20 cps adult English as cited by secondary sources) (https://backlothelp.netflix.com/hc/en-us/articles/215274938, https://backlothelp.netflix.com/hc/en-us/articles/115002812588-Slovak-Timed-Text-Style-Guide)
- **murch:** Walter Murch, In the Blink of an Eye: rule of six (emotion 51 %, story 23 %, rhythm 10 %, eye-trace 7 %, 2D plane 5 %, 3D space 4 %) (https://nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch)
- **safe_zones_social:** Social vertical-video safe zones are not published as one official spec; figures vary by source and app version (https://reap.video/blog/short-form-video-safe-zones, https://adaptlypost.com/blog/social-media-safe-zones-2026-complete-guide)
- **loudness:** YouTube and Spotify normalise around -14 LUFS / -1 dBTP; Instagram and TikTok publish no exact spec (https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026)
- **wcag:** WCAG 2.x: text contrast 4.5:1 (3:1 for large text); no more than three flashes in any one-second period (https://www.w3.org/TR/WCAG21/)
- **itu_sync:** ITU-R BT.1359: audio/video sync detectability about +45 ms (audio early) to -125 ms (audio late) (https://www.itu.int/rec/R-REC-BT.1359)
- **cuts:** Film-cut glossaries: MasterClass, Adobe (J and L cuts), No Film School, Artlist (https://www.masterclass.com/articles/essential-film-cuts, https://www.adobe.com/creativecloud/video/discover/j-cut-and-l-cut, https://nofilmschool.com/essential-cuts-every-video-editor-needs-know)
- **fonts:** Font availability and Devanagari subsets verified on the npm registry (@fontsource/<family>, v5.3.0) on 2026-11-02; all fonts listed are open-licensed (OFL) Google Fonts
- **iart-motion-skills:** iart-ai/motion-skills, talking-head-b-roll skill (MIT): speaker / overlay / cover treatments and lead / sync / wait timing; method adopted 2026-11-23 (https://github.com/iart-ai/motion-skills)
- **barty-motion-graphics:** Barty-Bart/motion-graphics, motion-broll skill (MIT): cutaway length and face time between cutaways; method adopted 2026-11-23 (https://github.com/Barty-Bart/motion-graphics)
- **ghost-editor:** kurbaitaev/ghost-editor QC (MIT): nothing over the face, A/V lengths, tail not black; method adopted 2026-11-23 (https://github.com/kurbaitaev/ghost-editor)
