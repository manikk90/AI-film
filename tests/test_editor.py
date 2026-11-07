"""Mann (AI video editor) tests. All media are SYNTHETIC FFmpeg fixtures (test patterns,
sine tones, pink noise), never real footage. They prove the pipeline's mechanics, not edit quality."""

import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from aifilm.core import ProductionError, read_json, write_json
from aifilm.editor import edl as E
from aifilm.editor import media, render as R, style as S, tools as T
from aifilm.editor.cli import main

REPO = Path(__file__).resolve().parents[1]
HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + [str(a) for a in args], check=True, timeout=120)


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is required for media tests")
class EditorCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = Path(tempfile.mkdtemp(prefix="mann-fixtures-"))
        f = cls.fixtures
        ff("-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:d=4", "-f", "lavfi", "-i", "sine=frequency=330:duration=4",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", f / "A.mp4")
        ff("-f", "lavfi", "-i", "smptebars=size=480x360:rate=25:d=3", "-c:v", "libx264", "-pix_fmt", "yuv420p", f / "B_silent.mp4")
        ff("-f", "lavfi", "-i", "sine=frequency=110:duration=2", "-c:a", "libmp3lame", f / "music.mp3")
        ff("-f", "lavfi", "-i", "anoisesrc=d=0.3:c=pink", f / "whoosh.wav")
        # Three solid colours, hard cuts at 1.0 s and 2.0 s, for cut detection.
        ff("-f", "lavfi", "-i", "color=c=red:s=320x180:r=25:d=1", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=25:d=1",
           "-f", "lavfi", "-i", "color=c=green:s=320x180:r=25:d=1", "-filter_complex", "[0][1][2]concat=n=3:v=1:a=0",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", f / "cuts.mp4")
        (f / "subs.srt").write_text("1\n00:00:00,000 --> 00:00:01,500\nSynthetic fixture caption\n", encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fixtures, ignore_errors=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.edit = Path(self.temp.name) / "edit"
        T.ingest(self.edit, [self.fixtures / n for n in ("A.mp4", "B_silent.mp4", "music.mp3", "whoosh.wav", "subs.srt")])
        self.edl = {
            "version": 1, "title": "Synthetic fixture edit", "format": {"width": 360, "height": 640, "fps": 30},
            "sources": {"A": "raw/A.mp4", "B": "raw/B_silent.mp4"},
            "clips": [
                {"id": "C01", "source": "A", "in": 0.2, "out": 1.4, "beat": "hook", "zoom": {"from": 1.0, "to": 1.2},
                 "text": {"value": "हुक HOOK", "position": "top", "box": True}},
                {"id": "C02", "source": "B", "in": 0.5, "out": 2.0, "transition_in": {"type": "dissolve", "duration": 0.3}, "grade": "warm-film"},
                {"id": "C03", "source": "A", "in": 2.0, "out": 3.2, "speed": 1.5},
            ],
            "grade": {"preset": "punchy-social"},
            "audio": {"music": {"file": "raw/music.mp3", "gain_db": -14, "fade_out": 0.4},
                      "sfx": [{"file": "raw/whoosh.wav", "at": 1.0, "gain_db": -6}]},
            "subtitles": {"file": "raw/subs.srt"},
            "master": {"lufs": -14, "true_peak": -1},
        }
        self.save()

    def save(self):
        write_json(self.edit / "edl.json", self.edl)

    def test_ingest_records_hashes_and_probes(self):
        log = read_json(self.edit / "media.json")["files"]
        self.assertEqual(len(log["raw/A.mp4"]["sha256"]), 64)
        self.assertTrue(log["raw/A.mp4"]["probe"]["has_audio"])
        self.assertFalse(log["raw/B_silent.mp4"]["probe"]["has_audio"])

    def test_timeline_and_pace(self):
        rows, total = E.timeline(self.edl)
        self.assertEqual([r["start"] for r in rows], [0.0, 0.9, 2.4])
        self.assertAlmostEqual(total, 1.2 + 1.5 + 0.8 - 0.3, places=3)
        self.assertEqual(E.pace(self.edl)["shots"], 3)

    def test_validation_rejects_bad_edits(self):
        cases = [
            (lambda d: d["clips"][0].update(out=99), "past the end"),
            (lambda d: d["clips"][0].update(transition_in={"type": "dissolve", "duration": 0.2}), "first clip"),
            (lambda d: d["clips"][1].update(transition_in={"type": "dissolve", "duration": 1.3}), "shorter than both"),
            (lambda d: d["clips"][1].update(transition_in={"type": "spin3d"}), "unknown transition"),
            (lambda d: d["grade"].update(preset="nope"), "grade preset"),
            (lambda d: d["sources"].update(A="../escape.mp4"), "escapes"),
        ]
        for mutate, message in cases:
            with self.subTest(message=message):
                data = json.loads(json.dumps(self.edl))
                mutate(data)
                with self.assertRaisesRegex(ProductionError, message):
                    E.validate(self.edit, data)

    def test_storyboard_gate_render_and_qc(self):
        board = E.storyboard(self.edit)
        self.assertEqual([f["clip"] for f in board["frames"]], ["C01", "C02", "C03"])
        for f in board["frames"]:
            info = media.probe(self.edit / "storyboard" / f["file"])
            self.assertEqual((info["width"], info["height"]), (360, 640))
        self.assertIn("waiting for owner approval", (self.edit / "storyboard" / "STORYBOARD.md").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ProductionError, "not approved"):
            R.render(self.edit)
        with self.assertRaisesRegex(ProductionError, "exact approval words"):
            E.approve(self.edit, "  ")
        E.approve(self.edit, "synthetic fixture approval")
        out = R.render(self.edit)
        info = media.probe(out["master"])
        self.assertEqual((info["width"], info["height"]), (360, 640))
        self.assertAlmostEqual(info["duration"], out["expected_seconds"], delta=0.07)
        self.assertTrue((self.edit / "renders" / "preview_720p.mp4").exists())
        record = R.qc(self.edit)
        checks = {c["check"]: c for c in record["checks"]}
        self.assertEqual(checks["loudness"]["result"], "pass", checks["loudness"])
        self.assertEqual(checks["duration"]["result"], "pass")
        self.assertTrue(record["passed"], record["checks"])
        self.assertGreaterEqual(len(R.contact_frames(self.edit, 1.0)), 3)
        # A changed EDL voids the approval and the change list names the change.
        self.edl["clips"][2]["grade"] = "cool-night"
        self.save()
        with self.assertRaisesRegex(ProductionError, "not approved"):
            R.render(self.edit)
        with self.assertRaisesRegex(ProductionError, "qc for this EDL"):
            E.approve(self.edit, "final ok", kind="final")
        again = E.storyboard(self.edit)
        self.assertTrue(any("C03" in line and "cool-night" in line for line in again["changes_since_previous"]))

    def test_changed_source_file_voids_approval(self):
        E.storyboard(self.edit)
        E.approve(self.edit, "synthetic fixture approval")
        self.assertTrue(E.approved(self.edit, E.load(self.edit)))
        shutil.copyfile(self.fixtures / "whoosh.wav", self.edit / "raw" / "music.mp3")
        self.assertFalse(E.approved(self.edit, E.load(self.edit)))

    def test_qc_flags_missing_subtitles_and_dead_air(self):
        self.edl["subtitles"] = None
        self.edl["audio"] = {"keep_source": False}
        self.save()
        E.storyboard(self.edit)
        E.approve(self.edit, "synthetic fixture approval")
        R.render(self.edit, preview=False)
        record = R.qc(self.edit)
        failed = {c["check"] for c in record["checks"] if c["result"] == "fail"}
        self.assertFalse(record["passed"])
        self.assertIn("subtitles", failed)
        self.assertIn("loudness", failed)

    def test_cli_exit_codes(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(["validate", str(self.edit)]), 0)
            self.assertEqual(main(["render", str(self.edit)]), 2)
        self.assertIn("not approved", err.getvalue())

    def test_style_analysis_finds_hard_cuts(self):
        work = Path(self.temp.name) / "lab"
        a = S.analyze(self.fixtures / "cuts.mp4", work, "Synthetic three colours")
        self.assertEqual(a["pace"]["shots"], 3)
        self.assertEqual([round(s["start"], 1) for s in a["shots"]], [0.0, 1.0, 2.0])
        self.assertEqual(len(list((work / "frames").glob("*.jpg"))), 3)
        hexes = {c["hex"] for c in a["colour"]["palette"]}
        self.assertTrue(any(h.startswith("#f") or h.startswith("#e") for h in hexes), hexes)
        draft = (work / "STYLE_SHEET.draft.md").read_text(encoding="utf-8")
        self.assertIn("## Measured", draft)
        with self.assertRaisesRegex(ProductionError, "Write"):
            S.publish(work, Path(self.temp.name) / "styles", "synthetic")
        (work / "STYLE_SHEET.md").write_text(draft, encoding="utf-8")
        with self.assertRaisesRegex(ProductionError, "unfilled"):
            S.publish(work, Path(self.temp.name) / "styles", "synthetic")
        (work / "STYLE_SHEET.md").write_text(draft.replace("_Mann:", "Observed:"), encoding="utf-8")
        dest = S.publish(work, Path(self.temp.name) / "styles", "synthetic")
        saved = read_json(dest / "style.json")
        self.assertAlmostEqual(saved["targets"]["average_shot_seconds"], 1.0, places=1)
        self.assertNotIn("frames", saved["analysis"])


class EditorStaticTest(unittest.TestCase):
    def test_rules_file(self):
        data = read_json(REPO / "editor" / "rules.json")
        for key in ["loudness_lufs", "true_peak_max_db", "max_dead_air_seconds", "short_form_max_shot_seconds",
                    "hook_first_cut_max_seconds", "short_form_requires_subtitles", "min_shot_seconds", "style_pace_tolerance",
                    "loudness_tolerance_lu", "max_black_seconds", "dead_air_noise_db", "short_form_max_seconds"]:
            self.assertIn(key, data["rules"])
        for h in data["history"]:
            self.assertRegex(h["date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIn(h["kind"], {"owner", "observed", "result"})

    def test_srt_writer_splits_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            seg = [{"start": 0.0, "end": 2.0, "text": "a b c d e",
                    "words": [{"start": i * 0.4, "end": i * 0.4 + 0.3, "word": w} for i, w in enumerate("abcde")]}]
            self.assertEqual(T.write_srt(seg, Path(tmp) / "x.srt", max_words=2), 3)
            self.assertIn("00:00:01,600 --> 00:00:01,900", (Path(tmp) / "x.srt").read_text(encoding="utf-8"))

    def test_vendor_gsap_rewrites_cdn_link_without_network_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "vendor").mkdir()
            (p / "vendor" / "gsap.min.js").write_text("/* synthetic stand-in */", encoding="utf-8")
            (p / "compositions").mkdir()
            cdn = '<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>'
            (p / "index.html").write_text(cdn, encoding="utf-8")
            (p / "compositions" / "intro.html").write_text(cdn, encoding="utf-8")
            T.vendor_gsap(p)
            self.assertIn('src="vendor/gsap.min.js"', (p / "index.html").read_text(encoding="utf-8"))
            self.assertIn('src="../vendor/gsap.min.js"', (p / "compositions" / "intro.html").read_text(encoding="utf-8"))

    def test_atempo_chain(self):
        self.assertEqual(R.atempo(1.0), [])
        self.assertEqual(R.atempo(3.0), ["atempo=2.0", "atempo=1.50000"])
        self.assertEqual(R.atempo(0.25), ["atempo=0.5", "atempo=0.50000"])


if __name__ == "__main__":
    unittest.main()


CATALOG = REPO / "editor" / "styles" / "catalog.json"


class CatalogTest(unittest.TestCase):
    def test_fifty_styles_are_complete_and_engine_ready(self):
        data = read_json(CATALOG)
        styles = data["styles"]
        self.assertEqual(len(styles), 50)
        self.assertEqual(len({s["slug"] for s in styles}), 50)
        self.assertEqual({s["family"] for s in styles}, set(data["families"]))
        text_fields = ["name", "best_for", "aspect", "duration", "hook", "structure", "cutting", "camera", "transitions",
                       "type", "mg", "colour", "sound", "vfx"]
        for s in styles:
            with self.subTest(style=s["slug"]):
                for f in text_fields:
                    self.assertTrue(isinstance(s[f], str) and s[f].strip(), f)
                self.assertGreaterEqual(len(s["signature"]), 3)
                self.assertTrue(s["avoid"] and s["twists"] and s["known_from"])
                self.assertIn(s["fit"]["speech"], {"high", "low", "any"})
                self.assertIn(s["fit"]["motion"], {"low", "mid", "high", "any"})
                e = s["edl"]
                self.assertIn(e["grade"], E.GRADES)
                self.assertIn(e.get("transition", "cut"), E.TRANSITIONS)
                for fx in list((e.get("fx_every") or {})) + (e.get("fx_all") or []) + (e.get("fx_last") or []):
                    self.assertIn(fx, E.FX)
                if e.get("captions"):
                    self.assertIn(e["captions"]["color"], E.SUB_COLOURS)
                    self.assertIn(e["captions"]["position"], E.TEXT_POSITIONS)
                sheet = REPO / "editor" / "styles" / s["slug"] / "STYLE_SHEET.md"
                self.assertTrue(sheet.exists(), "run python3 editor/styles/build_styles.py")
                self.assertIn(s["hook"], sheet.read_text(encoding="utf-8"))
                self.assertEqual(read_json(sheet.parent / "style.json")["targets"]["average_shot_seconds"], s["pace"]["avg_shot"])
        index = (REPO / "editor" / "styles" / "INDEX.md").read_text(encoding="utf-8")
        for s in styles:
            self.assertIn("`{}`".format(s["slug"]), index)


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is required for media tests")
class EngineCase(unittest.TestCase):
    """SYNTHETIC fixtures: a flat-colour 'talking' clip with a gated tone, two moving test
    patterns as B-roll, a 120 BPM click track as music, pink noise as an SFX."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = Path(tempfile.mkdtemp(prefix="mann-engine-"))
        f = cls.fixtures
        ff("-f", "lavfi", "-i", "color=c=0x806050:s=320x180:r=30:d=9", "-f", "lavfi",
           "-i", "sine=f=220:d=9,volume='if(lt(mod(t,3),2.2),1,0)':eval=frame", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", f / "talk.mp4")
        ff("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=6", "-c:v", "libx264", "-pix_fmt", "yuv420p", f / "broll1.mp4")
        ff("-f", "lavfi", "-i", "mandelbrot=s=320x180:r=30,trim=duration=5", "-c:v", "libx264", "-pix_fmt", "yuv420p", f / "broll2.mp4")
        ff("-f", "lavfi", "-i", "sine=f=1000:d=20,volume='if(lt(mod(t,0.5),0.05),1,0)':eval=frame", "-f", "lavfi", "-i", "sine=f=110:d=20",
           "-filter_complex", "[0][1]amix=inputs=2:weights=1 0.3", f / "music120.wav")
        ff("-f", "lavfi", "-i", "anoisesrc=d=0.3:c=pink", f / "whoosh.wav")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fixtures, ignore_errors=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.edit = Path(self.temp.name) / "edit"
        T.ingest(self.edit, sorted(self.fixtures.iterdir()))
        (self.edit / "BRIEF.md").write_text("Synthetic fixture brief: travel recap\n", encoding="utf-8")

    def test_assets_beats_and_suggestions(self):
        from aifilm.editor import engine as G
        items = {a["file"]: a for a in G.assets(self.edit)}
        self.assertEqual(items["raw/music120.wav"]["kind"], "music")
        self.assertEqual(items["raw/whoosh.wav"]["kind"], "sfx")
        self.assertEqual(items["raw/talk.mp4"]["label"], "talking")
        self.assertAlmostEqual(items["raw/music120.wav"]["bpm"], 120, delta=3)
        r = G.suggest(self.edit, "9:16")
        self.assertEqual(len(r["recommended"]), 3)
        fams = {s["slug"]: s["family"] for s in G.catalog()}
        self.assertNotEqual(fams[r["experiment"]["styles"][0]], fams[r["experiment"]["styles"][1]])
        self.assertTrue(any("reframe" in p for p in r["problems"]))
        self.assertTrue(r["unique_ideas"])
        self.assertIn("Recommended styles", (self.edit / "SUGGESTIONS.md").read_text(encoding="utf-8"))

    def test_autocut_makes_a_valid_draft_in_every_style(self):
        from aifilm.editor import engine as G
        for s in G.catalog():
            with self.subTest(style=s["slug"]):
                out = G.autocut(self.edit, s["slug"], seconds=8)
                edl = read_json(self.edit / "edl.json")
                E.validate(self.edit, edl)
                self.assertEqual(edl["style"], s["slug"])
                self.assertGreater(out["seconds"], 1.0)
                self.assertEqual(edl["grade"]["preset"], s["edl"]["grade"])

    def test_owner_decisions_gate_the_storyboard(self):
        from aifilm.editor import engine as G
        G.autocut(self.edit, "interview-broll-doc", seconds=6)
        with self.assertRaisesRegex(ProductionError, "not finalised"):
            E.storyboard(self.edit)
        E.approve_style(self.edit, "interview-broll-doc", "synthetic fixture pick")
        (self.edit / "SCRIPT.md").write_text("Synthetic locked script line\n", encoding="utf-8")
        edl = read_json(self.edit / "edl.json")
        edl["script"] = "SCRIPT.md"
        write_json(self.edit / "edl.json", edl)
        with self.assertRaisesRegex(ProductionError, "not locked"):
            E.storyboard(self.edit)
        E.lock_script(self.edit, "SCRIPT.md", "synthetic lock")
        E.storyboard(self.edit)
        (self.edit / "SCRIPT.md").write_text("Changed after lock\n", encoding="utf-8")
        with self.assertRaisesRegex(ProductionError, "not locked"):
            E.storyboard(self.edit)

    def test_part_correction_touches_only_that_part(self):
        from aifilm.editor import engine as G
        G.autocut(self.edit, "beat-sync-montage", seconds=6)
        E.approve_style(self.edit, "beat-sync-montage", "synthetic fixture pick")
        E.storyboard(self.edit)
        E.approve(self.edit, "synthetic whole approval")
        self.assertEqual(E.status(self.edit, E.load(self.edit))["scope"], "none")
        edl = read_json(self.edit / "edl.json")
        target = edl["clips"][1]["id"]
        edl["clips"][1]["grade"] = "cool-night"
        write_json(self.edit / "edl.json", edl)
        st = E.status(self.edit, E.load(self.edit))
        self.assertEqual((st["scope"], st["changed_clips"]), ("part", [target]))
        with self.assertRaisesRegex(ProductionError, "changed part"):
            R.render(self.edit, preview=False)
        with self.assertRaisesRegex(ProductionError, "No part storyboard|changed after"):
            E.approve(self.edit, "too early", clips=[target])
        part = E.storyboard(self.edit, only=[target])
        self.assertEqual([f["clip"] for f in part["frames"]], [target])
        self.assertTrue(any(target in line and "cool-night" in line for line in part["changes_since_previous"]))
        preview = R.preview_part(self.edit, [target])
        self.assertIn(target, preview["clips"])
        self.assertGreater(media.probe(preview["file"])["duration"], 0.5)
        E.approve(self.edit, "synthetic part approval", clips=[target])
        self.assertEqual(E.status(self.edit, E.load(self.edit))["scope"], "none")
        R.render(self.edit, preview=False)
        edl = read_json(self.edit / "edl.json")
        edl["grade"]["preset"] = "bw-contrast"
        write_json(self.edit / "edl.json", edl)
        self.assertEqual(E.status(self.edit, E.load(self.edit))["scope"], "whole")
        with self.assertRaisesRegex(ProductionError, "whole storyboard"):
            E.approve(self.edit, "part only", clips=[target])

    def test_every_fx_renders_through_the_graph(self):
        clips = [{"id": "X{}".format(i), "source": "T", "in": 0.0, "out": 0.6, "fx": [fx]} for i, fx in enumerate(sorted(E.FX))]
        clips[-1]["freeze"] = 0.3
        clips[1]["inserts"] = [{"source": "B", "in": 0.0, "out": 0.4, "at": 0.1}]
        (self.edit / "caps.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nsynthetic caption\n", encoding="utf-8")
        write_json(self.edit / "edl.json", {"version": 1, "format": {"width": 180, "height": 320, "fps": 30},
                                            "sources": {"T": "raw/talk.mp4", "B": "raw/broll1.mp4"}, "clips": clips,
                                            "subtitles": {"file": "caps.srt", "uppercase": True, "color": "yellow", "box": True, "position": "center"}})
        rec = E.storyboard(self.edit)
        self.assertEqual(len(rec["frames"]), len(E.FX))
        staged = E.stage_subtitles(self.edit, E.load(self.edit))
        self.assertIn("SYNTHETIC CAPTION", staged.read_text(encoding="utf-8"))

    def test_sub_edl_retimes_the_part(self):
        edl = {"version": 1, "format": {"width": 180, "height": 320, "fps": 30}, "sources": {"T": "raw/talk.mp4"},
               "clips": [{"id": "A", "source": "T", "in": 0, "out": 2}, {"id": "B", "source": "T", "in": 2, "out": 4},
                         {"id": "C", "source": "T", "in": 4, "out": 6}, {"id": "D", "source": "T", "in": 6, "out": 8}],
               "audio": {"music": {"file": "raw/music120.wav", "start": 1.0}, "sfx": [{"file": "raw/whoosh.wav", "at": 0.5}, {"file": "raw/whoosh.wav", "at": 4.5}]}}
        part, offset, length = E.sub_edl(edl, ["C"])
        self.assertEqual([c["id"] for c in part["clips"]], ["B", "C", "D"])
        self.assertEqual((offset, length), (2.0, 6.0))
        self.assertEqual(part["audio"]["music"]["start"], 3.0)
        self.assertEqual([s["at"] for s in part["audio"]["sfx"]], [2.5])
        self.assertIn("00:00:01,500", E.shift_srt("00:00:03,500 --> 00:00:04,000", 2.0))


class CraftStaticTest(unittest.TestCase):
    def test_rulebook_is_complete_and_built(self):
        from aifilm.editor import craft as C
        d = C.data()
        ids = [r["id"] for r in C.rules()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 80)
        domains = {dom["id"] for dom in d["domains"]}
        for needed in ["cuts", "transitions", "continuity", "eyelines", "composition", "shots", "pacing", "typography", "colour",
                       "safe-zones", "sound", "motion", "vfx", "story", "accessibility"]:
            self.assertIn(needed, domains)
        for r in C.rules():
            with self.subTest(rule=r["id"]):
                for f in ("name", "what", "when", "how", "avoid"):
                    self.assertTrue(r[f].strip())
                self.assertIn(r["check"], {"auto", "manual"})
        latin_only = {"Inter", "Montserrat", "Bebas Neue", "Playfair Display", "Anton"}
        for p in d["font_pairings"]:
            if p["devanagari"]:
                self.assertFalse({p["display"], p["text"]} & latin_only, p["id"])
        for t in d["colour_themes"]:
            self.assertIn(t["grade"], E.GRADES)
            for c in t["colours"]:
                self.assertRegex(c, r"^#[0-9a-f]{6}$")
        for aspect in ("9:16", "16:9", "1:1", "4:5"):
            self.assertEqual(set(d["safe_zones"][aspect]), {"standard", "strict"})
        md = (REPO / "editor" / "craft" / "CRAFT.md").read_text(encoding="utf-8")
        for i in ids:
            self.assertIn("`{}`".format(i), md, "run python3 editor/craft/build_craft.py")
        rules = read_json(REPO / "editor" / "rules.json")["rules"]
        import re as _re
        used = set(_re.findall(r'R\["([a-z_0-9]+)"\]', (REPO / "aifilm" / "editor" / "craft.py").read_text(encoding="utf-8")))
        self.assertLessEqual(used, set(rules))

    def test_contrast_width_and_font_resolve(self):
        from aifilm.editor import craft as C, fonts as F
        self.assertAlmostEqual(C.contrast((255, 255, 255), (0, 0, 0)), 21.0, places=1)
        self.assertAlmostEqual(C.text_width("कि", 100), C.text_width("क", 100), places=3)
        import os
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("MANN_FONTS")
            os.environ["MANN_FONTS"] = tmp
            try:
                for w in (400, 700):
                    (Path(tmp) / "Poppins-{}.ttf".format(w)).write_bytes(b"synthetic placeholder")
                self.assertTrue(F.resolve("Poppins", 600).endswith("Poppins-700.ttf"))
                self.assertTrue(F.resolve("Poppins", 450).endswith("Poppins-400.ttf"))
                self.assertIsNone(F.resolve("Hind", 400))
            finally:
                if old is None:
                    os.environ.pop("MANN_FONTS")
                else:
                    os.environ["MANN_FONTS"] = old


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is required for media tests")
class CraftCheckCase(unittest.TestCase):
    """SYNTHETIC fixtures only: a flat-colour clip with a tone, and a test pattern."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = Path(tempfile.mkdtemp(prefix="mann-craft-"))
        ff("-f", "lavfi", "-i", "color=c=0x806050:s=320x180:r=30:d=6", "-f", "lavfi", "-i", "sine=f=220:d=6",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", cls.fixtures / "talk.mp4")
        ff("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=6", "-c:v", "libx264", "-pix_fmt", "yuv420p", cls.fixtures / "broll.mp4")
        ff("-f", "lavfi", "-i", "sine=f=110:d=6", cls.fixtures / "music.wav")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fixtures, ignore_errors=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.edit = Path(self.temp.name) / "edit"
        T.ingest(self.edit, sorted(self.fixtures.iterdir()))

    def write(self, edl):
        write_json(self.edit / "edl.json", edl)
        return E.load(self.edit)

    def results(self, edl):
        from aifilm.editor import craft as C
        out = {}
        for f in C.check(self.edit, edl):
            out.setdefault(f["check"].split(" C0")[0], []).append(f["result"])
        return out

    def test_flawed_cut_is_caught(self):
        (self.edit / "caps.srt").write_text("1\n00:00:00,000 --> 00:00:00,500\nThis caption is far too long and far too fast to read on a phone\n",
                                            encoding="utf-8")
        edl = self.write({
            "version": 1, "format": {"width": 360, "height": 640, "fps": 30}, "sources": {"T": "raw/talk.mp4", "B": "raw/broll.mp4"},
            "clips": [{"id": "C01", "source": "T", "in": 0, "out": 1.5,
                       "text": {"value": "एक बहुत लंबा शीर्षक जो किनारे तक जाता है", "role": "title", "position": "top", "end": 0.4}},
                      {"id": "C02", "source": "T", "in": 1.6, "out": 2.4},
                      {"id": "C03", "source": "B", "in": 0, "out": 0.3, "fx": ["flash"]}, {"id": "C04", "source": "B", "in": 1, "out": 1.3, "fx": ["flash"]},
                      {"id": "C05", "source": "B", "in": 2, "out": 2.3, "fx": ["flash"]}, {"id": "C06", "source": "B", "in": 3, "out": 3.3, "fx": ["flash"]}],
            "audio": {"music": {"file": "raw/music.wav", "gain_db": -4}}, "subtitles": {"file": "caps.srt"}})
        r = self.results(edl)
        self.assertIn("fail", r["flash safety"])
        self.assertIn("fail", r["text safe zone"])
        self.assertIn("warn", r["reading time"])
        self.assertIn("warn", r["caption reading speed"])
        self.assertIn("warn", r["caption minimum duration"])
        self.assertIn("warn", r["caption line length"])
        self.assertIn("warn", r["30-degree rule / jump cuts"])
        self.assertIn("warn", r["music under voice"])

    def test_clean_cut_passes_and_storyboard_reports_craft(self):
        (self.edit / "caps.srt").write_text("1\n00:00:00,000 --> 00:00:01,600\nकिसी ने नहीं बताया\n", encoding="utf-8")
        edl = self.write({
            "version": 1, "format": {"width": 360, "height": 640, "fps": 30}, "sources": {"T": "raw/talk.mp4", "B": "raw/broll.mp4"},
            "clips": [{"id": "C01", "source": "T", "in": 0, "out": 1.5, "text": {"value": "कहानी", "role": "title", "position": "top"}},
                      {"id": "C02", "source": "B", "in": 0, "out": 1.0},
                      {"id": "C03", "source": "T", "in": 3.0, "out": 4.2, "zoom": {"from": 1.25, "to": 1.25}}],
            "audio": {"music": {"file": "raw/music.wav", "gain_db": -16}}, "subtitles": {"file": "caps.srt", "box": True}})
        r = self.results(edl)
        for name in ("flash safety", "text safe zone", "caption safe zone", "caption reading speed", "30-degree rule / jump cuts",
                     "music under voice", "type hierarchy", "font families"):
            if name in r:
                self.assertNotIn("fail", r[name], name)
        self.assertEqual(r["30-degree rule / jump cuts"], ["pass"])
        rec = E.storyboard(self.edit)
        self.assertTrue(rec["craft"])
        md = (self.edit / "storyboard" / "STORYBOARD.md").read_text(encoding="utf-8")
        self.assertIn("Craft check (automatic)", md)
        self.assertIn("Craft checklist", md)
        self.assertIn("`180-rule`", md)
        self.assertIn("`vertical-reframe`", md)

    def test_text_goes_through_ass_with_complex_shaping(self):
        (self.edit / "caps.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\n{braces} किसी\n", encoding="utf-8")
        edl = self.write({"version": 1, "format": {"width": 360, "height": 640, "fps": 30}, "sources": {"T": "raw/talk.mp4"},
                          "clips": [{"id": "C01", "source": "T", "in": 0, "out": 1.5, "text": {"value": "हिंदी\nदो पंक्ति", "role": "headline"}}],
                          "subtitles": {"file": "caps.srt", "uppercase": True}})
        script = E.ass_script(self.edit, edl).read_text(encoding="utf-8")
        self.assertIn("PlayResY: 640", script)
        self.assertIn("\\{BRACES\\} किसी", script)
        self.assertIn("हिंदी\\Nदो पंक्ति", script)
        textfiles = []
        _, graph, _, _, _ = R.build_graph(self.edit, edl, E.validate(self.edit, edl), textfiles)
        self.assertIn("shaping=complex", graph)
        self.assertNotIn("drawtext", graph)
        self.assertNotIn("subtitles=", graph)


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is required for media tests")
class ReframeCase(unittest.TestCase):
    """SYNTHETIC fixture: a white square ('the subject') moving right to left on a dark 16:9
    frame. A stand-in detector finds the square, so the crop logic is tested without faces."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = Path(tempfile.mkdtemp(prefix="mann-reframe-"))
        ff("-f", "lavfi", "-i", "color=c=0x202020:s=640x360:r=30:d=4", "-f", "lavfi", "-i", "color=c=white:s=60x60:r=30:d=4",
           "-filter_complex", "[0][1]overlay=x='520-100*t':y=80", "-c:v", "libx264", "-pix_fmt", "yuv420p", cls.fixtures / "moving.mp4")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fixtures, ignore_errors=True)

    def setUp(self):
        from aifilm.editor import reframe as RF
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("numpy is required for reframing")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.edit = Path(self.temp.name) / "edit"
        T.ingest(self.edit, [self.fixtures / "moving.mp4"])

        def bright_box(gray):
            import numpy as np
            ys, xs = np.nonzero(gray > 200)
            if not len(xs):
                return []
            return [(int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))]
        original = RF.detect
        RF.detect = bright_box
        self.addCleanup(setattr, RF, "detect", original)

    def test_crop_follows_the_subject(self):
        from aifilm.editor import reframe as RF
        tr = RF.track(self.edit, "raw/moving.mp4")
        self.assertGreater(tr["detected_share"], 0.9)
        p = RF.plan(tr, 0, 4, 1.0, 360, 640)
        self.assertEqual((p["w"], p["h"]), (202, 360))
        self.assertLess(RF.evaluate(p["x"], 3.5), RF.evaluate(p["x"], 0.5))
        edl = {"version": 1, "format": {"width": 360, "height": 640, "fps": 30, "reframe": "auto"}, "sources": {"A": "raw/moving.mp4"},
               "clips": [{"id": "C01", "source": "A", "in": 0, "out": 4}]}
        write_json(self.edit / "edl.json", edl)
        edl = E.load(self.edit)
        xs = [f["x"] for f in RF.framing(self.edit, edl, edl["clips"][0], 4)]
        self.assertTrue(all(0.3 <= x <= 0.7 for x in xs[2:-2]), xs)
        from aifilm.editor import craft as C
        found = {f["check"]: f["result"] for f in C.check(self.edit, edl, sample_contrast=False)}
        self.assertEqual(found.get("subject in frame"), "pass")
        rec = E.storyboard(self.edit, 2)
        self.assertEqual(len(rec["frames"]), 2)

    def test_piecewise_expression_and_simplify(self):
        from aifilm.editor import reframe as RF
        pts = [(0, 100.0), (1, 110.0), (2, 120.0), (3, 120.5), (4, 60.0)]
        simple = RF.simplify(pts, 2.0)
        self.assertEqual([p[0] for p in simple], [0, 2, 3, 4])
        expr = RF.piecewise(simple)
        self.assertAlmostEqual(RF.evaluate(expr, 1.5), 115.0, delta=1.0)
        self.assertAlmostEqual(RF.evaluate(expr, 4.0), 60.0, delta=0.5)
        self.assertEqual(RF.piecewise([(0, 50.0), (2, 50.2)]), "50.0")


class AnimatedCaptionTest(unittest.TestCase):
    """Text-only checks of the ASS events for animated captions (no media needed)."""

    cue = {"start": 1.0, "end": 2.0, "lines": ["एक दो", "तीन"]}

    def test_estimated_and_measured_word_timings(self):
        ws, measured = E.cue_words(self.cue, [])
        self.assertFalse(measured)
        self.assertEqual([w["word"] for w in ws], ["एक", "दो", "तीन"])
        self.assertAlmostEqual(ws[-1]["end"], 2.0, places=3)
        timed = [{"start": 1.0, "end": 1.2, "word": "a"}, {"start": 1.3, "end": 1.5, "word": "b"}, {"start": 1.6, "end": 1.9, "word": "c"}]
        ws, measured = E.cue_words(self.cue, timed)
        self.assertTrue(measured)
        self.assertEqual([(w["start"], w["word"]) for w in ws], [(1.0, "एक"), (1.3, "दो"), (1.6, "तीन")])

    def test_modes(self):
        subs = {"highlight_color": "yellow", "color": "white"}
        hl = E.animated_events(self.cue, [], "highlight", subs)
        self.assertEqual(len(hl), 3)
        self.assertIn("{\\c&H0000F0FF}दो{\\r}", hl[1][3])
        self.assertEqual(hl[-1][1], 2.0)
        pop = E.animated_events(self.cue, [], "pop", subs)
        self.assertIn("\\t(0,100,\\fscx100\\fscy100)", pop[0][3])
        word = E.animated_events(self.cue, [], "word", subs)
        self.assertTrue(word[2][3].endswith("तीन"))
        kar = E.animated_events(self.cue, [], "karaoke", subs)
        self.assertEqual(len(kar), 1)
        self.assertEqual(kar[0][3].count("\\kf"), 3)


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is required for media tests")
class ClipCacheCase(unittest.TestCase):
    """SYNTHETIC fixtures: a test pattern with a tone and a colour field."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        ff("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=4", "-f", "lavfi", "-i", "sine=f=300:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", base / "a.mp4")
        ff("-f", "lavfi", "-i", "color=c=0x406080:s=320x180:r=30:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", base / "b.mp4")
        self.edit = base / "edit"
        T.ingest(self.edit, [base / "a.mp4", base / "b.mp4"])
        write_json(self.edit / "edl.json", {
            "version": 1, "format": {"width": 180, "height": 320, "fps": 30}, "sources": {"A": "raw/a.mp4", "B": "raw/b.mp4"},
            "clips": [{"id": "C01", "source": "A", "in": 0, "out": 1.5, "text": {"value": "one", "role": "title", "position": "top"}},
                      {"id": "C02", "source": "B", "in": 0, "out": 1.0, "zoom": {"from": 1.0, "to": 1.2}},
                      {"id": "C03", "source": "A", "in": 2.0, "out": 3.0, "zoom": {"from": 1.25, "to": 1.25}}]})
        E.storyboard(self.edit)
        E.approve(self.edit, "synthetic fixture approval")

    def change(self, mutate, cid):
        edl = read_json(self.edit / "edl.json")
        mutate(edl)
        write_json(self.edit / "edl.json", edl)
        E.storyboard(self.edit, only=[cid])
        E.approve(self.edit, "synthetic part approval", clips=[cid])
        return R.render(self.edit, preview=False, quality="draft")

    def test_only_changed_clips_are_rerendered(self):
        first = R.render(self.edit, preview=False, quality="draft")
        self.assertEqual((first["clips_rendered"], first["clips_reused"]), (3, 0))
        graded = self.change(lambda d: d["clips"][1].update(grade="cool-night"), "C02")
        self.assertEqual((graded["clips_rendered"], graded["clips_reused"]), (1, 2))
        text = self.change(lambda d: d["clips"][0]["text"].update(value="two"), "C01")
        self.assertEqual((text["clips_rendered"], text["clips_reused"]), (0, 3))
        self.assertAlmostEqual(media.probe(text["master"])["duration"], text["expected_seconds"], delta=0.07)
        self.assertEqual(len(list((self.edit / "renders" / "cache").glob("*.mkv"))), 3)
        with self.assertRaisesRegex(ProductionError, "quality"):
            R.render(self.edit, quality="ultra")


class MotionStaticTest(unittest.TestCase):
    def test_templates_and_theme_roles(self):
        from aifilm.editor import craft as C, motion as MO
        names = [t["name"] for t in MO.templates()]
        self.assertEqual(len(names), 10)
        self.assertEqual(len(set(names)), 10)
        for t in MO.templates():
            self.assertTrue(t["description"] and t["vars"] and t["duration"] > 0, t["name"])
        for theme in C.data()["colour_themes"]:
            r = MO.roles(theme["colours"])
            rgb = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))  # noqa: E731
            with self.subTest(theme=theme["id"]):
                self.assertGreaterEqual(C.contrast(rgb(r["accent"]), rgb(r["bg"])), 3.0)
                self.assertGreaterEqual(C.contrast(rgb(r["ink"]), rgb(r["bg"])), 4.5)


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is required for media tests")
class MotionRenderCase(unittest.TestCase):
    """Renders every template small and short (synthetic text values)."""

    def setUp(self):
        from aifilm.editor import motion as MO
        if not MO.available():
            self.skipTest("Node + Playwright are required for motion templates")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def test_every_template_renders_transparent_stills(self):
        from aifilm.editor import motion as MO
        for t in MO.templates():
            with self.subTest(template=t["name"]):
                extra = {"dim": 0} if t["name"] == "highlight-box" else {}  # its outside dim is intentional
                png = MO.render(t["name"], self.base / t["name"], (180, 320), 1.5, extra, theme="neon-mumbai", stills=[0.9])[0]
                raw = subprocess.run(["ffmpeg", "-v", "error", "-i", png, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout
                alphas = raw[3::4]
                self.assertEqual(len(alphas), 180 * 320)
                self.assertGreater(sum(1 for a in alphas if a > 200), 50, "nothing drawn")
                self.assertGreater(sum(1 for a in alphas if a == 0), len(alphas) // 3, "background is not transparent")

    def test_mov_has_alpha_and_add_places_it(self):
        from aifilm.editor import motion as MO
        out = MO.render("lower-third", self.base / "lt.mov", (180, 320), 0.5, {"name": "परीक्षण"}, fps=10)
        self.assertEqual(out["frames"], 5)
        pix = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=pix_fmt", "-of", "csv=p=0",
                              str(self.base / "lt.mov")], capture_output=True, text=True).stdout.strip()
        self.assertTrue(pix.startswith("yuva"), pix)
        ff("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", self.base / "a.mp4")
        edit = self.base / "edit"
        T.ingest(edit, [self.base / "a.mp4"])
        (edit / "caps.srt").write_text("1\n00:00:00,000 --> 00:00:01,500\nsynthetic caption\n", encoding="utf-8")
        write_json(edit / "edl.json", {"version": 1, "format": {"width": 180, "height": 320, "fps": 10}, "sources": {"A": "raw/a.mp4"},
                                       "clips": [{"id": "C01", "source": "A", "in": 0, "out": 1.5}], "subtitles": {"file": "caps.srt"},
                                       "typography": {"theme": "clean-tech"}})
        placed = MO.placement(edit, read_json(edit / "edl.json"), 0.2, 1.0)
        self.assertLess(placed["bottom_limit"], 0.75)
        entry = MO.add(edit, "callout", 0.2, 1.0, {"x": 0.3, "y": 0.4, "label": "यहाँ"})
        edl = E.load(edit)
        self.assertEqual(edl["overlays"][0]["file"], entry["file"])
        self.assertTrue((edit / entry["file"]).exists())
        with self.assertRaisesRegex(ProductionError, "Unknown motion template"):
            MO.template("nope")
