"""Checks for studio/check_env.py (the studio doctor) and studio/render_canvas.cjs (the local canvas renderer).

The renderer test draws a SYNTHETIC FIXTURE page (a colour that changes with time), not a film asset."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "studio"))
import check_env as C  # noqa: E402

ALL_TOOLS = {t: True for c in C.CAPABILITIES for t in c[1]} | {"node": True, "ffmpeg": True, "ffprobe": True,
                                                             "python3": True, "chromium": True, "kokoro": True}


def has_playwright() -> bool:
    if not shutil.which("node"):
        return False
    return subprocess.run(["node", "-e", "require('playwright')"], capture_output=True).returncode == 0


class DoctorTest(unittest.TestCase):
    def test_capabilities_follow_tools_hosts_and_keys(self):
        hosts = {h: "000" for h in C.HOSTS} | {"pypi.org": "200", "registry.npmjs.org": "200"}
        rows = {r["capability"].split(" (")[0].split(":")[0]: r for r in C.assess(ALL_TOOLS, hosts, {})}
        self.assertTrue(rows["Canvas render"]["ready"])
        self.assertTrue(rows["Editor package and 2-file delivery"]["ready"])
        self.assertTrue(rows["Word timing for known words, offline"]["ready"])
        self.assertEqual(rows["Word timing"]["missing"], ["dl.fbaipublicfiles.com"])
        no_model = [r for r in C.assess(ALL_TOOLS | {"kokoro": False}, hosts, {}) if "known words" in r["capability"]][0]
        self.assertEqual(no_model["missing"], ["kokoro"])
        self.assertEqual(rows["Transcription"]["missing"], ["openaipublic.azureedge.net or huggingface.co"])
        self.assertEqual(rows["ElevenLabs voice and SFX"]["missing"], ["api.elevenlabs.io", "$ELEVENLABS_API_KEY not set"])
        open_hosts = {h: "200" for h in C.HOSTS}
        self.assertTrue(all(r["ready"] for r in C.assess(ALL_TOOLS, open_hosts, {"ELEVENLABS_API_KEY": True})))
        whisper_via_hf = open_hosts | {"openaipublic.azureedge.net": "000"}
        row = [r for r in C.assess(ALL_TOOLS, whisper_via_hf, {}) if r["capability"].startswith("Transcription")][0]
        self.assertTrue(row["ready"])
        no_ffmpeg = ALL_TOOLS | {"ffmpeg": False}
        self.assertFalse(C.assess(no_ffmpeg, open_hosts, {})[0]["ready"])


@unittest.skipUnless(has_playwright() and shutil.which("ffprobe"), "the renderer needs Node, Playwright and FFmpeg")
class CanvasRenderTest(unittest.TestCase):
    PAGE = """<!doctype html><meta charset="utf-8"><canvas width="64" height="36"></canvas>
<script>/* SYNTHETIC FIXTURE: a colour that changes with time */
window.FILM = { DUR: 1, init() {}, render(ctx, t) { ctx.fillStyle = `rgb(${Math.round(255 * t)},0,0)`; ctx.fillRect(0, 0, 64, 36); } };
</script>"""

    def test_video_and_preview_stills(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            page.write_text(self.PAGE, encoding="utf-8")
            out = Path(tmp) / "out.mp4"
            r = subprocess.run(["node", str(REPO / "studio" / "render_canvas.cjs"), str(page), str(out), "--fps", "10",
                                "--size", "64x36"], capture_output=True, text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-print_format", "json",
                                              "-show_streams", str(out)], capture_output=True, text=True).stdout)
            self.assertEqual(info["streams"][0]["nb_read_frames"], "10")
            r = subprocess.run(["node", str(REPO / "studio" / "render_canvas.cjs"), str(page), str(Path(tmp) / "prev"),
                                "--size", "64x36", "--stills", "0.1,0.5,0.9"], capture_output=True, text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sorted(p.name for p in Path(tmp).glob("prev_*.png")), ["prev_1.png", "prev_2.png", "prev_3.png"])


if __name__ == "__main__":
    unittest.main()
