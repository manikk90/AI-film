"""What the viewer sees on each spoken line (speaker, overlay or cover), when an overlay lands,
whether anything sits on the face, and how a candidate short clip from a long video scores.

Methods, written in our own code and words, adopted at the owner's request on 2026-11-23 from
MIT-licensed repos (credit, not copied code):

- iart-ai/motion-skills (`talking-head-b-roll`): three treatments per spoken line, A speaker
  alone, B overlay (a transparent layer over the speaker), C cover (an opaque full frame while
  the voice runs on); open and close on the speaker, no long speaker-only stretch, covers of a
  few seconds with the speaker back in between; per-element timing that leads, syncs or waits.
- Barty-Bart/motion-graphics (`motion-broll`): cutaway length and the face time kept between
  cutaways.
- kurbaitaev/ghost-editor: QC that nothing is drawn over the tracked face.
- agricidaniel/claude-shorts: a weighted rubric for long-video-to-shorts candidates with
  coherence red flags, and snapping clip edges to sentence boundaries.

Every threshold is read from editor/rules.json, where it is labelled `observed` with the repo it
came from; none of them is an owner rule, and owner corrections there win.
"""

import re

from ..core import read_json
from . import edl as E

TREATMENTS = ("speaker", "overlay", "cover")
TIMINGS = ("lead", "sync", "wait")
DEFAULTS = {
    "speaker_run_max_seconds": 8.0, "cover_min_seconds": 3.0, "cover_max_seconds": 8.0, "face_between_covers_min_seconds": 2.0,
    "overlay_lead_frames": 6, "face_box_pad": 0.1, "face_overlap_max_share": 0.02,
    "clip_score_weights": {"hook": 0.30, "standalone": 0.25, "emotion": 0.20, "value": 0.15, "payoff": 0.10},
    "clip_red_flag_penalty": 15, "clip_filler_max_share": 0.3,
    "snap_start_window_seconds": 1.5, "snap_end_window_seconds": 3.0, "snap_end_pad_seconds": 0.3,
}
SENTENCE_END = re.compile(r"[.?!।॥…]['\")\]]*$")  # . ? ! । ॥ …
NUMBER = re.compile(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|percent|"
                    r"ek|do|teen|char|paanch|sau|hazaar|lakh|crore)\b", re.I)
STRUCTURE = re.compile(r"\b(?:first(?:ly)?|second(?:ly)?|third(?:ly)?|step|steps|reasons?|ways?|tips?|rules?|list|"
                       r"pehla|doosra|teesra)\b", re.I)
TURN = re.compile(r"\b(?:but|not|never|no|actually|except|instead|wrong|nahi|nahin|lekin|par|magar)\b", re.I)


def rules():
    """Thresholds from editor/rules.json over the documented starting values."""
    from .craft import RULES
    out = dict(DEFAULTS)
    out.update({k: v for k, v in read_json(RULES)["rules"].items() if k in DEFAULTS})
    return out


# ---- timing ---------------------------------------------------------------------------------

def overlay_at(timing, line_start, anchor=None, fps=30, lead_frames=None):
    """Start time of an overlay element on a line, on the frame grid.
    lead: structure (a heading, a list frame) arrives about 6 frames before its line or word;
    sync: a key number lands on the frame its word is spoken (`anchor` = that word's onset);
    wait: a punchline or negation waits for the revealing word (`anchor` = that word's onset)."""
    if timing not in TIMINGS:
        raise E.ProductionError("Overlay timing must be one of {}".format(", ".join(TIMINGS)))
    lead = rules()["overlay_lead_frames"] if lead_frames is None else lead_frames
    t = float(line_start if anchor is None else anchor)
    if timing == "lead":
        t -= lead / float(fps)
    return max(0.0, round(round(t * fps) / float(fps), 4))


# ---- planning -------------------------------------------------------------------------------

def sentences(words, max_gap=0.7):
    """Spoken lines from word timings ({start, end, word}): split at sentence punctuation or a
    pause longer than `max_gap`."""
    out, cur = [], []
    for i, w in enumerate(words):
        if cur and w["start"] - cur[-1]["end"] > max_gap:
            out.append(cur)
            cur = []
        cur.append(w)
        if SENTENCE_END.search(w["word"].strip()):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [{"start": s[0]["start"], "end": s[-1]["end"], "text": " ".join(w["word"].strip() for w in s), "words": s} for s in out]


