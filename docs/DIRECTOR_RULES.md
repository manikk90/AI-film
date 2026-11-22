# Director: shot planning and prompt rules

Synced 2026-11-22 from the owner's saved Director corrections of 2026-11-18 and the current research discussion. Apply across films. Project identities, exact tags, layouts and dialogue stay in the project's approved records. These instructions guide the assistant; they do not add a model API, background sync service or automatic semantic validator.

## Planning before camera

Read the requested scene/beat and approved changes. Resolve purpose, character objective, obstacle, subtext, audience knowledge, reveal timing and emotional entry/exit. Establish world geometry, positions, facing, attention, entrances, contacts and prop ownership before selecting cameras. Give each shot an information, emotional or editing purpose. Check dialogue/action time and adjacent-shot continuity. Keep this planning internal when only executable prompts are requested.

## Blocking remains stable

Keep established character/object world positions, relative distance/depth, facing, seat/ground level, anatomical hand ownership, support, contact, prop orientation and scale across shots. Change them only for an authorised movement/repositioning and carry its end state forward. A reverse camera can change screen placement without changing the world. Compose around the arrangement; do not relocate people, resize a bag or move architecture to improve an angle. Keep offscreen state internally.

## Explore composition by default

A composition request authorises broad exploration of unlocked choices; the owner need not repeat "experiment". Compare meaningful changes in size, camera distance/height/viewpoint, perspective, balance, negative space, architectural framing, foreground/midground/background, focus and lighting relationships. Explore useful combinations until new candidates repeat an idea, offer no useful tradeoff or violate a lock. No fixed exploration quota and no obligation to use every technique.

For suitable 2S/OTS coverage, explore asymmetric depth and a relevant participant's lightly soft shoulder, partial head or profile at a frame edge. Name the actual owner, edge and sharp target. Keep both faces or contact readable when both matter. Do not add an absent third person or anonymous foreground head. A sustained eye-level shot remains valid when motivated.

Select complementary compositions across actual successive beats. Keep aesthetic alternatives separate from chronological coverage; a different lens alone is not a new event. Exploration does not authorise unlimited media batches or generation on a planning-only request. Existing production and approval gates still apply.

## Lighting with the composition

Use the [lighting library](director/lighting.md) when relevant. Resolve motivating source, world direction, softness, contrast/fill, colour relationship, falloff and subject/background separation. For a new open look, compare plausible alternatives. In an established scene retain time, source direction, approved palette and lighting character across reverses. A composition request does not automatically authorise relighting a strict frame. Keep required faces, hands, contacts and props readable; neither blur nor a new rim light is mandatory.

Apply the existing colour workflow to eligible choices. If a newer explicit source-frame lock conflicts with a generic palette target, preserve the lock and report the conflict rather than secretly regrade the frame. A still has one lighting state; flicker or moving light belongs to video direction.

## Detailed panels, beats and moments

An explicit request for detail overrides short-prompt defaults for that request. Develop maximum useful source-supported depth:

- Map emotional entry, intention/subtext, processing, decision and consequence. Express them through specific performance or purposeful stillness; do not force crying, shouting or a new emotion in every cell.
- Explore causal micro-beats: stimulus, justified anticipation, action/contact, perception, response and aftermath. Do not make each physical phase a robotic separate cut or restart the same action on every angle.
- Give reaction shots a named stimulus, perceiving listener, processing onset and changed response. Follow the character's approved perception; do not invent normal sight or simultaneous crowd reactions.
- Use inserts of already supported hands, objects, text, contact or environmental consequences. Explain their evidence/emotional/editing job. Preserve owner, scale, support and laterality; do not invent a symbolic prop for coverage.
- Plan outgoing and incoming cut states. Distinguish continuation of one action from a graphic/thematic match between different images. Use reaction cuts, contrast, J/L sound bridges and holds where motivated; no match-cut quota.
- Estimate pacing from actual dialogue/audio, action and processing. Label unmeasured times. Preserve exact words and reveal order.

Default one panel is a 3x3 board of nine distinct horizontal 16:9 shots unless the owner specifies otherwise. Each still shows one exact instant. Put movement/focus progression in video direction. Do not silently expand a requested single panel into later scenes; state any remaining beat/next entry state. Report unused capacity rather than inventing filler. A board's total resolution is not each cell's resolution.

## Every prompt is an individual shot

Self-contained means enough information to produce THIS frame/authorised shot, not the entire scene. Derive its inventory from the approved crop/beat or authorised video progression, not the global cast list. Include only:

