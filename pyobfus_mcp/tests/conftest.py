"""Shared pytest fixtures for the pyobfus_mcp test suite.

Two pieces of test-environment setup wired up `autouse`:

1. **PYOBFUS_MCP_PROJECT_ROOT** is set to `tempfile.gettempdir()` so the
   `tmp_path` pytest fixture (which lives under that directory on every
   platform we support) is always inside the path-scoping sandbox.
   Production deployments set this env var to the actual project root.

2. **Rate-limit state** is cleared before every test so that token-bucket
   accumulation in one test cannot make a later test fail spuriously.
"""

from __future__ import annotations

import tempfile

import pytest


@pytest.fixture(autouse=True)
def _security_test_setup(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset all global security state before each test."""
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", tempfile.gettempdir())

    # Late import: avoid module-level import side effects in conftest.
    from pyobfus_mcp._security import reset_rate_limit_state

    reset_rate_limit_state()

    # Trial guidance tests read status before/after the tool call. Keep those
    # reads off the developer's real ~/.pyobfus, even with the normal HOME.
    import pyobfus.trial as trial

    monkeypatch.setattr(trial, "TRIAL_DIR", tmp_path / ".pyobfus")
    monkeypatch.setattr(trial, "TRIAL_FILE", tmp_path / ".pyobfus" / "trial.json")
