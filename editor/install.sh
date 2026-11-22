#!/usr/bin/env bash
# Install Mann's open-source editing toolchain. Safe to re-run, from any directory.
#   FFmpeg      - cutting, grading, mixing, loudness, analysis   (system package)
#   yt-dlp      - reference downloads for the style lab          (pip)
#   Whisper     - transcripts and word-timed captions            (pip: faster-whisper)
#   Hyperframes - HTML/GSAP motion graphics rendered to video    (npm, needs Node >= 22)
# On an "externally managed" Python (PEP 668: Debian/Ubuntu system Python, Homebrew), run it inside a venv:
#   python3 -m venv .venv && . .venv/bin/activate && bash editor/install.sh
set -euo pipefail
cd "$(dirname "$0")/.."   # the repo root, so `python3 -m aifilm.editor` works wherever this was started

say() { printf '\n== %s\n' "$*"; }
SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null; then SUDO="sudo"; fi

say "FFmpeg"
if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install ffmpeg
  elif command -v apt-get >/dev/null; then $SUDO apt-get update && $SUDO apt-get install -y ffmpeg fontconfig fonts-noto-core
  else echo "Install FFmpeg from https://ffmpeg.org/download.html and re-run"; exit 1; fi
fi
ffmpeg -version | head -1

say "yt-dlp, faster-whisper, fontTools, OpenCV"
python3 -m pip install --upgrade yt-dlp faster-whisper fonttools
# Face-aware reframing needs OpenCV plus its Haar face cascades. OpenCV 4.x ships the cascades; OpenCV 5 does not,
# and studio/setup_env.sh caches them in ~/.cache/aifilm/opencv instead. MediaPipe (studio) brings
# opencv-contrib-python 5, and two OpenCV wheels in one environment overwrite each other's cv2/ folder, so only add
# the 4.x headless wheel when no OpenCV is installed yet.
if python3 -c "import cv2" 2>/dev/null; then
  echo "OpenCV $(python3 -c 'import cv2; print(cv2.__version__)') present; keeping it (cascades: OpenCV's own or ~/.cache/aifilm/opencv)"
else
  python3 -m pip install "opencv-python-headless==4.10.0.84"
fi

say "Hyperframes"
if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 22 ]; then
  npm install -g hyperframes@0.8.230
else
  echo "Node.js >= 22 is required for Hyperframes (https://nodejs.org). Motion graphics stay unavailable until then."
fi

say "Playwright Chromium (motion templates and canvas renders)"
# a global npm install lands in `npm root -g`, which Node does not search unless NODE_PATH says so
if command -v npm >/dev/null; then export NODE_PATH="$(npm root -g)${NODE_PATH:+:$NODE_PATH}"; fi
if node -e "require('playwright')" 2>/dev/null; then echo "playwright present"
else npm install -g playwright@1.63.0 && npx playwright install --with-deps chromium; fi

say "Fonts (open-licensed, Latin + Devanagari merged)"
python3 -m aifilm.editor fonts-install --pairing poppins-hind || echo "Font install failed; captions fall back to system fonts"

say "Whisper model (first transcription downloads it; needs huggingface.co)"
echo "Pre-download with: python3 -c \"from faster_whisper import WhisperModel; WhisperModel('small')\""

say "Check"
python3 -m aifilm.editor doctor
