"""Real FFmpeg regressions for cached transitions and sparse storyboard frames.

The clip and approval are synthetic fixtures, not owner media or approval.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from aifilm.core import write_json
from aifilm.editor import edl, media, render, tools


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is required for media tests")
class CachedFrameCompatibilityTest(unittest.TestCase):
    def test_cached_transition_and_sparse_duplicate_frames_at_24fps(self):
        self.check_cached_roundtrip(24)

    def test_cached_transition_preserves_default_fps_when_omitted(self):
        self.check_cached_roundtrip(None)

    def check_cached_roundtrip(self, fps):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "synthetic.mp4"
            subprocess.run([
                "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=4",
                "-f", "lavfi", "-i", "sine=f=300:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-shortest", str(source),
            ], check=True, timeout=60)
            project = base / "edit"
            tools.ingest(project, [source])
            plan = {
                "version": 1,
                "format": {"width": 180, "height": 320},
                "sources": {"A": "raw/synthetic.mp4"},
                "clips": [
                    {"id": "C01", "source": "A", "in": 0, "out": 1.5},
                    {"id": "C02", "source": "A", "in": 1.5, "out": 3,
                     "transition_in": {"type": "dissolve", "duration": 0.25}},
                ],
            }
            if fps is not None:
                plan["format"]["fps"] = fps
            write_json(project / "edl.json", plan)
            edl.storyboard(project)
            edl.approve(project, "synthetic compatibility fixture approval")
            result = render.render(project, preview=False, quality="draft")
            self.assertEqual(result["clips_rendered"], 2)
            info = media.probe(result["master"])
            # MP4 average-rate timestamps can round slightly over a short clip.
            self.assertAlmostEqual(info["fps"], fps or 30, delta=0.02)
            self.assertAlmostEqual(info["duration"], 2.75, delta=0.07)

            # With all clips cached, select a sparse subset rather than running
            # to the end. Duplicates must retain their caller-supplied positions.
            stills = base / "stills"
            stills.mkdir()
            edl.still_frames(project, plan, [6, 48, 6], stills)
            files = sorted(stills.glob(".still-*.jpg"))
            self.assertEqual(len(files), 3)
            self.assertEqual(files[0].read_bytes(), files[2].read_bytes())
            self.assertNotEqual(files[0].read_bytes(), files[1].read_bytes())
            self.assertFalse(list(stills.glob(".all-*.jpg")))


if __name__ == "__main__":
    unittest.main()
