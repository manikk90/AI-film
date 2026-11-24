"""Speaker / overlay / cover planning, face clearance, clip rubric, snap_clip and motion timing.

All inputs are SYNTHETIC FIXTURES: hand-written word timings, made-up EDL timelines and a white
square on a dark FFmpeg frame standing in for a face (a stand-in detector finds it). They prove
the rules' mechanics, not edit quality."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from aifilm.core import read_json, write_json
from aifilm.editor import edl as E
from aifilm.editor import motion as MO
from aifilm.editor import treatment as TR

REPO = Path(__file__).resolve().parents[1]
HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + [str(a) for a in args], check=True, timeout=120)


def words_of(spec):
    """SYNTHETIC word timings from [(start, end, word)]."""
    return [{"start": a, "end": b, "word": w} for a, b, w in spec]


def timeline_edl(beats):
    """SYNTHETIC EDL: one source, one clip per (seconds, treatment) beat, no media needed."""
    clips, cursor = [], 0.0
    for i, (dur, treat) in enumerate(beats, 1):
        clip = {"id": "C{:02d}".format(i), "source": "A", "in": cursor, "out": cursor + dur}
        if treat:
            clip["treatment"] = treat
        clips.append(clip)
        cursor += dur
    return {"version": 1, "format": {"width": 1080, "height": 1920, "fps": 30}, "sources": {"A": "raw/a.mp4"}, "clips": clips}


def rhythm(edl):
    return {name: ok for name, ok, _ in TR.rhythm_findings(edl)}


class RhythmTest(unittest.TestCase):
    def test_nine_second_speaker_run_fails(self):
        r = rhythm(timeline_edl([(9.0, "speaker"), (4.0, "cover"), (3.0, "speaker")]))
        self.assertFalse(r["speaker-only run"])

    def test_eight_second_run_and_clean_rhythm_pass(self):
        r = rhythm(timeline_edl([(4.0, "speaker"), (4.0, "overlay"), (4.0, "cover"), (2.5, "speaker"), (4.0, "cover"), (3.0, "speaker")]))
        self.assertTrue(all(r.values()), r)

    def test_two_second_cover_fails(self):
        r = rhythm(timeline_edl([(3.0, "speaker"), (2.0, "cover"), (3.0, "speaker")]))
        self.assertFalse(r["cover length"])

    def test_covers_need_face_time_between(self):
        r = rhythm(timeline_edl([(3.0, "speaker"), (3.0, "cover"), (1.0, "speaker"), (3.0, "cover"), (3.0, "speaker")]))
        self.assertFalse(r["face between covers"])

    def test_open_and_close_on_the_speaker(self):
        self.assertFalse(rhythm(timeline_edl([(3.0, "cover"), (3.0, "speaker")]))["open and close on the speaker"])
        self.assertFalse(rhythm(timeline_edl([(3.0, "speaker"), (3.0, "overlay")]))["open and close on the speaker"])

    def test_inserts_count_as_cover_and_legacy_edls_are_untouched(self):
        edl = timeline_edl([(10.0, "speaker")])
        edl["clips"][0]["inserts"] = [{"source": "A", "in": 0, "out": 4, "at": 3.0}]
        segs = TR.segments(edl)
        self.assertEqual([s["kind"] for s in segs], ["speaker", "cover", "speaker"])
        self.assertTrue(rhythm(edl)["speaker-only run"])
        self.assertEqual(TR.rhythm_findings(timeline_edl([(20.0, None)])), [])


class FaceOverlapTest(unittest.TestCase):
    """SYNTHETIC face samples and boxes in output pixels (1080x1920)."""
    face = [{"t": 1.0, "x": 0.5, "y": 0.35, "size": 0.15}]

    def test_overlay_on_face_box_fails_and_clear_one_passes(self):
        on = {"name": "on face", "start": 0.5, "end": 2.0, "box": {"x0": 300, "x1": 800, "y0": 600, "y1": 760}}
        off = {"name": "low", "start": 0.5, "end": 2.0, "box": {"x0": 100, "x1": 980, "y0": 1300, "y1": 1450}}
        later = dict(on, name="later", start=3.0, end=4.0)
        hits = TR.faces_over([on, off, later], self.face, 1080, 1920)
        self.assertEqual([h[0] for h in hits], ["on face"])


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is required for media tests")
class FaceClearCraftCase(unittest.TestCase):
    """SYNTHETIC fixture: a white square ('the face') on a dark 16:9 frame; a stand-in detector
    finds the square, so craft-check runs on Mann's real reframe face track."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = Path(tempfile.mkdtemp(prefix="mann-face-"))
        ff("-f", "lavfi", "-i", "color=c=0x202020:s=640x360:r=30:d=4", "-f", "lavfi", "-i", "color=c=white:s=120x120:r=30:d=4",
           "-filter_complex", "[0][1]overlay=x=260:y=60", "-c:v", "libx264", "-pix_fmt", "yuv420p", cls.fixtures / "face.mp4")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fixtures, ignore_errors=True)

    def setUp(self):
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy is required for face tracking")
        from aifilm.editor import reframe as RF
        from aifilm.editor import tools as T
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.edit = Path(self.temp.name) / "edit"
        T.ingest(self.edit, [self.fixtures / "face.mp4"])

        def bright_box(gray):
            import numpy as np
            ys, xs = np.nonzero(gray > 200)
            return [(int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))] if len(xs) else []
        original = RF.detect
        RF.detect = bright_box
        self.addCleanup(setattr, RF, "detect", original)

    def found(self, text_position, overlay_bbox):
        from aifilm.editor import craft as C
        edl = {"version": 1, "format": {"width": 360, "height": 640, "fps": 30, "reframe": "auto"}, "sources": {"A": "raw/face.mp4"},
               "clips": [{"id": "C01", "source": "A", "in": 0, "out": 4, "treatment": "overlay", "timing": "lead",
                          "text": {"value": "Teen baatein", "role": "headline", "position": text_position}}],
               "overlays": [{"file": "mg/none.mov", "at": 0.5, "duration": 1.0, "bbox": overlay_bbox}]}
        write_json(self.edit / "edl.json", edl)
        return {f["check"]: f for f in C.check(self.edit, edl, sample_contrast=False)}

    def test_text_or_overlay_on_the_face_fails(self):
        r = self.found("center", [0.05, 0.6, 0.95, 0.7])
        self.assertEqual(r["nothing over the face"]["result"], "fail", r["nothing over the face"])
        self.assertIn("text C01", r["nothing over the face"]["detail"])
        r = self.found("bottom", [0.2, 0.25, 0.8, 0.5])
        self.assertEqual(r["nothing over the face"]["result"], "fail")
        self.assertIn("overlay", r["nothing over the face"]["detail"])

    def test_items_clear_of_the_face_pass(self):
        r = self.found("bottom", [0.05, 0.6, 0.95, 0.65])
        self.assertEqual(r["nothing over the face"]["result"], "pass", r["nothing over the face"])


