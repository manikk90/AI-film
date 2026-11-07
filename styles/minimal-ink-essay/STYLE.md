# Minimal Ink Essay — Style Prompt

> A spoken essay drawn in very few lines: sparse white ink figures and symbols appear on black (or off-white) paper, one stroke per idea, with large calm serif statements and long silences. The voice carries the argument; the drawing gives each idea one image.
> References (grammar only): the owner listed this as "Dan Koe style" from a reel of Claude-made animation styles. The grammar here is a draft built from the minimalist essay-video genre (sparse sketches, monochrome, statement text). Check it against a real reference with `/mann-style-lab` before use, and copy no creator's drawings, wording, branding or thumbnails.

## 1. Essence, and what it is not

- **Almost empty frames.** At most one figure, one symbol and one line of text on screen.
- **Ink, not vector.** Lines are brush-pen strokes with pressure, slightly dry at the ends; figures are stick-like or gesture sketches, faceless or with minimal features.
- **Monochrome with one exception.** White on black (or black on warm off-white); a single accent colour appears only on the key word or object of the essay.
- **Statements, not captions.** The key sentence of each beat is set large in a serif, centred, and held.
- **Calm pacing.** Long holds, slow draw-ons, silence between ideas.

Not Glow Sketch (no glow, no neon). Not One-line Drawing (several strokes, no single continuous line). Not Whiteboard Explainer (no hand, no marker, no busy diagrams). Not Dark Keynote (no slides or product imagery).

## 2. Materials & rendering

- **Engine**: Canvas 2D. Strokes from hand-authored paths rendered with a variable-width brush (pressure from path speed), dry-brush breaks at stroke ends (alpha noise), slight ink bleed (1 px blur on edges).
- **Paper**: black `#0b0b0b` with faint grain, or off-white `#f1ede4` with fibre texture; a soft vignette.
- **Figures**: a small library of gesture figures (standing, walking, climbing, sitting at a desk, carrying a weight), mountains, doors, ladders, arrows, a sun, a clock: the visual vocabulary of self-improvement metaphors.
- **Transitions**: ink fades out like drying (contrast drops), or the paper slides like a page turn.

## 3. Colour logic

- Two values only: paper and ink.
- **One accent** for the whole film: muted gold `#c9a227` or terracotta `#c65d3b`; used on one word or one object per beat.
- Never: gradients, multiple colours, photographs, glow.

## 4. Type & subtitles

- **Statements**: **Tiro Devanagari Hindi** (Latin and Devanagari serif) 64–96 px, centred, sentence case, line length ≤ 22 characters on 9:16; fade in over 0.6 s, hold until the voice finishes plus 1 s.
- **Subtitles** (for the rest of the speech): **Hind** Medium 38–42 px, low contrast grey `#bdbdbd` on black, two lines at most.
- The accent colour marks one word in a statement.

## 5. Motion quality

- 24 or 30 fps; a figure draws in over 1–2 s with ease-out; holds of 2–4 s are normal.
- Movement is minimal: a figure takes one step, a door opens, a weight drops.
- Camera is static; occasionally a very slow push-in (2–4 % over a beat).

## 6. Camera grammar

| Move | What it expresses | Can serve |
|---|---|---|
| Static centred figure | the reader is that figure | identity; choice |
| Slow push-in | intensity, focus | the turn; the core claim |
| Wide empty frame with a tiny figure | scale, loneliness | ambition; difficulty |
| Hard cut to a statement on blank paper | emphasis | the thesis; the takeaway |

## 7. Sound palette

- **Music**: sparse piano (`upright` soft, felt), low drones, occasional cello; long reverb; tempo free.
- **SFX**: brush-on-paper strokes, a page turn, a faint room tone; no whooshes.
- **Silence**: deliberate pauses of 0.8–1.5 s before key statements (mark them as `deliberate_silences` in Mann's EDL).
- Voice close, warm, unhurried; music ducked ~12 dB; master −14 LUFS.

## 8. Native moves

- **The climb.** A figure climbs a staircase that keeps drawing itself. *Fits content like:* consistency; compounding; growth.
- **Two doors.** A figure stands between two doors. *Fits content like:* choices; risk; comfort vs growth.
- **The weight.** A figure carries a block that grows or drops. *Fits content like:* burdens; distraction; letting go.
- **Statement card.** Blank paper, one sentence, held. *Fits content like:* the thesis; a quote; the ending.

## 9. Pitfalls of the medium

- **Too many drawings per beat** → one image per idea.
- **Busy subtitles fighting statements** → hide subtitles while a statement is on screen.
- **Copying a known creator's sketches, phrasing or branding** → original metaphors and wording; never imply endorsement.
- **Monotony over long videos** → change scale, alternate statement cards and drawings, and use silence.

## 10. Engine

No demo engine yet (draft). A first demo should build, on the `studio/render_canvas.cjs` contract:
- `brush.js`: pressure-width ink strokes, dry-brush ends, bleed.
- `figures.js`: the gesture-figure and symbol vocabulary as authored paths.
- `statements.js`: serif statement layout with one accent word.
- `essay.js`: beats from the voice-over timings (Mann's word timings), with holds and silences.

Start from the Lemo-Opuscar `styles/one-line/demo/ink.js` (pressure ink) and `styles/ink-wash` (paper and brush feel).

## 11. Variation space

You decide black or off-white paper, the accent colour, how literal the metaphors are, and the length (60 s short or 8–12 min essay).

- Structures: **thesis, three reasons, takeaway**; **a parable** told with one figure; **mistake → lesson** pairs.
- Openings: **a single statement** in silence; **a tiny figure** in a huge empty frame.
- Endings: **the statement card**; **the figure walks out of frame**; **the ink dries** to blank paper.

---

Status: **draft** — no demo film yet. Before this is used as a library style it needs a demo film, `DEMO.md`, stills and the checks in the Lemo-Opuscar `MAINTAINING.md` ("Gates").
