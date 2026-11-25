"""Mann's sound pass: typed SFX cues from the EDL, SFX levels set relative to the voice,
the music start offset that lands cuts on beats, an off-beat lock check, and a short list of
the riskiest moments for a headphone check.

Methods adopted with the owner's approval (2026-11-23), re-implemented here, no code copied:
- SFX gain relative to the voice's p95 peak by role (ui -14, whoosh -12, impact -8, meme -3 dB),
  with louder-than-voice / inaudible flags: kurbaitaev/ghost-editor (MIT).
- Typed cues with offsets (whoosh 2 frames early, pop on the frame, riser ends on the next hit,
  reveal impact loudest), the music start-offset search with ms error per cut, the off-beat check
  (kicks below 120 Hz vs the beat lines), measuring on the exported MP4 and the headphone list of
  riskiest timestamps: Barty-Bart/motion-graphics (MIT).
Their loudness targets are not used: Mann masters to -14 LUFS / -1 dBTP (editor/rules.json).
Every threshold lives in editor/rules.json as an `observed` external calibration, not an owner rule.

Levels are measured on decoded audio (FFmpeg + numpy). librosa is optional: when it imports,
`beat_grid` uses its beat tracker; otherwise Mann's own `engine.beats`.
"""

import bisect
import statistics
import subprocess
from pathlib import Path

from ..core import inside, require
from . import edl as E
from . import media

ROLES = E.SFX_ROLES
DEFAULT_ROLE_DB = {"ui": -14.0, "whoosh": -12.0, "impact": -8.0, "meme": -3.0}

# cue type -> what plays, its level role, offset in frames from the anchor, and how it aligns
CUES = {
    "movement": {"sfx": "whoosh", "role": "whoosh", "offset_frames": -2, "align": "start"},
    "scene_cut": {"sfx": "whoosh", "role": "whoosh", "offset_frames": -2, "align": "start"},
    "appear": {"sfx": "pop", "role": "ui", "offset_frames": 0, "align": "start"},
    "success": {"sfx": "pop", "role": "ui", "offset_frames": 0, "align": "start"},
    "build_up": {"sfx": "riser", "role": "whoosh", "offset_frames": 0, "align": "end_on_next_hit"},
    "reveal": {"sfx": "impact", "role": "impact", "offset_frames": 0, "align": "start", "loudest": True},
    "typing": {"sfx": "typing", "role": "ui", "offset_frames": 0, "align": "loop_to_duration"},
    "meme": {"sfx": "meme", "role": "meme", "offset_frames": 0, "align": "start"},
}
CUE_NAMES = E.CUE_NAMES  # validated in edl.validate; tests keep it equal to CUES + "none"


# ---- cues ------------------------------------------------------------------------

def _q(t, fps):
    return round(max(t, 0.0) * fps) / float(fps)


