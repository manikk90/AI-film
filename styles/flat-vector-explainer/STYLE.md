# Flat Vector Explainer — Style Prompt

> Science explained in clean flat shapes: rounded geometric characters and objects, soft single-direction shading, bright saturated colours on dark or deep-coloured grounds, and the camera zooming between scales (body, cell, molecule; city, house, wire) as the explanation goes deeper.
> References (grammar only): flat-design science explainer channels and infographic animation: geometric construction, rounded corners, one light source, scale-to-scale zooms. Copy no channel's characters (birds, mascots), palettes or layouts.

## 1. Essence, and what it is not

- **Shapes are built from geometry**: circles, rounded rectangles and capsules; every object reads at thumbnail size.
- **Flat colour with one soft shade**: each shape has a base colour plus one darker shadow side and sometimes one highlight, all from one light direction (top-left).
- **Scale travel**: the signature move is zooming from one level of the world into the next, so the explanation is a journey through sizes.
- **Characters are simple and cute**: round bodies, dot eyes, no mouths unless they talk, expressive through pose.

Not Isometric Infographic (strict isometric grid, three-tone blocks). Not Game Show Flat (thick ink outlines, candy stripes). Not Mid-century Cartoon (printed misregistration, limited animation). No outlines at all here.

## 2. Materials & rendering

- **Engine**: Canvas 2D (or SVG drawn to canvas). Shapes as paths with corner radius 8–24 px at 1080 p.
- **Shading**: per shape a base fill, a shadow shape clipped inside it (12–20 % darker, hue shifted toward blue), an optional highlight (white 15 %).
- **Texture**: a very light noise grain (1–2 %) over everything so flat fields are not dead; soft long shadows on the ground at 10 % opacity.
- **Depth**: 3–4 parallax layers; distant layers lighter and less saturated.
- **Particles**: molecules, cells, stars as small circles with subtle glow on dark grounds.

## 3. Colour logic

- **Ground**: deep navy `#1b1f3b` or a single saturated field; foreground objects bright: coral `#ff6b6b`, sunflower `#ffd166`, teal `#06d6a0`, sky `#4cc9f0`, lilac `#9b5de5`.
- One palette per scale level; the zoom changes the palette, which tells the viewer they changed worlds.
- The "bad guy" or problem keeps one colour across all levels (e.g. coral = virus).
- Never: gradients inside objects (except subtle sky gradients), black outlines, photographic textures.

## 4. Type & subtitles

- **Labels**: **Poppins** Bold for headings, **Poppins** Medium for labels, Latin and Devanagari; short labels pop on with a scale bounce next to the object.
- **Subtitles**: **Poppins** SemiBold 40–46 px, white on a dark rounded pill, two lines at most, inside the safe zone.
- Numbers count up when they matter (millions, percentages).

## 5. Motion quality

- 30 fps, smooth easing (ease-in-out cubic), **squash and stretch on characters**, overshoot on pop-ins (back ease, 10 %).
- Objects enter by scaling from 0 at their centre or sliding in with motion trails; never fading alone.
- Constant gentle life: idle bobbing, blinking, rotating particles.
- **Scale zoom**: 1.2–2 s exponential zoom into a small object that becomes the next world.

## 6. Camera grammar

| Move | What it expresses | Can serve |
|---|---|---|
| Exponential zoom into a detail | going deeper | body → cell; city → atom |
| Zoom out to the whole system | the big picture | ecosystem; economy |
| Side-scroll along a process | sequence | digestion; manufacturing |
| Split screen of two worlds | comparison | healthy vs sick; then vs now |

## 7. Sound palette

- **Music**: light orchestral-electronic: `pizzicato_strings`, `marimba`, `celesta`, soft synth pads, gentle percussion; builds at reveals.
- **SFX**: soft pops for appearances, whooshes for zooms, bubbly sounds for cells, small chimes for answers.
- Voice warm and clear; music ducked ~10 dB; master −14 LUFS.

## 8. Native moves

- **Scale dive.** Zoom through three levels to reach the cause. *Fits content like:* why skin itches; how chips work; where rain comes from.
- **Army of tiny helpers.** Hundreds of small characters doing a job. *Fits content like:* immune cells; workers; data packets.
- **Counter mountain.** Units stack into a huge pile while a number counts up. *Fits content like:* plastic waste; population; money.
- **Split timeline.** Two paths side by side diverge. *Fits content like:* habits; decisions; evolution.

## 9. Pitfalls of the medium

- **Copying a famous explainer's look** (bird mascots, signature palettes) → design your own characters and palette.
- **Too many objects** → one idea per shot; dark ground helps focus.
- **Static frames** → keep idle motion on every character.
- **Long text** → let shapes explain; labels of three words at most.

## 10. Engine

No demo engine yet (draft). A first demo should build, on the `studio/render_canvas.cjs` contract:
- `shapes.js`: rounded primitives with inner shadow and highlight, grain overlay.
- `zoom.js`: exponential scale transitions between worlds, palette per level.
- `cast.js`: round characters with blink, bob, squash and stretch, simple walk.
- `labels.js`: pop-on labels, counters with Indian number grouping.

Start from the Lemo-Opuscar `styles/isometric-picture-book/demo/engine.js` (flat-colour scene engine) and Mann's `editor/motion/lib.js` (easing, counters, text fit).

## 11. Variation space

You decide the palette per level, how many scale levels the story needs, and how cute the characters are.

- Structures: **one dive** (outside to inside); **a day in the life** of a cell or a coin; **myth vs fact** pairs.
- Openings: **a big question** on a dark ground; **a zoom from space** to one person.
- Endings: **zoom back out** to the person; **the helpers wave**; **the counter** freezes on the final number.

---

Status: **draft** — no demo film yet. Before this is used as a library style it needs a demo film, `DEMO.md`, stills and the checks in the Lemo-Opuscar `MAINTAINING.md` ("Gates").
