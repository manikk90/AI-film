#!/usr/bin/env python3
"""QC for a living-painting loop: does it close without a jump, does every part of the picture move, does it snap,
and is any frame black. These are the polish rounds of the method, measured instead of eyeballed.

    python3 .claude/skills/living-painting/scripts/loop_check.py loop.mp4 [--grid 6x10] [--json report.json]

Checks (frames downscaled to 108x192 grey):
  seam    the jump from the last frame back to the first, against the median frame-to-frame change.
          Fails when it is over 2.5x the median: the loop visibly restarts.
  still   the share of grid cells whose picture never changes over the clip. Fails above 15 %: "parts of the
          picture stand still". Fix: give each a small reasoned motion (wind, water, light).
  snap    frame-to-frame changes over 6x the median: a sudden jump inside the loop. Fix: ease the motion.
  black   frames darker than 4 % mean: a broken or empty frame.
  motion  the median frame-to-frame change; under 0.15 grey levels the subject is hardly moving.
Exit 1 when any check fails. Needs numpy and FFmpeg.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np

W, H = 108, 192


def frames(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:flags=area,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)


def check(f: np.ndarray, grid=(6, 10)) -> dict:
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    med = float(np.median(d)) if len(d) else 0.0
    seam = float(np.abs(f[-1] - f[0]).mean())
    gx, gy = grid
    cw, ch = W // gx, H // gy
    span = f.max(axis=0) - f.min(axis=0)
    cells = [span[j * ch:(j + 1) * ch, i * cw:(i + 1) * cw].mean() for j in range(gy) for i in range(gx)]
    still = float(np.mean([c < 2.0 for c in cells]))
    snaps = [int(i + 1) for i, v in enumerate(d) if med > 0 and v > 6 * med]
    black = [int(i) for i, m in enumerate(f.mean(axis=(1, 2))) if m < 0.04 * 255]
    res = {
        "frames": int(len(f)), "median_change": round(med, 3), "seam_change": round(seam, 3),
        "seam_ratio": round(seam / med, 2) if med else None, "still_share": round(still, 3),
        "snap_frames": snaps[:20], "black_frames": black[:20],
    }
    res["fails"] = [name for name, bad in [
        ("seam", med > 0 and seam > 2.5 * med), ("still", still > 0.15), ("snap", bool(snaps)),
        ("black", bool(black)), ("motion", med < 0.15)] if bad]
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video")
    ap.add_argument("--grid", default="6x10")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    gx, gy = map(int, a.grid.split("x"))
    res = check(frames(a.video), (gx, gy))
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    print(("FAIL " + ", ".join(res["fails"]) if res["fails"] else "OK") + " " + json.dumps(res))
    return 1 if res["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