def cues_from_edl(edl, fps=None, riser_seconds=1.0, rules=None):
    """Typed SFX cues from the cuts, inserts and overlays of an EDL.

    Defaults: a transition or a hard cut to another source is a `movement`/`scene_cut` whoosh
    (2 frames early); a jump cut inside one source gets none; an insert is a `movement` whoosh;
    an overlay is an `appear` pop on its first frame. `cue` on a clip, insert or overlay
    overrides the default (any of CUES, or "none"). A `build_up` riser ends on the next hit."""
    fps = float(fps or edl.get("format", {}).get("fps", 30))
    rows, total = E.timeline(edl)
    events = []
    clips = edl["clips"]
    for i, clip in enumerate(clips):
        kind, tdur = E.transition(clip)
        anchor = rows[i]["start"]
        if i == 0:
            default = None
        elif kind != "cut":
            default = "movement"
        else:
            default = "scene_cut" if clip.get("source") != clips[i - 1].get("source") else None
        events.append({"anchor": anchor, "type": clip.get("cue", default), "from": "clip " + clip["id"],
                       "span": rows[i]["duration"], "is_cut": i > 0})
        for k, ins in enumerate(clip.get("inserts", [])):
            events.append({"anchor": anchor + float(ins.get("at", 0)), "type": ins.get("cue", "movement"),
                           "from": "insert {}#{}".format(clip["id"], k), "span": ins["out"] - ins["in"], "is_cut": True})
    for k, ov in enumerate(edl.get("overlays", [])):
        events.append({"anchor": float(ov.get("at", 0)), "type": ov.get("cue", "appear"), "from": "overlay {}".format(k),
                       "span": float(ov.get("duration", 0) or 0), "is_cut": False})
    for ev in events:
        require(ev["type"] in CUE_NAMES + (None,), "{}: cue must be one of {}".format(ev["from"], list(CUE_NAMES)))
    hits = sorted({round(ev["anchor"], 4) for ev in events if ev["is_cut"] or (ev["type"] not in (None, "none", "build_up"))})
    cues = []
    for ev in events:
        if ev["type"] in (None, "none"):
            continue
        spec = dict(CUES[ev["type"]])
        if spec["sfx"] == "whoosh" and (rules or {}).get("sfx_whoosh_lead_frames") is not None:
            spec["offset_frames"] = -int(rules["sfx_whoosh_lead_frames"])
        cue = {"type": ev["type"], "sfx": spec["sfx"], "role": spec["role"], "anchor": round(ev["anchor"], 3),
               "offset_frames": spec["offset_frames"], "from": ev["from"]}
        if spec["align"] == "end_on_next_hit":
            later = [h for h in hits if h > ev["anchor"] + 0.5 / fps]
            end = later[0] if later else total
            cue["end"] = round(_q(end, fps), 3)
            cue["at"] = round(_q(end - riser_seconds, fps), 3)
        else:
            cue["at"] = round(_q(ev["anchor"] + spec["offset_frames"] / fps, fps), 3)
            if spec["align"] == "loop_to_duration":
                cue["duration"] = round(ev["span"], 3)
        if spec.get("loudest"):
            cue["loudest"] = True
        cues.append(cue)
    return sorted(cues, key=lambda c: (c["at"], c["from"]))


# ---- levels ----------------------------------------------------------------------

def decode(path, rate=48000, af=None, mono=False):
    """Decoded audio as numpy float32: (n, channels), or (n,) with mono=True."""
    import numpy as np
    cmd = ["ffmpeg", "-v", "error", "-i", str(Path(path).resolve()), "-vn"]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "1" if mono else "2", "-ar", str(rate), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, timeout=media.FFMPEG_TIMEOUT).stdout
    x = np.frombuffer(raw[:len(raw) - len(raw) % 4], dtype=np.float32)
    return x if mono else x.reshape(-1, 2)


def db(amp):
    import math
    return round(20.0 * math.log10(amp), 2) if amp > 0 else None


def window_peaks(x, rate, win=0.05):
    """Peak |sample| (max over channels) of each `win`-second window, with window start times."""
    import numpy as np
    env = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    n = int(rate * win)
    count = len(env) // n
    if not count:
        return np.zeros(0), np.zeros(0)
    peaks = env[:count * n].reshape(count, n).max(axis=1)
    return peaks, np.arange(count) * win


def voice_p95(x, rate, exclude=(), floor_db=-50.0, win=0.05):
    """p95 of the 50 ms window peaks where the voice/bed is active, skipping `exclude` spans."""
    import numpy as np
    peaks, starts = window_peaks(x, rate, win)
    keep = peaks > 10 ** (floor_db / 20.0)
    for a, b in exclude:
        keep &= ~((starts + win > a) & (starts < b))
    active = peaks[keep]
    return float(np.percentile(active, 95)) if active.size else 0.0


def peak(path):
    import numpy as np
    x = decode(path)
    return float(np.abs(x).max()) if x.size else 0.0


