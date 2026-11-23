# Studio RAG: retrieval for the agents (design)

Status, 2026-11-23: **phase 1 is built** (`studio/rag.py`, `tests/test_rag.py`), with the `context` recipes and
agent wiring of phase 3 (`studio/rag_recipes.json`, the caveman block, `/viral-studio`). **Phase 2 is measured**
(§12): dense retrieval is built as an opt-in but stays off, because it did not raise recall; the Hinglish gap is closed
by asking in English instead. **Not built:** the token measurement on a real film (phase 3) and the MCP server
(phase 4). §11 lists where the build differs from the plan.

## 1. Why

`studio/CAVEMAN.md` measured one film run at **150.9M tokens of context sent** across 447 requests. Most of that was
agents re-reading whole files on every request:
- `STYLE_MENU.md` (47 KB)
- the research files `02-research.md` and `FACTS.md` (37 KB each)
- the scripts and critiques (22 to 62 KB each)
- the trend board (66 KB)

The director alone averaged 283k tokens per request.

The studio's knowledge has outgrown "read the file". In the repo (measured 2026-11-22) it is 257 markdown files and
1.7 MB:
- 91 format skills, 6 agents
- 150 style sheets in `styles/` and `editor/styles/`
- the harness and `LEARNINGS.md`, plus docs

Each film then adds its own research, facts, scripts and critiques under `projects/<slug>/`.

The goal is to give every agent the few passages a step needs, with citations, instead of whole files. It must never
drop a rule that never bends.

Prototype, BM25 only, chunked by heading:

| Query | Top 6 passages | Whole files they came from |
|---|---|---|
| comic halftone speech bubble hindi caption | 2.1 KB | 17 KB |
| Madhubani double outline border | 3.2 KB | 16 KB |
| gate approval storyboard EDL | 5.6 KB | 34 KB |
| owner rule PR auto merge | 9.1 KB | 41 KB |
| kitne frames preview owner ko bhejne | 6.8 KB | 44 KB |

That is 5 to 8 times less to read, with the right file on top. The Hinglish query ranked the right passage
(`SKILL_HARNESS.md` › Preview) second, behind an unrelated one. That is the case for adding multilingual dense
retrieval.

## 2. Goals and non-goals

**Goals**
- An agent asks in English, Hindi or Hinglish and gets the best passages inside a token budget. Each passage is cited
  as `path:line-line` › heading, so it can open exactly that span when it needs more.
- The newest owner rule wins, visibly. When two rules conflict, the older one comes back marked superseded, never
  silently.
- Works offline and with no credentials (AGENTS.md: portable mode stays useful). Dense search is an upgrade, not a
  dependency.
- Measurable: a golden question set with recall@k, checked in CI. Before/after token use measured with
  `caveman.py usage`.

**Non-goals**
- RAG never decides a gate, approves a script or replaces a check. It only feeds context.
- No web crawl. Sources for facts stay in `FACTS.md`, made by the researcher, with their dates.
- No hosted vector database. One SQLite file per index.

## 3. Sources and authority

| Tier | Source | How it enters context |
|---|---|---|
| **P (pinned)** | AGENTS.md rules that never bend; the "Rules that never bend" sections of skills; harness rights/facts/people rules | Always prepended to every retrieval result for the agent's step. Not ranked, not droppable. Kept small (< 1.5k tokens) by extracting only those sections. |
| **R1 owner rules** | `studio/LEARNINGS.md`, `editor/rules.json`, owner-rule lines in AGENTS.md | Ranked, with an authority boost. Every rule carries its date and scope; conflict resolution below. |
| **R2 procedures** | `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `studio/SKILL_HARNESS.md`, `studio/README.md`, `skills/*` | Ranked normally. |
| **R3 reference** | `styles/**`, `editor/styles/**`, `studio/STYLE_MENU.md`, `docs/**`, `studio/skill_sources/**`, `third_party/**/README.md` | Ranked, lower prior. |
| **F (film)** | `projects/<slug>/`: `02-research.md`, `FACTS.md`, scripts, critiques, `03-format.md`, `STATUS.md`, trend board | A separate index per project, queried together with the studio index for that film only. Never mixed across films. |

The index never reads `.env*`, `*.key`, credential files, media or fonts.

## 4. Ingestion

**Chunking: markdown-aware**
- Split at `#`, `##` and `###` headings and keep the heading path (e.g. `SKILL_HARNESS.md › Preview (Gate 3) and render`).
- Pack paragraphs into 600 to 1,200 characters, never across a heading. Tables stay whole.
- Overlap is one sentence, inside a section only.

