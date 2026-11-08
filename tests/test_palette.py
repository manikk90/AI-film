"""60-30-10 colour check (studio/palette.py, studio/COLOR.md). Pixels here are a SYNTHETIC FIXTURE."""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "studio"))
import palette as P  # noqa: E402

CREAM, MAROON, RED = (240, 228, 205), (110, 40, 50), (225, 40, 30)


class PaletteTest(unittest.TestCase):
    def test_a_60_30_10_frame_passes_and_names_each_role(self):
        r = P.roles([CREAM] * 60 + [MAROON] * 30 + [RED] * 10)
        self.assertEqual({k: v[1] for k, v in r.items()}, {"main": 60.0, "second": 30.0, "accent": 10.0})
        self.assertEqual(r["accent"][0], RED)
        self.assertEqual(P.verdict(r), "PASS")

    def test_a_frame_with_too_much_accent_fails_with_the_reason(self):
        r = P.roles([CREAM] * 40 + [MAROON] * 25 + [RED] * 35)
        self.assertIn("accent 35% (want 3-15)", P.verdict(r))

    def test_a_flat_frame_has_no_loud_accent(self):
        r = P.roles([CREAM] * 60 + [(200, 190, 175)] * 30 + [(180, 172, 160)] * 10)
        self.assertIn("no loud accent", P.verdict(r))

    def test_the_rule_reaches_every_visual_agent(self):
        for f in ["director", "mann", "social", "marich"]:
            self.assertIn("COLOR.md" if f != "marich" else "palette.py",
                          (REPO / ".claude" / "agents" / f"{f}.md").read_text(encoding="utf-8"), f)
        for f in ["studio/SKILL_HARNESS.md", "studio/templates/format-prompt.md", "studio/LEARNINGS.md"]:
            self.assertIn("60-30-10", (REPO / f).read_text(encoding="utf-8"), f)


if __name__ == "__main__":
    unittest.main()
