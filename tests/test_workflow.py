import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "deploy.yml"


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = WORKFLOW_PATH.read_text(encoding="utf-8")
        cls.workflow = yaml.load(cls.raw, Loader=yaml.BaseLoader)

    def test_workflow_validates_pull_requests_and_deploys_master(self):
        triggers = self.workflow["on"]
        self.assertIn("pull_request", triggers)
        self.assertEqual(triggers["push"]["branches"], ["master"])
        self.assertIn("workflow_dispatch", triggers)
        self.assertEqual(self.workflow["jobs"]["deploy"]["needs"], "build")
        self.assertEqual(self.workflow["jobs"]["build"]["permissions"]["pages"], "write")
        self.assertEqual(self.workflow["jobs"]["deploy"]["permissions"]["pages"], "write")
        self.assertEqual(self.workflow["jobs"]["deploy"]["permissions"]["id-token"], "write")

    def test_external_actions_are_pinned_to_full_commits(self):
        action_refs = re.findall(r"uses:\s+[^@\s]+@([^\s#]+)", self.raw)
        self.assertGreaterEqual(len(action_refs), 6)
        for reference in action_refs:
            with self.subTest(reference=reference):
                self.assertRegex(reference, r"^[0-9a-f]{40}$")

    def test_texlive_container_is_pinned_by_digest(self):
        self.assertIn("texlive-full:20260701@sha256:", self.raw)


if __name__ == "__main__":
    unittest.main()
