"""Mann's smart engine: analyse the owner's footage, suggest how to edit it (styles, unique
ideas, hooks, problems), and draft an EDL in a chosen style so Mann starts from a real cut.

Everything here is measured (FFmpeg) or rule-based from editor/styles/catalog.json. Labels
such as "talking" or "action" are heuristics from audio activity and motion and are marked
as guesses in the outputs; Whisper transcripts, when present, replace the audio guess.
"""

import math
import re
import subprocess
from array import array
from pathlib import Path

from ..core import inside, now, project_lock, read_json, require, write_json
from . import edl as E
from . import media
from .treatment import rank_clips, score_clip, snap_clip  # noqa: F401  (engine.snap_clip / score_clip / rank_clips)

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "editor" / "styles" / "catalog.json"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}


def catalog():
    return read_json(CATALOG)["styles"]


def style(slug):
    for s in catalog():
        if s["slug"] == slug:
            return s
    raise E.ProductionError("Unknown style {!r}; see editor/styles/catalog.json".format(slug))


# ---- analysis -------------------------------------------------------------------

def samples(path, duration, count=40, size=(32, 18)):
    """Evenly spaced tiny RGB frames from one FFmpeg call."""
    step = max(duration / count, 0.25)
    w, h = size
    data = subprocess.run(["ffmpeg", "-v", "error", "-i", str(Path(path).resolve()), "-vf",
                           "fps=1/{:.4f},scale={}:{}:flags=area".format(step, w, h), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          capture_output=True, timeout=600).stdout
    n = w * h * 3
    frames = [data[i:i + n] for i in range(0, len(data) - n + 1, n)]
    return step, [[tuple(f[j:j + 3]) for j in range(0, n, 3)] for f in frames]


def motion_series(frames):
    out = []
    for a, b in zip(frames, frames[1:]):
        out.append(sum(abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2]) for x, y in zip(a, b)) / (len(a) * 3 * 255.0))
    return out


def activity(path, duration, noise_db=-35, gap=0.35):
    """Audio-active segments (speech or other sound) as the complement of silences."""
    quiet = media.silences(path, noise_db, gap)
    segs, cursor = [], 0.0
    for s in quiet:
        if s["start"] - cursor > 0.15:
            segs.append({"start": round(cursor, 3), "end": round(s["start"], 3)})
        cursor = s["end"] if s["end"] is not None else duration
    if duration - cursor > 0.15:
        segs.append({"start": round(cursor, 3), "end": round(duration, 3)})
    return segs


def transcript_for(root, rel):
    path = Path(root) / "transcripts" / (Path(rel).stem + ".json")
    return read_json(path) if path.exists() else None


DOC_EXT = {".txt", ".md", ".json", ".pdf", ".docx", ".csv"}


def kind_of(rel, info):
    ext = Path(rel).suffix.lower()
    if ext in (".srt", ".vtt"):
        return "subtitles"
    if ext == ".cube":
        return "lut"
    if ext in IMAGE_EXT:
        return "image"
    if ext in DOC_EXT:
        return "document"
    if not info.get("has_video"):
        return "music" if info.get("duration", 0) >= 15 else "sfx"
    if info.get("pix_fmt", "").startswith(("yuva", "rgba", "argb", "bgra", "abgr", "gbrap")):
        return "overlay"
    return "video"


