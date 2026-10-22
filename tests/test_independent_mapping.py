"""Adversarial reader cases for file-scoped mapping; no artifact source is read."""

from __future__ import annotations

import json
import traceback
import unicodedata

import pytest

from pyobfus.core.mapping import ObfuscationMapping


def mapping(files=None, *, lines=True):
    result = ObfuscationMapping(mode="independent_files")
    for path, original in (
        files or {"alpha.py": "calculate_invoice", "beta.py": "validate_receipt"}
    ).items():
        result.add_independent_file(
            path,
            {original: "I0"},
            {
                "source": path,
                "module": path,
                "line_count": 10,
                "lines": [[1, 20]] if lines else None,
            },
            f"def {original}(): pass\n",
            "def I0(): pass\n",
        )
    return result


def frame(path, name="I0", line=3, prefix="  "):
    return f'{prefix}File "{path}", line {line}, in {name}\n'


def test_roundtrip_does_not_backfill_collisions(tmp_path):
    original = mapping()
    path = tmp_path / "mapping.json"
    original.save(path)
    raw = json.loads(path.read_text())
    assert raw["version"] == 2
    # Spurious legacy maps cannot turn collisions into a whole-text guess.
    raw.update(modules={"fake": {"WRONG": "I0"}}, locals={"fake": {"I0": "WRONG"}}, global_={})
    raw["global"] = {"I0": {"module": "fake", "original": "WRONG"}}
    path.write_text(json.dumps(raw))
    loaded = ObfuscationMapping.load(path)
    assert loaded.global_map == {}
    assert loaded.locals == {}
    assert loaded.reverse("I0") is None
    assert loaded.unmap_text("I0 I1") == "I0 I1"
    assert loaded.marker_id() == original.marker_id()
    assert loaded.stats() == {"modules": 2, "original_names": 2, "unique_obfuscated": 1}
    assert loaded.unmatched_names("I0 I10") == ["I10"]
    restored = loaded.unmap_trace(frame("/deploy/alpha.py") + frame("/deploy/beta.py"))
    assert "in calculate_invoice" in restored["unmapped_trace"]
    assert "in validate_receipt" in restored["unmapped_trace"]


@pytest.mark.parametrize("root", ["", "/deployment/", "C:\\deploy\\"])
def test_relative_absolute_windows_paths(root):
    m = mapping({"pkg/alpha.py": "calculate_invoice"})
    path = root + ("pkg\\alpha.py" if "\\" in root else "pkg/alpha.py")
    result = m.unmap_trace(frame(path))
    assert 'File "pkg/alpha.py", line 20, in calculate_invoice' in result["unmapped_trace"]
    assert result["frames"][0]["original_line"] == 20
    assert m.unmap_trace(frame("alpha.py"))["unmapped_trace"] == frame("alpha.py")


def test_nested_suffix_ambiguity_is_not_longest_match():
    m = mapping({"cli.py": "top_level", "pkg/cli.py": "nested", "main.py": "entry"})
    ambiguous = frame("/srv/pkg/cli.py")
    assert m.unmap_trace(ambiguous)["unmapped_trace"] == ambiguous
    assert m.resolve_location("/srv/pkg/cli.py", 3) is None
    # A distinct frame disambiguates the root jointly, not by majority voting.
    result = m.unmap_trace(frame("/srv/pkg/main.py", name="<module>") + ambiguous)
    assert "in top_level" in result["unmapped_trace"]
    assert "in nested" not in result["unmapped_trace"]


def test_competing_roots_cannot_win_by_recursion():
    m = mapping({"alpha.py": "calculate_invoice"})
    trace = frame("/app/alpha.py") + frame("/vendor/alpha.py") * 6
    result = m.unmap_trace(trace)
    assert result["unmapped_trace"] == trace
    assert all(f["status"] == "unmapped" for f in result["frames"])
    assert "ambiguous or inconsistent" in result["ai_hint"]


