"""Checks for /style-montage and the style/scene split in /living-painting: the 10 new styles, --style, the vendored
three.js and voxel kit, montage plan/check/assemble. The loops assembled here are SYNTHETIC FIXTURES (moving numpy
patterns made with FFmpeg), not rendered style paintings."""

import hashlib
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
SM = REPO / ".claude" / "skills" / "style-montage"
sys.path.insert(0, str(LP / "scripts"))
sys.path.insert(0, str(SM / "scripts"))
import new_painting  # noqa: E402

FF = shutil.which("ffmpeg")
NP = importlib.util.find_spec("numpy") is not None
PIL = importlib.util.find_spec("PIL") is not None
NEW = ["pop_art", "voxel_3d", "risograph", "storybook_gouache", "xray", "candy_world", "vhs_glitch", "ceramic_mosaic",
       "chalkboard", "embroidery"]


def has_playwright():
    if not shutil.which("node"):
        return False
    return subprocess.run(["node", "-e", "require('playwright')"], capture_output=True).returncode == 0


def synth_loop(path, tint, still=False, w=180, h=320, fps=15, dur=4):
    """SYNTHETIC FIXTURE: a seamless moving pattern (or a frozen one) standing in for a rendered style loop."""
    import numpy as np
    n = fps * dur
    yy, xx = np.mgrid[0:h, 0:w]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r",
                          str(fps), "-i", "-", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", str(path)],
                         stdin=subprocess.PIPE)
    for i in range(n):
        u = 0 if still else i / n * 2 * np.pi
        v = 0.5 + 0.5 * np.sin(xx / 12 + u) * np.cos(yy / 15 - u)
        cx, cy = w / 2 + 40 * np.cos(u), h / 2 + 40 * np.sin(u)
        v = np.where((xx - cx) ** 2 + (yy - cy) ** 2 < 20 ** 2, 1.0, v)
        p.stdin.write((v[..., None] * np.array(tint)[None, None, :]).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()


class StylesTest(unittest.TestCase):
    def test_ten_new_styles_are_complete_and_every_preset_is_also_a_style(self):
        styles = json.loads((LP / "styles.json").read_text(encoding="utf-8"))
        self.assertEqual([k for k in styles if not k.startswith("_")], NEW)
        for k in NEW:
            for f in ("name", "engine", "medium", "motion"):
                self.assertTrue(styles[k].get(f), (k, f))
            self.assertIn(styles[k]["engine"], ("canvas", "voxel"))
        allst = new_painting.all_styles()
        for k in ("madhubani", "warli", "miniature", "diwali_gouache"):  # the desi looks are styles too
            self.assertIn(k, allst)
        text = (LP / "styles.json").read_text(encoding="utf-8").lower()
        for name in ("ghibli", "pixar", "disney", "minecraft", "lego", "skale out's prompt"):
            self.assertNotIn(name, text)

    def test_style_replaces_the_look_keeps_the_scene_and_picks_the_engine_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(new_painting.main(["a", "golden_hour", "--style", "voxel_3d", "--root", tmp]), 0)
            brief = json.loads((Path(tmp) / "a" / "brief.json").read_text())
            self.assertIn("kite", brief["scene"])
            self.assertIn("cubes", brief["medium"])
            self.assertEqual(brief["engine"], "voxel")
            page = (Path(tmp) / "a" / "painting.html").read_text()
            self.assertIn("voxel_kit.js", page)
            self.assertIn("third_party/three/three.min.js", page)
            self.assertEqual(new_painting.main(["b", "warli", "--style", "risograph", "--medium", "my own look",
                                                "--root", tmp]), 0)
            self.assertEqual(json.loads((Path(tmp) / "b" / "brief.json").read_text())["medium"], "my own look")
            self.assertEqual(new_painting.main(["c", "custom", "--scene", "a kite", "--style", "chalkboard",
                                                "--root", tmp]), 0)
            self.assertIn("canvas_kit.js", (Path(tmp) / "c" / "painting.html").read_text())
            with self.assertRaises(SystemExit):
                new_painting.main(["d", "warli", "--style", "no_such_style", "--root", tmp])


class VendoredThreeTest(unittest.TestCase):
    def test_three_js_matches_its_recorded_hash_and_carries_its_licence(self):
        d = REPO / "third_party" / "three"
        sha = hashlib.sha256((d / "three.min.js").read_bytes()).hexdigest()
        self.assertIn(sha, (d / "README.md").read_text())
        self.assertIn("MIT License", (d / "LICENSE").read_text())
        kit = (REPO / "studio" / "voxel_kit.js").read_text()
        self.assertIn("preserveDrawingBuffer: true", kit)  # the 2D film canvas copies the GL canvas every frame

    @unittest.skipUnless(FF and NP and has_playwright(), "needs FFmpeg, numpy, Node and Playwright")
    def test_voxel_template_renders_a_seamless_loop_offline(self):
        sys.path.insert(0, str(LP / "scripts"))
        import loop_check
        projects = REPO / "projects"
        with tempfile.TemporaryDirectory(dir=projects if projects.is_dir() else None) as tmp:
            root = Path(tmp)
            self.assertEqual(new_painting.main(["v", "watercolour", "--style", "voxel_3d", "--root", str(root)]), 0)
            out = root / "v" / "loop.mp4"
            r = subprocess.run(["node", str(REPO / "studio" / "render_canvas.cjs"), str(root / "v" / "painting.html"),
                                str(out), "--size", "270x480", "--fps", "10"], capture_output=True, text=True,
                               timeout=600)
            self.assertEqual(r.returncode, 0, r.stderr[-800:])
            res = loop_check.check(loop_check.frames(str(out)))
            self.assertEqual(res["fails"], [], res)
            self.assertEqual(res["frames"], 60)


@unittest.skipUnless(FF and NP and PIL, "needs FFmpeg, numpy and Pillow")
class MontageTest(unittest.TestCase):
    def setUp(self):
        import montage
        self.m = montage
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = montage.projects
        montage.projects = lambda: Path(self.tmp.name)

    def tearDown(self):
        self.m.projects = self.saved
        self.tmp.cleanup()

    def plan_with_loops(self, styles=("pop_art", "voxel_3d", "madhubani"), still=()):
        p = self.m.plan("mt", list(styles), preset="golden_hour")
        tints = [(230, 60, 60), (60, 200, 230), (250, 200, 40), (230, 230, 230)]
        for e, tint in zip(p["styles"], tints):
            synth_loop(Path(self.tmp.name) / "mt" / e["loop"], tint, still=e["style"] in still)
        return p

    def test_plan_writes_one_page_per_style_all_on_the_shared_motion(self):
        p = self.m.plan("mt", ["pop_art", "voxel_3d", "madhubani"], preset="golden_hour")
        root = Path(self.tmp.name) / "mt"
        self.assertIn("window.MOTION", (root / "motion.js").read_text())
        self.assertEqual([e["style"] for e in p["styles"]], ["pop_art", "voxel_3d", "madhubani"])
        for e in p["styles"]:
            html = (root / e["page"]).read_text()
            self.assertEqual(html.count('<script src="../../motion.js"></script>'), 1)
            self.assertLess(html.index("canvas_kit.js"), html.index("motion.js\"></script>"))
        self.assertIn("voxel_kit.js", (root / p["styles"][1]["page"]).read_text())
        self.assertEqual(json.loads((root / "plan.json").read_text())["styles"][2]["name"], "Madhubani")
        with self.assertRaises(SystemExit):
            self.m.plan("mt", ["pop_art", "xray"], preset="golden_hour")  # exists: needs --force
        with self.assertRaises(SystemExit):
            self.m.plan("mt2", ["pop_art"], preset="golden_hour")  # one style is not a montage
        with self.assertRaises(SystemExit):
            self.m.plan("mt3", ["pop_art", "nope"], preset="golden_hour")

    def test_assemble_cuts_on_one_clock_and_writes_the_report(self):
        self.plan_with_loops()
        rep = self.m.assemble("mt", seg=0.8, size="180x320", fps=15)
        segs = rep["segments"]
        self.assertEqual([s["start"] for s in segs], [1.2, 2.0, 2.8])
        for s in segs:  # each style picks up at the same moment of the motion: source = global time mod loop
            self.assertAlmostEqual(s["source_offset"], s["start"] % 4.0, places=3)
        self.assertAlmostEqual(rep["total"], 1.2 + 3 * 0.8 + 1.6, places=3)
        out = Path(self.tmp.name) / "mt" / "montage.mp4"
        info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration",
                                          "-of", "json", str(out)], capture_output=True, text=True).stdout)
        self.assertEqual((info["streams"][0]["width"], info["streams"][0]["height"]), (180, 320))
        self.assertAlmostEqual(float(info["format"]["duration"]), rep["total"], delta=0.1)
        self.assertEqual(len(info["streams"]), 1)  # no song given: no audio track
        self.assertTrue((Path(self.tmp.name) / "mt" / "montage.json").exists())

    def test_a_failing_loop_blocks_the_montage(self):
        self.plan_with_loops(still=("voxel_3d",))
        rows = {r["style"]: r["fails"] for r in self.m.check("mt")}
        self.assertEqual(rows["pop_art"], [])
        self.assertIn("motion", rows["voxel_3d"])
        with self.assertRaises(SystemExit) as e:
            self.m.assemble("mt", size="180x320", fps=15)
        self.assertIn("voxel_3d", str(e.exception))

    def test_beat_cuts_and_a_hindi_hook(self):
        self.plan_with_loops()
        self.assertEqual(self.m.cut_points(3, 1.0, beats=[0.5, 1.0, 1.3, 1.6, 2.2, 2.9, 3.4], every=1),
                         [1.0, 1.6, 2.2, 2.9])  # 1.3 is under the 0.4 s minimum after 1.0
        with self.assertRaises(SystemExit):
            self.m.cut_points(3, 1.0, beats=[1.0, 1.5])
        beats = Path(self.tmp.name) / "beats.json"
        beats.write_text(json.dumps({"beats": [i * 0.5 for i in range(20)]}))
        rep = self.m.assemble("mt", beats=str(beats), every=2, hook="एक scene, तीन अंदाज़", size="180x320", fps=15)
        # beats every 0.5 s, every 2nd from the hook on: the hook stretches to 1.5 s, then cuts at 2.5 and 3.5
        self.assertEqual(rep["hook_dur"], 1.5)
        self.assertEqual([s["start"] for s in rep["segments"]], [1.5, 2.5, 3.5])
        ass = self.m.ass_file(180, 320, "एक scene", 1.0, rep["segments"], 4.0, 1.0, [])
        self.assertIn(",HookDeva,", ass)
        self.assertIn("01  POP ART", ass)
        self.assertNotIn(",HookDeva,", self.m.ass_file(180, 320, "1 PROMPT", 1.0, [], 2.0, 1.0, []))

    def test_audio_lands_in_the_montage_and_an_existing_montage_needs_force(self):
        self.plan_with_loops()
        song = Path(self.tmp.name) / "song.wav"  # SYNTHETIC FIXTURE: a sine tone standing in for a song
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=330:d=12", str(song)], check=True)
        rep = self.m.assemble("mt", audio=str(song), size="180x320", fps=15)
        out = Path(self.tmp.name) / "mt" / "montage.mp4"
        kinds = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True).stdout.split()
        self.assertEqual(sorted(kinds), ["audio", "video"])
        self.assertEqual(rep["audio"], str(song))
        with self.assertRaises(SystemExit) as e:
            self.m.assemble("mt", size="180x320", fps=15)
        self.assertIn("--force", str(e.exception))
        before = out.stat().st_mtime_ns
        self.m.assemble("mt", size="180x320", fps=15, force=True)
        self.assertNotEqual(out.stat().st_mtime_ns, before)
        self.assertFalse(list(out.parent.glob(".montage.part*")))

    def test_duration_and_multiline_briefs_reach_a_valid_motion_js(self):
        self.m.plan("md", ["pop_art", "voxel_3d"], scene="a kite\nover a field", action="it dips\nand climbs", dur=4)
        root = Path(self.tmp.name) / "md"
        js = (root / "motion.js").read_text()
        self.assertIn("DUR: 4,", js)
        self.assertIn("// Scene: a kite over a field", js)
        for e in json.loads((root / "plan.json").read_text())["styles"]:
            self.assertIn("const DUR = (M && M.DUR) || 6;", (root / e["page"]).read_text())  # the page takes MOTION.DUR
        if shutil.which("node"):
            r = subprocess.run(["node", "-e", "global.window={};eval(require('fs').readFileSync(process.argv[1],'utf8'));"
                                "console.log(window.MOTION.DUR, window.MOTION.subject(1).x.toFixed(3))",
                                str(root / "motion.js")],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(r.stdout.startswith("4 "))

    def test_a_busy_project_is_refused(self):
        root = Path(self.tmp.name) / "mb"
        root.mkdir()
        (root / ".production.lock").write_text("12345")  # another plan or assemble holds the project
        with self.assertRaises(SystemExit) as e:
            self.m.plan("mb", ["pop_art", "xray"], preset="golden_hour")
        self.assertIn("busy", str(e.exception))
        self.assertFalse((root / "motion.js").exists())

    def test_skill_points_at_real_files(self):
        md = (SM / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(md.startswith("---\nname: style-montage\n"))
        for path in re.findall(r"(?:studio|\.claude/skills/[\w-]+|third_party/three)/[\w/.-]+\.(?:py|cjs|js|json)", md):
            self.assertTrue((REPO / path).exists(), path)


SYNC_JS = r"""
const { chromium } = require('playwright');
(async () => {
  const [page2d, pageVox] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--enable-unsafe-swiftshader'] });
  const out = {};
  for (const [name, file] of [['canvas', page2d], ['voxel', pageVox]]) {
    const page = await browser.newPage();
    await page.goto('file://' + file);
    await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
    out[name] = await page.evaluate((kind) => {
      const c = document.querySelector('canvas'), ctx = c.getContext('2d'), rows = [];
      FILM.init && FILM.init();
      let seen = null;
      if (kind === 'canvas') {   // where the subject lands on screen: its draw point through the canvas transform
        const real = window.heron;
        window.heron = (cx, x, y, ...rest) => {
          seen = cx.getTransform().transformPoint({ x, y });
          return real(cx, x, y, ...rest);
        };
      }
      for (const t of [0.3, 1.1, 2.6, 3.7]) {
        FILM.render(ctx, t);
        const s = MOTION.subject(t);
        let px, py;
        if (kind === 'canvas') { px = seen.x / c.width; py = seen.y / c.height; }
        else { const v = boat.position.clone(); v.y -= 0.4 * Math.sin(s.phase * Math.PI * 2);
               v.project(V.camera); px = (v.x + 1) / 2; py = (1 - v.y) / 2; }
        rows.push([t, s.x, s.y, px, py]);
      }
      return rows;
    }, name);
  }
  console.log(JSON.stringify(out));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


@unittest.skipUnless(has_playwright(), "needs Node and Playwright")
class MontageSyncTest(unittest.TestCase):
    def test_every_engine_puts_the_subject_on_the_shared_screen_point(self):
        import montage
        projects = REPO / "projects"
        projects.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=projects) as tmp:
            saved = montage.projects
            montage.projects = lambda: Path(tmp)
            try:
                p = montage.plan("sync", ["sumi_e", "voxel_3d"], preset="sumi_e", dur=4)
            finally:
                montage.projects = saved
            root = Path(tmp) / "sync"
            pages = [str(root / e["page"]) for e in p["styles"]]
            script = Path(tmp) / "sync.cjs"
            script.write_text(SYNC_JS)
            r = subprocess.run(["node", str(script), *pages], capture_output=True, text=True, timeout=300,
                               env={**__import__("os").environ, "NODE_PATH": __import__("os").environ.get("NODE_PATH", "")})
            self.assertEqual(r.returncode, 0, r.stderr[-800:])
            got = json.loads(r.stdout)
            for engine, rows in got.items():
                for t, sx, sy, px, py in rows:
                    self.assertAlmostEqual(px, sx, delta=0.01, msg=(engine, t))
                    self.assertAlmostEqual(py, sy, delta=0.01, msg=(engine, t))


if __name__ == "__main__":
    unittest.main()
