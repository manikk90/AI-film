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


FAKE_EARSHOT = """#!/usr/bin/env python3
# SYNTHETIC FIXTURE: a stand-in for the earshot CLI with fixed answers
import json, subprocess, sys
a = sys.argv[1:]
out = a[a.index("-o") + 1]
want = a[-1]
dur = a[a.index("--dur") + 1] if "--dur" in a else "3"
open(out + ".args", "w").write(json.dumps(a))
if "hang" in want:
    import time; time.sleep(5)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=500:d=3", out], check=True)
info = {"sound": "bell/bike", "files": [out], "unknown": [], "not_in_sound": [], "takes": [{"dur_s": 3.0}]}
if "temple" in want:
    info["not_in_sound"] = ["temple"]
print(json.dumps(info))
"""


class OpenverseTest(unittest.TestCase):
    def test_only_safe_licences_and_no_mature_or_overlong_results(self):
        rows = [row(1, "by-nc"), row(2, mature=True), row(3, ms=90000), row(4), row(5, "pdm"), row(6, "by")]
        picked = OV.pick(rows, 10, OV.allowed("cc0,pdm"), max_s=30)
        self.assertEqual([r["id"][:8] for r in picked], ["00000004", "00000005"])
        with self.assertRaises(SystemExit):
            OV.allowed("cc0,by-nc")
        self.assertIn("REQUIRED", OV.credit_line(row(6, "by")))
        self.assertNotIn("REQUIRED", OV.credit_line(row(4)))

    @unittest.skipUnless(FF, "needs FFmpeg to make a real audio body")
    def test_save_writes_files_credits_and_sources_skips_refused_bad_and_existing(self):
        calls = []
        with tempfile.TemporaryDirectory() as t2:
            mp3 = Path(t2) / "a.mp3"  # synthetic tone standing in for a downloaded recording
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=d=0.5", str(mp3)], check=True)
            audio = mp3.read_bytes()

        def fake_get(url, tries=6):
            calls.append(url)
            if "/2-" in url:
                raise urllib.error.HTTPError(url, 403, "Forbidden", None, None)
            if "/5-" in url:
                return b"<html>login page</html>"  # HTTP 200 but not audio
            return audio

        real = OV._get
        OV._get = fake_get
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                files = OV.save([row(1), row(2), row(5), row(3), row(4)], out, want=2)
                self.assertEqual([f.name for f in files], ["bell-1_00000001.mp3", "bell-3_00000003.mp3"])  # 2, 5 skipped
                self.assertTrue(all(f.suffix == ".mp3" for f in files))  # from the URL, not filetype "aif"
                self.assertFalse(list(out.glob("*.part")))  # the bad body left nothing behind
                src = json.loads((out / "sources.json").read_text())
                self.assertEqual([s["file"] for s in src], [f.name for f in files])
                self.assertEqual((src[0]["license"], src[0]["verified"]), ("cc0", None))
                credits = (out / "CREDITS.md").read_text()
                self.assertEqual(credits.count("UNVERIFIED]"), 2)
                again = OV.save([row(1)], out)  # already there: skipped, nothing appended
                self.assertEqual(again, [])
                self.assertEqual(len(json.loads((out / "sources.json").read_text())), 2)
                # verify: the source page decides; page 1 shows CC0, page 3 shows a non-commercial licence
                pages = {"https://example.org/s/1": b"... creativecommons.org/publicdomain/zero/1.0 ...",
                         "https://example.org/s/3": b"... creativecommons.org/licenses/by-nc/4.0 ..."}
                OV._get = lambda url, tries=6: pages[url]
                rows = OV.verify(out)
                self.assertEqual([r["verified"] for r in rows], ["verified", "mismatch"])
                self.assertIn("LICENCE MISMATCH", (out / "CREDITS.md").read_text())
                self.assertEqual(OV.main(["verify", str(out)]), 1)  # a mismatch blocks
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


@unittest.skipUnless(FF and importlib.util.find_spec("numpy"), "needs FFmpeg and numpy")
class EarshotContractTest(unittest.TestCase):
    """Uses a fake earshot on PATH so the edge cases are exact and need no install."""

    def setUp(self):
        import os
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name)
        (self.bin / "earshot").write_text(FAKE_EARSHOT)
        (self.bin / "earshot").chmod(0o755)
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.bin}{os.pathsep}{self.old_path}"

    def tearDown(self):
        import os
        os.environ["PATH"] = self.old_path
        self.tmp.cleanup()

    def test_not_in_sound_is_refused_like_unknown(self):
        import sfx
        with self.assertRaises(sfx.EarshotMiss):
            sfx.earshot("temple bell")
        x, info = sfx.earshot("temple bell", allow_guess=True)
        self.assertTrue(info["guess"])

    def test_length_is_passed_and_enforced(self):
        import sfx
        rows = []
        bed = sfx.place([{"t": 0.0, "want": "a soft whoosh", "len": 1.0, "sfx": "whoosh"}], dur=3, report=rows)
        self.assertEqual(rows[0]["source"], "earshot")
        self.assertLess(float(abs(bed[int(1.05 * sfx.SR):]).max()), 1e-3)  # 3 s take trimmed to the 1 s cue

    def test_required_engine_never_falls_back_and_timeouts_are_misses(self):
        import subprocess as sp
        import sfx
        with self.assertRaises(SystemExit):
            sfx.place([{"t": 0.0, "want": "temple bell", "sfx": "bell"}], dur=2, engine="earshot")
        real = sp.run

        def quick_timeout(cmd, *a, **k):
            if cmd and cmd[0] == "earshot":
                raise sp.TimeoutExpired(cmd, 300)
            return real(cmd, *a, **k)
        sfx.subprocess.run = quick_timeout
        try:
            rows = []
            sfx.place([{"t": 0.0, "want": "a soft whoosh", "sfx": "whoosh"}], dur=2, report=rows)  # auto: falls back
            self.assertEqual(rows[0]["source"], "code")
            self.assertIn("300 s", rows[0]["fallback_reason"])
        finally:
            sfx.subprocess.run = real

    def test_want_accepts_a_catalogue_id_without_words(self):
        import sfx
        out = self.bin / "w.wav"
        self.assertEqual(sfx.main(["want", "--sound", "whoosh/fast", str(out)]), 0)
        self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
