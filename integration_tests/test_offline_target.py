"""Pro artifacts must run on an offline target that has only the runtime wheel.

Every other test imports ``pyobfus_runtime`` from this checkout, so they cannot
notice when generated code calls something the *released* runtime lacks
(2026-10-12: Core 0.5.30's ``--bind-key-env`` / ``--expire-warn-days``
artifacts failed against the published runtime 0.1.0). Here the target is a
fresh virtual environment that installs the runtime wheel built from this
checkout with ``pip install --no-index``, then runs each artifact in a
subprocess that cannot see the repository.

Only preparing the wheelhouse (downloading the runtime's own dependencies)
uses the network, the way a real offline delivery is staged; the test skips
when that download is impossible.
"""

from __future__ import annotations

import base64
import datetime as _dt
import os
import subprocess
import sys
import venv
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pyobfus.cli import main

try:
    import pyobfus_pro  # noqa: F401

    PRO_AVAILABLE = True
except ImportError:  # pragma: no cover - Pro ships in the same wheel
    PRO_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PRO_AVAILABLE, reason="pyobfus_pro not installed")

REPO_ROOT = Path(__file__).resolve().parent.parent
KEY_ENV = "PYOBFUS_OFFLINE_TARGET_KEY"
KEY_B64 = base64.b64encode(b"k" * 32).decode()
WRONG_KEY_B64 = base64.b64encode(b"w" * 32).decode()

SOURCE = """\
from pyobfus_pro import opacity, Layer

RATE = 7


@opacity(Layer.ENCRYPTED)
def price(units):
    return units * RATE + 3


def run():
    return price(6)


if __name__ == "__main__":
    print(run())
"""


def _clean_env(**extra: str) -> dict:
    """Environment for the target: nothing from this checkout leaks in."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("PYTHONPATH", "PYTHONHOME", KEY_ENV)
    }
    env.update(extra)
    return env


def _venv_python(env_dir: Path) -> Path:
    if os.name == "nt":
        return env_dir / "Scripts" / "python.exe"
    return env_dir / "bin" / "python"


@pytest.fixture(scope="module")
def target_python(tmp_path_factory) -> Path:
    """A fresh venv with only the runtime wheel installed, offline."""
    root = tmp_path_factory.mktemp("offline_target")
    wheelhouse = root / "wheelhouse"
    # Build with isolation so the runtime's declared build requirements are
    # used, not whatever setuptools the test environment happens to have.
    built = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "-w",
            str(wheelhouse),
            str(REPO_ROOT / "pyobfus_runtime"),
        ],
        capture_output=True,
        text=True,
    )
    assert built.returncode == 0, built.stdout[-2000:] + built.stderr[-2000:]
    runtime_wheel = next(wheelhouse.glob("pyobfus_runtime-*.whl"))
    staged = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "-d",
            str(wheelhouse),
            str(runtime_wheel),
        ],
        capture_output=True,
        text=True,
    )
    if staged.returncode != 0:
        pytest.skip(f"cannot stage the runtime's dependencies: {staged.stderr[-300:]}")

    env_dir = root / "venv"
    venv.create(env_dir, with_pip=True)
    python = _venv_python(env_dir)
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-q",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            "pyobfus-runtime",
        ],
        check=True,
        capture_output=True,
        env=_clean_env(),
    )
    probe = subprocess.run(
        [str(python), "-c", "import pyobfus, sys; sys.exit(0)"],
        capture_output=True,
        env=_clean_env(),
    )
    assert probe.returncode != 0, "the target must not have the builder installed"
    return python


def _build(tmp_path: Path, name: str, *options: str) -> Path:
    src = tmp_path / "src" / f"{name}.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(SOURCE, encoding="utf-8")
    cfg = tmp_path / "pyobfus.yaml"
    cfg.write_text("obfuscation:\n  exclude_names: [run]\n", encoding="utf-8")
    out_dir = tmp_path / "ship"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{name}.py"
    with patch("pyobfus.cli.is_trial_active", return_value=True):
        result = CliRunner().invoke(
            main,
            [
                str(src),
                "-o",
                str(out),
                "--level",
                "pro",
                "--config",
                str(cfg),
                "--selective-opacity",
                "--save-mapping",
                str(tmp_path / "private" / f"{name}.map.json"),
                *options,
            ],
            env={KEY_ENV: KEY_B64},
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.output
    return out


def _run(python: Path, artifact: Path, **extra_env: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(python), "-E", "-s", str(artifact)],
        cwd=str(artifact.parent),
        env=_clean_env(**extra_env),
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_app_provided_key_artifact(target_python, tmp_path):
    artifact = _build(tmp_path, "keyed", "--bind-key-env", KEY_ENV)

    ok = _run(target_python, artifact, **{KEY_ENV: KEY_B64})
    assert ok.returncode == 0, ok.stderr
    assert ok.stdout.strip() == "45"

    missing = _run(target_python, artifact)
    assert missing.returncode != 0
    assert "LicenseBindingError" in missing.stderr

    wrong = _run(target_python, artifact, **{KEY_ENV: WRONG_KEY_B64})
    assert wrong.returncode != 0
    assert "OpacityRuntimeError" in wrong.stderr


def test_expiry_warning_artifact(target_python, tmp_path):
    expires = (_dt.date.today() + _dt.timedelta(days=10)).isoformat()
    artifact = _build(tmp_path, "expiring", "--expire-hard", expires, "--expire-warn-days", "30")

    result = _run(target_python, artifact)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "45"
    assert "LicenseExpiryWarning" in result.stderr


def test_device_bound_artifact(target_python, tmp_path):
    artifact = _build(tmp_path, "bound", "--bind-device")

    result = _run(target_python, artifact)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "45"


def test_shipped_directory_holds_only_artifacts(target_python, tmp_path):
    _build(tmp_path, "keyed", "--bind-key-env", KEY_ENV)
    shipped = sorted(p.name for p in (tmp_path / "ship").iterdir())
    assert shipped == ["keyed.py"]
    text = (tmp_path / "ship" / "keyed.py").read_text(encoding="utf-8")
    assert "RATE = 7" not in text
    assert "units * RATE" not in text
