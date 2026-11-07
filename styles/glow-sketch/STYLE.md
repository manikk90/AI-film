# Glow Sketch — Style Prompt

> Hand-drawn line art that emits light: a single pen draws white and coloured strokes on near-black paper, every stroke blooms like a neon tube or a light-painting trail, and the drawing builds the explanation one line at a time.
> References (grammar only): light-painting photography (a moving light source traced by a long exposure), neon sign bending, glowing sketch explainers on social video. Copy no creator's drawings, characters or captions.

## 1. Essence, and what it is not

- **The line is the light source.** Strokes are drawn live, in stroke order, and each one glows: a hot white core, a coloured halo, and a soft bloom that lights the dark paper around it.
- **Dark ground, few lines.** The frame is mostly near-black; meaning comes from what has been drawn so far, so composition is built by adding lines, never by revealing a finished picture.
- **Sketch, not vector.** Lines wobble, overshoot and taper like a fast marker; corners are drawn, not mitred.
- **Light behaves physically.** New strokes are brightest, then settle; crossing lines add up; the glow dims when the idea moves on.

Not Vector Arcade (CRT vector monitor, rigid geometry, no hand). Not Chalkboard (opaque dusty chalk on slate, no emission). Not One-line Drawing (one unbroken line; here many separate strokes). Not neon-outline footage effects (this is a drawn world, not an outline around a filmed person).

## 2. Materials & rendering

- **Engine**: Canvas 2D (or WebGL for heavy bloom). Strokes are polylines sampled from hand-authored paths with a seeded wobble (±1.5 px at 1080 p, low-frequency) and pressure taper at both ends.
- **Glow stack per stroke**: (1) core line 2–3 px, near-white tinted toward the stroke colour; (2) halo: same path, 10–16 px wide, colour at 35 % alpha with `shadowBlur` 18–30; (3) bloom: a downsampled blurred copy of the whole stroke layer added back with `lighter` composite at 40–60 %.
- **Draw-on**: each stroke animates its length with an ease-out; a bright "pen tip" dot (8 px, white, extra bloom) leads the stroke.
- **Decay**: a stroke's brightness drops from 1.0 to 0.65 over 1.2 s after it finishes; an "active" idea can be re-lit to 1.0.
- **Paper**: near-black with a faint fibre noise (2–3 % luminance), a slight vignette; never pure #000.
- **Lens**: a faint chromatic fringe on the brightest strokes and a whisper of film grain; no lens flares.

## 3. Colour logic

- Background `#07080c` to `#0d0f16`.
- **Two working colours plus white**: one cool (cyan `#5ce1ff` or electric blue `#4d7cff`), one warm (amber `#ffb347` or magenta `#ff4fa3`), and a white core for every stroke.
- **Meaning by colour**: cool for the system, structure or "before"; warm for the change, the danger or the answer. Keep the mapping for the whole film.
- The accent warm colour appears only on the key idea of each beat.
- Never: rainbow strokes, gradients along a single line, coloured backgrounds.

## 4. Type & subtitles

- **Handwritten labels** are drawn as strokes with the same glow (single-line handwriting, written in stroke order). Latin: a single-stroke script built from a font's centre lines; Devanagari: written stroke by stroke with the shirorekha drawn last, never letter-spaced.
- **Subtitles**: screen-space, **Poppins** SemiBold (Latin and Devanagari) 40–46 px at 1080 × 1920, off-white `#f2f4f8` without glow, a soft dark backing, inside the 9:16 safe zone; two lines at most.
- Numbers that matter are drawn bigger and in the warm colour.

## 5. Motion quality

- 30 fps, drawing on ones; a stroke of 300 px takes 0.35–0.6 s, faster as the film warms up.
- **Rhythm from drawing**: one beat = one to three strokes; sentences end on a completed shape.
- Camera movement is rare; when ideas grow, the whole drawing scales down slowly (a pull-back) to make room.
- **Transitions**: the drawing fades to embers (brightness to 10 %, then out) while the pen starts the next idea; or one stroke from the old drawing is kept and becomes the first stroke of the next.
- Never: elements that appear without being drawn, bouncy UI easing, particles that are not light.

## 6. Camera grammar

| Move | What it expresses | Can serve |
|---|---|---|
| Static frame, drawing builds | thinking out loud | a process; a definition; a diagram |
| Slow pull-back as the drawing grows | the bigger picture | a system; a timeline; consequences |
| Push into one stroke until it fills the frame | focus | the key number; the cause |
| Pan along a long line | travel, sequence | a journey; a supply chain; a history |

Framing: keep the active stroke in the centre two-thirds; leave dark space for what comes next.

## 7. Sound palette

- **Music**: soft synth pads and pulses (`pad_warm`, `arp_soft`), a slow kick on scene changes; 70–100 BPM.
- **Pen foley**: a light electrical hiss while drawing (band-passed noise following stroke speed), a small "tick" when a stroke ends, a low hum that rises with total brightness.
- **Silence**: before the key reveal, the hum drops out and only the pen hiss remains.
- Voice close and dry; music ducked ~10 dB under voice; master −14 LUFS.

## 8. Native moves

- **Light the path.** A stroke runs along a chain of drawn nodes, lighting each one. *Fits content like:* a signal through a network; a habit loop; a supply chain.
- **Overload.** Strokes stack until the bloom saturates, then the frame dims. *Fits content like:* burnout; information overload; a short circuit.
- **Before / after colour.** The same drawing is redrawn from cool to warm. *Fits content like:* a change in mindset; a fix; a transformation.
- **The ember.** Everything fades except one glowing stroke. *Fits content like:* the takeaway; a memory; a closing thought.

## 9. Pitfalls of the medium

- **Too much glow** turns into fog → keep the core sharp; bloom ≤ 60 %.
- **Clean vector lines** read as a template → wobble and taper every stroke.
- **Many colours** lose the meaning → two colours plus white.
- **Text over a busy drawing** is unreadable → subtitles on a dark backing, inside the safe zone.
- **Elements popping in** break the rule that light is drawn → everything is drawn.

## 10. Engine

No demo engine yet (draft). A first demo should build, as a page that follows the `studio/render_canvas.cjs` contract (`window.FILM = { DUR, init(), render(ctx, t) }`):
- `strokes.js`: seeded wobble, pressure taper, draw-on by length, pen tip, decay and re-light.
- `glow.js`: core + halo + bloom stack with an offscreen downsampled blur layer.
- `write.js`: single-line handwriting from font centre lines (Latin) and stroke-order Devanagari.
- `story.js`: beats as lists of strokes with timings from the voice-over word timings.

Start from the Lemo-Opuscar `styles/one-line/demo/ink.js` (drawn lines with pressure) and `styles/whiteboard` (stroke-order writing). Render with `node studio/render_canvas.cjs page.html out.mp4 --size 1080x1920`.

## 11. Variation space

You decide the two colours, how much of the frame the drawing fills, whether one drawing grows for the whole film or each beat clears, and how fast the pen moves.

- Structures: **one diagram** that grows to a complete system; **five sketches** for five reasons; **a timeline** drawn left to right.
- Openings: **a single dot of light** that becomes the first stroke; **a question written** in glowing handwriting.
- Endings: **the ember** of one stroke; **the full drawing** pulled back to a constellation.

---

Status: **draft** — no demo film yet. Before this is used as a library style it needs a demo film, `DEMO.md`, stills and the checks in the Lemo-Opuscar `MAINTAINING.md` ("Gates").