def role_targets(rules=None):
    return dict(DEFAULT_ROLE_DB, **((rules or {}).get("sfx_role_db_vs_voice_p95") or {}))


def sfx_gain(role, voice_p95_db, sfx_peak_db, rules=None):
    """Gain (dB) that puts an SFX's peak at its role target below the voice's p95 peak."""
    targets = role_targets(rules)
    require(role in targets, "SFX role must be one of {}".format(sorted(targets)))
    require(voice_p95_db is not None and sfx_peak_db is not None, "voice and SFX both need measurable audio")
    return round(voice_p95_db + targets[role] - sfx_peak_db, 2)


def gain_for_files(voice, sfx, role, rules=None):
    """`sfx-gain`: measure a voice recording and an SFX file and return the gain for the role."""
    v = decode(voice)
    vp, sp = db(voice_p95(v, 48000)), db(peak(sfx))
    return {"voice_p95_db": vp, "sfx_peak_db": sp, "role": role, "target_db_vs_voice": role_targets(rules)[role],
            "gain_db": sfx_gain(role, vp, sp, rules)}


def sfx_levels(root, edl, master, rules, rate=48000):
    """Measure every audio.sfx item on the exported master: its peak relative to the voice p95.
    A window whose neighbouring voice (0.1 s either side) is within 10 dB of the SFX is reported
    as masked: the SFX cannot be separated from the mix there, so it goes on the headphone list."""
    import numpy as np
    sfx = (edl.get("audio") or {}).get("sfx", [])
    if not sfx:
        return {"voice_p95_db": None, "items": []}
    x = decode(master, rate)
    spans = []
    for s in sfx:
        dur = media.probe(inside(root, s["file"]))["duration"] or 0.0
        spans.append((float(s["at"]), float(s["at"]) + dur))
    pad = 0.03
    excl = [(a - pad, b + pad) for a, b in spans]
    vp = voice_p95(x, rate, excl)
    targets = role_targets(rules)
    tol = float(rules.get("sfx_level_tolerance_db", 2.0))
    quiet = float(rules.get("sfx_inaudible_db_vs_voice_p95", -24.0))
    items = []
    for s, (a, b) in zip(sfx, spans):
        seg = x[int(a * rate):int(b * rate)]
        p = float(np.abs(seg).max()) if seg.size else 0.0
        # the voice right next to the window stands in for the voice under it (it cannot be separated from the mix)
        near = np.concatenate([x[max(int((a - pad - 0.1) * rate), 0):max(int((a - pad) * rate), 0)],
                               x[int((b + pad) * rate):int((b + pad + 0.1) * rate)]])
        local = voice_p95(near, rate) if near.size else 0.0
        item = {"file": s["file"], "at": round(a, 3), "role": s.get("role"), "peak_db": db(p), "flags": []}
        if vp <= 0 or p <= 0:
            item["flags"].append("no voice reference" if vp <= 0 else "silent")
            items.append(item)
            continue
        rel = 20.0 * np.log10(p / vp)
        item["db_vs_voice_p95"] = round(float(rel), 2)
        if local > p * 10 ** (-10 / 20.0):
            item["flags"].append("masked")
        if rel > 0:
            item["flags"].append("louder_than_voice")
        if rel < quiet:
            item["flags"].append("inaudible")
        if s.get("role") in targets:
            item["target_db"] = targets[s["role"]]
            item["delta_db"] = round(float(rel) - targets[s["role"]], 2)
            item["ok"] = abs(item["delta_db"]) <= tol and not item["flags"]
        items.append(item)
    return {"voice_p95_db": db(vp), "items": items}


# ---- beats -----------------------------------------------------------------------