def _guess(line):
    """First guess for one line from its words alone (no picture knowledge): numbers and
    structure become an overlay; a turn (but/not/never) becomes an overlay that waits."""
    text, words = line.get("text", ""), line.get("words") or []
    if NUMBER.search(text):
        anchor = next((w["start"] for w in words if NUMBER.search(w["word"])), None)
        return "overlay", "sync", anchor, "a number: it lands on its spoken word"
    if STRUCTURE.search(text):
        return "overlay", "lead", None, "structure (list, steps): it leads the line"
    if TURN.search(text):
        anchor = words[-1]["start"] if words else None
        return "overlay", "wait", anchor, "a turn or punchline: it waits for the revealing word"
    return "speaker", None, None, "plain line: the speaker carries it"


def plan(lines, fps=30, r=None):
    """Propose a speaker/overlay/cover table for timed lines ({start, end, text[, words]}).
    Opens and closes on the speaker; breaks speaker-only stretches longer than the limit with a
    cover (a line of cover length, with face time kept around it) or else an overlay; never
    proposes a cover outside the cover length range. A draft for Mann: covers still need B-roll
    that shows what the line says, and on-screen words come only from what is said."""
    r = r or rules()
    rows = []
    for i, line in enumerate(lines):
        treat, timing, anchor, why = _guess(line)
        if i in (0, len(lines) - 1):
            treat, timing, anchor, why = "speaker", None, None, "first/last line: open and close on the speaker"
        rows.append({"start": round(line["start"], 3), "end": round(line["end"], 3), "text": line.get("text", ""),
                     "treatment": treat, "timing": timing, "anchor": anchor, "why": why})

    def run_over():
        start = None
        for i, row in enumerate(rows):
            if row["treatment"] == "speaker":
                start = i if start is None else start
                if row["end"] - rows[start]["start"] > r["speaker_run_max_seconds"]:
                    return list(range(start, i + 1))
            else:
                start = None
        return None

    def cover_ok(i):
        a, b = rows[i]["start"], rows[i]["end"]
        if not (r["cover_min_seconds"] <= b - a <= r["cover_max_seconds"]):
            return False
        for j, other in enumerate(rows):
            if other["treatment"] == "cover" and j != i:
                gap = a - other["end"] if other["end"] <= a else other["start"] - b
                if gap < r["face_between_covers_min_seconds"]:
                    return False
        return True

    for _ in range(len(rows)):
        run = run_over()
        if not run:
            break
        inner = [i for i in run if 0 < i < len(rows) - 1]
        if not inner:
            break
        mid = (rows[run[0]]["start"] + rows[run[-1]]["end"]) / 2
        inner.sort(key=lambda i: abs((rows[i]["start"] + rows[i]["end"]) / 2 - mid))
        pick = next((i for i in inner if cover_ok(i)), None)
        if pick is not None:
            rows[pick].update(treatment="cover", timing=None, anchor=None, why="breaks a long speaker-only stretch; B-roll of what is said")
        else:
            rows[inner[0]].update(treatment="overlay", timing="lead", anchor=None, why="breaks a long speaker-only stretch (too short for a cover)")
    for row in rows:
        row["at"] = overlay_at(row["timing"], row["start"], row["anchor"], fps) if row["treatment"] == "overlay" else None
    return rows


def lines_from_edl(edl, words=None):
    """One line per EDL clip (beat) on the final timeline, with its words when caption word
    timings (timeline seconds, as autocut writes captions.words.json) are given."""
    rows, _ = E.timeline(edl)
    out = []
    for row, clip in zip(rows, edl["clips"]):
        ws = [w for w in (words or []) if row["start"] - 0.02 <= w["start"] < row["end"]]
        text = " ".join(w["word"] for w in ws) or clip.get("beat", "")
        out.append({"start": row["start"], "end": row["end"], "text": text, "words": ws, "id": clip["id"]})
    return out


def table_markdown(rows):
    lines = ["| # | Time | Treatment | Timing | Overlay at | Line | Why |", "|---|---|---|---|---|---|---|"]
    for i, r_ in enumerate(rows, 1):
        lines.append("| {} | {}-{} | {} | {} | {} | {} | {} |".format(
            i, E.tc(r_["start"]), E.tc(r_["end"]), r_["treatment"], r_["timing"] or "-",
            E.tc(r_["at"]) if r_["at"] is not None else "-", r_["text"][:60].replace("|", "/") or "-", r_["why"]))
    return "\n".join(lines) + "\n"


# ---- checks ---------------------------------------------------------------------------------

