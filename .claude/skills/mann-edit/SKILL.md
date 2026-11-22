---
name: mann-edit
argument-hint: "[raw files or folder] [script / direction]"
description: Edit the owner's raw footage into a finished video with Mann, the AI video editor agent. The smart engine analyses the footage and suggests styles and unique edits; the owner only finalises the style, locks the script and approves the storyboard; Mann does everything else (assets, cut, motion graphics, sound, colour, VFX, render, QC) and scopes corrections to the whole video or just one part. Use when the owner shares raw videos, clips or audio with a script or direction and asks to edit, cut, "video edit karo", "isko edit kro", re-edit, add motion graphics, fix sound or colour, or sends corrections on a cut.
---

# Mann edit: raw footage to final cut

You (the main session) coordinate; the **mann** agent (`.claude/agents/mann.md`) does the editing. If the session does not list the project agents, run `general-purpose` with "Read `.claude/agents/mann.md` and act as Mann".

## Start
1. Read `studio/LEARNINGS.md` (Global, Editor, Production) and `editor/rules.json`.
2. Pick a slug and create `projects/<slug>/edit/` (git-ignored). Save the owner's direction verbatim in `BRIEF.md` and any script in `SCRIPT.md`.
3. No script but narration or dialogue is needed: the script goes through `skills/ai-writer` and the owner's approval first (AGENTS.md script gate).
4. Talk to the owner in Hinglish. Do not ask about anything except the three decisions below.

## Flow

| Step | Who | Output |
|---|---|---|
| 1. Tools, ingest, transcribe, `assets` | Mann | `media.json`, `transcripts/`, `assets.json`, `analysis/` |
| 2. `suggest` | Mann (smart engine) | `SUGGESTIONS.md`: 3 styles, 1 `experiment`, unique ideas, hooks, problems |
| **Decision 1: style** | owner | `approve-style <edit> <slug> --words "..."` |
| **Decision 2: script lock** | owner | `lock-script <edit> SCRIPT.md --words "..."` (skip if there is no script) |
| 3. `autocut --style <slug>` + refinement | Mann | `edl.json` |
| 4. `storyboard` | Mann | numbered frames + `STORYBOARD.md` |
| **Decision 3: storyboard** | owner | `approve --words "..."` |
| 5. `render`, `qc` | Mann | `renders/master.mp4`, `preview_720p.mp4`, `QC.md` |
| 6. Deliver | you | preview + QC summary to the owner |
| Notes from the owner | Mann | scoped correction (below), `/studio-learn` in the same turn |

## Corrections: whole or part
- Run `status <edit>` after applying the owner's note. It says `whole`, `part` (with the clip ids) or `none`.
- **Whole** (style, grade, music, captions look, format, order): full `storyboard`, show it, `approve --words`, `render`.
- **Part**: `storyboard --changed` and `preview-part --clips <ids>`; show the owner only that part (frames and the short video); `approve --clips <ids> --words "..."`; `render`. Approved parts stay as they were.

## Showing the owner
- Frames one by one with SendUserFile, numbered, each captioned with its timecode, clip and what happens. Never one dense contact sheet (owner rule).
- A compact Hinglish packet: length, shots, average shot, grade, music/SFX plan, motion graphics, captions, changes since the last version, and one `experiment`.
- Then stop. Only the owner's explicit words open the next step; the tool enforces it.

## Deliver
Tell the owner, in Hinglish: where the files are (`renders/`), what QC passed, what failed and what could not be checked, and the learnings recorded. Send exactly 2 files with SendUserFile, the ones `python3 studio/deliver.py <edit>/renders --video <the final render>` prints: the final video, and one zip with everything else (owner rule, 2026-11-02). Never upload or publish.
