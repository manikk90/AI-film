"""Mann's edit decision list (EDL): validation, timeline maths, the filter graph per clip,
the storyboard and the owner's approval gates.

An edit project is a folder (normally `projects/<slug>/edit/`, git-ignored):

    BRIEF.md            the owner's script / direction (verbatim)
    raw/                the owner's footage, music and SFX (never modified)
    media.json          probe + sha256 of every ingested file
    analysis/           the smart engine's per-file analysis (cached by hash)
    SUGGESTIONS.md      the engine's edit suggestions for this footage
    edl.json            Mann's cut (this module's schema)
    storyboard/         numbered frames + STORYBOARD.md + storyboard.json; part/ for one-part corrections
    approvals.json      the owner's decisions: style, script lock, storyboard (whole or per part), final
    renders/            master.mp4, preview_720p.mp4, parts/, QC.md, qc.json

Approvals are per clip. The "globals" (format, grade, audio, overlays, subtitles, style,
script, clip order) and each clip have their own fingerprint, so a correction to one part
needs only that part re-approved, while a whole-video change needs the whole storyboard.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

from ..core import ProductionError, file_hash, fingerprint, inside, now, project_lock, read_json, require, write_json
from . import media

TRANSITIONS = {
    "cut", "fade", "fadeblack", "fadewhite", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown",
    "slideleft", "slideright", "slideup", "slidedown", "smoothleft", "smoothright", "circleopen", "circleclose",
    "radial", "pixelize", "zoomin", "hblur", "distance", "squeezeh", "squeezev",
}
# Colour presets: FFmpeg filter chains. They are starting points, judged on the storyboard frames.
GRADES = {
    "neutral": "",
    "punchy-social": "eq=contrast=1.12:saturation=1.28:gamma=0.97,unsharp=5:5:0.4",
    "teal-orange": "colorbalance=rs=-0.06:gs=0.0:bs=0.09:rh=0.09:gh=0.02:bh=-0.08,eq=contrast=1.08:saturation=1.12",
    "warm-film": "colorbalance=rm=0.06:bm=-0.05:rh=0.04,eq=contrast=1.05:saturation=0.95,noise=alls=5:allf=t",
    "cool-night": "colorbalance=bs=0.10:bm=0.06:rh=-0.04,eq=brightness=-0.03:saturation=0.88:contrast=1.06",
    "bw-contrast": "hue=s=0,eq=contrast=1.30:gamma=0.95",
    "faded-vintage": "curves=preset=vintage,eq=saturation=0.85",
    "moody-dark": "eq=brightness=-0.05:contrast=1.15:saturation=0.85,vignette=PI/4.5",
    "bright-clean": "eq=brightness=0.03:contrast=1.04:saturation=1.08,colorbalance=rh=0.02:bh=0.02",
    "pastel": "eq=brightness=0.04:contrast=0.92:saturation=0.9,colorbalance=rh=0.05:gh=0.02:bh=0.04:rs=0.03",
    "bleach-bypass": "eq=saturation=0.55:contrast=1.25:gamma=0.95",
    "desat-doc": "eq=saturation=0.7:contrast=1.08,colorbalance=bs=0.03:bm=0.02",
    "neon-night": "eq=saturation=1.4:contrast=1.15:brightness=-0.03,colorbalance=bs=0.08:rs=0.05:gm=-0.04",
    "vhs-retro": "curves=preset=vintage,eq=saturation=1.15:contrast=0.92,rgbashift=rh=3:bh=-3",
    "golden-hour": "colorbalance=rm=0.08:gm=0.02:bm=-0.08:rh=0.05,eq=saturation=1.1:contrast=1.03",
}
# Per-clip effects (VFX). Each is a plain FFmpeg chain applied after the grade.
FX = {
    "shake": "scale=w='2*trunc(iw*1.08/2)':h='2*trunc(ih*1.08/2)',crop={W}:{H}:x='(iw-{W})/2+(iw-{W})/2*0.8*sin(t*37)':y='(ih-{H})/2+(ih-{H})/2*0.8*sin(t*29+1)'",
    "flash": "fade=t=in:st=0:d=0.15:color=white",
    "fade_in": "fade=t=in:st=0:d=0.4",
    "rgb_split": "rgbashift=rh=6:bh=-6:rv=2:bv=-2",
    "letterbox": "drawbox=x=0:y=0:w=iw:h=ih*0.11:color=black:t=fill,drawbox=x=0:y=ih*0.89:w=iw:h=ih*0.11:color=black:t=fill",
    "step_print": "fps=12,tmix=frames=3",
    "vhs": "noise=alls=14:allf=t,gblur=sigma=0.6",
    "stop_motion": "fps=10",
    "glow": "eq=brightness=0.04:saturation=1.1,gblur=sigma=1.2",
    "bw": "hue=s=0",
}
TEXT_POSITIONS = {"top": "h*0.18", "center": "(h-text_h)/2", "bottom": "h*0.66"}
SUB_COLOURS = {"white": "&H00FFFFFF", "yellow": "&H0000F0FF", "green": "&H0033FF66", "red": "&H003333FF", "cyan": "&H00FFFF00"}
DEVANAGARI = re.compile("[ऀ-ॿ]")


def load(root):
    root = Path(root)
    edl = read_json(root / "edl.json")
    validate(root, edl)
    return edl


def num(value, name, low=None, high=None):
    require(isinstance(value, (int, float)) and not isinstance(value, bool), name + " must be a number")
    require(low is None or value >= low, "{} must be >= {}".format(name, low))
    require(high is None or value <= high, "{} must be <= {}".format(name, high))
    return float(value)


def clip_duration(clip):
    return (clip["out"] - clip["in"]) / clip.get("speed", 1.0) + float(clip.get("freeze", 0) or 0)


def transition(clip):
    t = clip.get("transition_in") or {"type": "cut"}
    return t.get("type", "cut"), (0.0 if t.get("type", "cut") == "cut" else float(t.get("duration", 0.5)))


def as_list(value):
    return value if isinstance(value, list) else ([value] if value else [])


def validate(root, edl):
    require(isinstance(edl, dict) and edl.get("version") == 1, "edl.json needs \"version\": 1")
    fmt = edl.get("format", {})
    for key in ("width", "height"):
        require(isinstance(fmt.get(key), int) and fmt[key] >= 16 and fmt[key] % 2 == 0, "format.{} must be an even integer".format(key))
    num(fmt.get("fps", 30), "format.fps", 1, 120)
    require(fmt.get("reframe") in (None, "auto", "center"), "format.reframe must be auto or center")
    sources = edl.get("sources")
    require(isinstance(sources, dict) and sources, "sources must map ids to files in the edit folder")
    probes = {}
    for sid, rel in sources.items():
        require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", sid) is not None, "Bad source id " + sid)
        probes[sid] = media.probe(inside(root, rel))
        require(probes[sid]["has_video"], "Source {} has no video stream".format(sid))
    clips = edl.get("clips")
    require(isinstance(clips, list) and clips, "clips must be a nonempty list")
    seen = set()
    for i, clip in enumerate(clips):
        cid = clip.get("id")
        require(isinstance(cid, str) and re.fullmatch(r"[A-Za-z0-9_-]+", cid) is not None and cid not in seen,
                "Clip {} needs a unique id (letters, digits, - and _)".format(i + 1))
        seen.add(cid)
        require(clip.get("source") in sources, "{}: unknown source {!r}".format(cid, clip.get("source")))
        dur = probes[clip["source"]]["duration"]
        start, end = num(clip.get("in"), cid + ".in", 0), num(clip.get("out"), cid + ".out", 0)
        require(start < end, cid + ": in must be before out")
        require(end <= dur + 0.05, "{}: out {:.2f}s is past the end of {} ({:.2f}s)".format(cid, end, clip["source"], dur))
        num(clip.get("speed", 1.0), cid + ".speed", 0.25, 4.0)
        num(clip.get("freeze", 0), cid + ".freeze", 0, 10)
        require(clip.get("reframe") in (None, "auto", "center"), cid + ": reframe must be auto or center")
        kind, tdur = transition(clip)
        require(kind in TRANSITIONS, "{}: unknown transition {!r}".format(cid, kind))
        require(i > 0 or kind == "cut", cid + ": the first clip cannot have a transition in")
        if i:
            shortest = min(clip_duration(clip), clip_duration(clips[i - 1]))
            require(0 <= tdur < shortest, "{}: transition {:.2f}s must be shorter than both clips".format(cid, tdur))
        grade = clip.get("grade")
        require(grade is None or grade in GRADES, "{}: unknown grade {!r}".format(cid, grade))
        for fx in as_list(clip.get("fx")):
            require(fx in FX, "{}: unknown fx {!r}; choose from {}".format(cid, fx, sorted(FX)))
        zoom = clip.get("zoom")
        if zoom:
            num(zoom.get("from", 1.0), cid + ".zoom.from", 1.0, 3.0)
            num(zoom.get("to", 1.0), cid + ".zoom.to", 1.0, 3.0)
        for text in as_list(clip.get("text")):
            require(isinstance(text.get("value"), str) and text["value"].strip(), cid + ": text needs a value")
            require(text.get("position", "bottom") in TEXT_POSITIONS, cid + ": text position must be top/center/bottom")
            require(text.get("role") in (None, "title", "headline", "body", "caption", "label"), cid + ": text role must be title/headline/body/caption/label")
        for ins in clip.get("inserts", []):
            require(ins.get("source") in sources, "{}: insert has unknown source {!r}".format(cid, ins.get("source")))
            a, b = num(ins.get("in"), cid + ".insert.in", 0), num(ins.get("out"), cid + ".insert.out", 0)
            require(a < b <= probes[ins["source"]]["duration"] + 0.05, cid + ": insert in/out outside its source")
            at = num(ins.get("at", 0), cid + ".insert.at", 0)
            require(at + (b - a) <= clip_duration(clip) + 0.05, cid + ": insert runs past the end of its clip")
    grade = edl.get("grade", {})
    require(grade.get("preset", "neutral") in GRADES, "Unknown grade preset {!r}; choose from {}".format(grade.get("preset"), sorted(GRADES)))
    if grade.get("lut"):
        require(inside(root, grade["lut"]).is_file(), "LUT file missing: " + grade["lut"])
    audio = edl.get("audio", {})
    music = audio.get("music")
    if music:
        require(media.probe(inside(root, music["file"]))["has_audio"], "Music file has no audio")
    for sfx in audio.get("sfx", []):
        require(media.probe(inside(root, sfx["file"]))["has_audio"], "SFX {} has no audio".format(sfx["file"]))
        num(sfx.get("at"), "sfx.at", 0)
    for ov in edl.get("overlays", []):
        media.probe(inside(root, ov["file"]))
        num(ov.get("at", 0), "overlay.at", 0)
    subs = edl.get("subtitles")
    if subs:
        require(inside(root, subs["file"]).is_file(), "Subtitle file missing: " + subs["file"])
        require(subs.get("position", "bottom") in TEXT_POSITIONS, "subtitles.position must be top/center/bottom")
        require(subs.get("color", "white") in SUB_COLOURS, "subtitles.color must be one of {}".format(sorted(SUB_COLOURS)))
        require(subs.get("animate") in (None,) + ANIMATIONS, "subtitles.animate must be one of {}".format(list(ANIMATIONS)))
        if subs.get("words"):
            require(inside(root, subs["words"]).is_file(), "Caption word timings missing: " + subs["words"])
    if edl.get("script"):
        require(inside(root, edl["script"]).is_file(), "Script file missing: " + edl["script"])
    typo = edl.get("typography") or {}
    if typo:
        from . import craft
        if typo.get("pairing"):
            craft.pairing(typo["pairing"])
        if typo.get("theme"):
            craft.theme(typo["theme"])
    return probes


def timeline(edl):
    """Start time of every clip on the final timeline, and the total duration."""
    rows, cursor = [], 0.0
    for i, clip in enumerate(edl["clips"]):
        _, tdur = transition(clip)
        start = cursor - tdur if i else 0.0
        dur = clip_duration(clip)
        rows.append({"id": clip["id"], "start": round(start, 3), "end": round(start + dur, 3), "duration": round(dur, 3)})
        cursor = start + dur
    return rows, round(cursor, 3)


def pace(edl):
    rows, total = timeline(edl)
    lengths = sorted(r["duration"] for r in rows)
    mid = len(lengths) // 2
    median = lengths[mid] if len(lengths) % 2 else (lengths[mid - 1] + lengths[mid]) / 2
    return {"total_seconds": total, "shots": len(rows), "average_shot_seconds": round(total / len(rows), 2),
            "median_shot_seconds": round(median, 2), "longest_shot_seconds": lengths[-1], "shortest_shot_seconds": lengths[0],
            "cuts_per_10s": round(10.0 * max(len(rows) - 1, 0) / total, 2) if total else 0}


def tc(seconds):
    m, s = divmod(max(seconds, 0), 60)
    return "{}:{:04.1f}".format(int(m), s)


def font_for(text, override=None):
    if override:
        return override
    pattern = "sans:bold:lang=hi" if DEVANAGARI.search(text) else "sans:bold"
    if shutil.which("fc-match"):
        found = subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True).stdout.strip()
        if found:
            return found
    return None


def esc(path):
    """Escape a path for use inside an FFmpeg filter option."""
    return str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")


def grade_chain(root, edl, clip):
    g = edl.get("grade", {})
    parts = [GRADES[clip.get("grade") or g.get("preset", "neutral")]]
    eq = []
    if g.get("exposure"):
        eq.append("brightness={}".format(num(g["exposure"], "grade.exposure", -0.5, 0.5)))
    if g.get("contrast"):
        eq.append("contrast={}".format(num(g["contrast"], "grade.contrast", 0.5, 2.0)))
    if g.get("saturation") is not None:
        eq.append("saturation={}".format(num(g["saturation"], "grade.saturation", 0.0, 3.0)))
    if eq:
        parts.append("eq=" + ":".join(eq))
    if g.get("temperature"):
        parts.append("colortemperature=temperature={}".format(int(num(g["temperature"], "grade.temperature", 1000, 40000))))
    if g.get("lut"):
        parts.append("lut3d=file='{}'".format(esc(inside(root, g["lut"]))))
    if g.get("vignette"):
        parts.append("vignette=PI/5")
    if g.get("grain"):
        parts.append("noise=alls={}:allf=t".format(int(num(g["grain"], "grade.grain", 1, 40))))
    return ",".join(p for p in parts if p)


def frame_chain(edl, W, H):
    if edl["format"].get("fit", "cover") == "contain":
        return ["scale={W}:{H}:force_original_aspect_ratio=decrease".format(W=W, H=H),
                "pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black".format(W=W, H=H)]
    return ["scale={W}:{H}:force_original_aspect_ratio=increase".format(W=W, H=H), "crop={W}:{H}".format(W=W, H=H)]


def clip_video_chain(root, edl, clip, textfiles, t0=0.0):
    """FFmpeg filters that turn a trimmed source clip into a formatted, graded, titled shot."""
    fmt = edl["format"]
    W, H, fps = fmt["width"], fmt["height"], fmt.get("fps", 30)
    speed = clip.get("speed", 1.0)
    dur = clip_duration(clip)
    chain = ["setpts=(PTS-STARTPTS)/{}".format(speed)] if speed != 1.0 else ["setpts=PTS-STARTPTS"]
    from . import reframe
    chain += reframe.chain(root, edl, clip) or frame_chain(edl, W, H)
    zoom = clip.get("zoom")
    if zoom and (zoom.get("from", 1.0) != 1.0 or zoom.get("to", 1.0) != 1.0):
        z0, z1 = float(zoom.get("from", 1.0)), float(zoom.get("to", 1.0))
        expr = "({z0}+({z1}-{z0})*min(1,(t+{t0})/{d}))".format(z0=z0, z1=z1, t0=t0, d=dur)
        chain += ["scale=w='2*trunc({W}*{e}/2)':h='2*trunc({H}*{e}/2)':eval=frame".format(W=W, H=H, e=expr),
                  "crop={W}:{H}".format(W=W, H=H)]
    if clip.get("freeze"):
        chain.append("tpad=stop_mode=clone:stop_duration={:.3f}".format(float(clip["freeze"])))
    graded = grade_chain(root, edl, clip)
    if graded:
        chain.append(graded)
    for fx in as_list(clip.get("fx")):
        chain.append(FX[fx].format(W=W, H=H))
    chain += ["fps={}".format(fps), "format=yuv420p", "setsar=1", "settb=AVTB"]
    return ",".join(chain)


def insert_chain(root, edl, clip, ins, at):
    fmt = edl["format"]
    from . import reframe
    framed = reframe.chain(root, edl, clip, src=edl["sources"][ins["source"]], clip_in=ins["in"], clip_out=ins["out"], speed=1.0)
    chain = ["setpts=PTS-STARTPTS"] + (framed or frame_chain(edl, fmt["width"], fmt["height"])) + ["setpts=PTS+{:.3f}/TB".format(at)]
    graded = grade_chain(root, edl, clip)
    if graded:
        chain.append(graded)
    chain += ["fps={}".format(fmt.get("fps", 30)), "format=yuv420p", "setsar=1"]
    return ",".join(chain)


def ass_colour(name, alpha=0):
    from .craft import NAMED
    name = str(name or "white").lower()
    if re.fullmatch(r"#?[0-9a-f]{6}", name):
        h = name.lstrip("#")
        rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    else:
        rgb = NAMED.get(name, (255, 255, 255))
    return "&H{:02X}{:02X}{:02X}{:02X}".format(alpha, rgb[2], rgb[1], rgb[0])


def ass_time(t):
    cs = int(round(max(t, 0) * 100))
    return "{}:{:02d}:{:02d}.{:02d}".format(cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


def ass_text(value):
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def family_of(font_file):
    if font_file and shutil.which("fc-scan"):
        out = subprocess.run(["fc-scan", "--format", "%{family}\n", font_file], capture_output=True, text=True).stdout.strip()
        if out:
            return out.splitlines()[0].split(",")[0]
    return "Noto Sans"


ANIMATIONS = ("highlight", "pop", "word", "karaoke")


def load_words(root, subs, shift=0.0):
    """Timeline word timings for animated captions ([{start, end, word}]), or [] to estimate."""
    if not subs.get("words"):
        return []
    path = inside(root, subs["words"])
    if not path.exists():
        return []
    words = json.loads(path.read_text(encoding="utf-8"))
    upper = subs.get("uppercase")
    return [{"start": w["start"] - shift, "end": w["end"] - shift, "word": w["word"].strip().upper() if upper else w["word"].strip()}
            for w in words if w.get("word", "").strip()]


def cue_words(cue, words):
    """Words of one caption cue with timings: measured ones when they match the cue text,
    otherwise the cue's time split in proportion to word length (an estimate)."""
    tokens = " ".join(cue["lines"]).split()
    inside_ = [w for w in words if cue["start"] - 0.05 <= w["start"] < cue["end"] + 0.05]
    if inside_ and len(inside_) == len(tokens):
        return [dict(w, word=tok) for w, tok in zip(inside_, tokens)], True
    total = sum(len(tok) + 1 for tok in tokens) or 1
    out, t = [], cue["start"]
    for tok in tokens:
        d = (cue["end"] - cue["start"]) * (len(tok) + 1) / float(total)
        out.append({"start": t, "end": t + d, "word": tok})
        t += d
    return out, False


