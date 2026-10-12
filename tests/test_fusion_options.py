"""Fusion option checks run on the merged config and report what will not run."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core import reason_codes as rc
from pyobfus.core.build_plan import build_obfuscation_plan
from pyobfus.core.fusion_options import (
    FUSION_FIELDS,
    check_fusion_combinations,
    requested_fusion_fields,
)

try:
    import pyobfus_pro  # noqa: F401

    PRO_AVAILABLE = True
except ImportError:
    PRO_AVAILABLE = False

requires_pro = pytest.mark.skipif(not PRO_AVAILABLE, reason="pyobfus_pro not installed")

KEY_ENV = "PYOBFUS_TEST_FUSION_KEY"
KEY_B64 = base64.b64encode(b"q" * 32).decode()

SOURCE = (
    "from pyobfus_pro import opacity, Layer\n"
    "RATE = 3\n\n"
    "@opacity(Layer.ENCRYPTED)\n"
    "def price(n):\n"
    "    return n * RATE\n\n"
    "def run():\n"
    "    return price(2)\n"
)


def _cfg(**fields) -> ObfuscationConfig:
    cfg = ObfuscationConfig()
    for name, value in fields.items():
        setattr(cfg, name, value)
    return cfg


def _invoke(args, yaml_text=None, tmp_path=None):
    if yaml_text is not None:
        cfg = tmp_path / "pyobfus.yaml"
        cfg.write_text(yaml_text, encoding="utf-8")
        args = [*args, "--config", str(cfg)]
    with patch("pyobfus.cli.is_trial_active", return_value=True):
        return CliRunner().invoke(main, args, env={KEY_ENV: KEY_B64})


# -- pure checks ------------------------------------------------------------


def test_every_fusion_field_exists_on_config():
    cfg = ObfuscationConfig()
    for name in FUSION_FIELDS:
        assert hasattr(cfg, name), name


def test_requested_fields_follow_declaration_order():
    cfg = _cfg(embed_data="x.bin", vault=True)
    assert requested_fusion_fields(cfg) == ["vault", "embed_data"]


def test_bind_key_env_with_vault_is_an_error():
    errors, _ = check_fusion_combinations(
        _cfg(bind_key_env="K", selective_opacity=True, vault=True)
    )
    assert any("Vault" in e for e in errors)


def test_bind_key_env_without_l3_is_an_error():
    errors, _ = check_fusion_combinations(_cfg(bind_key_env="K"))
    assert any("L3" in e for e in errors)


def test_fingerprint_with_bound_key_warns():
    for bound in ({"bind_key_env": "K"}, {"bind_device": True}):
        errors, warnings = check_fusion_combinations(
            _cfg(fingerprint="buyer-1", selective_opacity=True, **bound)
        )
        assert errors == []
        assert any("cannot be matched to a buyer" in w for w in warnings)


def test_fingerprint_without_l3_warns():
    _, warnings = check_fusion_combinations(_cfg(fingerprint="buyer-1"))
    assert any("no effect without an L3 layer" in w for w in warnings)


def test_plain_fingerprint_is_clean():
    assert check_fusion_combinations(_cfg(fingerprint="b", selective_opacity=True)) == ([], [])


def test_disabled_transforms_lists_every_requested_fusion_field(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("x = 1\n", encoding="utf-8")
    cfg = _cfg(level="pro", selective_opacity=True, bind_key_env="K", embed_data="d.bin")
    plan = build_obfuscation_plan(
        input_path=src,
        output_path=tmp_path / "dist",
        config=cfg,
        config_source="level-default",
        config_path=None,
        preset=None,
        cross_file=True,
        mapping_path=None,
        provenance_manifest_path=None,
        build_report_path=None,
        trace_marker=None,
        cwd=tmp_path,
    )
    disabled = {d["transform"]: d["reason"] for d in plan["disabled_transforms"]}
    for name in ("selective_opacity", "bind_key_env", "embed_data"):
        assert disabled.get(name) == rc.DISABLED_CROSS_FILE_MODE


# -- CLI ----------------------------------------------------------------------


@requires_pro
def test_yaml_vault_with_bind_key_env_is_rejected(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text(SOURCE, encoding="utf-8")
    res = _invoke(
        [str(src), "-o", str(tmp_path / "o.py"), "--level", "pro", "--selective-opacity"],
        yaml_text=f"obfuscation:\n  vault: true\n  bind_key_env: {KEY_ENV}\n",
        tmp_path=tmp_path,
    )
    assert res.exit_code == 1
    assert "does not yet cover Runtime String Vault" in res.output
    assert not (tmp_path / "o.py").exists()


@requires_pro
def test_fingerprint_with_bind_key_env_warns(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text(SOURCE, encoding="utf-8")
    res = _invoke(
        [
            str(src),
            "-o",
            str(tmp_path / "o.py"),
            "--level",
            "pro",
            "--selective-opacity",
            "--bind-key-env",
            KEY_ENV,
            "--fingerprint",
            "buyer-1",
        ]
    )
    assert res.exit_code == 0, res.output
    assert "cannot be matched to a buyer" in res.output


@requires_pro
def test_directory_mode_names_every_skipped_fusion_option(tmp_path):
    src = tmp_path / "pkg"
    src.mkdir()
    (src / "mod.py").write_text(SOURCE, encoding="utf-8")
    res = _invoke(
        [
            str(src),
            "-o",
            str(tmp_path / "dist"),
            "--level",
            "pro",
            "--selective-opacity",
            "--bind-key-env",
            KEY_ENV,
        ]
    )
    assert res.exit_code == 0, res.output
    assert "NOT applied in cross-file directory mode" in res.output
    assert "selective_opacity, bind_key_env" in res.output


def test_mapping_inside_output_directory_warns(tmp_path):
    src = tmp_path / "pkg"
    src.mkdir()
    (src / "mod.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    out = tmp_path / "dist"
    res = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--save-mapping", str(out / "mapping.json")]
    )
    assert res.exit_code == 0, res.output
    assert "mapping file is inside the output directory" in res.output


def test_mapping_outside_output_directory_is_quiet(tmp_path):
    src = tmp_path / "pkg"
    src.mkdir()
    (src / "mod.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    res = CliRunner().invoke(
        main,
        [str(src), "-o", str(tmp_path / "dist"), "--save-mapping", str(tmp_path / "m.json")],
    )
    assert res.exit_code == 0, res.output
    assert "inside the output directory" not in res.output


@requires_pro
def test_scrub_traceback_warns_about_private_key_location(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text("def run():\n    return 1\n", encoding="utf-8")
    res = _invoke([str(src), "-o", str(tmp_path / "o.py"), "--level", "pro", "--scrub-traceback"])
    assert res.exit_code == 0, res.output
    assert "scrub.key.pem" in res.output
    assert (tmp_path / "o.py.scrub.key.pem").exists()
