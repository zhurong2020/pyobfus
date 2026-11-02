"""Entitlement regression tests: importable Pro is never authorization."""

import ast
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from pyobfus import _entitlement as entitlement
from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.content_transforms import apply_content_transforms
from pyobfus_pro import license as licensing

KEY = "PYOB-AAAA-BBBB-CCCC-DDDD"  # Synthetic only.


@pytest.fixture(params=["none", "trial", "license"])
def access(request, monkeypatch):
    trial = Mock(return_value=request.param == "trial")
    verify = Mock(return_value={"valid": True})
    status = Mock(return_value={"key": KEY} if request.param == "license" else None)
    monkeypatch.setattr("pyobfus.trial.is_trial_active", trial)
    monkeypatch.setattr(licensing, "get_license_status", status)
    monkeypatch.setattr(licensing, "verify_license", verify)
    return request.param, verify


CLI_REQUESTS = [
    ["--level", "pro"],
    *[["--preset", name] for name in ["trial", "commercial", "library", "maximum"]],
    ["--string-encryption"],
    ["--import-obfuscation"],
    ["--anti-debug"],
    ["--control-flow"],
    ["--dead-code"],
    ["--expire", "2099-12-31"],
    ["--bind-machine"],
    ["--max-runs", "5"],
    ["--selective-opacity"],
    ["--seal-code"],
    ["--vault"],
    ["--scrub-traceback"],
    ["--fingerprint", "synthetic-buyer"],
    ["--selective-opacity", "--bind-device"],
    ["--selective-opacity", "--bind-device-id", "synthetic-device"],
    ["--selective-opacity", "--bind-key-env", "SYNTHETIC_KEY"],
    ["--embed-data", "asset.txt"],
    ["--expire-hard", "2099-12-31"],
    ["--period", "5"],
    ["--requires-os", "Linux"],
    ["--requires-python-min", "3.9"],
    ["--requires-arch", "x86_64"],
]


@pytest.mark.parametrize("args", CLI_REQUESTS)
@pytest.mark.parametrize("json_mode", [False, True])
def test_cli_access_matrix(tmp_path, monkeypatch, access, args, json_mode):
    import json
    import pyobfus.cli as cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SYNTHETIC_KEY", "a2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2s=")
    (tmp_path / "asset.txt").write_text("synthetic asset")
    assert cli.PRO_AVAILABLE  # Exact regression: shipped/importable Pro is insufficient.
    src = tmp_path / "input.py"
    src.write_text('message = "hello"\nprint(message)\n')
    out = tmp_path / "out.py"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), *args, *(["--json"] if json_mode else [])]
    )
    state, verify = access
    if state == "none":
        assert result.exit_code == 1, result.output
        assert not out.exists()
        assert "license" in result.output.lower()
        if json_mode:
            payload = json.loads(result.output)
            assert payload["status"] == "error"
            assert payload["error_type"] == "ProAccessError"
            assert payload["ai_hint"]
    else:
        assert result.exit_code == 0, result.output
        assert out.exists()
    if state == "license":
        verify.assert_called_with(KEY)
    else:
        verify.assert_not_called()
    assert KEY not in result.output


@pytest.mark.parametrize("auto", [False, True])
@pytest.mark.parametrize(
    "yaml",
    [
        "preset: commercial",
        "level: pro",
        "string_encryption: true",
        "vault: true",
    ],
)
def test_config_access_matrix(tmp_path, monkeypatch, access, auto, yaml):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "input.py"
    src.write_text('print("hello")\n')
    cfg = tmp_path / "pyobfus.yaml"
    cfg.write_text("obfuscation:\n  " + yaml + "\n")
    out = tmp_path / "out.py"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), *([] if auto else ["--config", str(cfg)])]
    )
    assert result.exit_code == (1 if access[0] == "none" else 0), result.output
    assert out.exists() == (access[0] != "none")


@pytest.mark.parametrize("field", entitlement.PRO_CONFIG_FIELDS)
def test_every_pro_config_field_requires_access(field, monkeypatch):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    monkeypatch.setattr(licensing, "get_license_status", lambda **kw: None)
    cfg = ObfuscationConfig()
    setattr(cfg, field, True)
    with pytest.raises(entitlement.ProAccessError):
        entitlement.require_config_access(cfg)


