---
name: coverage-quality-audit
description: Independently check original-screenplay coverage and inspect generated clips for beat execution, continuity, audio and technical errors before accepting production shots.
---

# Coverage and quality audit

Inputs: original screenplay, plan, canonical assets, actual clips and their hashes. Read [review contract](../../docs/CONTRACT.md).

First compare original source against semantic beats and planned shots. A line mapping cannot prove every sub-action is represented. Inspect compound actions, exact dialogue/speakers, off-screen information, transitions and scene boundaries. Record breakdown acceptance only after this check and full structural mapping.

Inspect the entire relevant clip sequence, including audio where required. Compare face/look, geography, prop state/ownership, screen direction, performance and start/end boundaries against source, canonical images and adjacent shots. Do not infer action execution from a still or provider success flag.

For each assigned beat and exact acceptance criterion, write `pass`, `fail` or `uncertain` with concrete observed evidence, preferably timestamps. Complete continuity and technical checks. Copy the actual take hash returned at import. If the host cannot inspect video/audio, mark those checks uncertain; never invent observations.

Use `review-take`; all checks must pass for acceptance. A later failing review revokes acceptance for that take. Run `audit` and route defects to the responsible design/shot/input stage. Repair locally and preserve unaffected work. Changes to canonical assets use new IDs and require revalidation of dependents.

Output: missing/stale/unreviewed items, evidence-supported failures, accepted counts and recommended focused repairs. Distinguish completed bookkeeping from uncertain artistic judgment. No silent source omission or bypassed review to make the report green.