def test_external_names_excerpts_and_unframed_messages_stay_unchanged():
    m = mapping()
    trace = (
        frame("/app/alpha.py")
        + "    return I0()\n         ^^^^\n"
        + frame("/vendor/unknown.py")
        + "    raise ValueError('I0')\nValueError: I0\n"
        + "During handling of the above exception, another exception occurred:\n\n"
        + frame("/app/beta.py")
        + "    I0(\n        I0\n    )\nRuntimeError: I0\n"
    )
    result = m.unmap_trace(trace)
    assert "in calculate_invoice" in result["unmapped_trace"]
    assert "in validate_receipt" in result["unmapped_trace"]
    assert frame("/vendor/unknown.py") in result["unmapped_trace"]
    assert "ValueError: I0" in result["unmapped_trace"]
    assert "    I0(\n        I0\n    )" in result["unmapped_trace"]


@pytest.mark.skipif(__import__("sys").version_info < (3, 11), reason="ExceptionGroup requires 3.11")
def test_actual_nested_exception_group_preserves_layout():
    failures = []
    for path in ("alpha.py", "beta.py"):
        try:
            exec(
                compile("def I0():\n    raise ValueError('I0')\nI0()\n", "/app/" + path, "exec"), {}
            )
        except ValueError as exc:
            failures.append(exc)
    group_type = getattr(__import__("builtins"), "ExceptionGroup")
    group = group_type("I0", [failures[0], group_type("I0", [failures[1]])])
    trace = "".join(traceback.format_exception(group))
    result = mapping().unmap_trace(trace)
    assert "in calculate_invoice" in result["unmapped_trace"]
    assert "in validate_receipt" in result["unmapped_trace"]
    assert "ValueError: I0" in result["unmapped_trace"]
    # Branch dividers and tree prefixes are not flattened.
    assert [line for line in trace.splitlines() if "+-" in line] == [
        line for line in result["unmapped_trace"].splitlines() if "+-" in line
    ]


@pytest.mark.parametrize("lines", [True, False])
def test_marker_mismatch_never_restores_names_or_lines(lines):
    m = mapping(lines=lines)
    trace = "# pyobfus:obfuscated id=00000000\n" + frame("/app/alpha.py")
    result = m.unmap_trace(trace)
    assert result["unmapped_trace"] == trace
    assert result["frames"][0]["status"] == "unmapped"
    assert "marker mismatch" in result["ai_hint"]
    matching = trace.replace("00000000", m.marker_id())
    assert "in calculate_invoice" in m.unmap_trace(matching)["unmapped_trace"]
    mixed = matching + "# pyobfus:obfuscated id=00000000\n"
    assert m.unmap_trace(mixed)["unmapped_trace"] == mixed


def test_marker_covers_source_whitespace_without_depending_on_line_shift():
    first = mapping()
    second = mapping()
    record = dict(second.files["alpha.py"])
    second.add_independent_file(
        "alpha.py",
        {"calculate_invoice": "I0"},
        record,
        "\n\ndef calculate_invoice(): pass\n",
        "def I0(): pass\n",
    )
    assert first.marker_id() != second.marker_id()
    stable = first.marker_id()
    first.files["alpha.py"]["lines"] = [[1, None], [5, 20]]
    first.files["alpha.py"]["line_count"] += 4
    assert first.marker_id() == stable


def test_name_only_and_out_of_range_are_distinct():
    m = mapping(lines=False)
    result = m.unmap_trace(frame("/app/alpha.py"))
    assert "in calculate_invoice" in result["unmapped_trace"]
    assert result["line_map"] == "absent"
    out_of_range = frame("/app/alpha.py", line=100)
    assert m.unmap_trace(out_of_range)["unmapped_trace"] == out_of_range


def test_ambiguous_spelling_and_plain_logs_are_not_guessed():
    m = mapping()
    m.file_names["alpha.py"]["I0"] = ["first", "second"]
    trace = frame("/app/alpha.py")
    assert "in I0" in m.unmap_trace(trace)["unmapped_trace"]
    assert "No recognized traceback frames" in m.unmap_trace("I0 failed")["ai_hint"]
    assert "unverified" in m.unmap_trace(trace)["ai_hint"]
    with pytest.raises(ValueError, match="cannot be merged"):
        ObfuscationMapping.merge([m])