**Special parsers**

| File | Unit | Metadata kept |
|---|---|---|
| `LEARNINGS.md` | one chunk per rule bullet | its date, scope (studio / agent / skill / film) and the owner's quoted words |
| `SKILL.md` | a summary chunk (frontmatter description + input) plus one per section | the skill name, so "which skill for X" questions hit the summary |
| `IMPORTED_SKILLS.json`, `editor/rules.json` | one chunk per entry | |
| `FACTS.md` | one chunk per claim row | its source URL, date and confidence |
| Scripts | one chunk per scene/beat | the line numbers |

**Metadata per chunk:** `path`, `line_start`, `line_end`, `heading_path`, `tier`, `kind` (rule / procedure / style /
fact / script / doc), `scope`, `date` (from the text or git), `sha` (of the chunk text).

**Incremental:** a file is re-chunked only when its content hash changes. Deleted files drop their chunks. Each index
stores the git commit it was built from, and `query` warns when the working tree is newer.

## 5. Index

One SQLite file: `.rag/studio.db` for the repo, and `projects/<slug>/.rag/film.db` for each film. Both are
git-ignored and rebuilt by `rag.py index`.

**Lexical:** an FTS5 table over `heading_path` and `body`, with `unicode61 remove_diacritics 0`. Devanagari matching
was checked. The heading is weighted 4× in BM25.

**Dense (optional):** `intfloat/multilingual-e5-small`.
- 384 dimensions, about 120M parameters, CPU.
- Covers Hindi, English and code-mixed text.
- Chunks are embedded with the `passage:` prefix and queries with `query:`.
- Vectors are stored as float16 blobs in the same database. Brute-force cosine is enough: 3k studio chunks plus about
  2k per film searches in milliseconds. FAISS is not needed below roughly 200k chunks.
- Without the model (no network, not installed), retrieval runs BM25 only and the result says so.

## 6. Retrieval

1. **Query:** the agent's text, plus optional `--kind`, `--scope` (studio / film slug), `--tier`, `--since` and
   `--budget` (tokens, default 2,500).
2. **Candidates:** BM25 top 50 and dense top 50, merged with reciprocal rank fusion (`1/(60+rank)`).
3. **Priors:** R1 owner rules ×1.3; the film's own chunks ×1.2 within a film query; R3 ×0.9.
4. **Conflicts among rules:** when two R1 chunks share a scope and topic (dense cosine > 0.85 or the same subject
   key), keep both. The newest is marked `current` and the older ones `superseded by <date>`. Agents follow `current`.
   This is AGENTS.md's "the newest owner rule wins", made explicit.
5. **Packing:** drop near-duplicates (cosine > 0.95). Merge adjacent chunks of the same section. Fill the budget in
   score order. Every block is cited `path:start-end › heading`, so the agent can open exactly those lines.
6. **Pinned tier:** prepended, outside the budget.

