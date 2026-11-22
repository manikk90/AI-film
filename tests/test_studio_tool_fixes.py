"""Regression tests for the studio tools review fixes: font faces before READY, one word-timing format, strict
Openverse licence checks, rotation-aware video sizes, renderer --stills/--size, lead-in sound cues, digits in an
alignment script, per-speaker mouth curves and audio/video sync in frame_check.

Every page, clip, tone and script here is a SYNTHETIC FIXTURE written by the test, not a film asset."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STUDIO = REPO / "studio"
FONTS = STUDIO / "fonts"
sys.path.insert(0, str(STUDIO))

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
HAS_NUMPY = importlib.util.find_spec("numpy") is not None


def has_playwright() -> bool:
    if not shutil.which("node"):
        return False
    return subprocess.run(["node", "-e", "require('playwright')"], capture_output=True).returncode == 0


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def rotated_clip(tmp: Path) -> Path:
    """A 320x180 clip stored landscape with a 90 degree display rotation: what a phone writes for portrait video."""
    ff("-f", "lavfi", "-i", "testsrc=s=320x180:d=1:r=10", "-pix_fmt", "yuv420p", str(tmp / "flat.mp4"))
    ff("-display_rotation", "90", "-i", str(tmp / "flat.mp4"), "-c", "copy", str(tmp / "rot.mp4"))
    return tmp / "rot.mp4"


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- 2, 15: one word-timing format; mouth curve per speaker --------------------------------------------------------
class WordFormatTest(unittest.TestCase):
    def test_word_timing_writes_both_key_sets(self):
        src = (STUDIO / "word_timing.py").read_text(encoding="utf-8")
        self.assertIn('"text": w["w"], "start": w["s"], "end": w["e"]', src)

    @unittest.skipUnless(HAS_NUMPY, "mouth_curve needs numpy")
    def test_mouth_curve_reads_both_formats_and_filters_a_speaker(self):
        import mouth_curve as M
        mms = {"words": [{"text": "a", "start": 0.1, "end": 0.3, "speaker": "RAM"},
                         {"text": "b", "start": 0.5, "end": 0.8, "speaker": "SITA"}]}
        kokoro = {"words": [{"w": "a", "s": 0.1, "e": 0.3, "line": 1}]}
        self.assertEqual(M.word_spans(mms), [(0.1, 0.3), (0.5, 0.8)])
        self.assertEqual(M.word_spans(kokoro), [(0.1, 0.3)])
        self.assertEqual(M.word_spans(mms, "SITA"), [(0.5, 0.8)])
        self.assertEqual(M.word_spans(mms, "NOBODY"), [])


# --- 3: Openverse licence check --------------------------------------------------------------------------------------
class LicenceVerdictTest(unittest.TestCase):
    def setUp(self):
        import openverse_audio as O
        self.v = O.licence_verdict

    def test_any_other_licence_link_is_a_mismatch_even_next_to_the_expected_one(self):
        page = ('<a href="https://creativecommons.org/publicdomain/zero/1.0/">filter: CC0</a>'
                '<a href="https://creativecommons.org/licenses/by-nc/4.0/">This work: BY-NC</a>')
        self.assertEqual(self.v(page, "cc0"), "mismatch")
        self.assertEqual(self.v('<a href="https://creativecommons.org/licenses/by-sa/4.0/">x</a>', "by"), "mismatch")
        self.assertEqual(self.v('<p>Attribution NonCommercial</p><a href="https://creativecommons.org/licenses/by/4.0/">',
                                "by"), "mismatch")

    def test_only_the_expected_link_verifies_and_plain_text_does_not(self):
        self.assertEqual(self.v('<a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0</a>', "cc0"), "verified")
        self.assertEqual(self.v('<a href="http://creativecommons.org/licenses/by/3.0/">BY</a>', "by"), "verified")
        self.assertIsNone(self.v("<p>Creative Commons 0, public domain</p>", "cc0"))
        self.assertIsNone(self.v("", "cc0"))


# --- 4/5: rotation-aware sizes ----------------------------------------------------------------------------------------
@unittest.skipUnless(HAS_FFMPEG, "needs FFmpeg")
class RotationTest(unittest.TestCase):
    def test_every_frame_tool_sees_the_displayed_size(self):
        import media_probe
        import whatsapp_copy
        with tempfile.TemporaryDirectory() as tmp:
            clip = rotated_clip(Path(tmp))
            self.assertEqual(media_probe.displayed_size(str(clip)), (180, 320, 90))
            self.assertTrue(whatsapp_copy.is_portrait(str(clip)))
            covers = load_script(REPO / ".claude/skills/thumbnail-cover/scripts/covers.py", "covers_t")
            self.assertEqual(covers.displayed_size(str(clip)), (180, 320))
            for p in (STUDIO / "skill_sources/flicker-edit/scripts/flicker.py",
                      REPO / ".claude/skills/flicker-edit/scripts/flicker.py"):
                if p.is_file() and HAS_NUMPY and importlib.util.find_spec("PIL"):
                    self.assertEqual(load_script(p, "flicker_t").probe(clip), (180, 320), p)
            if HAS_NUMPY:
                import person_matte
                first = next(person_matte.frames(str(clip), 10))
                self.assertEqual(first.shape[:2], (320, 180))  # rows = height: decoded upright, not sheared

    def test_frame_check_size_is_the_displayed_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            clip = rotated_clip(Path(tmp))
            r = subprocess.run([sys.executable, str(STUDIO / "frame_check.py"), str(clip), "--silent",
                                "--size", "180x320"], capture_output=True, text=True)
            self.assertNotIn("size", r.stdout + r.stderr.replace("--size", ""))


# --- 13: lead-in cue ---------------------------------------------------------------------------------------------------
@unittest.skipUnless(HAS_NUMPY, "needs numpy")
class LeadInCueTest(unittest.TestCase):
    def test_a_cue_before_zero_keeps_its_tail(self):
        import sfx
        bed = sfx.place([{"t": -0.2, "sfx": "whoosh", "seed": 1}], dur=1.0, engine="code")
        self.assertEqual(len(bed), sfx.SR)
        self.assertGreater(float(abs(bed[: int(0.2 * sfx.SR)]).max()), 0.0)
        gone = sfx.place([{"t": -5, "sfx": "pop"}], dur=1.0, engine="code")
        self.assertEqual(float(abs(gone).max()), 0.0)


# --- 14: digits in an alignment script -----------------------------------------------------------------------------------
class UnspokenTest(unittest.TestCase):
    def test_digits_and_currency_are_refused_before_any_model_loads(self):
        import mms_align
        with tempfile.TemporaryDirectory() as tmp:
            txt = Path(tmp) / "lines.txt"
            txt.write_text("RAM|सिर्फ ₹500 में\nSITA|साल 2024 था, sach\nplain words only\n", encoding="utf-8")
            self.assertEqual(mms_align.unspoken(mms_align.parse_lines(str(txt))), ["₹500", "2024"])
            r = subprocess.run([sys.executable, str(STUDIO / "mms_align.py"), "none.wav", str(txt), str(Path(tmp) / "o")],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("₹500", r.stderr)
            self.assertIn("2024", r.stderr)
            self.assertNotIn("torch", r.stderr)


# --- 18: audio/video sync in frame_check ---------------------------------------------------------------------------------
@unittest.skipUnless(HAS_FFMPEG and HAS_NUMPY, "needs FFmpeg and numpy")
class SyncTest(unittest.TestCase):
    def test_a_shifted_soundtrack_fails_and_a_true_one_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            # a click every 0.37 s, irregular enough that a shifted copy correlates at one lag only
            ff("-f", "lavfi", "-i", "aevalsrc='if(lt(mod(t*7.3,2.7),0.05),sin(2*PI*900*t),0)':s=48000:d=3",
               str(t / "src.wav"))
            ff("-f", "lavfi", "-i", "color=c=gray:s=160x90:d=3:r=30", "-i", str(t / "src.wav"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(t / "good.mp4"))
            ff("-f", "lavfi", "-i", "color=c=gray:s=160x90:d=3:r=30", "-i", str(t / "src.wav"), "-filter_complex",
               "[1:a]adelay=250|250,atrim=0:3[a]", "-map", "0:v", "-map", "[a]",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(t / "late.mp4"))
            import frame_check
            self.assertLess(abs(frame_check.audio_offset(str(t / "good.mp4"), str(t / "src.wav"))), 0.04)
            self.assertAlmostEqual(frame_check.audio_offset(str(t / "late.mp4"), str(t / "src.wav")), 0.25, delta=0.03)
            r = subprocess.run([sys.executable, str(STUDIO / "frame_check.py"), str(t / "late.mp4"),
                                "--audio", str(t / "src.wav")], capture_output=True, text=True)
            self.assertIn("shifted", r.stdout + r.stderr)


# --- 1, 2, 8, 9: canvas kit and renderer (Chromium) ------------------------------------------------------------------------
PAGE = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="{fonts}/fonts.css">
<canvas width="320" height="180"></canvas>
<script src="{kit}"></script>
<script>
window.FILM = {{ DUR: 4, {setsize} init() {{}}, render(ctx, t) {{
  ctx.fillStyle = `rgb(${{Math.round(t * 60)}},40,90)`; ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}} }};
</script>"""
SETSIZE = "setSize(w, h) { const c = document.querySelector('canvas'); c.width = w; c.height = h; },"
CHECK = r"""
const { chromium } = require('playwright');
const { launchOptions } = require(process.argv[3]);
(async () => {
  const b = await chromium.launch(launchOptions());
  const p = await b.newPage();
  await p.goto('file://' + process.argv[2]);
  await p.waitForFunction(() => window.READY === true || window.READY_ERROR, null, { timeout: 60000 });
  const out = await p.evaluate(() => {
    const K = STUDIO;
    const notLoaded = [...document.fonts].filter(f => f.status !== 'loaded').map(f => `${f.family} ${f.weight} ${f.style}`);
    const kokoro = K.chunks({ words: [{w:'a',s:0,e:.2,line:1},{w:'b',s:.2,e:.4,line:1},{w:'c',s:.4,e:.6,line:2}] }, 3);
    return { notLoaded, n: kokoro.length, first: kokoro[0].start, end: kokoro[0].end, text: kokoro[0].words[1].text };
  });
  await b.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
"""


