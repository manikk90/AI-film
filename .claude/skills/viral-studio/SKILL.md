---
name: viral-studio
argument-hint: "[topic | khud chuno]"
description: Run the viral video studio end to end - find what is trending, research it, decide style/format/duration, get the script written and approved, then make the film and its publishing kit - by coordinating the social, researcher, writer and director agents. Use when the owner asks for a viral video, a trending-topic film, "viral chije dhundo", a new short or episode, or names a topic to turn into a video.
---

# Viral studio: the coordinated pipeline

You are the orchestrator, the producer. The four specialists are subagents in `.claude/agents/`: **social**, **researcher**, **writer** and **director**. By design the studio has one coordinator: the specialists do not start each other (the writer, social and researcher agents have no Agent tool, and the director disallows it), so **you** run them, pass their files to each other, keep `STATUS.md` current and stop at the owner's gates. You do not write the script yourself.

## Start every run
1. Read `studio/LEARNINGS.md` (all sections; the newest rule wins) and `studio/PROFILE.md`. Follow caveman mode (below); open `studio/README.md` only for a tool you need.
2. Create `projects/<slug>/` (git-ignored). Copy in `studio/templates/STATUS.md` and `studio/templates/00-brief.md`, then fill in the brief from the owner's request. Infer whatever the request implies; leave the rest at the profile defaults.
3. Talk to the owner in Hinglish. Do not ask about routine choices. The gates below are the owner's explicit rules, not optional permission questions.
4. **Auto mode:** if the owner said "auto" (this run) or "hamesha auto" (standing), do not stop at Gate 1–4 below. Take the recommended option at each, with the per-gate rules in `studio/README.md` → "Auto mode" (Gate 2 needs a clean critique round; Gate 4 needs a clean `06-qc.md`). Your own choice there satisfies "only after the owner approves" wherever it appears below or in `writer.md`/`director.md`. Log one line to `STATUS.md` as `auto-approved`, not the full packet, and give one chat line, then continue. A message the owner actually sends mid-run still overrides it.

## The flow

| Stage | Who | Output | Runs in parallel with |
|---|---|---|---|
| 1. Trend scan + pitches | social | `01-trend-board.md` | skipped when the owner gave a topic (then only the competition scan runs) |
| **Gate 1: pick** | owner | the chosen pitch | skipped if the owner said "khud chuno" or gave a topic; then take the top-ranked pitch and say so |
| 2. Research | researcher | `02-research.md`, `FACTS.md` | stage 3 |
| 3. Format brief | director | `03-format.md` (style, aspect, duration, pace, first frame, voice, music) | stage 2 |
| 4. Script | writer | `04-script/SCRIPT_v1.md` (hooks, retention map, full script) | – |
| 5. Critique | director (flow, feasibility, timing) + social (hooks, shareability) | numbered fixes | each other |
| 6. Revision | writer | `SCRIPT_v2.md` (you `cp` v1 first; the writer edits it in place) + change list | – |
| **Gate 2: approve script + format** | owner | an explicit "approved" | **mandatory** (see `skills/ai-writer/SKILL.md`) |
| 7. Preview | director | **3 frames at 3 timecodes** (hook ≈ 0:01, the turn or midpoint, the climax or ending), rendered with the real code at the final aspect, plus a 20–30 s **music sketch** | – |
| **Gate 3: approve look + music** | owner | an explicit "approved" or notes | **mandatory**. Send the frames as individual numbered images, each captioned with its timecode, what happens and the line spoken; send the music sketch as audio |
| 8. Production | director | the film: voice → music → SFX → picture → edit → mix → QC, plus the editor package (`final/editor/`) | – |
| **Gate 4: final cut** | owner | approval or notes; small fixes the owner can make directly in the editor package (Premiere Pro or DaVinci Resolve) | mandatory before the publish kit is called final |
| 9. Publishing kit | social | `07-publish-kit.md` | – |
| 10. Learn | you | updates to `studio/LEARNINGS.md` | – |

At Gate 2, show the owner one compact packet:
- the topic and why now
- the unique angle and the top 5 research details
- the recommended style, aspect and duration
- 3 hook variants
- the full script with timings
- the retention map
- the risks

Keep it to 30 lines in chat; the full packet stays in the file. Then **stop**. Silence or a question about the packet is not approval. On approval, write `04-script/dialogue-lock.md` and `DIGEST.md` (at most 4 KB: locked line IDs, format decisions, timeline and cues, FACTS rows in use, open requests); production reads these first. On notes, send them to the writer (and to the director if they touch the format), produce version N+1 with a change list, and show it again.

