#!/usr/bin/env python3
"""Flicker edit: the model shot and the empty shot swap every quarter beat, so she appears and vanishes.

    python3 flicker.py model.(jpg|mp4) empty.(jpg|mp4) song.mp3 out.mp4 \
        [--beats beats.json] [--face 0.5,0.4] [--dur 15] [--fps 30] [--stills 1,4,8] [--force]

- Both shots are cover-cropped to 1080×1920 the same way (same scale, same crop), so only the model changes.
- One warm sunset grade for both: a little contrast, warm tint, soft vignette, fine grain.
- Beats: --beats beats.json ({"tempo": .., "beats": [s, ...], "downbeats": [...], "strong": [...]}, e.g. from
  librosa), or a built-in spectral-flux fallback. Swap every quarter beat; open on one full beat of the model; the last
  beat to the end shows only the empty shot.
- Every model return: a 3% ease-out zoom over that quarter beat, on top of an 8% push-in over the whole edit, both
  anchored on her face (--face x,y in 0–1 of the 9:16 frame) so the face stays put.
- A very short soft white flash on strong beats.
- Frames are numpy arrays piped to FFmpeg (rawvideo → H.264, CRF 18, yuv420p), the song as AAC 192k.
- --stills t1,t2 writes out_<t>.png preview frames instead of the video. Refuses to overwrite without --force.
Needs numpy, Pillow and FFmpeg.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

W, H = 1080, 1920
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}


# ---------- audio and beats ----------
def load_audio(path: Path, sr: int = 22050) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def flux_beats(y: np.ndarray, sr: int = 22050) -> dict:
    """Fallback beat tracker: spectral flux onset envelope, autocorrelation tempo, best-phase grid."""
    hop, n = 512, 2048
    frames = 1 + max(0, (len(y) - n) // hop)
    if frames < 8:
        return {"tempo": 120.0, "beats": [], "downbeats": [], "strong": []}
    idx = np.arange(n)[None, :] + hop * np.arange(frames)[:, None]
    mag = np.abs(np.fft.rfft(y[idx] * np.hanning(n), axis=1))
    mag = np.log1p(mag)
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fps = sr / hop
    lags = np.arange(int(fps * 60 / 180), int(fps * 60 / 70) + 1)  # 70–180 BPM
    ac = np.array([np.dot(flux[:-l], flux[l:]) for l in lags])
    period = lags[int(np.argmax(ac))]
    phases = [flux[p::period].sum() for p in range(period)]
    start = int(np.argmax(phases))
    beat_frames = np.arange(start, len(flux), period)
    beats = (beat_frames / fps).tolist()
    strength = flux[beat_frames]
    thr = np.quantile(strength, 0.8) if len(strength) else 0
    strong = [b for b, s in zip(beats, strength) if s >= thr]
    return {"tempo": 60 * fps / period, "beats": beats, "downbeats": beats[::4], "strong": strong}


# ---------- pictures ----------
def cover_size(w: int, h: int) -> tuple[int, int, int, int]:
    """Scaled size and crop offsets that fill W×H without stretching (centre crop)."""
    s = max(W / w, H / h)
    nw, nh = round(w * s), round(h * s)
    return nw, nh, (nw - W) // 2, (nh - H) // 2


def probe(path: Path) -> tuple[int, int]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0:s=x", str(path)], capture_output=True, text=True, check=True).stdout
    w, h = out.strip().split("x")[:2]
    return int(w), int(h)


class Source:
    """A still image or a video, delivered as W×H uint8 RGB frames at the film's fps (videos loop)."""

    def __init__(self, path: Path, fps: int):
        self.video = path.suffix.lower() in VIDEO_EXTS
        if not self.video:
            img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
            nw, nh, ox, oy = cover_size(*img.size)
            self.still = np.asarray(img.resize((nw, nh), Image.LANCZOS).crop((ox, oy, ox + W, oy + H)))
            return
        nw, nh, ox, oy = cover_size(*probe(path))
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                              f"fps={fps},scale={nw}:{nh}:flags=lanczos,crop={W}:{H}:{ox}:{oy}",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        self.frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
        if not len(self.frames):
            raise SystemExit(f"{path}: no frames decoded")

    def at(self, i: int) -> np.ndarray:
        return self.still if not self.video else self.frames[i % len(self.frames)]


def grade_luts() -> list[np.ndarray]:
    x = np.arange(256) / 255.0
    con = np.clip(0.5 + (x - 0.5) * 1.08, 0, 1)
    gains = (1.06, 1.0, 0.90)
    lift = (0.02, 0.01, 0.0)
    return [np.clip((lift[c] + con * (1 - lift[c])) * gains[c] * 255, 0, 255).astype(np.uint8) for c in range(3)]


