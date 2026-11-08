"""Checks for caveman mode, the studio's token diet (studio/CAVEMAN.md, studio/caveman.py).
Every project and transcript here is a SYNTHETIC FIXTURE."""

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "studio"))
import caveman as C  # noqa: E402

AGENTS = REPO / ".claude" / "agents"
EFFORT = {"social": "medium", "researcher": "medium", "writer": "high", "director": "high", "mann": "high", "marich": "high"}


def block(text):
    m = re.search(r"<!-- caveman -->\n.*?<!-- /caveman -->", text, re.S)
    return m.group(0) if m else None


class WiringTest(unittest.TestCase):
    def test_every_agent_carries_the_same_short_block_and_its_effort(self):
        source = block((REPO / "studio" / "CAVEMAN.md").read_text(encoding="utf-8"))
        self.assertIsNotNone(source)
        self.assertLessEqual(len(source.splitlines()), 13)  # the block itself rides along on every request
        self.assertEqual(sorted(EFFORT), sorted(p.stem for p in AGENTS.glob("*.md")))
        for name, effort in EFFORT.items():
            text = (AGENTS / f"{name}.md").read_text(encoding="utf-8")
            front = text.split("\n---\n", 1)[0] + "\n"
            self.assertIn(f"\neffort: {effort}\n", front, name)
            window = re.search(r"\nautoCompactWindow: (\d+)\n", front)
            self.assertTrue(window and 100000 <= int(window.group(1)) <= 1000000, name)
            self.assertEqual(block(text), source, name)

    def test_the_orchestrator_harness_and_docs_point_to_the_diet(self):
        needles = {
            ".claude/skills/viral-studio/SKILL.md": ["studio/CAVEMAN.md", "caveman.py check", "DIGEST.md", "caveman.py usage"],
            "studio/SKILL_HARNESS.md": ["studio/CAVEMAN.md"],
            "AGENTS.md": ["studio/CAVEMAN.md"],
            "studio/README.md": ["caveman.py"],
            "studio/LEARNINGS.md": ["studio/CAVEMAN.md"],
        }
        for path, words in needles.items():
            text = (REPO / path).read_text(encoding="utf-8")
            for w in words:
                self.assertIn(w, text, path)

    def test_each_role_reads_global_and_its_own_sections_only(self):
        for role, own in C.ROLES.items():
            self.assertEqual(re.findall(r"^## (.+)$", C.cmd_rules(role), re.M), ["Global"] + own, role)
        with self.assertRaises(SystemExit):
            C.cmd_rules("nobody")


class ReadAndBudgetTest(unittest.TestCase):
    MD = "# T\nintro\n## A one\na\n### A sub\nsub\n## B two\nb\n```\n## not a heading\n```\n"

    def test_sections_skip_code_and_keep_subsections(self):
        _, secs = C.sections(self.MD)
        self.assertEqual([s[1] for s in secs], ["T", "A one", "A sub", "B two"])
        self.assertEqual(C.pick(self.MD, ["a one"]), "## A one\na\n### A sub\nsub")
        self.assertEqual(C.pick(self.MD, ["two"]), "## B two\nb\n```\n## not a heading\n```")
        with self.assertRaises(SystemExit):
            C.pick(self.MD, ["missing"])

    def test_check_flags_only_files_over_their_budget(self):
        with tempfile.TemporaryDirectory() as d:  # SYNTHETIC FIXTURE project
            root = Path(d)
            (root / "04-script").mkdir()
            (root / "FACTS.md").write_text("| F01 | synthetic fixture fact |\n", encoding="utf-8")
            (root / "04-script" / "SCRIPT_v1.md").write_text("क" * 5000, encoding="utf-8")  # 15,000 bytes
            (root / "notes.md").write_text("y" * 99 * 1024, encoding="utf-8")  # not a budgeted file
            lines, over = C.check(root)
            self.assertEqual(over, 1)
            self.assertTrue(lines[0].startswith("OVER") and lines[0].endswith("04-script/SCRIPT_v1.md"), lines)
            self.assertEqual(C.check(root, scale=2)[1], 0)
            self.assertEqual(len(C.check(root, show_all=True)[0]), 3)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(C.main(["check", str(root)]), 1)


class UsageTest(unittest.TestCase):
    def test_usage_counts_each_request_once_and_names_the_agents(self):
        u1 = {"input_tokens": 10, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 0, "output_tokens": 50}
        u2 = dict(u1, cache_creation_input_tokens=3000, cache_read_input_tokens=1000, output_tokens=20)
        read = {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": str(C.REPO / "projects/x/FACTS.md")}}
        lines = [
            {"type": "assistant", "effort": "max", "message": {"id": "m1", "usage": u1, "content": [{"type": "thinking"}]}},
            {"type": "assistant", "effort": "max", "message": {"id": "m1", "usage": u1, "content": [read]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "z" * 2048}]}},
            {"type": "assistant", "effort": "max", "message": {"id": "m2", "usage": u2, "content": [{"type": "text", "text": "ok"}]}},
            {"type": "assistant", "isSidechain": True, "message": {"id": "side", "usage": u2}},
        ]
        with tempfile.TemporaryDirectory() as d:  # SYNTHETIC FIXTURE transcripts
            main = Path(d) / "s.jsonl"
            main.write_text("\n".join([json.dumps(x) for x in lines] + ["not json"]), encoding="utf-8")
            sub = Path(d) / "s" / "subagents"
            sub.mkdir(parents=True)
            (sub / "agent-a1.jsonl").write_text(json.dumps(
                {"type": "assistant", "effort": "medium", "message": {"id": "x", "usage": u1}}), encoding="utf-8")
            (sub / "agent-a1.meta.json").write_text(json.dumps(
                {"agentType": "writer", "description": "Synthetic job"}), encoding="utf-8")
            r = C.read_run(main, main=True)
            self.assertEqual((r["requests"], r["sent"], r["peak"], r["output"], r["effort"]), (2, 5020, 4010, 70, "max"))
            self.assertEqual(r["results"], [(2048, "Read", "projects/x/FACTS.md")])
            report = C.usage(main, top=1)
        self.assertIn("writer · Synthetic job", report)
        self.assertIn("medium", report)
        self.assertRegex(report, r"\ntotal\s+3\s")
        self.assertIn("2.0KB main session Read projects/x/FACTS.md", report)


if __name__ == "__main__":
    unittest.main()
