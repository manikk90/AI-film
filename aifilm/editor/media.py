"""FFmpeg-backed measurements. Every number here is measured from the file, never guessed."""

import json
import re
import shutil
import subprocess
from pathlib import Path

from ..core import ProductionError, require

FFMPEG_TIMEOUT = 3600


def need(tool):
    require(shutil.which(tool) is not None, "{} is required; run `python3 -m aifilm.editor doctor`".format(tool))


def run(cmd, timeout=FFMPEG_TIMEOUT):
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-6:])
        raise ProductionError("{} failed:\n{}".format(Path(str(cmd[0])).name, tail))
    return result


def ratio(value):
    try:
        num, den = str(value).split("/")
        return float(num) / float(den) if float(den) else 0.0
    except ValueError:
        return float(value or 0)


def rotation(stream):
    """Degrees the player rotates this video stream (display matrix side data or the old rotate tag)."""
    deg = (stream.get("tags") or {}).get("rotate")
    for side in stream.get("side_data_list") or []:
        if "rotation" in side:
            deg = side["rotation"]
    try:
        return int(round(float(deg or 0))) % 360
    except (TypeError, ValueError):
        return 0


def display_size(stream):
    """Width and height as shown on screen: phone footage stored landscape with a 90/270 turn is portrait."""
    w, h = int(stream.get("width", 0)), int(stream.get("height", 0))
    return (h, w) if rotation(stream) in (90, 270) else (w, h)


def probe(path):
    need("ffprobe")
    path = Path(path)
    require(path.is_file(), "Missing media file: {}".format(path))
    info = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path.resolve()], 120).stdout)
    video = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    fmt = info.get("format", {})
    out = {"path": str(path), "duration": float(fmt.get("duration") or 0), "has_video": bool(video), "has_audio": bool(audio)}
    if video:
        v = video[0]
        w, h = display_size(v)
        out.update(width=w, height=h, rotation=rotation(v),
                   fps=round(ratio(v.get("avg_frame_rate") or v.get("r_frame_rate") or 0), 3), vcodec=v.get("codec_name"))
        if not out["duration"]:
            out["duration"] = float(v.get("duration") or 0)
    if audio:
        out.update(acodec=audio[0].get("codec_name"), sample_rate=int(audio[0].get("sample_rate", 0)),
                   channels=int(audio[0].get("channels", 0)))
    return out


def scene_cuts(path, threshold=0.3, max_seconds=None):
    """Return cut timestamps (seconds) where FFmpeg's scene score exceeds `threshold`."""
    need("ffmpeg")
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", Path(path).resolve()]
    if max_seconds:
        cmd[3:3] = ["-t", str(max_seconds)]
    cmd += ["-an", "-vf", "select='gt(scene,{})',showinfo".format(threshold), "-f", "null", "-"]
    err = run(cmd).stderr
    return [round(float(t), 3) for t in re.findall(r"pts_time:([0-9.]+)", err)]


def loudness(path):
    """Integrated loudness (LUFS), true peak (dBTP) and loudness range of the audio stream."""
    need("ffmpeg")
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", Path(path).resolve(), "-vn",
               "-af", "loudnorm=print_format=json", "-f", "null", "-"]).stderr
    block = err[err.rfind("{"): err.rfind("}") + 1]
    data = json.loads(block)
    num = lambda k: None if data.get(k) in (None, "-inf", "inf") else round(float(data[k]), 2)
    return {"lufs": num("input_i"), "true_peak": num("input_tp"), "lra": num("input_lra")}


def silences(path, noise_db=-40, min_seconds=1.0):
    need("ffmpeg")
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", Path(path).resolve(), "-vn",
               "-af", "silencedetect=noise={}dB:d={}".format(noise_db, min_seconds), "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    out = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        out.append({"start": round(max(s, 0), 3), "end": None if e is None else round(e, 3)})
    return out


def black_segments(path, min_seconds=0.5):
    need("ffmpeg")
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", Path(path).resolve(), "-an",
               "-vf", "blackdetect=d={}:pix_th=0.10".format(min_seconds), "-f", "null", "-"]).stderr
    return [{"start": float(a), "end": float(b)} for a, b in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", err)]


def frame_rgb(path, at, size=(48, 27)):
    """Decode one frame at `at` seconds into a list of (r, g, b) tuples at a tiny size."""
    need("ffmpeg")
    w, h = size
    data = subprocess.run(["ffmpeg", "-v", "error", "-ss", "{:.3f}".format(max(at, 0)), "-i", str(Path(path).resolve()),
                           "-frames:v", "1", "-vf", "scale={}:{}:flags=area".format(w, h), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          capture_output=True, timeout=120).stdout
    return [tuple(data[i:i + 3]) for i in range(0, len(data) - 2, 3)]


def save_frame(path, at, out, vf=None, width=None):
    need("ffmpeg")
    filters = [f for f in [vf, "scale={}:-2".format(width) if width else None] if f]
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", "{:.3f}".format(max(at, 0)), "-i", Path(path).resolve(), "-frames:v", "1"]
    if filters:
        cmd += ["-vf", ",".join(filters)]
    cmd += ["-q:v", "3", Path(out).resolve()]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    run(cmd, 120)
    return Path(out)


def hexcolor(rgb):
    return "#{:02x}{:02x}{:02x}".format(*[int(round(c)) for c in rgb])


def palette(pixels, k=5, rounds=8):
    """Dominant colours by a small deterministic k-means. Returns [(hex, share)] sorted by share."""
    if not pixels:
        return []
    ordered = sorted(pixels, key=lambda p: 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2])
    k = min(k, len(set(ordered)))
    centers = [ordered[int((i + 0.5) * len(ordered) / k)] for i in range(k)]
    groups = []
    for _ in range(rounds):
        groups = [[] for _ in centers]
        for p in pixels:
            best = min(range(len(centers)), key=lambda i: sum((p[j] - centers[i][j]) ** 2 for j in range(3)))
            groups[best].append(p)
        centers = [tuple(sum(c[j] for c in g) / len(g) for j in range(3)) if g else centers[i] for i, g in enumerate(groups)]
    total = float(len(pixels))
    result = [(hexcolor(c), round(len(g) / total, 3)) for c, g in zip(centers, groups) if g]
    return sorted(result, key=lambda x: -x[1])


def tone(pixels):
    """Mean luma (0-255), mean saturation (0-1) and warmth (mean R - B) of a frame."""
    if not pixels:
        return {"luma": 0, "saturation": 0, "warmth": 0}
    n = float(len(pixels))
    luma = sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels) / n
    sat = sum((max(p) - min(p)) / max(p) if max(p) else 0 for p in pixels) / n
    warm = sum(r - b for r, _, b in pixels) / n
    return {"luma": round(luma, 1), "saturation": round(sat, 3), "warmth": round(warm, 1)}
