#!/usr/bin/env python3
"""The size a video is SHOWN at, for tools that scale or reshape its frames.

Phones store portrait video as landscape pixels plus a rotation tag (side data "rotation", or the older "rotate"
tag). FFmpeg applies that rotation when it decodes, so a tool that reads the stored width and height and then
reshapes or scales the decoded frames gets them sideways or squashed. Always size frames with displayed_size().

    python3 studio/media_probe.py clip.mp4      # prints "W H rotation"
"""
from __future__ import annotations

import json
import subprocess
import sys


def rotation(stream: dict) -> int:
    """The stream's rotation in degrees (0, 90, 180, 270), from side data or the legacy tag."""
    for sd in stream.get("side_data_list") or []:
        if "rotation" in sd:
            return int(round(float(sd["rotation"]))) % 360
    tag = (stream.get("tags") or {}).get("rotate")
    return int(tag) % 360 if tag not in (None, "") else 0


def displayed_size(path: str) -> tuple[int, int, int]:
    """(width, height, rotation) of the first video stream as it will be decoded, i.e. after the rotation."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation:stream_tags=rotate", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    w, h, rot = int(s["width"]), int(s["height"]), rotation(s)
    return (h, w, rot) if rot in (90, 270) else (w, h, rot)


if __name__ == "__main__":
    w, h, r = displayed_size(sys.argv[1])
    print(w, h, r)