def beat_grid(path, lock=True):
    """Beat times of a music file: librosa's tracker when installed, else Mann's engine.beats.
    With `lock`, the grid is shifted to the kicks below 120 Hz when they miss the beat lines."""
    grid = None
    try:
        import librosa  # optional
        y = decode(path, 22050, mono=True)
        tempo, frames = librosa.beat.beat_track(y=y, sr=22050)
        times = [round(float(t), 3) for t in librosa.frames_to_time(frames, sr=22050)]
        if len(times) >= 2:
            grid = {"bpm": round(float(getattr(tempo, "item", lambda: tempo)()), 1), "beats": times, "method": "librosa"}
    except Exception:  # librosa missing or failed: fall back to the engine's tracker
        grid = None
    if grid is None:
        from . import engine as G
        g = G.beats(path)
        grid = {"bpm": g["bpm"], "beats": g["beats"], "confidence": g["confidence"], "method": "engine"}
    if lock and len(grid["beats"]) >= 4:
        check = offbeat_check(path, grid["beats"])
        grid["lock"] = check
        if check.get("locked") is False:
            grid["beats"] = [round(b + check["shift_s"], 3) for b in grid["beats"] if b + check["shift_s"] >= 0]
            grid["shifted_s"] = check["shift_s"]
    return grid


def period_of(beats):
    gaps = [b - a for a, b in zip(beats, beats[1:]) if b > a]
    return statistics.median(gaps) if gaps else None


def extend_grid(beats, until):
    """Continue a beat grid at its median period (music is looped under longer edits)."""
    beats = list(beats)
    p = period_of(beats)
    if not p:
        return beats
    while beats[-1] + p <= until:
        beats.append(round(beats[-1] + p, 4))
    return beats


def cut_errors(beats, cuts):
    """For each cut, the nearest beat and the signed error in ms (cut minus beat)."""
    beats = sorted(beats)
    out = []
    for c in cuts:
        i = bisect.bisect_left(beats, c)
        near = [beats[j] for j in (i - 1, i) if 0 <= j < len(beats)]
        if not near:
            continue
        b = min(near, key=lambda t: abs(t - c))
        out.append({"cut": round(c, 3), "beat": round(b, 3), "error_ms": round((c - b) * 1000.0, 1)})
    return out


def _summary(errors):
    absd = [abs(e["error_ms"]) for e in errors]
    return (statistics.median(absd), sum(absd) / len(absd)) if absd else (0.0, 0.0)


def music_offset(beats, cut_times, search=(0.0, 2.0, 0.001)):
    """Grid-search the music start offset (seconds into the music file) that minimises the
    cut-to-beat error. Beat times are in music-file time; on the timeline a beat sits at
    beat - start. Exact alignments (beat - cut) inside the range are always tried as well.
    Returns the best start, median/mean error and the ms error of every cut."""
    lo, hi, step = (tuple(search) + (0.001,))[:3]
    require(hi >= lo and step > 0, "search needs (min, max, step) with max >= min and step > 0")
    beats = sorted(float(b) for b in beats)
    cuts = sorted(float(c) for c in cut_times)
    require(len(beats) >= 2 and cuts, "need at least two beats and one cut")
    beats = extend_grid(beats, max(cuts) + hi + (period_of(beats) or 0))
    cands = {round(lo + k * step, 4) for k in range(int(round((hi - lo) / step)) + 1)}
    cands |= {round(b - c, 4) for b in beats for c in cuts if lo <= b - c <= hi}
    best = None
    for s in sorted(cands):
        errs = cut_errors([b - s for b in beats if b - s >= -1.0], cuts)
        med, mean = _summary(errs)
        key = (round(med, 3), round(mean, 3), s)
        if best is None or key < best[0]:
            best = (key, s, errs)
    _, start, errs = best
    med, mean = _summary(errs)
    return {"start": round(start, 3), "median_error_ms": round(med, 1), "mean_error_ms": round(mean, 1), "per_cut": errs}


