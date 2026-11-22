#!/usr/bin/env python3
"""Word timing with no model download: align a known script or lyrics to a recording, offline.

    <lemo-opuscar>/.venv/bin/python studio/word_timing.py voice.wav script.txt words.json \
        [--lang hi] [--voice hm_omega] [--kokoro <lemo-opuscar>/core/tts] [--js words.js] [--srt lines.srt]

How it works:
1. The offline Kokoro voice speaks every word of the text on its own, so each word's start and end in that reference is
   exact. The voice is male or female by the speaker's pitch, and its spectrum is warped to fit the speaker.
2. The reference and the recording are compared frame by frame (MFCC features every 10 ms; pauses longer than 100 ms
   shortened on both sides) and matched with dynamic time warping, with the speed difference kept between 0.5x and 2x.
   The first pass runs over the whole recording to find each line; the second runs line by line to place the words.
3. Each word's reference span maps onto the recording.

One line of the text file is one line on screen (a sentence, a lyric line); blank lines are ignored. Put a comma where
the speaker pauses inside a line: a long pause (over about 0.3 s) with no punctuation can shift a word.

It needs the words: a script, lyrics or the locked dialogue. It cannot transcribe unknown speech; that needs Whisper,
which is blocked in the cloud session (see `studio/check_env.py`). It needs numpy and FFmpeg, and for the reference
voice kokoro-onnx with the Kokoro model (the Lemo-Opuscar venv has both). Accuracy notes are in
studio/SKILL_HARNESS.md; synthetic-signal tests are in tests/test_word_timing.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

import numpy as np

SR = 24000
HOP = 0.010            # seconds per feature frame
WIN = 0.025
N_MELS, N_MFCC = 40, 13
LEAD, WORD_GAP, PUNCT_GAP, LINE_GAP = 0.30, 0.06, 0.25, 0.45   # silences in the reference, seconds
PUNCT_END = tuple(",;:.!?।॥")
SEARCH = 1.0           # seconds of recording searched around each line's coarse position
COARSE_MAX = 4000      # frames per side in the whole-recording pass (a 4000x4000 byte matrix)
SILENCE_KEEP = 15      # frames kept at each end of a silent run: pauses longer than 300 ms count as 300 ms
WARPS = (0.82, 0.88, 0.94, 1.0, 1.06, 1.12, 1.18)   # reference frequency warps tried (vocal tract length normalisation)
SILENCE_VECTOR = np.array([0.0] * (N_MFCC - 1) + [-4.0])   # every silent frame, after normalisation
SPEECH = re.compile(r"[^\s\.,!?;:\"'“”‘’()\[\]{}…।॥–—]+")


# ---------------------------------------------------------------- text and reference
def tokenize(text: str) -> list[list[tuple[str, str]]]:
    """Lines of (shown word, spoken word). Punctuation stays on the shown word and is dropped from the spoken one."""
    lines = []
    for raw in text.splitlines():
        words = []
        for tok in raw.split():
            spoken = " ".join(SPEECH.findall(tok))
            if spoken:
                words.append((tok, spoken))
            elif words:  # a lone punctuation mark joins the word before it
                words[-1] = (words[-1][0] + " " + tok, words[-1][1])
        if words:
            lines.append(words)
    if not lines:
        raise SystemExit("word_timing: the text has no words")
    return lines


def trim(x: np.ndarray, rel: float = 0.02) -> np.ndarray:
    nz = np.where(np.abs(x) > (np.abs(x).max() if len(x) else 0) * rel)[0]
    return x[nz[0]:nz[-1] + 1] if len(nz) else x


def build_reference(lines, synth: Callable[[str], np.ndarray]):
    """Speak every word on its own and join them: returns the audio, each word's (start, end) in samples, per line,
    and each line's (start, end)."""
    parts, spans, line_spans, cache = [np.zeros(int(LEAD * SR))], [], [], {}
    pos = len(parts[0])
    for li, line in enumerate(lines):
        if li:
            parts.append(np.zeros(int(LINE_GAP * SR)))
            pos += len(parts[-1])
        ws, start = [], pos
        for wi, (_, spoken) in enumerate(line):
            if wi:  # speakers pause at punctuation, so the reference does too
                parts.append(np.zeros(int((PUNCT_GAP if line[wi - 1][0].endswith(PUNCT_END) else WORD_GAP) * SR)))
                pos += len(parts[-1])
            if spoken not in cache:
                cache[spoken] = trim(np.asarray(synth(spoken), dtype=np.float64))
            a = cache[spoken]
            parts.append(a)
            ws.append((pos, pos + len(a)))
            pos += len(a)
        spans.append(ws)
        line_spans.append((start, pos))
    parts.append(np.zeros(int(LEAD * SR)))
    return np.concatenate(parts), spans, line_spans


