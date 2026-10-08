---
name: storyboard-keyframes
description: Create and inspect shot-specific storyboard panels and clean generation keyframes using canonical character, costume, location and prop references.
---

# Storyboard and keyframes

Inputs: shot plan, canonical images, target input route. Follow [reference routing](../../docs/SOP.md).

Use a storyboard to resolve framing, action readability, blocking and geography before expensive video generation. Preserve identities and scene-specific looks by supplying actual canonical references. A contact sheet is a review artifact, not automatically a valid starting frame for one video shot.

Extract or regenerate the intended panel into a clean, sufficiently detailed image without labels/borders. Inspect face, wardrobe, important props, hands, perspective, entrance geometry and intended initial pose. Resolve contradictions with the planned action: a final pose is not necessarily a useful starting pose.

Register a clean frame as a `keyframe` asset with `derived_from` listing its canonical input IDs. Ensure all dependencies are represented transitively, then update the shot's input mapping. Review actual pixels; declared provenance does not prove identity or location fidelity.

For direct multi-reference video, a generated storyboard can be skipped when not useful, but shot planning and reference checks remain required. Do not auto-generate unused panels. Deliver panel/keyframe files, mapped shot IDs and observed review findings; missing generation stays explicit.
