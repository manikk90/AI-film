#!/usr/bin/env python3
"""Beat grid, kicks and music hits for the format skills (librosa).

    python3 studio/beats.py song.mp3 beats.json [--fps 30] [--tempo-hint 96]

Writes JSON:
  tempo       BPM from librosa's beat tracker (check it by ear; trackers can be off by a few BPM or by 2x)
  beats       beat times, seconds
  downbeats   every 4th beat starting at the strongest phase (a 4/4 guess; check it against the bars)
  kicks       low-band (20-150 Hz) onsets: the camera punches/shakes on these
  hits        strong full-band onsets: cuts, flashes and bursts land on these
  strong      beats whose onset strength is in the top quarter
  frames      the same lists as frame numbers at --fps
Needs librosa (pip install librosa) and FFmpeg for MP3 decoding. Use the drum/instrumental stem when the vocals are loud.
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np


def onset_times(y, sr, fmin=None, fmax=None, rel=0.4, min_gap=0.12):
    import librosa
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    band = np.ones_like(freqs, dtype=bool)
    if fmin is not None:
        band &= freqs >= fmin
    if fmax is not None:
        band &= freqs <= fmax
    env = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S[band] ** 2 + 1e-10), sr=sr, hop_length=512)
    peaks = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=512, units="frames")
    if len(peaks) == 0:
        return [], env
    thr = rel * float(env[peaks].max())  # relative to the loudest onset, so an even grid keeps every hit
    out, last = [], -1e9
    for p in peaks:
        t = float(librosa.frames_to_time(p, sr=sr, hop_length=512))
        if env[p] >= thr and t - last >= min_gap:
            out.append(round(t, 3))
            last = t
    return out, env


def analyse(path: str, tempo_hint: float | None = None) -> dict:
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    kw = {"start_bpm": tempo_hint} if tempo_hint else {}
    tempo, bf = librosa.beat.beat_track(onset_envelope=env, sr=sr, hop_length=512, **kw)
    tempo = float(np.atleast_1d(tempo)[0])
    beats = [round(float(t), 3) for t in librosa.frames_to_time(bf, sr=sr, hop_length=512)]
    strength = env[bf] if len(bf) else np.array([])
    phase = int(np.argmax([strength[i::4].mean() if len(strength[i::4]) else 0 for i in range(4)])) if len(bf) >= 4 else 0
    downbeats = beats[phase::4]
    strong = [b for b, s in zip(beats, strength) if len(strength) and s >= np.percentile(strength, 75)]
    kicks, _ = onset_times(y, sr, 20, 150, rel=0.35)
    hits, _ = onset_times(y, sr, None, None, rel=0.6)
    return {"source": path, "duration": round(len(y) / sr, 3), "tempo": round(tempo, 2), "beats": beats,
            "downbeats": downbeats, "kicks": kicks, "hits": hits, "strong": strong}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--tempo-hint", type=float)
    a = ap.parse_args(argv)
    try:
        import librosa  # noqa: F401
    except ImportError:
        sys.exit("librosa is missing: pip install librosa")
    d = analyse(a.audio, a.tempo_hint)
    d["fps"] = a.fps
    d["frames"] = {k: [round(t * a.fps) for t in d[k]] for k in ("beats", "downbeats", "kicks", "hits", "strong")}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    print(f"{a.out}: {d['tempo']} BPM, {len(d['beats'])} beats, {len(d['kicks'])} kicks, {len(d['hits'])} hits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
