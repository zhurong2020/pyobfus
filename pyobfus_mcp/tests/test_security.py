"""Tests for the security baseline primitives in pyobfus_mcp._security.

Three concerns:
- `validate_path` — project-root sandbox + traversal rejection
- `check_rate_limit` — sliding-window per-tool cap with env-var override
- `audit_log` — JSON-line emission with redaction; stderr default + file override

The conftest.py autouse fixture sets `PYOBFUS_MCP_PROJECT_ROOT` to
`tempfile.gettempdir()` for the whole suite, so `tmp_path` paths are
always in-scope unless a test explicitly tightens the root.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyobfus_mcp._security import (
    PathScopeError,
    RateLimitExceeded,
    audit_log,
    check_rate_limit,
    secure_tool,
    validate_path,
)


# ---------------------------------------------------------------------------
# validate_path
# ---------------------------------------------------------------------------


def test_validate_path_inside_scope_returns_resolved(tmp_path: Path) -> None:
    p = tmp_path / "inner"
    p.mkdir()
    target = p / "file.txt"
    target.write_text("hi", encoding="utf-8")

    result = validate_path(str(target), must_exist=True)
    assert result == target.resolve()


def test_validate_path_absolute_outside_scope_rejected() -> None:
    # /etc/passwd is outside any reasonable temp-dir scope on Unix; on Windows
    # the equivalent escape is C:\Windows\System32\drivers\etc\hosts. We use
    # the Unix path here because the test suite runs on Ubuntu in CI; the
    # validation logic is platform-agnostic.
    with pytest.raises(PathScopeError) as exc_info:
        validate_path("/etc/passwd")
    assert "outside the configured project root" in str(exc_info.value)


def test_validate_path_traversal_via_dotdot_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    inner = tmp_path / "inner"
    inner.mkdir()
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(inner))

    # Relative path that resolves above the root.
    with pytest.raises(PathScopeError):
        validate_path("../escape.txt")


def test_validate_path_must_exist_raises_filenotfound(tmp_path: Path) -> None:
    nonexistent = tmp_path / "definitely_not_here.txt"
    with pytest.raises(FileNotFoundError):
        validate_path(str(nonexistent), must_exist=True)


def test_validate_path_must_exist_false_returns_resolved_anyway(
    tmp_path: Path,
) -> None:
    nonexistent = tmp_path / "future.txt"
    result = validate_path(str(nonexistent))  # must_exist defaults False
    assert result == nonexistent.resolve()


def test_validate_path_relative_anchored_to_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(tmp_path))
    (tmp_path / "x.py").write_text("ok", encoding="utf-8")

    result = validate_path("x.py", must_exist=True)
    assert result == (tmp_path / "x.py").resolve()


# ---------------------------------------------------------------------------
# check_rate_limit
# ---------------------------------------------------------------------------


def test_check_rate_limit_under_cap_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "5")
    for _ in range(4):
        check_rate_limit("test_tool")  # should not raise


def test_check_rate_limit_at_cap_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "3")
    for _ in range(3):
        check_rate_limit("test_tool")
    with pytest.raises(RateLimitExceeded) as exc_info:
        check_rate_limit("test_tool")
    assert exc_info.value.tool_name == "test_tool"
    assert exc_info.value.retry_after_seconds > 0


def test_check_rate_limit_disabled_when_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "0")
    for _ in range(100):
        check_rate_limit("test_tool")  # never raises


def test_check_rate_limit_separate_tools_separate_buckets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "2")
    check_rate_limit("tool_a")
    check_rate_limit("tool_a")
    # tool_a is at cap; tool_b should still pass.
    check_rate_limit("tool_b")
    check_rate_limit("tool_b")
    with pytest.raises(RateLimitExceeded) as exc_info:
        check_rate_limit("tool_a")
    assert exc_info.value.tool_name == "tool_a"


def test_check_rate_limit_invalid_env_var_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "not-a-number")
    # Default is 30, so 30 calls should pass.
    for _ in range(30):
        check_rate_limit("test_tool")
    # 31st should raise.
    with pytest.raises(RateLimitExceeded):
        check_rate_limit("test_tool")


# ---------------------------------------------------------------------------
# audit_log
# ---------------------------------------------------------------------------


def test_audit_log_emits_json_to_stderr_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("PYOBFUS_MCP_AUDIT_LOG", raising=False)

    audit_log("test_tool", {"path": "/tmp/x"}, "success", 12.34)

    captured = capsys.readouterr()
    line = captured.err.strip()
    assert line, "audit_log should write to stderr by default"

    record = json.loads(line)
    assert record["tool"] == "test_tool"
    assert record["params"]["path"] == "/tmp/x"
    assert record["outcome"] == "success"
    assert record["duration_ms"] == 12.34
    assert "ts" in record


def test_audit_log_redacts_listed_params(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("PYOBFUS_MCP_AUDIT_LOG", raising=False)
    sensitive_trace = "Traceback (most recent call last):\n  password: hunter2"

    audit_log(
        "unmap_stack_trace",
        {"trace": sensitive_trace, "mapping_path": "m.json"},
        "success",
        5.0,
        redact_keys=["trace"],
    )

    record = json.loads(capsys.readouterr().err.strip())
    # Sensitive content gone, only length-marker remains.
    assert "hunter2" not in record["params"]["trace"]
    assert "REDACTED" in record["params"]["trace"]
    assert str(len(sensitive_trace)) in record["params"]["trace"]
    # Non-redacted params pass through as-is.
    assert record["params"]["mapping_path"] == "m.json"


def test_audit_log_writes_to_file_when_env_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("PYOBFUS_MCP_AUDIT_LOG", str(log_path))

    audit_log("test_tool", {"x": 1}, "success", 1.0)
    audit_log("test_tool", {"x": 2}, "success", 2.0)

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    rec0 = json.loads(lines[0])
    rec1 = json.loads(lines[1])
    assert rec0["params"]["x"] == 1
    assert rec1["params"]["x"] == 2


def test_audit_log_file_failure_falls_back_to_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Point the audit log at a path that can't be opened (parent doesn't
    # exist and isn't creatable as a directory). audit_log should swallow
    # the OSError and emit to stderr instead — we never want to silently
    # drop an audit record.
    monkeypatch.setenv(
        "PYOBFUS_MCP_AUDIT_LOG", "/nonexistent_root_xyz_12345/cant/write/here.jsonl"
    )

    audit_log("test_tool", {"x": 1}, "success", 1.0)

    err = capsys.readouterr().err.strip()
    assert err, "fallback to stderr expected when audit-log file is unwritable"
    record = json.loads(err)
    assert record["tool"] == "test_tool"


# ---------------------------------------------------------------------------
# secure_tool decorator integration
# ---------------------------------------------------------------------------


def test_secure_tool_returns_rate_limit_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "1")

    @secure_tool()
    def my_tool(x: int) -> dict:
        return {"status": "success", "result": x}

    # First call passes.
    r1 = my_tool(1)
    assert r1["status"] == "success"

    # Second call hits rate limit and returns the structured error envelope.
    r2 = my_tool(2)
    assert r2["status"] == "error"
    assert r2["error_type"] == "RateLimitExceeded"
    assert "retry_after_seconds" in r2
    assert r2["retry_after_seconds"] > 0
    assert "PYOBFUS_MCP_RATE_LIMIT_PER_MIN" in r2["ai_hint"]


def test_secure_tool_emits_audit_on_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("PYOBFUS_MCP_AUDIT_LOG", raising=False)

    @secure_tool()
    def my_tool(x: int) -> dict:
        return {"status": "success"}

    my_tool(42)

    record = json.loads(capsys.readouterr().err.strip())
    assert record["tool"] == "my_tool"
    assert record["params"]["x"] == 42
    assert record["outcome"] == "success"
    assert record["duration_ms"] >= 0


def test_secure_tool_emits_audit_on_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("PYOBFUS_MCP_AUDIT_LOG", raising=False)

    @secure_tool()
    def my_tool(x: int) -> dict:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        my_tool(1)

    record = json.loads(capsys.readouterr().err.strip())
    assert record["tool"] == "my_tool"
    assert record["outcome"] == "exception:RuntimeError"


def test_secure_tool_redacts_listed_params(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("PYOBFUS_MCP_AUDIT_LOG", raising=False)

    @secure_tool(redact_params=["secret"])
    def my_tool(x: int, secret: str) -> dict:
        return {"status": "success"}

    my_tool(1, secret="password123")

    record = json.loads(capsys.readouterr().err.strip())
    # Sensitive content gone.
    assert "password123" not in record["params"]["secret"]
    assert "REDACTED" in record["params"]["secret"]
    # Non-redacted param visible.
    assert record["params"]["x"] == 1


def test_secure_tool_emits_audit_on_rate_limited_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "1")
    monkeypatch.delenv("PYOBFUS_MCP_AUDIT_LOG", raising=False)

    @secure_tool()
    def my_tool(x: int) -> dict:
        return {"status": "success"}

    my_tool(1)
    capsys.readouterr()  # discard the success audit line
    my_tool(2)  # rate-limited

    record = json.loads(capsys.readouterr().err.strip())
    assert record["outcome"] == "rate_limited"
    assert record["params"]["x"] == 2
