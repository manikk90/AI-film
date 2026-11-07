"""Explicit browser selection uses local executables without downloading them."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node is required for renderer configuration")
class ChromiumConfigurationTest(unittest.TestCase):
    def options(self, value=None):
        env = os.environ.copy()
        env.pop("AIFILM_CHROMIUM_EXECUTABLE", None)
        if value is not None:
            env["AIFILM_CHROMIUM_EXECUTABLE"] = value
        code = "const {launchOptions}=require(process.argv[1]); console.log(JSON.stringify(launchOptions()))"
        return subprocess.run(["node", "-e", code, str(ROOT / "studio/chromium.cjs")],
                              env=env, capture_output=True, text=True, timeout=10)

    def test_default_keeps_playwright_browser_selection(self):
        result = self.options()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})

    def test_explicit_executable_is_passed_without_shell_interpretation(self):
        # Configuration checks need an executable, not an actual browser launch.
        executable = str(Path(sys.executable).resolve())
        result = self.options(executable)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"executablePath": executable})

    def test_missing_or_relative_executable_is_rejected(self):
        for value in ("chromium", str(ROOT / "missing-browser")):
            with self.subTest(value=value):
                result = self.options(value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("AIFILM_CHROMIUM_EXECUTABLE", result.stderr)