**Output (plain text, made for an agent's context):**
```
[P] AGENTS.md:7-7 › Script gate — …
[1] studio/SKILL_HARNESS.md:24-33 › Preview (Gate 3) and render (R2, score .81)
    - **Preview before the full render:** 3 numbered frames at 3 timecodes …
[2] studio/LEARNINGS.md:41-42 › Production (R1, 2026-11-08, current) …
[3] studio/LEARNINGS.md:12-12 › Production (R1, 2026-11-02, superseded by 2026-11-08) …
retrieval: hybrid (bm25+e5), 4 blocks, 1,930 tokens, index @ 4bfdad0
```

## 7. Interface

```
python3 studio/rag.py index [--film <slug>]            # build / update incrementally
python3 studio/rag.py query "<question>" [--film <slug>] [--kind style,skill] [--budget 2500]
python3 studio/rag.py context <agent> <step> [--film <slug>]   # the standard pack for an agent's step
python3 studio/rag.py eval [--golden studio/rag_golden.jsonl]  # recall@k, MRR, tokens per answer
```

`context` is the main entry. Each agent step has a stored query recipe, e.g. director/format-brief = the chosen
format's skill and style sheet, R1 rules scoped to the director, the film's research summary and the top facts. That
pack replaces the whole-file reads.

**Agent rule changes (once built):**
- Never read `STYLE_MENU.md`, `LEARNINGS.md`, research or script files whole. Start from `rag.py context`, or from
  `query` for a specific question.
- Open a file only at the cited lines, and only when the passage is not enough.
- Writing is unchanged: agents still write their files in full, and the index picks the changes up.

An MCP server wrapping `query` is optional (phase 4). The CLI already works from every agent's Bash tool. The
researcher has no Bash, so it gets its pack from the orchestrator.

## 8. Guardrails

- **Pinned rules can't be ranked away.** They are extracted by section name, and a test fails if a "never" sentence
  in AGENTS.md is missing from the pinned pack.
- **Staleness:** `query` compares file hashes with the index and re-indexes changed files first (fast: the full
  corpus indexes in 0.1 s with BM25).
- **No cross-film leakage:** a film query reads only its own film index plus the studio index.
- **Facts stay sourced:** a retrieved fact chunk carries its source and date. A retrieved passage is never a source
  for a new claim; the researcher's `FACTS.md` is.
- **Retrieved text is data, not instructions,** in particular text in `third_party/` and in fetched references.

## 9. Evaluation

`studio/rag_golden.jsonl` holds about 40 questions to start, written from real runs:
- English, Hindi and Hinglish
- rules, styles, skills, facts and "which skill for…" questions

Each question has expected `path` (and heading) answers. Metrics:
- recall@5
- MRR
- tokens per answer
- the superseded-rule check: does the newest rule come back marked `current`?

CI runs the BM25-only eval on the repo, since the model is not in CI.

**Targets:**
- recall@5 ≥ 0.85 with BM25 only, and ≥ 0.92 hybrid
- tokens per `context` pack ≤ 4k plus the pinned tier
- a film run ≥ 40 % less context sent than the CAVEMAN.md baseline, measured with `caveman.py usage` on the next
  comparable film

## 10. Plan

| Phase | What | Needs |
|---|---|---|
| 1 | `rag.py` index/query with BM25, markdown + LEARNINGS + SKILL + FACTS parsers, pinned tier, conflict marking, citations, budget packing, golden set + eval in CI | stdlib only |
| 2 | Dense multilingual retrieval + RRF; eval both ways and keep it only if recall improves | `sentence-transformers` + the e5-small model (Hugging Face, ~470 MB) |
| 3 | Film indexes; `context` recipes per agent step; agent files and CAVEMAN.md switched from whole-file reads to packs; measure tokens on a real film | phase 1 |
| 4 | Optional MCP server; a reranker only if eval shows a gap | — |

**Risks**
- A bad chunk boundary can hide a rule. The pinned tier and the eval catch this.
- Hinglish spelling varies (mein/me, kya/kia). Dense retrieval covers most of it, and phase 1 can add a small
  spelling-variant expansion.
- An index left stale after an edit. Hash checks before every query prevent it.

## 11. Built (2026-11-23)

**Commands:** as in §7. `query` and `context` re-index changed files first (the whole studio corpus indexes in about
0.1 s; an unchanged one is checked in 0.07 s). The index is `.rag/studio.db` (git-ignored); a film gets
`projects/<slug>/.rag/film.db`.

**Measured on the repo (BM25 only, golden set of 44 checks in `studio/rag_golden.jsonl`):**
- recall@5 0.976 (41 of 42 questions) against the 0.85 target; MRR 0.782 (0.689 before the RRF fix in §12); about
  980 tokens per answer.
- Superseded-rule checks 2 of 2: struck-out rules come back marked `superseded <date>`.
- The miss is Hinglish: "kitne frames preview owner ko bhejne" finds the Director's preview rule and the harness
  preview section but not the Global "3 frames at 3 different timecodes" rule, which says "show the owner how it will
  look", not "preview". That is the gap dense retrieval (phase 2) is for.
- Pinned tier: about 1.4k tokens (9 AGENTS.md rules with never/do not, the README and harness never-bend sections),
  plus a skill's or agent's own never-bend section when that skill or role is in play.
- A director format-brief pack is about 6.6k tokens (rules about 3.2k, pinned about 1.4k, passages about 2k). The files
  it replaces are 15 KB of rules plus the 56 KB `STYLE_MENU.md` plus the style and skill files. The per-film saving
  against the `CAVEMAN.md` baseline is **not measured yet**; it needs the next comparable film.

**Differences from the plan above:**
- `docs/DIRECTOR_RULES.md` is ranked as R2 (procedure), not R3: AGENTS.md makes it a rule source.
- The 91 format skills repeat the generated harness block; it is blanked before chunking (line numbers kept), so the
  harness is retrieved once, from `studio/SKILL_HARNESS.md`.
- Without dense vectors, "same topic" between two current owner rules is word overlap (Jaccard ≥ 0.3 in one
  LEARNINGS section). The older one is labelled `older: a newer related rule (<date>, line N) wins on conflict`, not
  `superseded`: overlap shows they are related, not that they conflict. Only rules struck through in LEARNINGS.md are
  called superseded.
- A `context` pack does not rank owner rules. It carries every current rule of the role's LEARNINGS sections (the
  `caveman.py` ROLES map) in full and leaves the superseded ones out, so retrieval can never drop a rule an agent must
  follow. Ranked passages fill the budget around them.
