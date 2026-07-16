"""Regression test: CI must not depend on gitignored, toolkit-managed local files.

`test_repo.sh`, `pyproject.toml`, `AGENTS.md`, `ai_context/`, etc. are agent-workflow
scaffolding kept local-only (see the "Agent workflow scaffolding" block in
`.gitignore`) and are never committed to this repository. A fresh CI checkout will
not have them, so the CI workflow must invoke tracked `pixi.toml` tasks directly
(`pixi run format-check`, `pixi run lint`, `pixi run test`) rather than a script or
config file that only exists in a developer's local working tree.
"""

from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "test.yml"

# Files/dirs that are intentionally gitignored (agent-workflow scaffolding) and
# therefore must never be referenced by a committed CI workflow.
LOCAL_ONLY_REFERENCES = (
    "test_repo.sh",
    "pyproject.toml",
    "AGENTS.md",
    "ai_context/",
)


class CIWorkflowAlignmentTest(unittest.TestCase):
    def test_ci_does_not_reference_gitignored_local_files(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        for reference in LOCAL_ONLY_REFERENCES:
            self.assertNotIn(
                reference,
                workflow_text,
                msg=(
                    f"CI workflow references '{reference}', which is gitignored "
                    "local-only tooling and will not exist on a fresh checkout."
                ),
            )

    def test_ci_uses_pixi_tasks(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        for task in ("pixi run format-check", "pixi run lint", "pixi run test"):
            self.assertIn(task, workflow_text)


if __name__ == "__main__":
    unittest.main()
