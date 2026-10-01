---
name: shot-continuity
description: Turn screenplay beats and designed assets into a complete ordered shot plan with blocking, timing, reference dependencies and continuity boundaries.
---

# Shot planning and continuity

Inputs: source-linked beats, treatment, character/look/location/prop records. Read the [shot contract](../../docs/CONTRACT.md).

Plan shots around dramatic purpose and observable action. A shot may cover multiple beats; every beat must have coverage. Preserve exact dialogue and allow time to perform it. Do not remove beats to fit a model's duration; split at an intelligible action boundary instead.

Specify composition, blocking, eyeline, screen direction, camera behaviour, lighting, audio intent, duration and aspect ratio. Set concrete `start_state` and `end_state` covering position, prop ownership/state, costume/injury and emotion. Check adjacency and scene chronology, including flashbacks and deliberate jumps.

Set `asset_ids` to all canonical dependencies. Set `input_asset_ids` only to the actual ordered generator inputs. For a composed frame, include it among dependencies and require provenance for the canonical assets it replaces in the actual input list. Do not silently omit a prop/identity to satisfy reference-count limits.

Write observable acceptance criteria, such as a specific prop transfer or exact line, rather than "cinematic quality". Validate with `set-plan` and inspect `audit`. Structural completeness does not replace a semantic comparison against the screenplay.

Output: ordered shots, scene-specific continuity notes, asset/input mapping, timing assumptions and unresolved material conflicts. Keep shot IDs stable across retries.
