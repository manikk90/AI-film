#!/usr/bin/env python3
"""Studio doctor: what works in this environment right now, for the studio and the imported format skills.

    python3 studio/check_env.py           # a table, plus what to change in the environment settings
    python3 studio/check_env.py --json    # the same as JSON

It checks the local tools, whether the hosts the skills download from answer through the session's proxy (one quick
HEAD request each, nothing downloaded), and whether the ElevenLabs key is set (never printing it). Run it at the start
of a production and paste the table into 06-qc.md. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CHROMIUM = Path("/opt/pw-browsers")
KOKORO = Path(os.environ.get("KOKORO_DIR") or Path(__file__).resolve().parents[2] / "lemomo-ai/lemo-opuscar/core/tts")
HOSTS = {
    "dl.fbaipublicfiles.com": "https://dl.fbaipublicfiles.com/mms/torchaudio/ctc_alignment_mling_uroman/model.pt",
    "openaipublic.azureedge.net": "https://openaipublic.azureedge.net/main/whisper/models/"
                                  "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
    "huggingface.co": "https://huggingface.co/",
    "api.elevenlabs.io": "https://api.elevenlabs.io/v1/models",
    "registry.npmjs.org": "https://registry.npmjs.org/hyperframes",
    "pypi.org": "https://pypi.org/simple/pip/",
}
# capability, the tools it needs, the hosts it needs (all of them), alternative hosts (any one), env vars, who uses it
CAPABILITIES = [
    ("Canvas render (Playwright Chromium + FFmpeg, studio/render_canvas.cjs)", ["node", "ffmpeg", "chromium"], [], [], [],
     "daksh-ai and every canvas-drawn imported skill"),
    ("Editor package and 2-file delivery", ["ffmpeg", "ffprobe"], [], [], [], "every finished film"),
    ("Word timing for known words, offline (studio/word_timing.py)", ["ffmpeg", "kokoro"], [], [], [],
     "captions from a script, lyrics or the locked dialogue"),
    ("Word timing: torchaudio MMS_FA forced alignment", ["python3"], ["dl.fbaipublicfiles.com", "pypi.org"], [], [],
     "the imported skills' own alignment step"),
    ("Transcription: Whisper", ["python3"], ["pypi.org"], ["openaipublic.azureedge.net", "huggingface.co"], [],
     "skills that start from a recording with no script (talking-head edits, katha, podcasts)"),
    ("Beats, kicks and hits (studio/beats.py, librosa)", ["py:librosa", "ffmpeg"], [], [], [],
     "every music skill: cuts, punches and pops on the beat"),
    ("Mouth curve for lip-sync (studio/mouth_curve.py)", ["py:numpy", "ffmpeg"], [], [], [],
     "every skill with a talking or singing cartoon"),
    ("Vocal separation (studio/separate_vocals.py, demucs)", ["py:demucs"], ["dl.fbaipublicfiles.com"], [], [],
     "lyric and rap skills: align on the vocal stem, mute a word over the instrumental"),
    ("Person matte (studio/person_matte.py, MediaPipe)", ["py:mediapipe"], [], [], [],
     "skills that put graphics behind the owner or trace their outline"),
    ("Blender headless (EEVEE)", ["blender"], [], [], [], "3d-explainer"),
    ("WhatsApp copy and render QC (studio/whatsapp_copy.py, studio/frame_check.py)", ["ffmpeg", "ffprobe"], [], [],
     [], "every finished video"),
    ("ElevenLabs voice and SFX", [], ["api.elevenlabs.io"], [], ["ELEVENLABS_API_KEY"], "the director's voice and SFX"),
    ("HyperFrames render (npm)", ["node"], ["registry.npmjs.org"], [], [],
     "daksh-ai's own renderer; also needs the owner's permission to run npx packages"),
]


def probe_tool(name: str) -> bool:
    if name.startswith("py:"):  # a Python module, found without importing it
        import importlib.util
        return importlib.util.find_spec(name[3:]) is not None
    if name == "chromium":
        return CHROMIUM.is_dir() and any(CHROMIUM.glob("chromium*"))
    if name == "kokoro":  # the offline voice model, with a Python that can run it (the Lemo-Opuscar venv)
        return (KOKORO / "kokoro-v1.0.onnx").exists() and (KOKORO / "voices-v1.0.bin").exists()
    return shutil.which(name) is not None


def probe_host(url: str) -> str:
    """The HTTP status as text, or "000" when nothing answered (blocked, or no route)."""
    if shutil.which("curl"):
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-I", "-m", "12", "-w", "%{http_code}", url],
                           capture_output=True, text=True)
        return (r.stdout or "000").strip()[-3:]
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=12) as resp:
            return str(resp.status)
    except Exception as e:  # noqa: BLE001  (any failure means the host did not answer usefully)
        code = getattr(e, "code", None)
        return str(code) if code else "000"


def assess(tools: dict, hosts: dict, env: dict) -> list[dict]:
    rows = []
    for name, need_tools, need_hosts, any_hosts, need_env, used_by in CAPABILITIES:
        missing = [t for t in need_tools if not tools.get(t)]
        missing += [h for h in need_hosts if hosts.get(h, "000") == "000"]
        if any_hosts and all(hosts.get(h, "000") == "000" for h in any_hosts):
            missing.append(" or ".join(any_hosts))
        missing += [f"${v} not set" for v in need_env if not env.get(v)]
        rows.append({"capability": name, "ready": not missing, "missing": missing, "used_by": used_by})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Report what works in this environment for the studio.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    names = {t for c in CAPABILITIES for t in c[1]} | {"node", "ffmpeg", "ffprobe", "python3", "chromium", "kokoro"}
    tools = {t: probe_tool(t) for t in sorted(names)}
    with ThreadPoolExecutor(len(HOSTS)) as pool:
        hosts = dict(zip(HOSTS, pool.map(probe_host, HOSTS.values())))
    env = {"ELEVENLABS_API_KEY": bool(os.environ.get("ELEVENLABS_API_KEY"))}
    rows = assess(tools, hosts, env)
    if a.json:
        print(json.dumps({"tools": tools, "hosts": hosts, "env": env, "capabilities": rows}, indent=1))
        return 0
    print("| Capability | Ready | Missing | Used by |\n|---|---|---|---|")
    for r in rows:
        print(f"| {r['capability']} | {'yes' if r['ready'] else 'no'} | {', '.join(r['missing']) or '-'} | {r['used_by']} |")
    blocked = sorted(h for h, code in hosts.items() if code == "000")
    if blocked:
        print("\nBlocked hosts: " + ", ".join(blocked) + ". The owner can allow them under Network access in the "
              "environment's settings (https://code.claude.com/docs/en/cloud-environments#network-access).")
    if not env["ELEVENLABS_API_KEY"]:
        print("ELEVENLABS_API_KEY is not set: the owner adds it in the environment's settings, never in chat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