def animated_events(cue, words, mode, subs):
    """ASS events for one cue: `highlight` (current word coloured), `pop` (current word coloured
    and popping), `word` (one word at a time, popping) or `karaoke` (fill sweeps word by word)."""
    hl = ass_colour(subs.get("highlight_color", "yellow"))
    base = ass_colour(subs.get("color", "white"))
    ws, _ = cue_words(cue, words)
    if not ws:
        return []
    if mode == "karaoke":
        parts = ["{{\\1c{}\\2c{}}}".format(hl, base)]
        for w in ws:
            parts.append("{{\\kf{}}}{} ".format(max(1, int(round((w["end"] - w["start"]) * 100))), ass_text(w["word"])))
        return [(cue["start"], cue["end"], "Cap", "".join(parts).rstrip())]
    out = []
    for i, w in enumerate(ws):
        a = w["start"]
        b = ws[i + 1]["start"] if i + 1 < len(ws) else cue["end"]
        if b - a < 0.02:
            continue
        if mode == "word":
            text = "{\\fscx130\\fscy130\\t(0,110,\\fscx100\\fscy100)}" + ass_text(w["word"])
        else:
            pop = "\\fscx125\\fscy125\\t(0,100,\\fscx100\\fscy100)" if mode == "pop" else ""
            pieces = []
            for j, other in enumerate(ws):
                if j == i:
                    pieces.append("{{\\c{}{}}}{}{{\\r}}".format(hl, pop, ass_text(other["word"])))
                else:
                    pieces.append(ass_text(other["word"]))
            text = " ".join(pieces)
        out.append((a, b, "Cap", text))
    return out