def offbeat_check(path, beats, bars=4, beats_per_bar=4, cutoff=120, tolerance=0.035, rate=4000, hop=0.005, start=0.0):
    """Do the kicks (energy below `cutoff` Hz) land on the beat lines? Looks at `bars` bars from
    `start`, finds the shift of the grid that best fits the low-band onsets and calls the grid
    locked when that shift is within `tolerance` seconds."""
    import numpy as np
    beats = [b for b in sorted(beats) if b >= start][:bars * beats_per_bar]
    p = period_of(beats)
    if len(beats) < 2 or not p:
        return {"locked": None, "reason": "fewer than two beats"}
    x = decode(path, rate, af="lowpass=f={0},lowpass=f={0}".format(cutoff), mono=True)
    n = max(int(rate * hop), 1)
    count = len(x) // n
    if not count:
        return {"locked": None, "reason": "no audio"}
    env = np.sqrt((x[:count * n].reshape(count, n) ** 2).mean(axis=1))
    flux = np.maximum(np.diff(env, prepend=env[0]), 0.0)
    if float(flux.max()) <= 1e-5:
        return {"locked": None, "reason": "no kick energy below {} Hz".format(cutoff)}
    half = int(p / 2 / hop)
    best, best_s = -1.0, 0
    for s in range(-half, half + 1):
        idx = [int(round(b / hop)) + s for b in beats]
        score = sum(float(flux[max(i - 1, 0):i + 2].max()) for i in idx if 0 <= i < count)
        if score > best + 1e-9 or (abs(score - best) <= 1e-9 and abs(s) < abs(best_s)):
            best, best_s = score, s
    shift = round(best_s * hop, 3)
    return {"locked": abs(shift) <= tolerance, "shift_s": shift, "shift_ms": round(shift * 1000.0, 1),
            "checked_beats": len(beats), "cutoff_hz": cutoff}


def cut_times(edl):
    """Where each cut lands on the timeline (a transition counts at its midpoint)."""
    rows, _ = E.timeline(edl)
    out = []
    for i, clip in enumerate(edl["clips"][1:], start=1):
        _, tdur = E.transition(clip)
        out.append(round(rows[i]["start"] + tdur / 2.0, 3))
    return out


def music_report(root, edl, search=None, master=None, rules=None):
    """Cut-to-beat error for the music as placed in the EDL, the best start offset, and (with
    `master`) the off-beat check measured on the exported file's low band."""
    rules = rules or {}
    music = (edl.get("audio") or {}).get("music")
    if not music:
        return None
    cuts = cut_times(edl)
    fps = float(edl["format"].get("fps", 30))
    grid = beat_grid(inside(root, music["file"]))
    beats = grid["beats"]
    p = period_of(beats)
    rep = {"bpm": grid.get("bpm"), "method": grid["method"], "beats": len(beats), "cuts": len(cuts), "frame_ms": round(1000.0 / fps, 1)}
    if grid.get("shifted_s"):
        rep["grid_shifted_s"] = grid["shifted_s"]
    if len(beats) < 2 or not p or not cuts:
        rep["note"] = "no usable beat grid or no cuts"
        return rep
    start = float(music.get("start", 0))
    _, total = E.timeline(edl)
    full = extend_grid(beats, start + total + p)
    errs = cut_errors([b - start for b in full if b >= start], cuts)
    med, mean = _summary(errs)
    rep.update({"start": start, "median_error_ms": round(med, 1), "mean_error_ms": round(mean, 1), "per_cut": errs})
    best = music_offset(beats, cuts, search or (0.0, round(4 * p, 3), 0.001))
    rep["best_start"] = best["start"]
    rep["best_median_error_ms"] = best["median_error_ms"]
    if master:
        tl = [round(b - start, 3) for b in full if b >= start and b - start <= total]
        rep["offbeat"] = offbeat_check(master, tl, cutoff=int(rules.get("beat_kick_lowpass_hz", 120)), tolerance=1.0 / fps)
    return rep


# ---- QC --------------------------------------------------------------------------

