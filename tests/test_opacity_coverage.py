"""Opacity coverage: say how many rule-matched functions were not encrypted."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig

pyobfus_pro = pytest.importorskip("pyobfus_pro")
from pyobfus_pro.build_fusion import opacity_coverage  # noqa: E402

SOURCE = """\
def secret_top(x):
    return x * 7 + 1


class Engine:
    def secret_method(self, x):
        return x + 3

    def public_method(self):
        return 1


def outer():
    def secret_inner():
        return 2

    return secret_inner()


def run():
    return secret_top(2) + Engine().secret_method(1) + outer()
"""

TOML = """\
default_layer = "obfuscated"

[[rules]]
pattern = "*secret_*"
layer = "encrypted"
"""


@pytest.fixture
def project(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text(SOURCE, encoding="utf-8")
    cfg = tmp_path / "opacity.toml"
    cfg.write_text(TOML, encoding="utf-8")
    keep = tmp_path / "pyobfus.yaml"
    keep.write_text("obfuscation:\n  exclude_names: [run]\n", encoding="utf-8")
    return src, cfg, keep


def test_counts_methods_and_nested_functions(project):
    src, cfg, _ = project
    config = ObfuscationConfig()
    config.opacity_config = str(cfg)
    counts = opacity_coverage(src.read_text(), config, module_qualname="mod")
    assert counts == {"l3_skipped_methods": 1, "l3_skipped_nested": 1}


def test_no_config_counts_nothing(project):
    src, _, _ = project
    counts = opacity_coverage(src.read_text(), ObfuscationConfig(), module_qualname="mod")
    assert counts == {"l3_skipped_methods": 0, "l3_skipped_nested": 0}


def test_build_warns_and_reports_counts(project, tmp_path):
    src, cfg, keep = project
    out = tmp_path / "out.py"
    report = tmp_path / "report.json"
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
                str(keep),
                "--opacity-config",
                str(cfg),
                "--build-report",
                str(report),
            ],
        )
    assert res.exit_code == 0, res.output
    assert "2 function(s) matched by opacity rules were NOT encrypted" in res.output
    transformations = json.loads(report.read_text())["transformations"]
    assert transformations["l3_functions_encrypted"] == 1
    assert transformations["l3_skipped_methods"] == 1
    assert transformations["l3_skipped_nested"] == 1
    assert "secret_method" not in report.read_text()


def test_community_build_report_keeps_its_shape(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text("def f():\n    return 1\n", encoding="utf-8")
    report = tmp_path / "report.json"
    res = CliRunner().invoke(
        main, [str(src), "-o", str(tmp_path / "o.py"), "--build-report", str(report)]
    )
    assert res.exit_code == 0, res.output
    transformations = json.loads(report.read_text())["transformations"]
    assert not any(key.startswith("l3_") for key in transformations)
