#!/usr/bin/env python3
"""QC a render before it goes to the owner: black frames, frozen stretches, size, fps, duration and audio.

    python3 studio/frame_check.py final.mp4 [--size 1080x1920] [--fps 30] [--audio song.mp3] [--max-mb 20]

Exit 1 with a list of problems, else prints OK and the facts (paste them into 06-qc.md). Black = ffmpeg blackdetect
(>= 0.1 s, pixel 0.10); frozen = freezedetect (>= 1.5 s, noise -60 dB; a deliberate hold may trip it, say so in QC).
With --audio, the video's duration must match the source audio within 0.1 s. Needs FFmpeg and ffprobe.
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video")
    ap.add_argument("--size")
    ap.add_argument("--fps", type=float)
    ap.add_argument("--audio")
    ap.add_argument("--max-mb", type=float)
    ap.add_argument("--allow-black-ends", action="store_true", help="ignore black within 1 s of the start or end (fades)")
    a = ap.parse_args(argv)
    info = probe(a.video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    dur = float(info["format"]["duration"])
    num, den = map(int, v["r_frame_rate"].split("/"))
    fps = num / den
    problems = []
    if a.size and f"{v['width']}x{v['height']}" != a.size:
        problems.append(f"size {v['width']}x{v['height']}, expected {a.size}")
    if a.fps and abs(fps - a.fps) > 0.01:
        problems.append(f"fps {fps:.3f}, expected {a.fps}")
    if not has_audio:
        problems.append("no audio stream")
    if a.audio:
        ad = float(probe(a.audio)["format"]["duration"])
        if abs(ad - dur) > 0.1:
            problems.append(f"duration {dur:.2f} s vs audio {ad:.2f} s")
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
