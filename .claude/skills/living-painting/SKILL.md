---
name: living-painting
description: "A painting made in code that comes alive as a seamless 6-second loop: watercolour, stone mosaic, ink wash, impasto oil, night gouache, botanical plate, paper cut, Art Nouveau, golden hour, hand-painted anime background, Madhubani, Indian miniature, Warli or Diwali gouache, or any medium you describe. No voice, no footage, no video model. Use when the user asks for a living painting, an animated painting, an ambient art loop, a painted reel background or intro, or types /living-painting with a scene and a medium (or a preset name)."
argument-hint: "[preset name, or a scene + a medium]"
---

# Living painting

A still painting drawn entirely in code, then brought to life as a seamless loop, then polished in measured rounds.
Made for reel openers, painted backgrounds under lyrics, story breaks and standalone art posts.

**Input:** a preset (`python3 .claude/skills/living-painting/scripts/new_painting.py --list`) or a scene plus a medium
in the owner's words. Optional: length (default 6 s), aspect (default 9:16), a song to lay under it.
**Run it:** `/living-painting diwali_gouache` or `/living-painting "a tiger drinking at a forest pool" in "Kalighat painting"`.

Method credit: the three-round method (paint, animate, polish) follows Skale Out's public tutorial
([learn.skaleout.com/animation-styles](https://learn.skaleout.com/animation-styles), read 2026-11-14). The presets,
scenes, template and checks here are the studio's own; their prompt text is not copied. Breakdown and gate record:
`projects/living-painting/re/` (Daksh job).

## Before you start
- Read `studio/LEARNINGS.md`. Make `projects/<slug>/` with `STATUS.md` from `studio/templates/` and log each step.
- `python3 .claude/skills/living-painting/scripts/new_painting.py <slug> <preset>` (or `custom --scene ... --medium ...`)
  writes `projects/<slug>/painting.html` from the template, with the brief at the top. It never overwrites without `--force`.
- The template already loads `studio/fonts/fonts.css` and `studio/canvas_kit.js` and renders end to end; replace its
  `paint*()` functions and the subject with the new scene.

## Round 1: paint the still
1. Write the scene as one painting at 1080×1920. The medium must look made by hand in that medium, not a filter on
   flat shapes: real texture, uneven edges, the marks the tool leaves, the ground (paper, canvas, wall, stone)
   showing through. No flat vector fills, no plain digital gradients.
2. One function per element: the subject, every other creature or object, and every depth layer of the background,
   each painted once into its own offscreen layer (`K.layer`). Seeded randomness only (`K.rng`, `K.noise`).
3. Keep the subject in the middle half of the frame with room to move. No text on screen.
4. Show the owner one still (Gate 3, `node studio/render_canvas.cjs painting.html projects/<slug>/still --stills 0`).
   Change the painting from their notes before anything moves.

## Round 2: bring it to life
1. Everything lives: the subject moves with purpose (big, readable poses: wingbeats, strides, strokes, never a small
   wobble); every other element has small idle motion.
2. Every motion has a reason inside the scene: wind, water, light, or the subject passing.
3. The medium decides how things move (each preset's `motion` line): paper pieces hinge and never melt, mosaic stones
   never slide through each other, light in gouache is a painted dab that brightens, not a digital glow. Paint layers
   move; the paper or canvas grain stays fixed to the frame.
4. Camera: a slow push-in (about 1.0 → 1.3) with the subject kept in the middle half, and parallax by depth (near
   layers move further than far ones).
5. Seamless loop: every motion is a whole number of cycles of the loop length (`K.loopWave`), so the last frame flows
   into the first. A one-way slide only loops if that layer is painted tileable; otherwise sway it.
6. Smooth: every position, angle and brightness on an eased curve; time comes from t only, never from the clock.
7. Render: `node studio/render_canvas.cjs painting.html projects/<slug>/loop.mp4 --size 1080x1920 --fps 30`.

## Round 3: polish, measured
Run `python3 .claude/skills/living-painting/scripts/loop_check.py projects/<slug>/loop.mp4`, then fix what fails,
one fix at a time, re-render and re-check:

| Check fails / you see | Fix |
|---|---|
| `seam`: the loop visibly restarts | make every motion whole cycles of the loop; sway layers that are not tileable |
| `still`: parts of the picture never move | give each a small reasoned motion: wind, ripple, drifting light, mist |
| `motion`: the subject barely moves | make its action twice as big and let it travel further, camera keeping it centred |
| `snap`: something jumps | put that position, angle or brightness on an eased curve |
| `black`, or a page error | find the error in the render output, fix, re-render |
| it looks digital (by eye) | more medium texture: uneven edges, tool marks, ground showing through; keep the motion |
| it stutters while previewing | paint textured layers once, only move and combine them per frame |

Then show the owner 3 numbered frames (start, middle, end) and wait for their OK before final delivery.

## Render settings (studio)
- **Output:** `9:16 1080×1920` (or `16:9 1920×1080` on request), 30 fps, 6 s = 180 frames by default, H.264 High,
  yuv420p, CRF 18, `-movflags +faststart`.
- **Audio:** none by default. With a song or a bed: `--audio song.mp3 --abitrate 256k`; a sound bed from
  `python3 studio/sfx.py` (wind, bell, typing…) only when the owner asks.
- **For posting:** an Instagram loop plays better at 2–3 repeats: `ffmpeg -stream_loop 2 -i loop.mp4 -c copy loop_x3.mp4`.
- **WhatsApp copy:** `python3 studio/whatsapp_copy.py loop.mp4 loop_whatsapp.mp4`.
- **QC before delivery:** `loop_check.py` OK, then `python3 studio/frame_check.py loop.mp4 --size 1080x1920 --fps 30 --silent`
  (drop `--silent` when a song or bed is laid under it).

## Rules that never bend
- Everything is drawn in code: no images, video models or stock. The same seed gives the same painting.
- Original scenes and characters only. Name a medium or a tradition, never a studio, film or artist to copy; the
  "anime background" preset is an original look, not any studio's.
- Ask before overwriting files. Deliver to `projects/<slug>/final/` with `studio/deliver.py` (the video, and one zip
  with the page, brief and QC).
