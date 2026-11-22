---
name: ai-writer
description: Write the story, screenplay or narration for a film through a dedicated writer agent, and stop at a script approval gate before any voice, music, picture or render work starts.
---

# AI Writer and the script approval gate

Adapted from the owner's AI Writer agent dossier (reconstructed documentation dated 2026-11-01; the original installed skill was not available). The owner's rule: the director never writes the script itself. The script is written by the writer, shown to the owner, and **production starts only after explicit approval**.

## When this runs

- Any new film, short, promo, explainer or episode for which the owner has not supplied a finished screenplay or narration. This includes code-rendered films, such as those made with the Lemo-Opuscar style library.
- Any later change to approved words (a new line, a cut, a rewrite) goes back through this skill as a revision and needs approval again.
- A screenplay supplied by the owner is not rewritten. Use [screenplay-breakdown](../screenplay-breakdown/SKILL.md) instead, and propose any change here as a revision.

## Who writes

Run the writer as a **separate agent** with this skill as its brief, not inline in the director's own turn. Give it the topic, length, language, audience, style or medium constraints, known facts and sources, and any owner locks. A second, independent agent then critiques the draft against the checklist below. The writer revises once before anything is shown to the owner.

## Workflow

Brief → theme and audience → the character's goal and motivation → conflict and emotional stakes → sequence beats → scene outline → screenplay or narration → dialogue pass → continuity and fact pass → script packet → **approval gate** → production handoff.

Keep three lists apart: approved canon, proposed alternatives and rejected ideas.

## Craft rules

- **Every beat** has a point of view, an immediate objective, opposition, a change, and a hook or reveal where one is relevant.
- **Narration adds what the picture can't show:** a feeling, a history, a stake, a question. It never describes what is already on screen ("the lamps are lit" over a shot of lamps being lit).
- **No plot summary.** A list of events ("X happened, then Y happened") is a synopsis, not a script. Choose a point of view, a voice with a personality and one emotional line, and cut every event that doesn't serve it.
- **Spoken language, written to be heard.** Hindi and Hinglish should sound like a real storyteller, a grandmother or a narrator people would listen to. It must not read like a translated document. Use short breath-sized phrases, deliberate repetition, and direct address where it fits.
- **Concrete images over abstractions.** "One lamp, then two" beats "the city was filled with light".
- **Give the ending a turn or an echo:** a line that only lands because of something set up earlier.
- **Miracles and myths:** tie them to emotional or moral stakes, not random fixes. Name a variant of a myth or tradition when it is one ("in the version told at Diwali…"). Keep devotional material respectful.
- **Regional dialogue:** use meaningful local rhythm, age, status and situation, never decorative dialect.
- **Real events:** every factual claim is sourced in a `FACTS.md`, or marked as uncertain and kept out of the script.
- **Timing:** Hindi narration runs at about 2–2.5 words per second, English at about 2.5. Every line gets a time slot, with silences and music-only moments written into the script. Subtitle lines stay at most about 45 characters each, and a long sentence is split at a natural pause.
- **Visible entities:** never add a character or prop to a scene unless it truly appears or is heard.

## The script packet (what the owner approves)

Save it where the caller says. In a `/viral-studio` run that is `04-script/SCRIPT_v<N>.md`; standalone, also use `04-script/` in the project folder. Show it in chat:

1. **Logline** (one sentence), **theme**, **audience**, **length**, **language**, **voice** (who is speaking, and how).
2. **Two or three approaches**, a few lines each, with a recommendation and the reason for it.
3. **Beat sheet with timings:** for each beat, what we see (one line), what we hear (voice, music, silence), and the emotional change.
4. **The full script:** every spoken word in final form, numbered (`L1`, `L2`…), with its time slot and a delivery note. On-screen text and subtitles are listed separately.
5. **Facts and sources** (for real events), and any tradition or variant choices.
6. **Open questions:** only those whose answer would change the script.
7. For a revision: **what changed**, and what stays locked.

## Approval gate

- After presenting the packet, **stop**. Do not generate voice, music, picture, stills, storyboards, renders or uploads.
- Only an explicit approval from the owner opens the gate ("approved", "haan, ye theek hai, banao", or similar). Silence, "dekhte hain", or a question about the script is not approval.
- Auto mode exception: when the owner said "auto" or "hamesha auto", the orchestrator's logged `auto-approved` line in `STATUS.md` for Gate 2 counts as that approval, and only for a clean critique round (`studio/README.md` → "Auto mode"). Never for rights, facts, real people or publishing.
- On feedback, the writer revises. Show version N+1 with a change list, and wait again.
- Once the script is approved, the orchestrator records the exact words in `04-script/dialogue-lock.md` (with the version and the date). Voice, subtitles and timing then use those words unchanged. If production shows that a line has to change (for example, it is too long for its shot), take the change back to the writer and to the owner. Never edit it silently.

## Handoff

Pass on the approved script version, `dialogue-lock.md`, the beat timings, visible characters and props per beat, offscreen voices, the target language and any open dependencies. A handoff is not proof that a downstream step ran.

## Acceptance checklist

- [ ] Correct task, output and scope; owner locks honoured
- [ ] Written by the writer agent and critiqued by an independent agent
- [ ] Every craft rule above checked: no synopsis, no narrating the picture, spoken-language voice, a turn or echo at the end
- [ ] Facts sourced, or kept out of the script
- [ ] Timings fit the length; subtitles are splittable
- [ ] Packet shown to the owner and **explicit approval received** before any production step
