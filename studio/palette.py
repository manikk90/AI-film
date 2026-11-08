#!/usr/bin/env python3
"""60-30-10 colour check (studio/COLOR.md): how much of a frame each colour role takes.

  python3 studio/palette.py IMAGE_OR_VIDEO [--at 1,18.5,27.5] [--every 2]

Each frame is scaled to 72 px wide and split into 6 colour groups (k-means). The largest group and the groups
close to it are the main colour; loud groups (saturated and bright, well above the main) are the accent; the
rest is the second colour. Target: main 50-70 %, second 20-40 %, accent 3-15 %.
These are measurements of a downscaled frame, so treat a near miss as a judgement call, not a failure.
"""
from __future__ import annotations

import argparse
import colorsys
import subprocess
import sys

WIDTH = 72
BANDS = {"main": (50, 70), "second": (20, 40), "accent": (3, 15)}


def kmeans(pixels, k=3, iters=12):
    """Deterministic k-means: farthest-point start, so the same frame always gives the same groups."""
    centers = [max(pixels, key=lambda p: sum(p))]
    while len(centers) < k:
        centers.append(max(pixels, key=lambda p: min(sum((a - b) ** 2 for a, b in zip(p, c)) for c in centers)))
    for _ in range(iters):
        sums = [[0, 0, 0, 0] for _ in centers]
        for p in pixels:
            i = min(range(len(centers)), key=lambda j: sum((a - b) ** 2 for a, b in zip(p, centers[j])))
            s = sums[i]
            s[0] += p[0]; s[1] += p[1]; s[2] += p[2]; s[3] += 1
        new = [(s[0] / s[3], s[1] / s[3], s[2] / s[3]) if s[3] else c for s, c in zip(sums, centers)]
        if new == centers:
            break
        centers = new
    counts = [0] * len(centers)
    for p in pixels:
        counts[min(range(len(centers)), key=lambda j: sum((a - b) ** 2 for a, b in zip(p, centers[j])))] += 1
    return [(c, n / len(pixels)) for c, n in zip(centers, counts)]


def loud(rgb):
    """How loud a colour is: HSV saturation x value (0 grey or dark, 1 pure bright colour)."""
    _, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in rgb))
    return s * v


def roles(pixels, k=6):
    """{'main'|'second'|'accent': (rgb, share %, loudness)} for a list of (r, g, b) pixels.

    The frame is split into k colour groups. The largest group is the main colour, and groups close to it
    join its family. Loud groups (loudness >= 0.45 and 0.2 above the main colour) are the accent. The rest
    is the second colour. Each role reports its biggest group's colour and the whole family's share."""
    groups = [g for g in kmeans(pixels, k) if g[1] > 0]
    main = max(groups, key=lambda g: g[1])
    def near(a, b):
        return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5 < 60
    fam = {"main": [], "second": [], "accent": []}
    for g in groups:
        if loud(g[0]) >= 0.45 and loud(g[0]) >= loud(main[0]) + 0.2:
            fam["accent"].append(g)
        elif g is main or near(g[0], main[0]):
            fam["main"].append(g)
        else:
            fam["second"].append(g)
    out = {}
    for name, gs in fam.items():
        if gs:
            top = max(gs, key=lambda g: g[1])
            out[name] = (tuple(round(x) for x in top[0]), round(sum(g[1] for g in gs) * 100, 1), round(loud(top[0]), 2))
        else:
            out[name] = ((0, 0, 0), 0.0, 0.0)
    return out


def verdict(r):
    """'PASS' or the list of misses for one frame's roles."""
    misses = [f"{k} {r[k][1]:g}% (want {lo}-{hi})" for k, (lo, hi) in BANDS.items() if not lo <= r[k][1] <= hi]
    if not r["accent"][1]:
        misses.append("no loud accent")
    return "PASS" if not misses else "; ".join(misses)


def hexcode(rgb):
    return "#%02x%02x%02x" % rgb


def describe(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in rgb))
    return f"{hexcode(rgb)} h{round(h * 360)} s{s:.2f} v{v:.2f}"


def frame_pixels(path, t=None):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats"]
    if t is not None:
        cmd += ["-ss", str(t)]
    cmd += ["-i", path, "-frames:v", "1", "-vf", f"scale={WIDTH}:-2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    if not raw:
        raise SystemExit(f"no frame from {path} at {t}")
    return [tuple(raw[i:i + 3]) for i in range(0, len(raw) - 2, 3)]


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--at", help="comma-separated seconds")
    ap.add_argument("--every", type=float, help="sample every N seconds of a video")
    a = ap.parse_args(argv)
    if a.at:
        times = [float(x) for x in a.at.split(",")]
    elif a.every:
        d = duration(a.file)
        times = [round(i * a.every, 2) for i in range(int(d // a.every) + 1)] if d else [None]
    else:
        times = [None]
    passed = 0
    for t in times:
        r = roles(frame_pixels(a.file, t))
        v = verdict(r)
        passed += v == "PASS"
        parts = " · ".join(f"{k} {r[k][1]:g}% {describe(r[k][0])}" for k in ("main", "second", "accent"))
        print(f"{'-' if t is None else t:>6} {parts} | {v}")
    print(f"{passed}/{len(times)} frames inside 60-30-10")
    return 0


if __name__ == "__main__":
    sys.exit(main())
