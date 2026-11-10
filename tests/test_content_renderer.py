import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContentRendererTests(unittest.TestCase):
    def test_browser_content_renderer(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests" / "test_content_renderer.js")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