def test_malformed_optional_names_and_line_runs_do_not_guess(tmp_path):
    m = mapping()
    raw = json.loads(m.to_json())
    raw["file_names"]["alpha.py"] = {
        "I0": ["calculate_invoice", "calculate_invoice"],
        "I1": [1],
        "bad key": ["bad"],
        "I2": [],
    }
    raw["file_names"]["orphan.py"] = {"I0": ["WRONG"]}
    raw["file_names"]["../unsafe.py"] = {"I0": ["WRONG"]}
    raw["files"]["entries"]["alpha.py"]["lines"] = [[3, -4]]
    path = tmp_path / "mapping.json"
    path.write_text(json.dumps(raw))
    loaded = ObfuscationMapping.load(path)
    assert loaded.file_names["alpha.py"] == {"I0": ["calculate_invoice"]}
    assert "orphan.py" not in loaded.file_names
    assert "../unsafe.py" not in loaded.file_names
    result = loaded.unmap_trace(frame("/app/alpha.py"))
    assert "in calculate_invoice" in result["unmapped_trace"]
    assert result["frames"][0]["status"] == "unmapped"


@pytest.mark.parametrize("files", [None, {}, {"line_map_version": 99, "entries": {}}])
def test_v2_requires_file_identity(tmp_path, files):
    raw = json.loads(mapping().to_json())
    raw["files"] = files
    path = tmp_path / "mapping.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="requires files.entries"):
        ObfuscationMapping.load(path)


def test_v1_still_writes_and_loads_original_format(tmp_path):
    m = ObfuscationMapping.from_single_file({"calculate_invoice": "I0"})
    path = tmp_path / "mapping.json"
    m.save(path)
    assert json.loads(path.read_text())["version"] == 1
    assert ObfuscationMapping.load(path).unmap_text("I0") == "calculate_invoice"


@pytest.mark.parametrize("prefix", ["λ", "a\u0301"])
def test_unicode_prefix_and_combining_characters(prefix):
    m = mapping({"alpha.py": "calculate_invoice"})
    name = prefix + "0"
    m.file_names["alpha.py"] = {unicodedata.normalize("NFKC", name): ["calculate_invoice"]}
    trace = frame("/app/alpha.py", name=name)
    assert "in calculate_invoice" in m.unmap_trace(trace)["unmapped_trace"]
    assert m.unmap_file_text(name + "more", "alpha.py") == name + "more"


def test_path_only_app_frame_vetoes_foreign_named_frame():
    m = mapping({"main.py": "entry", "helpers.py": "calculate_invoice"})
    trace = frame("/app/main.py", name="<module>") + frame("/app/vendor/helpers.py")
    assert m.unmap_trace(trace)["unmapped_trace"] == trace


def test_single_external_path_only_frame_is_not_restored():
    m = mapping({"__init__.py": "calculate_invoice"})
    trace = frame("/usr/lib/python3.12/json/__init__.py", name="loads")
    assert m.unmap_trace(trace)["unmapped_trace"] == trace


def test_failed_nested_path_is_negative_identity_evidence():
    m = mapping({"util.py": "calculate_invoice", "main.py": "entry"})
    m.unmapped_files["pkg/util.py"] = "File transformation failed"
    stale = frame("/app/pkg/util.py")
    assert m.unmap_trace(stale)["unmapped_trace"] == stale
    result = m.unmap_trace(frame("/app/main.py") + stale)
    assert "in entry" in result["unmapped_trace"]
    assert stale in result["unmapped_trace"]
    assert result["frames"][-1]["resolved_file"] is None


def test_already_restored_trace_and_control_separators_do_not_remap_or_crash():
    m = mapping()
    restored = m.unmap_trace(frame("/app/alpha.py"))["unmapped_trace"]
    assert m.unmap_trace(restored)["unmapped_trace"] == restored
    malformed = '  File "/app/alpha.py", line 3, in \x0c\n'
    assert m.unmap_trace(malformed)["unmapped_trace"] == malformed


def test_name_only_restoration_cannot_cascade_into_another_original_name():
    m = mapping({"app.py": "I1"}, lines=False)
    m.file_names["app.py"] = {"I0": ["I1"], "I1": ["other"]}
    restored = m.unmap_trace(frame("/app/app.py"))["unmapped_trace"]
    assert "in I1  [names restored by pyobfus]" in restored
    assert m.unmap_trace(restored)["unmapped_trace"] == restored
