#!/usr/bin/env python3
"""Split a song or a noisy recording into vocals + instrumental with demucs (htdemucs, two stems).

    python3 studio/separate_vocals.py song.mp3 stems/ [--model htdemucs]

Writes stems/vocals.wav and stems/no_vocals.wav (44.1 kHz). Align the lyrics on vocals.wav, find beats on the original
or no_vocals.wav, and keep the ORIGINAL mix as the film's audio. no_vocals.wav is also the bed for muting a word
(swap only the voice, so the beat keeps playing).
Needs demucs (pip install demucs, which pulls torch) and its weights from dl.fbaipublicfiles.com; check_env.py says
whether that host is open. If not, align on the full mix and say so in 06-qc.md.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audio")
    ap.add_argument("outdir")
    ap.add_argument("--model", default="htdemucs")
    a = ap.parse_args(argv)
    try:
        import demucs  # noqa: F401
    except ImportError:
        sys.exit("demucs is missing: pip install demucs")
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", a.model, "-o", tmp, a.audio],
                       check=True)
        found = list(Path(tmp).glob(f"{a.model}/*/vocals.wav"))
        if not found:
            sys.exit("demucs wrote no vocals.wav")
        for name in ("vocals.wav", "no_vocals.wav"):
            shutil.move(str(found[0].parent / name), out / name)
    print(f"{out}/vocals.wav and {out}/no_vocals.wav")
    return 0


if __name__ == "__main__":
    sys.exit(main())
