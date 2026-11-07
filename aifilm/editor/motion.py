"""Mann's motion-graphics template library (editor/motion/templates/*.html).

Each template is a canvas page drawn as a pure function of time, rendered by headless
Chromium (Playwright) and FFmpeg, so the same command works in the cloud session and on a
laptop without npx or a network fetch. Output is a ProRes 4444 .mov with alpha (an overlay
for an edit) or an H.264 .mp4 on the theme background (a standalone clip), or PNG stills.

Colours come from a craft colour theme and fonts from a font pairing (installed with
`fonts-install`), so motion graphics match the film's typography and grade.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

from ..core import inside, project_lock, read_json, require, write_json

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "editor" / "motion"
TEMPLATES = ROOT / "templates"
RENDERER = ROOT / "render_motion.cjs"
CENTRED = {"title-card", "counter", "kinetic-words", "stat-card"}


def templates():
    out = []
    for path in sorted(TEMPLATES.glob("*.html")):
        m = re.search(r'<script type="application/json" id="meta">(.*?)</script>', path.read_text(encoding="utf-8"), re.S)
        require(m is not None, "Template {} has no meta block".format(path.name))
        out.append(dict(json.loads(m.group(1)), file=str(path)))
    return out


def template(name):
    for t in templates():
        if t["name"] == name:
            return t
    from ..core import ProductionError
    raise ProductionError("Unknown motion template {!r}; available: {}".format(name, ", ".join(t["name"] for t in templates())))


def available():
    if not (shutil.which("node") and shutil.which("ffmpeg")):
        return False
    probe = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True, text=True, cwd=str(REPO))
    return probe.returncode == 0


def roles(colours):
    """Assign theme colours to roles by measurement, not list order: background = darkest,
    ink = lightest, accent = the most saturated colour that still reads against the background."""
    from .craft import contrast, luminance
    rgb = {c: tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for c in colours}
    sat = lambda c: (max(rgb[c]) - min(rgb[c])) / float(max(rgb[c]) or 1)  # noqa: E731
    bg = min(colours, key=lambda c: luminance(rgb[c]))
    ink = max(colours, key=lambda c: luminance(rgb[c]))
    rest = [c for c in colours if c not in (bg, ink)] or [ink]
    readable = [c for c in rest if contrast(rgb[c], rgb[bg]) >= 3.0] or [ink]
    accent = max(readable, key=lambda c: sat(c) * min(contrast(rgb[c], rgb[bg]), 7.0))  # vivid and clearly readable
    others = [c for c in rest if c != accent]
    accent2 = max(others, key=sat) if others else accent
    muted = min(others, key=sat) if others else ink
    if contrast(rgb[ink], rgb[bg]) < 4.5:
        ink = "#ffffff" if luminance(rgb[bg]) < 0.4 else "#111111"
    return {"bg": bg, "ink": ink, "accent": accent, "accent2": accent2, "muted": muted}


def design(theme=None, pairing=None):
    """Theme colours and font files for the templates' variables."""
    from . import craft, fonts
    v = {}
    if theme:
        v.update(roles(craft.theme(theme)["colours"]))
    if pairing:
        p = craft.pairing(pairing)
        v.update(font_display=p["display"], font_text=p["text"])
        faces = []
        for fam, weight in ((p["display"], p.get("display_weight", 700)), (p["text"], p.get("text_weight", 600)), (p["display"], 900)):
            f = fonts.resolve(fam, weight)
            if f:
                faces.append({"family": fam, "url": Path(f).resolve().as_uri(), "weight": weight})
        v["fonts"] = faces
    return v


def render(name, out, size=(1080, 1920), duration=None, variables=None, theme=None, pairing=None, fps=30, stills=None):
    """Render template `name` to `out` (.mov alpha / .mp4) or, with `stills`, to `<out>_N.png`."""
    require(available(), "Motion templates need Node, FFmpeg and Playwright: `npm i -g playwright && npx playwright install chromium` "
                         "(already present in the cloud session)")
    t = template(name)
    dur = float(duration or t.get("duration", 3))
    v = dict(design(theme, pairing))
    v.update(variables or {})
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["node", str(RENDERER), t["file"], str(out), "--size", "{}x{}".format(*size), "--dur", str(dur), "--fps", str(fps),
           "--vars", json.dumps(v, ensure_ascii=False)]
    if stills:
        cmd += ["--stills", ",".join(str(s) for s in stills)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, cwd=str(REPO))
    require(result.returncode == 0, "Motion render failed: " + (result.stderr or result.stdout).strip()[-600:])
    if stills:
        return [l for l in result.stdout.splitlines() if l.endswith(".png")]
    return json.loads(result.stdout.strip().splitlines()[-1])


def placement(root, edl, at, duration):
    """Layout hints from the edit itself: keep graphics above the burned captions, and move
    centred graphics off the tracked face (reframed clips) for the time they are on screen."""
    from . import craft
    from . import edl as E
    fmt = edl["format"]
    out = {}
    if edl.get("subtitles") and edl["subtitles"].get("burn", True):
        out["bottom_limit"] = round(craft.subtitle_bbox(fmt, edl["subtitles"])["y0"] / fmt["height"] - 0.015, 3)
    rows, _ = E.timeline(edl)
    faces = []
    for row, clip in zip(rows, edl["clips"]):
        if row["end"] > at and row["start"] < at + duration and clip.get("reframe", fmt.get("reframe")) == "auto":
            from . import reframe
            if reframe.available():
                faces += [f["y"] for f in reframe.framing(root, edl, clip, row["duration"])]
    if faces:
        face_y = sorted(faces)[len(faces) // 2]
        out["y"] = 0.72 if face_y < 0.45 else 0.3  # opposite half of the frame from the face
        if "bottom_limit" in out and out["y"] > out["bottom_limit"] - 0.08:
            out["y"] = round(out["bottom_limit"] - 0.1, 3)
    return out


def add(edit_root, name, at, duration=None, variables=None, label=None):
    """Render a template sized to the edit, store it in <edit>/mg/, and add it to edl.json as an
    overlay at `at` seconds. Uses the EDL's typography theme and pairing."""
    root = Path(edit_root)
    with project_lock(root):
        edl = read_json(root / "edl.json")
        fmt = edl["format"]
        typo = edl.get("typography") or {}
        mg = root / "mg"
        mg.mkdir(exist_ok=True)
        n = 1 + sum(1 for o in edl.get("overlays", []) if o.get("template") == name)
        rel = "mg/{}-{}.mov".format(label or name, n)
        placed = dict(placement(root, edl, float(at), float(duration or template(name).get("duration", 3))))
        if name not in CENTRED:
            placed.pop("y", None)  # point templates use x/y as the target, not a layout hint
        placed.update(variables or {})
        render(name, inside(root, rel), (fmt["width"], fmt["height"]), duration, placed, typo.get("theme"), typo.get("pairing"),
               fps=fmt.get("fps", 30))
        entry = {"file": rel, "at": float(at), "template": name, "vars": variables or {}}
        edl.setdefault("overlays", []).append(entry)
        write_json(root / "edl.json", edl)
        return entry


__all__ = ["templates", "template", "available", "design", "render", "add", "inside"]
