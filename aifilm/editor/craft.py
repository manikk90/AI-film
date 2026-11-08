"""Mann's craft rulebook (editor/craft/craft.json) put to work.

- `rules()` / `rule(id)`: the knowledge (cuts, continuity, eyelines, composition, shots,
  pacing, typography, colour, safe zones, sound, motion, VFX, story, accessibility).
- `typography()`: font pairings and the type scale used by EDL text `role`s.
- `check(root, edl)`: automatic checks for every measurable rule, against the thresholds in
  editor/rules.json; returns findings with the rule id they enforce.
- `manual_checklist(edl)`: the frame-by-frame items Mann confirms before showing the owner.
"""

import re
import subprocess
from pathlib import Path

from ..core import inside, read_json
from . import edl as E
from . import fonts as F

REPO = Path(__file__).resolve().parents[2]
CRAFT = REPO / "editor" / "craft" / "craft.json"
RULES = REPO / "editor" / "rules.json"
NAMED = {"white": (255, 255, 255), "black": (0, 0, 0), "yellow": (255, 240, 0), "red": (255, 51, 51), "green": (102, 255, 51),
         "cyan": (0, 255, 255), "orange": (255, 153, 51), "gold": (255, 215, 0)}


def data():
    return read_json(CRAFT)


def rules(domain=None):
    out = []
    for d in data()["domains"]:
        if domain in (None, d["id"]):
            out += [dict(r, domain=d["id"]) for r in d["rules"]]
    return out


def rule(rule_id):
    for r in rules():
        if r["id"] == rule_id:
            return r
    raise E.ProductionError("Unknown craft rule " + rule_id)


def pairing(pid):
    for p in data()["font_pairings"]:
        if p["id"] == pid:
            return p
    raise E.ProductionError("Unknown font pairing {!r}; see editor/craft/CRAFT.md".format(pid))


def theme(tid):
    for t in data()["colour_themes"]:
        if t["id"] == tid:
            return t
    raise E.ProductionError("Unknown colour theme {!r}; see editor/craft/CRAFT.md".format(tid))


def aspect_of(fmt):
    w, h = fmt["width"], fmt["height"]
    r = w / float(h)
    if r < 0.7:
        return "9:16"
    if r < 0.9:
        return "4:5"
    if r < 1.2:
        return "1:1"
    return "16:9"


def safe_box(fmt, profile):
    zones = data()["safe_zones"][aspect_of(fmt)]
    z = zones.get(profile) or zones["standard"]
    W, H = fmt["width"], fmt["height"]
    return {"x0": W * z["left"], "x1": W * (1 - z["right"]), "y0": H * z["top"], "y1": H * (1 - z["bottom"])}


def resolve_text(edl, item):
    """Size (px), font file and family for a text item, from its role and the EDL's pairing."""
    H = edl["format"]["height"]
    scale = data()["type_scale"]
    role = item.get("role")
    size = int(item.get("size") or round(H * scale["roles"].get(role or "caption", 0.045)))
    pid = (edl.get("typography") or {}).get("pairing")
    family, file = None, item.get("font")
    if not file and pid:
        p = pairing(pid)
        family = p["display"] if role in ("title", "headline") else p["text"]
        weight = p["display_weight"] if role in ("title", "headline") else p.get("text_weight", scale["weights"].get(role or "caption", 600))
        file = F.resolve(family, weight)
    return size, file, family


def text_width(value, size, font_file=None):
    """Width in px: from the font's advance widths when fontTools and the file are available,
    otherwise an estimate that ignores combining marks (matras, halant)."""
    import unicodedata
    if font_file:
        try:
            from fontTools.ttLib import TTFont
            font = TTFont(font_file, lazy=True)
            cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
            units = sum(hmtx[cmap[ord(ch)]][0] for ch in value if ord(ch) in cmap and unicodedata.category(ch) not in ("Mn",))
            return units * size / float(upm)
        except Exception:
            pass
    visible = [ch for ch in value if unicodedata.category(ch) not in ("Mn", "Mc", "Cf")]
    return len(visible) * size * (0.62 if E.DEVANAGARI.search(value) else 0.55)


