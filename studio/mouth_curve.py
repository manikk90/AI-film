#!/usr/bin/env python3
"""Mouth-open curve from voice loudness, one value per video frame, for lip-sync on canvas characters.

    python3 studio/mouth_curve.py voice.wav mouth.json [--fps 30] [--js mouth.js] [--words words.json]

0 = closed, 1 = wide open. RMS in a 40 ms window at every frame, in dB, gated at the noise floor, normalised to the
loud speech level (95th percentile), lightly smoothed (fast open, slower close). With --words (word_timing.py or
mms_align.py output) the mouth is forced shut outside spoken words, so breaths and music bleed do not move it.
For two speakers, run it once per speaker's stem or per speaker's lines. Needs numpy and FFmpeg.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np

SR = 16000


def load(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def curve(y: np.ndarray, fps: float, spans=None) -> list[float]:
    n = int(np.ceil(len(y) / SR * fps))
    win = int(0.04 * SR)
    db = np.empty(n)
    for i in range(n):
        c = int(i / fps * SR)
        seg = y[max(0, c - win // 2): c + win // 2]
        db[i] = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-6) if len(seg) else -120
    floor, top = np.percentile(db, 20) + 6, np.percentile(db, 95)
    v = np.clip((db - floor) / max(top - floor, 1e-3), 0, 1)
    if spans:
        mask = np.zeros(n, dtype=bool)
        for s, e in spans:
            mask[int(s * fps): int(np.ceil(e * fps)) + 1] = True
        v[~mask] = 0
    out, prev = np.empty(n), 0.0
    for i, x in enumerate(v):  # attack fast, release slower
        prev = prev + (x - prev) * (0.75 if x > prev else 0.35)
        out[i] = prev
    return [round(float(x), 3) for x in out]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--js", help="also write `window.MOUTH = {...}` for a canvas page")
    ap.add_argument("--words", help="word timings JSON; keep the mouth shut outside the words")
    a = ap.parse_args(argv)
    spans = None
    if a.words:
        d = json.load(open(a.words, encoding="utf-8"))
        ws = d.get("words", d) if isinstance(d, dict) else d
        spans = [(w["start"], w["end"]) for w in ws]
    vals = curve(load(a.audio), a.fps, spans)
    data = {"fps": a.fps, "values": vals}
    json.dump(data, open(a.out, "w"), separators=(",", ":"))
    if a.js:
        open(a.js, "w").write("window.MOUTH=" + json.dumps(data, separators=(",", ":")) + ";\n")
    print(f"{a.out}: {len(vals)} frames, mean open {np.mean(vals):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