def analyze_file(root, rel):
    """Analyse one file once (cached by content hash in analysis/)."""
    root = Path(root)
    sha = E.hashed(root, rel)
    cache = root / "analysis" / (sha[:20] + ".json")
    if cache.exists():
        return read_json(cache)
    path = inside(root, rel)
    if Path(rel).suffix.lower() in {".srt", ".vtt", ".cube"} | DOC_EXT:
        result = {"file": rel, "sha256": sha, "kind": kind_of(rel, {})}
        write_json(cache, result)
        return result
    info = media.probe(path)
    pix = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=pix_fmt", "-of", "csv=p=0",
                          str(path.resolve())], capture_output=True, text=True).stdout.strip() if info["has_video"] else ""
    info["pix_fmt"] = pix
    kind = kind_of(rel, info)
    result = {"file": rel, "sha256": sha, "kind": kind, "probe": info, "analyzed": now()}
    dur = info["duration"]
    if kind == "video" and dur > 0:
        cuts = media.scene_cuts(path, 0.3)
        edges = [0.0] + [c for c in cuts if 0.2 < c < dur - 0.2] + [dur]
        result["shots"] = [{"start": round(a, 3), "end": round(b, 3)} for a, b in zip(edges, edges[1:]) if b - a > 0.3]
        step, frames = samples(path, dur)
        motion = motion_series(frames)
        result["sample_step"] = round(step, 3)
        result["motion"] = {"mean": round(sum(motion) / len(motion), 4) if motion else 0.0,
                            "peaks": sorted(({"at": round((i + 1) * step, 2), "value": round(m, 4)} for i, m in enumerate(motion)),
                                            key=lambda x: -x["value"])[:5]}
        result["motion_series"] = [round(m, 4) for m in motion]
        tones = [media.tone(f) for f in frames]
        pix_all = [p for f in frames for p in f[::4]]
        result["colour"] = {"luma": round(sum(t["luma"] for t in tones) / max(len(tones), 1), 1),
                            "saturation": round(sum(t["saturation"] for t in tones) / max(len(tones), 1), 3),
                            "palette": [h for h, _ in media.palette(pix_all, 5)]}
        result["black"] = media.black_segments(path, 0.5)
    if info.get("has_audio") and dur > 0:
        result["loudness"] = media.loudness(path)
        segs = activity(path, dur)
        result["audio_segments"] = segs
        result["audio_activity"] = round(sum(s["end"] - s["start"] for s in segs) / dur, 3)
    if kind == "music":
        result["beats"] = beats(path)
    write_json(cache, result)
    return result


def label(a):
    """Heuristic footage type for a video analysis (a guess, not a fact)."""
    if a["kind"] != "video":
        return a["kind"]
    act, mot = a.get("audio_activity", 0), a.get("motion", {}).get("mean", 0)
    sat = a.get("colour", {}).get("saturation", 0.3)
    if act > 0.55 and mot < 0.06:
        return "talking"
    if mot >= 0.10:
        return "action"
    if mot < 0.015 and sat < 0.15:
        return "screen"
    return "broll"


def assets(root):
    """Analyse every ingested file; write assets.json grouped by kind with footage guesses."""
    root = Path(root)
    with project_lock(root):
        return _assets(root)


def _assets(root):
    log = read_json(root / "media.json")["files"] if (root / "media.json").exists() else {}
    files = sorted(set(log) | {"raw/" + p.name for p in (root / "raw").glob("*") if p.is_file()})
    items = []
    for rel in files:
        a = analyze_file(root, rel)
        t = transcript_for(root, rel)
        items.append({"file": rel, "kind": a["kind"], "label": label(a), "duration": round(a.get("probe", {}).get("duration", 0), 2),
                      "size": "{}x{}".format(a["probe"].get("width"), a["probe"].get("height")) if a.get("probe", {}).get("has_video") else None,
                      "audio_activity": a.get("audio_activity"), "motion": a.get("motion", {}).get("mean"),
                      "shots": len(a.get("shots", [])), "transcript": bool(t), "bpm": (a.get("beats") or {}).get("bpm")})
    write_json(root / "assets.json", {"updated": now(), "assets": items})
    return items


# ---- beats ----------------------------------------------------------------------

