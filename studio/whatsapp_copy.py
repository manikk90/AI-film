#!/usr/bin/env python3
"""The WhatsApp copy: 720p (short side 720), H.264 + AAC, under a size cap (default 20 MB).

    python3 studio/whatsapp_copy.py final.mp4 final_whatsapp.mp4 [--max-mb 20] [--force]

The video bitrate comes from the duration and the cap, with a 6 % margin for the container; two-pass x264.
If the result is still over the cap, it retries at 85 % of the bitrate (up to 3 times). It never overwrites an
existing file without --force. Prints the final size. Needs FFmpeg and ffprobe.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

AUDIO_KBPS = 128


def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def is_portrait(path: str) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()
    w, h = map(int, out.split(",")[:2])
    return h > w


def encode(src: str, dst: str, kbps: int) -> None:
    scale = "scale=720:-2" if is_portrait(src) else "scale=-2:720"
    with tempfile.TemporaryDirectory() as tmp:
        log = os.path.join(tmp, "pass")
        common = ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", scale + ",format=yuv420p", "-c:v", "libx264",
                  "-preset", "medium", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.5)}k",
                  "-bufsize", f"{kbps * 2}k", "-passlogfile", log]
        subprocess.run(common + ["-pass", "1", "-an", "-f", "mp4", os.devnull], check=True)
        subprocess.run(common + ["-pass", "2", "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-movflags", "+faststart",
                                 dst], check=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--max-mb", type=float, default=20)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if os.path.exists(a.dst) and not a.force:
        sys.exit(f"{a.dst} exists; ask the owner, then pass --force")
    cap = a.max_mb * 1000 * 1000
    kbps = int(min(4000, (cap * 8 / 1000 * 0.94) / duration(a.src) - AUDIO_KBPS))
    if kbps < 150:
        sys.exit(f"too long for {a.max_mb} MB at 720p (would need {kbps} kbps); cut it or raise --max-mb")
    for _ in range(4):
        encode(a.src, a.dst, kbps)
        size = os.path.getsize(a.dst)
        if size <= cap:
            print(f"{a.dst}: {size / 1e6:.1f} MB at {kbps} kbps")
            return 0
        kbps = int(kbps * 0.85)
    sys.exit(f"{a.dst} is still {size / 1e6:.1f} MB; check the source")


if __name__ == "__main__":
    sys.exit(main())