class TimingTest(unittest.TestCase):
    def test_lead_sync_wait(self):
        self.assertAlmostEqual(TR.overlay_at("lead", 2.0, fps=30), 1.8)
        self.assertAlmostEqual(TR.overlay_at("sync", 2.0, anchor=2.51, fps=30), 2.5)
        self.assertAlmostEqual(TR.overlay_at("wait", 2.0, anchor=3.2, fps=30), 3.2)
        self.assertEqual(TR.overlay_at("lead", 0.05), 0.0)
        with self.assertRaises(E.ProductionError):
            TR.overlay_at("early", 1.0)

    def test_plan_opens_and_closes_on_speaker_and_breaks_long_runs(self):
        lines = [{"start": 0, "end": 3, "text": "Aaj ek kahani."}, {"start": 3, "end": 7.5, "text": "Main gaon gaya tha."},
                 {"start": 7.5, "end": 11, "text": "Wahan sab badal gaya tha."}, {"start": 11, "end": 13, "text": "Teen saal mein."},
                 {"start": 13, "end": 16, "text": "Bas yahi baat hai."}]
        rows = TR.plan(lines)
        self.assertEqual((rows[0]["treatment"], rows[-1]["treatment"]), ("speaker", "speaker"))
        edl = timeline_edl([(r["end"] - r["start"], r["treatment"]) for r in rows])
        self.assertTrue(all(ok for _, ok, _ in TR.rhythm_findings(edl)), rows)
        number = next(r for r in rows if r["text"].startswith("Teen"))
        self.assertEqual((number["treatment"], number["timing"]), ("overlay", "sync"))


