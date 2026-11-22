#!/usr/bin/env bash
# Studio setup for a fresh cloud container: the tools the format skills need beyond what the image ships.
# Idempotent: re-running skips what is already there. Paste its path into the environment's setup script setting so
# every new session starts ready, or run it by hand:  bash studio/setup_env.sh
#
# Hosts it fetches from (allow them in the environment's network settings):
#   pypi.org, files.pythonhosted.org          Python packages
#   download.pytorch.org                      the CPU build of torch + torchaudio
#   registry.npmjs.org, cdn.playwright.dev,   Playwright and its Chromium (skipped when already installed)
#     playwright.download.prss.microsoft.com
#   github.com, codeload.github.com           earshot (pinned commit)
#   download.blender.org                      Blender LTS
#   raw.githubusercontent.com                 the OpenCV face cascades (pinned tag)
# And on first use, by the tools themselves: dl.fbaipublicfiles.com (MMS_FA + demucs weights),
# openaipublic.azureedge.net (Whisper), storage.googleapis.com (MediaPipe models), api.openverse.org + cdn.freesound.org.
# Then run `python3 studio/check_env.py` to see what is ready. A step that cannot run warns and the rest go on; only a
# missing Playwright (every canvas render needs it) stops the script.
set -euo pipefail

say() { printf '\n== %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
have_py() { python3 -c "import $1" 2>/dev/null; }

SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null; then SUDO="sudo"; fi

# pip on a PEP 668 ("externally managed") Python: allowed here only as root in a throwaway container. Anywhere else,
# use a virtual environment: python3 -m venv .venv && . .venv/bin/activate && bash studio/setup_env.sh
PIP=(python3 -m pip install -q)
if python3 -c 'import sys, sysconfig, os; sys.exit(0 if os.path.exists(os.path.join(sysconfig.get_paths()["stdlib"], "EXTERNALLY-MANAGED")) and sys.prefix == sys.base_prefix else 1)'; then
  if [ "$(id -u)" -eq 0 ] && { [ -f /.dockerenv ] || [ -n "${CLAUDE_CODE_REMOTE:-}" ] || grep -qE 'docker|containerd|kubepods' /proc/1/cgroup 2>/dev/null; }; then
    PIP+=(--break-system-packages)
  else
    echo "This Python is externally managed (PEP 668). Create a venv first:"
    echo "  python3 -m venv .venv && . .venv/bin/activate && bash studio/setup_env.sh"
    exit 1
  fi
fi

# download $1 to $2 through a temporary name, so an interrupted or refused download never leaves a broken file
fetch() {
  local url=$1 dest=$2 tmp
  tmp="$(mktemp "${dest}.XXXX.part")"
  if curl -fsSL --retry 3 --max-time 900 -o "$tmp" "$url"; then mv -f "$tmp" "$dest"; else rm -f "$tmp"; return 1; fi
}

say "system libraries (EGL for MediaPipe, espeak-ng for synthetic test speech)"
if command -v apt-get >/dev/null; then
  missing=()
  for p in libegl1 libgles2 libgl1 espeak-ng; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
  if ((${#missing[@]})); then
    { $SUDO apt-get update -qq && $SUDO apt-get install -y -qq "${missing[@]}" >/dev/null; } || warn "apt could not install ${missing[*]}"
  fi
fi

say "Playwright + Chromium (studio/render_canvas.cjs renders every canvas skill)"
# a global npm install lands in `npm root -g`, which Node does not search unless NODE_PATH says so
if command -v npm >/dev/null; then export NODE_PATH="$(npm root -g)${NODE_PATH:+:$NODE_PATH}"; fi
if node -e "require('playwright')" 2>/dev/null; then echo "playwright present"
else npm install -g playwright@1.63.0 && npx playwright install --with-deps chromium; fi
node -e "require('playwright')" || { echo "playwright is still missing: canvas renders will fail (NODE_PATH=$NODE_PATH)"; exit 1; }

say "torch + torchaudio (CPU build, matching versions)"
have_py torchaudio || "${PIP[@]}" torch torchaudio --index-url https://download.pytorch.org/whl/cpu || warn "torch could not be installed"

say "alignment, separation, transcription, beats, mattes"
for mod in demucs uroman whisper mediapipe librosa soundfile; do
  pkg=$mod; [ "$mod" = whisper ] && pkg=openai-whisper
  # --extra-index-url keeps pip on the CPU torch already installed instead of pulling a CUDA build
  have_py "$mod" || "${PIP[@]}" "$pkg" --extra-index-url https://download.pytorch.org/whl/cpu || warn "$pkg could not be installed"
done

say "earshot: real-sounding effects in words (MIT; github.com/Leonxlnx/earshot, not the PyPI name)"
EARSHOT_REF=7a7f7c5c70d4a763a1eca4b3666af7c77e313f97   # main as of 2026-11-22; bump on purpose
command -v earshot >/dev/null || "${PIP[@]}" "earshot @ git+https://github.com/Leonxlnx/earshot@${EARSHOT_REF}" \
  || warn "earshot could not be installed (is github.com allowed?); sfx.py falls back to its code sounds"

say "Blender (LTS) for 3d-explainer"
if ! command -v blender >/dev/null; then
  ver=4.5
  base="https://download.blender.org/release/Blender${ver}"
  file=$( { curl -fsS "$base/" || true; } | { grep -o "blender-${ver}\.[0-9]*-linux-x64\.tar\.xz" || true; } | sort -V | tail -1)
  if [ -z "$file" ]; then
    warn "could not list Blender ${ver} builds; skipping (3d-explainer will say so)"
  elif fetch "$base/$file" /tmp/blender.tar.xz; then
    sums=$( { curl -fsS "$base/${file%-linux-x64.tar.xz}.sha256" || true; } )   # e.g. blender-4.5.15.sha256
    want=$(printf '%s\n' "$sums" | grep -E "(^| )\*?${file}\$" | awk '{print $1}' | head -1)
    have=$(sha256sum /tmp/blender.tar.xz | awk '{print $1}')
    if [ -n "$want" ] && [ "$want" != "$have" ]; then
      warn "Blender checksum mismatch; not installed"; rm -f /tmp/blender.tar.xz
    else
      [ -z "$want" ] && warn "no published checksum found for $file; installed unchecked"
      $SUDO tar -xf /tmp/blender.tar.xz -C /opt && rm -f /tmp/blender.tar.xz
      $SUDO ln -sf "/opt/${file%.tar.xz}/blender" /usr/local/bin/blender
    fi
  else
    warn "Blender download failed; skipping"
  fi
fi

say "OpenCV face cascades for reframing (OpenCV 5 ships without them)"
CASCADES="$HOME/.cache/aifilm/opencv"
mkdir -p "$CASCADES"
for name in haarcascade_frontalface_default.xml haarcascade_profileface.xml; do
  [ -s "$CASCADES/$name" ] && continue
  fetch "https://raw.githubusercontent.com/opencv/opencv/4.10.0/data/haarcascades/$name" "$CASCADES/$name" \
    || warn "could not fetch $name; face-aware reframing stays off"
done
echo "$CASCADES"

say "done"
python3 "$(dirname "$0")/check_env.py"   # the table says what is ready; read it before the first render
