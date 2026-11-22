"""Checks for the shared canvas kit (studio/canvas_kit.js), the vendored studio fonts (studio/fonts/) and the code-made
sound effects (studio/sfx.py). The demo page and the cues are SYNTHETIC FIXTURES written by the test."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FONTS = REPO / "studio" / "fonts"
sys.path.insert(0, str(REPO / "studio"))


def has_playwright() -> bool:
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True)
    return r.returncode == 0


DEMO = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="{fonts}/fonts.css">
<canvas width="1080" height="1920"></canvas>
<script src="{kit}"></script>
<script>
const K = STUDIO;
const words = [{{text:'मंज़िल',start:0.2,end:0.6,line:0}},{{text:'क्या',start:0.6,end:0.9,line:0}},
  {{text:'है?',start:0.9,end:1.2,line:0}},{{text:'DEATH.',start:2.0,end:2.6,line:1}}];
const chunks = K.chunks(words, 3);
let paper;
K.whenReady(() => {{ paper = K.paper(1080, 1920, 5); }});
window.FILM = {{ DUR: 3, init() {{}}, render(ctx, t) {{
  ctx.drawImage(paper, 0, 0);
  K.camera(ctx, {{zoom: K.lerp(1, 1.3, K.ease.inOut(t / 3))}}, () => {{
    ctx.fillStyle = '#e5334a'; ctx.beginPath(); ctx.arc(540, 800, 260, 0, 7); ctx.fill();
  }});
  const box = K.caption(ctx, K.chunkAt(chunks, t), t, {{pill: '#ffd400'}});
  window.__safe = K.inSafe(ctx, box);
  if (t > 2) K.burst(ctx, 540, 600, 200, 'POW!', {{seed: 2}});
  K.grain(ctx, t); K.vignette(ctx);
}} }};
</script>"""

CHECK = r"""
const { chromium } = require('playwright');
const { launchOptions } = require(process.argv[3]);
(async () => {
  const b = await chromium.launch(launchOptions());
  const p = await b.newPage();
  const errors = []; p.on('pageerror', e => errors.push(String(e)));
  await p.goto('file://' + process.argv[2]);
  await p.waitForFunction(() => window.READY === true || window.READY_ERROR, null, { timeout: 60000 });
  const out = await p.evaluate(() => {
    const K = STUDIO, r = K.rng(42), a = [r(), r(), r()], r2 = K.rng(42), b2 = [r2(), r2(), r2()];
    const ctx = document.querySelector('canvas').getContext('2d');
    FILM.render(ctx, 0.7);
    const safe = window.__safe;
    return {
      ready: window.READY, error: window.READY_ERROR || null, missing: K.FONTS.filter(f => !document.fonts.check(`40px "${f}"`)),
      seeded: JSON.stringify(a) === JSON.stringify(b2), loop: Math.abs(K.loopWave(0, 6, 2) - K.loopWave(6, 6, 2)) < 1e-9,
      chunks: K.chunks([{text:'a',start:0,end:.2,line:0},{text:'b',start:.2,end:.4,line:0},{text:'c',start:.4,end:.6,line:1}], 3).length,
      ease: [K.ease.outExpo(0), K.ease.outExpo(1), K.tween(5, 0, 1, 0, 10)], safe,
    };
  });
  await b.close();
  console.log(JSON.stringify({ ...out, errors }));
})().catch(e => { console.error(e); process.exit(1); });
"""


class FontsTest(unittest.TestCase):
    def test_every_named_family_is_vendored_with_its_licence(self):
        css = (FONTS / "fonts.css").read_text(encoding="utf-8")
        families = json.loads((FONTS / "families.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(families), 20)
        for fam in families:
            self.assertIn(f'font-family:"{fam}"', css, fam)
        import re
        for f in re.findall(r'url\("([^"]+)"\)', css):
            self.assertTrue((FONTS / f).is_file(), f)
        self.assertEqual(len(list((FONTS / "licenses").glob("*-OFL.txt"))), 20)
        kit = (REPO / "studio" / "canvas_kit.js").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"'([^']+)'", kit.split("K.FONTS = [")[1].split("];")[0])), set(families))

    def test_skill_fonts_are_all_available(self):
        """Every font a format skill names in its steps is one the studio ships."""
        import re
        families = set(json.loads((FONTS / "families.json").read_text(encoding="utf-8")))
        named = set()
        for md in (REPO / ".claude" / "skills").glob("*/SKILL.md"):
            text = md.read_text(encoding="utf-8")
            named |= set(re.findall(r"\b(Yatra One|Bangers|Tiro Devanagari(?: Hindi)?|Rozha One|Kalam|Caveat|Great Vibes|Teko|"
                                    r"Cormorant|Quicksand|EB Garamond|Amatic SC|Instrument Serif|Kaushan Script|"
                                    r"Abril Fatface|Playfair(?: Display)?|Saira Extra Condensed|Caladea)\b", text))
        named = {"Tiro Devanagari Hindi" if n.startswith("Tiro") else "Playfair Display" if n.startswith("Playfair") else n
                 for n in named}
        self.assertTrue(named)
        self.assertFalse(named - families, named - families)