def rendered_bbox(edl, item):
    """Exact box of a text item, measured by rendering it alone with the same ASS renderer
    (complex shaping, real font, outline) on a black frame. None when FFmpeg is unavailable."""
    import shutil
    import tempfile
    if not shutil.which("ffmpeg"):
        return None
    fmt = edl["format"]
    W, H = fmt["width"], fmt["height"]
    probe_edl = {"version": 1, "format": fmt, "typography": edl.get("typography"),
                 "clips": [{"id": "X", "source": "_", "in": 0, "out": 1, "text": dict(item, start=0, end=1)}]}
    with tempfile.TemporaryDirectory() as tmp:
        script = E.ass_script(tmp, probe_edl)
        from .fonts import font_dir
        fdir = ":fontsdir='{}'".format(E.esc(font_dir())) if font_dir().exists() else ""
        raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s={}x{}:d=1".format(W, H), "-frames:v", "1",
                              "-vf", "ass=filename='{}'{}:shaping=complex,format=gray".format(E.esc(script), fdir),
                              "-f", "rawvideo", "-"], capture_output=True, timeout=60).stdout
    if len(raw) < W * H:
        return None
    rows = [y for y in range(H) if max(raw[y * W:(y + 1) * W]) > 40]
    if not rows:
        return None
    cols = [x for x in range(W) if any(raw[y * W + x] > 40 for y in range(rows[0], rows[-1] + 1, 2))]
    return {"x0": float(cols[0]), "x1": float(cols[-1] + 1), "y0": float(rows[0]), "y1": float(rows[-1] + 1)}


def text_bbox(fmt, value, size, position, font_file=None):
    W, H = fmt["width"], fmt["height"]
    lines = value.split("\n")
    width = max(text_width(l, size, font_file) for l in lines)
    height = size * 1.25 * len(lines)
    y = {"top": H * 0.18, "center": (H - height) / 2, "bottom": H * 0.66}[position]
    return {"x0": (W - width) / 2, "x1": (W + width) / 2, "y0": y, "y1": y + height}


def subtitle_margins(fmt, profile=None):
    """Caption margins in output pixels that keep captions inside the safe zone."""
    import math
    profile = profile or read_json(RULES)["rules"].get("safe_zone_profile", "standard")
    zones = data()["safe_zones"][aspect_of(fmt)]
    z = zones.get(profile) or zones["standard"]
    W, H = fmt["width"], fmt["height"]
    pad = 0.01
    return {"l": int(math.ceil((z["left"] + pad) * W)), "r": int(math.ceil((z["right"] + pad) * W)),
            "bottom": int(math.ceil((z["bottom"] + pad) * H)), "top": int(math.ceil((z["top"] + pad) * H))}


def subtitle_bbox(fmt, subs, line_chars=24):
    H, W = fmt["height"], fmt["width"]
    size = float(subs.get("size", 0.05)) * H
    height = size * 1.25 * 2
    pos = subs.get("position", "bottom")
    m = subtitle_margins(fmt)
    margin = float(subs.get("margin_v_px", m["bottom"] if pos == "bottom" else m["top"]))
    if pos == "bottom":
        y1 = H - margin
        y0 = y1 - height
    elif pos == "top":
        y0 = margin
        y1 = y0 + height
    else:
        y0, y1 = (H - height) / 2, (H + height) / 2
    x0, x1 = float(m["l"]), float(W - m["r"])
    width = min(x1 - x0, line_chars * size * 0.55)
    centre = (x0 + x1) / 2
    return {"x0": centre - width / 2, "x1": centre + width / 2, "y0": y0, "y1": y1}


def inside_box(b, box):
    return b["x0"] >= box["x0"] - 1 and b["x1"] <= box["x1"] + 1 and b["y0"] >= box["y0"] - 1 and b["y1"] <= box["y1"] + 1


def luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def background(root, edl, clip, local_t, band, size=(90, 160)):
    """Mean colour of the formatted, graded frame inside `band` (pixel box on the output frame)."""
    fmt = edl["format"]
    W, H = fmt["width"], fmt["height"]
    w, h = (size if H > W else (160, 90))
    chain = ",".join(E.frame_chain(edl, W, H) + [g for g in [E.grade_chain(root, edl, clip)] if g] + ["scale={}:{}".format(w, h)])
    src_t = clip["in"] + local_t * clip.get("speed", 1.0)
    data_ = subprocess.run(["ffmpeg", "-v", "error", "-ss", "{:.3f}".format(src_t), "-i", str(inside(root, edl["sources"][clip["source"]])),
                            "-frames:v", "1", "-vf", chain, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=120).stdout
    if len(data_) < w * h * 3:
        return None
    x0, x1 = int(max(band["x0"], 0) * w / W), int(min(band["x1"], W) * w / W)
    y0, y1 = int(max(band["y0"], 0) * h / H), int(min(band["y1"], H) * h / H)
    px = [tuple(data_[(y * w + x) * 3:(y * w + x) * 3 + 3]) for y in range(y0, max(y1, y0 + 1)) for x in range(x0, max(x1, x0 + 1))]
    if not px:
        return None
    n = float(len(px))
    return tuple(sum(p[i] for p in px) / n for i in range(3))


def parse_srt(text):
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", block)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000.0
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000.0
        rows_ = block.splitlines()
        at = next(i for i, l in enumerate(rows_) if "-->" in l)
        lines = [l for l in rows_[at + 1:] if l.strip()]
        cues.append({"start": a, "end": b, "lines": lines})
    return cues


def check(root, edl, sample_contrast=True):
    """Automatic craft checks. Each finding: {check, rule, result (pass/warn/fail), detail}."""
    root = Path(root)
    R = read_json(RULES)["rules"]
    fmt = edl["format"]
    W, H = fmt["width"], fmt["height"]
    aspect = aspect_of(fmt)
    box = safe_box(fmt, R.get("safe_zone_profile", "standard"))
    rows, total = E.timeline(edl)
    out = []

    def add(name, rule_id, ok, detail, level="warn"):
        out.append({"check": name, "rule": rule_id, "result": "pass" if ok else level, "detail": detail})

    # Typography: sizes, hierarchy, families, safe zone, reading time, Devanagari support, contrast.
    texts = []
    for row, clip in zip(rows, edl["clips"]):
        for item in E.as_list(clip.get("text")):
            size, file, family = resolve_text(edl, item)
            texts.append((row, clip, item, size, file, family))
    pid = (edl.get("typography") or {}).get("pairing")
    if texts or edl.get("subtitles"):
        families = {t[5] or (Path(t[4]).stem.split("-")[0] if t[4] else "default") for t in texts}
        if edl.get("subtitles"):
            families.add(pairing(pid)["text"] if pid else "Noto Sans")
        add("font families", "two-families", len(families) <= R["max_font_families"], "{} ({})".format(len(families), ", ".join(sorted(families))))
        if pid:
            p = pairing(pid)
            need = any(E.DEVANAGARI.search(t[2]["value"]) for t in texts)
            if edl.get("subtitles"):
                need = need or bool(E.DEVANAGARI.search(inside(root, edl["subtitles"]["file"]).read_text(encoding="utf-8")))
            add("Devanagari support", "devanagari", not need or p["devanagari"], "pairing `{}` {} Devanagari".format(pid, "has" if p["devanagari"] else "lacks"), "fail")
            missing = sorted({t[5] for t in texts if t[5] and not t[4]})
            add("pairing fonts installed", "two-families", not missing,
                "missing: {} (run `fonts-install --pairing {}`)".format(", ".join(missing), pid) if missing else "installed")
    sizes = sorted({t[3] for t in texts})
    if texts:
        add("minimum text size", "min-size", sizes[0] >= R["text_min_height_ratio"] * H,
            "smallest {}px = {:.1%} of height (min {:.0%})".format(sizes[0], sizes[0] / float(H), R["text_min_height_ratio"]))
    if len(sizes) > 1:
        ratios = [b / float(a) for a, b in zip(sizes, sizes[1:])]
        add("type hierarchy", "type-scale", min(ratios) >= R["type_scale_min_ratio"],
            "sizes {} px, closest step x{:.2f} (min x{})".format(sizes, min(ratios), R["type_scale_min_ratio"]))
    for row, clip, item, size, file, family in texts:
        bb = rendered_bbox(edl, item) or text_bbox(fmt, item["value"], size, item.get("position", "bottom"), file)
        add("text safe zone {}".format(clip["id"]), "vertical-safe" if aspect == "9:16" else "title-safe", inside_box(bb, box),
            "'{}' spans y {:.0%}-{:.0%}, x {:.0%}-{:.0%}".format(item["value"][:24], bb["y0"] / H, bb["y1"] / H, bb["x0"] / W, bb["x1"] / W), "fail")
        start = float(item.get("start", 0))
        end = float(item.get("end", row["duration"]))
        words = len(item["value"].split())
        need = words / R["text_hold_words_per_second"] + 0.5
        add("reading time {}".format(clip["id"]), "reading-time", end - start >= need - 0.05,
            "{:.1f}s on screen for {} words (needs {:.1f}s)".format(end - start, words, need))
        if sample_contrast and not item.get("box"):
            bg = background(root, edl, clip, (start + end) / 2, bb)
            colour = NAMED.get(str(item.get("color", "white")).lower())
            if bg and colour:
                c = contrast(colour, bg)
                add("text contrast {}".format(clip["id"]), "contrast", c >= R["text_contrast_min_outlined"],
                    "{:.1f}:1 against the frame (min {} with outline; add `box: true` or darken)".format(c, R["text_contrast_min_outlined"]))
    # Captions.
    subs = edl.get("subtitles")
    if subs:
        cues = parse_srt(inside(root, subs["file"]).read_text(encoding="utf-8-sig"))
        max_chars = R["caption_max_chars_line_vertical"] if aspect in ("9:16", "4:5") else R["caption_max_chars_line"]
        fast = [c for c in cues if sum(len(l) for l in c["lines"]) / max(c["end"] - c["start"], 0.01) > R["caption_max_cps"]]
        short = [c for c in cues if c["end"] - c["start"] < R["caption_min_seconds"]]
        long_lines = [c for c in cues if any(len(l) > max_chars for l in c["lines"])]
        many = [c for c in cues if len(c["lines"]) > R["caption_max_lines"]]
        add("caption reading speed", "caption-rules", not fast, "{} of {} cues over {} chars/s".format(len(fast), len(cues), R["caption_max_cps"]))
        add("caption minimum duration", "caption-rules", not short, "{} cues under {}s".format(len(short), R["caption_min_seconds"]))
        add("caption line length", "caption-rules", not long_lines, "{} cues over {} chars per line".format(len(long_lines), max_chars))
        add("caption lines", "caption-rules", not many, "{} cues over {} lines".format(len(many), R["caption_max_lines"]))
        sb = subtitle_bbox(fmt, subs, max_chars)
        add("caption safe zone", "vertical-safe" if aspect == "9:16" else "title-safe", inside_box(sb, box),
            "captions span y {:.0%}-{:.0%} (safe {:.0%}-{:.0%})".format(sb["y0"] / H, sb["y1"] / H, box["y0"] / H, box["y1"] / H), "fail")
        if sample_contrast and not subs.get("box"):
            worst = None
            for row, clip in list(zip(rows, edl["clips"]))[:12]:
                bg = background(root, edl, clip, row["duration"] / 2, sb)
                colour = NAMED.get(subs.get("color", "white"))
                if bg and colour:
                    c = contrast(colour, bg)
                    worst = c if worst is None else min(worst, c)
            if worst is not None:
                add("caption contrast", "contrast", worst >= R["text_contrast_min_outlined"], "lowest {:.1f}:1 behind captions".format(worst))
    # Subject framing after face-aware reframing.
    from . import reframe as RF
    reframed = [(row, c) for row, c in zip(rows, edl["clips"]) if c.get("reframe", fmt.get("reframe")) == "auto"]
    if reframed and RF.usable():
        cap_top = subtitle_bbox(fmt, subs)["y0"] / H if subs else 1.0
        bad, lost = [], []
        for row, c in reframed:
            pts = RF.framing(root, edl, c, row["duration"])
            if not pts:
                lost.append(c["id"])
                continue
            if any(not (0.2 <= p["x"] <= 0.8 and 0.15 <= p["y"] <= 0.55 and p["y"] + p["size"] / 2 < cap_top) for p in pts):
                bad.append(c["id"])
        add("subject in frame", "subject-in-frame", not bad, "face off-position in {}".format(", ".join(bad)) if bad else "face placed well in every reframed clip")
        if lost:
            add("face found", "subject-in-frame", False, "no face tracked in {} (crop stays centred)".format(", ".join(lost)))
    # Cuts and continuity.
    clips = edl["clips"]
    style_jump = False
    if edl.get("style"):
        try:
            from .engine import style as st
            style_jump = float(st(edl["style"])["edl"].get("silence_cut") or 0) > 0
        except E.ProductionError:
            pass
    jumps = []
    for a, b in zip(clips, clips[1:]):
        if a["source"] == b["source"] and E.transition(b)[0] == "cut" and abs(b["in"] - a["out"]) < 2.0:
            za = (a.get("zoom") or {}).get("to", 1.0)
            zb = (b.get("zoom") or {}).get("from", 1.0)
            if abs(zb - za) / max(za, zb) < R["jump_cut_min_zoom_change"]:
                jumps.append(b["id"])
    add("30-degree rule / jump cuts", "30-degree-rule", not jumps,
        "same framing across cuts into {}{}".format(", ".join(jumps), " (jump-cut style: alternate punch-ins)" if style_jump else "") if jumps else "every same-source cut changes size")
    kinds = [E.transition(c)[0] for c in clips[1:]]
    soft = [k for k in kinds if k != "cut"]
    if kinds:
        add("transition use", "transition-motivated", len(soft) <= R["transition_max_share"] * len(kinds) and len(set(soft)) <= 2,
            "{} of {} cuts are transitions ({} types)".format(len(soft), len(kinds), len(set(soft))))
    grades = {c.get("grade") for c in clips if c.get("grade")}
    add("grade consistency", "consistency", len(grades) <= R["max_grades_per_film"], "{} per-clip looks: {}".format(len(grades), ", ".join(sorted(grades)) or "none"))
    run_len, worst_run, prev = 1, 1, None
    for c in clips:
        key = (c["source"], (c.get("zoom") or {}).get("to", 1.0))
        run_len = run_len + 1 if key == prev else 1
        worst_run = max(worst_run, run_len)
        prev = key
    add("shot variety", "variety", worst_run < R["max_same_framing_run"], "longest run of identical source+framing: {}".format(worst_run))
    # Photosensitivity: flashes per second.
    flashes = sorted(r["start"] for r, c in zip(rows, clips) if "flash" in E.as_list(c.get("fx")))
    worst = max((sum(1 for f in flashes if t <= f < t + 1.0) for t in flashes), default=0)
    add("flash safety", "flash-safety", worst <= R["flash_max_per_second"], "max {} flashes in one second (limit {})".format(worst, R["flash_max_per_second"]), "fail")
    # Sound: music under the voice.
    audio = edl.get("audio", {})
    if audio.get("music") and audio.get("keep_source", True):
        gap = float(audio.get("source_gain_db", 0)) - float(audio["music"].get("gain_db", -16))
        add("music under voice", "voice-first", gap >= R["music_under_voice_db"],
            "music {} dB under the source (min {} dB){}".format(round(gap, 1), R["music_under_voice_db"], ", plus ducking" if audio["music"].get("duck", True) else ""))
    return out


MANUAL_CORE = ["cut-on-action", "180-rule", "screen-direction", "eyeline-match", "eye-trace", "look-room", "headroom", "tangents",
               "props-wardrobe", "skin-tones", "hold-for-emotion", "rule-of-six", "open-loop", "payoff", "room-tone", "layers"]


def manual_checklist(edl):
    ids = list(MANUAL_CORE)
    fmt = edl["format"]
    if aspect_of(fmt) == "9:16":
        ids += ["vertical-reframe", "eye-height"]
    if any(E.as_list(c.get("text")) for c in edl["clips"]) or edl.get("subtitles"):
        ids += ["emphasis", "tracking-case", "alignment"]
    if any(E.transition(c)[0] != "cut" for c in edl["clips"]):
        ids += ["dissolve-length", "match-cut"]
    if any(c.get("inserts") for c in edl["clips"]):
        ids += ["l-cut", "cutaway"]
    if any(c.get("speed", 1.0) < 0.6 for c in edl["clips"]):
        ids.append("speed-ramp-quality")
    if edl.get("overlays"):
        ids += ["easing", "timing", "direction-logic", "grid-12"]
    known = {r["id"]: r for r in rules()}
    return [known[i] for i in ids if i in known]


def markdown(findings, checklist):
    lines = ["## Craft check (automatic)", "", "| Check | Rule | Result | Detail |", "|---|---|---|---|"]
    lines += ["| {} | `{}` | {} | {} |".format(f["check"], f["rule"], f["result"].upper(), f["detail"].replace("|", "/")) for f in findings]
    lines += ["", "## Craft checklist (Mann confirms on the frames)", ""]
    lines += ["- [ ] **{}** (`{}`): {}".format(r["name"], r["id"], r["how"]) for r in checklist]
    return "\n".join(lines) + "\n"


__all__ = ["rules", "rule", "pairing", "theme", "check", "manual_checklist", "markdown"]
