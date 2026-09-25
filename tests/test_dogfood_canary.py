"""Cheap guards for the self-dogfooding fixture and driver.

The lanes themselves run in the Dogfood workflow (see
docs/SELF_DOGFOODING_BEST_PRACTICES.md), not in this matrix — obfuscating and
building on every Python/OS combination would multiply cost for no extra
signal. These two guards are cheap: they catch a broken canary or a syntax
error in the driver fast, so the dogfood workflow is never the first to notice.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANARY = REPO_ROOT / "dogfood" / "canary"
DRIVER = REPO_ROOT / "scripts" / "dogfood" / "run.py"


def test_canary_runs_and_prints_stable_result() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(CANARY)
    proc = subprocess.run(
        [sys.executable, str(CANARY / "app.py")],
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "25"


def test_dogfood_driver_compiles() -> None:
    compile(DRIVER.read_text(encoding="utf-8"), str(DRIVER), "exec")
