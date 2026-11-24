"""Mann's cleaner cut: find the speech, transcribe it piece by piece, resolve retakes and false
starts, remove fillers and write word-accurate keep pieces to `<edit>/analysis/takes.json`,
which `autocut` turns into the A-roll and the storyboard shows to the owner as retake groups.

Method credit (methods only; this is Mann's own code, nothing pasted). The owner approved
adopting these methods on 2026-11-23 (`projects/editor-repos/re/SPEC.md`):
- kurbaitaev/ghost-editor (MIT, (c) 2026 kurbaitaev), `references/take-selection.md`:
  transcribe each speech island on its own, keep the later fluent take, cut on word times
  (in = first word - 0.12 s, out = last word + 0.25 s), shrink pauses > 0.26 s inside a take
  to 0.18 s, snap cuts to the frame grid, and `subcheck` (re-transcribe each kept piece; a
  repeated opening is a hidden false start).
- louisedesadeleer/cut-video (MIT): silence relative to the recording's own noise floor
  (F = 10th percentile of 0.5 s window RMS, threshold F + 6 dB; when speech minus floor is
  under 8 dB energy cannot split speech, so cuts come from word times only), n-gram retakes
  (3-gram > 0.8 within 3 s = false start, drop the earlier; 4-gram > 0.7 within 60 s = full
  retake, keep the LAST unless flubbed), filler list cut with a 50 ms pad, the gap table per
  tone, and laugh/reaction protection (window RMS > F + 10 dB stays).

Every threshold lives in `editor/rules.json` under `rules.takes` as an external calibration
(history kind `observed`), not an owner rule. Hindi/Hinglish starters ("matlab", "toh", "na",
"haan") are only flagged for the owner when they stand alone, never cut automatically.

The transcriber is injectable: any callable `(media_path, start, end, purpose) -> [{"word",
"start", "end"}]` with times in source seconds. The default runs Mann's Whisper path
(`tools.whisper_segments`) on an FFmpeg slice. Nothing here approves anything: the cut still
goes through the storyboard and the owner's recorded approval of the exact EDL.
"""

import difflib
import math
import re
import subprocess
import tempfile
from array import array
from pathlib import Path

from ..core import ProductionError, inside, now, project_lock, read_json, require, write_json
from . import media

REPO = Path(__file__).resolve().parents[2]
RULES = REPO / "editor" / "rules.json"
TAKES = "analysis/takes.json"
RATE = 16000
FRAME = 0.02  # analysis frame (s)
TONES = ("aggressive", "balanced", "documentary")
SENTENCE_SPLIT = re.compile(r"[.!?।॥\n]+")


def rules():
    return read_json(RULES)["rules"]["takes"]


def norm(word):
    """Lower-case word without punctuation; Devanagari letters and matras are kept."""
    return re.sub(r"[^\wऀ-ॿ]+", "", str(word).lower()).strip("_")


# ---- audio levels and islands ------------------------------------------------------

def decode(path, rate=RATE):
    media.need("ffmpeg")
    proc = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(Path(path).resolve()), "-vn", "-ac", "1", "-ar", str(rate),
                           "-f", "s16le", "-"], capture_output=True, timeout=3600)
    require(proc.returncode == 0, "FFmpeg could not decode the audio of {}: {}".format(path, proc.stderr.decode(errors="replace")[-300:]))
    pcm = array("h")
    pcm.frombytes(proc.stdout[:len(proc.stdout) - len(proc.stdout) % 2])
    return pcm


def frame_power(pcm, rate=RATE, frame=FRAME):
    """Mean power of each analysis frame (int16 units squared)."""
    n = int(rate * frame)
    try:
        import numpy as np
        a = np.frombuffer(pcm.tobytes(), dtype=np.int16).astype(np.float64)
        k = len(a) // n
        return [float(x) for x in (a[:k * n].reshape(k, n) ** 2).mean(axis=1)] if k else []
    except ImportError:
        return [sum(x * x for x in pcm[i:i + n]) / n for i in range(0, len(pcm) - n + 1, n)]


def db(power):
    return 10 * math.log10(power / (32768.0 ** 2)) if power > 0 else -120.0


def window_db(power, a, b):
    seg = power[max(int(a), 0):max(int(b), int(a) + 1)]
    return db(sum(seg) / len(seg)) if seg else -120.0