@unittest.skipUnless(has_playwright(), "needs Node and Playwright")
class CanvasTest(unittest.TestCase):
    def page(self, tmp: Path, setsize: str = "") -> Path:
        p = tmp / "page.html"
        p.write_text(PAGE.format(fonts=FONTS.as_uri(), kit=(STUDIO / "canvas_kit.js").as_uri(), setsize=setsize),
                     encoding="utf-8")
        return p

    def render(self, *args):
        return subprocess.run(["node", str(STUDIO / "render_canvas.cjs"), *map(str, args)],
                              capture_output=True, text=True, timeout=180)

    def test_every_font_face_is_loaded_and_chunks_read_word_timing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp) / "check.cjs"
            check.write_text(CHECK, encoding="utf-8")
            r = subprocess.run(["node", str(check), str(self.page(Path(tmp))), str(STUDIO / "chromium.cjs")],
                               capture_output=True, text=True, timeout=120, cwd=str(REPO))
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertEqual(out["notLoaded"], [])  # bold and italic faces too, not only the regular one
            self.assertEqual((out["n"], out["first"], out["end"], out["text"]), (2, 0, 0.4, "b"))

    def test_named_stills_and_a_still_past_the_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = self.page(Path(tmp))
            r = self.render(page, Path(tmp) / "s", "--stills", "hook,mid,end")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("t=1s", r.stdout)
            self.assertIn("t=2s", r.stdout)
            self.assertIn("t=3.5s", r.stdout)
            r = self.render(page, Path(tmp) / "x", "--stills", "1,9")
            self.assertEqual(r.returncode, 2)
            self.assertIn("past the end", r.stderr)
            self.assertFalse((Path(tmp) / "x_1.png").exists())

    def test_size_resizes_through_setsize_or_stops(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            r = self.render(self.page(Path(tmp)), Path(tmp) / "a", "--size", "180x320", "--stills", "1")
            self.assertEqual(r.returncode, 2)
            self.assertIn("FILM.setSize", r.stderr)
            r = self.render(self.page(Path(tmp), SETSIZE), Path(tmp) / "b", "--size", "180x320", "--stills", "1")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(Image.open(Path(tmp) / "b_1.png").size, (180, 320))
            r = self.render(self.page(Path(tmp)), Path(tmp) / "c", "--stills", "1")  # no --size: the page's own size
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(Image.open(Path(tmp) / "c_1.png").size, (320, 180))


if __name__ == "__main__":
    unittest.main()
