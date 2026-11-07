# Caveman mode: the studio's token diet

Owner rule, 2026-11-07: "koi bhi movie bnate time ya video m ye kaafi token use krta h caveman techniques use kro or token usages optimize kro minimum usages tk".

Every studio agent (social, researcher, writer, director, Mann) and the orchestrator follow this file on every film and video. The technique comes from [caveman](https://github.com/JuliusBrussee/caveman) (Apache-2.0) and its 6-line [caveman-micro](https://github.com/kuba-guzik/caveman-micro) (MIT): terse writing, every fact kept. The wording and the tool here are our own; no code was copied.

## Where the tokens went (measured)

`python3 studio/caveman.py usage` on the session that made the Ramayana film, the skill import and naraz-fufa up to Gate 2 (2026-11-01 to 11-07):

| Run | Requests | Context sent | Peak context | Output | Effort |
|---|---|---|---|---|---|
| Main session (orchestrator) | 274 | 118.2M | 900k | 559k | max |
| director: format brief + critique | 60 | 17.0M | 555k | 285k | max |
| writer: script v1 + v2 | 35 | 7.7M | 416k | 412k | max |
| social: trend scan | 20 | 2.6M | 297k | 147k | max |
| researcher: research | 27 | 2.5M | 209k | 113k | max |
| social: hook critique | 15 | 1.7M | 240k | 123k | max |
| researcher: verse source | 16 | 1.2M | 132k | 71k | max |
| **Total** | 447 | 150.9M | | 1.7M | |

"Context sent" adds up the whole context of every request. Cache reads are in it, and they cost less than fresh tokens. Output includes thinking.

What made it big:
1. **Every request re-sends the whole context.** A big context times many requests is the main cost: 60 director requests averaged 283k tokens each.
2. **One long main session.** It ran for a week, and its context peaked at 900k.
3. **Whole-file reads of big files:**
   - `03-format.md` (47 KB), `SCRIPT_v1.md` and `SCRIPT_v2.md` (52 and 62 KB)
   - the two critiques (22 and 38 KB), `02-research.md` and `FACTS.md` (37 KB each)
   - `STYLE_MENU.md` (47 KB) and the trend board (66 KB)
   - Every downstream agent read them again.
4. **Max effort everywhere.** The writer spent 412k output tokens on about 114 KB of script files.
5. **Resumed agents** carried their whole old context into the next job.

## The rules

### 1. Write like a smart caveman
- No filler, pleasantries, hedging, recap or closing offer. Fragments are fine. Use short words.
- Keep these exact:
  - not, never, no, only
  - numbers, units, dates, names, paths, commands, code and quotes
  - the locked script words and the `FACTS.md` wording
- Internal files and handbacks are in English. Devanagari only for the exact words that go on screen or into the voice: it costs more tokens per word than Roman text.
- The owner's packets and messages: short, plain Hinglish. Gate questions, safety and legal warnings, and anything irreversible get full sentences.

### 2. Read less
- **Learnings:** read Global plus your own sections only. `python3 studio/caveman.py rules <role>` prints them; without Bash, Grep `^## ` with line numbers and Read that range.
- **Files over 16 KB:** read the heading index first (`caveman.py index FILE`, or Grep `^#`), then only the sections you need (`caveman.py section FILE "Heading"`, or Read with offset and limit).
- Never re-read a file that is already in context.
- `STYLE_MENU.md` and the Lemo-Opuscar docs: search them, then read only what matches.

### 3. Write less: budgets
`python3 studio/caveman.py check projects/<slug>` lists every file over its budget and exits 1. Budgets are for a short of up to 60 s; long form uses `--scale 4`.

| File | KB | Shape |
|---|---|---|
| `00-brief.md` | 3 | |
| `01-trend-board.md` | 10 | one table row per pitch, plus sources |
| `02-research.md` | 10 | angle, detail bank, sources |
| `FACTS.md` | 8 | one table row per fact: ID, claim, source, confidence, use |
| `03-format.md` | 10 | |
| `04-script/SCRIPT*.md` | 14 | |
| `04-script/dialogue-lock.md` | 3 | |
| `05-critique-*.md` | 5 | numbered fixes, one or two lines each |
| `DIGEST.md` | 4 | the production brief, written at Gate 2 |
| `STATUS.md` | 8 | |
| `06-qc.md`, `07-publish-kit.md` | 8 each | |

- Refer to facts by ID (`F17`) and to lines by ID (`L3`, `T19`). Never paste one file's text into another.
- A revision changes the file in place. The orchestrator copies the old version first (`cp SCRIPT_v1.md SCRIPT_v2.md`); the agent Edits only the changed lines and adds one change-list line per fix. Never re-Write a whole file to change part of it.

### 4. Fewer, smaller requests
- Batch independent reads, searches and checks in one turn.
- **Web:** at most 8 searches per job (15 for a trend scan). Use WebFetch with a narrow question, and never search again for what `FACTS.md` already has.
- **Tool output:**
  - Cap it: `| tail -n 20` or `| head -c 4000`.
  - FFmpeg: `-hide_banner -loglevel error -nostats`. ffprobe: only the fields you need, with `-of csv=p=0`.
  - Tests: run without `-v`, then re-run only the failing test.
  - Never print JSON dumps, base64, frame lists or whole logs.
- **Images:** an image costs about width × height / 750 tokens: a full 1080×1920 frame is about 2,800. Check a contact sheet at most 1024 px on its long side (about 800 tokens), not single frames.

### 5. Effort and context per agent
Set in each agent's frontmatter. The Agent tool's `effort` parameter overrides it for one job, only when the owner asks.

| Agent | `effort` | `autoCompactWindow` |
|---|---|---|
| social | medium | 100000 |
| researcher | medium | 100000 |
| writer | high | 150000 |
| director | high | 200000 |
| mann | high | 200000 |

- `autoCompactWindow` needs Claude Code v2.1.296 or later; older versions ignore the field.
- The `CLAUDE_CODE_EFFORT_LEVEL` environment variable overrides every agent's setting, so leave it unset.

### 6. The orchestrator (main session)
- **One session per film, start to finish.** Start each new film in a fresh session. Never move a film in progress to a new session: `projects/` is git-ignored, and a new cloud session is a new container without it. When the context grows (`/context` shows it), run `/compact` in the same session; the files stay on disk.
- **Effort:** `/effort high` is enough to coordinate. Use `max` only when the owner asks.
- **Agent prompts:** at most 15 lines: the task, the paths, the sections to read, the budget and the handback format. Never paste file contents into a prompt.
- **Fresh or resumed:** resume an agent (SendMessage) only for a small follow-up. For a new job, start a fresh agent with paths: a resumed agent sends its whole old context with every request.
- **Critique:** one round. The director and the social agent run in parallel, each writing at most 5 KB of numbered fixes. Then one revision.
- **Check output:** read the handback, run `caveman.py check`, and open sections of the agent's file only when needed.
- **At Gate 2 approval:** write `04-script/dialogue-lock.md` and `DIGEST.md`. `DIGEST.md` holds:
  - the locked line IDs
  - the format decisions
  - the timeline and cue points
  - the `FACTS.md` rows in use
  - the open requests

  Production reads `DIGEST.md` first and opens the long files only by section.
- **Owner messages:** a gate packet is at most 30 lines in chat; the full packet stays in the file. Give one status line per phase.
- **After each film:** run `python3 studio/caveman.py usage` and note the totals in `STATUS.md` (stage 10, Learn), so the next film can be compared.

## The agent block
Every studio agent file ends with this block, word for word. `tests/test_caveman.py` keeps the copies identical.

<!-- caveman -->
## Caveman mode (owner rule 2026-11-07: minimum tokens)
- Write terse: no filler, pleasantries, hedging or recap; fragments fine. Keep not/never/no/only, numbers, names, paths, code, quotes, locked words and FACTS wording exact.
- Internal files and handbacks in English. Devanagari only for exact on-screen or spoken words. Owner packets: short, plain Hinglish.
- Learnings: Global plus your own sections only (`python3 studio/caveman.py rules <role>`, or Grep `^## ` and Read that range).
- Files over 16 KB: heading index first (`caveman.py index`, or Grep `^#`), then read only the sections you need. Never re-read what is in context.
- Batch independent reads and searches in one turn: every request re-sends your whole context. Web: 8 searches per job (trend scan 15).
- Revise in place: Edit only the changed lines. Never re-Write a whole file to change part of it.
- Cap tool output (`| tail -n 20`, ffmpeg `-hide_banner -loglevel error -nostats`, tests without `-v`). Images: one contact sheet, 1024 px long side at most.
- Stay inside your file's budget in `studio/CAVEMAN.md` (`python3 studio/caveman.py check projects/<slug>`).
- Handback: 10 lines at most (paths, decisions, open questions). Details live in the files.
<!-- /caveman -->
