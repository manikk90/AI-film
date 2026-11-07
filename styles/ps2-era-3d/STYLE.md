# PS2-era 3D — Style Prompt

> A story told as an early-2000s console game: low-polygon characters with painted textures, vertex-lit rooms in fog, a soft bloom on every bright light, a slightly blurry 480-line picture, menu screens and a loading bar between scenes.
> References (grammar only): sixth-generation console 3D (around 2000–2005): limited polygon budgets, low-resolution textures, fog to hide draw distance, cutscenes with stiff facial animation, memory-card save screens. Copy no game, character, logo, font or console interface; never use a console maker's marks.

## 1. Essence, and what it is not

- **Low-poly, but not faceted.** Characters are a few thousand triangles with smooth (Gouraud) shading and painted texture detail: faces, folds and dirt live in the texture, not the geometry.
- **Texture resolution is visibly low**: 128–256 px textures on characters, 64–128 px on props, bilinear-filtered so they look soft, never sharp pixel art.
- **The world sits in fog**: distance fades into a coloured fog that matches the sky; the far plane is close.
- **Light is baked**: vertex colours and lightmaps do most of the lighting; one dynamic light; blob shadows under characters.
- **The picture is 480-line video**: rendered around 640 × 448, upscaled with a soft filter, slight interlace shimmer on motion, bloom on bright areas, mild chromatic smear.
- **Game framing**: title screen, menu, loading bar, dialogue boxes, a save prompt; cutscenes with letterbox bars.

Not Pixel RPG (2D sprites, hard pixels). Not Low-poly Isometric Island (flat-shaded facets, clean modern render). Not a PS1 look (no affine texture warping or vertex jitter here: those belong to the previous generation). Not modern photoreal.

## 2. Materials & rendering

- **Engine**: three.js (vendored from npm, not a CDN). Render to a 640 × 448 (4:3) or 448 × 800 (9:16) target, then upscale with linear filtering and a 0.6 px blur.
- **Materials**: `MeshLambertMaterial` with vertex colours and a diffuse texture; specular only on wet or metal surfaces, as a matcap.
- **Textures**: generated or painted at low resolution; `LinearFilter`, mipmaps on; colour depth reduced to 16-bit (5-6-5) with a 2×2 ordered dither.
- **Fog**: `THREE.Fog` with near 15–30 m and far 60–120 m, colour equal to the sky gradient's horizon.
- **Lighting**: hemisphere ambient + one directional light; blob shadow decals; lightmapped rooms.
- **Post**: bloom (threshold high, radius large, strength 0.4–0.7), slight bloom bleed on white UI, 1-line interlace offset on fast motion, film grain 2 %.
- **Characters**: rigged with ~20 bones; faces with 3–5 blend shapes (blink, mouth open, smile); hair as textured cards.

## 3. Colour logic

- Slightly desaturated, with a cool-blue or warm-sepia cast per level; skies as gradient domes.
- Night scenes lean teal with orange street lights; day scenes lean pale cyan with a warm sun.
- UI colours: one bright accent (cyan or gold) on dark translucent panels.
- Never: deep HDR contrast, physically based reflections, pure black shadows.

## 4. Type & subtitles

- **Game UI type**: **Rajdhani** SemiBold for menus and HUD (Latin and Devanagari), in caps for menu items, with a 1 px bevel and a soft glow; dialogue in a translucent box at the bottom with a speaker name tag.
- **Subtitles** are dialogue boxes: two lines at most, text that types on at 30–45 characters per second with a small blip per character, a blinking "next" arrow when done.
- Loading and save screens use small caps and a progress bar.

## 5. Motion quality

- Gameplay at 30 fps; cutscenes at 30 fps with **stiff, slightly floaty animation**: idle loops, canned gestures, mouths that open and close rather than lip-sync exactly.
- Characters walk on fixed cycles and turn on the spot; collisions are simple.
- Camera moves are smooth splines (cutscenes) or a chase camera with a little lag (gameplay).
- Scene changes: fade to black, loading screen 1.5–3 s with a tip line, fade in.

## 6. Camera grammar

| Move | What it expresses | Can serve |
|---|---|---|
| Chase camera behind the hero | play, agency | a journey; a commute; a mission |
| Cutscene two-shot with letterbox | story, dialogue | a conversation; a reveal |
| Slow orbit around a character | the hero moment | an introduction; a victory |
| Fixed security-cam angle | survival-horror tension | a mystery; a scary place |
| Menu screen with a turning model | choice, stats | a comparison; a "character select" of options |

## 7. Sound palette

- **Music**: early-2000s game score palette: sampled orchestra hits, `strings_ensemble`, `choir_aah`, breakbeat loops, `synth_brass`, trance arps for action; loops that restart cleanly.
- **UI sounds**: menu cursor blips, a confirm chime, a save "shimmer", a loading hum.
- **Foley**: footsteps per surface, cloth swishes, simple impacts; ambience loops per level.
- **Voice**: slightly compressed and band-limited (80 Hz–10 kHz) like game voice acting; music ducked ~10 dB; master −14 LUFS.

## 8. Native moves

- **Character select.** Options shown as playable characters with stat bars. *Fits content like:* comparing phones; career paths; choices.
- **Loading tip.** A loading screen with one fact. *Fits content like:* a fact between chapters; a joke; a teaser.
- **Save point.** The story pauses to save. *Fits content like:* a milestone; a cliffhanger; an ending.
- **Quest log.** A menu lists objectives that tick off. *Fits content like:* steps of a process; a to-do; a recipe.

## 9. Pitfalls of the medium

- **Too clean** reads as a modern indie game → low-res textures, fog, bloom, upscale blur.
- **PS1 wobble** is the wrong generation → no affine warping, no vertex snapping.
- **Using real game or console assets, fonts or logos** → invent everything; never imitate a specific game's UI.
- **Unreadable UI on phones** → menu text at least 3 % of the frame height, inside the safe zone.

## 10. Engine

No demo engine yet (draft). A first demo should build a three.js page on the `studio/render_canvas.cjs` contract (WebGL canvas with `preserveDrawingBuffer: true`; `FILM.render(ctx, t)` sets the scene time and calls `renderer.render`):
- `lowres.js`: render target at 640 × 448 / 448 × 800, upscale pass, 5-6-5 dither, interlace offset, bloom.
- `ps2mat.js`: Lambert + vertex colour + low-res texture factory, matcap specular, fog.
- `rig.js`: simple bone rig, canned idle/walk/gesture clips, blink and mouth-open blend shapes.
- `ui.js`: menus, dialogue boxes with type-on, loading bar, save prompt.

Start from the Lemo-Opuscar `styles/pixel-rpg/demo/ui.js` (game UI states) and `styles/lowpoly-island/demo/post.js` (post chain). Vendor three.js with `npm pack three@0.170.0`.

## 11. Variation space

You decide the era tint (blue night city, sepia desert, green forest), how much is gameplay versus cutscene, and how much game UI frames the story.

- Structures: **a level** (start, obstacle, boss, save); **a cutscene** with dialogue choices; **a character select** of options.
- Openings: **a title screen** with "Press Start"; **a loading screen** with a tip.
- Endings: **save complete**; **credits roll** over the level; **"Continue?"** with a countdown.

---

Status: **draft** — no demo film yet. Before this is used as a library style it needs a demo film, `DEMO.md`, stills and the checks in the Lemo-Opuscar `MAINTAINING.md` ("Gates").
