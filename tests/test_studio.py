"""Checks for the viral studio: agent and skill definitions, the learning ledger and the templates (text only)."""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AGENTS = REPO / ".claude" / "agents"
SKILLS = REPO / ".claude" / "skills"
STUDIO = REPO / "studio"
TOOLS = {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"}
SECTIONS = ["Global", "Social", "Research", "Writer", "Director", "Editor", "Production"]
SECRET = re.compile(r"\b[0-9a-f]{40,}\b|sk_[A-Za-z0-9]{16,}|xi-api-key\s*[:=]\s*\S{8,}", re.I)


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    fields = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    return fields, text[m.end():]


class StudioTest(unittest.TestCase):
    def test_agents(self):
        names = sorted(p.stem for p in AGENTS.glob("*.md"))
        self.assertEqual(names, ["director", "mann", "marich", "researcher", "social", "writer"])
        for p in AGENTS.glob("*.md"):
            with self.subTest(agent=p.stem):
                fields, body = frontmatter(p)
                self.assertEqual(fields.get("name"), p.stem)
                self.assertGreater(len(fields.get("description", "")), 80)
                if "tools" in fields:
                    self.assertLessEqual({t.strip() for t in fields["tools"].split(",")}, TOOLS)
                self.assertIn("studio/LEARNINGS.md", body, "every agent must read the ledger")
                self.assertIn("learnings", body.lower(), "every agent must propose learnings")

    def test_writer_and_director_respect_the_script_gate(self):
        writer = (AGENTS / "writer.md").read_text(encoding="utf-8")
        director = (AGENTS / "director.md").read_text(encoding="utf-8")
        self.assertIn("skills/ai-writer/SKILL.md", writer)
        self.assertIn("Never starts production", writer)
        self.assertIn("only after the owner approves the script", director)

    def test_skills(self):
        for name in ["viral-studio", "studio-learn", "mann-edit", "mann-style-lab"]:
            with self.subTest(skill=name):
                fields, body = frontmatter(SKILLS / name / "SKILL.md")
                self.assertEqual(fields.get("name"), name)
                self.assertGreater(len(fields.get("description", "")), 80)
        flow = (SKILLS / "viral-studio" / "SKILL.md").read_text(encoding="utf-8")
        for agent in ["social", "researcher", "writer", "director", "studio-learn", "Gate 2", "Gate 3", "3 frames at 3 timecodes", "music sketch", "experiment", "studio/NIGHTLY.md"]:
            self.assertIn(agent, flow)

    def test_learning_ledger(self):
        text = (STUDIO / "LEARNINGS.md").read_text(encoding="utf-8")
        heads = re.findall(r"^## (.+)$", text, re.M)
        for s in SECTIONS:
            self.assertIn(s, heads)
        entries = [l for l in text.splitlines() if l.startswith("- ")]
        self.assertGreater(len(entries), 5)
        for line in entries:
            with self.subTest(entry=line[:60]):
                self.assertRegex(line, r"^- (~~superseded \d{4}-\d{2}-\d{2}~~ )?\d{4}-\d{2}-\d{2} · (owner|result|observed) · \S")

    def test_no_secrets_in_studio_files(self):
        files = list(STUDIO.rglob("*.md")) + list(AGENTS.glob("*.md")) + list(SKILLS.rglob("*.md"))
        for p in files:
            with self.subTest(file=str(p.relative_to(REPO))):
                self.assertIsNone(SECRET.search(p.read_text(encoding="utf-8")))

    def test_templates(self):
        status = (STUDIO / "templates" / "STATUS.md").read_text(encoding="utf-8")
        self.assertIn("Gate 2", status)
        self.assertIn("blocked until Gate 2", status)
        self.assertIn("blocked until Gate 3", status)
        self.assertIn("3 timecode frames", status)

    def test_nightly_scan_and_style_menu(self):
        nightly = (STUDIO / "NIGHTLY.md").read_text(encoding="utf-8")
        for needle in ["10 topics", "STYLE_MENU.md", "experiment", "Never post"]:
            self.assertIn(needle, nightly)
        menu = (STUDIO / "STYLE_MENU.md").read_text(encoding="utf-8")
        rows = [l for l in menu.splitlines() if l.startswith("| ") and "`" in l]
        self.assertGreaterEqual(len(rows), 133)
        for slug in [p.parent.name for p in (REPO / "styles").glob("*/style.json")]:
            self.assertIn(f"`{slug}`", menu)

    def test_mann_storyboard_gate_and_learning(self):
        mann = (AGENTS / "mann.md").read_text(encoding="utf-8")
        for needle in ["storyboard (gate, mandatory)", "approve --clips", "approve-style", "lock-script", "approve --words", "editor/rules.json", "mann-style-lab", "/studio-learn",
                       "Never post", "experiment"]:
            self.assertIn(needle, mann)
        learn = (SKILLS / "studio-learn" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("editor/rules.json", learn)
        self.assertIn("**Editor**", learn)

    def test_director_preview_gate_and_music(self):
        director = (AGENTS / "director.md").read_text(encoding="utf-8")
        for needle in ["3 frames at 3 different timecodes", "music sketch", "Music (special attention)", "experiment"]:
            self.assertIn(needle, director)
        self.assertTrue((STUDIO / "templates" / "00-brief.md").exists())

    def test_director_delivers_an_editor_package(self):
        director = (AGENTS / "director.md").read_text(encoding="utf-8")
        for needle in ["studio/editor_package.py", "editor.json", "post-fader, pre-master", "editor package", "textless",
                       "studio/deliver.py", "2 files"]:
            self.assertIn(needle, director)
        self.assertIn("editor package", (SKILLS / "viral-studio" / "SKILL.md").read_text(encoding="utf-8"))
        template = json.loads((STUDIO / "templates" / "editor.json").read_text(encoding="utf-8"))
        for key in ["fps", "picture", "shots", "audio", "subtitles", "picture_textless"]:
            self.assertIn(key, template)


if __name__ == "__main__":
    unittest.main()
