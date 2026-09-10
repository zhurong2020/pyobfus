"""Tests for the transparent build marker (docs/COMMUNITY_BUILD_MARKER_DESIGN.md).

The marker is attribution, not protection. What these tests actually guard:

1. **No absolute path reaches shipped output.** Before 0.5.23 the header
   embedded the caller's absolute input path, which leaks the build machine's
   directory layout and usually a username into every file a customer receives.
2. **The marker is emitted at all.** Also before 0.5.23, the single-file
   non-fusion path computed the header and then threw it away by regenerating
   from the AST, and directory mode never asked for one -- so Community output
   carried no marker while Pro fusion output carried the leaky one.
3. Idempotency, prologue safety, and separation from the trace marker.
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.constants import BUILD_MARKER_PREFIX, TRACE_MARKER_PREFIX
from pyobfus.core.build_marker import (
    apply_marker,
    build_marker_block,
    has_marker,
    insert_after_prologue,
    marker_enabled,
    marker_state,
    safe_source_label,
)

SAMPLE = "def greet(name):\n    value = 42\n    return f'{name}{value}'\n"


# ---------------------------------------------------------------------------
# Privacy: no absolute path, ever
# ---------------------------------------------------------------------------


def test_source_label_is_relative_to_the_project_root(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    source = root / "pkg" / "mod.py"
    source.parent.mkdir(parents=True)
    source.write_text("x = 1\n", encoding="utf-8")

    assert safe_source_label(source, root) == "pkg/mod.py"


def test_source_label_falls_back_to_basename_outside_the_root(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    outside = tmp_path / "elsewhere" / "secret_client.py"
    outside.parent.mkdir(parents=True)
    outside.write_text("x = 1\n", encoding="utf-8")

    label = safe_source_label(outside, root)
    assert label == "secret_client.py"
    assert str(tmp_path) not in str(label)


def test_source_label_of_a_single_file_build_is_a_bare_basename(tmp_path: Path) -> None:
    source = tmp_path / "billing.py"
    source.write_text("x = 1\n", encoding="utf-8")

    # A single-file build passes the input file itself; it resolves to its parent.
    assert safe_source_label(source, source) == "billing.py"
    assert safe_source_label(source, source.parent) == "billing.py"


def test_source_label_never_returns_an_absolute_path(tmp_path: Path) -> None:
    source = tmp_path / "deep" / "nested" / "mod.py"
    source.parent.mkdir(parents=True)
    source.write_text("x = 1\n", encoding="utf-8")

    for root in (None, tmp_path, source, source.parent, Path("/nonexistent-root")):
        label = safe_source_label(source, root)
        assert label is not None
        assert not Path(label).is_absolute()
        assert not label.startswith("/")
        assert ":" not in label  # no Windows drive letter


@pytest.mark.parametrize("mode", ["single", "directory"])
def test_generated_output_contains_no_absolute_build_path(tmp_path: Path, mode: str) -> None:
    """The regression that motivated this feature: an absolute path in output."""
    runner = CliRunner()
    if mode == "single":
        source = tmp_path / "app.py"
        source.write_text(SAMPLE, encoding="utf-8")
        out = tmp_path / "out.py"
        result = runner.invoke(main, [str(source), "-o", str(out)])
        produced = [out]
    else:
        src_dir = tmp_path / "src"
        (src_dir / "pkg").mkdir(parents=True)
        (src_dir / "pkg" / "mod.py").write_text(SAMPLE, encoding="utf-8")
        out_dir = tmp_path / "out"
        result = runner.invoke(main, [str(src_dir), "-o", str(out_dir)])
        produced = list(out_dir.rglob("*.py"))

    assert result.exit_code == 0, result.output
    assert produced, "no output was written"
    for path in produced:
        text = path.read_text(encoding="utf-8")
        assert BUILD_MARKER_PREFIX in text
        assert str(tmp_path) not in text
        assert str(tmp_path.resolve()) not in text


# ---------------------------------------------------------------------------
# The marker is actually emitted
# ---------------------------------------------------------------------------


def test_single_file_output_carries_the_marker(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "out.py"

    result = CliRunner().invoke(main, [str(source), "-o", str(out)])

    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert text.startswith(f"{BUILD_MARKER_PREFIX} format=1 edition=community")
    assert "# Source: app.py" in text


def test_directory_output_carries_a_project_relative_marker(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    (src_dir / "pkg").mkdir(parents=True)
    (src_dir / "pkg" / "mod.py").write_text(SAMPLE, encoding="utf-8")
    out_dir = tmp_path / "out"

    result = CliRunner().invoke(main, [str(src_dir), "-o", str(out_dir)])

    assert result.exit_code == 0, result.output
    text = (out_dir / "pkg" / "mod.py").read_text(encoding="utf-8")
    assert BUILD_MARKER_PREFIX in text
    assert "# Source: pkg/mod.py" in text


def test_marker_can_be_suppressed_from_the_cli(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "out.py"

    result = CliRunner().invoke(main, [str(source), "-o", str(out), "--no-community-marker"])

    assert result.exit_code == 0, result.output
    assert BUILD_MARKER_PREFIX not in out.read_text(encoding="utf-8")


def test_marker_can_be_suppressed_from_a_config_file(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "out.py"
    config = tmp_path / "pyobfus.yaml"
    config.write_text("obfuscation:\n  community_marker: 'off'\n", encoding="utf-8")

    result = CliRunner().invoke(main, [str(source), "-o", str(out), "-c", str(config)])

    assert result.exit_code == 0, result.output
    assert BUILD_MARKER_PREFIX not in out.read_text(encoding="utf-8")


def test_suppressing_the_marker_does_not_change_the_obfuscated_code(tmp_path: Path) -> None:
    """Marker policy is cosmetic: it must not alter transformation semantics."""
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    with_marker = tmp_path / "with.py"
    without = tmp_path / "without.py"

    runner = CliRunner()
    assert runner.invoke(main, [str(source), "-o", str(with_marker)]).exit_code == 0
    assert (
        runner.invoke(main, [str(source), "-o", str(without), "--no-community-marker"]).exit_code
        == 0
    )

    marked = with_marker.read_text(encoding="utf-8")
    plain = without.read_text(encoding="utf-8")
    block = build_marker_block(
        tool_version=marked.split("# Tool: pyobfus ")[1].split(" ")[0],
        edition="community",
        source_label="app.py",
    )
    assert marked == block + plain


# ---------------------------------------------------------------------------
# Idempotency and prologue safety
# ---------------------------------------------------------------------------


def test_apply_marker_is_idempotent() -> None:
    once = apply_marker(SAMPLE, tool_version="1.2.3", edition="community", source_label="a.py")
    twice = apply_marker(once, tool_version="1.2.3", edition="community", source_label="a.py")

    assert once == twice
    assert twice.count(BUILD_MARKER_PREFIX) == 1


def test_rerunning_a_build_does_not_double_stamp(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "out.py"

    runner = CliRunner()
    assert runner.invoke(main, [str(source), "-o", str(out)]).exit_code == 0
    first = out.read_text(encoding="utf-8")
    assert runner.invoke(main, [str(source), "-o", str(out)]).exit_code == 0
    second = out.read_text(encoding="utf-8")

    assert first == second
    assert second.count(BUILD_MARKER_PREFIX) == 1


def test_shebang_stays_on_the_first_line() -> None:
    text = insert_after_prologue("#!/usr/bin/env python3\nx = 1\n", "# marker\n")

    assert text.splitlines()[0] == "#!/usr/bin/env python3"
    assert text.splitlines()[1] == "# marker"


def test_encoding_cookie_stays_within_the_first_two_lines() -> None:
    source = "#!/usr/bin/env python3\n# -*- coding: latin-1 -*-\nx = 1\n"

    text = apply_marker(source, tool_version="1.2.3", edition="community", source_label="a.py")

    lines = text.splitlines()
    assert lines[0] == "#!/usr/bin/env python3"
    assert "coding: latin-1" in lines[1]
    assert lines[2].startswith(BUILD_MARKER_PREFIX)


def test_encoding_cookie_without_a_shebang_stays_on_the_first_line() -> None:
    text = apply_marker(
        "# -*- coding: latin-1 -*-\nx = 1\n",
        tool_version="1.2.3",
        edition="community",
        source_label="a.py",
    )

    lines = text.splitlines()
    assert "coding: latin-1" in lines[0]
    assert lines[1].startswith(BUILD_MARKER_PREFIX)


def test_marked_output_stays_syntactically_valid() -> None:
    text = apply_marker(SAMPLE, tool_version="1.2.3", edition="community", source_label="a.py")

    compile(text, "<marked>", "exec")


def test_marker_adds_no_runtime_object() -> None:
    """The marker is a comment: it must not define anything importable."""
    text = apply_marker(SAMPLE, tool_version="1.2.3", edition="community", source_label="a.py")
    namespace: dict = {}

    exec(compile(text, "<marked>", "exec"), namespace)  # noqa: S102 - deliberate

    assert set(namespace) - {"__builtins__"} == {"greet"}


# ---------------------------------------------------------------------------
# Separation from the trace marker
# ---------------------------------------------------------------------------


def test_build_and_trace_marker_prefixes_are_distinct() -> None:
    assert BUILD_MARKER_PREFIX != TRACE_MARKER_PREFIX
    assert not BUILD_MARKER_PREFIX.startswith(TRACE_MARKER_PREFIX)
    assert not TRACE_MARKER_PREFIX.startswith(BUILD_MARKER_PREFIX)


def test_a_build_marker_alone_is_not_mistaken_for_a_trace_marker() -> None:
    text = apply_marker(SAMPLE, tool_version="1.2.3", edition="community", source_label="a.py")

    assert has_marker(text)
    assert TRACE_MARKER_PREFIX not in text


def test_both_markers_coexist_without_duplication(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "out.py"
    mapping = tmp_path / "map.json"

    result = CliRunner().invoke(
        main,
        [str(source), "-o", str(out), "--save-mapping", str(mapping), "--trace-marker"],
    )

    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert text.count(BUILD_MARKER_PREFIX) == 1
    assert text.count(TRACE_MARKER_PREFIX) == 1
    # The trace marker is stamped after the build marker, so it lands on top.
    assert text.index(TRACE_MARKER_PREFIX) < text.index(BUILD_MARKER_PREFIX)
    assert str(tmp_path) not in text


# ---------------------------------------------------------------------------
# Mode resolution and reported state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mode,expected",
    [("auto", True), ("on", True), ("off", False), ("OFF", False), (" off ", False), (None, True)],
)
def test_marker_mode_resolution(mode, expected) -> None:
    assert marker_enabled(mode) is expected


def test_an_unknown_mode_fails_open_rather_than_raising() -> None:
    """A cosmetic comment must never be able to fail a build."""
    assert marker_enabled("nonsense") is True
    assert marker_state(mode="nonsense", edition="community", emitted=True)["mode"] == "auto"


def test_marker_state_shape() -> None:
    state = marker_state(mode="auto", edition="community", emitted=True)

    assert state == {"format": 1, "edition": "community", "mode": "auto", "emitted": True}


def test_marker_mode_is_part_of_the_effective_config_hash() -> None:
    """Marker policy changes output bytes, so it must move the config hash."""
    from pyobfus.core.provenance import config_hash

    on = ObfuscationConfig(community_marker="auto")
    off = ObfuscationConfig(community_marker="off")

    assert config_hash(on) != config_hash(off)


def test_dry_run_plan_reports_marker_state(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [str(source), "-o", str(tmp_path / "out.py"), "--dry-run", "--json"],
    )

    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)["plan"]
    assert plan["output_marker"] == {
        "format": 1,
        "edition": "community",
        "mode": "auto",
        "emitted": True,
    }
    assert {"kind": "build-marker", "role": "ship", "path": "embedded-in-output"} in plan[
        "artifacts"
    ]


def test_dry_run_plan_reports_a_suppressed_marker(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            str(source),
            "-o",
            str(tmp_path / "out.py"),
            "--dry-run",
            "--json",
            "--no-community-marker",
        ],
    )

    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)["plan"]
    assert plan["output_marker"]["emitted"] is False
    assert plan["output_marker"]["mode"] == "off"
    assert all(artifact["kind"] != "build-marker" for artifact in plan["artifacts"])


def test_provenance_manifest_records_marker_state(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    manifest = tmp_path / "provenance.json"

    result = CliRunner().invoke(
        main,
        [
            str(source),
            "-o",
            str(tmp_path / "out.py"),
            "--provenance-manifest",
            str(manifest),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["output_marker"] == {
        "format": 1,
        "edition": "community",
        "mode": "auto",
        "emitted": True,
    }


def test_manifest_stays_valid_and_integrity_checked_with_the_new_field(tmp_path: Path) -> None:
    from pyobfus.core.provenance import validate_provenance_manifest, verify_manifest_integrity

    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    manifest = tmp_path / "provenance.json"

    result = CliRunner().invoke(
        main,
        [str(source), "-o", str(tmp_path / "out.py"), "--provenance-manifest", str(manifest)],
    )
    assert result.exit_code == 0, result.output

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert verify_manifest_integrity(payload) is True
    assert validate_provenance_manifest(payload)["valid"] is True


def test_a_v1_manifest_without_the_new_field_still_validates(tmp_path: Path) -> None:
    """The field is additive: manifests written before 0.5.23 must still pass.

    The old manifest is reconstructed by dropping the field *and* recomputing
    the integrity digest, which is what a genuine pre-0.5.23 file looks like.
    Merely deleting the key would fail on integrity -- correctly, since that is
    tampering, not an older format.
    """
    from pyobfus.core.provenance import (
        _integrity_digest_for,
        validate_provenance_manifest,
        verify_manifest_integrity,
    )

    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    manifest = tmp_path / "provenance.json"
    result = CliRunner().invoke(
        main,
        [str(source), "-o", str(tmp_path / "out.py"), "--provenance-manifest", str(manifest)],
    )
    assert result.exit_code == 0, result.output

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload.pop("output_marker")
    payload["integrity"] = _integrity_digest_for(
        {k: v for k, v in payload.items() if k != "integrity"}
    )

    assert verify_manifest_integrity(payload) is True
    assert validate_provenance_manifest(payload)["valid"] is True


def test_deleting_the_marker_field_from_a_manifest_breaks_integrity(tmp_path: Path) -> None:
    """The flip side: the new field is covered by the integrity digest."""
    from pyobfus.core.provenance import verify_manifest_integrity

    source = tmp_path / "app.py"
    source.write_text(SAMPLE, encoding="utf-8")
    manifest = tmp_path / "provenance.json"
    result = CliRunner().invoke(
        main,
        [str(source), "-o", str(tmp_path / "out.py"), "--provenance-manifest", str(manifest)],
    )
    assert result.exit_code == 0, result.output

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload.pop("output_marker")

    assert verify_manifest_integrity(payload) is False
