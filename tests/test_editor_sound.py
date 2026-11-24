"""Mann's sound pass (aifilm/editor/sound.py). Every medium here is a SYNTHETIC FIXTURE made with
FFmpeg (test patterns, gated sine "voice", sine-burst SFX, a 60 Hz decaying "kick" track) or a
synthetic beat grid in numbers. They prove the measurements and the cue maths, not taste."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from aifilm.core import ProductionError, write_json
from aifilm.editor import edl as E
from aifilm.editor import render as R
from aifilm.editor import sound as SD
from aifilm.editor import tools as T
from aifilm.editor.cli import main

try:
    import numpy  # noqa: F401
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def ff(*args):
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + [str(a) for a in args], check=True, timeout=120)


class CueTests(unittest.TestCase):
    """SYNTHETIC EDL dicts (no media): cue types and offsets."""

    def edl(self):
        return {"version": 1, "format": {"width": 320, "height": 180, "fps": 30},
                "sources": {"A": "raw/A.mp4", "B": "raw/B.mp4"},
                "clips": [
                    {"id": "C01", "source": "A", "in": 0.0, "out": 1.0},
                    {"id": "C02", "source": "B", "in": 0.0, "out": 1.0},                      # scene cut at 1.0
                    {"id": "C03", "source": "B", "in": 1.0, "out": 2.0},                      # jump cut: no cue
                    {"id": "C04", "source": "A", "in": 1.0, "out": 2.0, "cue": "build_up"},   # riser ends on next hit
                    {"id": "C05", "source": "B", "in": 2.0, "out": 3.0, "cue": "reveal"},
                ],
                "overlays": [{"file": "raw/lower.mov", "at": 0.5}]}

    def test_whoosh_is_two_frames_before_the_cut(self):
        cues = SD.cues_from_edl(self.edl())
        whoosh = [c for c in cues if c["type"] == "scene_cut"]
        self.assertEqual(len(whoosh), 1)
        self.assertEqual(whoosh[0]["anchor"], 1.0)
        self.assertAlmostEqual(whoosh[0]["at"], 1.0 - 2 / 30.0, places=3)
        self.assertEqual(whoosh[0]["offset_frames"], -2)
        self.assertFalse(any(c["from"] == "clip C03" for c in cues), "a jump cut inside one source gets no whoosh")

    def test_pop_on_the_frame_riser_ends_on_next_hit_reveal_loudest(self):
        cues = {c["type"]: c for c in SD.cues_from_edl(self.edl(), riser_seconds=0.8)}
        self.assertEqual(cues["appear"]["at"], 0.5)
        self.assertEqual(cues["build_up"]["end"], 4.0)        # C05 starts at 4.0 s
        self.assertAlmostEqual(cues["build_up"]["at"], 3.2, places=3)
        self.assertTrue(cues["reveal"]["loudest"])
        self.assertEqual(cues["reveal"]["role"], "impact")
        targets = SD.role_targets()
        self.assertEqual(max(targets[r] for r in ("ui", "whoosh", "impact")), targets["impact"])

    def test_rules_lead_frames_and_bad_cue(self):
        edl = self.edl()
        cues = SD.cues_from_edl(edl, rules={"sfx_whoosh_lead_frames": 3})
        self.assertAlmostEqual([c for c in cues if c["type"] == "scene_cut"][0]["at"], 0.9, places=3)
        edl["clips"][1]["cue"] = "kaboom"
        with self.assertRaises(ProductionError):
            SD.cues_from_edl(edl)

    def test_cue_names_match_edl_validation(self):
        self.assertEqual(set(SD.CUES) | {"none"}, set(E.CUE_NAMES))
        self.assertEqual(set(SD.DEFAULT_ROLE_DB), set(E.SFX_ROLES))

    def test_gain_formula(self):
        self.assertEqual(SD.sfx_gain("ui", -10.0, -3.0), -21.0)
        self.assertEqual(SD.sfx_gain("meme", -10.0, -20.0), 7.0)
        with self.assertRaises(ProductionError):
            SD.sfx_gain("loud", -10.0, -3.0)


class OffsetTests(unittest.TestCase):
    """SYNTHETIC beat grid (numbers only): 120 BPM, music placed 0.37 s into the file."""

    def test_offset_search_brings_median_error_under_one_frame(self):
        beats = [round(0.25 + 0.5 * k, 3) for k in range(40)]
        true_start = 0.37
        jitter = [0.012, -0.008, 0.004, -0.015, 0.0, 0.009, -0.004]
        picks = [2, 5, 6, 9, 13, 14, 18]
        cuts = [round(beats[p] - true_start + j, 3) for p, j in zip(picks, jitter)]
        before = SD.cut_errors(beats, cuts)  # music started at 0
        self.assertGreater(sorted(abs(e["error_ms"]) for e in before)[len(before) // 2], 1000 / 30.0)
        best = SD.music_offset(beats, cuts, (0.0, 2.0, 0.001))
        self.assertLessEqual(best["median_error_ms"], 1000 / 30.0)
        self.assertLessEqual(best["median_error_ms"], 10.0)
        self.assertEqual(len(best["per_cut"]), len(cuts))
        self.assertAlmostEqual((best["start"] - true_start + 0.25) % 0.5 - 0.25, 0.0, delta=0.015)  # same phase as 0.37


@unittest.skipUnless(HAS_FFMPEG and HAS_NUMPY, "FFmpeg and numpy are required for sound media tests")
class SoundMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = Path(tempfile.mkdtemp(prefix="mann-sound-fixtures-"))
        f = cls.fx
        # SYNTHETIC "voice": a 300 Hz sine with gaps at 1.0-1.6 s and 2.4-3.0 s, over a test pattern.
        ff("-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:d=4", "-f", "lavfi", "-i", "sine=frequency=300:duration=4",
           "-af", "volume='if(between(t,1.0,1.6)+between(t,2.4,3.0),0,1)':eval=frame",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", f / "voice.mp4")
        ff("-f", "lavfi", "-i", "smptebars=size=320x180:rate=30:d=4", "-f", "lavfi", "-i", "sine=frequency=300:duration=4",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", f / "bars.mp4")
        # SYNTHETIC SFX: sine bursts at different file peaks, so the gain maths matters.
        ff("-f", "lavfi", "-i", "sine=frequency=1000:duration=0.2", "-af", "volume=2.0", f / "ui.wav")
        ff("-f", "lavfi", "-i", "sine=frequency=1500:duration=0.2", "-af", "volume=0.25", f / "impact.wav")
        # SYNTHETIC "kick" music: 60 Hz bursts every 0.5 s (120 BPM) decaying fast.
        ff("-f", "lavfi", "-i", "aevalsrc=0.8*sin(2*PI*60*t)*exp(-25*mod(t\\,0.5)):s=44100:d=12", f / "kicks.wav")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fx, ignore_errors=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.edit = Path(self.temp.name) / "edit"
        T.ingest(self.edit, [self.fx / n for n in ("voice.mp4", "bars.mp4", "ui.wav", "impact.wav", "kicks.wav")])

    def test_sfx_peaks_land_on_role_targets_in_the_exported_mp4(self):
        sfx = []
        for name, role, at in (("ui.wav", "ui", 1.2), ("impact.wav", "impact", 2.6)):
            g = SD.gain_for_files(self.edit / "raw" / "voice.mp4", self.edit / "raw" / name, role)
            sfx.append({"file": "raw/" + name, "at": at, "gain_db": g["gain_db"], "role": role})
        edl = {"version": 1, "title": "Synthetic sound fixture", "format": {"width": 320, "height": 180, "fps": 30},
               "sources": {"V": "raw/voice.mp4"}, "clips": [{"id": "C01", "source": "V", "in": 0.0, "out": 4.0}],
               "audio": {"sfx": sfx}, "master": {"lufs": -14, "true_peak": -1}}
        bad = dict(edl, audio={"sfx": [dict(sfx[0], role="loud")]})
        with self.assertRaisesRegex(ProductionError, "role must be one of"):
            E.validate(self.edit, bad)
        write_json(self.edit / "edl.json", edl)
        E.storyboard(self.edit)
        with self.assertRaisesRegex(ProductionError, "not approved"):
            R.render(self.edit, preview=False)  # the sound pass never bypasses the storyboard gate
        E.approve(self.edit, "synthetic fixture approval")
        R.render(self.edit, preview=False)
        record = R.qc(self.edit)
        items = record["measured"]["sound"]["sfx_levels"]["items"]
        self.assertEqual(len(items), 2)
        for it in items:
            self.assertEqual(it["flags"], [], it)
            self.assertLessEqual(abs(it["delta_db"]), 2.0, it)
        checks = {c["check"]: c for c in record["checks"]}
        self.assertEqual(checks["sfx level 0:01.2 (ui)"]["result"], "pass", checks)
        self.assertEqual(checks["sfx level 0:02.6 (impact)"]["result"], "pass", checks)
        self.assertIn("Headphone check", (self.edit / "renders" / "QC.md").read_text(encoding="utf-8"))
        self.assertLessEqual(len(record["headphone_check"]), 5)

    def test_offbeat_check_finds_kicks_off_the_grid(self):
        kicks = self.edit / "raw" / "kicks.wav"
        on = SD.offbeat_check(kicks, [0.5 + 0.5 * k for k in range(16)])
        self.assertTrue(on["locked"], on)
        off = SD.offbeat_check(kicks, [0.6 + 0.5 * k for k in range(16)])
        self.assertFalse(off["locked"], off)
        self.assertAlmostEqual(off["shift_s"], -0.1, delta=0.012)

    def test_music_offset_puts_cuts_on_beats_in_qc(self):
        edl = {"version": 1, "title": "Synthetic beat fixture", "format": {"width": 320, "height": 180, "fps": 30},
               "sources": {"V": "raw/voice.mp4", "B": "raw/bars.mp4"},
               "clips": [{"id": "C01", "source": "V", "in": 0.0, "out": 0.9},
                         {"id": "C02", "source": "B", "in": 0.0, "out": 1.0},
                         {"id": "C03", "source": "V", "in": 2.0, "out": 3.1}],
               "audio": {"music": {"file": "raw/kicks.wav", "gain_db": -10, "start": 0.0, "fade_out": 0}},
               "master": {"lufs": -14, "true_peak": -1}}
        write_json(self.edit / "edl.json", edl)
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["music-offset", str(self.edit)]), 0)
            self.assertEqual(main(["sound-cues", str(self.edit)]), 0)
        import json
        text = out.getvalue()
        best = json.loads(text[:text.index("\n}\n") + 2])
        self.assertLessEqual(best["median_error_ms"], 1000 / 30.0, best)
        edl["audio"]["music"]["start"] = best["start"]
        write_json(self.edit / "edl.json", edl)
        E.storyboard(self.edit)
        E.approve(self.edit, "synthetic fixture approval")
        R.render(self.edit, preview=False)
        record = R.qc(self.edit)
        checks = {c["check"]: c for c in record["checks"]}
        self.assertEqual(checks["cut-to-beat"]["result"], "pass", checks["cut-to-beat"])
        music = record["measured"]["sound"]["music"]
        self.assertLessEqual(music["median_error_ms"], 1000 / 30.0)
        self.assertEqual(len(music["per_cut"]), 2)
        self.assertIn("offbeat", music)


if __name__ == "__main__":
    unittest.main()