@unittest.skipUnless(has_playwright(), "needs Node and Playwright")
class CanvasKitTest(unittest.TestCase):
    def test_kit_loads_every_font_and_its_helpers_behave(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "demo.html"
            page.write_text(DEMO.format(fonts=FONTS.as_uri(), kit=(REPO / "studio" / "canvas_kit.js").as_uri()),
                            encoding="utf-8")
            check = Path(tmp) / "check.cjs"
            check.write_text(CHECK, encoding="utf-8")
            r = subprocess.run(["node", str(check), str(page), str(REPO / "studio" / "chromium.cjs")],
                               capture_output=True, text=True, timeout=120, cwd=str(REPO))
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertTrue(out["ready"], out)
            self.assertIsNone(out["error"])
            self.assertEqual(out["missing"], [])
            self.assertEqual(out["errors"], [])
            self.assertTrue(out["seeded"])
            self.assertTrue(out["loop"])
            self.assertEqual(out["chunks"], 2)
            self.assertEqual(out["ease"], [0, 1, 10])
            self.assertTrue(out["safe"])

    def test_demo_page_renders_through_the_studio_renderer(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "demo.html"
            page.write_text(DEMO.format(fonts=FONTS.as_uri(), kit=(REPO / "studio" / "canvas_kit.js").as_uri()),
                            encoding="utf-8")
            r = subprocess.run(["node", str(REPO / "studio" / "render_canvas.cjs"), str(page), str(Path(tmp) / "s"),
                                "--size", "1080x1920", "--stills", "0.7,2.3"], capture_output=True, text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            from PIL import Image
            a = Image.open(Path(tmp) / "s_1.png")
            self.assertEqual(a.size, (1080, 1920))
            self.assertGreater(len(set(a.convert("L").resize((64, 114)).getdata())), 20)  # not a blank frame


@unittest.skipUnless(importlib.util.find_spec("numpy"), "needs numpy")
class SfxTest(unittest.TestCase):
    def test_every_sound_is_short_loud_enough_and_deterministic(self):
        import numpy as np
        import sfx
        for name in sfx.SOUNDS:
            a, b = sfx.make(name, seed=3), sfx.make(name, seed=3)
            self.assertTrue(np.array_equal(a, b), name)
            self.assertEqual(a.shape[1], 2, name)
            self.assertLess(len(a) / sfx.SR, 3.0, name)
            self.assertAlmostEqual(float(np.abs(a).max()), 10 ** (-3 / 20), delta=0.15, msg=name)
            self.assertLess(float(np.abs(a[-50:]).max()), 0.05, name)  # ends faded, no click

    def test_place_puts_each_cue_at_its_time(self):
        import numpy as np
        import sfx
        with tempfile.TemporaryDirectory() as tmp:
            cues = Path(tmp) / "cues.json"
            cues.write_text(json.dumps([{"t": 0.5, "sfx": "pop"}, {"t": 2.0, "sfx": "impact"}]))
            out = Path(tmp) / "bed.wav"
            self.assertEqual(sfx.main(["place", str(cues), str(out), "--dur", "3"]), 0)
            with wave.open(str(out)) as w:
                self.assertEqual((w.getframerate(), w.getnchannels()), (48000, 2))
                x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2) / 32768
            self.assertEqual(len(x), 3 * 48000)
            self.assertLess(np.abs(x[: int(0.49 * 48000)]).max(), 1e-3)
            self.assertGreater(np.abs(x[int(0.5 * 48000): int(0.6 * 48000)]).max(), 0.1)
            self.assertLess(np.abs(x[int(1.0 * 48000): int(1.99 * 48000)]).max(), 1e-3)
            self.assertGreater(np.abs(x[int(2.0 * 48000): int(2.2 * 48000)]).max(), 0.1)
            self.assertLessEqual(np.abs(x).max(), 0.9)


if __name__ == "__main__":
    unittest.main()