class ClipScoreTest(unittest.TestCase):
    def test_weights_sum_to_one_and_match_rules(self):
        w = read_json(REPO / "editor" / "rules.json")["rules"]["clip_score_weights"]
        self.assertAlmostEqual(sum(w.values()), 1.0)
        self.assertEqual(w, {"hook": 0.30, "standalone": 0.25, "emotion": 0.20, "value": 0.15, "payoff": 0.10})
        self.assertEqual(TR.score_clip({k: 100 for k in w})["score"], 100.0)
        self.assertEqual(TR.score_clip({"hook": 100})["score"], 30.0)

    def test_ranking_order_and_red_flags(self):
        same = {"hook": 80, "standalone": 80, "emotion": 60, "value": 60, "payoff": 60}
        cands = [
            {"id": "weak", "start": 0, "text": "So today I want to talk about things.", "scores": {"hook": 20, "standalone": 70, "emotion": 30, "value": 40, "payoff": 30}},
            {"id": "flagged", "start": 10, "text": "As I mentioned earlier, it was the reason and", "scores": same},
            {"id": "clean", "start": 20, "text": "I tested 30 phones and one beat them all.", "scores": same},
            {"id": "hooky", "start": 30, "text": "Nobody tells you this about rent.", "scores": dict(same, hook=95)},
        ]
        ranked = TR.rank_clips(cands)
        self.assertEqual([c["id"] for c in ranked], ["hooky", "clean", "flagged", "weak"])
        flagged = next(c for c in ranked if c["id"] == "flagged")
        self.assertEqual(len(flagged["red_flags"]), 2)
        self.assertIn("ends mid-sentence", flagged["red_flags"])
        self.assertIn("opens on a pronoun with no referent", TR.red_flags("They never came back."))


class SnapClipTest(unittest.TestCase):
    # SYNTHETIC transcript: three sentences with clear gaps.
    W = words_of([(0.0, 0.4, "Hello"), (0.5, 0.9, "there."), (1.6, 1.9, "Money"), (2.0, 2.3, "is"), (2.4, 2.9, "time."),
                  (4.0, 4.3, "But"), (4.4, 4.8, "nobody"), (4.9, 5.4, "listens."), (6.5, 6.9, "Next"), (7.0, 7.4, "one.")])

    def test_start_snaps_to_sentence_start_within_window(self):
        s = TR.snap_clip(self.W, 2.4, 5.0)
        self.assertEqual((s["start"], s["start_snap"]), (1.6, "sentence"))

    def test_start_falls_back_to_nearest_word(self):
        far = words_of([(0.0, 0.3, "One"), (5.0, 5.3, "long"), (5.4, 5.7, "words"), (5.8, 6.1, "run"), (6.2, 6.5, "on.")])
        s = TR.snap_clip(far, 5.75, 6.5)
        self.assertEqual((s["start"], s["start_snap"]), (5.8, "word"))

    def test_end_extends_to_sentence_end_plus_pad(self):
        s = TR.snap_clip(self.W, 1.6, 4.5)
        self.assertEqual((s["end"], s["end_snap"]), (5.7, "sentence"))

    def test_end_pad_never_runs_into_the_next_word(self):
        tight = words_of([(0.0, 0.5, "Short."), (0.6, 1.0, "Next.")])
        self.assertEqual(TR.snap_clip(tight, 0.0, 0.4)["end"], 0.58)

    def test_engine_exposes_snap_clip(self):
        from aifilm.editor import engine as G
        self.assertIs(G.snap_clip, TR.snap_clip)


class MotionTimingTest(unittest.TestCase):
    def test_exit_and_follower_offsets(self):
        self.assertAlmostEqual(MO.exit_seconds(0.6), 0.39)
        self.assertEqual(MO.exit_seconds(0.05), 0.12)
        self.assertEqual([round(MO.follower_offset(i) * 30) for i in range(6)], [0, 4, 9, 15, 22, 30])
        gaps = [round((MO.follower_offset(i + 1) - MO.follower_offset(i)) * 30) for i in range(8)]
        self.assertEqual(len(set(gaps)), len(gaps))  # never an even stagger
        self.assertEqual(MO.timing()["follower_frames"], [0, 4, 9, 15, 22, 30])

    def test_tween_is_seek_safe(self):
        forward = [MO.tween(t / 10.0, 0.2, 0.8, 0, 100) for t in range(11)]
        backward = [MO.tween(t / 10.0, 0.2, 0.8, 0, 100) for t in reversed(range(11))]
        self.assertEqual(forward, list(reversed(backward)))
        self.assertEqual((forward[0], forward[-1]), (0, 100))

    def test_library_follows_the_same_rules(self):
        lib = (REPO / "editor" / "motion" / "lib.js").read_text(encoding="utf-8")
        self.assertIn("exit_ratio: 0.65", lib)
        self.assertIn("follower_frames: [0, 4, 9, 15, 22, 30]", lib)
        self.assertIn("timing", MO.design())


if __name__ == "__main__":
    unittest.main()