def ass_script(root, edl, shift=0.0, name=".mann-text.ass"):
    """All burned text in one ASS script: on-screen text items (timeline-mapped) and subtitles.
    Rendered by FFmpeg's `ass` filter with complex shaping, so Devanagari reorders correctly
    (pre-base matras, conjuncts, anusvara); drawtext and the subtitles filter do not."""
    from . import craft
    fmt = edl["format"]
    W, H = fmt["width"], fmt["height"]
    rows, _ = timeline(edl)
    events = []
    for row, clip in zip(rows, edl["clips"]):
        for item in as_list(clip.get("text")):
            size, file_, family = craft.resolve_text(edl, item)
            family = family if (family and file_) else family_of(file_ or font_for(item["value"], item.get("font")))
            weight = 700 if item.get("role") in (None, "title", "headline", "caption") else 500
            pos = item.get("position", "bottom")
            an, y = {"top": (8, H * 0.18), "center": (5, H / 2.0), "bottom": (8, H * 0.66)}[pos]
            a = row["start"] + float(item.get("start", 0))
            b = row["start"] + float(item.get("end", row["duration"]))
            tags = "{{\\an{}\\pos({},{})\\fn{}\\fs{}\\b{}\\c{}\\bord{}}}".format(
                an, int(W / 2), int(y), family, size, weight, ass_colour(item.get("color", "white")), max(2, size // 14))
            events.append((a, b, "TxtBox" if item.get("box") else "Txt", tags + ass_text(item["value"])))
    subs = edl.get("subtitles")
    cap = None
    if subs and subs.get("burn", True):
        size = int(round(float(subs.get("size", 0.05)) * H))
        family = "Noto Sans"
        pid = (edl.get("typography") or {}).get("pairing")
        if pid:
            from . import fonts
            p = craft.pairing(pid)
            if fonts.resolve(p["text"], p.get("text_weight", 600)):
                family = p["text"]
        m = craft.subtitle_margins(fmt)
        pos = subs.get("position", "bottom")
        align = {"bottom": 2, "center": 5, "top": 8}[pos]
        margin_v = int(subs.get("margin_v_px", m["bottom"] if pos == "bottom" else m["top"]))
        box = bool(subs.get("box"))
        cap = "Style: Cap,{},{},{},&H000000FF,{},{},-1,0,0,0,100,100,0,0,{},{},0,{},{},{},{},1".format(
            family, size, ass_colour(subs.get("color", "white")), "&H80000000" if box else "&H00000000", "&H80000000",
            3 if box else 1, max(2, size // 12) if not box else max(4, size // 5), align, m["l"], m["r"], margin_v)
        from .craft import parse_srt
        text = stage_subtitles(root, edl, shift).read_text(encoding="utf-8")
        animate = subs.get("animate")
        words = load_words(root, subs, shift) if animate else []
        for c in parse_srt(text):
            if animate:
                events += animated_events(c, words, animate, subs)
            else:
                events.append((c["start"], c["end"], "Cap", ass_text("\n".join(c["lines"]))))
        (Path(root) / ".mann-subs.srt").unlink(missing_ok=True)
    if not events:
        return None
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: {}".format(W), "PlayResY: {}".format(H), "WrapStyle: 0",
             "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
             "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             "Style: Txt,Noto Sans,48,&H00FFFFFF,&H000000FF,&H26000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,8,0,0,0,1",
             "Style: TxtBox,Noto Sans,48,&H00FFFFFF,&H000000FF,&H73000000,&H73000000,-1,0,0,0,100,100,0,0,3,12,0,8,0,0,0,1"]
    if cap:
        lines.append(cap)
    lines += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    lines += ["Dialogue: 0,{},{},{},,0,0,0,,{}".format(ass_time(a), ass_time(b), st, txt) for a, b, st, txt in sorted(events)]
    path = Path(root) / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def stage_subtitles(root, edl, shift=0.0, name=".mann-subs.srt"):
    """Copy the subtitle file to a filter-safe name, uppercased and time-shifted when asked."""
    text = inside(root, edl["subtitles"]["file"]).read_text(encoding="utf-8-sig")
    if edl["subtitles"].get("uppercase"):
        text = "\n".join(l if ("-->" in l or l.strip().isdigit()) else l.upper() for l in text.splitlines())
    if shift:
        text = shift_srt(text, shift)
    staged = Path(root) / name
    staged.write_text(text, encoding="utf-8")
    return staged


def shift_srt(text, shift):
    def stamp(m):
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000.0 - shift
        t = max(t, 0)
        ms = int(round(t * 1000))
        return "{:02d}:{:02d}:{:02d},{:03d}".format(ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
    return re.sub(r"(\d+):(\d+):(\d+)[,.](\d+)", stamp, text)


# ---- fingerprints and approvals -------------------------------------------------

def hashed(root, rel):
    """sha256 of an edit file, cached by size and mtime so big footage is hashed once."""
    root = Path(root)
    path = inside(root, rel)
    st = path.stat()
    cache_path = root / ".mann-hash-cache.json"
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    key = "{}|{}|{}".format(rel, st.st_size, st.st_mtime_ns)
    if key not in cache:
        cache = {k: v for k, v in cache.items() if not k.startswith(rel + "|")}
        cache[key] = file_hash(path)
        write_json(cache_path, cache)
    return cache[key]


def global_files(edl):
    audio = edl.get("audio", {})
    files = ([audio["music"]["file"]] if audio.get("music") else []) + [s["file"] for s in audio.get("sfx", [])]
    files += [o["file"] for o in edl.get("overlays", [])]
    files += ([edl["subtitles"]["file"]] if edl.get("subtitles") else []) + ([edl["grade"]["lut"]] if edl.get("grade", {}).get("lut") else [])
    files += [edl["subtitles"]["words"]] if (edl.get("subtitles") or {}).get("words") else []
    files += [edl["script"]] if edl.get("script") else []
    return sorted(set(files))


def globals_fingerprint(root, edl):
    rest = {k: v for k, v in edl.items() if k != "clips"}
    return fingerprint({"globals": rest, "order": [c["id"] for c in edl["clips"]],
                        "files": {f: hashed(root, f) for f in global_files(edl)}})


def clip_fingerprint(root, edl, clip):
    files = sorted({edl["sources"][clip["source"]]} | {edl["sources"][i["source"]] for i in clip.get("inserts", [])})
    return fingerprint({"clip": clip, "files": {f: hashed(root, f) for f in files}})


def fingerprints(root, edl):
    return globals_fingerprint(root, edl), {c["id"]: clip_fingerprint(root, edl, c) for c in edl["clips"]}


def edit_fingerprint(root, edl):
    g, clips = fingerprints(root, edl)
    return fingerprint({"globals": g, "clips": clips})


def approvals(root):
    path = Path(root) / "approvals.json"
    return read_json(path)["approvals"] if path.exists() else []


def record(root, entry):
    path = Path(root) / "approvals.json"
    log = read_json(path) if path.exists() else {"approvals": []}
    entry = dict(entry, at=now())
    log["approvals"].append(entry)
    write_json(path, log)
    return entry


def status(root, edl):
    """What the owner still has to see: nothing, some parts, or the whole video."""
    g, clips = fingerprints(root, edl)
    boards = [a for a in approvals(root) if a["kind"] == "storyboard"]
    globals_ok = any(a.get("globals") == g for a in boards)
    approved_fps = {(cid, fp) for a in boards for cid, fp in a.get("clips", {}).items()}
    changed = [cid for cid, fp in clips.items() if (cid, fp) not in approved_fps]
    scope = "whole" if not globals_ok else ("part" if changed else "none")
    return {"scope": scope, "globals_approved": globals_ok, "changed_clips": changed if globals_ok else list(clips)}


def approved(root, edl, kind="storyboard"):
    if kind == "storyboard":
        return status(root, edl)["scope"] == "none"
    current = edit_fingerprint(root, edl)
    return any(a["kind"] == kind and a.get("edl_fingerprint") == current for a in approvals(root))


def require_approval(root, edl):
    st = status(root, edl)
    if st["scope"] == "whole":
        raise ProductionError("Storyboard not approved for this exact EDL (a whole-video setting changed or nothing is approved yet). "
                              "Run `storyboard`, show the owner, and record their words with `approve` before rendering.")
    if st["scope"] == "part":
        raise ProductionError("Storyboard not approved for the changed part(s) {}. Run `storyboard --changed` (and `preview-part`), "
                              "show the owner that part, and record their words with `approve --clips {}`.".format(
                                  ", ".join(st["changed_clips"]), ",".join(st["changed_clips"])))


def require_decisions(root, edl):
    """The owner's other two decisions: the style is final and the script is locked.
    Also refuses archive footage whose licence is missing or not usable."""
    from . import footage
    footage.gate(root, edl)
    if edl.get("style"):
        require(any(a["kind"] == "style" and a.get("slug") == edl["style"] for a in approvals(root)),
                "Style `{}` is not finalised by the owner. Show the suggestions and record their pick with `approve-style`.".format(edl["style"]))
    if edl.get("script"):
        sha = hashed(root, edl["script"])
        require(any(a["kind"] == "script" and a.get("file") == edl["script"] and a.get("sha256") == sha for a in approvals(root)),
                "Script `{}` is not locked (or changed after locking). Get the owner's lock with `lock-script`.".format(edl["script"]))


def approve_style(root, slug, words):
    require(isinstance(words, str) and words.strip(), "Quote the owner's exact words with --words")
    with project_lock(Path(root)):
        return record(root, {"kind": "style", "slug": slug, "by": "owner", "words": words.strip()})


def lock_script(root, rel, words):
    require(isinstance(words, str) and words.strip(), "Quote the owner's exact words with --words")
    with project_lock(Path(root)):
        require(inside(root, rel).is_file(), "Script file missing: " + rel)
        return record(root, {"kind": "script", "file": rel, "sha256": hashed(root, rel), "by": "owner", "words": words.strip()})


# ---- storyboard -----------------------------------------------------------------

def clip_summary(edl, row, clip):
    kind, tdur = transition(clip)
    return {"id": clip["id"], "source": clip["source"], "in": clip["in"], "out": clip["out"], "speed": clip.get("speed", 1.0),
            "start": row["start"], "duration": row["duration"], "transition": kind if kind == "cut" else "{} {:.2f}s".format(kind, tdur),
            "grade": clip.get("grade") or edl.get("grade", {}).get("preset", "neutral"),
            "text": " | ".join(t["value"] for t in as_list(clip.get("text"))), "beat": clip.get("beat", ""), "zoom": clip.get("zoom"),
            "fx": as_list(clip.get("fx")), "freeze": clip.get("freeze", 0), "inserts": len(clip.get("inserts", []))}


def diff(old, new):
    before = {c["id"]: c for c in old}
    after = {c["id"]: c for c in new}
    lines = ["- added {} ({}s at {})".format(i, after[i]["duration"], tc(after[i]["start"])) for i in after if i not in before]
    lines += ["- removed {}".format(i) for i in before if i not in after]
    for i in after:
        if i in before:
            changed = [k for k in ("source", "in", "out", "speed", "transition", "grade", "text", "beat", "zoom", "fx", "freeze", "inserts")
                       if before[i].get(k) != after[i].get(k)]
            if changed:
                lines.append("- changed {}: {}".format(i, ", ".join("{} {!r} -> {!r}".format(k, before[i].get(k), after[i].get(k)) for k in changed)))
    if [c["id"] for c in old if c["id"] in after] != [c["id"] for c in new if c["id"] in before]:
        lines.append("- clip order changed")
    return lines


def global_summary(edl):
    return {"format": edl["format"], "grade": edl.get("grade", {}), "audio": edl.get("audio", {}),
            "overlays": edl.get("overlays", []), "subtitles": edl.get("subtitles"), "master": edl.get("master", {}),
            "style": edl.get("style"), "script": edl.get("script")}


def flatten(value, prefix=""):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            out.update(flatten(v, "{}.{}".format(prefix, k) if prefix else k))
        return out
    if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
        out = {}
        for i, v in enumerate(value):
            out.update(flatten(v, "{}[{}]".format(prefix, i)))
        return out
    return {prefix: value}


def diff_globals(old, new):
    if not old:
        return []
    a, b = flatten(old), flatten(new)
    return ["- changed {}: {} -> {}".format(k, json_short(a.get(k)), json_short(b.get(k)))
            for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def json_short(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= 160 else text[:157] + "..."


def still_frames(root, edl, indices, out):
    """Pull exact frames out of the full edit graph (transitions, overlays, inserts, subtitles
    included) without writing a video file: what the owner approves is what will render."""
    from .render import build_graph
    probes = validate(root, edl)
    textfiles = []
    try:
        from .render import cached_clips
        cache, _ = cached_clips(root, edl, probes)
        inputs, graph, v, a, total = build_graph(root, edl, probes, textfiles, cache=cache)
        unique = sorted(set(indices))
        select = "+".join("eq(n\\,{})".format(i) for i in unique)
        graph += ";[{}]select='{}'[sb];[{}]anullsink".format(v, select, a)
        # Stop once every requested frame is written. Continuing a cached concat
        # graph into its audio sink after an early selection can abort FFmpeg 7's
        # scheduler. The exact-count check below still rejects missing frames.
        media.run(["ffmpeg", "-hide_banner", "-y"] + inputs + ["-filter_complex", graph, "-map", "[sb]", "-fps_mode", "passthrough",
                   "-q:v", "3", "-t", "{:.3f}".format(total), "-frames:v", str(len(unique)), str(out / ".all-%04d.jpg")])
    finally:
        for f in textfiles:
            Path(f).unlink(missing_ok=True)
    written = sorted(out.glob(".all-*.jpg"))
    unique = sorted(set(indices))
    require(len(written) == len(unique), "Storyboard extraction returned {} of {} frames".format(len(written), len(unique)))
    by_index = dict(zip(unique, written))
    for n, i in enumerate(indices, 1):
        (out / ".still-{:04d}.jpg".format(n)).write_bytes(by_index[i].read_bytes())
    for f in written:
        f.unlink()


def storyboard(root, frames_per_clip=1, only=None):
    """Numbered frames from the full edit graph plus STORYBOARD.md. With `only` (clip ids) it
    makes a part storyboard in storyboard/part/ for a one-part correction."""
    root = Path(root)
    with project_lock(root):
        edl = load(root)
        require_decisions(root, edl)
        rows, total = timeline(edl)
        ids = [c["id"] for c in edl["clips"]]
        if only:
            unknown = [c for c in only if c not in ids]
            require(not unknown, "Unknown clip id(s): " + ", ".join(unknown))
        out = root / "storyboard" / ("part" if only else "")
        if out.exists():
            for f in list(out.glob("F*.jpg")) + list(out.glob("P*.jpg")):
                f.unlink()
        out.mkdir(parents=True, exist_ok=True)
        previous_path = root / "storyboard" / "storyboard.json"
        previous = read_json(previous_path) if previous_path.exists() else None
        fps = float(edl["format"].get("fps", 30))
        frames, summaries, picks = [], [], []
        for row, clip in zip(rows, edl["clips"]):
            summaries.append(clip_summary(edl, row, clip))
            if only and clip["id"] not in only:
                continue
            for frac in ([0.5] if frames_per_clip == 1 else [0.15, 0.85]):
                picks.append((clip["id"], min(int(round((row["start"] + row["duration"] * frac) * fps)), int(total * fps) - 1)))
        still_frames(root, edl, [p[1] for p in picks], out)
        prefix = "P" if only else "F"
        for n, (cid, index) in enumerate(picks, 1):
            name = "{}{:02d}_{}_{}.jpg".format(prefix, n, cid, tc(index / fps).replace(":", "m") + "s")
            (out / ".still-{:04d}.jpg".format(n)).replace(out / name)
            frames.append({"file": name, "clip": cid, "timeline": round(index / fps, 2)})
        g, clip_fps = fingerprints(root, edl)
        globals_now = global_summary(edl)
        changes = (diff(previous["clips"], summaries) + diff_globals(previous.get("globals", {}), globals_now)) if previous else []
        rec = {"edl_fingerprint": fingerprint({"globals": g, "clips": clip_fps}), "globals_fingerprint": g,
               "clip_fingerprints": {c: clip_fps[c] for c in (only or ids)}, "created": now(), "frames": frames,
               "clips": summaries, "globals": globals_now, "pace": pace(edl), "changes_since_previous": changes,
               "scope": "part" if only else "whole", "only": only or []}
        from . import craft
        rec["craft"] = craft.check(root, edl)
        craft_md = craft.markdown(rec["craft"], craft.manual_checklist(edl))
        if only:
            write_json(out / "part.json", rec)
            (out / "PART.md").write_text(storyboard_markdown(edl, rec, total) + "\n" + craft_md, encoding="utf-8")
        else:
            write_json(out / "storyboard.json", rec)
            (out / "STORYBOARD.md").write_text(storyboard_markdown(edl, rec, total) + "\n" + craft_md, encoding="utf-8")
        return rec


def storyboard_markdown(edl, rec, total):
    fmt = edl["format"]
    p = rec["pace"]
    part = rec["scope"] == "part"
    approve_cmd = "approve <edit-dir> --clips {} --words \"<owner's words>\"".format(",".join(rec["only"])) if part else \
        "approve <edit-dir> --words \"<owner's words>\""
    lines = ["# {}: {}".format("Part storyboard ({})".format(", ".join(rec["only"])) if part else "Storyboard", edl.get("title", "untitled")), "",
             "Status: **waiting for owner approval** (`python3 -m aifilm.editor {}`).".format(approve_cmd),
             "Fingerprint: `{}`".format(rec["edl_fingerprint"][:16]), "",
             "Format {}x{} @ {} fps · total {} · {} shots · average shot {}s · {} cuts per 10 s · grade `{}`{}".format(
                 fmt["width"], fmt["height"], fmt.get("fps", 30), tc(total), p["shots"], p["average_shot_seconds"], p["cuts_per_10s"],
                 edl.get("grade", {}).get("preset", "neutral"), " · style `{}`".format(edl["style"]) if edl.get("style") else ""), ""]
    if part:
        lines += ["Only these clips changed; everything else stays as approved.", ""]
    if rec["changes_since_previous"]:
        lines += ["## Changes since the previous storyboard", ""] + rec["changes_since_previous"] + [""]
    lines += ["## Frames", "", "| # | Frame | Timeline | Clip | Source in-out | Shot | Transition in | Grade | FX | On-screen text | Beat |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    by_id = {c["id"]: c for c in rec["clips"]}
    for i, f in enumerate(rec["frames"], 1):
        c = by_id[f["clip"]]
        extras = [x for x in c["fx"]] + (["freeze {}s".format(c["freeze"])] if c["freeze"] else []) + (["{} insert(s)".format(c["inserts"])] if c["inserts"] else [])
        lines.append("| {} | `{}` | {} | {} | {} {:.2f}-{:.2f}s{} | {:.2f}s | {} | {} | {} | {} | {} |".format(
            i, f["file"], tc(f["timeline"]), c["id"], c["source"], c["in"], c["out"],
            " x{}".format(c["speed"]) if c["speed"] != 1.0 else "", c["duration"], c["transition"], c["grade"],
            ", ".join(extras) or "-", c["text"].replace("|", "/") or "-", c["beat"].replace("|", "/") or "-"))
    audio = edl.get("audio", {})
    lines += ["", "## Sound plan", ""]
    music = audio.get("music")
    lines.append("- Music: {}".format("`{}` at {} dB{}".format(music["file"], music.get("gain_db", -16),
                                                              ", ducked under voice" if music.get("duck", True) else "") if music else "none"))
    lines.append("- Source audio: {}".format("kept at {} dB".format(audio.get("source_gain_db", 0)) if audio.get("keep_source", True) else "muted"))
    for s in audio.get("sfx", []):
        lines.append("- SFX `{}` at {} ({} dB)".format(s["file"], tc(s["at"]), s.get("gain_db", 0)))
    for o in edl.get("overlays", []):
        lines.append("- Motion graphic `{}` at {}".format(o["file"], tc(o.get("at", 0))))
    if edl.get("subtitles"):
        lines.append("- Subtitles `{}` ({})".format(edl["subtitles"]["file"], "burned in" if edl["subtitles"].get("burn", True) else "sidecar"))
    master = edl.get("master", {})
    lines.append("- Master loudness {} LUFS, true peak <= {} dBTP".format(master.get("lufs", -14), master.get("true_peak", -1)))
    lines += ["", "## Rules applied (Mann fills this before showing the owner)", "",
              "For each Editor rule in `studio/LEARNINGS.md` and `editor/rules.json`, one line: how this cut follows it.", ""]
    return "\n".join(lines) + "\n"


def approve(root, words, by="owner", kind="storyboard", clips=None):
    """Record the owner's explicit approval: the whole storyboard, some parts (`clips`), or the final cut."""
    root = Path(root)
    require(isinstance(words, str) and words.strip(), "Quote the owner's exact approval words with --words")
    require(kind in ("storyboard", "final"), "kind must be storyboard or final")
    with project_lock(root):
        edl = load(root)
        g, clip_fps = fingerprints(root, edl)
        if kind == "final":
            qc = root / "renders" / "qc.json"
            current = fingerprint({"globals": g, "clips": clip_fps})
            require(qc.exists() and read_json(qc).get("edl_fingerprint") == current, "Run render and qc for this EDL before final approval")
            return record(root, {"kind": "final", "edl_fingerprint": current, "by": by, "words": words.strip()})
        if clips:
            board = root / "storyboard" / "part" / "part.json"
            require(board.exists(), "No part storyboard yet; run `storyboard --only {}` first".format(",".join(clips)))
            part = read_json(board)
            require(status(root, edl)["globals_approved"], "A whole-video setting changed, so the whole storyboard needs approval, not a part")
            for cid in clips:
                require(cid in clip_fps, "Unknown clip " + cid)
                require(part["clip_fingerprints"].get(cid) == clip_fps[cid], "Clip {} changed after its part storyboard; rebuild and re-show it".format(cid))
            return record(root, {"kind": "storyboard", "scope": "part", "globals": None, "clips": {c: clip_fps[c] for c in clips},
                                 "by": by, "words": words.strip()})
        board = root / "storyboard" / "storyboard.json"
        require(board.exists(), "No storyboard yet; run `storyboard` and show it to the owner first")
        require(read_json(board)["edl_fingerprint"] == fingerprint({"globals": g, "clips": clip_fps}),
                "The EDL changed after the storyboard was made; rebuild and re-show it")
        return record(root, {"kind": "storyboard", "scope": "whole", "globals": g, "clips": clip_fps, "by": by, "words": words.strip()})


def sub_edl(edl, ids, context=1):
    """The part of the EDL around `ids` (plus `context` neighbours), re-timed to start at 0,
    for a quick video preview of a one-part correction."""
    order = [c["id"] for c in edl["clips"]]
    idx = sorted(order.index(i) for i in ids)
    lo, hi = max(idx[0] - context, 0), min(idx[-1] + context, len(order) - 1)
    rows, _ = timeline(edl)
    offset = rows[lo]["start"]
    part = json.loads(json.dumps(edl))
    part["clips"] = part["clips"][lo:hi + 1]
    part["clips"][0]["transition_in"] = {"type": "cut"}
    _, length = timeline(part)
    audio = part.get("audio", {})
    if audio.get("music"):
        audio["music"]["start"] = float(audio["music"].get("start", 0)) + offset
    audio["sfx"] = [dict(s, at=s["at"] - offset) for s in audio.get("sfx", []) if offset <= s["at"] < offset + length]
    part["overlays"] = [dict(o, at=o.get("at", 0) - offset) for o in part.get("overlays", []) if offset <= o.get("at", 0) < offset + length]
    return part, offset, length