def segments(edl, rows=None):
    """Timeline spans by what the viewer sees. A clip's declared `treatment` (speaker when
    absent) covers its span; its `inserts` are cover spans inside it. Adjacent spans of the same
    kind are merged. Returns [{start, end, kind}]."""
    if rows is None:
        rows, _ = E.timeline(edl)
    spans = []
    for row, clip in zip(rows, edl["clips"]):
        kind, a, b = clip.get("treatment", "speaker"), row["start"], row["end"]
        if kind == "cover":
            spans.append([a, b, "cover"])
            continue
        cursor = a
        for ins in sorted(clip.get("inserts", []), key=lambda x: float(x.get("at", 0))):
            s = a + float(ins.get("at", 0))
            e = min(s + float(ins["out"]) - float(ins["in"]), b)
            if s > cursor:
                spans.append([cursor, s, kind])
            spans.append([max(s, cursor), e, "cover"])
            cursor = max(cursor, e)
        if b > cursor:
            spans.append([cursor, b, kind])
    merged = []
    for a, b, k in spans:
        if b - a <= 1e-6:
            continue
        if merged and merged[-1]["kind"] == k and abs(merged[-1]["end"] - a) < 0.05:
            merged[-1]["end"] = round(b, 3)
        else:
            merged.append({"start": round(a, 3), "end": round(b, 3), "kind": k})
    return merged


def rhythm_findings(edl, rows=None, r=None):
    """Treatment rhythm checks, only for an EDL that declares treatments on its beats.
    Each finding: (check name, ok, detail)."""
    if not any("treatment" in c for c in edl["clips"]):
        return []
    r = r or rules()
    segs = segments(edl, rows)
    out = []
    speaker = [s for s in segs if s["kind"] == "speaker"]
    long_ = [s for s in speaker if s["end"] - s["start"] > r["speaker_run_max_seconds"] + 1e-6]
    out.append(("speaker-only run", not long_, "longest {:.1f}s (max {}s){}".format(
        max((s["end"] - s["start"] for s in speaker), default=0), r["speaker_run_max_seconds"],
        "; over at " + ", ".join(E.tc(s["start"]) for s in long_) if long_ else "")))
    covers = [s for s in segs if s["kind"] == "cover"]
    bad = [s for s in covers if not (r["cover_min_seconds"] - 1e-6 <= s["end"] - s["start"] <= r["cover_max_seconds"] + 1e-6)]
    out.append(("cover length", not bad, "{} cover(s); outside {}-{}s: {}".format(
        len(covers), r["cover_min_seconds"], r["cover_max_seconds"],
        ", ".join("{} ({:.1f}s)".format(E.tc(s["start"]), s["end"] - s["start"]) for s in bad) or "none")))
    tight = [(a, b) for a, b in zip(covers, covers[1:]) if b["start"] - a["end"] < r["face_between_covers_min_seconds"] - 1e-6]
    out.append(("face between covers", not tight, "min {}s of speaker between covers; short at: {}".format(
        r["face_between_covers_min_seconds"], ", ".join(E.tc(a["end"]) for a, _ in tight) or "none")))
    ends = segs[0]["kind"] == "speaker" and segs[-1]["kind"] == "speaker" if segs else True
    out.append(("open and close on the speaker", ends, "first beat {}, last beat {}".format(
        segs[0]["kind"] if segs else "-", segs[-1]["kind"] if segs else "-")))
    return out


def face_box(face, W, H, pad):
    """Pixel box of a tracked face sample ({x, y, size} as fractions of the output frame, size
    being the face height), grown by `pad` of its size on each side."""
    half = face["size"] * H * (0.5 + pad)
    return {"x0": face["x"] * W - half, "x1": face["x"] * W + half, "y0": face["y"] * H - half, "y1": face["y"] * H + half}


def overlap_share(box, face):
    """Share of the face box covered by `box`."""
    w = min(box["x1"], face["x1"]) - max(box["x0"], face["x0"])
    h = min(box["y1"], face["y1"]) - max(box["y0"], face["y0"])
    area = (face["x1"] - face["x0"]) * (face["y1"] - face["y0"])
    return max(w, 0) * max(h, 0) / area if area > 0 else 0.0


def faces_over(items, faces, W, H, r=None):
    """Items ({name, start, end, box} in timeline seconds and output pixels) drawn on a tracked
    face ({t, x, y, size} in timeline seconds). Returns [(name, t, share)]."""
    r = r or rules()
    hits = []
    for item in items:
        worst = None
        for f in faces:
            if item["start"] - 1e-6 <= f["t"] <= item["end"] + 1e-6:
                share = overlap_share(item["box"], face_box(f, W, H, r["face_box_pad"]))
                if share > r["face_overlap_max_share"] and (worst is None or share > worst[2]):
                    worst = (item["name"], f["t"], share)
        if worst:
            hits.append(worst)
    return hits


# ---- long video to shorts -------------------------------------------------------------------

BACK_REFERENCE = re.compile(r"\b(?:as i (?:said|mentioned)|like i said|i mentioned (?:earlier|before)|as we (?:saw|discussed)|"
                            r"earlier|mentioned before|going back to|jaisa (?:maine|humne) (?:bataya|kaha)|pehle bataya)\b", re.I)
