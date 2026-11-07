# Miniature Diorama — Style Prompt

> A tiny hand-built world sitting on a real table: a model village or city on a wooden base, foam trees, painted houses and little figures, shot with a macro lens, while real everyday objects (a cup of chai, a pencil, a phone) at the edge of the frame give away the scale.
> References (grammar only): model-railway layouts, architectural maquettes and toy dioramas photographed close-up; the owner's reel shows a cartoon village on a wooden table beside a real glass of chai. Copy no studio's or artist's dioramas, characters or brands.

## 1. Essence, and what it is not

- **A built object**: the world ends at the edges of a base board; you can see its cut sides, layered soil and the table below.
- **Toy materials**: matte painted wood and plaster, flocked grass, sponge trees, plastic figures with simple faces, cotton-wool clouds on wires.
- **Real-world scale cues**: one or two real objects on the table, in focus or softly out of focus, larger than the buildings.
- **Macro photography**: shallow depth of field, warm window light, everything looks small because of focus and light.

Not Tilt-shift Miniature (a real photoreal place faked as small; here the place is a model). Not Memphis Diorama (paper-built Memphis-pattern models). Not Brick Toy (no bricks or studs). Not Claymation (rigid painted materials, no clay boil).

## 2. Materials & rendering

- **Engine**: three.js (vendored), PBR with matte materials: painted wood (roughness 0.8), flock grass (instanced cards with a fuzzy texture), sponge trees (noise-displaced spheres with a porous normal map), plastic figures (roughness 0.5, slight sheen).
- **Base board**: a rounded rectangle slab with exposed cut sides showing soil layers and a wooden plinth; the table below as a real wood texture.
- **Real props**: one hero real object (a glass of chai with liquid and steam, a pencil, a ceramic cup) rendered photoreal to contrast the toy world.
- **Lighting**: warm window key from one side, soft fill, small practical lights inside houses at dusk.
- **Camera**: physical DOF with focal length 60–100 mm equivalent at macro distance; narrow focus band; slight lens vignette.
- **Motion of figures**: stop-motion stepping (12 fps) or smooth toy motion on rails; clouds bob on visible wires.

## 3. Colour logic

- Toy-saturated buildings (red `#e4572e`, yellow `#f2c14e`, blue `#4d8fd6`, peach `#f4a582`) on fresh grass `#5bb04a`; the real table in warm brown `#8a5a35`.
- Warm afternoon light; dusk version with orange windows and a blue sky card.
- The real object keeps its real colours, slightly less saturated than the toy world.

## 4. Type & subtitles

- **Signs inside the diorama** are painted on tiny boards or flags; titles appear as a printed card leaning against the base or as a label on the plinth.
- **Subtitles**: **Baloo 2** SemiBold 40–44 px (Latin and Devanagari), cream with a soft dark outline, inside the safe zone.

## 5. Motion quality

- 24 fps; figures on twos (stop-motion feel) or smooth rail motion for vehicles; real objects move rarely and slowly (steam rising, a hand placing a cup).
- Camera: slow macro dolly and push-ins on ones; rack focus between the toy world and the real object.
- Time of day can change by sliding lights, like a studio light rig.

## 6. Camera grammar

| Move | What it expresses | Can serve |
|---|---|---|
| Wide of the whole base on the table | the world is small | introductions; a place |
| Macro push into a street | intimacy | a character; a shop |
| Rack focus to the real object | the outside world | scale reveal; humour |
| Top-down over the base | planning | a map; a route |
| A real hand enters | the maker, fate | change; a correction |

## 7. Sound palette

- **Music**: gentle acoustic (`ukulele`, `glockenspiel`, `accordion`, soft `upright` piano), music-box textures.
- **SFX**: tiny town sounds pitched up and quieter (bells, bicycles, birds), plastic clicks for figures, a real-room ambience (a clock, a distant kitchen).
- Voice warm, storybook; music ducked ~10 dB; master −14 LUFS.

## 8. Native moves

- **Scale reveal.** Pull out to show the table and the giant cup. *Fits content like:* humour; "it's all in your head"; small business vs world.
- **The maker's hand.** A real hand places a new building. *Fits content like:* growth; building a business; city planning.
- **Day to night.** The light rig slides from sun to dusk, windows glow. *Fits content like:* a day in a life; time passing.
- **Diorama map.** Top-down route with a tiny vehicle. *Fits content like:* a journey; logistics; directions.

## 9. Pitfalls of the medium

- **Looks like a game level** → show the base edges, the table and a real object.
- **Too sharp everywhere** → narrow focus; macro DOF is what makes it small.
- **Real object too dominant** → one real object, at the edge, partly out of focus.
- **Copying a known diorama artist** → original layouts and figures.

## 10. Engine

No demo engine yet (draft). A first demo should build a three.js page on the `studio/render_canvas.cjs` contract:
- `base.js`: base board with cut-soil sides, plinth, table, scale props.
- `kit.js`: houses, sponge trees, flock grass (instanced), figures, vehicles on rails, clouds on wires.
- `macro.js`: physical DOF, rack focus, window-light rig, day-to-night slider.
- `stepper.js`: twos stepping for figures, smooth rails for vehicles.

Start from the Lemo-Opuscar `styles/tilt-shift/demo/post.js` (miniature DOF), `styles/memphis-diorama/demo/main.js` (tabletop model framing) and `styles/brick-toy/demo/set.js` (real tabletop scale and light).

## 11. Variation space

You decide the place (village, city block, market, campus), the real object, toy style (wood, plastic, plaster) and whether a hand appears.

- Structures: **a day in the tiny town**; **a journey across the board**; **the town grows** piece by piece.
- Openings: **a macro street shot** that pulls out to the table; **an empty base** and a hand placing the first house.
- Endings: **scale reveal** with the real object; **lights out** at night; **the hand** places the last figure.

---

Status: **draft** — no demo film yet. Before this is used as a library style it needs a demo film, `DEMO.md`, stills and the checks in the Lemo-Opuscar `MAINTAINING.md` ("Gates").
