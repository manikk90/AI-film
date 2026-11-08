#!/usr/bin/env python3
"""60-30-10 colour check (studio/COLOR.md): how much of a frame each colour role takes.

  python3 studio/palette.py IMAGE_OR_VIDEO [--at 1,18.5,27.5] [--every 2] [--declared MAIN,SECOND,ACCENT]

Each frame is scaled to 72 px wide and split into 6 colour groups (k-means). The largest group and the groups
close to it are the main colour; loud groups (saturated and bright, well above the main) are the accent; the
rest is the second colour. Target: main 50-70 %, second 20-40 %, accent 3-15 %.
Without --declared the roles are inferred from group size, so a frame where the second colour took over the
world still reads as a clean split. With --declared (the brief's three hex values) every pixel goes to the
nearest declared colour, and pixels near none of them (skin, stray colours) count as "other".
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


def hexrgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def declared(pixels, main, second, accent, far=90):
    """Roles measured against the brief's own colours: {'main'|'second'|'accent'|'other': (rgb, share %, loudness)}.

    Each pixel joins the nearest declared colour; a pixel farther than `far` from all three counts as other."""
    named = {"main": main, "second": second, "accent": accent}
    counts = dict.fromkeys(list(named) + ["other"], 0)
    for p in pixels:
        name, d = min(((k, sum((a - b) ** 2 for a, b in zip(p, c)) ** 0.5) for k, c in named.items()),
                      key=lambda x: x[1])
        counts[name if d <= far else "other"] += 1
    n = len(pixels)
    out = {k: (c, round(counts[k] / n * 100, 1), round(loud(c), 2)) for k, c in named.items()}
    out["other"] = ((0, 0, 0), round(counts["other"] / n * 100, 1), 0.0)
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
        return None
    return [tuple(raw[i:i + 3]) for i in range(0, len(raw) - 2, 3)]


def duration(path):
    """The video stream's duration, else the container's (0.0 when neither is known)."""
    for entry in (["-select_streams", "v:0", "-show_entries", "stream=duration"], ["-show_entries", "format=duration"]):
        out = subprocess.run(["ffprobe", "-v", "error", *entry, "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.strip().splitlines()
        try:
            return float(out[0])
        except (IndexError, ValueError):
            continue
    return 0.0


def sample_times(d, every):
    """Every `every` seconds from 0, strictly before the end: a seek to the duration itself is EOF."""
    times, i = [], 0
    while i * every < d:
        times.append(round(i * every, 2))
        i += 1
    return times


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--at", help="comma-separated seconds")
    ap.add_argument("--every", type=float, help="sample every N seconds of a video")
    ap.add_argument("--declared", help="the brief's colours as MAIN,SECOND,ACCENT hex, e.g. f0e4cd,6e2832,e1281e")
    a = ap.parse_args(argv)
    if a.at:
        times = [float(x) for x in a.at.split(",")]
    elif a.every:
        d = duration(a.file)
        times = sample_times(d, a.every) or [None]
    else:
        times = [None]
    colours = [hexrgb(h) for h in a.declared.split(",")] if a.declared else None
    if colours and len(colours) != 3:
        ap.error("--declared takes exactly 3 hex colours: MAIN,SECOND,ACCENT")
    passed = checked = 0
    for t in times:
        px = frame_pixels(a.file, t)
        if px is None:
            print(f"{'-' if t is None else t:>6} no frame (skipped)")
            continue
        r = declared(px, *colours) if colours else roles(px)
        v = verdict(r)
        checked += 1
        passed += v == "PASS"
        parts = " · ".join(f"{k} {r[k][1]:g}% {describe(r[k][0])}" for k in ("main", "second", "accent"))
        if colours:
            parts += f" · other {r['other'][1]:g}%"
        print(f"{'-' if t is None else t:>6} {parts} | {v}")
    print(f"{passed}/{checked} frames inside 60-30-10" + (" (declared colours)" if colours else " (inferred roles)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
