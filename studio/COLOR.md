# Colour: the 60-30-10 rule (owner rule, 2026-11-08)

Owner: "60 main 30 second or 10 loud ... ye logic ko samjho or hrr jgah apply kro". It applies to every visual the studio makes: films, style frames, the Gate 3 preview, edits of the owner's footage, motion graphics, covers and thumbnails, captions and title cards, the ready formats and the replicas Marich specifies.

## The logic
- **60 % main.** The world: background, sky, walls, paper. It sets the mood, so it stays quiet: one hue family, low to medium saturation.
- **30 % second.** The people and big props: costume, furniture, the set's second colour. It contrasts with the main colour without fighting it.
- **10 % loud (accent).** Where the eye must go. It is the most saturated or brightest colour in the frame, and it is rare, which is why it works.

## How to use it
1. **Choose the three colours per film before drawing,** in the format brief or the style sheet, with a reason. Write them as hex values.
2. **The accent is a story decision.** Give it to the thing the story follows: the planted object, the hero's prop, the stamp, the CTA. Never spread it over everything.
3. **Keep the accent constant across the film,** so the viewer learns it. Main and second can shift between scenes, such as night and dawn.
4. **Let the accent grow at the climax:** 10 % can rise to about 20 % for the turn or the payoff, then fall back.
5. **Text follows the same rule.** Captions sit in the main or second family; only the key word takes the accent.
6. **Skin tones are never forced** into the palette. Protect them and build the 60/30/10 around them.

## Check it
`python3 studio/palette.py frame.png` or `python3 studio/palette.py film.mp4 --every 2` splits each frame into 6 colour groups, sorts them into main, second and accent (loud = saturated and bright), and prints the shares. The target bands are: main 50–70 %, second 20–40 %, accent 3–15 %, and at least one loud accent. It measures a 72 px wide frame, so a near miss is a judgement call; a frame with no accent at all, or an accent over 25 %, needs a fix or a reason.

- **Director:** in the format brief, and in QC on the Gate 3 frames and the contact sheets.
- **Mann:** in the grade and the storyboard check.
- **Social:** on the cover and the thumbnail.
- **Marich:** measure the original's palette as a layer of the breakdown, and put the 60/30/10 hex values in `REPLICA_SPEC.md`.
