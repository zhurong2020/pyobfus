"""The builder's declared dependency on the redistributable Pro runtime.

``pyobfus-runtime`` was published (0.1.0) before any builder release emitted
its import namespace. These tests hold the second half of that gate: the
``pyobfus`` wheel must declare a compatible runtime range, the range must
actually admit the runtime this repository ships, the Core wheel must not
swallow the runtime package, provenance output must name the requirement for
artifacts that need it, and a broken environment must be explained rather than
mistaken for a missing licence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from pyobfus import cli as cli_module
from pyobfus.config import ObfuscationConfig
from pyobfus.constants import (
    RUNTIME_DISTRIBUTION,
    RUNTIME_IMPORT_NAME,
    RUNTIME_REQUIREMENT,
    RUNTIME_REQUIREMENT_SPECIFIER,
)
from pyobfus.core.provenance import (
    build_provenance_manifest,
    runtime_requirement_for,
    validate_provenance_manifest,
    verify_manifest_integrity,
)

try:
    import tomllib  # type: ignore[import-not-found,unused-ignore]
except ModuleNotFoundError:  # Python 3.9 / 3.10
    import tomli as tomllib  # type: ignore[import-not-found,no-redef,unused-ignore]

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


# --------------------------------------------------------------------------
# Packaging metadata
# --------------------------------------------------------------------------


def test_pyproject_declares_the_runtime_requirement() -> None:
    project = _load_toml(REPO_ROOT / "pyproject.toml")["project"]
    runtime_deps = [
        dep
        for dep in project["dependencies"]
        if dep.split(">")[0].split("<")[0] == RUNTIME_DISTRIBUTION
    ]
    assert runtime_deps == [RUNTIME_REQUIREMENT], (
        "pyproject.toml must declare exactly the runtime requirement that "
        "pyobfus.constants publishes; the provenance manifest and CLI hint reuse it"
    )


def test_runtime_requirement_admits_the_shipped_runtime_version() -> None:
    runtime_project = _load_toml(REPO_ROOT / "pyobfus_runtime" / "pyproject.toml")["project"]
    assert runtime_project["name"] == RUNTIME_DISTRIBUTION
    shipped = Version(runtime_project["version"])
    assert shipped in SpecifierSet(RUNTIME_REQUIREMENT_SPECIFIER), (
        f"the builder pins {RUNTIME_REQUIREMENT!r} but this repository ships "
        f"{RUNTIME_DISTRIBUTION} {shipped}; widen the range or bump the runtime"
    )


def test_core_wheel_does_not_bundle_the_runtime_package() -> None:
    find = _load_toml(REPO_ROOT / "pyproject.toml")["tool"]["setuptools"]["packages"]["find"]
    assert f"{RUNTIME_IMPORT_NAME}*" in find["exclude"], (
        "the runtime must only ever reach a target through its own wheel; "
        "bundling it into pyobfus would silently fork the implementation"
    )


# --------------------------------------------------------------------------
# Provenance manifest
# --------------------------------------------------------------------------


def _manifest_for(config: ObfuscationConfig, tmp_path: Path) -> dict:
    src = tmp_path / "app.py"
    src.write_text("def predict(x):\n    return x + 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    out.write_text("def a(b):\n    return b + 1\n", encoding="utf-8")
    return build_provenance_manifest(
        input_root=src,
        output_root=out,
        config=config,
        files=[src],
        mapping_path=None,
        preset=None,
        mode="single-file",
    )


def _component_properties(manifest: dict) -> dict:
    props = manifest["cyclonedx"]["metadata"]["component"]["properties"]
    return {prop["name"]: prop["value"] for prop in props}


def test_community_output_records_no_runtime_requirement(tmp_path: Path) -> None:
    config = ObfuscationConfig.community_edition()
    assert runtime_requirement_for(config) is None

    manifest = _manifest_for(config, tmp_path)
    assert manifest["runtime_requirement"] is None
    assert "pyobfus:runtime-requirement" not in _component_properties(manifest)
    assert verify_manifest_integrity(manifest)
    assert validate_provenance_manifest(manifest)["valid"]


def test_pro_output_without_fusion_records_no_runtime_requirement(tmp_path: Path) -> None:
    # String encryption and friends inline their own helpers; only the fusion
    # passes import pyobfus_runtime.
    config = ObfuscationConfig.pro_edition()
    assert config.level == "pro"
    assert runtime_requirement_for(config) is None
    assert _manifest_for(config, tmp_path)["runtime_requirement"] is None


@pytest.mark.parametrize(
    "fusion_flag",
    ["vault", "seal_code", "scrub_traceback", "selective_opacity", "bind_device"],
)
def test_fusion_output_records_the_runtime_requirement(tmp_path: Path, fusion_flag: str) -> None:
    config = ObfuscationConfig.pro_edition()
    setattr(config, fusion_flag, True)

    expected = {
        "package": RUNTIME_DISTRIBUTION,
        "import_name": RUNTIME_IMPORT_NAME,
        "specifier": RUNTIME_REQUIREMENT_SPECIFIER,
        "requirement": RUNTIME_REQUIREMENT,
    }
    assert runtime_requirement_for(config) == expected

    manifest = _manifest_for(config, tmp_path)
    assert manifest["runtime_requirement"] == expected
    assert _component_properties(manifest)["pyobfus:runtime-requirement"] == RUNTIME_REQUIREMENT
    assert verify_manifest_integrity(manifest)
    assert validate_provenance_manifest(manifest)["valid"]


def test_fusion_flags_on_a_community_config_do_not_claim_a_runtime(tmp_path: Path) -> None:
    # The CLI only runs the fusion passes at level "pro"; a stray flag on a
    # community config produces plain output and must not be reported as
    # runtime-dependent.
    config = ObfuscationConfig.community_edition()
    config.vault = True
    assert runtime_requirement_for(config) is None


def test_validator_rejects_a_malformed_runtime_requirement(tmp_path: Path) -> None:
    config = ObfuscationConfig.pro_edition()
    config.vault = True
    manifest = _manifest_for(config, tmp_path)

    broken = json.loads(json.dumps(manifest))
    broken["runtime_requirement"] = {"package": RUNTIME_DISTRIBUTION}
    result = validate_provenance_manifest(broken)
    assert not result["valid"]
    assert any("runtime_requirement.specifier" in error for error in result["errors"])

    not_an_object = json.loads(json.dumps(manifest))
    not_an_object["runtime_requirement"] = RUNTIME_REQUIREMENT
    result = validate_provenance_manifest(not_an_object)
    assert any("runtime_requirement must be null or an object" in e for e in result["errors"])


def test_validator_accepts_manifests_written_before_the_field_existed(tmp_path: Path) -> None:
    manifest = _manifest_for(ObfuscationConfig.community_edition(), tmp_path)
    legacy = json.loads(json.dumps(manifest))
    del legacy["runtime_requirement"]
    # Re-seal: older writers computed their digest over a payload without the key.
    from pyobfus.core.provenance import _integrity_digest_for

    legacy["integrity"] = _integrity_digest_for(
        {k: v for k, v in legacy.items() if k != "integrity"}
    )
    assert validate_provenance_manifest(legacy)["valid"]


# --------------------------------------------------------------------------
# CLI: a broken Pro import must not masquerade as "no licence"
# --------------------------------------------------------------------------


def _simulate_missing_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    error = ModuleNotFoundError(
        f"No module named '{RUNTIME_IMPORT_NAME}'", name=RUNTIME_IMPORT_NAME
    )
    monkeypatch.setattr(cli_module, "PRO_AVAILABLE", False)
    monkeypatch.setattr(cli_module, "PRO_IMPORT_ERROR", error)
    monkeypatch.setattr(cli_module, "is_trial_active", lambda: False)


def test_pro_import_hint_names_the_missing_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    _simulate_missing_runtime(monkeypatch)
    hint = cli_module._pro_import_hint()
    assert hint is not None
    assert RUNTIME_DISTRIBUTION in hint
    assert f'pip install "{RUNTIME_REQUIREMENT}"' in hint


def test_pro_import_hint_is_silent_when_pro_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_module, "PRO_AVAILABLE", True)
    monkeypatch.setattr(cli_module, "PRO_IMPORT_ERROR", None)
    assert cli_module._pro_import_hint() is None


def test_pro_import_hint_reports_other_import_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_module, "PRO_AVAILABLE", False)
    monkeypatch.setattr(
        cli_module, "PRO_IMPORT_ERROR", ImportError("cannot import name 'x' from 'pyobfus_pro'")
    )
    hint = cli_module._pro_import_hint()
    assert hint is not None
    assert "could not be imported: cannot import name 'x'" in hint


@pytest.mark.parametrize(
    "args",
    [
        ["--preset", "commercial"],
        ["--level", "pro"],
        ["--string-encryption"],
    ],
)
def test_pro_gates_explain_a_missing_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, args: list
) -> None:
    _simulate_missing_runtime(monkeypatch)
    src = tmp_path / "app.py"
    src.write_text("x = 1\n", encoding="utf-8")

    result = CliRunner().invoke(cli_module.main, [str(src), "-o", str(tmp_path / "out.py"), *args])
    assert result.exit_code == 1
    assert "requires" in result.output or "require" in result.output
    assert RUNTIME_DISTRIBUTION in result.output, result.output
    assert f'pip install "{RUNTIME_REQUIREMENT}"' in result.output
