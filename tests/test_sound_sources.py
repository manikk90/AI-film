"""Checks for the sound sources behind studio/sfx.py: earshot (real-sounding effects in words) and Openverse
(studio/openverse_audio.py, CC0 / public-domain recordings). Network is never used here: Openverse answers are
SYNTHETIC FIXTURES shaped like the API's, and audio files are made with FFmpeg."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "studio"))
import openverse_audio as OV  # noqa: E402

FF = shutil.which("ffmpeg")


def row(i, license="cc0", mature=False, ms=3000, title="bell", url=None):
    return {"id": f"{i:08d}-0000-0000-0000-000000000000", "title": f"{title} {i}", "creator": f"maker{i}",
            "license": license, "license_version": "1.0", "license_url": "https://creativecommons.org/",
            "url": url or f"https://cdn.example.org/previews/{i}-hq.mp3", "foreign_landing_url": f"https://example.org/s/{i}",
            "duration": ms, "filetype": "aif", "mature": mature, "provider": "freesound"}


class OpenverseTest(unittest.TestCase):
    def test_only_safe_licences_and_no_mature_or_overlong_results(self):
        rows = [row(1, "by-nc"), row(2, mature=True), row(3, ms=90000), row(4), row(5, "pdm"), row(6, "by")]
        picked = OV.pick(rows, 10, OV.allowed("cc0,pdm"), max_s=30)
        self.assertEqual([r["id"][:8] for r in picked], ["00000004", "00000005"])
        with self.assertRaises(SystemExit):
            OV.allowed("cc0,by-nc")
        self.assertIn("REQUIRED", OV.credit_line(row(6, "by")))
        self.assertNotIn("REQUIRED", OV.credit_line(row(4)))

    def test_save_writes_files_credits_and_sources_skips_refused_and_existing(self):
        calls = []

        def fake_get(url, tries=6):
            calls.append(url)
            if "/2-" in url:
                raise urllib.error.HTTPError(url, 403, "Forbidden", None, None)
            return b"ID3 synthetic audio bytes"

        real = OV._get
        OV._get = fake_get
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                files = OV.save([row(1), row(2), row(3), row(4)], out, want=2)
                self.assertEqual([f.name for f in files], ["bell-1_00000001.mp3", "bell-3_00000003.mp3"])  # 2 refused
                self.assertTrue(all(f.suffix == ".mp3" for f in files))  # from the URL, not filetype "aif"
                src = json.loads((out / "sources.json").read_text())
                self.assertEqual([s["file"] for s in src], [f.name for f in files])
                self.assertEqual(src[0]["license"], "cc0")
                self.assertEqual(len((out / "CREDITS.md").read_text().splitlines()), 2)
                again = OV.save([row(1)], out)  # already there: skipped, nothing appended
                self.assertEqual(again, [])
                self.assertEqual(len(json.loads((out / "sources.json").read_text())), 2)
        finally:
            OV._get = real
        self.assertNotIn(row(4)["url"], calls)  # stopped once it had two files


@unittest.skipUnless(FF and importlib.util.find_spec("numpy"), "needs FFmpeg and numpy")
class SfxSourcesTest(unittest.TestCase):
    def test_file_cue_is_trimmed_levelled_and_reported(self):
        import numpy as np
        import sfx
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "bell.mp3"  # synthetic 5 s tone standing in for a fetched recording
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=660:d=5", str(f)], check=True)
            rows = []
            bed = sfx.place([{"t": 1.0, "file": str(f), "len": 1.5, "gain": -6}], dur=4, report=rows)
            self.assertEqual(rows[0]["source"], "file")
            on = np.abs(bed[int(1.05 * sfx.SR): int(2.4 * sfx.SR)]).max()
            self.assertAlmostEqual(float(on), 10 ** (-6 / 20), delta=0.05)
            self.assertLess(np.abs(bed[int(2.6 * sfx.SR):]).max(), 1e-3)  # trimmed to 1.5 s
            self.assertLess(np.abs(bed[: int(0.95 * sfx.SR)]).max(), 1e-3)

    def test_code_engine_ignores_words_and_a_cue_without_fallback_fails(self):
        import sfx
        rows = []
        sfx.place([{"t": 0.1, "want": "footstep on gravel", "sfx": "pop"}], dur=1, engine="code", report=rows)
        self.assertEqual((rows[0]["source"], rows[0]["id"]), ("code", "pop"))
        with self.assertRaises(SystemExit):
            sfx.place([{"t": 0.1, "want": "footstep on gravel"}], dur=1, engine="code")

    @unittest.skipUnless(shutil.which("earshot"), "needs earshot (bash studio/setup_env.sh)")
    def test_earshot_makes_clear_requests_and_refuses_guesses(self):
        import sfx
        x, info = sfx.earshot("a fast whoosh for a cut", seed=1)
        self.assertTrue(info["id"].startswith("whoosh/"), info)
        self.assertEqual(x.shape[1], 2)
        with self.assertRaises(sfx.EarshotMiss):
            sfx.earshot("temple bell")  # earshot only guesses (a bicycle bell): refused
        rows = []
        sfx.place([{"t": 0.1, "want": "temple bell", "sfx": "bell"}], dur=3, report=rows)
        self.assertEqual(rows[0]["source"], "code")
        self.assertIn("did not understand", rows[0]["fallback_reason"])


if __name__ == "__main__":
    unittest.main()
