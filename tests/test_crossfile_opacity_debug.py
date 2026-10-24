"""Slice D tests: encrypted-code frame identity, name-only restore, report."""

from __future__ import annotations

import secrets
import traceback

import pytest

import pyobfus_runtime
from pyobfus.core.crossfile_opacity_debug import (
    L3_UNMAP_MIN_CORE_VERSION,
    build_encrypted_code_table,
    build_opacity_report,
    interpreter_tuple,
    l3_co_filename,
    parse_l3_co_filename,
    restore_l3_names,
)
from pyobfus_pro.crossfile_opacity_adapter import encrypt_targets

ENV = "APP_L3_KEY"


# --------------------------------------------------------------------------
# co_filename identity
# --------------------------------------------------------------------------


def test_co_filename_round_trip():
    cf = l3_co_filename("abcd1234", "pkg/util.py")
    assert cf == "<pyobfus-l3:abcd1234:pkg/util.py>"
    assert parse_l3_co_filename(cf) == ("abcd1234", "pkg/util.py")


def test_co_filename_supports_windows_relative_path():
    cf = l3_co_filename("id1", "C:sub/mod.py")
    assert parse_l3_co_filename(cf) == ("id1", "C:sub/mod.py")


def test_parse_rejects_non_l3_path():
    assert parse_l3_co_filename("/real/path.py") is None
    assert parse_l3_co_filename("<string>") is None


def test_artifact_id_may_not_contain_delimiters():
    with pytest.raises(ValueError):
        l3_co_filename("bad:id", "f.py")


# --------------------------------------------------------------------------
# End-to-end: a real traceback from an encrypted function carries the frame
# --------------------------------------------------------------------------


def _build_and_run_raising(original_name, src, key=None):
    key = key or secrets.token_bytes(32)
    cf = l3_co_filename("aid123", "pkg/mod.py")
    res = encrypt_targets(src, [original_name], key=key, env_name=ENV, code_filename=cf)
    pyobfus_runtime.set_key_provider(lambda: key)
    try:
        ns: dict = {}
        exec(compile(res.source, "<emitted>", "exec"), ns)  # noqa: S102 -- our emitted source
        try:
            ns[original_name]()
        except ValueError:
            return cf, traceback.format_exc()
    finally:
        pyobfus_runtime.set_key_provider(None)
    raise AssertionError("expected the target to raise")


def test_encrypted_function_traceback_carries_dedicated_frame_and_restores_name():
    src = 'def boom():\n    raise ValueError("x")\n'
    cf, trace = _build_and_run_raising("boom", src)
    assert f'File "{cf}", line' in trace
    assert "in boom" in trace

    table = build_encrypted_code_table([(cf, "boom", "compute_total")])
    result = restore_l3_names(trace, table)
    assert "in compute_total" in result["restored_trace"]
    assert "in boom" not in result["restored_trace"]
    named = [f for f in result["frames"] if f["status"] == "name_only"]
    assert named and named[0]["name"] == "compute_total"
    assert named[0]["original_line"] is None  # never a reconstructed line


def test_no_source_line_is_shown_for_the_encrypted_frame():
    # linecache must not resolve the <pyobfus-l3:...> pseudo-path to source.
    src = (
        "def boom():\n    secret_constant = 123456789\n    raise ValueError(str(secret_constant))\n"
    )
    cf, trace = _build_and_run_raising("boom", src)
    assert "secret_constant" not in trace  # no source excerpt leaked


# --------------------------------------------------------------------------
# Restorer: exact match, mixed traces, wrong build id
# --------------------------------------------------------------------------


def test_restore_all_l3_trace():
    cf = l3_co_filename("aid", "a.py")
    table = build_encrypted_code_table([(cf, "I0", "alpha"), (cf, "I1", "beta")])
    trace = (
        "Traceback (most recent call last):\n"
        f'  File "{cf}", line 2, in I0\n'
        f'  File "{cf}", line 5, in I1\n'
        "ValueError: boom\n"
    )
    out = restore_l3_names(trace, table)["restored_trace"]
    assert "in alpha" in out and "in beta" in out
    assert "in I0" not in out and "in I1" not in out


