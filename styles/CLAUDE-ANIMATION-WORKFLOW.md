# Claude animation styles: workflow

The owner shared two reels of "10 Claude animation styles" (2026-11-07). Between them they list 16 styles. Nine already exist in the studio's libraries; seven were added here as draft styles. This page says where each one lives, how a film in any of them is made in this repo, and gives a starting prompt for each.

Everything here is drawn in code (Canvas 2D or three.js) and rendered locally with headless Chromium and FFmpeg, so it runs in the cloud session and on the laptop. No image or video model is involved.

## 1. Where each style lives

| Reel name | Style | Where | Engine | Status |
|---|---|---|---|---|
| Pixel Art | `pixel-rpg` (16-bit Pixel RPG) | Lemo-Opuscar library | Canvas 2D | has a demo film |
| ChalkBoard Style | `chalkboard` | Lemo-Opuscar library | Canvas 2D | has a demo film |
| Glow Sketch | [`glow-sketch`](glow-sketch/STYLE.md) | AI-film draft (new) | Canvas 2D | draft |
| PS2 Style | [`ps2-era-3d`](ps2-era-3d/STYLE.md) | AI-film draft (new) | three.js | draft (pipeline test rendered) |
| Comic Art | `/comic-reel`, `comic-book`; [`manga-screentone`](manga-screentone/STYLE.md); `halftone-dossier` | imported format / AI-film draft / Lemo | Canvas 2D | format ready; drafts |
| Flat Vector | [`flat-vector-explainer`](flat-vector-explainer/STYLE.md) | AI-film draft (new) | Canvas 2D | draft |
| Dan Koe Style | [`minimal-ink-essay`](minimal-ink-essay/STYLE.md) | AI-film draft (new) | Canvas 2D | draft; check against a reference first |
| CGI Motion | [`cgi-motion`](cgi-motion/STYLE.md) | AI-film draft (new) | three.js | draft |
| Lego Style | `brick-toy` | Lemo-Opuscar library | three.js | has a demo film |
| ZackD Films | [`what-if-3d-explainer`](what-if-3d-explainer/STYLE.md) | AI-film draft (new) | three.js | draft |
| Claymation | [`claymation`](claymation/STYLE.md); `claymation-stop-motion` | AI-film draft / imported format | three.js | draft |
| Paper Cutout | `paper-popup`, `papercut-red`; [`collage-cutout`](collage-cutout/STYLE.md); `paper-cut-out` | Lemo / AI-film draft / imported format | Canvas 2D / three.js | demo films for the Lemo ones |
| Retro Anime | `cel-anime-80s`; `anime-opening` | Lemo / imported format | Canvas 2D | has a demo film |
| Low Poly 3D | `lowpoly-island` | Lemo-Opuscar library | three.js | has a demo film |
| Risograph | `risograph` | Lemo-Opuscar library | Canvas 2D | has a demo film |
| Miniature Diorama | [`miniature-diorama`](miniature-diorama/STYLE.md); `tilt-shift`, `memphis-diorama` | AI-film draft (new) / Lemo | three.js | draft |

Library styles with a demo film are the fast, reliable picks. Draft styles need their engine built first (each `STYLE.md` §10 lists what to build), so plan more time and show the owner a style frame before the full film.

Names of creators (Dan Koe, ZackD Films) are kept only as the owner's labels for the genre. The films copy no creator's drawings, models, scenes, wording, voice or branding, and never imply endorsement.

## 2. Making a film in one of these styles

The studio's gates apply unchanged: the owner approves the script (Gate 2) and the look (Gate 3) before full production.

1. **Topic and script.** Through `/viral-studio`: research (`FACTS.md` for any body or science claim), writer, critique, owner approval. The approved words are locked.
2. **Pick the style.** The director's format brief recommends one style from the table plus one `experiment`; the owner decides.
3. **Build the page.** One HTML page per film that follows the `studio/render_canvas.cjs` contract:
   - `window.FILM = { DUR, init(), render(ctx, t) }` draws the frame at time `t` (seconds). Every frame must be a pure function of `t`: seeded randomness only, no `Date` or unseeded `Math.random`.
   - Set `window.READY = true` once fonts and assets are loaded.
   - three.js styles draw on the page's first `<canvas>` with `preserveDrawingBuffer: true` and ignore `ctx`.
4. **Style frame (Gate 3).** Three stills at three timecodes (the hook, the turn, the ending), plus the music sketch:
   `node studio/render_canvas.cjs film.html stills/frame --size 1080x1920 --stills 1,6.5,11`
   Send them as separate numbered images. Stop until the owner approves.
5. **Render the picture.**
   `node studio/render_canvas.cjs film.html film.mp4 --size 1080x1920 --fps 30 --audio voice.mp3`
6. **Finish with Mann.** Ingest the render into an edit folder and let Mann add what the style asks for:
   - animated captions (`subtitles.animate`: `pop` or `highlight` for the explainer styles)
   - motion templates (step tags, counters, lower thirds)
   - music and SFX on the beat grid, the −14 LUFS master and QC

   Mann's storyboard approval still applies.
