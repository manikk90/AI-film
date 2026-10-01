# Screenplay-to-video SOP

Scope ends at checked video shots and the production handoff. Final editing, scoring and film mastering are separate. Script-required speech and performance must still be covered by the chosen video/audio workflow.

## 1. Intake and source accounting

Preserve the original screenplay. The CLI supports explicit English-format scene headings (`INT.`, `EXT.`, `INT./EXT.`, `I/E.`, `SCENE 1`); it does not pretend to infer scenes from prose. Convert other document formats into traceable UTF-8 text before intake and verify conversion completeness.

Account for every nonblank line, including title/preamble lines. Only lines before the first scene can be classified as preamble. Split compound actions into separate beats, preserve exact dialogue, include off-screen events, montages, intercuts, flashbacks and transitions. Every beat maps to original source units and a scene; every beat needs planned coverage.

An independent review pass must read the original screenplay against the breakdown. Do not approve based only on nonempty mappings: a single line may contain five actions. The reviewer can be an assistant with the original source, not necessarily the human owner.

## 2. Creative decision policy

Honor screenplay facts and previously resolved choices. Infer routine details coherently and label them `inferred`. Seek human input only for consequential ambiguity or a proposed deviation: genre/treatment changes, story contradictions, major character reinterpretation or altered dialogue/ending.

Provide the conflict, your recommended choice, and its impact. Record unresolved issues as `needs_creative_decision`; exports remain blocked until resolved. Resume unrelated analysis/design work while awaiting the decision where useful.

An unavailable account, tool outage or exhausted configured budget is an operational blocker, not a creative question. Recover automatically when possible, otherwise report it accurately. Never claim human-free execution when tool access is missing.

## 3. Design and asset continuity

Separate identity from look: a character's face/body is stable; costume, hair, makeup, injury, dirt and wetness are scene-dependent versions. Use a canonical image for identity and derive consistent views. Define costume fabric, fit, accessories, footwear and wear states.

Define locations with entrances, exits, object positions, sightlines and required reverse angles. Specify important props, ownership and state changes. Design everything required by screenplay/coverage; do not generate every imaginable variant. Background dressing can share a location record; story-critical props need individual identity.

Register actual PNG/JPEG/WebP files using immutable IDs. Register a composed keyframe with `derived_from` IDs for every canonical reference it uses. Inspect identity, wardrobe, location geometry and prop state before allowing the frame to drive video. Registration alone is not visual approval.

## 4. Shots and reference routing

Each shot carries screenplay beats, purpose through its action/criteria, framing, blocking, lighting, audio intent, duration, start/end states and input references. Timing must accommodate real action and dialogue; split long beats without losing them.

For storyboard-driven work, extract or regenerate the intended clean panel. Do not feed a labelled contact sheet as a single-shot starting frame unless that exact model/workflow supports it. Inspect crop quality and resolution; do not assume a crop is a production-quality frame.

For direct-reference work, verify the tool accepts the requested identities/roles. When only one image is supported, compose a keyframe rather than dropping identities/locations/props. `asset_ids` records dependencies; `input_asset_ids` records exactly what will be uploaded. Derived provenance must account for the difference.

## 5. Model/tool handoff

Check the exact tool AND model version, supported input route, reference roles/order/count, duration, aspect ratio, audio, prompt syntax and parameters against current official documentation or a dated successful check.

Included profiles are portable templates. Empty duration/aspect-ratio arrays mean **not specified**, not unlimited provider support. Exported prompts are generic direction drafts. For an actual provider, resolve binding syntax and unsupported audio/settings before running; create a new plan/profile/bundle revision when inputs change.

Before a paid call, use the owner's established budget/tool authorization. Do not infer unlimited spending from a request to create a skill or inspect a repo. No paid calls exist in this CLI.

## 6. Generation, import and review

Preserve the bundle used for execution. Download the real output, record actual tool/model and import against that bundle. The core checks duration, aspect ratio, hashes and stale dependencies. It cannot prove which prompt a third-party UI actually submitted; the operator/connector must verify the actual bound inputs.

Review the full relevant temporal sequence, not just a thumbnail or first/last frame. Check every beat and acceptance criterion, face/costume, prop transitions, screen direction, emotional performance, temporal artifacts, dialogue and technical quality. Check adjacent shots and canonical references. Record timestamps and concrete evidence. `fail` and `uncertain` both prevent acceptance.

Do not submit invented review evidence to get a green dashboard. If the host cannot view video/hear audio, leave those checks pending and use a capable review environment.

## 7. Repair and completion

Repair the responsible input or shot. Preserve unrelated approved work. Use new asset IDs; update the plan and re-export. Global treatment changes can invalidate all takes; local shot changes invalidate that shot, and boundary changes also invalidate adjacent continuity checks. Inspect any further narrative dependencies manually until a richer dependency graph exists.

Complete only when all source units, scenes and beats are covered, the independent breakdown review is current, every planned shot has a current accepted take, and no unresolved creative decision remains. The completion report represents stored attestations and bookkeeping checks, not a guarantee of artistic perfection.