def riskiest(levels, music, count=5, fps=30.0):
    """The `count` timestamps most worth a headphone check, worst first."""
    frame_ms = 1000.0 / fps
    risks = []
    for it in (levels or {}).get("items", []):
        flags = it.get("flags", [])
        score = 10.0 if "louder_than_voice" in flags else 8.0 if "inaudible" in flags else 6.0 if "masked" in flags else 0.0
        score = max(score, abs(it.get("delta_db", 0.0)), 3.0 if not it.get("role") else 0.0)
        why = "SFX `{}` ({}): {}".format(it["file"], it.get("role") or "no role",
                                         ", ".join(flags) or "{:+.1f} dB vs role target".format(it.get("delta_db", 0.0)))
        risks.append({"at": it["at"], "score": round(score, 2), "why": why})
    for e in (music or {}).get("per_cut", []):
        risks.append({"at": e["cut"], "score": round(abs(e["error_ms"]) / frame_ms, 2),
                      "why": "cut {:+.0f} ms off the beat".format(e["error_ms"])})
    off = (music or {}).get("offbeat") or {}
    if off.get("locked") is False:
        risks.append({"at": 0.0, "score": round(abs(off["shift_ms"]) / frame_ms, 2),
                      "why": "beat grid off the kicks by {:+.0f} ms".format(off["shift_ms"])})
    risks.sort(key=lambda r: (-r["score"], r["at"]))
    return [dict(r, tc=E.tc(r["at"])) for r in risks[:count]]


def qc_checks(root, edl, master, rules):
    """Sound checks on the exported master for render.qc: SFX levels vs role targets, cut-to-beat
    error and the off-beat check. Returns (checks, measured, riskiest)."""
    checks = []

    def check(name, ok, detail, kind="warn"):
        checks.append({"check": name, "result": "pass" if ok else kind, "detail": detail})

    fps = float(edl["format"].get("fps", 30))
    levels = sfx_levels(root, edl, master, rules)
    for it in levels["items"]:
        name = "sfx level {} ({})".format(E.tc(it["at"]), it.get("role") or "no role")
        if not it.get("role"):
            check(name, False, "`{}` has no role; set audio.sfx[].role to one of {}".format(it["file"], "/".join(ROLES)))
        elif "db_vs_voice_p95" not in it:
            check(name, False, "`{}`: {}".format(it["file"], ", ".join(it["flags"])))
        else:
            check(name, it["ok"], "{:+.1f} dB vs voice p95 (target {:+.0f} ±{}){}".format(
                it["db_vs_voice_p95"], it["target_db"], rules.get("sfx_level_tolerance_db", 2.0),
                "; " + ", ".join(it["flags"]) if it["flags"] else ""))
    music = music_report(root, edl, master=master, rules=rules) if (edl.get("audio") or {}).get("music") else None
    if music and "per_cut" in music:
        limit = float(rules.get("cut_to_beat_max_median_frames", 1)) * 1000.0 / fps
        worst = max(music["per_cut"], key=lambda e: abs(e["error_ms"]))
        check("cut-to-beat", music["median_error_ms"] <= limit,
              "median {} ms, worst {:+.0f} ms at {} (max median {:.0f} ms = {} frame); best music start {}s gives {} ms".format(
                  music["median_error_ms"], worst["error_ms"], E.tc(worst["cut"]), limit, rules.get("cut_to_beat_max_median_frames", 1),
                  music["best_start"], music["best_median_error_ms"]))
        off = music.get("offbeat") or {}
        if off.get("locked") is not None:
            check("beat grid on the kicks", off["locked"], "grid vs kicks <{} Hz: {:+.0f} ms".format(off["cutoff_hz"], off["shift_ms"]))
    risky = riskiest(levels, music, int(rules.get("headphone_check_count", 5)), fps)
    return checks, {"sfx_levels": levels, "music": music}, risky


__all__ = ["cues_from_edl", "sfx_gain", "gain_for_files", "sfx_levels", "music_offset", "cut_errors", "offbeat_check",
           "beat_grid", "music_report", "riskiest", "qc_checks", "CUES", "ROLES"]
