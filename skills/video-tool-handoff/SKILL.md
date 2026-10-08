---
name: video-tool-handoff
description: Adapt a planned shot to an identified video tool/model, bind its actual references, export an immutable package and import the real generated take.
---

# Video tool handoff

Inputs: current shot plan, actual reference files, selected tool and model/version, applicable spending authorization. Read [profiles/bundles](../../docs/CONTRACT.md) and [walkthrough](../../docs/WALKTHROUGH.md).

Verify current official documentation or a dated direct check for the exact tool/model: input route, reference count/roles/order, duration, aspect ratio, prompt syntax, audio/dialogue and other required controls. Do not assume two UIs exposing the same model have identical features. Included portable profiles are unverified templates.

Choose a compatible route. Single-image generation needs a clean composed keyframe; multi-reference generation needs actual supported image bindings. Build the prompt around intended performance and motion; preserve visual context when the tool requires it. Unsupported dialogue or reference roles must be resolved explicitly, not silently dropped.

Prepare plan/profile changes before exporting. The current compiler produces generic direction text, not vendor-specific API requests. If a tool needs specific syntax, preserve the intended action and record the adapted version in the shot plan; review the outgoing inputs in the tool. Keep issued bundles immutable. Do not claim API/browser automation exists in this release.

Execute only through available authorized tools. Otherwise provide the package and exact manual actions. Record actual tool/model, download the real output and use `import-take` with the bundle used. Import validates technical metadata and provenance but leaves visual acceptance pending. Timeouts do not justify duplicate paid submissions; inspect an existing provider job before retrying.

Output: bundle location, actual execution status, imported take ID/hash if available, actual tool/model and remaining review requirements.
