#!/usr/bin/env bash
# Studio setup for a fresh cloud container: the tools the format skills need beyond what the image ships.
# Idempotent: re-running skips what is already there. Paste its path into the environment's setup script setting so
# every new session starts ready, or run it by hand:  bash studio/setup_env.sh
#
# Needs these hosts open (environment network settings): pypi.org, download.pytorch.org, dl.fbaipublicfiles.com
# (MMS_FA + demucs weights, fetched on first use), openaipublic.azureedge.net (Whisper, on first use),
# storage.googleapis.com (MediaPipe models, on first use), download.blender.org, raw.githubusercontent.com,
# github.com (earshot), api.openverse.org + cdn.freesound.org (recorded CC0 sounds).
# Then run `python3 studio/check_env.py` to see what is ready.
set -euo pipefail

say() { printf '\n== %s\n' "$*"; }
have_py() { python3 -c "import $1" 2>/dev/null; }

say "system libraries (EGL for MediaPipe, espeak-ng for synthetic test speech)"
if command -v apt-get >/dev/null; then
  missing=()
  for p in libegl1 libgles2 libgl1 espeak-ng; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
  if ((${#missing[@]})); then apt-get update -qq && apt-get install -y -qq "${missing[@]}" >/dev/null; fi
fi

say "Playwright + Chromium (studio/render_canvas.cjs renders every canvas skill)"
if node -e "require('playwright')" 2>/dev/null; then echo "playwright present"
else npm install -g playwright && npx playwright install chromium; fi
node -e "require('playwright')" || { echo "playwright is still missing: canvas renders will fail"; exit 1; }

say "torch + torchaudio (CPU build)"
have_py torchaudio || python3 -m pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu

say "alignment, separation, transcription, beats, mattes"
for mod in demucs uroman whisper mediapipe librosa soundfile; do
  pkg=$mod; [ "$mod" = whisper ] && pkg=openai-whisper
  have_py "$mod" || python3 -m pip install -q "$pkg"
done

say "earshot: real-sounding effects in words (MIT; github.com/Leonxlnx/earshot, not the PyPI name)"
command -v earshot >/dev/null || python3 -m pip install -q "earshot @ git+https://github.com/Leonxlnx/earshot" \
  || echo "earshot could not be installed (is github.com allowed?); sfx.py falls back to its code sounds"

say "Blender (LTS) for 3d-explainer"
if ! command -v blender >/dev/null; then
  ver=4.5
  file=$( { curl -s "https://download.blender.org/release/Blender${ver}/" || true; } | { grep -o "blender-${ver}\.[0-9]*-linux-x64\.tar\.xz" || true; } | sort -V | tail -1)
  if [ -n "$file" ]; then
    curl -sSL -o /tmp/blender.tar.xz "https://download.blender.org/release/Blender${ver}/${file}"
    tar -xf /tmp/blender.tar.xz -C /opt && rm -f /tmp/blender.tar.xz
    ln -sf "/opt/${file%.tar.xz}/blender" /usr/local/bin/blender
  else
    echo "could not list Blender ${ver} builds; skipping (3d-explainer will say so)"
  fi
fi

say "OpenCV face cascade for reframing (OpenCV 5 ships without it)"
python3 - <<'PY'
from pathlib import Path
import urllib.request
base = Path.home() / ".cache" / "aifilm" / "opencv"
base.mkdir(parents=True, exist_ok=True)
for name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
    dest = base / name
    if not dest.exists():
        urllib.request.urlretrieve("https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/" + name, dest)
print(base)
PY

say "done"
python3 "$(dirname "$0")/check_env.py"   # the table says what is ready; read it before the first render
