#!/usr/bin/env python3
"""Sound effects for the format skills, from two sources:
  - code:    11 sounds synthesised here (whoosh, swoosh_up, ding, bell, pop, boom, impact, shutter, typing, damru, riser),
             the same on every run, nothing to download
  - earshot: real-sounding effects rendered by earshot (github.com/Leonxlnx/earshot, MIT; every sound it renders is free
             to use, commercial too; its learned sounds come from public-domain recordings). Asked for in words
             ("footstep on gravel", "a fast whoosh for a cut") or by a catalogue id ("whoosh/fast").

    python3 studio/sfx.py list
    python3 studio/sfx.py make whoosh out/whoosh.wav [--seed 3] [--len 0.6] [--gain -6]
    python3 studio/sfx.py want "footstep on gravel" out/step.wav [--seed 2] [--allow-guess]   # earshot
    python3 studio/sfx.py all out/sfx/                         # one WAV per code sound, for a project's sfx/ folder
    python3 studio/sfx.py place cues.json bed.wav [--dur 30] [--engine auto|code|earshot] [--report bed.json]

cues.json: [{"t": 1.20, "sfx": "whoosh", "gain": -6}, {"t": 2.05, "want": "footstep on gravel", "sfx": "impact"},
            {"t": 3.1, "sound": "whoosh/deep"}]   (t in seconds; gain in dB)
  sfx    a code sound (also the fallback when earshot cannot make a cue)
  want   words for earshot          sound  an exact earshot catalogue id (`earshot sounds`)
  file   a recording fetched with studio/openverse_audio.py (CC0/PD; credited in that folder's CREDITS.md),
         trimmed to `len` seconds from `from` (default 0) when given
--engine auto (default): earshot for cues with want/sound when it is installed, code otherwise. code: never earshot.
earshot: require it. A request earshot only half understood (it answers with its nearest guess, e.g. a bicycle bell
for "temple bell") is refused unless the cue says "allow_guess": true; the cue then falls back to its code `sfx`, or
fails if it has none. --report writes where every cue's sound came from: put it in the film's CREDITS / 06-qc.md.
Cue times come from the alignment (a word's start) or beats.json (a kick), never guessed.
The bed is 48 kHz stereo 16-bit WAV, peaks kept under -1 dBFS; mix it under the voice with FFmpeg's amix.
Needs numpy, and FFmpeg to read earshot's files. Sounds are dry; reverb or EQ, if wanted, belongs in the final mix.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 48000


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _env(n, attack=0.005, release=0.2, curve=4.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.exp(-curve * t / max(release, 1e-4))
    return a * r


def _noise(n, rng):
    return rng.standard_normal(n)


def _onepole_lp(x, cutoff):
    """Lowpass with a per-sample cutoff (Hz): array or scalar."""
    cut = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x)
    prev = 0.0
    for i in range(len(x)):
        prev = (1 - a[i]) * x[i] + a[i] * prev
        y[i] = prev
    return y


def whoosh(rng, length=0.55):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    shape = np.sin(np.pi * t) ** 1.6
    cutoff = 300 + 5200 * np.sin(np.pi * t) ** 2
    x = _onepole_lp(_noise(n, rng), cutoff) - _onepole_lp(_noise(n, rng), 120)
    pan = np.linspace(-0.7, 0.7, n)
    return x * shape, pan


def swoosh_up(rng, length=0.8):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    cutoff = 200 + 7000 * t ** 2
    rise = t ** 1.5
    tail = np.clip((1 - t) / 0.12, 0, 1) ** 0.7  # fall away over the last 12 % instead of stopping at the peak
    x = _onepole_lp(_noise(n, rng), cutoff) * rise * tail
    return x, None


def ding(rng, length=1.2, f=1760.0):
    t = _t(length)
    tone = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in [(1, 1), (2.76, 0.35), (5.4, 0.12)])
    return tone * _env(len(t), 0.002, 0.35, 3.0), None


def bell(rng, length=2.5, f=523.25):
    t = _t(length)
    partials = [(0.5, 0.6), (1, 1), (1.19, 0.5), (1.56, 0.35), (2.0, 0.3), (2.74, 0.2), (3.0, 0.15)]
    tone = sum(a * np.sin(2 * np.pi * f * m * t + rng.uniform(0, 6)) * np.exp(-t * (1.2 + m)) for m, a in partials)
    return tone * _env(len(t), 0.003, 3.0, 1.0), None


def pop(rng, length=0.18):
    t = _t(length)
    f = 900 * np.exp(-t * 30) + 180
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * _env(len(t), 0.001, 0.05, 5), None


def boom(rng, length=1.6):
    t = _t(length)
    f = 55 + 90 * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * _env(len(t), 0.004, 0.9, 3)
    crack = _onepole_lp(_noise(len(t), rng), 2500) * _env(len(t), 0.001, 0.08, 6) * 0.6
    return np.tanh(1.6 * (body + crack)), None


def impact(rng, length=0.7):
    t = _t(length)
    f = 70 + 160 * np.exp(-t * 25)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.001, 0.25, 4)
    hit = _noise(len(t), rng) * _env(len(t), 0.0005, 0.03, 6) * 0.8
    return np.tanh(2.0 * (body + hit)), None


def shutter(rng, length=0.35):
    n = int(length * SR)
    x = np.zeros(n)
    for start, g in [(0.0, 1.0), (0.09, 0.7)]:
        s = int(start * SR)
        m = min(int(0.05 * SR), n - s)  # a short --len cuts the pulse instead of overflowing the buffer
        if m <= 0:
            continue
        click = _onepole_lp(_noise(m, rng), 6000) * _env(m, 0.0005, 0.012, 5)
        x[s:s + m] += g * click
    return x, None


def typing(rng, length=1.2, rate=11.0):
    n = int(length * SR)
    x = np.zeros(n)
    t = 0.0
    while t < length - 0.05:
        s = int(t * SR)
        m = int(0.03 * SR)
        x[s:s + m] += (0.6 + 0.4 * rng.random()) * _onepole_lp(_noise(m, rng), 3500 + 2000 * rng.random()) * _env(m, 0.0003, 0.008, 5)
        t += (1 / rate) * (0.6 + 0.8 * rng.random())
    return x, None


def damru(rng, length=0.9, strokes=4):
    n = int(length * SR)
    x = np.zeros(n)
    for k in range(strokes):
        s = int(k * length / strokes * SR)
        m = n - s
        tt = np.arange(m) / SR
        f = 210 * (1 + 0.6 * np.exp(-tt * 40)) * (1.0 if k % 2 == 0 else 1.18)
        head = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(m, 0.001, 0.12, 4)
        slap = _onepole_lp(_noise(m, rng), 1800) * _env(m, 0.0005, 0.02, 6) * 0.5
        x[s:] += (head + slap) * (0.85 if k % 2 else 1.0)
    return np.tanh(1.3 * x), None


def riser(rng, length=2.0):
    t = _t(length)
    u = t / length
    f = 200 * (2 ** (3 * u))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    air = _onepole_lp(_noise(len(t), rng), 400 + 8000 * u ** 2) * 0.6
    return (tone + air) * u ** 2, None


SOUNDS = {
    "whoosh": (whoosh, "cut / transition air, pans left to right"),
    "swoosh_up": (swoosh_up, "rising air into a reveal"),
    "ding": (ding, "a number or tick lands"),
    "bell": (bell, "temple bell for aarti and devotional hits"),
    "pop": (pop, "a word, sticker or bubble pops in"),
    "boom": (boom, "big title, BREAKING sting, drop"),
    "impact": (impact, "punch, slam, burst word"),
    "shutter": (shutter, "camera flash, photo card drop"),
    "typing": (typing, "a chat or comment being typed"),
    "damru": (damru, "damru roll for Shiv aarti beats"),
    "riser": (riser, "build before a reveal or the drop"),
}


def make(name: str, seed: int = 1, length: float | None = None, gain_db: float = -3.0) -> np.ndarray:
    """Return a stereo float array (n, 2) of the sound, peak at gain_db."""
    if name not in SOUNDS:
        raise SystemExit(f"unknown sound {name!r}; try: {', '.join(SOUNDS)}")
    fn = SOUNDS[name][0]
    rng = np.random.default_rng(seed)
    x, pan = fn(rng, length) if length else fn(rng)
    x = np.asarray(x, dtype=float)
    fade = min(len(x), int(0.012 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * 10 ** (gain_db / 20)
    if pan is None:
        return np.stack([x, x], axis=1)
    left, right = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    return np.stack([x * left * 1.41, x * right * 1.41], axis=1)


def write(path: str | Path, stereo: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = np.max(np.abs(stereo)) if stereo.size else 0
    if peak > 0.891:  # keep peaks under -1 dBFS
        stereo = stereo * (0.891 / peak)
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


class EarshotMiss(Exception):
    """earshot is missing, failed, or only guessed at the request."""


def earshot_available() -> bool:
    return shutil.which("earshot") is not None


def _read_any(path: str) -> np.ndarray:
    """Any audio file as float stereo (n, 2) at SR, through FFmpeg."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)


