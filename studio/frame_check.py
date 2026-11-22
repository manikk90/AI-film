#!/usr/bin/env python3
"""QC a render before it goes to the owner: black frames, frozen stretches, size, fps, duration and audio.

    python3 studio/frame_check.py final.mp4 [--size 1080x1920] [--fps 30] [--audio song.mp3] [--max-mb 20] [--silent]

Exit 1 with a list of problems, else prints OK and the facts (paste them into 06-qc.md). Black = ffmpeg blackdetect
(>= 0.1 s, pixel 0.10); frozen = freezedetect (>= 1.5 s, noise -60 dB; a deliberate hold may trip it, say so in QC).
The audio and video streams must start within 0.05 s of each other and end within 0.1 s. With --audio, the film's
duration must match the source audio within 0.1 s, and (when numpy is installed) the first 20 s of the film's audio
are cross-correlated with the source to catch a shifted track (offset over 40 ms fails). That finds a track that
starts late or early; it does not prove every cut is in sync. --size compares the size as displayed (rotation
applied). --silent: a video meant to have no audio (a living-painting loop) passes without an audio stream.
Needs FFmpeg and ffprobe.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys


def probe(path: str) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def detect(path: str) -> tuple[list, list]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-vf", "blackdetect=d=0.1:pix_th=0.10,freezedetect=n=-60dB:d=1.5",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    black = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)
    frozen = re.findall(r"freeze_start: ([\d.]+)", r.stderr)
    return [(float(s), float(e)) for s, e in black], [float(s) for s in frozen]


def audio_offset(video: str, source: str, seconds: float = 20.0, sr: int = 8000):
    """Seconds the film's audio lags the source audio (positive = late), by cross-correlating the first `seconds`.
    None when numpy is missing or either side is silent."""
    try:
        import numpy as np
    except ImportError:
        return None

    def pcm(path):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-t", str(seconds), "-ac", "1", "-ar", str(sr),
                              "-f", "f32le", "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.float32).astype(np.float64)
    a, b = pcm(video), pcm(source)
    if len(a) < sr // 2 or len(b) < sr // 2 or not a.any() or not b.any():
        return None
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    xc = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    k = int(np.argmax(np.abs(xc)))
    if k > n // 2:
        k -= n
    return k / sr


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video")
    ap.add_argument("--size")
    ap.add_argument("--fps", type=float)
    ap.add_argument("--audio")
    ap.add_argument("--max-mb", type=float)
    ap.add_argument("--silent", action="store_true", help="no audio stream is expected")
    ap.add_argument("--allow-black-ends", action="store_true", help="ignore black within 1 s of the start or end (fades)")
    a = ap.parse_args(argv)
    if a.silent and a.audio:
        ap.error("--silent means no audio is expected; it cannot be combined with --audio")
    info = probe(a.video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    has_audio = au is not None
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from media_probe import rotation
    vw, vh = (v["height"], v["width"]) if rotation(v) in (90, 270) else (v["width"], v["height"])
    dur = float(info["format"]["duration"])
    num, den = map(int, v["r_frame_rate"].split("/"))
    fps = num / den
    problems = []
    if a.size and f"{vw}x{vh}" != a.size:
        problems.append(f"size {vw}x{vh} as displayed, expected {a.size}")
    if a.fps and abs(fps - a.fps) > 0.01:
        problems.append(f"fps {fps:.3f}, expected {a.fps}")
    if not has_audio and not a.silent:
        problems.append("no audio stream")
    if has_audio and a.silent:
        problems.append("an audio stream is present but --silent says the video has none")
    if has_audio:
        vs, as_ = float(v.get("start_time") or 0), float(au.get("start_time") or 0)
        if abs(vs - as_) > 0.05:
            problems.append(f"audio stream starts at {as_:.3f} s, video at {vs:.3f} s")
        vd, ad_ = float(v.get("duration") or dur), float(au.get("duration") or dur)
        if abs(vd - ad_) > 0.1:
            problems.append(f"audio stream lasts {ad_:.2f} s, video {vd:.2f} s")
    if a.audio:
        ad = float(probe(a.audio)["format"]["duration"])
        if abs(ad - dur) > 0.1:
            problems.append(f"duration {dur:.2f} s vs audio {ad:.2f} s")
        lag = audio_offset(a.video, a.audio) if has_audio else None
        if lag is not None and abs(lag) > 0.04:
            problems.append(f"the film's audio is shifted {lag * 1000:+.0f} ms against the source audio")
    size_mb = os.path.getsize(a.video) / 1e6
    if a.max_mb and size_mb > a.max_mb:
        problems.append(f"{size_mb:.1f} MB > {a.max_mb} MB")
    black, frozen = detect(a.video)
    for s, e in black:
        if a.allow_black_ends and (s < 1.0 or e > dur - 1.0):
            continue
        problems.append(f"black frames {s:.2f}-{e:.2f} s")
    for s in frozen:
        problems.append(f"frozen picture from {s:.2f} s")
    facts = f"{v['width']}x{v['height']} {fps:.2f} fps {dur:.2f} s {size_mb:.1f} MB audio={'yes' if has_audio else 'no'}"
    if problems:
        print("FAIL " + facts + "\n- " + "\n- ".join(problems))
        return 1
    print("OK " + facts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
