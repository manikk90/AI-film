# Viral studio

A team of four agents (plus Mann, the editor) that finds what people want to watch, researches it, writes a script built to hold attention, and makes the film. Each agent is defined in `.claude/agents/`; the pipeline and the gates are in `.claude/skills/viral-studio/SKILL.md`.

| Agent | Kaam (job) | Writes |
|---|---|---|
| **social** | Trending topics dhoondhna (with dated sources), virality score, competition gap, hook critique, publishing kit, performance review | `01-trend-board.md`, `07-publish-kit.md` |
| **researcher** | Unique angle aur detailing: verified facts, wow details, era-accurate visual and sound details, myth vs record | `02-research.md`, `FACTS.md` |
| **writer** | Viral script: hooks, holds, open loops, suspense, cliffhangers, loop endings, A/B hooks, retention map | `04-script/SCRIPT_vN.md`, `dialogue-lock.md` |
| **director** | Style, aspect, duration, flow; then production from style frame to edit, mix, QC and final files | `03-format.md`, the film, `06-qc.md`, `final/` |
| **mann** | Editor for the owner's raw footage: storyboard first, then cut, motion graphics, sound design, colour, VFX, QC; style lab and learned rules (`/mann-edit`, `/mann-style-lab`) | `edit/edl.json`, `edit/storyboard/`, `edit/renders/`, `editor/styles/` |

The orchestrator (the main session, running `/viral-studio`) runs the agents, passes the files between them and stops at the owner's gates.

## Flow

```
owner's ask ─► social: trend board + 3 pitches ─► [Gate 1: pick, or "khud chuno"]
                         │
         ┌───────────────┴───────────────┐
   researcher: research + FACTS     director: format brief (style, 9:16/16:9, duration)
         └───────────────┬───────────────┘
                writer: script v1 (hooks, retention map)
                         │
         director (flow) + social (hooks) critique ─► writer: v2
                         │
            [Gate 2: owner approves script + format]   ◄── nothing is produced before this
                         │
   director: 3 frames at 3 timecodes + a 20–30 s music sketch
                         │
            [Gate 3: owner approves look + music]       ◄── full production only after this
                         │
   director: voice → music → SFX → picture → edit → mix → QC → final/ + editor/ (NLE)
                         │
            [Gate 4: owner approves the final cut] ─► social: publishing kit
                         │
            studio-learn: owner feedback → studio/LEARNINGS.md
```

## Use it

- `/viral-studio`: scan what is trending and pitch three ideas.
- `/viral-studio <topic>`: skip the scan and make a film on the topic.
- `/viral-studio khud chuno`: the team picks the top pitch and goes as far as the script gate.
- Call one agent directly when you need only that job ("social se trending topics nikalo", "director se is script ka flow check karao").
- Feedback of any kind ("ye hook weak hai", "aisa SFX mat lagana") is recorded by `/studio-learn` in `studio/LEARNINGS.md`, and every agent reads it before it works.

## Editor package (NLE corrections)

Every finished film comes with `final/editor/`, a timeline the owner opens in **Premiere Pro or DaVinci Resolve** (Final Cut Pro 7 XML) to make small corrections: a trim, the shot order, a level, a line's timing, a subtitle.

- V1: the picture cut at the shot boundaries, textless when the film burns in subtitles.
- One stereo track per stem: each VO line as its own clip, each music stem, SFX/foley and ambience. The stems are post-fader and pre-master, so at 0 dB they play the final mix before the loudness step.
- A marker on every VO line (with its words) and on every sync point; `timeline.csv` lists every timecode; the subtitles come as `.srt`.
- The director builds it with `python3 studio/editor_package.py <film>/editor.json projects/<slug>/final/editor`. The manifest format is in the script's docstring, and there is a template in `studio/templates/editor.json`.
  - `--codec prores` gives ProRes 422 HQ instead of H.264.
  - `--crf 18` (instead of the default 16) is still visually lossless and about a third smaller. Use it when the package must fit a 400 MB upload.
  - `--media-root <folder>` writes the owner's own media path, so nothing needs relinking.
- **Delivery is always 2 files** (owner rule): the final video, and one zip with everything else. `python3 studio/deliver.py projects/<slug>/final --video <final video>` makes them and refuses a file over 400 MiB.
- Limits:
  - there are no handles beyond the shot edges
  - the animation is baked into the picture
  - the music ducking is baked into the stems
  - new words go back through the writer

## Ready formats (imported skills)

The owner's Ai-Animation repo brought 47 format skills, listed in `studio/IMPORTED_SKILLS.json` and under "Ready formats" in `STYLE_MENU.md`. They include `/madhubani-kahani`, `/katha-video`, `/lyric-video`, `/hindi-lyric-video`, `/anime-reel`, `/talking-head-edit`, 27 more reel edits, effects and looks, and `daksh-ai` with its own engine.

- **Calling them:** call one directly ("`/madhubani-kahani kahani.mp3`"), or let the director pick one as the format.
- **Running them:** every one runs inside [`SKILL_HARNESS.md`](SKILL_HARNESS.md):
  - where the words come from, and the script gate when the skill writes them
  - 3 preview frames and the music sketch before the render
  - rights checks for songs and other people's recordings
  - no real logos
  - sourced facts
  - the 2-file delivery
- **Before a production:** `python3 studio/check_env.py` shows what works in the session.
- **Rendering:** `node studio/render_canvas.cjs` renders any canvas page locally, and its `--stills` option makes the Gate 3 preview frames. `daksh-ai`'s template rendered end to end with it on 2026-11-02.
- **Word timing:** `studio/word_timing.py` aligns known words (a script, lyrics, the locked dialogue) offline. On Kokoro speech, line starts were within 20 ms and 90 % of word starts within 17 ms (2026-11-02). Transcribing unknown speech still needs the owner to allow the Whisper or alignment hosts (see the harness).

## Format prompts

The 12 looks from the "12 Claude Video Formats" guide are saved in `studio/formats/` and listed under "Format prompts" in `STYLE_MENU.md`. They include kinetic typography, claymation, pixel art game, whiteboard sketch, 80s VHS, anime opening, comic book and liquid motion.

Each is one prompt line (`Format: <name>.`) for `studio/templates/format-prompt.md`, which writes a page that `studio/render_canvas.cjs` renders frame by frame. They have a first-try result in the guide, not in this repo.

## Rules that never bend
- No production before the owner approves the script (Gate 2), and none before the owner approves 3 timecode frames and the music sketch (Gate 3).
- Music gets special attention at every stage.
- Out-of-the-box experiments are allowed: every brief and script carries one bold option labelled `experiment`.
- Every night about 10:40 PM IST a scheduled task suggests 10 trending topics with a style for each (`studio/NIGHTLY.md`).
- No posting, scheduling or messaging on any platform. The owner publishes.
- No invented facts, trend numbers or sources.
- At most 3 agents run in parallel.

Project work lives in `projects/<slug>/` (git-ignored); the templates are in `studio/templates/`.
