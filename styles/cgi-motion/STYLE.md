# CGI Motion — Style Prompt

> Glossy, tactile 3D motion design: soft-body balls, inflatable shapes, cloth and ramps in a seamless pastel studio, lit by big soft lights, moving in satisfying loops where every contact lands on the beat.
> References (grammar only): "satisfying" 3D loops and abstract motion-design reels made in 3D tools (soft bodies, cloth simulation, physics chains, studio cyclorama lighting). Copy no studio's or artist's specific scenes, brands or signature objects.

## 1. Essence, and what it is not

- **Materials you want to touch**: soft rubber, frosted glass, matte clay-like plastic, satin cloth, chrome accents.
- **Physics that feels right**: bounces with squash, cloth that drapes, chains that ripple; slightly slower than reality for satisfaction.
- **A seamless studio**: an infinite curved backdrop (cyclorama) in one pastel colour, soft contact shadows, no horizon line.
- **Loops and rhythm**: actions repeat or flow into each other; contacts sync with the music.

Not Glass Product Render (a real product hero; here abstract objects and play). Not Claymation (no fingerprints or boil; clean CG surfaces are the point). Not Low-poly (smooth, high-subdivision surfaces).

## 2. Materials & rendering

- **Engine**: three.js with `MeshPhysicalMaterial` (vendored from npm): soft rubber (roughness 0.45, sheen 0.3), frosted glass (transmission 0.9, roughness 0.35, thickness 0.5), satin cloth (sheen 0.6), chrome (metalness 1, roughness 0.15) for small accents.
- **Lighting**: a large soft key (RectAreaLight 4 × 2 m), a fill, a top rim; environment from a generated studio HDRI (gradient + softboxes); ACES tone mapping.
- **Shadows**: soft contact shadows (PCSS or baked AO on the backdrop), GTAO for crevices.
- **Simulation**: pre-baked per frame in JS (verlet for cloth and soft bodies, rigid body for balls and blocks), deterministic with a seed so renders match.
- **Post**: subtle DOF, bloom on chrome highlights only, very light grain.

## 3. Colour logic

- **Backdrop pastel**: peach `#ffd6c2`, mint `#c9f2e3`, lavender `#d9d2ff` or butter `#fff1b8`; objects one step more saturated in two or three complementary colours.
- One "hero" object in the strongest colour; supporting objects quieter.
- Colour can shift per section of the music (a palette change on the drop).
- Never: dark gritty scenes, more than four object colours, brand logos.

## 4. Type & subtitles

- **3D type**: **Baloo 2** ExtraBold extruded with rounded bevels and the same rubber or glass material; letters can bounce, inflate or be pushed by objects.
- **Subtitles**: **Poppins** SemiBold 40–44 px, dark grey on a white rounded pill, inside the safe zone.

## 5. Motion quality

- 30 or 60 fps; physics on ones; camera on smooth splines.
- **Anticipation and overshoot** on every action; soft-body squash 10–25 % on impact.
- Loops: the last frame matches the first for seamless repeats (essential for Reels).
- Timing locks to the music grid: contacts on beats, big moves on downbeats (Mann's `beats` gives the grid).

## 6. Camera grammar

| Move | What it expresses | Can serve |
|---|---|---|
| Slow orbit around the action | admiration | a hero object; a reveal |
| Locked close-up on a contact | satisfaction | a press; a squish; a click |
| Top-down on a run of objects | process, flow | a chain reaction; steps |
| Dolly follow of a rolling object | journey | a path; a process; a story |

## 7. Sound palette

- **Music**: clean electronic or lo-fi house, 100–124 BPM, with bright plucks (`pluck_synth`), soft kicks, claps on contacts.
- **Foley of materials**: rubber squeaks and bounces, glass clinks, cloth swishes, soft pops for inflation, a satisfying "thock" for blocks; each synced to contact frames.
- Voice optional; when present, music ducked ~10 dB; master −14 LUFS.

## 8. Native moves

- **The domino chain.** One push runs through a chain of objects. *Fits content like:* cause and effect; a habit; a process.
- **The squish.** A soft object is pressed and recovers. *Fits content like:* stress; resilience; a product benefit.
- **Inflate.** A flat shape inflates into the logo or the answer. *Fits content like:* a reveal; growth; a launch.
- **Perfect fit.** An object drops exactly into its slot. *Fits content like:* the solution; matching; order.

## 9. Pitfalls of the medium

- **Floaty physics** reads fake → correct gravity, slightly slowed, with real squash.
- **Harsh lighting** kills the softness → big soft lights, no hard shadows.
- **Plastic-looking everything** → mix materials: rubber, glass, cloth, one chrome.
- **Non-looping endings on Reels** → match the last frame to the first.

## 10. Engine

No demo engine yet (draft). A first demo should build a three.js page on the `studio/render_canvas.cjs` contract (WebGL canvas, `preserveDrawingBuffer: true`, scene time set in `FILM.render`):
- `studio.js`: cyclorama, RectArea key, generated HDRI, ACES, contact shadows.
- `softbody.js` / `cloth.js`: deterministic verlet simulation baked per frame.
- `materials.js`: rubber, frosted glass, satin, chrome presets.
- `sync.js`: contact events placed on the music beat grid.

Start from the Lemo-Opuscar `styles/glass-product/demo/studio.js` (studio lighting) and `core/three/post.js` (GTAO, DOF, grade). Vendor three.js with `npm pack three@0.170.0`.

## 11. Variation space

You decide the pastel, the material mix, loop length (4–12 s for Reels), and whether text appears in 3D.

- Structures: **one loop** repeated with variations; **a chain reaction** from left to right; **three satisfying moments** then the reveal.
- Openings: **a ball drops** into frame on the first beat; **a flat shape inflates**.
- Endings: **perfect fit**; **the loop seam** back to the opening frame.

---

Status: **draft** — no demo film yet. Before this is used as a library style it needs a demo film, `DEMO.md`, stills and the checks in the Lemo-Opuscar `MAINTAINING.md` ("Gates").
