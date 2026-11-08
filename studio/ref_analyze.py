#!/usr/bin/env python3
"""Break a reference reel down: frames at 2 fps, every cut, shot lengths and the grade of each shot.

    python3 studio/ref_analyze.py reference.mp4 out_dir [--threshold 0.3] [--fps 2]

Writes into out_dir:
- frames/f_0001.jpg ...  frames at --fps (default 2) to look at
- ref.json               duration, cuts (s), shots [{start, end, len, black, white, mean_rgb, tint}], median shot length
- ref.md                 the same as a short table
Cuts come from FFmpeg scene detection (select='gt(scene,T)',showinfo). Per shot it samples frames and measures the
black level (2nd percentile luma), white level (98th), mean RGB and the tint (warm if R > B, cool if B > R).
Needs numpy and FFmpeg.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def cuts(path: Path, thr: float) -> list[float]:
    res = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", f"select='gt(scene,{thr})',showinfo",
                          "-an", "-f", "null", "-"], capture_output=True, text=True)
    return sorted({round(float(m), 3) for m in re.findall(r"pts_time:([0-9.]+)", res.stderr)})


def frame_at(path: Path, t: float, w: int = 160, h: int = 284) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8)[: w * h * 3].reshape(-1, 3).astype(np.float32) if raw else np.zeros((0, 3))


def grade(path: Path, a: float, b: float) -> dict:
    ts = np.linspace(a + 0.05 * (b - a), b - 0.05 * (b - a), 3) if b - a > 0.2 else [(a + b) / 2]
    px = np.concatenate([frame_at(path, float(t)) for t in ts])
    if not len(px):
        return {}
    luma = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mean = px.mean(axis=0)
    rb = float(mean[0] - mean[2])
    return {"black": round(float(np.percentile(luma, 2)), 1), "white": round(float(np.percentile(luma, 98)), 1),
            "mean_rgb": [round(float(v), 1) for v in mean],
            "tint": "warm" if rb > 6 else "cool" if rb < -6 else "neutral"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("reel", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--threshold", type=float, default=0.3)
    ap.add_argument("--fps", type=float, default=2)
    a = ap.parse_args(argv)
    frames = a.out_dir / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a.reel), "-vf", f"fps={a.fps},scale=-2:640",
                    "-q:v", "3", str(frames / "f_%04d.jpg")], check=True)
    dur = duration(a.reel)
    cs = cuts(a.reel, a.threshold)
    bounds = [0.0] + [c for c in cs if 0.05 < c < dur - 0.05] + [dur]
    shots = []
    for s, e in zip(bounds, bounds[1:]):
        shots.append({"start": round(s, 3), "end": round(e, 3), "len": round(e - s, 3), **grade(a.reel, s, e)})
    lens = [s["len"] for s in shots]
    data = {"source": a.reel.name, "duration": round(dur, 3), "threshold": a.threshold, "cuts": bounds[1:-1],
            "shots": shots, "median_shot": round(float(np.median(lens)), 3) if lens else None,
            "frames_dir": str(frames), "frames_fps": a.fps}
    (a.out_dir / "ref.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    md = [f"# Reference: {a.reel.name}", "",
          f"{dur:.2f} s, {len(shots)} shots, median shot {data['median_shot']} s, cuts at scene > {a.threshold}.", "",
          "| # | start | len | black | white | tint |", "|---|---|---|---|---|---|"]
    md += [f"| {i} | {s['start']:.2f} | {s['len']:.2f} | {s.get('black', '')} | {s.get('white', '')} | "
           f"{s.get('tint', '')} |" for i, s in enumerate(shots, 1)]
    (a.out_dir / "ref.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{a.out_dir / 'ref.json'}: {len(shots)} shots, median {data['median_shot']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
