#!/usr/bin/env python3
"""Person matte for every frame of a clip (MediaPipe selfie segmentation), for skills that put graphics behind the
owner or trace their outline.

    python3 studio/person_matte.py clip.mp4 mattes/ [--fps 30] [--smooth 3] [--video matte.mp4]

Writes mattes/00001.png ... (8-bit alpha, 255 = person) at the clip's size, smoothed over --smooth frames so edges do
not boil, and optionally a grey matte video. A canvas page loads them as images and composites: background, graphics,
then the original frame masked by the matte. The owner's face is never filtered; the matte only cuts.
Needs mediapipe and numpy (pip install mediapipe) and FFmpeg. For body/hair/clothes classes or face and pose
landmarks (scribble-edit), use the MediaPipe Tasks models; this script covers the plain person cut-out.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np


def frames(path: str, fps: float):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout
    w, h = map(int, out.strip().split(",")[:2])
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps}", "-f", "rawvideo", "-pix_fmt",
                          "rgb24", "-"], stdout=subprocess.PIPE)
    size = w * h * 3
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    p.wait()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("clip")
    ap.add_argument("outdir")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--smooth", type=int, default=3)
    ap.add_argument("--video")
    a = ap.parse_args(argv)
    try:
        import mediapipe as mp
        from PIL import Image
    except ImportError:
        sys.exit("mediapipe/Pillow missing: pip install mediapipe pillow")
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    hist: list[np.ndarray] = []
    n = 0
    with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0) as seg:
        for rgb in frames(a.clip, a.fps):
            m = seg.process(rgb).segmentation_mask.astype(np.float32)
            hist = (hist + [m])[-max(1, a.smooth):]
            avg = np.mean(hist, axis=0)
            n += 1
            Image.fromarray((np.clip((avg - 0.35) / 0.3, 0, 1) * 255).astype(np.uint8)).save(out / f"{n:05d}.png")
    if a.video:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", str(out / "%05d.png"),
                        "-pix_fmt", "yuv420p", a.video], check=True)
    print(f"{out}: {n} mattes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