# ---------------------------------------------------------------- features and DTW
def _mel_filterbank(n_fft: int, warp: float = 1.0) -> np.ndarray:
    hz2mel = lambda f: 2595 * np.log10(1 + f / 700)  # noqa: E731
    mel2hz = lambda m: 700 * (10 ** (m / 2595) - 1)  # noqa: E731
    hz = np.minimum(mel2hz(np.linspace(hz2mel(60.0), hz2mel(SR / 2), N_MELS + 2)) * warp, SR / 2)
    bins = np.floor((n_fft + 1) * hz / SR).astype(int)
    fb = np.zeros((N_MELS, n_fft // 2 + 1))
    for m in range(1, N_MELS + 1):
        lo, c, hi = bins[m - 1], bins[m], bins[m + 1]
        if c > lo:
            fb[m - 1, lo:c] = (np.arange(lo, c) - lo) / (c - lo)
        if hi > c:
            fb[m - 1, c:hi] = (hi - np.arange(c, hi)) / (hi - c)
    return fb


def raw_features(x: np.ndarray, warp: float = 1.0) -> np.ndarray:
    """MFCC 1-12 and the log energy (last column) for every 10 ms frame, not normalised."""
    win, hop = int(WIN * SR), int(HOP * SR)
    n_fft = 1 << (win - 1).bit_length()
    x = np.pad(x, (0, max(0, win - len(x))))
    n = 1 + (len(x) - win) // hop
    fb, w = _mel_filterbank(n_fft, warp), np.hamming(win)
    k = np.arange(N_MELS)
    dct = np.cos(np.pi / N_MELS * (k[None, :] + 0.5) * np.arange(N_MFCC)[:, None])
    out = np.empty((n, N_MFCC))
    for a in range(0, n, 4000):  # in blocks, so a long recording does not need gigabytes
        idx = np.arange(win)[None, :] + hop * np.arange(a, min(n, a + 4000))[:, None]
        frames = x[idx] * w
        mel = np.log(np.abs(np.fft.rfft(frames, n_fft)) ** 2 @ fb.T + 1e-10)
        out[a:a + len(idx), :N_MFCC - 1] = (mel @ dct.T)[:, 1:]
        out[a:a + len(idx), N_MFCC - 1] = np.log((frames ** 2).sum(1) + 1e-10)
    return out


def prepare(x: np.ndarray, keep: int = SILENCE_KEEP, warp: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Normalised features of the frames worth matching, their frame numbers, and which frames hold sound. Every frame within 30 dB of the
    loud frames counts as sound; a silent run keeps only `keep` frames at each end, so pauses of any length look
    alike in the reference and the recording."""
    f = raw_features(x, warp)
    loge = f[:, -1]
    sound = loge > np.percentile(loge, 95) - 6.9
    edges = np.flatnonzero(np.diff(np.concatenate(([1], sound.astype(np.int8), [1]))))
    kept = np.ones(len(f), bool)
    for a, b in zip(edges[::2], edges[1::2]):  # silent runs [a, b)
        if b - a > 2 * keep:
            kept[a + keep:b - keep] = False
    idx = np.flatnonzero(kept)
    ref = f[sound] if sound.any() else f
    out = (f[idx] - ref.mean(0)) / (ref.std(0) + 1e-8)
    # Silence looks the same on both sides: digital zero in the reference, room noise in a recording.
    out[~sound[idx]] = SILENCE_VECTOR
    return out, idx, sound


def _snap(sound: np.ndarray, f0: int, f1: int) -> tuple[int, int]:
    """Move a word's edges off silence: its start forward to the next sound, its end back to the last sound."""
    n = len(sound)
    while f0 < min(f1, n) - 1 and not sound[f0]:
        f0 += 1
    while f1 > f0 + 1 and f1 - 1 < n and not sound[f1 - 1]:
        f1 -= 1
    return f0, f1


def dtw_path(ref: np.ndarray, rec: np.ndarray) -> tuple[list[tuple[int, int]], float]:
    """Subsequence DTW with the slope kept between 1/2 and 2: steps (1,1), (1,2) and (2,1), each paying for every
    cell it crosses. Every reference frame is matched; the match may start and end anywhere in the recording.
    Returns the cells as (reference, recording) pairs and the mean cost per cell."""
    n, m = len(ref), len(rec)
    if m * 2 < n:
        raise ValueError("the recording window is less than half as long as the reference")
    rr = (rec * rec).sum(1)
    cols = np.arange(m)

    def row(i: int) -> np.ndarray:
        return np.sqrt(np.maximum(ref[i] @ ref[i] + rr - 2 * rec @ ref[i], 0))

    choice = np.zeros((n, m), np.int8)
    c_prev, d_prev, d_prev2 = None, np.full(m, np.inf), np.full(m, np.inf)
    for i in range(n):
        c = row(i)
        if i == 0:
            d = c.copy()  # free start
        else:
            opts = np.full((3, m), np.inf)
            opts[0, 1:] = d_prev[:-1]                       # (i-1, j-1)
            opts[1, 2:] = d_prev[:-2] + c[1:-1]             # (i-1, j-2) through (i, j-1)
            opts[2, 1:] = d_prev2[:-1] + c_prev[1:]         # (i-2, j-1) through (i-1, j)
            k = opts.argmin(0)
            choice[i] = k
            d = c + opts[k, cols]
        d_prev2, d_prev, c_prev = d_prev, d, c
    j = int(np.argmin(d_prev))
    if not np.isfinite(d_prev[j]):
        raise ValueError("no path within the slope limits")
    total, i = d_prev[j], n - 1
    cells = [(i, j)]
    while i > 0:
        k = choice[i, j]
        if k == 1:
            cells.append((i, j - 1))
            i, j = i - 1, j - 2
        elif k == 2:
            cells.append((i - 1, j))
            i, j = i - 2, j - 1
        else:
            i, j = i - 1, j - 1
        cells.append((i, j))
    cells.reverse()
    return cells, float(total / len(cells))


def _pool(f: np.ndarray, p: int) -> np.ndarray:
    n = -(-len(f) // p) * p
    f = np.concatenate([f, np.repeat(f[-1:], n - len(f), 0)]) if n > len(f) else f
    return f.reshape(-1, p, f.shape[1]).mean(1) if p > 1 else f


def _spans(cells) -> tuple[dict, dict]:
    first, last = {}, {}
    for i, j in cells:
        first.setdefault(i, j)
        last[i] = j
    return first, last


def align(rec_audio: np.ndarray, ref_audio: np.ndarray, spans, line_spans) -> dict:
    """Place every reference word on the recording: a coarse pass finds each line, a fine pass places its words.
    Times are seconds in the recording."""
    hop = int(HOP * SR)
    fa, ka, sound = prepare(rec_audio)
    best = None
    for warp in WARPS:  # the reference voice is not the speaker: stretch its spectrum to fit them best
        fr_w, kr_w, _ = prepare(ref_audio, warp=warp)
        p = max(1, -(-max(len(fr_w), len(fa)) // COARSE_MAX))
        cells_w, cost_w = dtw_path(_pool(fr_w, p), _pool(fa, p))
        if best is None or cost_w < best[0]:
            best = (cost_w, warp, fr_w, kr_w, p, cells_w)
    _, warp, fr, kr, p, cells = best
    first, last = _spans(cells)
    coarse = []  # each line's first and last reference frame, and where the coarse pass put its start and end
    for ls, le in line_spans:
        c0 = int(np.searchsorted(kr, ls // hop))
        c1 = max(c0, int(np.searchsorted(kr, le // hop, side="right")) - 1)
        a0 = int(ka[min(first[min(c0 // p, max(first))] * p, len(ka) - 1)])
        a1 = int(ka[min(last[min(c1 // p, max(last))] * p + p - 1, len(ka) - 1)])
        coarse.append((c0, c1, a0, a1))
    words, lines, prev_end = [], [], 0
    for li, ((ls, le), ws) in enumerate(zip(line_spans, spans)):
        c0, c1, a0, a1 = coarse[li]
        pad = int(SEARCH / HOP)
        # Lines run in order: search after the line before ended, and stop where the next line starts. The coarse
        # starts are the reliable estimates; a coarse end can slide across a pause into the next line.
        lo = max(a0 - pad, prev_end - int(0.2 / HOP))
        hi = a1 + pad
        if li + 1 < len(coarse):
            hi = min(hi, coarse[li + 1][2] + int(0.1 / HOP))
        hi = max(hi, lo + int(0.6 * (le - ls) / hop))
        asel = np.flatnonzero((ka >= lo) & (ka <= hi))
        rsel = np.flatnonzero((kr >= ls // hop - int(0.15 / HOP)) & (kr <= le // hop + int(0.15 / HOP)))
        try:
            cells, cost = dtw_path(fr[rsel], fa[asel])
            flagged = False
        except ValueError:  # the line could not be placed inside its window: keep the coarse guess, flag it
            cells, cost, flagged = None, float("inf"), True
        f2, l2 = _spans(cells) if cells else ({}, {})
        for (s, e) in ws:
            if cells:
                i0 = int(np.searchsorted(kr[rsel], s // hop))
                i1 = max(i0, int(np.searchsorted(kr[rsel], max(s // hop, e // hop - 1), side="right")) - 1)
                i0, i1 = min(i0, len(rsel) - 1), min(i1, len(rsel) - 1)
                f0, f1 = _snap(sound, int(ka[asel[f2[i0]]]), int(ka[asel[l2[i1]]]) + 1)
                t0, t1 = f0 * HOP, f1 * HOP
            else:
                frac0, frac1 = (s - ls) / max(1, le - ls), (e - ls) / max(1, le - ls)
                t0, t1 = (a0 + frac0 * (a1 - a0)) * HOP, (a0 + frac1 * (a1 - a0)) * HOP
            words.append({"s": round(t0, 3), "e": round(t1, 3), "line": li + 1})
        prev_end = max(prev_end, int(round(words[-1]["e"] / HOP)))
        lines.append({"line": li + 1, "cost": round(cost, 3) if np.isfinite(cost) else None, "flagged": flagged})
    return {"words": _order(words), "lines": lines, "warp": warp}


def _order(words: list[dict]) -> list[dict]:
    """Keep the words in order and give each a visible length."""
    for a, b in zip(words, words[1:]):
        b["s"] = round(max(b["s"], a["s"] + 0.02), 3)
        a["e"] = round(min(max(a["e"], a["s"] + 0.05), max(b["s"], a["s"] + 0.05)), 3)
    if words:
        words[-1]["e"] = round(max(words[-1]["e"], words[-1]["s"] + 0.05), 3)
    return words


def speaker_pitch(x: np.ndarray) -> float:
    """Median pitch in Hz of the voiced 40 ms frames (autocorrelation), or 0 when nothing is voiced. It picks the
    reference voice: the warp search fits voices of the same gender well, across genders less reliably."""
    win, hop, lo, hi = int(0.04 * SR), int(0.02 * SR), int(SR / 400), int(SR / 70)
    n = max(0, 1 + (len(x) - win) // hop)
    f0 = []
    for a in range(0, n, 2000):
        idx = np.arange(win)[None, :] + hop * np.arange(a, min(n, a + 2000))[:, None]
        fr = x[idx] - x[idx].mean(1, keepdims=True)
        e = (fr * fr).sum(1)
        ac = np.fft.irfft(np.abs(np.fft.rfft(fr, 2 * win)) ** 2)[:, :win]
        loud = e > np.percentile(e, 50) if len(e) else e > 0
        peak = ac[:, lo:hi].max(1) / (ac[:, 0] + 1e-12)
        lag = ac[:, lo:hi].argmax(1) + lo
        f0 += list(SR / lag[loud & (peak > 0.45)])
    return float(np.median(f0)) if f0 else 0.0


REFERENCE = {"hi": ("hm_omega", "hf_alpha"), "en-us": ("am_michael", "af_heart")}   # (male, female)


# ---------------------------------------------------------------- input, output, CLI
def decode(path: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le",
                        "-"], capture_output=True)
    if r.returncode or not r.stdout:
        raise SystemExit(f"word_timing: FFmpeg could not read {path}: {r.stderr.decode(errors='replace')[-300:]}")
    return np.frombuffer(r.stdout, dtype="<f4").astype(np.float64)


def kokoro_synth(model_dir: Path, voice: str, lang: str, speed: float) -> Callable[[str], np.ndarray]:
    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        raise SystemExit("word_timing: kokoro-onnx is missing; run this with the Lemo-Opuscar venv's Python") from None
    model, voices = model_dir / "kokoro-v1.0.onnx", model_dir / "voices-v1.0.bin"
    if not (model.exists() and voices.exists()):
        raise SystemExit(f"word_timing: no Kokoro model in {model_dir}; pass --kokoro <lemo-opuscar>/core/tts")
    k = Kokoro(str(model), str(voices))

    def synth(word: str) -> np.ndarray:
        audio, sr = k.create(word, voice=voice, speed=speed, lang=lang)
        audio = np.asarray(audio, dtype=np.float64)
        if sr != SR:
            audio = np.interp(np.arange(0, len(audio), sr / SR), np.arange(len(audio)), audio)
        return audio
    return synth


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def run(audio, text: str, synths: list[tuple[str, Callable[[str], np.ndarray]]], lang: str = "") -> dict:
    """Align with each reference voice, then keep, line by line, the voice whose reference matched best."""
    lines = tokenize(text)
    rec = decode(audio) if isinstance(audio, Path) else audio
    runs = []
    for voice, synth in synths:
        ref, spans, line_spans = build_reference(lines, synth)
        runs.append((voice, align(rec, ref, spans, line_spans)))
    words, picked = [], []
    for li in range(len(lines)):
        def line_cost(r):
            c = r[1]["lines"][li]["cost"]
            return float("inf") if c is None else c
        voice, best = min(runs, key=line_cost)
        words += [dict(w) for w in best["words"] if w["line"] == li + 1]
        picked.append(dict(best["lines"][li], voice=voice))
    res = {"words": _order(words), "lines": picked, "warp": [r["warp"] for _, r in runs]}
    voice = "+".join(v for v, _ in synths)
    flat = [w for line in lines for w in line]
    for w, (shown, _) in zip(res["words"], flat):
        w["w"] = shown
    costs = [ln["cost"] for ln in res["lines"] if ln["cost"] is not None]
    med = float(np.median(costs)) if costs else 0.0
    for ln, words in zip(res["lines"], lines):
        own = [w for w in res["words"] if w["line"] == ln["line"]]
        ln.update({"text": " ".join(s for s, _ in words), "s": own[0]["s"], "e": own[-1]["e"],
                   "check": bool(ln.pop("flagged") or ln["cost"] is None or ln["cost"] > 1.5 * med)})
    return {"audio": str(audio) if isinstance(audio, Path) else "<array>",
            "method": f"offline TTS reference (Kokoro {voice or '?'}, {lang or '?'}) + MFCC + subsequence DTW",
            # w/s/e (daksh-ai's format) and text/start/end (mms_align.py's, read by mouth_curve and canvas_kit)
            "words": [{"w": w["w"], "s": w["s"], "e": w["e"], "line": w["line"],
                       "text": w["w"], "start": w["s"], "end": w["e"]} for w in res["words"]],
            "lines": res["lines"], "warp": res["warp"],
            "note": "Lines marked check matched worse than the rest; look at them before trusting their word times."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Align a known script or lyrics to a recording, offline (word timing).")
    ap.add_argument("audio")
    ap.add_argument("text", help="a UTF-8 text file: one line per caption line")
    ap.add_argument("out", help="words.json to write")
    ap.add_argument("--lang", help="Kokoro language: hi for Hindi (the default for Devanagari text), en-us for English")
    ap.add_argument("--voice", default="auto",
                    help="Kokoro reference voice. Default auto: a male or female voice by the speaker's pitch "
                         "(hm_omega or hf_alpha for Hindi, am_michael or af_heart for English); its spectrum is then "
                         "warped to fit the speaker")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--kokoro", default=os.environ.get("KOKORO_DIR", ""),
                    help="the folder with kokoro-v1.0.onnx and voices-v1.0.bin (<lemo-opuscar>/core/tts)")
    ap.add_argument("--js", help="also write window.WORDS for daksh-ai's assets/words.js")
    ap.add_argument("--srt", help="also write one subtitle per text line")
    a = ap.parse_args(argv)
    text = Path(a.text).read_text(encoding="utf-8")
    lang = a.lang or ("hi" if re.search(r"[ऀ-ॿ]", text) else "en-us")
    rec = decode(Path(a.audio))
    pitch = speaker_pitch(rec)
    male, female = REFERENCE.get(lang, REFERENCE["en-us"])
    voices = [female if pitch >= 165 else male] if a.voice == "auto" else a.voice.split(",")
    model_dir = Path(a.kokoro) if a.kokoro else Path(__file__).resolve().parents[2] / "lemomo-ai/lemo-opuscar/core/tts"
    out = run(rec, text, [(v, kokoro_synth(model_dir, v, lang, a.speed)) for v in voices], lang)
    out.update({"audio": a.audio, "speaker_pitch_hz": round(pitch)})
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.js:
        Path(a.js).write_text("/* word timings from studio/word_timing.py */\nwindow.WORDS=" + json.dumps(
            [{k: w[k] for k in ("w", "s", "e")} for w in out["words"]], ensure_ascii=False) + ";\n", encoding="utf-8")
    if a.srt:
        Path(a.srt).write_text("".join(f"{i}\n{srt_time(ln['s'])} --> {srt_time(ln['e'])}\n{ln['text']}\n\n"
                                       for i, ln in enumerate(out["lines"], 1)), encoding="utf-8")
    flagged = [ln["line"] for ln in out["lines"] if ln["check"]]
    print(f"{len(out['words'])} words in {len(out['lines'])} lines -> {a.out}" +
          (f"; check line(s) {flagged}" if flagged else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