def vignette() -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
    return (1 - 0.35 * np.clip(d - 0.35, 0, 1) ** 1.5 / 0.65 ** 1.5)[..., None].astype(np.float32)


def zoom(frame: np.ndarray, scale: float, fx: float, fy: float) -> np.ndarray:
    """Zoom in by `scale` keeping the point (fx, fy) of the frame fixed."""
    if scale <= 1.0001:
        return frame
    cw, ch = W / scale, H / scale
    left, top = fx * W * (1 - 1 / scale), fy * H * (1 - 1 / scale)
    img = Image.fromarray(frame).resize((W, H), Image.BILINEAR, box=(left, top, left + cw, top + ch))
    return np.asarray(img)


# ---------- timeline ----------
def timeline(beats: list[float], dur: float):
    """Segments (start, end, is_model) on the quarter-beat grid."""
    beats = [b for b in beats if 0 <= b < dur]
    if len(beats) < 3:
        raise SystemExit("not enough beats in the song to cut on")
    period = float(np.median(np.diff(beats)))
    grid = []
    for a, b in zip(beats[:-1], beats[1:]):
        grid += [a + (b - a) * k / 4 for k in range(4)]
    grid.append(beats[-1])
    segs = [(0.0, beats[1], True)]           # open on one full beat of the model (from 0)
    model = False
    for a, b in zip(grid, grid[1:]):
        if a < beats[1]:
            continue
        if a >= beats[-1] - period * 0.01:
            break
        segs.append((a, b, model))
        model = not model
    segs.append((beats[-1], dur, False))      # end on the empty shot
    return segs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("model", type=Path)
    ap.add_argument("empty", type=Path)
    ap.add_argument("song", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--beats", type=Path)
    ap.add_argument("--face", default="0.5,0.4")
    ap.add_argument("--dur", type=float, help="seconds (default: the song length)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--stills")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    fx, fy = (float(v) for v in a.face.split(","))
    fps = a.fps

    y = load_audio(a.song)
    song_dur = len(y) / 22050
    dur = min(a.dur or song_dur, song_dur)
    bt = json.loads(a.beats.read_text()) if a.beats else flux_beats(y)
    strong = [s for s in bt.get("strong", []) if s < dur]
    segs = timeline(bt["beats"], dur)

    stills = [float(t) for t in a.stills.split(",")] if a.stills else None
    targets = ([a.out.with_name(f"{a.out.stem}_{t:g}.png") for t in stills] if stills else [a.out])
    clash = [str(t) for t in targets if t.exists()]
    if clash and not a.force:
        print("would overwrite " + ", ".join(clash) + "; ask the owner, then re-run with --force", file=sys.stderr)
        return 1

    model, empty = Source(a.model, fps), Source(a.empty, fps)
    luts, vig = grade_luts(), vignette()
    rng = np.random.default_rng(7)
    grains = [rng.normal(0, 5.0, (H, W, 1)).astype(np.float32) for _ in range(6)]

    def frame_at(t: float, i: int) -> np.ndarray:
        seg = next((s for s in segs if s[0] <= t < s[1]), segs[-1])
        is_model = seg[2]
        src = (model if is_model else empty).at(i)
        scale = 1 + 0.08 * (t / dur)
        if is_model:
            p = min(1.0, (t - seg[0]) / max(1e-6, seg[1] - seg[0]))
            scale *= 1 + 0.03 * (1 - (1 - p) ** 3)       # ease-out to her face
        f = zoom(src, scale, fx, fy)
        g = np.stack([luts[c][f[..., c]] for c in range(3)], axis=-1).astype(np.float32)
        g = g * vig + grains[i % len(grains)]
        flash = max((0.35 * max(0.0, 1 - (t - s) / 0.08) for s in strong if 0 <= t - s < 0.08), default=0.0)
        if flash:
            g = g + (255 - g) * flash
        return np.clip(g, 0, 255).astype(np.uint8)

    if stills:
        for t, target in zip(stills, targets):
            Image.fromarray(frame_at(t, int(t * fps))).save(target)
            print(target)
        return 0

    a.out.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(dur * fps))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-i", str(a.song), "-map", "0:v", "-map", "1:a", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(a.out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame_at(i / fps, i).tobytes())
    proc.stdin.close()
    if proc.wait():
        raise SystemExit("ffmpeg failed")
    swaps = sum(1 for s in segs if s[2])
    print(f"{a.out}  {n} frames, {dur:.2f} s, tempo {bt.get('tempo', 0):.1f}, {len(segs)} segments ({swaps} model)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