OPEN_PRONOUN = re.compile(r"^\W*(?:he|she|they|it|that|those|these|him|her|them|this one|vo|woh|usne|unhone|ye wala)\b", re.I)
FILLERS = {"um", "uh", "er", "erm", "hmm", "like", "basically", "actually", "matlab", "toh", "na", "haan", "you know"}


def red_flags(text):
    """Coherence red flags for a clip cut out of a longer video: it points back to something
    the viewer has not seen, opens on a pronoun with nothing to refer to, or stops mid-sentence."""
    flags = []
    if BACK_REFERENCE.search(text):
        flags.append("refers back to earlier in the video")
    if OPEN_PRONOUN.search(text):
        flags.append("opens on a pronoun with no referent")
    if text.strip() and not SENTENCE_END.search(text.strip()):
        flags.append("ends mid-sentence")
    return flags


def filler_share(text):
    words = re.findall(r"[\w']+", text.lower())
    return sum(1 for w in words if w in FILLERS) / float(len(words)) if words else 0.0


def score_clip(scores, text="", r=None):
    """Weighted 0-100 score of one candidate. `scores` holds 0-100 marks for hook, standalone,
    emotion, value and payoff (Mann's judgement of the words and picture). Measured from the
    text: each red flag takes `clip_red_flag_penalty` off standalone, and filler words over
    `clip_filler_max_share` of the words scale value down."""
    r = r or rules()
    w = r["clip_score_weights"]
    s = {k: float(scores.get(k, 0)) for k in w}
    flags = red_flags(text) if text else []
    s["standalone"] = max(0.0, s["standalone"] - r["clip_red_flag_penalty"] * len(flags))
    fill = filler_share(text) if text else 0.0
    if fill > r["clip_filler_max_share"]:
        s["value"] *= max(0.0, 1 - (fill - r["clip_filler_max_share"]) * 2)
    total = sum(w[k] * min(max(s[k], 0.0), 100.0) for k in w)
    return {"score": round(total, 1), "parts": {k: round(v, 1) for k, v in s.items()}, "red_flags": flags, "filler_share": round(fill, 3)}


def rank_clips(candidates, r=None):
    """Score and sort candidates ({start, end, text, scores}); best first, earlier start on ties."""
    out = [dict(c, **score_clip(c.get("scores", {}), c.get("text", ""), r)) for c in candidates]
    return sorted(out, key=lambda c: (-c["score"], c.get("start", 0)))


def _starts_sentence(words, i):
    return i == 0 or bool(SENTENCE_END.search(words[i - 1]["word"].strip()))


def snap_clip(words, start, end, r=None):
    """Snap a candidate clip's edges to the speech (word timings {start, end, word}, seconds).
    Start: the nearest sentence start within the start window, else the nearest word start.
    End: the first sentence end at or after `end` within the end window (else the nearest word
    end), plus the end pad, never running into the next word."""
    r = r or rules()
    words = sorted(words, key=lambda w: w["start"])
    if not words:
        return {"start": start, "end": end, "start_snap": "none", "end_snap": "none"}
    sent = [w["start"] for i, w in enumerate(words) if _starts_sentence(words, i)]
    near = [t for t in sent if abs(t - start) <= r["snap_start_window_seconds"] + 1e-9]
    if near:
        new_start, how_start = min(near, key=lambda t: (abs(t - start), t)), "sentence"
    else:
        new_start, how_start = min((w["start"] for w in words), key=lambda t: (abs(t - start), t)), "word"
    ends = [(i, w) for i, w in enumerate(words) if SENTENCE_END.search(w["word"].strip())
            and end - 0.05 <= w["end"] <= end + r["snap_end_window_seconds"] + 1e-9 and w["end"] > new_start]
    if ends:
        idx, last = ends[0]
        how_end = "sentence"
    else:
        idx, last = min(((i, w) for i, w in enumerate(words) if w["end"] > new_start), key=lambda iw: abs(iw[1]["end"] - end),
                        default=(len(words) - 1, words[-1]))
        how_end = "word"
    new_end = last["end"] + r["snap_end_pad_seconds"]
    if idx + 1 < len(words):
        new_end = min(new_end, max(last["end"], words[idx + 1]["start"] - 0.02))
    return {"start": round(new_start, 3), "end": round(new_end, 3), "start_snap": how_start, "end_snap": how_end}


__all__ = ["TREATMENTS", "TIMINGS", "overlay_at", "sentences", "plan", "lines_from_edl", "segments", "rhythm_findings",
           "faces_over", "red_flags", "score_clip", "rank_clips", "snap_clip"]