def earshot(want: str | None = None, sound: str | None = None, seed: int = 0, allow_guess: bool = False,
            gain_db: float = -3.0, dur: float | None = None) -> tuple[np.ndarray, dict]:
    """Render one take with earshot. Returns (stereo float (n, 2) peaked at gain_db, info)."""
    if not earshot_available():
        raise EarshotMiss("earshot is not installed (bash studio/setup_env.sh)")
    if not (want or sound):
        raise EarshotMiss("an earshot cue needs `want` (words) or `sound` (a catalogue id)")
    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "take.wav")
        cmd = ["earshot", "make", "-o", out, "--json", "--seed", str(seed)]
        if dur:
            cmd += ["--dur", f"{float(dur):g}"]
        if sound:
            cmd += ["--sound", sound]
        if want:
            cmd.append(want)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            raise EarshotMiss("earshot took over 300 s and was stopped")
        try:
            info = json.loads(r.stdout)
        except json.JSONDecodeError:
            raise EarshotMiss(f"earshot failed: {(r.stderr or r.stdout).strip()[:300]}")
        if r.returncode or not Path(out).exists():
            raise EarshotMiss(f"earshot failed: {info.get('summary', '')[:300]}")
        missing = list(info.get("unknown") or []) + list(info.get("not_in_sound") or [])
        if missing and not sound and not allow_guess:
            raise EarshotMiss(f"earshot did not understand or cannot make {', '.join(missing)} in {want!r}; its nearest "
                              f"guess was {info.get('sound')} (pass allow_guess, name a catalogue id, or use a code sfx)")
        x = _read_any(out)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * 10 ** (gain_db / 20)
    fade = min(len(x), int(0.012 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)[:, None]
    take = (info.get("takes") or [{}])[0]
    return x, {"source": "earshot", "id": info.get("sound"), "want": want, "seed": seed,
               "guess": bool(info.get("unknown") or info.get("not_in_sound")), "dur_s": take.get("dur_s")}


def render_cue(c: dict, i: int = 0, engine: str = "auto") -> tuple[np.ndarray, dict]:
    """One cue as (stereo float, provenance). See the module doc for the cue fields and engines."""
    seed, gain = int(c.get("seed", i + 1)), float(c.get("gain", -6))
    if c.get("file"):
        x = _read_any(c["file"])
        start = int(float(c.get("from", 0)) * SR)
        x = x[start:start + int(float(c["len"]) * SR)] if c.get("len") else x[start:]
        if not len(x):
            raise SystemExit(f"cue {i}: {c['file']} has no audio after {c.get('from', 0)} s")
        x = x / (np.max(np.abs(x)) or 1.0) * 10 ** (gain / 20)
        fade = min(len(x), int(0.02 * SR))
        x[-fade:] *= np.linspace(1, 0, fade)[:, None]
        return x, {"source": "file", "id": Path(c["file"]).name, "want": c.get("want"), "seed": None}
    wants_earshot = bool(c.get("want") or c.get("sound"))
    why = None
    if wants_earshot and engine != "code" and (engine == "earshot" or earshot_available()):
        try:
            x, info = earshot(c.get("want"), c.get("sound"), seed, bool(c.get("allow_guess")), gain, c.get("len"))
            if c.get("len") and len(x) > int(float(c["len"]) * SR):  # earshot honours --dur only for some sounds
                x = x[:int(float(c["len"]) * SR)].copy()
                fade = min(len(x), int(0.02 * SR))
                x[-fade:] *= np.linspace(1, 0, fade)[:, None]
            return x, info
        except EarshotMiss as e:
            why = str(e)
            if engine == "earshot":  # earshot was required: never fall back silently
                raise SystemExit(f"cue {i} at {c.get('t')} s: {e}")
    if not c.get("sfx"):
        raise SystemExit(f"cue {i} at {c.get('t')} s has no code `sfx` to fall back to"
                         + (f": {why}" if why else " (earshot not used)"))
    x = make(c["sfx"], seed, c.get("len"), gain)
    return x, {"source": "code", "id": c["sfx"], "want": c.get("want"), "seed": seed, "fallback_reason": why}


def place(cues: list[dict], dur: float | None = None, engine: str = "auto", report: list | None = None) -> np.ndarray:
    """Mix cues [{t, sfx?, want?, sound?, gain?, seed?, len?, allow_guess?}] onto one stereo bed. When a list is
    given as `report`, one provenance row per cue is appended to it."""
    rendered = []
    for i, c in enumerate(cues):
        x, info = render_cue(c, i, engine)
        rendered.append((float(c["t"]), x))
        if report is not None:
            report.append({"t": float(c["t"]), **info})
    end = max([max(0.0, t + len(x) / SR) for t, x in rendered] + [dur or 0])
    bed = np.zeros((int(np.ceil(end * SR)) + 1, 2))
    for t, x in rendered:
        s = int(round(t * SR))
        if s < 0:  # a lead-in cue that starts before 0:00 (a whoosh into the first cut): keep only its tail
            x, s = x[-s:], 0
            if not len(x):
                continue
        bed[s:s + len(x)] += x
    if dur:
        bed = bed[:int(dur * SR)]
    return bed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    m = sub.add_parser("make")
    m.add_argument("name")
    m.add_argument("out")
    m.add_argument("--seed", type=int, default=1)
    m.add_argument("--len", type=float)
    m.add_argument("--gain", type=float, default=-3.0)
    w = sub.add_parser("want")
    w.add_argument("words", nargs="?", default="", help="the request in words (optional with --sound)")
    w.add_argument("out")
    w.add_argument("--seed", type=int, default=0)
    w.add_argument("--sound", help="an earshot catalogue id instead of words")
    w.add_argument("--allow-guess", action="store_true")
    w.add_argument("--gain", type=float, default=-3.0)
    w.add_argument("--len", type=float, help="length in seconds (earshot --dur)")
    al = sub.add_parser("all")
    al.add_argument("outdir")
    p = sub.add_parser("place")
    p.add_argument("cues")
    p.add_argument("out")
    p.add_argument("--dur", type=float)
    p.add_argument("--engine", choices=["auto", "code", "earshot"], default="auto")
    p.add_argument("--report", help="write where each cue's sound came from (JSON)")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for k, (_, what) in SOUNDS.items():
            print(f"{k:10s} {what}")
    elif a.cmd == "make":
        write(a.out, make(a.name, a.seed, a.len, a.gain))
        print(a.out)
    elif a.cmd == "want":
        try:
            if not (a.words or a.sound):
                raise SystemExit("want needs words or --sound <catalogue id>")
            x, info = earshot(a.words or None, a.sound, a.seed, a.allow_guess, a.gain, a.len)
        except EarshotMiss as e:
            raise SystemExit(str(e))
        write(a.out, x)
        print(f"{a.out}: earshot {info['id']}" + (" (a guess)" if info["guess"] else ""))
    elif a.cmd == "all":
        for k in SOUNDS:
            write(Path(a.outdir) / f"{k}.wav", make(k))
        print(f"{a.outdir}: {len(SOUNDS)} sounds")
    else:
        cues = json.load(open(a.cues, encoding="utf-8"))
        rows: list = []
        write(a.out, place(cues, a.dur, a.engine, rows))
        if a.report:
            Path(a.report).write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        count = {k: sum(r["source"] == k for r in rows) for k in ("earshot", "file", "code")}
        print(f"{a.out}: {len(cues)} cues (" + ", ".join(f"{v} {k}" for k, v in count.items()) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
