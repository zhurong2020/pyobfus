"""A real FastAPI + Pydantic v2 application, obfuscated and exercised over HTTP.

Framework presets are otherwise only tested for what they exclude. This test
builds `frameworks/fastapi_shop/` (three modules: Pydantic models, pricing
rules, FastAPI routes) with `--preset fastapi`, drives the same HTTP
scenarios against the original and the obfuscated build, and requires the
results to be identical: status codes, response bodies, and the location and
type of every validation error.

It also checks that the private mapping stays out of the output, that the
pricing module's own names do not survive, and that a traceback raised from
the obfuscated build unmaps back to the original function name.

FastAPI is not a dev dependency, so the test is skipped unless the pinned
stack in `frameworks/requirements.txt` is installed. CI runs it in the
`framework-lane.yml` workflow (weekly and on demand), not on every push.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

FRAMEWORKS = Path(__file__).resolve().parent / "frameworks"
APP_DIR = FRAMEWORKS / "fastapi_shop"
DRIVER = FRAMEWORKS / "drive_fastapi_shop.py"
# No __pycache__: it would land in the build being inspected and in the repo.
UTF8_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def _run(*args: str, cwd: Path = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd) if cwd else None,
        env=UTF8_ENV,
        timeout=300,
    )


def _drive(app_dir: Path) -> subprocess.CompletedProcess:
    result = _run(str(DRIVER), str(app_dir))
    assert result.returncode == 0, result.stderr
    return result


@pytest.fixture(scope="module")
def build(tmp_path_factory):
    work = tmp_path_factory.mktemp("fastapi_shop")
    out = work / "dist"
    mapping = work / "private" / "shop.map.json"
    result = _run(
        "-m",
        "pyobfus",
        str(APP_DIR),
        "-o",
        str(out),
        "--preset",
        "fastapi",
        "--save-mapping",
        str(mapping),
        "--verify-syntax",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return out, mapping


def test_obfuscated_app_answers_exactly_like_the_original(build):
    out, _ = build
    original = json.loads(_drive(APP_DIR).stdout)
    obfuscated = json.loads(_drive(out).stdout)
    assert len(original) == 7
    assert obfuscated == original


def test_mapping_and_private_names_stay_out_of_the_build(build):
    out, mapping = build
    shipped = sorted(p.name for p in out.rglob("*") if p.is_file())
    assert shipped == ["app.py", "models.py", "pricing.py"]
    assert mapping.exists()

    pricing = (out / "pricing.py").read_text(encoding="utf-8")
    for private_name in ("discount_rate", "quote_order", "TIER_DISCOUNTS", "VOLUME_BONUS"):
        assert private_name not in pricing


def test_traceback_from_obfuscated_app_unmaps(build, tmp_path):
    out, mapping = build
    trace = _drive(out).stderr
    assert "ZeroDivisionError" in trace
    assert "margin_ratio" not in trace

    trace_file = tmp_path / "error.log"
    trace_file.write_text(trace, encoding="utf-8")
    result = _run("-m", "pyobfus", "--unmap", "--trace", str(trace_file), "--mapping", str(mapping))
    assert result.returncode == 0, result.stderr
    assert "in margin_ratio" in result.stdout
