"""Checks for the shared format-skill tools in studio/ (beats, mouth curve, WhatsApp copy, render QC, alignment input
parsing). Every input here is a SYNTHETIC FIXTURE made with FFmpeg: clicks on a grid, tone bursts, colour bars."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "studio"))
FF = shutil.which("ffmpeg") and shutil.which("ffprobe")


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


@unittest.skipUnless(FF, "needs FFmpeg")
class SkillToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_mouth_curve_opens_on_voice_and_shuts_in_silence(self):
        import mouth_curve
        wav = self.tmp / "v.wav"  # synthetic: 1 s silence, 1 s tone, 1 s silence
        ff("-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=1", "-f", "lavfi", "-i", "sine=f=220:d=1:r=16000",
           "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=1", "-filter_complex", "[0][1][2]concat=n=3:v=0:a=1",
           str(wav))
        vals = mouth_curve.curve(mouth_curve.load(str(wav)), 30)
        self.assertEqual(len(vals), 90)
        self.assertLess(max(vals[:25]), 0.05)
        self.assertGreater(sum(vals[35:55]) / 20, 0.6)
        self.assertLess(max(vals[75:]), 0.05)
        shut = mouth_curve.curve(mouth_curve.load(str(wav)), 30, spans=[(1.0, 1.3)])
        self.assertLess(max(shut[52:60]), 0.01)  # released within ~0.4 s after the last word

    def test_frame_check_finds_black_and_passes_a_clean_render(self):
        import frame_check
        good, bad = self.tmp / "good.mp4", self.tmp / "bad.mp4"
        ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=2", "-f", "lavfi", "-i", "sine=d=2", "-shortest",
           "-pix_fmt", "yuv420p", str(good))
        ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=1", "-f", "lavfi", "-i", "color=black:s=320x240:r=30:d=1",
           "-f", "lavfi", "-i", "sine=d=2", "-filter_complex", "[0][1]concat=n=2:v=1:a=0[v]", "-map", "[v]",
           "-map", "2", "-shortest", "-pix_fmt", "yuv420p", str(bad))
        self.assertEqual(frame_check.main([str(good), "--size", "320x240", "--fps", "30"]), 0)
        self.assertEqual(frame_check.main([str(bad)]), 1)
        self.assertEqual(frame_check.main([str(good), "--size", "1080x1920"]), 1)

    def test_whatsapp_copy_is_720p_under_the_cap_and_never_overwrites(self):
        import whatsapp_copy
        src, dst = self.tmp / "src.mp4", self.tmp / "wa.mp4"
        ff("-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=3", "-f", "lavfi", "-i", "sine=d=3", "-shortest",
           "-pix_fmt", "yuv420p", str(src))
        self.assertEqual(whatsapp_copy.main([str(src), str(dst), "--max-mb", "2"]), 0)
        self.assertLessEqual(os.path.getsize(dst), 2_000_000)
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height", "-of", "csv=p=0", str(dst)], capture_output=True, text=True).stdout
        self.assertEqual(out.strip(), "720,1280")
        with self.assertRaises(SystemExit):
            whatsapp_copy.main([str(src), str(dst)])

    @unittest.skipUnless(importlib.util.find_spec("librosa"), "needs librosa")
    def test_beats_find_a_click_grid(self):
        import beats
        wav = self.tmp / "clicks.wav"  # synthetic: a 100 Hz kick-like burst every 0.5 s (120 BPM) for 8 s
        ff("-f", "lavfi", "-i", "aevalsrc='if(lt(mod(t,0.5),0.04),sin(2*PI*90*t)*exp(-60*mod(t,0.5)),0)':s=22050:d=8",
           str(wav))
        d = beats.analyse(str(wav))
        self.assertAlmostEqual(d["tempo"], 120, delta=4)
        self.assertGreater(len(d["kicks"]), 10)
        gaps = [b - a for a, b in zip(d["beats"], d["beats"][1:])]
        self.assertAlmostEqual(sum(gaps) / len(gaps), 0.5, delta=0.03)

    def test_alignment_input_keeps_speakers_adlibs_and_devanagari(self):
        import mms_align
        txt = self.tmp / "l.txt"
        txt.write_text("GUEST|मंज़िल क्या है?\n\nroad pad denge (skrrt skrrt)\n", encoding="utf-8")
        lines = mms_align.parse_lines(str(txt))
        self.assertEqual([l["speaker"] for l in lines], ["GUEST", None])
        self.assertEqual([w["clean"] for w in lines[0]["words"]], ["मंज़िल", "क्या", "है"])
        self.assertEqual([w["adlib"] for w in lines[1]["words"]], [False, False, False, True, True])
        self.assertEqual(mms_align.romanise(["Road", "pad's"]), ["road", "pad's"])


if __name__ == "__main__":
    unittest.main()
