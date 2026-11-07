"""Checks for the format prompts saved from the "12 Claude Video Formats" guide (studio/formats/) and their prompt
template (text only; nothing is rendered)."""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = json.loads((REPO / "studio" / "formats" / "claude-video-formats.json").read_text(encoding="utf-8"))
MENU = (REPO / "studio" / "STYLE_MENU.md").read_text(encoding="utf-8")
KEYS = ["slug", "typed", "name", "hi", "in_reel", "look", "guide_film", "good_for", "nearest", "notes"]
TYPED = ["Kinetic typography", "Claymation stop motion", "Pixel art game", "Whiteboard sketch", "80s VHS commercial",
         "Rubber hose cartoon", "Isometric 3D", "Anime opening", "Paper cut-out", "Comic book", "Neon synthwave",
         "Liquid motion"]  # the guide's appendix list, as typed


class FormatPromptsTest(unittest.TestCase):
    def test_the_twelve_formats_as_typed_in_the_guide(self):
        formats = DATA["formats"]
        self.assertEqual(sorted(f["typed"] for f in formats), sorted(TYPED))
        self.assertEqual([f["slug"] for f in formats if not f["in_reel"]], ["neon-synthwave", "liquid-motion"])
        slugs = [f["slug"] for f in formats]
        self.assertEqual(len(set(slugs)), 12)
        for f in formats:
            with self.subTest(format=f["slug"]):
                self.assertEqual(list(f), KEYS)
                self.assertRegex(f["slug"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
                self.assertTrue(re.search(r"[ऀ-ॿ]", f["hi"]), "Hindi name must be in Devanagari")
                self.assertEqual(len(f["good_for"]), 3)
                self.assertTrue(1 <= len(f["nearest"]) <= 3)
                self.assertTrue(f["look"] and f["guide_film"])

    def test_slugs_are_new_and_nearest_styles_exist(self):
        taken = {p.name for p in (REPO / "styles").iterdir() if p.is_dir()}
        taken |= {p.name for p in (REPO / ".claude" / "skills").iterdir() if p.is_dir()}
        for f in DATA["formats"]:
            with self.subTest(format=f["slug"]):
                self.assertNotIn(f["slug"], taken)
                self.assertIn(f"`{f['slug']}`", MENU)  # listed in the style menu
                for n in f["nearest"]:
                    self.assertIn(f"`{n}`", MENU, f"nearest style {n} is not on the menu")

    def test_template_and_no_model_names(self):
        template = (REPO / "studio" / "templates" / "format-prompt.md").read_text(encoding="utf-8")
        for needle in ["Format: [FORMAT].", "window.FILM", "render_canvas.cjs", "--stills", "Size 1080 by 1920"]:
            self.assertIn(needle, template)
        readme = (REPO / "studio" / "formats" / "README.md").read_text(encoding="utf-8")
        for text in (json.dumps(DATA), template, readme):
            self.assertNotRegex(text, r"(?i)\bopus\b|\bsonnet\b|\bhaiku\b")


if __name__ == "__main__":
    unittest.main()