## Caveman mode (owner rule, 2026-11-07: minimum tokens)
Full rules and measured numbers: `studio/CAVEMAN.md`. For you:
- **One session per film.** Start each new film in a fresh session, but never move a film in progress: `projects/` is git-ignored, and a new cloud session is a new container without it. To shrink the context mid-film, the owner runs `/compact`. Your own context was the biggest cost on 2026-11-07: 274 requests sent 118M tokens, with the context peaking at 900k.
- **Effort:** `/effort high` is enough to coordinate; the agents carry their own `effort` in their frontmatter.
- **Agents:** resume one (SendMessage) only for a small follow-up. For a new job, start a fresh agent with paths: a resumed agent re-sends its whole old context.
- **Critique:** one round, then one revision.
- **Status:** one line per phase to the owner, and no recaps.
- **After the film:** run `python3 studio/caveman.py usage` and put the totals in `STATUS.md` (stage 10).

## The owner's standing rules for every run
- **Music gets special attention** at every stage:
  - social notes the sound trends
  - the researcher finds authentic instruments and forms
  - the writer writes the music cues
  - the director writes a music brief, makes a music sketch for Gate 3, and checks every sync point in the final score
- **Out-of-the-box experiments are allowed.** Every format brief and script packet carries one bold option labelled `experiment` beside the safe recommendation; the owner decides.
- **Ready formats.** The 47 skills imported from the owner's Ai-Animation repo (`studio/IMPORTED_SKILLS.json`, listed under "Ready formats" in `studio/STYLE_MENU.md`) are formats like any style. Examples are `/madhubani-kahani`, `/katha-video`, `/lyric-video` and `/talking-head-edit`.
  - When the director or the social agent picks one, it runs inside `studio/SKILL_HARNESS.md`, with every gate above.
  - The owner can also call one directly; it still runs inside the harness.
- **The nightly scan** (`studio/NIGHTLY.md`) runs automatically every night and suggests 10 topics with a style for each. When the owner replies with a pick ("/viral-studio #N"), start at stage 2 with that topic.

## How to run each agent
- Use the Agent tool with `subagent_type` set to the agent's name. If a session does not list the project agents yet, use `general-purpose` with the prompt "Read `.claude/agents/<name>.md` and act as that agent".
- Brief each one in at most 15 lines: the project folder path, the exact task (for example "Job 2: hook critique on SCRIPT_v1.md"), the files and sections to read, the file to write, its budget and a 10-line handback. Never paste file contents. Each agent reads `studio/LEARNINGS.md` itself.
- **Run at most 3 agents at a time.** Seven in parallel exhausted the owner's 5-hour usage limit on 2026-11-01. Run in parallel only the stages marked as parallel above.
- After each stage, read the handback, run `python3 studio/caveman.py check projects/<slug>`, and open only the sections of the output file you need. Check it against the agent's checklist, update `STATUS.md` (stage, version, gate state, open issues), and send it back once if it misses the brief.

## Coordination rules
- **Files are the handoff.** Each stage reads the earlier files. Nobody relies on another agent's chat summary.
- Use the owner's handoff fields where they apply: project, request, source revision, approved locks, visible characters, visible props, offscreen audio, target language, output format, duration, owner, acceptance checks, unresolved dependencies, artifact paths, QC result.
- **Locks win.** Approved words (`dialogue-lock.md`), the approved style and format, and the owner's explicit rules in `LEARNINGS.md` are changed only by the owner.
- **Facts flow one way:** researcher → `FACTS.md` → writer. If the writer or director needs a new fact, it goes back to the researcher.
- **Never publish, schedule, post or message on any platform.** The owner publishes.

## Learn as you go (self-learning)
- Whenever the owner corrects, praises, rejects or states a preference, run the `studio-learn` skill in the same turn, before continuing the task.
- At the end of a run, collect the agents' proposed learnings. Record only the ones the owner's words or real results support. Mark the rest as proposals in `STATUS.md`.
- When the owner shares performance numbers, run social Job 4, then `studio-learn`.

## Deliver (at the end of a run)
Tell the owner, in Hinglish:
- where the final files are
- the editor package (`final/editor/`) for small corrections in Premiere Pro or DaVinci Resolve
- what was checked and what could not be checked
- the publishing kit
- the learnings that were recorded

Send exactly 2 files with SendUserFile (owner rule, 2026-11-02), the ones `studio/deliver.py` prints:
- the final video
- one zip with everything else: the editor package, subtitles, cover, credits and the QC note
