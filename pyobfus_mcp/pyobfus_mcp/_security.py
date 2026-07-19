"""
Security baseline primitives for pyobfus-mcp.

Surfaced by the 2026-05-07 self-audit against Atlas Whoff's "5 MCP Server
Security Mistakes That Could Expose Your AI Stack" (dev.to, 2026-05-06)
plus Phase 2 production hardening:

  1. **Path scoping** (`validate_path`) — resolve a user-provided path,
     reject `..`-traversal and any absolute path that escapes the
     configured project root. Default root is the server process's cwd
     at first call; override with the `PYOBFUS_MCP_PROJECT_ROOT` env var.
  2. **Rate limiting** (`check_rate_limit`) — sliding-window per-tool
     cap. Default 30 calls/min/tool; override with the
     `PYOBFUS_MCP_RATE_LIMIT_PER_MIN` env var (set to 0 to disable).
  3. **Audit logging** (`audit_log`) — JSON-line per tool invocation,
     stderr by default; override destination with the
     `PYOBFUS_MCP_AUDIT_LOG=path/to/file.jsonl` env var. Sensitive
     parameter values are redacted by name.
  4. **Administrative tool gating** (Phase 2) — comma-separated tool
     names listed in `PYOBFUS_MCP_DISABLED_TOOLS` are rejected with a
     structured `ToolDisabled` error envelope and audit-logged with
     `outcome: "disabled"`. Useful for restricting an exposed server
     to a subset of tools without redeploying.
  5. **OpenTelemetry instrumentation** (Phase 2) — soft-imported.
     When `opentelemetry` is installed (e.g. via the `pyobfus-mcp[otel]`
     extras) and a `TracerProvider` is configured (typically the user
     sets `OTEL_EXPORTER_OTLP_ENDPOINT` and runs an SDK initializer at
     app startup), every tool invocation emits a span with attributes
     (`tool.name`, `tool.status`, `tool.duration_ms`). Without OTel the
     span context yields a no-op object — zero runtime cost.

The `secure_tool` decorator wires all of (2)+(3)+(4)+(5) around any
tool-implementation function. Path validation (1) is left to the tool
body so each tool can provide its own per-parameter error message.

This module is deliberately MCP-SDK-agnostic — it has no dependency on
the `mcp` package and is independently unit-testable.
"""

from __future__ import annotations

import contextlib
import inspect
import json
import os
import sys
import time
from collections import defaultdict
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, FrozenSet, Iterable, Iterator, List

# ---------------------------------------------------------------------------
# OpenTelemetry soft-import (Phase 2)
# ---------------------------------------------------------------------------

# OTel is intentionally a soft dependency: when `opentelemetry` is installed
# the secure_tool decorator emits a span per tool invocation; when it isn't,
# the same code path runs against a no-op span and there's zero overhead.
# Install via `pip install pyobfus-mcp[otel]` to opt in (also requires
# OTEL_EXPORTER_OTLP_ENDPOINT and a configured TracerProvider for spans
# to actually go anywhere).
try:
    from opentelemetry import trace as _otel_trace  # type: ignore[import-not-found]

    _OTEL_AVAILABLE = True
    _otel_tracer = _otel_trace.get_tracer("pyobfus_mcp")
except ImportError:  # pragma: no cover — exercised only on hosts without otel
    _OTEL_AVAILABLE = False
    _otel_tracer = None


class _NoOpSpan:
    """Stub span exposing the subset of the OTel span API we use.

    When `opentelemetry` isn't installed the `_otel_span` context manager
    yields one of these so `secure_tool` doesn't need any branching when
    setting attributes.
    """

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def record_exception(self, exc: BaseException) -> None:
        pass


_NOOP_SPAN = _NoOpSpan()


@contextlib.contextmanager
def _otel_span(tool_name: str) -> Iterator[Any]:
    """Yield an OTel span (or no-op stub) for the duration of a tool call."""
    if _OTEL_AVAILABLE:
        # The cast to `_otel_tracer` is safe inside this branch because
        # _OTEL_AVAILABLE only flips True after the import succeeded.
        assert _otel_tracer is not None
        with _otel_tracer.start_as_current_span(f"pyobfus_mcp.{tool_name}") as span:
            span.set_attribute("tool.name", tool_name)
            yield span
    else:
        yield _NOOP_SPAN


# ---------------------------------------------------------------------------
# 1. Path scoping
# ---------------------------------------------------------------------------


class PathScopeError(ValueError):
    """Raised when a path argument escapes the configured project-root sandbox."""


def get_project_root() -> Path:
    """Return the path-scoping root.

    Resolution order:
      1. `PYOBFUS_MCP_PROJECT_ROOT` env var (explicit user config; supports `~`).
      2. cwd of the server process at the time of the call.

    The returned path is always resolved (symlinks followed, normalized).
    """
    raw = os.environ.get("PYOBFUS_MCP_PROJECT_ROOT")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(os.getcwd()).resolve()