def percentile(values, p):
    s = sorted(values)
    return s[int(round(p / 100.0 * (len(s) - 1)))] if s else -120.0


def levels(power, cfg):
    """Noise floor F and speech level S from 0.5 s window RMS, the island threshold and the guard."""
    win = max(1, int(round(cfg["rms_window_s"] / FRAME)))
    wins = [window_db(power, i, i + win) for i in range(0, max(len(power) - win + 1, 1), win)]
    F, S = percentile(wins, cfg["floor_percentile"]), percentile(wins, cfg["speech_percentile"])
    ok = S - F >= cfg["min_dynamic_range_db"]
    return {"floor_db": round(F, 1), "speech_db": round(S, 1), "threshold_db": round(F + cfg["threshold_above_floor_db"], 1),
            "laugh_db": round(F + cfg["laugh_above_floor_db"], 1), "dynamic_range_db": round(S - F, 1),
            "guard": "ok" if ok else "low-dynamic-range"}


def islands(power, lv, cfg):
    """Speech islands: frames above F + 6 dB, joined across pauses shorter than island_min_pause_s."""
    thr = lv["threshold_db"]
    runs, start = [], None
    for i, p in enumerate(power + [0.0]):
        loud = i < len(power) and db(p) > thr
        if loud and start is None:
            start = i
        elif not loud and start is not None:
            runs.append([start * FRAME, i * FRAME])
            start = None
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] < cfg["island_min_pause_s"]:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(round(a, 3), round(b, 3)) for a, b in merged if b - a >= 0.06]


def peak_window_db(power, a, b, win_s):
    """Loudest RMS over windows of win_s (or the whole span when shorter) inside [a, b] seconds."""
    fa, fb = int(round(a / FRAME)), int(round(b / FRAME))
    if fb <= fa:
        return -120.0
    w = max(1, min(int(round(win_s / FRAME)), fb - fa))
    return max(window_db(power, i, i + w) for i in range(fa, fb - w + 1))


# ---- transcription ----------------------------------------------------------------

def whisper_transcriber(model="small", language=None):
    """Mann's Whisper path on an FFmpeg slice of [start, end]; word times returned in source seconds."""
    from . import tools

    def run(path, start, end, purpose="island"):
        with tempfile.TemporaryDirectory(prefix="mann-takes-") as tmp:
            wav = Path(tmp) / "slice.wav"
            media.run(["ffmpeg", "-v", "error", "-y", "-ss", "{:.3f}".format(start), "-to", "{:.3f}".format(end), "-i", Path(path).resolve(),
                       "-vn", "-ac", "1", "-ar", str(RATE), wav])
            _, _, segs = tools.whisper_segments(wav, model, language, vad=False)
        return [{"word": w["word"], "start": round(start + w["start"], 3), "end": round(start + w["end"], 3)}
                for s in segs for w in s.get("words", []) if w.get("start") is not None]
    return run


def transcribe_islands(path, isl, transcriber, duration):
    words = []
    for n, (a, b) in enumerate(isl, 1):
        lo, hi = max(0.0, a - 0.1), min(duration, b + 0.1)
        for w in transcriber(path, lo, hi, "island"):
            mid = (w["start"] + w["end"]) / 2
            if lo <= mid <= hi and norm(w["word"]) and not any(abs(x["start"] - w["start"]) < 0.02 for x in words[-3:]):
                words.append({"word": str(w["word"]).strip(), "start": round(float(w["start"]), 3), "end": round(float(w["end"]), 3),
                              "island": "I{:02d}".format(n)})
    words.sort(key=lambda w: w["start"])
    return words


# ---- the cut plan (pure: words in, pieces out) ------------------------------------

def script_sentences(text):
    out = []
    for s in SENTENCE_SPLIT.split(re.sub(r"^#+\s*", "", text or "", flags=re.M)):
        toks = [norm(t) for t in s.split() if norm(t)]
        if toks:
            out.append({"n": len(out) + 1, "text": s.strip(), "tokens": toks})
    return out


def grams(tokens, n):
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def contains(seq, sub):
    k = len(sub)
    return any(tuple(seq[i:i + k]) == tuple(sub) for i in range(len(seq) - k + 1))


