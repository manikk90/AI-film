"""Face-aware reframing: track the main face in a source and move the crop with it, so a
16:9 interview cut to 9:16 keeps the speaker in frame instead of centre-cropping them out.

Detection uses OpenCV's bundled Haar cascades (no model download): opencv-python-headless
4.x (4.10.0.84 is pinned by editor/install.sh; OpenCV 5 dropped the cascade files). The crop
path is smoothed (gap fill + centred moving average + tolerance-based simplification) and simplified, then written as
a piecewise-linear FFmpeg expression in the crop filter. Tracks are cached by file hash.
"""

import subprocess
from pathlib import Path

from ..core import inside, now, read_json, require, write_json

VERSION = 1
EYE_LINE = 0.40      # face centre at 40 % of the crop height: eyes near the upper third
DEAD_ZONE = 0.04     # ignore moves smaller than 4 % of the source width
_CASCADES = None


def available():
    try:
        import cv2  # noqa: F401
        return hasattr(cv2, "data") and Path(cv2.data.haarcascades, "haarcascade_frontalface_default.xml").exists()
    except ImportError:
        return False


def usable():
    """Faces can be tracked: OpenCV's Haar cascade is installed, or a detector was put in place of `detect`."""
    return available() or detect.__module__ != __name__


def detect(gray):
    """Faces in a grayscale numpy frame as [(x, y, w, h)]. Replaceable in tests."""
    global _CASCADES
    import cv2
    if _CASCADES is None:
        base = cv2.data.haarcascades
        _CASCADES = [cv2.CascadeClassifier(base + "haarcascade_frontalface_default.xml"),
                     cv2.CascadeClassifier(base + "haarcascade_profileface.xml")]
    h = gray.shape[0]
    size = (max(int(h * 0.06), 24),) * 2
    found = list(_CASCADES[0].detectMultiScale(gray, 1.1, 5, minSize=size))
    if not found:
        found = list(_CASCADES[1].detectMultiScale(gray, 1.1, 5, minSize=size))
    if not found:
        flipped = gray[:, ::-1]
        w = gray.shape[1]
        found = [(w - x - fw, y, fw, fh) for x, y, fw, fh in _CASCADES[1].detectMultiScale(flipped.copy(), 1.1, 5, minSize=size)]
    return [tuple(int(v) for v in f) for f in found]


