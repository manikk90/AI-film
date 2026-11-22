# AI-film

A portable screenplay-to-video production foundation. Keep the screenplay, creative decisions, reference assets, shot plan and review evidence in your own project, then hand shots to different image/video tools.

**Current release: runnable CLI + eight production skills + a script-writing skill with an approval gate + an orchestrator skill + SOP.** It is not yet an autonomous video generator or a graphical app. No provider accounts, model calls, paid generation, browser automation or verified vendor integrations are included.

## What works now

- Preserve an original UTF-8 screenplay and register every nonblank source line and scene heading.
- Validate an assistant-authored beat/shot plan; report missing scenes, source units and beats.
- Register immutable character, costume, location, prop and keyframe images with hashes and provenance.
- Export a single-image, multi-reference or text-only shot bundle with prompt, input order, settings, source excerpts and checks.
- Reject dropped references, incompatible declared limits, changed bundle files, stale plans and wrong media dimensions/duration.
- Import real video files, attach per-beat review evidence and keep generated versus accepted states separate.
- Mark affected takes stale when a shot, its assets, mapped beats, adjacent continuity boundaries or global direction changes.

Coverage checks prove bookkeeping completeness, **not** that an AI understood every action or that a video looks correct. An independent breakdown review and full-clip visual/audio review remain necessary; a capable assistant can perform those reviews when its host can inspect the media. Human attention is for creative exceptions and unavoidable access/setup blockers.

## Run locally

Python 3.9+ is enough for records and exports. Install FFmpeg (`ffprobe` on PATH) for asset/video import. No Python runtime dependencies are needed.

```bash
git clone https://github.com/manikk90/AI-film.git
cd AI-film
python3 -m aifilm --help
python3 -m aifilm init examples/screenplay.txt projects/demo
python3 -m aifilm set-plan projects/demo examples/plan.json
python3 -m aifilm audit projects/demo
```

The audit intentionally exits **1**: no generated, reviewed takes exist. Exit **0** means the recorded completion gates pass; **2** means invalid input or an operational error.

Export a text-only demonstration shot:

```bash
python3 -m aifilm export-shot projects/demo SH001 exports/demo-SH001-v1 \
  --profile profiles/portable-text.json
```

Open `RUN_IN_TOOL.md` inside the export. The three included profiles are explicitly **portable templates**, not certified settings for any current model. They do not guarantee support for dialogue, reference syntax or every duration. The example plan's text-only route demonstrates the records; use canonical references/keyframes for actual character continuity.

## Use with your AI assistant

Keep this repository available to the assistant and ask:

> Read `skills/film-production/SKILL.md`. Use my screenplay to prepare a complete production project in a new ignored `projects/` folder. Preserve screenplay intent, develop character/costume/location/prop references, plan every beat, and export shots for my selected tool. Read the relevant specialist skills. Ask me only about consequential creative ambiguities. Do not report generated or reviewed assets without real output and evidence.

These are repository skills, not automatically installed plugins. Hosts that load `SKILL.md` can use them directly; other assistants can read the same instructions and linked contracts. Keep the repo layout intact because skills link to shared docs. [Skill map](docs/SKILLS.md).

The [Director rules](docs/DIRECTOR_RULES.md) also cover stable blocking, broad composition/lighting exploration, detailed emotional coverage, reactions/inserts, match cuts and exact frame-local prompt information. They are shared by the Director agent and the relevant production skills; the linked lighting and art-direction references are supporting knowledge, not new runtime/model integrations.

For image references, manual video import and review commands, follow the [walkthrough](docs/WALKTHROUGH.md). The [data contract](docs/CONTRACT.md) defines plan and review formats. The [SOP](docs/SOP.md) defines decision and completion rules.

## Style library (drafts)

[`styles/`](styles/README.md) holds 67 draft style prompts (Indian traditions, world folk arts, animation techniques, art movements, internet/digital looks, cinema eras) for films rendered in code, in the Lemo-Opuscar `STYLE.md` format. They are written prompts with **no demo film yet**; treat them as creative-direction references, not tested looks.

## Viral studio

[`studio/`](studio/README.md) and `.claude/` define a four-agent team, run with `/viral-studio`:

- **social** finds trending topics and writes the publishing kit
- **researcher** finds the unique angle and verified detail
- **writer** writes hook-driven scripts
- **director** decides the style, format and duration, then makes the film
- **mann** edits the owner's raw footage (storyboard first), and learns styles and corrections

The owner approves the script before any production starts, and agents never post anything. Every finished film also ships an editor package (`final/editor/`, built by `studio/editor_package.py`) that opens in Premiere Pro or DaVinci Resolve for small corrections. Owner feedback is recorded in `studio/LEARNINGS.md` (`/studio-learn`), and every agent reads it.

## Ready format skills (imported)

There are 47 format skills from the owner's Ai-Animation repo (MIT © aansh.ai). They include a Madhubani kahani, a katha video, lyric videos, anime reels, talking-head edits, motion effects and looks, plus `daksh-ai` with its own engine.

- They live in `.claude/skills/` and are listed in `studio/STYLE_MENU.md` under "Ready formats".
- Each runs inside `studio/SKILL_HARNESS.md`: the owner's gates, rights and fact checks, and the 2-file delivery.
- `studio/import_skills.py` regenerates them from the upstream repo.

## Mann: AI video editor

[`editor/`](editor/README.md) adds **Mann**, an editor agent for the owner's own footage (`/mann-edit`). A smart engine analyses the footage and suggests styles, unique edits, hooks and problems; the owner only finalises the style, locks the script and approves the storyboard (corrections are re-shown for the whole video or just the changed part). `autocut` drafts the cut in any of **50 catalogued editing styles** ([`editor/styles/INDEX.md`](editor/styles/INDEX.md)); then Whisper transcripts, a **storyboard of numbered frames that must be approved before the render**, and FFmpeg assembly with transitions, speed ramps, punch-ins, colour presets/LUTs, titles, burned Hindi/English subtitles, Hyperframes motion graphics (alpha overlays), ducked music, SFX, −14 LUFS mastering and measured QC. A craft rulebook ([`editor/craft/CRAFT.md`](editor/craft/CRAFT.md): cuts, continuity, eyelines, composition, typography hierarchy, font pairings, colour themes, safe zones, sound) is applied to every cut, with 27 measurable rules checked automatically. `/mann-style-lab` breaks down reference videos (yt-dlp) into style sheets in `editor/styles/`, and the owner's corrections tighten `editor/rules.json`, which QC enforces. Tools: `bash editor/install.sh`; `python3 -m aifilm.editor doctor`.

## Next implementation stages

The next useful milestone is a tested image API adapter and video API adapter, backed by persisted jobs, credentials outside the repo, budget limits and provider-job reconciliation. Then add the dashboard, provider-specific prompt compilers and optional MCP access. [Architecture and roadmap](docs/ARCHITECTURE.md).

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q aifilm
```

Media tests use FFmpeg-generated synthetic fixtures. Passing them proves workflow invariants, not cinematic quality or provider integration. No paid generation is performed.

[CI workflow example](docs/ci-checks.example.yml) runs the same checks on Python 3.9 and 3.12. It is documentation only, not an active GitHub workflow; a maintainer can install it at `.github/workflows/checks.yml` with a workflow-enabled credential.

Project media, exports and secrets are ignored by Git. Exported shot bundles do contain screenplay excerpts and assets; share them only with the intended tools/collaborators.
