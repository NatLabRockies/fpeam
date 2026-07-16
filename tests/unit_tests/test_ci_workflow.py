"""Regression tests for CI workflow alignment with test_repo.sh."""

from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "test.yml"


class CIWorkflowAlignmentTest(unittest.TestCase):
    def test_ci_calls_authoritative_repo_gate(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("bash test_repo.sh --ci", workflow_text)
        self.assertNotIn("python -m pytest tests/ -v", workflow_text)


if __name__ == "__main__":
    unittest.main()
