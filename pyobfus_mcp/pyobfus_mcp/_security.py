"""
Security baseline primitives for pyobfus-mcp.

Three categories, all surfaced by the 2026-05-07 self-audit against Atlas
Whoff's "5 MCP Server Security Mistakes That Could Expose Your AI Stack"
(dev.to, 2026-05-06):

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

The `secure_tool` decorator combines rate-limit + audit-log around any
tool-implementation function. Path validation is left to the tool body
so each tool can provide its own per-parameter error message.

This module is deliberately MCP-SDK-agnostic — it has no dependency on
the `mcp` package and is independently unit-testable.
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import time
from collections import defaultdict
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, FrozenSet, Iterable, List


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
            f"Rate limit exceeded for tool {tool_name!r}. "
            f"Retry in {retry_after_seconds:.1f}s."
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
    redacted = {
        k: _redact_value(v) if k in redact_set else v
        for k, v in params.items()
    }
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
# Combined decorator
# ---------------------------------------------------------------------------


def _bind_params(
    func: Callable[..., Any], args: tuple, kwargs: dict
) -> Dict[str, Any]:
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
    """Decorate an MCP tool implementation with rate-limiting + audit-logging.

    Path-scoping is intentionally *not* applied by this decorator. Tools that
    accept path arguments call `validate_path()` explicitly inside their body
    so they can map `PathScopeError` to a tool-specific structured error.

    Wrapped behavior:
      - Pre-call: increment & check the per-tool token bucket. On overflow,
        return a structured `RateLimitExceeded` error matching the standard
        error envelope (`status` / `error_type` / `message` / `ai_hint` /
        `retry_after_seconds`). Audit-log the rate-limit event.
      - Call: invoke the wrapped function. Time it.
      - Post-call (success): audit-log with the function's `status` field.
      - Post-call (exception): audit-log with `exception:<class>` and re-raise.

    Args:
        redact_params: Parameter names whose values should be redacted in
            audit logs (e.g. `'trace'` for `unmap_stack_trace`).

    Returns:
        A decorator that wraps a `(...) -> Dict[str, Any]` function.
    """
    redact_keys: FrozenSet[str] = frozenset(redact_params)

    def decorator(
        func: Callable[..., Dict[str, Any]]
    ) -> Callable[..., Dict[str, Any]]:
        tool_name = func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            t_start = time.perf_counter()
            params = _bind_params(func, args, kwargs)

            # Step 1: rate limit check.
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

            # Step 2: invoke the wrapped function. On exception, log + re-raise.
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
                raise

            # Step 3: log success with the tool's own status field as outcome.
            duration_ms = (time.perf_counter() - t_start) * 1000
            outcome = (
                str(result.get("status", "unknown"))
                if isinstance(result, dict)
                else "unknown"
            )
            audit_log(tool_name, params, outcome, duration_ms, redact_keys=redact_keys)
            return result

        return wrapper

    return decorator
