---
name: screenplay-breakdown
description: Convert a complete screenplay into source-linked scenes, semantic beats and asset requirements without losing actions, dialogue, intercuts or transitions.
---

# Screenplay breakdown

Inputs: original screenplay, source-unit register, existing creative decisions. Read the [plan contract](../../docs/CONTRACT.md) before writing JSON.

Read the entire source. Register scenes with the CLI; if source conversion or scene-heading detection is incomplete, fix the conversion rather than inventing a successful import. Preserve original wording and original scene order.

Split each scene into observable narrative beats. A single sentence may contain multiple ordered actions; create separate beats with the same source-unit IDs. Preserve dialogue verbatim, including speaker and off-screen/voice-over intent. Include context that is essential to interpreting an action. Account for flashbacks, montage sub-events, intercuts and transitions rather than merging them into a vague summary.

Produce `beats` plus a scene-indexed asset-requirement document: character identities, look changes, location/time variants, hero props and prop transitions. Distinguish script facts from visual choices. Only title/metadata before the first heading may be classified as preamble; never use preamble to hide a scene.

Read the original source again against the proposed beats. Confirm every independent action and exact dialogue has representation; line-ID coverage alone is insufficient. Save a partial plan honestly if shots are not yet planned. Record `review-breakdown` only after complete shot mapping and a genuine independent review pass.

Output: source-linked beat list, asset requirements, unresolved material contradictions and coverage findings. Do not rewrite the story without a recorded creative decision.