def test_restore_mixed_trace_leaves_plain_frames_untouched():
    cf = l3_co_filename("aid", "a.py")
    table = build_encrypted_code_table([(cf, "I0", "alpha")])
    trace = (
        '  File "/app/main.py", line 10, in run\n'
        f'  File "{cf}", line 2, in I0\n'
        "ValueError: boom\n"
    )
    out = restore_l3_names(trace, table)["restored_trace"]
    assert '  File "/app/main.py", line 10, in run\n' in out  # plain frame verbatim
    assert "in alpha" in out


def test_restore_leaves_wrong_build_id_frame_untouched():
    table = build_encrypted_code_table([(l3_co_filename("right", "a.py"), "I0", "alpha")])
    wrong = l3_co_filename("wrong", "a.py")
    trace = f'  File "{wrong}", line 2, in I0\n'
    result = restore_l3_names(trace, table)
    assert result["restored_trace"] == trace  # unchanged
    assert result["frames"][0]["status"] == "unmatched_l3"


def test_restore_leaves_unknown_name_untouched():
    cf = l3_co_filename("aid", "a.py")
    table = build_encrypted_code_table([(cf, "I0", "alpha")])
    trace = f'  File "{cf}", line 2, in I9\n'
    assert restore_l3_names(trace, table)["restored_trace"] == trace


def test_build_table_rejects_conflicting_original():
    cf = l3_co_filename("aid", "a.py")
    with pytest.raises(ValueError):
        build_encrypted_code_table([(cf, "I0", "alpha"), (cf, "I0", "beta")])


# --------------------------------------------------------------------------
# Counts-only report
# --------------------------------------------------------------------------


def test_report_is_counts_only_and_carries_no_original_names():
    report = build_opacity_report(
        artifact_id="aid123",
        env_name=ENV,
        eligible=5,
        encrypted=3,
        rejected_reasons=["async_function", "decorated_function", "async_function"],
    )
    assert report["mode"] == "crossfile_opacity"
    assert report["build_id"] == "aid123"
    assert report["eligible_targets"] == 5
    assert report["encrypted_targets"] == 3
    assert report["rejected_targets"] == 3
    assert report["rejection_histogram"] == {"async_function": 2, "decorated_function": 1}
    assert report["key_source"] == {"type": "application_provided_env", "env_name": ENV}
    assert report["unmap_min_core_version"] == L3_UNMAP_MIN_CORE_VERSION
    assert set(report["interpreter"]) == {"implementation", "python_version", "gil_disabled"}
    # No original qualified names anywhere in the serialized report.
    import json

    assert "compute_total" not in json.dumps(report)


def test_interpreter_tuple_shape():
    t = interpreter_tuple()
    assert t["implementation"] == "cpython"
    assert isinstance(t["gil_disabled"], bool)


# --------------------------------------------------------------------------
# Regressions for the slice-D review findings
# --------------------------------------------------------------------------


def test_restore_exception_group_frame():
    # ExceptionGroup tracebacks prefix frames with '|' and extra indent.
    cf = l3_co_filename("aid", "a.py")
    table = build_encrypted_code_table([(cf, "I0", "alpha")])
    trace = f'    | File "{cf}", line 2, in I0\n'
    out = restore_l3_names(trace, table)
    assert "in alpha" in out["restored_trace"]
    assert out["restored_trace"].startswith("    | File ")  # EG prefix preserved
    assert out["frames"][0]["status"] == "name_only"


@pytest.mark.parametrize("artifact,file", [("", "a.py"), ("aid", "")])
def test_empty_components_rejected(artifact, file):
    with pytest.raises(ValueError):
        l3_co_filename(artifact, file)


@pytest.mark.parametrize("bad", ['pkg/qu"ote.py', "pkg/new\nline.py", "pkg/a>b.py"])
def test_relative_file_with_frame_breaking_chars_rejected(bad):
    with pytest.raises(ValueError):
        l3_co_filename("aid", bad)
