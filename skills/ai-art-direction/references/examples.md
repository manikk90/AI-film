# Worked examples

## Index
- 1. Meaning before style
- 2. Region-specific world
- 3. Shot-local insert
- 4. Dirty OTS
- 5. Reverse angle
- 6. Strict frame correction
- 7. Screenshot-to-video
- 8. Detailed emotional panel
- 9. Conceptual substitution
- 10. Campaign system
- 11. Missing angle tag
- 12. Dialogue and offscreen audio

All scenes and registered tags below are synthetic teaching fixtures, not real project bindings or new story canon. In actual work replace them with approved project data. Good examples illustrate application; they are not evidence of generated-image or audience success.

## 1. Meaning before style

**Request:** Design a closing workshop scene that feels like pride mixed with loss.

**Bad:** "Epic moody cinematic, teal-orange, dusty rays, masterpiece." No evidence supports the feeling.

**Better reasoning:** The repairer completes one last careful handover, waits after the customer leaves, then closes the shop. Approved work surfaces, gestures and empty space can express the ending. Compare a shared-depth handover with separate restrained reactions; preserve the actual screenplay.

**Rule:** Select visible causal/emotional evidence before palette and lens. Do not invent the shop closure if the supplied story is only a routine pickup.

## 2. Region-specific world

**Request:** Develop a contemporary office for a contractor in a named north Indian village.

**Bad:** Fill it with cracked walls, hay, brass pots, temple lamps and tropical palms because it is "rural India."

**Better:** Research local construction and the contractor's work, then propose supported functions, construction, repairs and client circulation. Use approved character circumstances to decide maintenance/display choices. Show only approved objects after design is locked.

**Rule:** A place comes from evidence and use, not a stereotype inventory. Keep regional research questions open until evidence resolves them.

## 3. Shot-local insert

Synthetic bindings: `@repairer-01`, `@customer-01`, `@clock-01`, `@wrapping-paper-01`, `@workshop.counter.right-view`. The customer is by the entrance, outside this insert.

**Bad:** "@repairer-01 and @customer-01 in the full workshop, chairs, shelves, door, tools; close-up hands wrapping the clock."

**Good still prompt:**
```
[INSERT] @repairer-01's hands fold @wrapping-paper-01 around the supported @clock-01 on @workshop.counter.right-view. Hand-level close view; the fingertips and paper contact are sharp, with only the relevant counter surface visible. Retain the established window-light direction.
```

**Rule:** The hand owner and objects are relevant bindings. The customer, invisible face/full costume and unrelated shelves are omitted. The story still informs possession and action internally.

## 4. Dirty OTS

Synthetic bindings: `@repairer-01`, `@customer-01`, `@workshop.counter.front-view`. The repairer is behind the counter; the customer faces it from the public side.

**Bad:** Add an unnamed large blurred man to the left to make the shot cinematic.

**Good still prompt:**
```
[OTS, MCU] From behind @customer-01 at @workshop.counter.front-view, a narrow soft shoulder fragment occupies the left edge. @repairer-01 is sharp beyond the counter, pausing before replying; the mouth and eyes remain unobstructed. Preserve the established soft window light.
```

**Rule:** The foreground owner is an actual participant at an established position. Blur has a purpose. Compare a clean single if the foreground weakens the emotional read; do not move the cast to force an OTS.

## 5. Reverse angle

**Given:** A is beside the window; B is beside the door. The reverse camera sees the opposite wall.

**Bad:** Swap A and B's physical positions to preserve screen-left/right, and reuse the previous wall tag.

**Better:** Retain world positions, facing and distance; map the new projection and use the approved reverse view. Screen order may change. Preserve anatomical hand ownership and illumination origin.

**Rule:** Composition changes around the world. The world does not rearrange around composition.

## 6. Strict frame correction

**Request:** Correct the face identity in a supplied frame; keep its light.

**Bad:** Beautify skin, raise exposure, add rim light, change hairstyle and replace the background.

**Better edit instruction:** Use the supplied identity reference only for the face. Preserve the target's pose, expression intent, body, outfit, hair arrangement, camera, background and existing light. Remove non-scene overlays. Use the image-edit tool and inspect the actual result before declaring completion.

**Rule:** Identity correction is not a redesign. This instruction alone is not an edited image.

## 7. Screenshot-to-video

**Request:** The person in a screenshot nods once, then speaks; static frame, 5 seconds.

**Bad:** Start from a new angle, dolly around, reveal a doorway and add another participant.

**Better:** Preserve the supplied opening composition/light and visible inventory. Use one small compatible nod, a settled head, then the exact supplied line, with static camera. Check whether the required performance/dialogue can fit; do not speed through an implausible duration silently.

**Rule:** Temporal development must start from the actual frame. A semantic match is insufficient for fm.

## 8. Detailed emotional panel

**Request:** Detail the approved final clock pickup, ending at the completed handover.

**Bad:** Nine nearly identical close-ups, followed by an invented shutdown scene.

**Better internal coverage:** Existing wrapping action -> customer's arrival where established -> readable exchange -> recipient's response -> repairer's held reaction. Expand useful contact/response instants only as needed. End at the requested boundary; do not force nine shots when fewer distinct beats suffice unless the user requires a grid, in which case resolve meaningful supported instants.

**Rule:** Detail increases narrative precision, not cast count or unrelated plot. Each resulting cell still has its own local tags/view and one instant.

## 9. Conceptual substitution

**Request:** Explore an editorial image about protecting time; new conceptual imagery is permitted.

**Bad:** A spectacular random calendar-animal hybrid.

**Better proposed directions:** Show calendar and shelter in a meaningful relation; develop a recognisable composite; or imply a missing counterpart through a familiar context. State what the viewer must infer and compare whether the visible relation supports it.

**Rule:** Juxtaposition, fusion and replacement describe structures, not automatic effectiveness. Do not transfer the surreal transformation to a locked literal film scene. Restricted Iris terminology remains unverified beyond the public preview.

## 10. Campaign system

**Request:** Make three related campaign executions for an approved concept.

**Bad:** Three unrelated styles that happen to share a logo.

**Better:** Define invariant core relation, grid/shape, palette/type roles and exact copy; vary approved subject/crop/format while retaining recognisable structure. Compare each at actual viewing size and check adaptation hierarchy.

**Rule:** Consistency requires designed invariants, not identical composition or a copied external identity. Do not claim conversions or trust gains without data.

## 11. Missing angle tag

**Given:** The visible view requires an exact location-angle tag, but only a room name is supplied.

**Bad:** Invent `@room.reverse-angle` and call the prompt ready.

**Better:** Complete the composition proposal; state that exact angle binding is pending outside executable content. Ask for the approved mapping or inspect the authorised registry if available. Do not produce a generation-ready prompt with a fake identifier.

**Rule:** Unresolved binding is different from unresolved creative design. Do not stop independent work.

## 12. Dialogue and offscreen audio

Synthetic bindings: `@repairer-01`, `@customer-01`, `@workshop.counter.front-view`. Source explicitly requires the customer's voice offscreen. Exact line: "कितने पैसे हुए?"

**Good video prompt:**
```
[0-5s] [CU] @repairer-01 at @workshop.counter.front-view listens, then takes a small breath before answering. Static camera; retain the established soft window light. @customer-01 is heard offscreen only.

DIALOGUE: @customer-01 [offscreen, quietly] "कितने पैसे हुए?"
```

**Rule:** Offscreen audio is operationally relevant without making the customer visible. No text follows the dialogue paragraph. Do not add this voice to a silent still request.
