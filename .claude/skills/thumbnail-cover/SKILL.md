---
name: thumbnail-cover
description: "Make the Reel cover (1080x1920) and the YouTube thumbnail (1280x720) for a finished video: picks the strongest frames, then sets one big Hindi or Hinglish title on them in three layouts each, inside the Instagram safe zone and grid crop. Use when the user asks for a cover, a thumbnail, a cover frame or a poster for a video, or types /thumbnail-cover with a video and the title."
argument-hint: "[final video, and the cover text]"
---

# Thumbnail and cover

The click decides whether anyone sees the video, so every finished film gets a cover and a thumbnail. This skill picks
the frames and sets the type; the words come from the owner or from the publishing kit (the social agent's cover text).

**Input:** the finished video (`projects/<slug>/final/*.mp4`) and the cover text (3–6 words; Hindi in Devanagari,
Hinglish in Latin), optionally a smaller second line.
**Run it:** `/thumbnail-cover projects/<slug>/final/film.mp4 "मौत से डर लगता है?"`

## Steps
1. **Pick frames:** `python3 .claude/skills/thumbnail-cover/scripts/covers.py pick <video> projects/<slug>/covers --n 6`
   - scores every 0.25 s for sharpness, contrast and colour, skips frames on a cut and the first 0.5 s
   - writes `cand_01.png` …, `candidates.json` and `sheet.png`
   - look at the sheet and choose the frame where the subject reads at a glance: a face with a clear expression, the
     key object, the most dramatic moment. The score only ranks; the choice is yours, and the owner's.
2. **Words:** the hook in 3–6 words, a question or a sharp claim, the most loaded word last (it is drawn in the accent
   colour). Never a claim the video does not make. A second line only if it adds something.
3. **Make:** `python3 .claude/skills/thumbnail-cover/scripts/covers.py make projects/<slug>/covers/cand_03.png "<text>" projects/<slug>/covers [--sub "..."] [--accent "#ffd400"] [--font "Rozha One"]`
   - `cover_reel_A/B/C.png`: A title top on a dark fade, B title bottom-left on an accent bar, C a text panel above the frame
   - `thumb_yt_A/B/C.png`: the same three for 16:9
   - fonts: Rozha One (default; Devanagari and Latin), Yatra One (comic), Teko (Latin condensed), Bangers (Latin comic);
     all from `studio/fonts/`. Match the film's own type where it has one.
4. **Check:** every title sits inside the safe zone (top 250 px, bottom 420 px) and the 3:4 profile-grid crop of the
   reel cover; nothing important under the text; the text reads at thumbnail size (look at it at 25 %).
5. Show the owner the six images as numbered options and let them choose. Never pick for them in a Gate.

## Render settings (studio)
- Reel cover 1080×1920 PNG; YouTube thumbnail 1280×720 PNG (under 2 MB, YouTube's limit).
- Rendered through `studio/render_canvas.cjs` (`--stills 0`) with `studio/canvas_kit.js` and `studio/fonts/fonts.css`,
  so Devanagari shapes correctly and the look is the same on every run.
- Delivered in the film's zip under `covers/`; never posted or uploaded.

## Rules that never bend
- The frame comes from the owner's own video. No generated faces, no stock, no logos or channel branding that is not
  the owner's.
- No misleading text: the cover promises only what the video shows. A real person's face carries no words they did
  not say.
- Ask before overwriting covers (`--force` only after a yes).
