#!/usr/bin/env python3
"""Forced alignment with torchaudio MMS_FA: the format skills' own word-timing step, for known words.

    python3 studio/mms_align.py voice.wav words.txt words.json [--js words.js] [--windows lines.json] [--max-word 1.2]

- words.txt: one screen line per row (a sentence, a lyric line, `SPEAKER|text`). Devanagari, Hinglish and English
  all work: every word is romanised with uroman for the aligner and the original spelling is kept for the screen.
  Ad-libs in (brackets) are aligned too and marked `adlib`.
- --windows: a JSON list of [start, end] seconds per line. Each line is then aligned only inside its own window
  (windowed alignment: for hooks, chants and party vocals, or a line that came out squeezed).
- --max-word caps a word's end that stretches over a pause (default 1.2 s, sung words get more with --max-word 3).
Output: {"words":[{"i","line","text","roman","start","end","score","speaker","adlib"}], "lines":[...]}.
It flags lines whose words average under 0.08 s (squeezed) as `check`: re-run them with --windows.

Needs torch + torchaudio (pip), uroman (pip install uroman) and the MMS_FA model from dl.fbaipublicfiles.com.
`python3 studio/check_env.py` says whether that host is open in this session; if not, use studio/word_timing.py
(offline) or a transcript the owner gives you. Never guess timings.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

SR = 16000


def romanise(words: list[str]) -> list[str]:
    try:
        import uroman as ur
        u = ur.Uroman()
        rom = [u.romanize_string(w) for w in words]
    except ImportError:
        if any(re.search(r"[^\x00-\x7f]", w) for w in words):
            sys.exit("uroman is missing for non-Latin text: pip install uroman")
        rom = words
    out = []
    for r in rom:
        r = re.sub(r"[^a-z']", "", r.lower().replace("’", "'"))
        out.append(r or "a")
    return out


def parse_lines(path: str) -> list[dict]:
    lines = []
    for raw in open(path, encoding="utf-8"):
        raw = raw.strip()
        if not raw:
            continue
        speaker = None
        if "|" in raw:
            speaker, raw = (x.strip() for x in raw.split("|", 1))
        toks = re.findall(r"\([^)]*\)|\S+", raw)
        words = []
        for t in toks:
            adlib = t.startswith("(")
            for w in (t.strip("()").split() if adlib else [t]):
                clean = w.strip(",.!?;:—-\"'“”‘’।॥")
                if clean:
                    words.append({"text": w.strip("()"), "clean": clean, "adlib": adlib})
        lines.append({"text": raw, "speaker": speaker, "words": words})
    return lines


def load(path: str):
    import torch
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    import numpy as np
    return torch.from_numpy(np.frombuffer(raw, dtype=np.float32).copy()).unsqueeze(0)


def align_span(model, tokenizer, aligner, wav, roman, offset):
    import torch
    with torch.inference_mode():
        emission, _ = model(wav)
        spans = aligner(emission[0], tokenizer(roman))
    ratio = wav.size(1) / emission.size(1) / SR
    out = []
    for s in spans:
        out.append((offset + s[0].start * ratio, offset + s[-1].end * ratio,
                    float(sum(t.score * len(t) for t in s) / sum(len(t) for t in s))))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audio")
    ap.add_argument("text")
    ap.add_argument("out")
    ap.add_argument("--js")
    ap.add_argument("--windows")
    ap.add_argument("--max-word", type=float, default=1.2)
    a = ap.parse_args(argv)
    try:
        import torch  # noqa: F401
        import torchaudio
    except ImportError:
        sys.exit("torch/torchaudio missing: pip install torch torchaudio (or use studio/word_timing.py)")
    bundle = torchaudio.pipelines.MMS_FA
    model = bundle.get_model(with_star=False)
    tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
    wav = load(a.audio)
    lines = parse_lines(a.text)
    for ln in lines:
        ln["roman"] = romanise([w["clean"] for w in ln["words"]])
    timed: list[tuple] = []
    if a.windows:
        wins = json.load(open(a.windows))
        if len(wins) != len(lines):
            sys.exit(f"--windows has {len(wins)} spans for {len(lines)} lines")
        for ln, (s, e) in zip(lines, wins):
            seg = wav[:, int(s * SR): int(e * SR)]
            timed += align_span(model, tokenizer, aligner, seg, ln["roman"], s)
    else:
        timed = align_span(model, tokenizer, aligner, wav, [r for ln in lines for r in ln["roman"]], 0.0)
    words, out_lines, k = [], [], 0
    for li, ln in enumerate(lines):
        first = k
        for w, r in zip(ln["words"], ln["roman"]):
            s, e, sc = timed[k]
            e = min(e, s + a.max_word)
            words.append({"i": k, "line": li, "text": w["text"], "roman": r, "start": round(s, 3), "end": round(e, 3),
                          "score": round(sc, 3), "speaker": ln["speaker"], "adlib": w["adlib"]})
            k += 1
        ws = words[first:k]
        avg = sum(w["end"] - w["start"] for w in ws) / max(len(ws), 1)
        out_lines.append({"line": li, "text": ln["text"], "speaker": ln["speaker"], "start": ws[0]["start"] if ws else None,
                          "end": ws[-1]["end"] if ws else None, "check": avg < 0.08})
    data = {"source": a.audio, "method": "torchaudio MMS_FA" + (" (windowed)" if a.windows else ""),
            "words": words, "lines": out_lines}
    json.dump(data, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.js:
        open(a.js, "w", encoding="utf-8").write("window.WORDS=" + json.dumps(data, ensure_ascii=False) + ";\n")
    flagged = [l["line"] for l in out_lines if l["check"]]
    print(f"{a.out}: {len(words)} words, {len(out_lines)} lines" + (f"; check lines {flagged}" if flagged else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