def test_community_does_not_consult_entitlement(tmp_path, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Community must not read trial/license state or contact a server")

    monkeypatch.setattr("pyobfus.trial.is_trial_active", unexpected)
    monkeypatch.setattr(licensing, "get_license_status", unexpected)
    monkeypatch.setattr(licensing, "verify_license", unexpected)
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "input.py"
    src.write_text("print(42)\n")
    result = CliRunner().invoke(main, [str(src), "-o", str(tmp_path / "out.py"), "--json"])
    assert result.exit_code == 0, result.output
    apply_content_transforms(ast.parse("print(42)"), ObfuscationConfig())


def api_call(name, tmp_path):
    from pyobfus_pro import (
        StringAESEncryptor,
        AntiDebugInjector,
        ControlFlowFlattener,
        DeadCodeInjector,
        ImportObfuscator,
        LicenseEmbedder,
    )
    from pyobfus_pro import build_fusion
    from pyobfus_pro.crossfile_opacity_adapter import encrypt_targets
    from pyobfus_pro.crossfile_opacity_build import _require_authorization
    from pyobfus_pro.transformers import opacity, seal, scrub, vault
    from pyobfus.core.orchestrator import CrossFileOrchestrator

    cfg = ObfuscationConfig.pro_edition()
    constructors = {
        "strings": lambda: StringAESEncryptor(cfg),
        "anti_debug": lambda: AntiDebugInjector(cfg),
        "control_flow": ControlFlowFlattener,
        "dead_code": DeadCodeInjector,
        "imports": ImportObfuscator,
        "license_embed": LicenseEmbedder,
    }
    if name in constructors:
        constructors[name]()
    elif name == "content":
        apply_content_transforms(ast.parse('print("hello")'), cfg)
    elif name == "fusion_pre":
        build_fusion.apply_pre_passes("x = 1", cfg)
    elif name == "fusion_post":
        build_fusion.apply_post_passes("x = 1", cfg)
    elif name == "adapter":
        encrypt_targets("def f():\n    return 1\n", ["f"], key=b"k" * 32, env_name="TEST_KEY")
    elif name == "directory_authorization":
        _require_authorization()
    elif name == "orchestrator":
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.py").write_text("x = 1\n")
        CrossFileOrchestrator(cfg).obfuscate(src, tmp_path / "out")
    else:
        funcs = {
            "opacity": opacity.transform_module,
            "seal": seal.transform_module,
            "vault": vault.transform_module,
        }
        if name == "scrub":
            # Authorization must run before key generation or file creation.
            scrub.transform_module("x = 1", b"synthetic public PEM")
        else:
            funcs[name]("x = 1")


@pytest.mark.parametrize(
    "name",
    [
        "strings",
        "anti_debug",
        "control_flow",
        "dead_code",
        "imports",
        "license_embed",
        "content",
        "fusion_pre",
        "fusion_post",
        "adapter",
        "directory_authorization",
        "orchestrator",
        "opacity",
        "seal",
        "vault",
        "scrub",
    ],
)
def test_library_access_matrix(name, tmp_path, access):
    if access[0] == "none":
        with pytest.raises(entitlement.ProAccessError):
            api_call(name, tmp_path)
    else:
        api_call(name, tmp_path)


@pytest.mark.parametrize("days", [0, 4, 30])
def test_existing_cache_and_offline_grace(monkeypatch, days):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    licensing.cache_license(
        {
            "key": KEY,
            "type": "professional",
            "expires": "2099-12-31",
            "verified": (datetime.now() - timedelta(days=days)).isoformat(),
        }
    )
    online = Mock(side_effect=licensing.LicenseServerUnreachableError("synthetic offline"))
    monkeypatch.setattr(licensing, "_verify_online", online)
    entitlement.require_pro_access()
    assert online.call_count == (0 if days < 3 else 1)


@pytest.mark.parametrize("error", [licensing.LicenseRevokedError, licensing.LicenseExpiredError])
def test_definitive_rejection_overrides_stale_cache(monkeypatch, error):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    licensing.cache_license(
        {
            "key": KEY,
            "type": "professional",
            "expires": "2099-12-31",
            "verified": (datetime.now() - timedelta(days=4)).isoformat(),
        }
    )
    monkeypatch.setattr(licensing, "_verify_online", Mock(side_effect=error(KEY)))
    with pytest.raises(entitlement.ProAccessError) as exc:
        entitlement.require_pro_access()
    assert KEY not in str(exc.value)


def test_false_verification_is_denied(monkeypatch):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    monkeypatch.setattr(licensing, "get_license_status", lambda **kw: {"key": KEY})
    monkeypatch.setattr(licensing, "verify_license", lambda key: {"valid": False})
    with pytest.raises(entitlement.ProAccessError):
        entitlement.require_pro_access()


def test_offline_registration_recovery_remains_supported():
    from pyobfus_pro.cli import cli

    result = CliRunner().invoke(cli, ["register", KEY, "--no-verify"])
    assert result.exit_code == 0
    entitlement.require_pro_access()


def test_expired_cache_is_denied_after_refresh_fails(monkeypatch):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    licensing.cache_license(
        {
            "key": KEY,
            "type": "professional",
            "expires": "2000-01-01",
            "verified": (datetime.now() - timedelta(days=4)).isoformat(),
        }
    )
    monkeypatch.setattr(
        licensing,
        "_verify_online",
        Mock(side_effect=licensing.LicenseServerUnreachableError("synthetic offline")),
    )
    with pytest.raises(entitlement.ProAccessError, match="expired"):
        entitlement.require_pro_access()


def test_build_approval_is_scoped_and_offline_retry_happens_once(monkeypatch):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    licensing.cache_license(
        {
            "key": KEY,
            "type": "professional",
            "expires": "2099-12-31",
            "verified": (datetime.now() - timedelta(days=4)).isoformat(),
        }
    )
    online = Mock(side_effect=licensing.LicenseServerUnreachableError("synthetic offline"))
    monkeypatch.setattr(licensing, "_verify_online", online)
    with entitlement.entitlement_session():
        entitlement.require_pro_access()
        with entitlement.entitlement_session():
            entitlement.require_pro_access()
    assert online.call_count == 1
    licensing.remove_cached_license()
    with entitlement.entitlement_session(), pytest.raises(entitlement.ProAccessError):
        entitlement.require_pro_access()


def test_upgrade_does_not_claim_an_importable_package_is_licensed(monkeypatch):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    result = CliRunner().invoke(main, ["--upgrade"])
    assert result.exit_code == 0
    assert "COMPONENTS INSTALLED" in result.output
    assert "Your Pro license is active" not in result.output


def test_gate_covers_all_schema_pro_fields():
    from pyobfus.config_schema import _PRO_ONLY_FIELDS

    assert _PRO_ONLY_FIELDS <= set(entitlement.PRO_CONFIG_FIELDS)
