# Standalone design and implementation boundary

## Implemented in this release

The production core is a Python standard-library CLI. `project.json` is the versioned, local source of truth; media lives alongside it. A process lock prevents simultaneous CLI writes and JSON replacement is atomic. Original screenplay bytes and registered media are hashed. This is a single-user foundation, not a distributed database.

The `skills/` layer supplies filmmaking judgment. Skills produce structured plans, designs and reviews; the core validates records. A prompt is not execution, a registered image is not automatically visually approved, and a submitted review is an attestation rather than mathematical proof.

The portable adapter emits immutable manual bundles. Input roles/order and composed-frame provenance are explicit. A model-specific API request/compiler is not implemented. Generic `Reference 1` labels may need a particular tool's syntax; update the plan/profile and re-export when adapting a shot. Do not silently edit an already issued bundle.

Current CLI commands: `init`, `add-asset`, `set-plan`, `review-breakdown`, `export-shot`, `import-take`, `review-take`, `audit`.

## Capability boundaries

| Capability | Current | Next implementation |
|---|---|---|
| Screenplay parsing | UTF-8 plain text with explicit headings | FDX/DOCX/PDF import with source preservation |
| Semantic breakdown | Assistant-authored, source-linked, independently reviewed | Optional LLM adapter, still reviewed |
| Asset/storyboard generation | External tool + registered actual images | Image API connector |
| Video generation | Portable bundle + external execution | Provider adapter and durable jobs |
| Model adaptation | Generic input modes and declared limits | Vendor/version-specific syntax, parameters and audio checks |
| Visual/audio QC | Evidence submitted by a reviewer with media access | Assisted temporal vision/audio checks; uncertain stays pending |
| Recovery | Atomic records, locks, idempotent repeat imports | Provider job reconciliation and retry budget |
| Interface | CLI and repository skills | Local React dashboard; optional MCP |

## Planned connector contract

Each connector should expose `capabilities`, `validate_inputs`, `compile_request`, `submit`, `status`, `download`, and, if supported, `cancel`.

- Capability records identify the exact tool wrapper, model/version, region/tier when relevant, verification date and evidence.
- Before submission persist the immutable request hash, input hashes, estimated cost, budget reservation and attempt ID.
- Save provider job IDs. A timeout is an unknown outcome, not permission to submit again. Reconcile the existing job before any retry.
- Separate transient network retries from creative regeneration. Both have finite configured limits.
- Preserve exact outgoing requests and downloaded outputs without recording credentials.
- An unsupported constraint produces an explicit alternative or a blocked status; do not silently remove references or dialogue.

API integration is preferred where available. Browser execution requires tested flows and can break with UI/login changes. Manual export/import remains the universal fallback; it does not provide unattended generation.

## Build sequence and acceptance gates

1. **Portable core (this release):** source completeness, input provenance, import/review, stale-output and interruption tests.
2. **One image connector:** compose approved identities/looks/locations into a clean shot frame; preserve provenance.
3. **One video connector:** real job lifecycle, spending ceiling, timeout reconciliation, output download and review. Validate against the exact current provider API before coding.
4. **Dashboard:** scene progress, asset versions, comparison views, missing beats, creative decision inbox and focused repair.
5. **More adapters and MCP:** add tools without changing the screenplay/asset contracts. MCP exposes this system to compatible assistants; it does not make third-party generators automatically controllable.

Use React + FastAPI for the dashboard/API stage and SQLite for evolving transactional records, with a separate persisted worker for long jobs. Do not run durable generation solely inside an HTTP request or an in-process background callback. [FastAPI guidance](https://fastapi.tiangolo.com/tutorial/background-tasks/).

## Known limitations

- Line-level accounting cannot discover omitted sub-actions by itself. The semantic breakdown review must compare the original screenplay, not only a summary.
- A reviewer can be mistaken. Hashes establish which artifact was reviewed, not whether the judgment was correct.
- Registering `derived_from` records declared provenance; it does not prove the pixels match. Inspect the composed keyframe before generation.
- No automated adjacent-shot visual comparison, speech transcription or asset-design approval database exists yet. Record those checks in the review evidence and decision records.
- Plan history is retained, but in-place screenplay revision/migration is not implemented. Create a new project revision; do not edit the frozen source.
- Jobs are not implemented because no provider calls are made. Resume currently means reopening persistent project state and importing existing outputs.
- Remove a stale `.production.lock` only after checking the recorded PID and confirming no writer is active. Do not run two writers on the same project.
