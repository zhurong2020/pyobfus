"""key_exposure: L3 limits shown without a model (synthetic fixture only)."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from benchmarks.llm_resistance.key_exposure import runtime_capture, static_recover
from pyobfus.cli import main

pytest.importorskip("pyobfus_pro")

KEY_ENV = "PYOBFUS_KEY_EXPOSURE_TEST"
KEY_B64 = base64.b64encode(b"e" * 32).decode()

SOURCE = """\
from pyobfus_pro import opacity, Layer


@opacity(Layer.ENCRYPTED)
def price(units):
    return units * 7 + 1234567


def run():
    return price(2)


if __name__ == "__main__":
    print(run())
"""


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))


def _build(tmp_path: Path, name: str, *options: str) -> Path:
    src = tmp_path / f"{name}_src.py"
    src.write_text(SOURCE, encoding="utf-8")
    cfg = tmp_path / "pyobfus.yaml"
    cfg.write_text("obfuscation:\n  exclude_names: [run]\n", encoding="utf-8")
    out = tmp_path / f"{name}.py"
    with patch("pyobfus.cli.is_trial_active", return_value=True):
        res = CliRunner().invoke(
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
                *options,
            ],
            env={KEY_ENV: KEY_B64},
        )
    assert res.exit_code == 0, res.output
    return out


def test_default_l3_decrypts_statically(tmp_path):
    report = static_recover(_build(tmp_path, "plain"))
    assert report["key_in_artifact"] is True
    assert len(report["protected_functions"]) == 1
    (recovered,) = report["recovered"].values()
    assert "1234567" in recovered["constants"]


def test_app_provided_key_blocks_static_but_not_the_operator(tmp_path):
    artifact = _build(tmp_path, "keyed", "--bind-key-env", KEY_ENV)
    report = static_recover(artifact)
    assert report["key_in_artifact"] is False
    assert report["recovered"] == {}

    without_key = runtime_capture(artifact)
    assert without_key["status"].startswith("failed")
    assert without_key["captured"] == []

    with_key = runtime_capture(artifact, env={KEY_ENV: KEY_B64})
    assert with_key["status"] == "ran"
    assert with_key["captured"] == report["protected_functions"]
