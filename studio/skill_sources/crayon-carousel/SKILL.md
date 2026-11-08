---
name: crayon-carousel
description: "The trending crayon carousel from How to do this with Claude (Ep 3): every slide puts a crayon drawing of your photo on top, labelled “One day”, over the real photo labelled “Day one”, ready to post as an Instagram carousel. Use when the user asks for a crayon carousel or types /crayon-carousel with 3–10 of your photos, and their crayon drawings from Gemini."
---

# Crayon carousel

The trending crayon carousel from How to do this with Claude (Ep 3): every slide puts a crayon drawing of your photo on top, labelled “One day”, over the real photo labelled “Day one”, ready to post as an Instagram carousel.

**Input:** 3–10 of your photos, and their crayon drawings from Gemini.
**Run it:** `/crayon-carousel` and attach or name the files.

## Steps

1. First give me a Gemini prompt that redraws each of my photos as a colourful crayon drawing on white paper (same pose, outfit and place, bold wax-crayon strokes, a bit childlike). I'll make the drawings and save them next to the photos with _drawing at the end of the name.
2. Make one 4:5 slide (1080×1350) per photo: the crayon drawing on the top half and the real photo on the bottom half, both cropped to fill, with a thin white gap between them.
3. Crop each half around the person (find the face or body) so nobody gets cut off.
4. Write “One day” on the top-left of the drawing and “Day one” on the top-left of the photo, in a handwritten white font (Caveat) with a soft shadow so it reads on any background.
5. Export every slide as a numbered PNG, in the same order as my photos, plus one contact sheet so I can check them all at once.

## Every time it runs

- The only generated images are the crayon drawings I give you. Lay out the slides and draw the text in code (Python Pillow or an HTML canvas).
- Keep the person fully in frame in both halves, and never stretch an image.
- Show me the first slide before making the rest, and ask before overwriting files.

## Helper scripts

Run from this skill's folder (`.claude/skills/crayon-carousel/`).

- `scripts/make_slides.py`: pairs every photo with its `<name>_drawing` image and makes 1080×1350 slides: drawing on top, photo below, a 6 px white gap, each half cover-cropped (never stretched) around the person (MediaPipe face detection when installed, otherwise a skin-tone and detail centroid). Writes the labels in Caveat (pass `--font Caveat.ttf`; otherwise the best TTF it finds), white with a soft shadow, then numbered PNGs and `contact_sheet.png`. `--first-only` makes slide 1 for the preview; it refuses to overwrite without `--force`.

  ```bash
  python3 scripts/make_slides.py photos_dir out_dir [--font Caveat-Bold.ttf] [--first-only] [--force]
  ```

---
From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Trend edits
