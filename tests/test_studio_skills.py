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
            # seam: a steady slow drift that never comes back (frame 0 and the last frame differ a lot)
            ff("-f", "lavfi", "-i", "gradients=s=216x384:r=30:d=6:speed=0.004:seed=3", "-pix_fmt", "yuv420p", str(seam))
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