- Hinglish: a stop-word list and a small Hinglish→English word map (`HINGLISH` in `rag.py`), labelled as a stopgap.

**Agent wiring:** the caveman block (identical in every agent file and `CAVEMAN.md`) now says to start from
`rag.py context`; `/viral-studio` names each agent's step, builds the researcher's pack (it has no Bash) and re-indexes
the film after each stage. Agents still write whole files; the index picks them up.

## 12. Phase 2: dense retrieval and Hinglish (measured 2026-11-23)

**A held-out set first.** The 42-question golden set was written while phase 1 was being built, so it flatters BM25.
`studio/rag_golden_heldout.jsonl` has 20 new questions, written before any run: owner-style Hinglish, Hindi
(Devanagari) and paraphrases that share few words with the answer. Each also has an English version (`q_en`), as an
agent would translate it.

**Embedding models on romanized Hinglish.** Same 656-chunk subset (rules, harness, agents, README, docs), top 5:

| Model | Size | Held-out (as asked) | Main set |
|---|---|---|---|
| multilingual-e5-small | ~470 MB | 4/20 | 26/29 |
| multilingual-e5-base | ~1.1 GB | 4/20 | 28/29 |
| bge-m3 | ~2.2 GB | 5/20 | 26/29 |
| paraphrase-multilingual-mpnet-base-v2 | ~1.1 GB | 3/20 | 25/29 |

None of them understands romanized Hindi well enough. A bigger model is not the fix.

**Asking in English is.** The full index, recall@5:

| Mode | Main set (42) | Held-out as asked (20) | Held-out in English (20) |
|---|---|---|---|
| BM25 | 0.976, MRR 0.782 | 0.30 | 0.75 |
| Hybrid (BM25 + e5-small) | 0.952, MRR 0.802 | 0.30 | 0.75 |

Fusing the Hinglish question with its English version did worse than English alone (BM25, measured before the k fix below: 10/20 vs 14/20).

**Decisions:**
- **Agents ask in English.** They translate the owner's Hinglish into an English query and keep the owner's words for
  quoting. The caveman block says so, and `query` adds a note when a question is Hindi or Hinglish.
- **Dense stays an opt-in, off by default.** It raised MRR a little but not recall, which was the bar in §10. Turn it
  on with `pip install sentence-transformers` and `python3 studio/rag.py index --dense` (one ~470 MB download, about
  3 minutes to embed the studio corpus on 4 CPUs, then about 8 s to load the model per query process). `--no-dense`
  turns it off; `RAG_DENSE=0` skips it for one run. CI tests the dense code with a synthetic stand-in encoder.
- **Ranking fix found on the way.** Reciprocal-rank fusion used k = 60, which flattened ranks so much that the tier
  priors decided the order: an owner rule ranked 15th beat the best procedure passage. k = 10 keeps rank first. It
  raised main-set MRR from 0.689 to 0.782 and held-out English recall from 0.70 to 0.75, with the same main-set recall.

**Still open:** 5 held-out English questions miss. Two of them return sources that are also right (`/viral-studio`'s
"at most 3 agents"; the social agent's "never publish"), so the real recall is higher than the strict count. They
stay counted as misses: the set's answers were fixed before the runs.
