"""Checks for the format skills imported from the owner's Ai-Animation repo (.claude/skills/, registered in
studio/IMPORTED_SKILLS.json) and the studio harness around them. The generator test uses a SYNTHETIC FIXTURE skill."""

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / ".claude" / "skills"
REGISTRY = json.loads((REPO / "studio" / "IMPORTED_SKILLS.json").read_text(encoding="utf-8"))
MARK = "<!-- studio-harness:"
SECRET = re.compile(r"\b[0-9a-f]{40,}\b|sk_[A-Za-z0-9]{16,}|xi-api-key\s*[:=]\s*\S{8,}", re.I)
KINDS = {"voice", "script", "song", "third-party-audio", "written", "visual", "clip", "assets"}
sys.path.insert(0, str(REPO / "studio"))
import import_skills as IS  # noqa: E402


class ImportedSkillsTest(unittest.TestCase):
    def test_registry_matches_the_skill_folders(self):
        names = [e["name"] for e in REGISTRY]
        local = list((REPO / "studio" / "skill_sources").glob("*/SKILL.md"))
        self.assertEqual(len(local), 44)
        self.assertEqual(len(names), 47 + len(local))
        self.assertEqual(len(set(names)), len(names))
        on_disk = {p.name for p in SKILLS.iterdir() if (p / "SKILL.md").exists()}
        self.assertTrue(set(names) <= on_disk, set(names) - on_disk)
        for other in sorted(on_disk - set(names)):  # the studio's own skills: no stale imported copy among them
            self.assertNotIn(MARK, (SKILLS / other / "SKILL.md").read_text(encoding="utf-8"), other)
        agents = {p.stem for p in (REPO / ".claude" / "agents").glob("*.md")}
        self.assertFalse(agents & set(names))
        for e in REGISTRY:
            self.assertIn(e["kind"], KINDS, e["name"])
            self.assertTrue(set(e["flags"]) <= set(IS.FLAG_LINES), e["name"])

    def test_every_copy_has_frontmatter_and_the_harness_above_its_steps(self):
        for e in REGISTRY:
            text = (SKILLS / e["name"] / "SKILL.md").read_text(encoding="utf-8")
            m = re.match(r'^---\nname: (.+)\ndescription: (".+")\n(?:argument-hint: (".+")\n)?---\n', text)
            self.assertTrue(m, e["name"])
            self.assertEqual(m.group(1), e["name"])
            self.assertTrue(json.loads(m.group(2)))
            self.assertEqual(text.count(MARK), 1, e["name"])
            head = text.split("\n## ", 1)[0]
            for needle in ["studio/SKILL_HARNESS.md", "studio/LEARNINGS.md", "3 numbered frames at 3 timecodes",
                           "studio/deliver.py", "third_party/ai-animation/LICENSE", IS.WORDS[e["kind"]],
                           "studio/check_env.py", "studio/render_canvas.cjs"]:
                self.assertIn(needle, head, e["name"])
            for flag in e["flags"]:
                self.assertIn(IS.FLAG_LINES[flag], head, e["name"])
            if e["kind"] != "visual":
                self.assertIn("studio/word_timing.py", head, e["name"])
            if e["name"] != IS.ENGINE:
                self.assertIn("From [aanshai.vercel.app/skills]", text, e["name"])  # the original text is kept
            self.assertFalse(SECRET.search(text), e["name"])

    def test_every_copy_has_render_settings_and_working_tool_paths(self):
        for e in REGISTRY:
            if e["name"] == IS.ENGINE:
                continue
            text = (SKILLS / e["name"] / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual(text.count("## Render settings (studio)"), 1, e["name"])
            self.assertLess(text.index("## Render settings (studio)"), text.index("From [aanshai.vercel.app/skills]"))
            for tool in set(re.findall(r"studio/[a-z_]+\.(?:py|cjs)", text)):
                self.assertTrue((REPO / tool).exists(), (e["name"], tool))
            for script in re.findall(r"scripts/[A-Za-z0-9_]+\.py", text):
                self.assertTrue((SKILLS / e["name"] / script).exists(), (e["name"], script))

    def test_local_specs_match_their_copies(self):
        for src in (REPO / "studio" / "skill_sources").glob("*/SKILL.md"):
            name = src.parent.name
            body = IS.parse(src.read_text(encoding="utf-8"), src)[1]
            steps = body.split("## Steps", 1)[1].split("\n---\nFrom [", 1)[0].split("## Helper scripts")[0].strip()
            self.assertIn(steps, (SKILLS / name / "SKILL.md").read_text(encoding="utf-8"), name)
            for f in (src.parent / "scripts").glob("*") if (src.parent / "scripts").is_dir() else []:
                if f.is_file():
                    self.assertEqual(f.read_bytes(), (SKILLS / name / "scripts" / f.name).read_bytes(), (name, f.name))

    def test_risky_skills_carry_their_checks(self):
        by = {e["name"]: e for e in REGISTRY}
        self.assertEqual(by["news-report"]["kind"], "written")
        for name in ["pusho-reel", "latent-reel", "comic-reel", "katha-video", "podcast-explainer"]:
            self.assertEqual(by[name]["kind"], "third-party-audio", name)
        self.assertIn("original-characters", by["titan-anime"]["flags"])
        self.assertIn("brands", by["breaking-news"]["flags"])
        self.assertIn("own-footage-only", by["youtube-clips"]["flags"])
        for name in ["maut-ke-bare-mai-sochte-ho", "baba-pusho", "woof-woof", "latent-comic", "podcast-comic"]:
            self.assertEqual(by[name]["kind"], "third-party-audio", name)
            self.assertIn("real-people", by[name]["flags"], name)
        for name in ["anime-fight", "podcast-cartoon", "kids-story"]:
            self.assertIn("original-characters", by[name]["flags"], name)
        self.assertIn("generated-media", by["miniature-painting-lyrics"]["flags"])
        self.assertEqual(by["phone-chat-lyrics"]["kind"], "song")

    def test_generator_keeps_the_original_text(self):
        md = ('---\nname: demo-skill\ndescription: "Synthetic fixture skill. Use when testing."\n---\n\n# Demo\n\n'
              'One line.\n\n**Input:** a test clip.\n\n## Steps\n\n1. Do it.\n\n---\n'
              'From [aanshai.vercel.app/skills](https://aanshai.vercel.app/skills) · Looks\n')
        front, body = IS.parse(md, Path("demo-skill/SKILL.md"))
        info = IS.describe("demo-skill", front, body, "skills/demo-skill/SKILL.md", "abc1234")
        self.assertEqual((info["group"], info["input"], info["kind"], info["flags"]), ("Looks", "a test clip", "clip", []))
        harness = IS.block("demo-skill", info["source"], "abc1234", info["kind"], info["flags"])
        out = IS.render(front, body, harness, info["input"])
        self.assertTrue(out.startswith('---\nname: demo-skill\ndescription: "Synthetic fixture skill. Use when testing."\n'
                                       'argument-hint: "[a test clip]"\n---\n\n# Demo\n\n' + harness))
        self.assertEqual(out.replace(harness, "").split("---\n", 2)[2], body.replace("# Demo\n", "# Demo\n\n", 1))

    def test_licence_menu_and_wiring(self):
        lic = (REPO / "third_party" / "ai-animation" / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", lic)
        self.assertIn("aansh.ai", lic)
        menu = (REPO / "studio" / "STYLE_MENU.md").read_text(encoding="utf-8")
        for e in REGISTRY:
            self.assertIn(f"`/{e['name']}`", menu)
        for path, needles in {".claude/agents/director.md": ["IMPORTED_SKILLS.json", "SKILL_HARNESS.md"],
                              ".claude/skills/viral-studio/SKILL.md": ["SKILL_HARNESS.md"],
                              "AGENTS.md": ["import_skills.py", "SKILL_HARNESS.md"]}.items():
            text = (REPO / path).read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, path)

    @unittest.skipUnless(shutil.which("node"), "the daksh-ai harness needs Node")
    def test_daksh_ai_template_renders_every_frame_in_its_harness(self):
        d = SKILLS / IS.ENGINE
        assets = [d / "template" / "assets" / f for f in ("words.js", "mouth.js", "engine.js", "scenes.js")]
        r = subprocess.run(["node", str(d / "harness.js"), *map(str, assets)], capture_output=True, text=True,
                           timeout=120)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "ok"), r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