- Exact relevant character/partial-owner and approved look bindings.
- Required visible props and the actual matching location-view/surface binding.
- Action/pose/contact, performance, framing, focus and lighting information operationally necessary for this shot.

Remove unrelated exposition, adjacent/future beats, absent people/props, off-frame accessory/body descriptions and scene-wide continuity paragraphs from visual prose AND actual reference inputs. Deleting an irrelevant tag while retaining its subject in prose fails. Do not mention an absent object merely to say it is absent. Keep relevant visible crowd and partial/reflected owners; economy is not permission to erase required evidence.

A hand/shoulder owner tag establishes identity without requiring the whole person onscreen. A necessary offscreen source can explain visible illumination. Required offscreen dialogue/sound keeps its exact audio source but does not add that person to visual bindings. A composed frame's genuine ancestor dependencies remain in provenance; this is not permission to attach the entire scene register.

Detailed mode increases relevant precision, not inventory. Example only: a face CU omits an out-of-crop bag/cane/footwear; a hand-and-object insert omits off-frame eyes; an OTS retains the visible shoulder owner's exact tag. Actual approved crops win over examples.

## Exact location and tag checks

Preserve exact spelling, suffix, identity and approved costume variant. Do not normalise or upgrade production identifiers. Repeat required local bindings in EVERY individually executable shot and board cell; a shared panel header is not a substitute.

When the asset system requires a view-qualified location token, choose an actual registered front/left/right/wall/ground view matching the camera. Do not submit an unresolved base family, guess a suffix or attach all views. Missing mappings remain pending; continue unaffected planning and resolve them before reference-dependent execution. Check actual asset roles as well as tag strings.

## Prompt output and frame-match modes

For prompt-only work, return ordered executable shots in one copy-ready block. Omit scene/panel preambles, shared PHYSICAL/LOCATION LOCK paragraphs, standalone Refs lines, research IDs and QC commentary; encode only each shot's necessary facts locally. Keep existing shot IDs. Be concise by default; provide relevant actionable depth when requested.

This is the assistant's prompt-delivery contract. Existing CLI export bundles keep their documented generic structured format; the handoff agent must adapt the outgoing prompt to the requested tool/mode. The CLI does not automatically crop context, infer visible inventory or enforce this copy-ready format. Keep genuine provenance and audit records separate from the final model-facing prompt.

For video, keep all action, camera, sound and performance direction before a blank line and the final dialogue block. Preserve approved words, order and exact speaker token. Nothing follows that shot's dialogue. Still/storyboard prompts use dialogue to guide the selected instant; do not add spoken text or rendered captions unless requested.

- Screenshot plus a video-prompt request defaults to frame match (`fm`): preserve the actual starting/ending reference role, crop, inventory, geometry, focus and light; only compatible authorised progression.
- `fx` rethinks every supplied shot's unlocked composition dimensions, retaining established blocking and strict locks. Do not satisfy it with cosmetic wording edits.
- `fx c` is composition-focused and includes actual visual previews above revised prompts. Text sketches are not delivered previews. Preserve source/production gates.
- `fc` corrects the supplied image within the requested scope. Preserve original lighting unless relighting is requested, preserve unrequested identity/pose/outfit/geometry, and remove non-scene interface overlays. Do not erase real scene signage or transfer an identity reference's unrelated features.

## Art-direction research

Use [AI Art Direction](../skills/ai-art-direction/SKILL.md) for the operational workflow, technique selection, world/material design, 2S/OTS and lighting decisions, worked examples and separate QC passes. Load relevant references rather than the entire library. Its synthetic examples are not project canon; strict frames, blocking, identities, exact bindings and current approval gates remain authoritative.

Use [the research reference](director/art-direction-research.md) for visual communication, perception and design methods. Keep sourced techniques separate from untested applications. A metaphor is optional and must serve the scene; it does not authorise a new prop, altered geography or a premature reveal. Distinguish what an image depicts, what it suggests and whether the execution is coherent.

## Review and sync scope

Read each shot alone. Check local completeness and relevance, exact bindings, stable blocking/light, perception, performance causality, cut continuity and requested output scope. Text/tag review does not prove visual, temporal or audio quality; inspect actual media for those claims.

This sync updates Director instructions, affected planning/storyboard/handoff/QC skills and the studio's owner-rule ledger. It does not change runtime code, schedules, provider integrations, other agents or project assets. Research is a dated reference, not a tested quality-gain claim. Future changes require an actual repository write; connection alone is not background synchronisation.
