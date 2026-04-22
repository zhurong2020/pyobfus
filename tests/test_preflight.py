"""Tests for the pre-flight risk checker (pyobfus/core/preflight.py)."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path


from pyobfus.core.preflight import (
    CAT_ALL_EXPORT,
    CAT_DYNAMIC_ATTR,
    CAT_DYNAMIC_EXEC,
    CAT_DYNAMIC_IMPORT,
    CAT_ENTRY_POINT,
    CAT_FRAMEWORK,  # noqa: F401  (imported for category registry completeness)
    CAT_INTROSPECTION,
    CAT_NAME_STRING,
    PreflightChecker,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    format_report_text,
)


def _write(tmp_path: Path, name: str, src: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(src).lstrip(), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Core detections
# ---------------------------------------------------------------------------


def test_detects_eval(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "x = eval('1+1')\n")
    report = PreflightChecker().check_path(f)
    cats = {r.category for r in report.risks}
    assert CAT_DYNAMIC_EXEC in cats
    assert any(r.severity == SEVERITY_HIGH for r in report.risks)
    assert report.exit_code() == 1


def test_detects_exec_and_compile(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "a.py",
        """
        exec('print(1)')
        compile('x=1', '<s>', 'exec')
        """,
    )
    report = PreflightChecker().check_path(f)
    assert sum(1 for r in report.risks if r.category == CAT_DYNAMIC_EXEC) == 2


def test_detects_getattr_dynamic(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "v = getattr(obj, name)\n")
    report = PreflightChecker().check_path(f)
    assert any(r.category == CAT_DYNAMIC_ATTR and r.severity == SEVERITY_HIGH for r in report.risks)


def test_getattr_with_string_literal_is_medium(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "v = getattr(obj, 'known_attr')\n")
    report = PreflightChecker().check_path(f)
    risks = [r for r in report.risks if r.category == CAT_DYNAMIC_ATTR]
    assert len(risks) == 1
    assert risks[0].severity == SEVERITY_MEDIUM


def test_detects_dunder_import(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "m = __import__('os')\n")
    report = PreflightChecker().check_path(f)
    assert any(r.category == CAT_DYNAMIC_IMPORT for r in report.risks)


def test_detects_importlib_import_module(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "a.py",
        """
        import importlib
        importlib.import_module('os')
        """,
    )
    report = PreflightChecker().check_path(f)
    assert any(r.category == CAT_DYNAMIC_IMPORT for r in report.risks)


def test_detects_introspection(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "print(vars())\nprint(dir())\n")
    report = PreflightChecker().check_path(f)
    assert sum(1 for r in report.risks if r.category == CAT_INTROSPECTION) == 2


def test_detects_name_string(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "a.py",
        """
        class Foo:
            pass
        x = Foo().__class__.__name__
        """,
    )
    report = PreflightChecker().check_path(f)
    assert any(r.category == CAT_NAME_STRING for r in report.risks)


def test_detects_all_export(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "__all__ = ['foo']\ndef foo(): pass\n")
    report = PreflightChecker().check_path(f)
    assert any(r.category == CAT_ALL_EXPORT for r in report.risks)


def test_detects_main_guard(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "a.py",
        """
        if __name__ == '__main__':
            pass
        """,
    )
    report = PreflightChecker().check_path(f)
    assert any(r.category == CAT_ENTRY_POINT for r in report.risks)


def test_main_guard_reverse_order(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "a.py",
        """
        if '__main__' == __name__:
            pass
        """,
    )
    report = PreflightChecker().check_path(f)
    assert any(r.category == CAT_ENTRY_POINT for r in report.risks)


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------


def test_framework_fastapi(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "api.py",
        """
        from fastapi import FastAPI
        app = FastAPI()
        """,
    )
    report = PreflightChecker().check_path(f)
    assert any(fw.name == "FastAPI" for fw in report.frameworks)
    assert report.suggested_preset == "fastapi"


def test_framework_pydantic(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "m.py",
        """
        from pydantic import BaseModel
        class User(BaseModel):
            x: int
        """,
    )
    report = PreflightChecker().check_path(f)
    assert any(fw.name == "Pydantic" for fw in report.frameworks)


def test_framework_priority_fastapi_over_pydantic(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "api.py",
        """
        from fastapi import FastAPI
        from pydantic import BaseModel
        app = FastAPI()
        class U(BaseModel): x: int
        """,
    )
    report = PreflightChecker().check_path(f)
    assert report.suggested_preset == "fastapi"


# ---------------------------------------------------------------------------
# Directory scanning + report shape
# ---------------------------------------------------------------------------


def test_directory_scan(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "x = 1\n")
    _write(tmp_path, "b.py", "eval('x')\n")
    (tmp_path / "pkg").mkdir()
    _write(tmp_path, "pkg/c.py", "getattr(obj, name)\n")

    report = PreflightChecker().check_path(tmp_path)
    assert report.files_scanned == 3
    assert report.severity_counts()[SEVERITY_HIGH] >= 2


def test_exit_code_safe(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "x = 1\ndef foo(): return 2\n")
    report = PreflightChecker().check_path(f)
    assert report.exit_code() == 0


def test_exit_code_parse_error(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "def broken(:\n")
    report = PreflightChecker().check_path(f)
    assert report.exit_code() == 2
    assert len(report.parse_errors) == 1


def test_json_roundtrip(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "eval('x')\n")
    report = PreflightChecker().check_path(f)
    data = json.loads(report.to_json())
    assert data["version"] == 1
    assert data["exit_code"] == 1
    assert data["files_scanned"] == 1
    assert data["severity_counts"]["high"] >= 1
    assert data["ai_hint"]
    assert "risks" in data and len(data["risks"]) >= 1


def test_ai_hint_mentions_preset_when_framework_detected(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "api.py",
        """
        from fastapi import FastAPI
        app = FastAPI()
        """,
    )
    report = PreflightChecker().check_path(tmp_path)
    assert "fastapi" in report.ai_hint.lower()


def test_text_formatter_smoke(tmp_path: Path) -> None:
    f = _write(tmp_path, "a.py", "eval('x')\n")
    report = PreflightChecker().check_path(f)
    text = format_report_text(report)
    assert "pyobfus pre-flight check" in text
    assert "Next:" in text
    assert "HIGH" in text
