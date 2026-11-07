# What-if 3D Explainer — Style Prompt

> A short body or science fact shown in close, slightly gross, realistic-cartoon 3D: the camera dives into skin, blood or a machine, numbered steps walk through what happens, and huge outlined captions shout the key phrase ("THAT BUMP IS YOUR IMMUNE SYSTEM").
> References (grammar only): the owner's reel lists "ZackD Films"; the screenshot shows the genre's grammar: a close 3D macro of skin with a bump, a "STEP 10" tag, bold yellow-and-white outlined captions and a "that's why…" payoff. Copy no creator's models, scenes, wording, voice or branding, and never imply endorsement.

## 1. Essence, and what it is not

- **Macro 3D of everyday things**: skin, teeth, eyes, insects, food, small machines, shown far closer than a camera could go.
- **Realistic-cartoon materials**: believable textures (pores, moisture, veins) with simplified shapes and saturated colour, so it is fascinating but not medical-gore.
- **Step structure**: the fact is told as numbered steps (STEP 1 … STEP 10) or a chain "and that's why…".
- **Captions are the design**: two-tone heavy captions, the key word in yellow, thick black outline, centre frame.
- **Fast and blunt**: 20–45 s, a cut or move every 1.5–2.5 s, a payoff line at the end.

Not Microscope Story (scientific measurement, slide imagery, counting). Not X-ray (radiographic look). Not Flat Vector Explainer (no 3D materials).

## 2. Materials & rendering

- **Engine**: three.js (vendored), PBR. Skin: `MeshPhysicalMaterial` with subsurface fake (wrap lighting, warm terminator), pore normal map (procedural cellular noise), moisture specular (clearcoat 0.2–0.4); blood vessels as tube geometry under translucent skin.
- **Cells and microbes**: soft spheres and blobs with fresnel rim light, inner translucency, slow wobble (noise displacement).
- **Lighting**: a warm key, a cool rim, strong ambient occlusion; macro DOF with a very narrow focus band.
- **Effects**: swelling (vertex displacement over time), fluids as metaball blobs, particles for chemicals (histamine, signals) with glow.
- **Look**: slightly over-saturated, high clarity, mild vignette, no film grain.

## 3. Colour logic

- Skin tones warm and saturated: `#e38a6f`, `#c96a55`; blood `#a3151f`; immune cells pale cream `#f4ead2`; signals cyan `#3ad7ff`.
- Sky or "outside" shots: clear pale blue `#9cc8ea` to separate the outside world from inside the body.
- Caption colours fixed: white `#ffffff` and yellow `#ffd400`, black outline.
- Never: realistic gore, grey hospital palettes, brand logos.

## 4. Type & subtitles

- **Captions**: **Poppins** ExtraBold (Latin and Devanagari) 70–96 px at 1080 × 1920, uppercase for Latin, black outline 6–8 px, line 1 white, the key phrase yellow; centred in the upper-middle third, inside the safe zone; pop on with a 110 % → 100 % scale. In Mann: `subtitles.animate: "pop"` or `"highlight"` with `highlight_color: "yellow"`.
- **Step tag**: "STEP 10" in a dark rounded pill top-right inside the safe zone, **Rajdhani** Bold.
- **Payoff line**: "and that's why" small white, then the key word huge yellow.

## 5. Motion quality

- 30 fps, smooth CG motion, fast camera dives (0.8–1.2 s) with ease-in-out, time-lapse for slow processes (swelling, healing).
- Every step changes something visible: a new object, a zoom level, a colour shift.
- Hold the payoff shot 1.5–2 s, then end (loop to the first frame when possible).

## 6. Camera grammar

| Move | What it expresses | Can serve |
|---|---|---|
| Dive from outside into the body | the hidden world | under the skin; inside the ear |
| Macro hold on a reacting surface | the visible symptom | a bump; a bruise; a pimple |
| Orbit around a cell or object | understanding | an immune cell; a virus; a gear |
| Cutaway cross-section | the mechanism | layers of skin; inside a tooth |

## 7. Sound palette

- **Music**: tense, curious underscore: plucked synth arps, low pulses, subtle risers into each step; light, never horror.
- **SFX**: squelches, bubbling, a heartbeat thump, whooshes for dives, a "ding" for each step, a deep boom for the payoff.
- Voice-over fast and confident (2.6–3 words/s), or no voice with captions only; music ducked ~10 dB; master −14 LUFS.

## 8. Native moves

- **Step countdown.** STEP 1 to STEP N through the process. *Fits content like:* what happens when you get a cut; how a vaccine works.
- **"That's why."** A chain of causes ending in a familiar symptom. *Fits content like:* why it itches; why you yawn; why ears pop.
- **What if.** An extreme scenario shown calmly. *Fits content like:* what if you never slept; what if you swallowed gum.
- **Inside view.** The camera passes through a surface into a cross-section. *Fits content like:* inside a tooth; inside a battery.

## 9. Pitfalls of the medium

- **Medical claims without sources** → every step checked by the researcher (`FACTS.md`); label simplifications.
- **Real gore** → stylise; keep it fascinating, not disturbing.
- **Captions that cover the action** → captions in the upper-middle third, action in the centre-lower third.
- **Copying the creator's scenes or phrasing** → original scenarios, models and script.

## 10. Engine

No demo engine yet (draft). A first demo should build a three.js page on the `studio/render_canvas.cjs` contract:
- `skin.js`: skin material with pores, moisture, wrap lighting, vessels; swelling displacement.
- `cells.js`: blob cells and microbes with fresnel and wobble; metaball fluids.
- `dive.js`: camera paths for outside → inside dives, cross-section clipping planes.
- `steps.js`: step timeline synced to the voice-over; captions burned by Mann (`edl` ASS text with `pop` animation and the step tag as a motion template).

Start from the Lemo-Opuscar `styles/microscope/demo/film.js` (macro biology camera) and `core/three/post.js`; captions and step tags come from Mann (`motion` templates, animated captions).

## 11. Variation space

You decide the subject, how close the camera goes, whether a voice is used, and the step count (5–12).

- Structures: **step countdown**; **cause chain** ending in "that's why"; **what-if** scenario.
- Openings: **the symptom** in macro (a bump, a yawn); **a bold question** caption over the outside view.
- Endings: **the payoff caption**; **a loop** back to the opening symptom.

---

Status: **draft** — no demo film yet. Before this is used as a library style it needs a demo film, `DEMO.md`, stills and the checks in the Lemo-Opuscar `MAINTAINING.md` ("Gates").
