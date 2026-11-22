---
name: studio-learn
description: Record the owner's feedback, preferences, corrections, approvals and shared performance results as dated, scoped rules in studio/LEARNINGS.md, so the social, researcher, writer, director and Mann (editor) agents follow them next time. Use whenever the owner says something like "aisa mat karo", "ye pasand aaya", "hamesha...", "kabhi bhi...", "ye bekar hai", approves or rejects a direction, or shares views/retention numbers.
---

# Studio learning: keep the agents updated

The owner's instruction (2026-11-01): "jo jo chije batata jau usko update krte jao." Every piece of feedback becomes a rule the studio follows from then on.

## Steps
1. **Capture the exact words.** Quote the owner (Hinglish is fine) and note the date and the project.
2. **Turn it into a rule.** Write it as an imperative an agent can follow, plus *why*: "Do X / never Y, because Z."
3. **Scope it** to one section:
   - **Global**
   - **Social**
   - **Research**
   - **Writer**
   - **Director**
   - **Editor** (Mann: cutting, motion graphics, sound design, colour, VFX, style sheets)
   - **Marich** (reverse engineering under Daksh)
   - **Production** (voice, music, SFX, render)
   - **Project: <slug>**, for anything that only holds for one film

   Never turn a fix for one shot or one film into a global rule unless the owner said "hamesha" (always) or the same correction has come up twice.
4. **Check for conflicts.** If an older rule disagrees, keep it, prefix it with `~~superseded YYYY-MM-DD~~`, and add the new rule. The newest explicit instruction wins.
5. **Kinds:**
   - `owner` (the owner said it)
   - `result` (real performance numbers)
   - `observed` (a check we ran)

   Agent proposals without owner backing do not go in; they stay in the project's `STATUS.md`.
6. **Write** the entry under its section in `studio/LEARNINGS.md`:
   `- YYYY-MM-DD · kind · rule. Why: … Source: "<owner's words>" (project)`
7. **Editor rules that can be measured** (loudness, dead air, shot length, hook timing, subtitles, pace) also go into `editor/rules.json`: change or add the threshold under `rules` and append a `history` entry `{date, rule, value, kind, source}` quoting the owner. Mann's `qc` enforces these from the next render. If a style sheet was wrong, fix `editor/styles/<slug>/STYLE_SHEET.md` too.
8. **Save it.** Run `python3 -m unittest tests.test_studio tests.test_editor`. Then commit only `studio/LEARNINGS.md` (and `editor/rules.json` or the style sheet when they changed), with the message `studio: learn - <short rule>`, on a work branch (never the default branch), push it and open a PR; it merges once CI is green (owner rule, 2026-11-08: PR auto-merge).
9. **Confirm** to the owner in one line which rule was recorded, then continue the task with the new rule applied.

## Never
- Never record secrets, API keys, private numbers or personal data in the ledger.
- Never let a learning remove a safety rule: no posting without the owner, no invented facts, the script approval gate.
