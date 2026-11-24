"""Checks for the studio's own skills built on the canvas kit: /living-painting (presets, template, loop QC) and
/thumbnail-cover (frame pick, covers). Videos and frames here are SYNTHETIC FIXTURES made with FFmpeg or the template."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LP = REPO / ".claude" / "skills" / "living-painting"
TC = REPO / ".claude" / "skills" / "thumbnail-cover"
FF = shutil.which("ffmpeg") and shutil.which("ffprobe")


def has_playwright() -> bool:
    if not shutil.which("node"):
        return False
    return subprocess.run(["node", "-e", "require('playwright')"], capture_output=True).returncode == 0


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


class LivingPaintingTest(unittest.TestCase):
    def test_skill_and_presets_are_complete_and_original(self):
        md = (LP / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(md.startswith("---\nname: living-painting\n"))
        for path in re.findall(r"(?:studio|\.claude/skills/living-painting)/[\w/.-]+\.(?:py|cjs|js|css|json)", md):
            self.assertTrue((REPO / path).exists(), path)
        presets = {k: v for k, v in json.loads((LP / "presets.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
        self.assertGreaterEqual(len(presets), 14)
        for k, v in presets.items():
            self.assertEqual(set(v), {"name", "scene", "medium", "action", "motion"}, k)
        text = json.dumps(presets).lower()
        for banned in ["ghibli", "studio ghibli", "koi", "humpback"]:  # no studio names; scenes are our own
            self.assertNotIn(banned, text, banned)
        self.assertIn("learn.skaleout.com", md)  # the method is credited

    def test_new_painting_writes_the_page_and_never_overwrites(self):
        np_ = load(LP / "scripts" / "new_painting.py", "new_painting")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(np_.main(["demo", "madhubani", "--root", tmp]), 0)
            page = Path(tmp) / "demo" / "painting.html"
            html = page.read_text(encoding="utf-8")
            self.assertNotIn("__STUDIO__", html)
            self.assertIn("BRIEF (Madhubani)", html)
            for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
                self.assertTrue((page.parent / ref).resolve().exists(), ref)
            with self.assertRaises(SystemExit):
                np_.main(["demo", "madhubani", "--root", tmp])
            with self.assertRaises(SystemExit):
                np_.main(["x", "custom", "--root", tmp])  # custom needs a scene and a medium

    @unittest.skipUnless(FF and importlib.util.find_spec("numpy"), "needs FFmpeg and numpy")
    def test_loop_check_separates_a_good_loop_from_broken_ones(self):
        lc = load(LP / "scripts" / "loop_check.py", "loop_check")
        with tempfile.TemporaryDirectory() as tmp:
            good, still, seam = (Path(tmp) / n for n in ("good.mp4", "still.mp4", "seam.mp4"))
            # good: stripes over the whole frame that travel exactly one stripe period in 6 s, so the end meets the start
            ff("-f", "lavfi", "-i", "color=black:s=216x384:r=30:d=6", "-vf",
               "geq=lum='128+90*sin(2*PI*(X/36+Y/64-T/6))':cb=128:cr=128", "-pix_fmt", "yuv420p", str(good))
            # still: only the top half moves
            ff("-f", "lavfi", "-i", "testsrc2=s=216x192:r=30:d=6", "-f", "lavfi", "-i", "color=gray:s=216x192:r=30:d=6",
               "-filter_complex", "[0][1]vstack", "-pix_fmt", "yuv420p", str(still))
            # seam: the same stripes drifting a third of a period in 6 s, so the last frame never meets the first.
            # (Built with geq, not the gradients source, whose drift speed differs between FFmpeg builds.)
            ff("-f", "lavfi", "-i", "color=black:s=216x384:r=30:d=6", "-vf",
               "geq=lum='128+90*sin(2*PI*(X/36+Y/64-T/18))':cb=128:cr=128", "-pix_fmt", "yuv420p", str(seam))
            r_good = lc.check(lc.frames(str(good)))
            self.assertNotIn("seam", r_good["fails"], r_good)
            self.assertNotIn("still", r_good["fails"], r_good)
            self.assertIn("still", lc.check(lc.frames(str(still)))["fails"])
            self.assertIn("seam", lc.check(lc.frames(str(seam)))["fails"])

    @unittest.skipUnless(has_playwright() and FF, "needs Node, Playwright and FFmpeg")
    def test_template_renders_a_clean_seamless_loop(self):
        np_ = load(LP / "scripts" / "new_painting.py", "new_painting")
        lc = load(LP / "scripts" / "loop_check.py", "loop_check")
        with tempfile.TemporaryDirectory() as tmp:
            np_.main(["demo", "sumi_e", "--root", tmp])
            page, out = Path(tmp) / "demo" / "painting.html", Path(tmp) / "loop.mp4"
            # a 2 s slice at low resolution keeps the test quick; the loop maths is the same
            r = subprocess.run(["node", str(REPO / "studio" / "render_canvas.cjs"), str(page), str(out),
                                "--size", "1080x1920", "--fps", "10"], capture_output=True, text=True, timeout=400)
            self.assertEqual(r.returncode, 0, r.stderr)
            res = lc.check(lc.frames(str(out)))
            self.assertEqual(res["fails"], [], res)


class ThumbnailCoverTest(unittest.TestCase):
    def test_skill_points_at_real_files(self):
        md = (TC / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(md.startswith("---\nname: thumbnail-cover\n"))
        for path in re.findall(r"(?:studio|\.claude/skills/thumbnail-cover)/[\w/.-]+\.(?:py|cjs|js|css)", md):
            self.assertTrue((REPO / path).exists(), path)

    @unittest.skipUnless(FF and importlib.util.find_spec("numpy") and importlib.util.find_spec("PIL"), "needs FFmpeg, numpy, Pillow")
    def test_pick_prefers_sharp_frames_and_skips_cuts(self):
        cv = load(TC / "scripts" / "covers.py", "covers")
        with tempfile.TemporaryDirectory() as tmp:
            v = Path(tmp) / "v.mp4"  # 0-2 s blurry, 2-4 s sharp detail
            ff("-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=2", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=2",
               "-filter_complex", "[0]gblur=sigma=12[a];[a][1]concat=n=2:v=1", "-pix_fmt", "yuv420p", str(v))
            res = cv.pick(str(v), Path(tmp) / "out", n=2)
            self.assertEqual(len(res), 2)
            self.assertTrue(all(r["t"] >= 2.0 for r in res), res)
            self.assertTrue((Path(tmp) / "out" / "sheet.png").exists())

    @unittest.skipUnless(has_playwright() and importlib.util.find_spec("PIL"), "needs Node, Playwright and Pillow")
    def test_make_writes_six_covers_at_the_right_sizes(self):
        cv = load(TC / "scripts" / "covers.py", "covers")
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            frame = Path(tmp) / "f.png"
            Image.new("RGB", (1280, 720), (40, 90, 140)).save(frame)
            files = cv.make(str(frame), "मौत से डर लगता है?", Path(tmp) / "c", sub="test fixture")
            self.assertEqual(len(files), 6)
            for f in files:
                im = Image.open(f)
                self.assertEqual(im.size, (1080, 1920) if "reel" in f.name else (1280, 720), f.name)
                self.assertGreater(len(set(im.convert("L").resize((60, 60)).getdata())), 8, f.name)  # text was drawn
            with self.assertRaises(SystemExit):
                cv.make(str(frame), "again", Path(tmp) / "c")  # never overwrites without force


if __name__ == "__main__":
    unittest.main()


class ReviewFixesTest(unittest.TestCase):
    """Regression tests for the PR #22 review findings. All inputs are SYNTHETIC FIXTURES."""

    def test_new_painting_guards_the_brief_too(self):
        np_ = load(LP / "scripts" / "new_painting.py", "new_painting")
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "demo"
            d.mkdir()
            (d / "brief.json").write_text('{"owner": "edited"}')
            with self.assertRaises(SystemExit):
                np_.main(["demo", "warli", "--root", tmp])
            self.assertEqual((d / "brief.json").read_text(), '{"owner": "edited"}')

    @unittest.skipUnless(FF and importlib.util.find_spec("PIL"), "needs FFmpeg and Pillow")
    def test_pick_refuses_to_overwrite_and_force_clears_stale_candidates(self):
        cv = load(TC / "scripts" / "covers.py", "covers")
        with tempfile.TemporaryDirectory() as tmp:
            v, out = Path(tmp) / "v.mp4", Path(tmp) / "out"
            ff("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=6", "-pix_fmt", "yuv420p", str(v))
            self.assertEqual(len(cv.pick(str(v), out, n=4)), 4)
            with self.assertRaises(SystemExit):
                cv.pick(str(v), out, n=2)
            self.assertEqual(len(list(out.glob("cand_*.png"))), 4)  # nothing touched
            self.assertEqual(len(cv.pick(str(v), out, n=2, force=True)), 2)
            self.assertEqual(sorted(p.name for p in out.glob("cand_*.png")), ["cand_01.png", "cand_02.png"])

    @unittest.skipUnless(importlib.util.find_spec("PIL") and importlib.util.find_spec("numpy"), "needs Pillow and numpy")
    def test_oversize_youtube_thumbnail_becomes_a_jpeg_under_2_mb(self):
        import numpy as np
        from PIL import Image
        cv = load(TC / "scripts" / "covers.py", "covers")
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "thumb_yt_A.png"
            Image.fromarray(np.random.default_rng(1).integers(0, 255, (720, 1280, 3), dtype=np.uint8)).save(png)
            self.assertGreater(png.stat().st_size, cv.YT_MAX)  # pure noise PNG: ~2.7 MB
            out = cv._fit_youtube(png)
            self.assertEqual(out.suffix, ".jpg")
            self.assertLessEqual(out.stat().st_size, cv.YT_MAX)
            self.assertFalse(png.exists())

    @unittest.skipUnless(has_playwright(), "needs Node and Playwright")
    def test_renderer_fails_fast_with_the_page_error(self):
        import time
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "p.html"
            page.write_text(f'<!doctype html><canvas width=64 height=64></canvas><script src="{(REPO / "studio" / "canvas_kit.js").as_uri()}"></script>'
                            '<script>STUDIO.FONTS=[];STUDIO.whenReady(async()=>{await STUDIO.loadImage("missing.png")});'
                            'window.FILM={DUR:1,init(){},render(){}};</script>', encoding="utf-8")
            t0 = time.time()
            r = subprocess.run(["node", str(REPO / "studio" / "render_canvas.cjs"), str(page), str(Path(tmp) / "s"),
                                "--size", "64x64", "--stills", "0"], capture_output=True, text=True, timeout=90)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("missing.png", r.stderr)
            self.assertLess(time.time() - t0, 40)  # not the 60 s wait timeout