7. **Deliver.** `python3 studio/deliver.py`: the final video plus one zip of the rest.

### Engine notes

- **three.js**: vendor it from npm, never a CDN.
  ```
  npm pack three@0.158.0 && tar xzf three-0.158.0.tgz && cp package/build/three.min.js <film>/vendor/
  ```
  Use the UMD build (`three.min.js`, global `THREE`) with a plain `<script src>`. Releases from r160 on ship no UMD build, and ES-module imports from `file://` pages are blocked by Chromium. This was verified on 2026-11-07: a three.js r158 scene rendered through `studio/render_canvas.cjs` in this cloud session.
- **Light intensities**: since r155 three.js uses physical light units by default, so values copied from old tutorials render dark. Raise intensities (about ×π), or tune them on the style frame.
- **Low-resolution looks** (PS2, pixel): render to a small `WebGLRenderTarget` or offscreen canvas, then upscale with the filter the style asks for.
- **Fonts**: install them with `python3 -m aifilm.editor fonts-install --pairing <id>`. Load them with `@font-face` from the installed files and wait on `document.fonts.ready` before `READY`. Devanagari shapes correctly in Chromium.
- **Speed**: render the three stills first. A full 30–45 s film at 1080 × 1920 renders one frame at a time, so 3D styles take minutes.

## 3. Starting prompts

Give Claude the prompt with the approved script and the style's `STYLE.md`. Each prompt asks for a style frame first, not the whole film.

- **Pixel Art** (`pixel-rpg`): "Build a 16-bit RPG page at 320×180 upscaled ×6 for this script: limited indexed palette, tile map, sprite hero, dialogue boxes, save screen ending. Follow the Lemo `pixel-rpg` STYLE.md and its demo engine. Render 3 stills at 1 s, 6.5 s and 11 s."
- **ChalkBoard** (`chalkboard`): "Chalk writes this script's key lines on a real blackboard, in true stroke order, with no hand. Diagrams draw themselves, and wipes leave ghosts. Use the Lemo `chalkboard` engine."
- **Glow Sketch** (`glow-sketch`): "Near-black paper. One glowing pen draws each idea stroke by stroke: white core, a cyan halo for the system, amber for the answer. The pen tip leads every stroke, and old strokes dim as the story moves on."
- **PS2 Style** (`ps2-era-3d`): "Tell this story as a 2002 console cutscene in three.js. Render at 448×800 and upscale soft, with fog, vertex-lit low-poly characters, bloom on lights and a 5-6-5 dither. Add a title screen, dialogue boxes that type on, a loading tip between scenes and a save prompt at the end."
- **Comic Art** (`/comic-reel` or `manga-screentone`): "Retell this scene as comic panels: halftone dots, speed lines, onomatopoeia bursts, speech bubbles for every line, and panels that slide in on the beat."
- **Flat Vector** (`flat-vector-explainer`): "Explain this script in rounded flat shapes on deep navy. Use one soft shade per shape, no outlines, cute round characters, and one exponential zoom per level (body → cell → molecule). Counters use Indian digit grouping."
- **Dan Koe Style** (`minimal-ink-essay`): "A calm essay on black paper: one white brush-ink figure or symbol per idea, a serif statement card for each key line, one muted gold accent word, long holds and silences. Sparse piano."
- **CGI Motion** (`cgi-motion`): "A pastel cyclorama studio in three.js: a soft rubber ball, frosted glass blocks and satin cloth play a chain reaction. Every contact lands on the beat, and the last frame loops into the first."
- **Lego Style** (`brick-toy`): "Shoot this story as a stop-motion brick-toy film on a real desk, with macro lens, studded bricks and minifigure-style actors of our own design (no trademarks). Use the Lemo `brick-toy` engine."
- **ZackD Films** (`what-if-3d-explainer`): "Explain this fact as a 3D macro dive into the body. Number the steps with a 'STEP n' tag, put bold white and yellow outlined captions in the upper-middle third (Mann `pop` captions), and end on a 'that's why…' payoff. Every claim comes from FACTS.md."
- **Claymation** (`claymation`): "Clay characters with fingerprints, boil on twos, replacement mouths, a miniature set and macro DOF. One lump becomes each object in turn."
- **Paper Cutout** (`paper-popup` / `collage-cutout`): "A pop-up book on a desk: flat cut-paper actors with white borders, paper sets that fold up as the page turns, and soft shadows between the layers."
- **Retro Anime** (`cel-anime-80s`): "An 80s cel-anime treatment: two-tone cels over airbrushed backgrounds, speed lines, a dramatic sky and a title-card ending. Use the Lemo engine."
- **Low Poly 3D** (`lowpoly-island`): "A faceted low-poly world under an orthographic isometric camera. Tiles grow one per beat, flat-shaded with soft fog."
- **Risograph** (`risograph`): "Print this story in two or three translucent spot inks on warm paper, with misregistration, grain and each scene adding an ink."
- **Miniature Diorama** (`miniature-diorama`): "A hand-built model village on a real wooden table in three.js, with sponge trees, painted houses and macro DOF. A real glass of chai at the edge of frame gives away the scale, and the film ends on the scale reveal."