def track(root, rel, rate=4.0, width=640):
    """Main-face track of a source: samples of {t, face: [cx, cy, size] in 0-1 or None}."""
    from . import edl as E
    from . import media
    root = Path(root)
    sha = E.hashed(root, rel)
    cache = root / "analysis" / "{}-faces-v{}.json".format(sha[:20], VERSION)
    if cache.exists():
        return read_json(cache)
    require(usable(),
            "Face tracking needs OpenCV with Haar cascades: python3 -m pip install opencv-python-headless==4.10.0.84")
    import numpy as np
    info = media.probe(inside(root, rel))
    dur = info["duration"]
    rate = min(rate, 600.0 / max(dur, 1.0))
    sw = width
    sh = int(round(info["height"] * sw / float(info["width"]) / 2)) * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(inside(root, rel).resolve()), "-vf",
                          "fps={:.4f},scale={}:{}".format(rate, sw, sh), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, timeout=1800).stdout
    n = sw * sh
    samples, prev = [], None
    for i in range(len(raw) // n):
        gray = np.frombuffer(raw[i * n:(i + 1) * n], dtype=np.uint8).reshape(sh, sw)
        faces = detect(gray)
        face = None
        if faces:
            def score(f):
                x, y, w, h = f
                c = (x + w / 2.0) / sw, (y + h / 2.0) / sh
                stick = 0 if prev is None else ((c[0] - prev[0]) ** 2 + (c[1] - prev[1]) ** 2) ** 0.5
                return w * h / float(n) - 0.5 * stick  # biggest face, but stay with the same person
            x, y, w, h = max(faces, key=score)
            face = [round((x + w / 2.0) / sw, 4), round((y + h / 2.0) / sh, 4), round(h / float(sh), 4)]
            prev = face
        samples.append({"t": round((i + 0.5) / rate, 3), "face": face})
    detected = sum(1 for s in samples if s["face"]) / float(max(len(samples), 1))
    result = {"file": rel, "version": VERSION, "rate": rate, "width": info["width"], "height": info["height"],
              "detected_share": round(detected, 3), "samples": samples, "created": now()}
    write_json(cache, result)
    return result


def crop_size(src_w, src_h, out_w, out_h):
    a = out_w / float(out_h)
    if src_w / float(src_h) > a:
        ch = src_h
        cw = int(round(src_h * a / 2)) * 2
    else:
        cw = src_w
        ch = int(round(src_w / a / 2)) * 2
    return min(cw, src_w), min(ch, src_h)


def centres(tr, start, end, window=5):
    """Face centres (source 0-1) for source times in [start, end]: gaps held from the last
    detection, then a centred moving average (no lag behind a moving subject)."""
    pts = [s for s in tr["samples"] if start - 1.0 <= s["t"] <= end + 1.0]
    known = [s for s in pts if s["face"]]
    if not known:
        return [(start, 0.5, 0.5), (end, 0.5, 0.5)], False
    filled, last = [], known[0]["face"]
    for s in pts:
        last = s["face"] or last
        filled.append((s["t"], last[0], last[1]))
    half = window // 2
    out = []
    for i, (t, _, _) in enumerate(filled):
        win = filled[max(0, i - half):i + half + 1]
        out.append((t, sum(w[1] for w in win) / len(win), sum(w[2] for w in win) / len(win)))
    return out, True


def simplify(points, tol):
    """Drop keyframes that a straight line already explains within `tol` (Douglas-Peucker)."""
    if len(points) < 3:
        return points
    (t0, v0), (t1, v1) = points[0], points[-1]
    worst, idx = -1.0, 0
    for i, (t, v) in enumerate(points[1:-1], 1):
        lin = v0 + (v1 - v0) * (t - t0) / ((t1 - t0) or 1)
        if abs(v - lin) > worst:
            worst, idx = abs(v - lin), i
    if worst <= tol:
        return [points[0], points[-1]]
    return simplify(points[:idx + 1], tol)[:-1] + simplify(points[idx:], tol)


def piecewise(points):
    """FFmpeg expression of t for a piecewise-linear curve (flat sum of clamped ramps)."""
    points = [(round(t, 3), round(v, 1)) for t, v in points]
    if all(abs(v - points[0][1]) < 0.5 for _, v in points):
        return "{:.1f}".format(points[0][1])
    terms = ["{:.1f}".format(points[0][1])]
    for (ta, va), (tb, vb) in zip(points, points[1:]):
        if tb > ta and abs(vb - va) >= 0.5:
            terms.append("{:.5f}*(clip(t\\,{:.3f}\\,{:.3f})-{:.3f})".format((vb - va) / (tb - ta), ta, tb, ta))
    return "+".join(terms)


def plan(tr, clip_in, clip_out, speed, out_w, out_h):
    """Crop box and x/y expressions (output-clip time) that follow the face."""
    sw, sh = tr["width"], tr["height"]
    cw, ch = crop_size(sw, sh, out_w, out_h)
    pts, found = centres(tr, clip_in, clip_out)
    xs, ys = [], []
    for t, cx, cy in pts:
        tout = max((t - clip_in) / speed, 0.0)
        xs.append((tout, min(max(cx * sw - cw / 2.0, 0), sw - cw)))
        ys.append((tout, min(max(cy * sh - EYE_LINE * ch, 0), sh - ch)))
    tol = max(2.0, DEAD_ZONE * 0.5 * sw)  # jitter inside the tolerance becomes a steady hold
    return {"w": cw, "h": ch, "x": piecewise(simplify(xs, tol)), "y": piecewise(simplify(ys, tol)), "face_found": found,
            "keyframes": len(simplify(xs, tol))}


def chain(root, edl, clip, src=None, clip_in=None, clip_out=None, speed=None):
    """Crop+scale filters for a reframed clip (or insert), or None when reframing is off."""
    mode = clip.get("reframe", edl["format"].get("reframe"))
    if mode not in ("auto",) or edl["format"].get("fit", "cover") != "cover":
        return None
    fmt = edl["format"]
    rel = src or edl["sources"][clip["source"]]
    tr = track(root, rel)
    p = plan(tr, clip["in"] if clip_in is None else clip_in, clip["out"] if clip_out is None else clip_out,
             clip.get("speed", 1.0) if speed is None else speed, fmt["width"], fmt["height"])
    return ["crop=w={}:h={}:x='{}':y='{}'".format(p["w"], p["h"], p["x"], p["y"]), "scale={}:{}".format(fmt["width"], fmt["height"])]


def framing(root, edl, clip, row_duration):
    """Where the tracked face lands in the output frame (0-1), sampled over the clip."""
    rel = edl["sources"][clip["source"]]
    tr = track(root, rel)
    fmt = edl["format"]
    cw, ch = crop_size(tr["width"], tr["height"], fmt["width"], fmt["height"])
    p = plan(tr, clip["in"], clip["out"], clip.get("speed", 1.0), fmt["width"], fmt["height"])
    out = []
    for s in tr["samples"]:
        if s["face"] and clip["in"] <= s["t"] <= clip["out"]:
            tout = (s["t"] - clip["in"]) / clip.get("speed", 1.0)
            x = evaluate(p["x"], tout)
            y = evaluate(p["y"], tout)
            fx = (s["face"][0] * tr["width"] - x) / cw
            fy = (s["face"][1] * tr["height"] - y) / ch
            fs = s["face"][2] * tr["height"] / ch
            out.append({"t": round(tout, 2), "x": round(fx, 3), "y": round(fy, 3), "size": round(fs, 3)})
    return out


def evaluate(expr, t):
    """Evaluate a piecewise() expression in Python (for checks)."""
    text = expr.replace("\\,", ",")
    clip = lambda v, a, b: min(max(v, a), b)  # noqa: E731
    return eval(text, {"__builtins__": {}}, {"clip": clip, "t": t})


__all__ = ["available", "detect", "track", "plan", "chain", "framing", "evaluate"]