def validate_path(p: str, *, must_exist: bool = False) -> Path:
    """Resolve a user-supplied path and assert it stays within the project root.

    Rejects any path whose resolved form is not contained by
    `get_project_root()`. This catches both `..`-traversal and absolute
    paths that point elsewhere on the filesystem.

    Args:
        p: The path string supplied by the calling agent.
        must_exist: If True, also raise `FileNotFoundError` when the
            resolved path does not exist on disk.

    Returns:
        The fully-resolved `Path` (safe to pass to file operations).

    Raises:
        PathScopeError: when the resolved path escapes the project root.
        FileNotFoundError: when `must_exist=True` and the path does not exist.
    """
    root = get_project_root()
    candidate = Path(p).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PathScopeError(
            f"Path '{p}' resolves to {resolved}, which is outside the configured "
            f"project root {root}. Set PYOBFUS_MCP_PROJECT_ROOT to widen the scope, "
            f"or use a path that stays within the root."
        ) from exc

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {p}")

    return resolved


# ---------------------------------------------------------------------------
# 2. Rate limiting
# ---------------------------------------------------------------------------


_call_history: Dict[str, List[float]] = defaultdict(list)
_call_history_lock = Lock()


class RateLimitExceeded(RuntimeError):
    """Raised when a per-tool rate limit is hit."""

    def __init__(self, tool_name: str, retry_after_seconds: float) -> None:
        self.tool_name = tool_name
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Rate limit exceeded for tool {tool_name!r}. " f"Retry in {retry_after_seconds:.1f}s."
        )


def _rate_limit_cap() -> int:
    """Return the per-minute cap from `PYOBFUS_MCP_RATE_LIMIT_PER_MIN` (default 30).

    A value of 0 (or any non-positive integer) disables rate limiting entirely.
    """
    raw = os.environ.get("PYOBFUS_MCP_RATE_LIMIT_PER_MIN", "30")
    try:
        return int(raw)
    except ValueError:
        return 30


def check_rate_limit(tool_name: str, *, window_seconds: int = 60) -> None:
    """Enforce a sliding-window per-tool rate limit.

    Mutates the in-process call-history dict. Thread-safe.

    Raises:
        RateLimitExceeded: when more than `_rate_limit_cap()` calls
            happened in the last `window_seconds` for `tool_name`.
    """
    cap = _rate_limit_cap()
    if cap <= 0:
        return  # disabled

    now = time.time()
    cutoff = now - window_seconds
    with _call_history_lock:
        history = _call_history[tool_name]
        history[:] = [t for t in history if t > cutoff]
        if len(history) >= cap:
            oldest = history[0]
            retry_after = window_seconds - (now - oldest)
            raise RateLimitExceeded(tool_name, retry_after)
        history.append(now)


def reset_rate_limit_state() -> None:
    """Clear all rate-limit history. Test-only utility."""
    with _call_history_lock:
        _call_history.clear()


# ---------------------------------------------------------------------------
# 3. Audit logging
# ---------------------------------------------------------------------------


def _redact_value(value: Any) -> str:
    """Replace a parameter value with a length-and-type marker.

    Keeps observability ("the param was an 80-char string") without leaking
    content (e.g. the contents of a stack trace that may include user data).
    """
    if value is None:
        return "[REDACTED:None]"
    s = str(value)
    return f"[REDACTED:{len(s)}_chars]"