def retake_similarity(a, b, n):
    """Share of the shorter unit's n-grams found in the other (a short unit counts whole)."""
    if not a or not b:
        return 0.0
    if len(a) < n or len(b) < n:
        short, other = (a, b) if len(a) <= len(b) else (b, a)
        return 1.0 if len(short) >= 2 and contains(other, short) else 0.0
    ga, gb = set(grams(a, n)), set(grams(b, n))
    return len(ga & gb) / float(min(len(ga), len(gb)))


def tone_target(gap, bands):
    """Rendered length of a pause of `gap` seconds under a tone's gap table (gap itself when kept)."""
    for lo, hi, target in bands:
        if gap >= lo and (hi is None or gap < hi):
            return gap if target is None else min(gap, target)
    return gap


def standalone(words, i, cfg):
    gap = cfg["standalone_pause_s"]
    before = i == 0 or words[i]["start"] - words[i - 1]["end"] >= gap
    after = i == len(words) - 1 or words[i + 1]["start"] - words[i]["end"] >= gap
    return before and after


def plan(words, cfg, tone="balanced", sentences=None, duration=None, fps=30.0, reactions=(), laugh=None, overrides=None):
    """Turn timed words into keep pieces. `laugh(a, b)` says whether [a, b] holds protected sound;
    `reactions` are word-less loud islands kept as their own pieces."""
    require(tone in TONES, "tone must be one of " + ", ".join(TONES))
    words = [dict(w, i=i, n=norm(w["word"])) for i, w in enumerate(sorted(words, key=lambda w: w["start"]))]
    duration = duration if duration is not None else (words[-1]["end"] + 1.0 if words else 0.0)
    fillers, flag_only = set(cfg["fillers"]), set(cfg["flag_only_fillers"])
    removed, flagged = [], []
    for k, w in enumerate(words):
        w["state"] = "keep"
        if w["n"] in fillers:
            w["state"], w["why"] = "filler", "filler"
            removed.append(w)
        elif w["n"] in flag_only and standalone(words, k, cfg):
            flagged.append(w)

    # units: one breath run of words (split at long pauses)
    units, cur = [], []
    for w in words:
        if cur and w["start"] - cur[-1]["end"] >= cfg["unit_merge_pause_s"]:
            units.append(cur)
            cur = []
        cur.append(w)
    if cur:
        units.append(cur)
    for u_i, u in enumerate(units):
        for w in u:
            w["unit"] = "L{:02d}".format(u_i + 1)
    unit_start = {u[0]["i"] for u in units}

    # A. false starts: a restart of the same words within the window drops the earlier attempt
    groups = []
    content = [w for w in words if w["state"] == "keep"]
    n3, sim3, win3 = cfg["false_start_ngram"], cfg["false_start_similarity"], cfg["false_start_window_s"]
    floor_i = 0
    for j in range(len(content)):
        if any(w["state"] != "keep" for w in content[j:j + 1]):
            continue
        best = None
        for i in range(floor_i, j):
            w0 = content[i]
            restart_point = w0["i"] in unit_start or (w0["i"] > 0 and w0["start"] - words[w0["i"] - 1]["end"] >= cfg["restart_pause_s"])
            if not restart_point or any(w["state"] != "keep" for w in content[i:j]):
                continue
            span = j - i
            if span >= n3 and j + n3 <= len(content):
                gi, gj = content[i:i + n3], content[j:j + n3]
                if 0 <= gj[0]["start"] - gi[-1]["end"] <= win3 and \
                        difflib.SequenceMatcher(None, " ".join(w["n"] for w in gi), " ".join(w["n"] for w in gj)).ratio() > sim3:
                    best = i
                    break
            elif 2 <= span < n3 and [w["n"] for w in content[i:j]] == [w["n"] for w in content[j:j + span]] and \
                    content[j]["start"] - content[j - 1]["end"] <= win3:
                best = i
                break
        if best is not None:
            attempt = content[best:j]
            for w in attempt:
                w["state"], w["why"] = "false-start", "false start (restarted at {:.2f}s)".format(content[j]["start"])
            floor_i = j
            groups.append({"kind": "false-start", "text": " ".join(w["word"] for w in attempt),
                           "takes": [{"start": attempt[0]["start"], "end": attempt[-1]["end"], "text": " ".join(w["word"] for w in attempt)},
                                     {"start": content[j]["start"], "end": content[min(j + n3, len(content)) - 1]["end"],
                                      "text": " ".join(w["word"] for w in content[j:j + n3]) + " ..."}],
                           "kept": 1, "why": "restart within {} s: earlier attempt dropped".format(win3)})

    # B. full retakes between units (and units mapped to the same script sentence)
    def tokens(u):
        return [w["n"] for w in u if w["state"] == "keep"]
    info = []
    for u_i, u in enumerate(units):
        tk = tokens(u)
        rec = {"id": "L{:02d}".format(u_i + 1), "start": u[0]["start"], "end": u[-1]["end"], "text": " ".join(w["word"] for w in u),
               "tokens": tk, "sentence": None, "coverage": None}
        if sentences and tk:
            def score(s):
                bag = list(s["tokens"])
                hit = 0
                for t in tk:
                    if t in bag:
                        bag.remove(t)
                        hit += 1
                return hit
            best = max(sentences, key=score)
            hit = score(best)
            if hit / float(len(tk)) >= cfg["script_match_min"]:
                rec["sentence"], rec["coverage"] = best["n"], round(hit / float(len(best["tokens"])), 2)
        info.append(rec)
    parent = list(range(len(units)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    n4, sim4, win4 = cfg["retake_ngram"], cfg["retake_similarity"], cfg["retake_window_s"]
    for a in range(len(units)):
        for b in range(a + 1, len(units)):
            if info[b]["start"] - info[a]["end"] > win4:
                break
            same_line = info[a]["sentence"] is not None and info[a]["sentence"] == info[b]["sentence"]
            if same_line or retake_similarity(info[a]["tokens"], info[b]["tokens"], n4) > sim4:
                parent[find(b)] = find(a)
    clusters = {}
    for x in range(len(units)):
        if info[x]["tokens"]:
            clusters.setdefault(find(x), []).append(x)
    overrides = dict(overrides or {})
    retake_n = 0
    for members in sorted((m for m in clusters.values() if len(m) > 1), key=lambda m: m[0]):
        retake_n += 1
        gid = "G{:02d}".format(retake_n)
        longest = max(len(info[m]["tokens"]) for m in members)
        fluent = [m for m in members if len(info[m]["tokens"]) >= cfg["fluent_min_share"] * longest and
                  (info[m]["coverage"] is None or info[m]["coverage"] >= cfg["fluent_min_share"])]
        keep, why = (fluent[-1], "last fluent take") if fluent else (members[-1], "no fluent take: last take kept, check it")
        if members[-1] != keep and fluent:
            why = "last fluent take (later take {} incomplete)".format(info[members[-1]]["id"])
        if gid in overrides:
            pick = [m for m in members if info[m]["id"] == overrides[gid]]
            require(pick, "--keep {}={}: that take is not in group {} ({})".format(gid, overrides[gid], gid, ", ".join(info[m]["id"] for m in members)))
            keep, why = pick[0], "owner override"
        for m in members:
            if m != keep:
                for w in units[m]:
                    if w["state"] == "keep":
                        w["state"], w["why"] = "retake", "earlier/other take of {} (kept {})".format(gid, info[keep]["id"])
        groups.append({"id": gid, "kind": "retake", "sentence": info[keep]["sentence"],
                       "text": " ".join(w["word"] for w in units[keep] if w["state"] == "keep"),
                       "takes": [{"unit": info[m]["id"], "start": info[m]["start"], "end": info[m]["end"], "text": info[m]["text"]} for m in members],
                       "kept": members.index(keep), "kept_unit": info[keep]["id"], "why": why})
    fs = 0
    for g in groups:
        if g["kind"] == "false-start":
            fs += 1
            g["id"] = "F{:02d}".format(fs)
    groups.sort(key=lambda g: g["takes"][0]["start"])

    # C. pieces on word times
    pieces = word_pieces(words, cfg, cfg["tones"][tone], duration, laugh)
    clear = cfg["filler_pad_s"]
    for a, b in reactions:
        lo = max([w["end"] + clear for w in words if w["end"] <= a] + [0.0, a - 0.05])
        hi = min([w["start"] - clear for w in words if w["start"] >= b] + [duration, b + 0.05])
        if hi > lo:
            pieces.append({"in": lo, "out": hi, "kind": "reaction", "words": []})
    pieces = snap_merge(pieces, fps, words, duration)
    for k, p in enumerate(pieces, 1):
        p["id"] = "K{:02d}".format(k)
    kept = [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in words if w["state"] == "keep"]
    units_out = [{k: v for k, v in r.items() if k != "tokens"} for r in info]
    for r, u in zip(units_out, units):
        r["state"] = "kept" if any(w["state"] == "keep" for w in u) else "dropped"
    return {"units": units_out, "groups": groups, "pieces": pieces, "kept_words": kept,
            "fillers": {"removed": [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in removed],
                        "flagged": [{"word": w["word"], "start": w["start"], "end": w["end"],
                                     "why": "Hindi/Hinglish starter standing alone: owner decides, not cut"} for w in flagged]},
            "dropped_words": [{"word": w["word"], "start": w["start"], "end": w["end"], "why": w["why"]} for w in words if w["state"] != "keep"]}


def word_pieces(words, cfg, bands, duration, laugh):
    pad_in, pad_out, clear = cfg["pad_in_s"], cfg["pad_out_s"], cfg["filler_pad_s"]
    share_in = pad_in / (pad_in + pad_out)
    kept = [w for w in words if w["state"] == "keep"]
    pieces = []
    for k, w in enumerate(kept):
        prev = kept[k - 1] if k else None
        between = words[prev["i"] + 1:w["i"]] if prev else []
        if prev is not None and not between:
            gap = w["start"] - prev["end"]
            target = tone_target(gap, bands)
            if target >= gap or (laugh and laugh(prev["end"], w["start"])):
                pieces[-1]["out_word"] = w
                pieces[-1]["words"].append(w)
                continue
            pieces[-1]["out"] = prev["end"] + target * (1 - share_in)
            start = w["start"] - target * share_in
        elif prev is not None:
            out = max(prev["end"], min(prev["end"] + pad_out, between[0]["start"] - clear))
            start = min(w["start"], max(w["start"] - pad_in, between[-1]["end"] + clear))
            if all(x["state"] == "filler" for x in between):
                rendered = (out - prev["end"]) + (w["start"] - start)
                target = tone_target(rendered, bands)
                if rendered > 0 and target < rendered:
                    out = prev["end"] + (out - prev["end"]) * target / rendered
                    start = w["start"] - (w["start"] - start) * target / rendered
            pieces[-1]["out"] = out
        else:
            before = words[:w["i"]]
            start = max(0.0, w["start"] - pad_in, (before[-1]["end"] + clear) if before else 0.0)
            start = min(start, w["start"])
        pieces.append({"in": start, "out": None, "kind": "speech", "words": [w], "in_word": w, "out_word": w})
    if pieces:
        last = kept[-1]
        after = words[last["i"] + 1:]
        pieces[-1]["out"] = max(last["end"], min(last["end"] + pad_out, duration, (after[0]["start"] - clear) if after else duration))
    return pieces


def snap_merge(pieces, fps, words, duration):
    """Snap every cut to the source frame grid (picture and voice cut at the same time), then merge overlaps."""
    def snap(t, first_start=None, last_end=None):
        f = round(t * fps)
        if first_start is not None and f / fps > first_start:
            f = math.floor(first_start * fps + 1e-9)
        if last_end is not None and f / fps < last_end:
            f = math.ceil(last_end * fps - 1e-9)
        return round(f / fps, 6)
    out = []
    for p in sorted(pieces, key=lambda p: p["in"]):
        ws = p["words"]
        a = snap(p["in"], first_start=ws[0]["start"] if ws else None)
        b = min(snap(p["out"], last_end=ws[-1]["end"] if ws else None), math.floor(duration * fps + 1e-9) / fps)
        if b <= a:
            continue
        if out and a <= out[-1]["out"] + 1e-6:
            out[-1]["out"] = max(out[-1]["out"], b)
            out[-1]["words"] += ws
            if p["kind"] == "reaction":
                out[-1]["kind"] = "speech+reaction" if out[-1]["kind"] != "reaction" else "reaction"
            continue
        out.append({"in": a, "out": b, "kind": p["kind"], "words": list(ws)})
    for p in out:
        ws = p.pop("words")
        p["text"] = " ".join(w["word"] for w in ws)
        p["first_word"] = ws[0]["start"] if ws else None
        p["last_word"] = ws[-1]["end"] if ws else None
        p["words"] = len(ws)
    return out


def subcheck(path, pieces, transcriber, cfg, fps, words):
    """Re-transcribe each kept speech piece alone; a repeated opening inside it is a hidden false start
    (whole-island transcription tends to merge restarts). The earlier attempt is cut off the piece."""
    k, win, clear = cfg["subcheck_opening_words"], cfg["false_start_window_s"], cfg["filler_pad_s"]
    fillers = set(cfg["fillers"])
    report = []
    for p in pieces:
        if not p["words"]:
            continue
        ws = [w for w in transcriber(path, p["in"], p["out"], "subcheck") if norm(w["word"]) and norm(w["word"]) not in fillers]
        toks = [norm(w["word"]) for w in ws]
        hit = next((j for j in range(1, len(toks) - k + 1) if toks[j:j + k] == toks[:k] and ws[j]["start"] - ws[0]["start"] <= win), None)
        row = {"piece": p["id"], "words": len(ws), "hidden_false_start": hit is not None}
        if hit is not None:
            new_in = max(ws[hit]["start"] - cfg["pad_in_s"], ws[hit - 1]["end"] + clear)
            new_in = min(math.floor(ws[hit]["start"] * fps + 1e-9), round(new_in * fps)) / fps
            row.update(repeat=" ".join(w["word"] for w in ws[:hit]), cut_from=p["in"], new_in=round(new_in, 6))
            p["in"], p["first_word"] = round(new_in, 6), ws[hit]["start"]
            p["text"] = " ".join(w["word"] for w in ws[hit:])
            p["subcheck"] = "hidden false start removed"
        report.append(row)
    return report


# ---- the command ------------------------------------------------------------------

def default_source(root):
    from . import engine as G
    prof = G.profile(root)
    return max(prof["videos"], key=lambda v: v.get("audio_activity", 0))["file"]


def analyse(root, source=None, script=None, tone="balanced", transcriber=None, overrides=None, check=True):
    """`mann takes`: write <edit>/analysis/takes.json for one A-roll source."""
    root = Path(root)
    with project_lock(root):
        return _analyse(root, source, script, tone, transcriber, overrides, check)


def _analyse(root, source, script, tone, transcriber, overrides, check):
    from . import edl as E
    cfg = rules()
    require(tone in TONES, "tone must be one of " + ", ".join(TONES))
    source = source or default_source(root)
    path = inside(root, source)
    require(path.is_file(), "Missing source: " + source)
    info = media.probe(path)
    require(info["has_audio"], "{} has no audio track to cut on".format(source))
    duration, fps = info["duration"], float(info.get("fps") or 30.0) or 30.0
    transcriber = transcriber or whisper_transcriber()
    power = frame_power(decode(path))
    lv = levels(power, cfg)
    guard_ok = lv["guard"] == "ok"
    isl = islands(power, lv, cfg) if guard_ok else [(0.0, round(duration, 3))]
    words = transcribe_islands(path, isl, transcriber, duration)
    isl_out, reactions = [], []
    for n, (a, b) in enumerate(isl, 1):
        iid = "I{:02d}".format(n)
        has_words = any(w["island"] == iid for w in words)
        peak = peak_window_db(power, a, b, cfg["rms_window_s"])
        kind = "speech" if has_words else ("reaction" if guard_ok and peak > lv["laugh_db"] else "noise")
        if kind == "reaction":
            reactions.append((a, b))
        isl_out.append({"id": iid, "start": a, "end": b, "kind": kind, "peak_db": round(peak, 1)})

    def laugh(a, b):
        return guard_ok and b - a > 0.1 and peak_window_db(power, a + 0.03, b - 0.03, cfg["rms_window_s"]) > lv["laugh_db"]
    sentences = None
    if script:
        sentences = script_sentences(inside(root, script).read_text(encoding="utf-8"))
        require(sentences, "Script {} has no sentences".format(script))
    out = plan(words, cfg, tone, sentences, duration, fps, reactions, laugh, overrides)
    checks = subcheck(path, out["pieces"], transcriber, cfg, fps, words) if check else []
    kept = sum(p["out"] - p["in"] for p in out["pieces"])
    rec = {"version": 1, "created": now(), "source": source, "sha256": E.hashed(root, source), "duration": round(duration, 3), "fps": fps,
           "tone": tone, "script": script, "overrides": dict(overrides or {}),
           "method": "ghost-editor take selection + cut-video floor-relative silence/retakes/fillers (MIT, methods only); "
                     "thresholds are external calibrations in editor/rules.json rules.takes",
           "levels": lv, "guard_note": None if guard_ok else
           "speech is less than {} dB above the floor: energy cannot split speech, so islands/laugh protection are off and "
           "every cut comes from word times".format(cfg["min_dynamic_range_db"]),
           "islands": isl_out, "words": words, **out, "subcheck": checks if check else "skipped (--no-subcheck)",
           "stats": {"source_seconds": round(duration, 2), "kept_seconds": round(kept, 2), "pieces": len(out["pieces"]),
                     "retake_groups": sum(1 for g in out["groups"] if g["kind"] == "retake"),
                     "false_starts": sum(1 for g in out["groups"] if g["kind"] == "false-start"),
                     "fillers_removed": len(out["fillers"]["removed"]), "fillers_flagged": len(out["fillers"]["flagged"]),
                     "hidden_false_starts": sum(1 for c in checks if c["hidden_false_start"])}}
    write_json(root / TAKES, rec)
    return rec


def load(root):
    """(takes record or None, reason it cannot be used or None)."""
    from . import edl as E
    root = Path(root)
    path = root / TAKES
    if not path.exists():
        return None, None
    rec = read_json(path)
    try:
        fresh = E.hashed(root, rec["source"]) == rec.get("sha256")
    except (ProductionError, OSError, KeyError):
        fresh = False
    return rec, None if fresh else "analysis/takes.json is stale (its source changed or is missing); run `takes` again"


def markdown(root, edl):
    """Storyboard section: the retake groups and fillers, so the owner can override a pick."""
    from .edl import tc
    rec, stale = load(root)
    if not rec:
        return ""
    lines = ["## Retake groups (owner can override)", ""]
    if stale:
        lines += ["**{}**".format(stale), ""]
    lines += ["From `{}` on `{}`, tone `{}`{}. Mann kept the last fluent take of each line. To keep another take: "
              "`python3 -m aifilm.editor takes <edit-dir> --keep G01=L02`, then `autocut` and `storyboard` again.".format(
                  TAKES, rec["source"], rec["tone"], ", script `{}`".format(rec["script"]) if rec.get("script") else ""), ""]
    if rec["groups"]:
        lines += ["| Group | Kind | Line | Takes (source time) | Kept | Why |", "|---|---|---|---|---|---|"]
        for g in rec["groups"]:
            takes = "; ".join("{}{} {}".format("**" if i == g["kept"] else "", t.get("unit", "t{}".format(i + 1)), tc(t["start"])) +
                              ("**" if i == g["kept"] else "") for i, t in enumerate(g["takes"]))
            kept = g["takes"][g["kept"]]
            lines.append("| {} | {} | {} | {} | {} {} | {} |".format(g["id"], g["kind"], g["text"].replace("|", "/")[:80], takes,
                                                                    kept.get("unit", "restart"), tc(kept["start"]), g["why"]))
    else:
        lines.append("No retakes or false starts found.")
    f = rec["fillers"]
    lines += ["", "- Fillers removed: {}".format(", ".join("`{}` {}".format(w["word"], tc(w["start"])) for w in f["removed"]) or "none"),
              "- Flagged for the owner (kept, not cut): {}".format(", ".join("`{}` {}".format(w["word"], tc(w["start"])) for w in f["flagged"]) or "none")]
    hidden = [c for c in rec["subcheck"] if c.get("hidden_false_start")] if isinstance(rec["subcheck"], list) else []
    lines.append("- Subcheck: {}".format(rec["subcheck"] if isinstance(rec["subcheck"], str) else
                                         ("{} hidden false start(s) cut: {}".format(len(hidden), ", ".join("{} (`{}`)".format(c["piece"], c["repeat"]) for c in hidden))
                                          if hidden else "no hidden false starts in {} pieces".format(len(rec["subcheck"])))))
    lv = rec["levels"]
    lines.append("- Levels: floor {} dB, speech {} dB, range {} dB ({}){}".format(lv["floor_db"], lv["speech_db"], lv["dynamic_range_db"], lv["guard"],
                                                                                  ": " + rec["guard_note"] if rec.get("guard_note") else ""))
    return "\n".join(lines) + "\n"