@unittest.skipUnless(FF, "needs FFmpeg")
class FrameCheckSilentTest(unittest.TestCase):
    def test_silent_rejects_a_video_with_audio_and_cannot_take_audio(self):
        sys.path.insert(0, str(REPO / "studio"))
        import frame_check
        with tempfile.TemporaryDirectory() as tmp:
            quiet, loud = Path(tmp) / "q.mp4", Path(tmp) / "l.mp4"
            ff("-f", "lavfi", "-i", "testsrc2=s=160x90:r=30:d=1", "-pix_fmt", "yuv420p", str(quiet))
            ff("-f", "lavfi", "-i", "testsrc2=s=160x90:r=30:d=1", "-f", "lavfi", "-i", "sine=d=1", "-shortest",
               "-pix_fmt", "yuv420p", str(loud))
            self.assertEqual(frame_check.main([str(quiet), "--silent"]), 0)
            self.assertEqual(frame_check.main([str(loud), "--silent"]), 1)
            with self.assertRaises(SystemExit):
                frame_check.main([str(quiet), "--silent", "--audio", str(loud)])


class SmallFixesTest(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("numpy"), "needs numpy")
    def test_short_shutter_fits_its_length(self):
        sys.path.insert(0, str(REPO / "studio"))
        import sfx
        for length in (0.03, 0.1, 0.12):
            x = sfx.make("shutter", length=length)
            self.assertEqual(len(x), int(length * sfx.SR))

    @unittest.skipUnless(importlib.util.find_spec("cv2"), "needs OpenCV")
    def test_reframe_needs_both_face_cascades(self):
        from aifilm.editor import reframe as R
        import cv2
        own = Path(getattr(getattr(cv2, "data", None), "haarcascades", "") or "/nonexistent")
        if (own / "haarcascade_frontalface_default.xml").exists():
            self.skipTest("this OpenCV ships its own cascades")
        saved = R.CACHE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            try:
                R.CACHE_DIR = Path(tmp)
                (Path(tmp) / "haarcascade_frontalface_default.xml").write_text("synthetic placeholder")
                self.assertFalse(R.available())  # profile cascade missing
                (Path(tmp) / "haarcascade_profileface.xml").write_text("synthetic placeholder")
                self.assertTrue(R.available())
            finally:
                R.CACHE_DIR = saved
