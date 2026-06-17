"""Regression tests for the Copilot CLI policy hook."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


def load_policy_module():
    """Load the standalone hook module from `scripts/`."""
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "copilot_tool_policy.py"
    spec = importlib.util.spec_from_file_location("copilot_tool_policy", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


policy = load_policy_module()


class CopilotToolPolicyTest(unittest.TestCase):
    """Policy hook regressions that mirror live Copilot CLI shell payloads."""

    def setUp(self):
        self.repo_policy = policy.AgentPolicy(
            allow_git_execution=True,
            allow_pr_execution=True,
        )

    def test_gh_alias_set_is_blocked(self):
        allowed, reason = policy.evaluate_command(
            "gh alias set gp 'git push'",
            self.repo_policy,
        )

        self.assertFalse(allowed)
        self.assertIn("alias", reason.lower())

    def test_shell_payload_for_gh_alias_set_is_denied(self):
        payload = {
            "toolName": "bash",
            "toolArgs": {"command": "gh alias set gp 'git push'"},
        }
        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout), mock.patch.object(policy.sys, "stdin", stdin):
            exit_code = policy.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {
                "permissionDecision": "deny",
                "permissionDecisionReason": "GitHub CLI alias creation is disabled by this repo policy.",
            },
        )


if __name__ == "__main__":
    unittest.main()
