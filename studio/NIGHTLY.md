# Nightly topic scan

Every night a scheduled task ("Nightly viral topic scan", around 10:40 PM IST) starts a fresh session. That session clones this repository and follows this file: it finds **10 topics** with viral potential for the owner and suggests the **best style** for each. The owner asked for this on 2026-11-01: "roj raat 11 bje automatically 10 topics dundne or mujhe suggest krne h or unpr konsa style acha rhega vo bhi. virality match krte hue".

The run only suggests. It does not research deeply, write scripts, start production or post anything. When the owner picks a topic, the normal `/viral-studio` flow starts in a session.

## Steps

1. **Read** `studio/LEARNINGS.md` (every section; the newest rule wins), `studio/PROFILE.md`, `.claude/agents/social.md` (Job 1 rules) and `studio/STYLE_MENU.md`.
2. **Search** with WebSearch, at most 15 queries (the caveman cap for a trend scan), several per turn, `standard` first and `extended` for freshness:
   - what is trending in India in the last 24–72 h (Google Trends India, YouTube trending and Shorts, Reels formats, X India, top news)
   - film, OTT and cricket events this week
   - the festival and observance calendar for the next 14–30 days, with dates from a source
   - evergreen themes that fit the profile
3. **Apply social Job 1:**
   - Every topic gets dated evidence: a URL and a date.
   - No invented numbers.
   - Safety is a gate: drop tragedy exploitation, communal or political bait, misinformation, and anything that needs someone else's footage or music.
   - Score with the social agent's rubric (out of 55).
4. **Match a style to each topic** from `studio/STYLE_MENU.md`:
   - **Best fit:** the style whose look, mood and native moves serve the topic and its emotion. Prefer a library style (it has a demo engine, so it is faster and safer). A draft style is fine when it is clearly better; mark it `draft`.
   - **Out-of-the-box option:** one bold alternative (a style mashup, an unexpected medium, an unusual point of view), marked `experiment`. The owner allows experiments.
   - **Why:** one line.
5. **Write the report** to `projects/nightly/YYYY-MM-DD.md` in the clone (not committed). Your final message is the same report in Hinglish, short enough to read on a phone.

## Report format (the final message)

```
Aaj ke 10 topics (DD Mon YYYY): top 3 pehle

1. <Title idea> · score NN/55 · lifespan <hours/days/evergreen>
   Hook: "<Hinglish hook line>"
   Kyun abhi: <one line> (<source, date>)
   Style: <best style> (`slug`, library/draft) · Experiment: <bold option> (`slug`)
   Format: <9:16 Reels/Shorts, NN s; a story film at least 2 min> · Music: <one line: mood, instruments>
   Risk: <one line, or "none">
...
10. ...

Mera pick: #N, kyunki <one line>.
Experiment pick: #N, kyunki <one line>.
Shuru karne ke liye: "/viral-studio #N" likho.
Verify nahi ho paaya: <blocked sites, unconfirmed dates>
```

## Rules
- Never post, schedule, comment or message on any platform.
- Never put secrets or personal data in the report.
- If a search source is blocked, say so in "Verify nahi ho paaya". Never guess in its place.
- Skip topics the owner has rejected in `studio/LEARNINGS.md`.
