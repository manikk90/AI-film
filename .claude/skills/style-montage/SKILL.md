---
name: style-montage
description: "One scene, many styles, one reel: the same moving scene painted in code in N styles (pop art, voxel 3D, risograph, storybook, X-ray, candy, VHS, ceramic tiles, chalkboard, embroidery, Madhubani, Warli, miniature, Diwali gouache and the other living-painting looks), each a seamless loop, cut on one continuous clock so the subject keeps moving through every style change, with a hook card, numbered style chips and a closing grid. Use when the user asks for a style montage, '1 prompt 10 styles', 'ek scene alag alag style mein', a style-switch reel, or types /style-montage with a scene and a list of styles."
argument-hint: "[scene or preset] [styles, comma separated] [optional song]"
---

# Style montage

One scene, only the look changes. Every style is a living painting drawn in code and checked as a seamless loop; the
montage cuts between them on one clock, so the subject is in the same place and the same pose at every cut and only
the style switches. Made for "1 prompt, 10 styles" reels; the desi looks (Madhubani, Warli, miniature, Diwali gouache)
are what make it ours.

**Input:** a scene (a `/living-painting` preset, or the owner's scene and action) and 2 to 12 styles
(`python3 .claude/skills/living-painting/scripts/new_painting.py --list-styles`). Optional: a song, the hook text,
seconds per style (default 0.9 s), aspect (default 9:16).
**Run it:** `/style-montage golden_hour pop_art,voxel_3d,risograph,madhubani,warli,chalkboard`.

Method credit: "one scene, only the style line changes, seamless loops, one reel" follows Skale Out's public
one-prompt-ten-styles page (read 2026-11-22). The styles, scenes, code and checks here are the studio's own; their
prompt text and their car are not used. Daksh job and gate record: `projects/style-montage/re/` (Gate R1 approved
2026-11-23).

## Steps
1. Read `studio/LEARNINGS.md`. Make `projects/<slug>/STATUS.md` from `studio/templates/` and log each step.
2. **Plan:** `python3 .claude/skills/style-montage/scripts/montage.py plan <slug> --preset <preset> --styles a,b,c,...`
   (or `--scene "..." --action "..."`). It writes:
   - `projects/<slug>/motion.js`: the one shared subject path and camera (`MOTION.subject(t)`, `MOTION.camera(t)`).
     Shape it once for the scene. Never move the subject inside one style's page; every page reads `MOTION`.
   - `projects/<slug>/styles/NN-<style>/painting.html` for each style: the living-painting template of that style's
     engine (canvas, or voxel 3D for `voxel_3d`), with its brief at the top and `motion.js` loaded.
   - `plan.json`.
3. **Paint each style** with the `/living-painting` method (Round 1 still, Round 2 motion, Round 3 measured polish) on
   its page: the same scene and the same subject path, only the medium changes. The style's `medium` and `motion` lines
   in the brief are binding. Voxel 3D builds models with `STUDIO.voxel` (`studio/voxel_kit.js`, three.js r159 vendored
   in `third_party/three/`).
4. **Preview (Gate 3):** before rendering every loop, show the owner one still per style
   (`node studio/render_canvas.cjs <page> <prefix> --stills mid`), numbered, and change them from their notes.
5. **Render each loop:** `node studio/render_canvas.cjs projects/<slug>/styles/NN-<style>/painting.html
   projects/<slug>/styles/NN-<style>/loop.mp4 --size 1080x1920 --fps 30`.
6. **Check:** `python3 .claude/skills/style-montage/scripts/montage.py check <slug>` runs living-painting's
   `loop_check` on every loop. Fix each failure with the Round 3 table of `/living-painting`, re-render, re-check.
7. **Assemble:** `python3 .claude/skills/style-montage/scripts/montage.py assemble <slug>` (it refuses while any loop
   fails). Options:
   - `--seg 0.9`: seconds per style; or cut on the music: `python3 studio/beats.py song.mp3 beats.json`, then
     `--beats beats.json --every 2 --audio song.mp3` (the hook then stretches to the first chosen beat, so every cut
     lands on the music).
   - `--hook "..."`: the opening card (default `1 PROMPT` / `N STYLES`; Hindi is shaped correctly, e.g.
     `"एक scene, दस अंदाज़"`); `--hook ""` for none. `--hook-dur 1.2`, `--grid-dur 1.6`.
   - Writes `montage.mp4` and `montage.json` (every segment: style, start, length, source loop and offset). An
     existing montage is never replaced without `--force` (ask the owner first). `plan` and `assemble` hold the
     project lock, so two runs on one project never mix their files.
8. Show the owner 3 numbered frames (the hook, a cut, the grid) and wait for their OK before delivery.

## How the cut stays continuous
`motion.js` is the contract. `MOTION.subject(t)` gives the subject's **screen** point (`x`, `y` as 0..1 of the frame),
its heading `angle` and its action `phase`; `MOTION.camera(t)` gives `zoom` and `panX`/`panY`; `MOTION.DUR` is the
loop length every page uses. Both templates already obey it: the 2D template inverts its camera so the subject is drawn
on that screen point, and the voxel template uses the shared camera (`V.setCamera`) and puts the subject where that
screen point meets the ground (`V.groundAt`). When you repaint a style, keep those lines. Assembly then shows segment
k from source time = global time mod the loop length, so the frame after a cut has the subject exactly where the frame
before it had it. `tests/test_style_montage.py` checks both engines land on the same screen point within 1 % of the
frame.

## Render settings (studio)
- **Output:** `9:16 1080×1920` (or `16:9 1920×1080`), 30 fps, H.264 High, yuv420p, CRF 18, `-movflags +faststart`.
  Length = hook + N × segment + grid (10 styles at 0.9 s: about 11.8 s).
- **Text:** libass with `shaping=complex` from the vendored `studio/fonts/` (Saira Extra Condensed for chips and the
  hook, Noto Sans Devanagari for Hindi). Never FFmpeg `drawtext` for Hindi (it breaks matras).
- **Audio:** none unless the owner gives a song or asks for a bed (`--audio`, faded out over the last 0.6 s, AAC 256k).
- **WhatsApp copy:** `python3 studio/whatsapp_copy.py montage.mp4 montage_whatsapp.mp4`.
- **QC before delivery:** `montage.py check` all OK, then `python3 studio/frame_check.py montage.mp4 --size 1080x1920
  --fps 30 --silent` (drop `--silent` with a song).

## Rules that never bend
- Everything is drawn in code: no images, video models or stock. The same seed gives the same montage.
- Original scenes and characters only. No real vehicles' logos or brand shapes, no named studio, film or artist to
  copy; a style names a medium or a tradition.
- The subject's path lives only in `motion.js`. A style that moves the subject on its own breaks every cut.
- No montage with a failing loop. Ask before overwriting files. Deliver to `projects/<slug>/final/` with
  `studio/deliver.py` (the video, and one zip with the pages, `motion.js`, `plan.json`, `montage.json` and QC).