def beats(path, rate=8000, hop=256):
    """Tempo and beat times from an onset-strength envelope (energy flux + autocorrelation).
    Good for steady music; returns confidence so Mann knows when to place cuts by hand."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(Path(path).resolve()), "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
                         capture_output=True, timeout=600).stdout
    pcm = array("h")
    pcm.frombytes(raw[:len(raw) - len(raw) % 2])
    if len(pcm) < rate * 3:
        return {"bpm": None, "beats": [], "confidence": 0.0}
    env = []
    for i in range(0, len(pcm) - hop, hop):
        block = pcm[i:i + hop]
        env.append(math.sqrt(sum(x * x for x in block) / hop))
    flux = [0.0] + [max(0.0, b - a) for a, b in zip(env, env[1:])]
    mean = sum(flux) / len(flux)
    flux = [f - mean for f in flux]
    fps = rate / float(hop)
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 70)
    best, best_lag, scores = -1e18, None, []
    for lag in range(lo, hi + 1):
        s = sum(flux[i] * flux[i - lag] for i in range(lag, len(flux)))
        scores.append(s)
        if s > best:
            best, best_lag = s, lag
    if not best_lag or best <= 0:
        return {"bpm": None, "beats": [], "confidence": 0.0}
    spread = sorted(scores)
    confidence = round((best - spread[len(spread) // 2]) / (abs(best) + 1e-9), 3)
    k = best_lag - lo
    lag = float(best_lag)
    if 0 < k < len(scores) - 1:  # parabolic peak refinement between envelope frames
        a, b, c = scores[k - 1], scores[k], scores[k + 1]
        denom = a - 2 * b + c
        if denom:
            lag += max(-0.5, min(0.5, 0.5 * (a - c) / denom))
    period = lag / fps
    phase = max(range(best_lag), key=lambda p: sum(flux[int(round(p + j * lag))] for j in range(int((len(flux) - p) / lag))))
    times, t = [], phase / fps
    while t < len(flux) / fps:
        times.append(round(t, 3))
        t += period
    return {"bpm": round(60.0 / period, 1), "beats": times, "confidence": confidence}


# ---- suggestions ----------------------------------------------------------------

def profile(root):
    root = Path(root)
    analyses = [analyze_file(root, a["file"]) for a in read_json(root / "assets.json")["assets"]] if (root / "assets.json").exists() \
        else [analyze_file(root, a["file"]) for a in _assets(root)]
    videos = [a for a in analyses if a["kind"] == "video"]
    require(videos, "No video footage found in raw/; ingest the owner's clips first")
    total = sum(v["probe"]["duration"] for v in videos)
    weight = lambda key: sum((v.get(key) or 0) * v["probe"]["duration"] for v in videos) / total
    vertical = sum(v["probe"]["duration"] for v in videos if v["probe"]["height"] > v["probe"]["width"])
    labels = {}
    for v in videos:
        labels[label(v)] = labels.get(label(v), 0) + v["probe"]["duration"]
    return {"videos": videos, "music": [a for a in analyses if a["kind"] == "music"], "sfx": [a for a in analyses if a["kind"] == "sfx"],
            "images": [a for a in analyses if a["kind"] == "image"], "overlays": [a for a in analyses if a["kind"] == "overlay"],
            "total_seconds": round(total, 2), "audio_activity": round(weight("audio_activity"), 3),
            "motion": round(sum(v.get("motion", {}).get("mean", 0) * v["probe"]["duration"] for v in videos) / total, 4),
            "orientation": "vertical" if vertical > total / 2 else "horizontal", "labels": labels,
            "shots": sum(len(v.get("shots", [])) for v in videos),
            "transcripts": [v["file"] for v in videos if transcript_for(root, v["file"])]}


def motion_band(m):
    return "low" if m < 0.04 else ("high" if m >= 0.10 else "mid")


def score_style(s, prof, brief_words, aspect):
    fit = s["fit"]
    score, why = 0.0, []
    act = prof["audio_activity"]
    if fit["speech"] == "high":
        score += 3 * act
        why.append("voice-led ({:.0%} audio activity)".format(act)) if act > 0.5 else None
    elif fit["speech"] == "low":
        score += 3 * (1 - act)
        why.append("works without dialogue") if act < 0.4 else None
    else:
        score += 1.5
    band, order = motion_band(prof["motion"]), ["low", "mid", "high"]
    if fit["motion"] == "any":
        score += 1
    else:
        gap = abs(order.index(fit["motion"]) - order.index(band))
        score += (2, 1, 0)[gap]
        why.append("{} motion footage".format(band)) if gap == 0 else None
    target = aspect or ("9:16" if prof["orientation"] == "vertical" else "16:9")
    if fit["orientation"] == "any" or target in s["aspect"] or s["aspect"] == "any":
        score += 1
    have = set(prof["labels"])
    overlap = have & set(fit["footage"])
    score += min(1.5 * len(overlap), 3)
    if overlap:
        why.append("footage looks like {}".format(", ".join(sorted(overlap))))
    text = set(re.findall(r"[a-z]+", " ".join([s["name"], s["best_for"], " ".join(s["known_from"])]).lower()))
    hits = [w for w in brief_words if w in text or w.rstrip("s") in text]
    score += min(len(hits), 3)
    if hits:
        why.append("brief mentions {}".format(", ".join(sorted(set(hits)))))
    if s["pace"]["avg_shot"] < 1.2 and prof["shots"] < 6 and fit["speech"] != "high":
        score -= 1.5
        why.append("needs more shots than this footage has")
    return round(score, 2), [w for w in why if w]


def brief_words(root):
    path = Path(root) / "BRIEF.md"
    if not path.exists():
        return []
    stop = {"this", "that", "with", "from", "video", "make", "karo", "krna", "wala", "wali", "have", "your", "about"}
    return sorted({w for w in re.findall(r"[a-z]{4,}", path.read_text(encoding="utf-8").lower()) if w not in stop})


GENERIC_IDEAS = [
    ("Start at the end", "Open on the final moment, then rewind to how it began; the loop closes at the last frame."),
    ("One-colour story", "Grade each act to its own colour so the story reads even with the sound off."),
    ("Sound-first cut", "Cut every shot on a real sound in the footage (a clap, a door, a step) instead of the music."),
    ("Silent hook", "First 1.5 s in total silence with one caption, then the music hits on the first cut."),
    ("Split-time", "Two moments from different times side by side, converging into one frame at the climax."),
]


def suggest(root, aspect=None):
    """Rank the catalog against this footage; write SUGGESTIONS.md and suggestions.json."""
    root = Path(root)
    with project_lock(root):
        return _suggest(root, aspect)


def _suggest(root, aspect):
    prof = profile(root)
    words = brief_words(root)
    ranked = sorted(((score_style(s, prof, words, aspect), s) for s in catalog()), key=lambda x: -x[0][0])
    top = [(sc, why, s) for (sc, why), s in ranked[:3]]
    lead = top[0][2]
    other = next(s for (sc, why), s in ranked[3:] if s["family"] != lead["family"])
    experiment = {"name": "{} cut + {} look".format(lead["name"], other["name"]),
                  "how": "Cut with {}'s rhythm ({}s average shot) but take {}'s colour ({}), sound ({}) and VFX ({}).".format(
                      lead["name"], lead["pace"]["avg_shot"], other["name"], other["edl"]["grade"], other["sound"].split(",")[0].lower(),
                      other["vfx"].rstrip(".").lower()),
                  "styles": [lead["slug"], other["slug"]]}
    hooks = []
    for v in prof["videos"]:
        for p in v.get("motion", {}).get("peaks", [])[:2]:
            hooks.append({"file": v["file"], "at": p["at"], "why": "strongest motion in this clip"})
        segs = v.get("audio_segments") or []
        if segs:
            hooks.append({"file": v["file"], "at": segs[0]["start"], "why": "first spoken/sound moment"})
    problems = []
    for v in prof["videos"]:
        loud = v.get("loudness") or {}
        if loud.get("true_peak") is not None and loud["true_peak"] > -0.5:
            problems.append("{}: audio peaks at {} dBTP, likely clipped in places".format(v["file"], loud["true_peak"]))
        if loud.get("lufs") is not None and loud["lufs"] < -32:
            problems.append("{}: very quiet audio ({} LUFS); expect noise when boosted".format(v["file"], loud["lufs"]))
        luma = v.get("colour", {}).get("luma", 128)
        if luma < 45:
            problems.append("{}: underexposed (mean luma {})".format(v["file"], luma))
        if luma > 215:
            problems.append("{}: overexposed (mean luma {})".format(v["file"], luma))
        for b in v.get("black", []):
            problems.append("{}: black frames {}-{}".format(v["file"], E.tc(b["start"]), E.tc(b["end"])))
    target = aspect or ("9:16" if prof["orientation"] == "vertical" else "16:9")
    if (target == "9:16") != (prof["orientation"] == "vertical"):
        problems.append("Footage is {} but the target is {}: Mann will reframe (crop) and check every frame for cut-off heads/text".format(
            prof["orientation"], target))
    if not prof["transcripts"] and prof["audio_activity"] > 0.4:
        problems.append("No Whisper transcript yet: captions and word-accurate cuts need `transcribe` (blocked hosts stop it in the cloud)")
    if not prof["music"]:
        problems.append("No music file supplied: the cut will use source sound only until the owner adds or approves a track")
    ideas = []
    for _, _, s in top:
        ideas += [{"style": s["slug"], "idea": t} for t in s["twists"]]
    ideas += [{"style": None, "idea": "{}: {}".format(n, d)} for n, d in GENERIC_IDEAS]
    plan = treatment_plan(root, prof)
    result = {"created": now(), "profile": {k: v for k, v in prof.items() if k not in ("videos", "music", "sfx", "images", "overlays")},
              "target_aspect": target,
              "recommended": [{"slug": s["slug"], "name": s["name"], "score": sc, "why": why} for sc, why, s in top],
              "experiment": experiment, "ranking": [{"slug": s["slug"], "score": sc} for (sc, _), s in ranked],
              "unique_ideas": ideas, "hook_candidates": hooks[:8], "problems": problems, "treatment_plan": plan}
    write_json(root / "suggestions.json", result)
    _atomic_text(root / "SUGGESTIONS.md", suggestions_markdown(result))
    return result


def treatment_plan(root, prof, fps=30):
    """Speaker / overlay / cover draft for the first transcribed video (method: iart-ai/motion-skills,
    MIT; see aifilm/editor/treatment.py). None without a Whisper transcript."""
    from . import treatment as TR
    for v in prof["videos"]:
        t = transcript_for(root, v["file"])
        words = [w for s in (t or {}).get("segments", []) for w in s.get("words", [])]
        if words:
            return {"file": v["file"], "rows": TR.plan(TR.sentences(words), fps)}
    return None


def clip_candidates(root, candidates):
    """Long video to shorts (method: agricidaniel/claude-shorts, MIT): snap each candidate
    ({source, start, end, scores}) to the source's Whisper words, take its text from the snapped
    words, score it with the weighted rubric and red flags, rank, and write analysis/clips.json."""
    root = Path(root)
    with project_lock(root):
        out = []
        for c in candidates:
            t = transcript_for(root, c["source"])
            words = [w for s in (t or {}).get("segments", []) for w in s.get("words", [])]
            snapped = snap_clip(words, float(c["start"]), float(c["end"]))
            text = " ".join(w["word"].strip() for w in words if snapped["start"] - 0.01 <= w["start"] and w["end"] <= snapped["end"] + 0.01)
            out.append(dict(c, **snapped, text=text or c.get("text", ""), transcript=bool(words)))
        ranked = rank_clips(out)
        write_json(root / "analysis" / "clips.json", {"created": now(), "clips": ranked})
        return ranked


def suggestions_markdown(r):
    p = r["profile"]
    lines = ["# Edit suggestions", "",
             "Footage: {}s of video in {} shots, mostly {}, audio activity {:.0%}, motion {} ({}). Labels are guesses: {}.".format(
                 p["total_seconds"], p["shots"], p["orientation"], p["audio_activity"], p["motion"], motion_band(p["motion"]),
                 ", ".join("{} {:.0f}s".format(k, v) for k, v in p["labels"].items())), "",
             "## Recommended styles (owner picks one)", ""]
    for i, s in enumerate(r["recommended"], 1):
        lines.append("{}. **{}** (`{}`), score {}: {}".format(i, s["name"], s["slug"], s["score"], "; ".join(s["why"]) or "general fit"))
    e = r["experiment"]
    lines += ["", "**experiment:** {}. {}".format(e["name"], e["how"]), "", "## Unique ways to edit this footage", ""]
    lines += ["- {}{}".format("[{}] ".format(i["style"]) if i["style"] else "", i["idea"]) for i in r["unique_ideas"]]
    lines += ["", "## Hook candidates", ""] + ["- `{}` at {}: {}".format(h["file"], E.tc(h["at"]), h["why"]) for h in r["hook_candidates"]]
    lines += ["", "## Problems found", ""] + (["- " + x for x in r["problems"]] or ["- none measured"])
    plan = r.get("treatment_plan")
    lines += ["", "## Speaker / overlay / cover (draft per line)", ""]
    if plan:
        from .treatment import table_markdown
        lines += ["From `{}`'s transcript. A draft: covers need B-roll that shows what the line says, and on-screen words come only "
                  "from what is said. Put the chosen `treatment`/`timing` on the EDL beats; craft-check holds the rhythm.".format(plan["file"]), "",
                  table_markdown(plan["rows"]).rstrip("\n")]
    else:
        lines.append("- needs a transcript (`transcribe`) to plan per line")
    lines += ["", "Next: the owner finalises a style (`approve-style`), then `autocut --style <slug>` drafts the cut for the storyboard.", ""]
    return "\n".join(lines)


# ---- autocut --------------------------------------------------------------------

def pick_music(prof):
    return max(prof["music"], key=lambda m: m["probe"]["duration"]) if prof["music"] else None


def speech_segments(root, v, gap):
    """Spoken spans: Whisper word timings when available, else audio-activity islands."""
    t = transcript_for(root, v["file"])
    words = [w for s in (t or {}).get("segments", []) for w in s.get("words", [])]
    if words:
        spans, cur = [], [words[0]["start"], words[0]["end"]]
        for w in words[1:]:
            if w["start"] - cur[1] > max(gap, 0.12):
                spans.append(cur)
                cur = [w["start"], w["end"]]
            else:
                cur[1] = w["end"]
        spans.append(cur)
        return [{"start": a, "end": b} for a, b in spans], words
    return [dict(s) for s in v.get("audio_segments", [])], []


def chunk(spans, max_len):
    out = []
    for s in spans:
        a = s["start"]
        while s["end"] - a > max_len * 1.4:
            out.append({"start": a, "end": a + max_len})
            a += max_len
        out.append({"start": a, "end": s["end"]})
    return [s for s in out if s["end"] - s["start"] >= 0.3]


def montage_segments(v, length):
    """One segment per shot, centred on the shot's strongest motion sample."""
    series, step = v.get("motion_series", []), v.get("sample_step", 1.0)
    dur = v["probe"]["duration"]
    segs = []
    for shot in v.get("shots") or [{"start": 0.0, "end": dur}]:
        span = shot["end"] - shot["start"]
        n = max(1, int(span // max(length * 2.5, 1.0)))
        for k in range(n):
            a0 = shot["start"] + k * span / n
            b0 = a0 + span / n
            inside_idx = [i for i in range(len(series)) if a0 <= (i + 1) * step < b0]
            centre = (max(inside_idx, key=lambda i: series[i]) + 1) * step if inside_idx else (a0 + b0) / 2
            L = min(length, b0 - a0)
            a = min(max(centre - L / 2, a0), b0 - L)
            energy = max((series[i] for i in inside_idx), default=0.0)
            segs.append({"start": round(a, 3), "end": round(a + L, 3), "energy": energy})
    return [s for s in segs if s["end"] - s["start"] >= 0.25]


def autocut(root, slug, seconds=None, aspect=None, title=None):
    """Draft edl.json in a style from the analysed footage. It is a draft for the storyboard,
    never approved by itself; Mann reviews and refines it before showing the owner."""
    root = Path(root)
    with project_lock(root):
        return _autocut(root, slug, seconds, aspect, title)


def _autocut(root, slug, seconds, aspect, title):
    s = style(slug)
    cfg = s["edl"]
    prof = profile(root)
    aspect = aspect or (s["aspect"].split()[0] if s["aspect"].split()[0] in SIZES else ("9:16" if prof["orientation"] == "vertical" else "16:9"))
    require(aspect in SIZES, "aspect must be one of {}".format(sorted(SIZES)))
    W, H = SIZES[aspect]
    avg = float(cfg.get("max_clip") or s["pace"]["avg_shot"])
    if seconds is None:
        seconds = 30.0 if aspect in ("9:16", "4:5") else 60.0
    videos = sorted(prof["videos"], key=lambda v: v["file"])
    sources = {"V{}".format(i + 1): v["file"] for i, v in enumerate(videos)}
    sid = {f: k for k, f in sources.items()}
    music = pick_music(prof)
    speech_led = s["fit"]["speech"] == "high" or (s["fit"]["speech"] == "any" and prof["audio_activity"] > 0.5)
    notes, clips, words_by_source = [], [], {}
    gap = float(cfg.get("silence_cut") or 0.35)
    if speech_led:
        aroll = max(videos, key=lambda v: v.get("audio_activity", 0))
        spans, words = speech_segments(root, aroll, gap)
        words_by_source[sid[aroll["file"]]] = words
        if not words:
            notes.append("Cuts follow audio-activity islands, not words: run `transcribe` for word-accurate cuts and captions.")
        pad = 0.06
        spans = chunk([{"start": max(sp["start"] - pad, 0), "end": min(sp["end"] + pad, aroll["probe"]["duration"])} for sp in spans], avg * 1.6)
        used = 0.0
        for sp in spans:
            if used >= seconds:
                break
            clips.append({"source": sid[aroll["file"]], "in": round(sp["start"], 3), "out": round(sp["end"], 3), "beat": "A-roll"})
            used += sp["end"] - sp["start"]
        broll = [v for v in videos if v is not aroll]
        every = int(cfg.get("broll_every") or (3 if broll else 0))
        if broll and every:
            pool = [(v, seg) for v in broll for seg in montage_segments(v, min(avg, 2.0))]
            pool.sort(key=lambda x: -x[1]["energy"])
            for i, c in enumerate(clips):
                if pool and i % every == every - 1:
                    v, seg = pool.pop(0)
                    length = min(seg["end"] - seg["start"], (c["out"] - c["in"]) * 0.9)
                    c["inserts"] = [{"source": sid[v["file"]], "in": seg["start"], "out": round(seg["start"] + length, 3), "at": 0.0}]
            notes.append("B-roll covers every {}th A-roll cut as a picture insert; the voice keeps running underneath.".format(every))
    else:
        speed = float(cfg.get("speed_montage") or 1.0)
        segs = [(v, seg) for v in videos for seg in montage_segments(v, avg * speed)]
        require(segs, "No usable shots found in the footage")
        hook = max(segs, key=lambda x: x[1]["energy"])
        ordered = [hook] + [x for x in segs if x is not hook]
        used = 0.0
        for v, seg in ordered:
            if used >= seconds:
                break
            dur = (seg["end"] - seg["start"]) / speed
            clips.append({"source": sid[v["file"]], "in": seg["start"], "out": seg["end"], "beat": "hook: strongest motion" if not clips else "montage",
                          **({"speed": speed} if speed != 1.0 else {})})
            used += dur
        notes.append("Montage: one segment per shot at its strongest motion, the strongest shot first as the hook.")
    require(clips, "The footage gave no usable segments for this style")
    if cfg.get("beat_sync") and music and (music.get("beats") or {}).get("bpm"):
        beat = 60.0 / music["beats"]["bpm"]
        n = max(1, round(avg / beat))
        for c in clips:
            src_dur = next(v for v in videos if sid[v["file"]] == c["source"])["probe"]["duration"]
            c["out"] = round(min(c["in"] + n * beat * c.get("speed", 1.0), src_dur), 3)
        notes.append("Beat-synced: every clip is {} beat(s) at {} BPM (confidence {}).".format(n, music["beats"]["bpm"], music["beats"]["confidence"]))
    elif cfg.get("beat_sync"):
        notes.append("Style wants beat sync but no music with a detectable tempo was supplied.")
    for i, c in enumerate(clips):
        c["id"] = "C{:02d}".format(i + 1)
        alt = cfg.get("speed_alternate")
        if alt and not speech_led:
            c["speed"] = alt[i % 2]
            src_dur = next(v for v in videos if sid[v["file"]] == c["source"])["probe"]["duration"]
            c["out"] = round(min(c["in"] + (c["out"] - c["in"]) * c["speed"], src_dur), 3)
        zoom_every, z = int(cfg.get("zoom_every") or 0), cfg.get("zoom") or [1.0, 1.1]
        if zoom_every and i % zoom_every == zoom_every - 1:
            c["zoom"] = {"from": z[1], "to": z[1]} if speech_led else {"from": z[0], "to": z[1]}
        every = int(cfg.get("transition_every") or 0)
        if i and every and i % every == 0 and cfg.get("transition", "cut") != "cut":
            c["transition_in"] = {"type": cfg["transition"], "duration": cfg.get("transition_s", 0.3)}
        for fx, n in (cfg.get("fx_every") or {}).items():
            if n and i % n == n - 1:
                c.setdefault("fx", []).append(fx)
        for fx in cfg.get("fx_all") or []:
            c.setdefault("fx", []).append(fx)
    last, first = clips[-1], clips[0]
    for fx in cfg.get("fx_last") or []:
        last.setdefault("fx", []).append(fx)
    if cfg.get("freeze_last"):
        last["freeze"] = cfg["freeze_last"]
    if cfg.get("freeze_first"):
        first["freeze"] = cfg["freeze_first"]
    if cfg.get("slowmo_last") and not speech_led:
        last["speed"] = cfg["slowmo_last"]
        last["out"] = round(last["in"] + (last["out"] - last["in"]) * cfg["slowmo_last"], 3)
    for i, c in enumerate(clips):  # transitions must be shorter than both neighbours
        if i and c.get("transition_in"):
            limit = min(E.clip_duration(c), E.clip_duration(clips[i - 1])) * 0.8
            if c["transition_in"]["duration"] >= limit:
                c["transition_in"] = {"type": "cut"}
    from . import reframe as RF
    vertical_target = H > W
    mismatch = any((v["probe"]["height"] > v["probe"]["width"]) != vertical_target for v in videos)
    if mismatch:
        notes.append("Footage and target orientation differ: {}.".format(
            "face-aware reframing (`reframe: auto`) keeps the subject in frame" if RF.available()
            else "install OpenCV (opencv-python-headless==4.10.0.84) for face-aware reframing; centre crop used"))
    edl = {"version": 1, "title": title or brief_title(root) or "Autocut draft", "style": slug,
           "format": dict({"width": W, "height": H, "fps": 30, "fit": "cover"}, **({"reframe": "auto"} if mismatch and RF.available() else {})), "sources": sources, "clips": clips,
           "grade": {k: v for k, v in {"preset": cfg["grade"], "grain": cfg.get("grain"), "vignette": cfg.get("vignette")}.items() if v},
           "audio": {"keep_source": speech_led or not music, "source_gain_db": 0},
           "master": {"lufs": -14, "true_peak": -1},
           "notes": ["Autocut draft from style `{}` on {}. Mann reviews every clip before the storyboard.".format(slug, now()[:10])] + notes}
    if music:
        edl["audio"]["music"] = {"file": music["file"], "gain_db": cfg.get("music_db", -18), "duck": speech_led, "fade_out": 1.0}
    script = Path(root) / "SCRIPT.md"
    if script.exists():
        edl["script"] = "SCRIPT.md"
    caps = cfg.get("captions")
    cue_count = write_captions(root, edl, words_by_source, caps) if caps else 0
    if caps and cue_count:
        edl["subtitles"] = {"file": "captions.srt", "burn": True, **{k: caps[k] for k in ("size", "position", "uppercase", "color", "box")}}
        if caps.get("animate"):
            edl["subtitles"].update(animate=caps["animate"], highlight_color=caps.get("highlight_color", "yellow"), words="captions.words.json")
    elif caps:
        edl["notes"].append("Style uses captions but there is no transcript; captions are added after `transcribe`.")
    total = E.timeline(edl)[1]
    if total < seconds * 0.8:
        edl["notes"].append("The footage gave {:.1f}s of usable material for a {:.0f}s target; ask the owner for more shots or accept the shorter cut.".format(total, seconds))
    E.validate(root, edl)
    write_json(root / "edl.json", edl)
    return {"edl": str(root / "edl.json"), "clips": len(clips), "seconds": E.timeline(edl)[1], "notes": edl["notes"]}


def _atomic_text(path, text):
    """Write a text file whole or not at all (temp file + rename), like core.write_json."""
    tmp = Path(path).with_name("." + Path(path).name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def brief_title(root):
    path = Path(root) / "BRIEF.md"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return line.strip("# ").strip()[:80]
    return None


def write_captions(root, edl, words_by_source, caps):
    """Map source word timings onto the cut's timeline and write captions.srt."""
    from .tools import srt_time
    rows, _ = E.timeline(edl)
    cues, n, timeline_words = [], int(caps.get("max_words", 3)), []
    for row, clip in zip(rows, edl["clips"]):
        words = [w for w in words_by_source.get(clip["source"], []) if w["start"] >= clip["in"] - 0.02 and w["end"] <= clip["out"] + 0.02]
        speed = clip.get("speed", 1.0)
        for w in words:
            timeline_words.append({"start": round(row["start"] + (w["start"] - clip["in"]) / speed, 3),
                                   "end": round(row["start"] + (w["end"] - clip["in"]) / speed, 3), "word": w["word"].strip()})
        for k in range(0, len(words), n):
            chunk_ = words[k:k + n]
            a = row["start"] + (chunk_[0]["start"] - clip["in"]) / speed
            b = row["start"] + (chunk_[-1]["end"] - clip["in"]) / speed
            cues.append((max(a, row["start"]), min(b, row["end"]), " ".join(w["word"].strip() for w in chunk_)))
    if not cues:
        return 0
    body = "\n".join("{}\n{} --> {}\n{}\n".format(i, srt_time(a), srt_time(b), t) for i, (a, b, t) in enumerate(cues, 1))
    _atomic_text(Path(root) / "captions.srt", body)
    write_json(Path(root) / "captions.words.json", timeline_words)
    return len(cues)


def library_scan(folder):
    """Index a reusable music/SFX/LUT/overlay library folder into <folder>/mann-library.json."""
    folder = Path(folder)
    require(folder.is_dir(), "Not a folder: {}".format(folder))
    items = []
    for p in sorted(folder.rglob("*")):
        ext = p.suffix.lower()
        if not p.is_file() or ext not in AUDIO_EXT | VIDEO_EXT | IMAGE_EXT | {".cube"}:
            continue
        entry = {"file": str(p.relative_to(folder)), "kind": "lut" if ext == ".cube" else None}
        if ext != ".cube":
            info = media.probe(p) if ext not in IMAGE_EXT else {"has_video": True, "duration": 0}
            entry["kind"] = kind_of(p.name, info) if ext not in IMAGE_EXT else "image"
            entry["duration"] = round(info.get("duration", 0), 2)
            if entry["kind"] == "music":
                entry["bpm"] = beats(p)["bpm"]
        entry["tags"] = [t for t in re.split(r"[^a-z0-9]+", p.stem.lower()) if len(t) > 2]
        items.append(entry)
    write_json(folder / "mann-library.json", {"updated": now(), "items": items})
    return items


__all__ = ["assets", "suggest", "autocut", "beats", "library_scan", "catalog", "style"]