def audit_log(
    tool_name: str,
    params: Dict[str, Any],
    outcome: str,
    duration_ms: float,
    *,
    redact_keys: Iterable[str] = (),
) -> None:
    """Emit a single JSON-line audit record.

    Args:
        tool_name: Name of the MCP tool being invoked.
        params: Mapping of parameter name → value. Values are JSON-serialized.
        outcome: 'success', 'warnings', 'error', 'rate_limited',
            'exception:<ExceptionClass>', etc.
        duration_ms: Tool execution duration in milliseconds.
        redact_keys: Parameter names whose values should be redacted (e.g.,
            'trace' carrying potentially-sensitive log content).
    """
    redact_set = frozenset(redact_keys)
    redacted = {k: _redact_value(v) if k in redact_set else v for k, v in params.items()}
    record = {
        "ts": round(time.time(), 3),
        "tool": tool_name,
        "params": redacted,
        "outcome": outcome,
        "duration_ms": round(duration_ms, 2),
    }
    line = json.dumps(record, default=str, ensure_ascii=False)

    log_path = os.environ.get("PYOBFUS_MCP_AUDIT_LOG")
    if log_path:
        # File output. Append-mode open per-call keeps the implementation
        # trivial; tool invocations are typically low-frequency (handful per
        # session), and OSError fallback to stderr means we never silently
        # drop an audit line if the file path is unwritable.
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            return
        except OSError:
            pass  # fall through to stderr
    print(line, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Administrative tool gating (Phase 2)
# ---------------------------------------------------------------------------


def _disabled_tools() -> FrozenSet[str]:
    """Return the set of tool names administratively disabled via env var.

    `PYOBFUS_MCP_DISABLED_TOOLS` is a comma-separated list of tool names
    (function names of the underlying `tools.*` callables); whitespace
    around individual entries is tolerated. Empty / unset env var = no
    tools disabled. The list is re-read on every check so operators can
    flip the env var on a running server with `kill -HUP` or equivalent
    (no in-process caching).
    """
    raw = os.environ.get("PYOBFUS_MCP_DISABLED_TOOLS", "")
    return frozenset(name.strip() for name in raw.split(",") if name.strip())


# ---------------------------------------------------------------------------
# Combined decorator
# ---------------------------------------------------------------------------


def _bind_params(func: Callable[..., Any], args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Best-effort capture of (positional + keyword) call args as a name→value dict.

    Falls back to a flat representation if the call signature can't be bound
    (e.g. *args / **kwargs with extras), so audit logs are never silently empty.
    """
    try:
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        return dict(bound.arguments)
    except TypeError:
        return {"_args": list(args), "_kwargs": dict(kwargs)}


def secure_tool(
    *,
    redact_params: Iterable[str] = (),
) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:
    """Decorate an MCP tool implementation with the full security baseline.

    Wraps each call through four checks, in order:
      1. **Disabled** (cheapest gate, before everything else): if the tool
         name is listed in `PYOBFUS_MCP_DISABLED_TOOLS`, return a structured
         `ToolDisabled` error envelope without consuming rate-limit budget
         or hitting OTel.
      2. **OTel span** (no-op when `opentelemetry` isn't installed): the
         remainder of the call runs inside `_otel_span(tool_name)`. Span
         attributes are set on every terminal exit (rate-limit, exception,
         success).
      3. **Rate limit**: token-bucket check. On overflow, return a
         structured `RateLimitExceeded` error envelope and audit-log
         `outcome: "rate_limited"`.
      4. **Function call** with timing. On exception: audit-log
         `outcome: "exception:<ClassName>"`, record on the span, re-raise.
         On success: audit-log with the function's own `status` field as
         the outcome string.

    Path-scoping is intentionally *not* applied by this decorator — tools
    that accept path arguments call `validate_path()` explicitly inside
    their body so they can map `PathScopeError` to a tool-specific
    structured error envelope.

    Args:
        redact_params: Parameter names whose values should be redacted in
            audit logs (e.g. `'trace'` for `unmap_stack_trace`).

    Returns:
        A decorator that wraps a `(...) -> Dict[str, Any]` function.
    """
    redact_keys: FrozenSet[str] = frozenset(redact_params)

    def decorator(func: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        tool_name = func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            t_start = time.perf_counter()
            params = _bind_params(func, args, kwargs)

            # Step 1 (cheapest gate): administratively disabled?
            if tool_name in _disabled_tools():
                duration_ms = (time.perf_counter() - t_start) * 1000
                audit_log(
                    tool_name,
                    params,
                    "disabled",
                    duration_ms,
                    redact_keys=redact_keys,
                )
                return {
                    "status": "error",
                    "error_type": "ToolDisabled",
                    "message": (
                        f"Tool {tool_name!r} is administratively disabled "
                        f"via PYOBFUS_MCP_DISABLED_TOOLS."
                    ),
                    "ai_hint": (
                        f"Remove {tool_name!r} from PYOBFUS_MCP_DISABLED_TOOLS, "
                        f"or call a different tool."
                    ),
                }

            # Step 2: optional OTel span wraps everything from here.
            with _otel_span(tool_name) as span:
                # Step 3: rate limit.
                try:
                    check_rate_limit(tool_name)
                except RateLimitExceeded as exc:
                    duration_ms = (time.perf_counter() - t_start) * 1000
                    audit_log(
                        tool_name,
                        params,
                        "rate_limited",
                        duration_ms,
                        redact_keys=redact_keys,
                    )
                    span.set_attribute("tool.status", "rate_limited")
                    span.set_attribute("tool.duration_ms", round(duration_ms, 2))
                    return {
                        "status": "error",
                        "error_type": "RateLimitExceeded",
                        "message": str(exc),
                        "ai_hint": (
                            f"Wait {exc.retry_after_seconds:.0f}s before retrying. "
                            f"To raise the cap set PYOBFUS_MCP_RATE_LIMIT_PER_MIN=N "
                            f"(0 disables)."
                        ),
                        "retry_after_seconds": round(exc.retry_after_seconds, 2),
                    }

                # Step 4: invoke the wrapped function.
                try:
                    result = func(*args, **kwargs)
                except Exception as exc:
                    duration_ms = (time.perf_counter() - t_start) * 1000
                    audit_log(
                        tool_name,
                        params,
                        f"exception:{type(exc).__name__}",
                        duration_ms,
                        redact_keys=redact_keys,
                    )
                    span.set_attribute("tool.status", "exception")
                    span.set_attribute("tool.duration_ms", round(duration_ms, 2))
                    span.record_exception(exc)
                    raise

                # Success path.
                duration_ms = (time.perf_counter() - t_start) * 1000
                outcome = (
                    str(result.get("status", "unknown")) if isinstance(result, dict) else "unknown"
                )
                audit_log(
                    tool_name,
                    params,
                    outcome,
                    duration_ms,
                    redact_keys=redact_keys,
                )
                span.set_attribute("tool.status", outcome)
                span.set_attribute("tool.duration_ms", round(duration_ms, 2))
                return result

        return wrapper

    return decorator
