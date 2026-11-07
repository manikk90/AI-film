#!/usr/bin/env bash
# Install Mann's open-source editing toolchain. Safe to re-run.
#   FFmpeg      - cutting, grading, mixing, loudness, analysis   (system package)
#   yt-dlp      - reference downloads for the style lab          (pip)
#   Whisper     - transcripts and word-timed captions            (pip: faster-whisper)
#   Hyperframes - HTML/GSAP motion graphics rendered to video    (npm, needs Node >= 22)
set -euo pipefail

say() { printf '\n== %s\n' "$*"; }

say "FFmpeg"
if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install ffmpeg
  elif command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y ffmpeg fontconfig fonts-noto-core
  else echo "Install FFmpeg from https://ffmpeg.org/download.html and re-run"; exit 1; fi
fi
ffmpeg -version | head -1

say "yt-dlp, faster-whisper, fontTools, OpenCV"
python3 -m pip install --upgrade yt-dlp faster-whisper fonttools
# OpenCV 4.x ships the Haar face cascades used for face-aware reframing (OpenCV 5 dropped them)
python3 -m pip install "opencv-python-headless==4.10.0.84"

say "Hyperframes"
if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 22 ]; then
  npm install -g hyperframes@0.8.230
else
  echo "Node.js >= 22 is required for Hyperframes (https://nodejs.org). Motion graphics stay unavailable until then."
fi

say "Playwright Chromium (motion templates and canvas renders)"
if node -e "require('playwright')" 2>/dev/null; then echo "playwright present"
else npm install -g playwright && npx playwright install chromium; fi

say "Fonts (open-licensed, Latin + Devanagari merged)"
python3 -m aifilm.editor fonts-install --pairing poppins-hind || echo "Font install failed; captions fall back to system fonts"

say "Whisper model (first transcription downloads it; needs huggingface.co)"
echo "Pre-download with: python3 -c \"from faster_whisper import WhisperModel; WhisperModel('small')\""

say "Check"
python3 -m aifilm.editor doctor
