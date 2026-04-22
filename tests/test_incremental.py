"""Tests for --incremental obfuscation + BuildCache (P1-5)."""

from __future__ import annotations

import json
import textwrap
import time
from pathlib import Path

from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.cache import BuildCache


def _write(tmp_path: Path, name: str, src: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(src).lstrip(), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# BuildCache unit tests
# ---------------------------------------------------------------------------


def test_build_signature_is_stable(tmp_path: Path) -> None:
    src = _write(tmp_path, "a.py", "x = 1\n")
    cfg = ObfuscationConfig.preset_balanced()
    cache = BuildCache(tmp_path / "out")
    sig1 = cache.build_signature(tmp_path, [src], cfg)
    sig2 = cache.build_signature(tmp_path, [src], cfg)
    assert sig1 == sig2


def test_build_signature_changes_with_file_content(tmp_path: Path) -> None:
    src = _write(tmp_path, "a.py", "x = 1\n")
    cfg = ObfuscationConfig.preset_balanced()
    cache = BuildCache(tmp_path / "out")
    sig1 = cache.build_signature(tmp_path, [src], cfg)
    src.write_text("x = 2\n", encoding="utf-8")
    sig2 = cache.build_signature(tmp_path, [src], cfg)
    assert sig1 != sig2


def test_build_signature_changes_with_config(tmp_path: Path) -> None:
    src = _write(tmp_path, "a.py", "x = 1\n")
    cache = BuildCache(tmp_path / "out")
    sig1 = cache.build_signature(tmp_path, [src], ObfuscationConfig.preset_safe())
    sig2 = cache.build_signature(tmp_path, [src], ObfuscationConfig.preset_aggressive())
    assert sig1 != sig2


def test_can_reuse_without_manifest(tmp_path: Path) -> None:
    src = _write(tmp_path, "a.py", "x = 1\n")
    cache = BuildCache(tmp_path / "out")
    sig = cache.build_signature(tmp_path, [src], ObfuscationConfig())
    hit, reason, outputs = cache.can_reuse(sig)
    assert hit is False
    assert "no manifest" in reason.lower()
    assert outputs is None


def test_save_and_reuse_manifest_hit(tmp_path: Path) -> None:
    src = _write(tmp_path, "a.py", "x = 1\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    fake_output = out_dir / "a.py"
    fake_output.write_text("obfuscated\n", encoding="utf-8")

    cache = BuildCache(out_dir)
    sig = cache.build_signature(tmp_path, [src], ObfuscationConfig())
    cache.save_manifest(sig, [str(fake_output)])

    hit, reason, outputs = cache.can_reuse(sig)
    assert hit is True
    assert "unchanged" in reason
    assert outputs == [str(fake_output)]


def test_can_reuse_miss_when_output_deleted(tmp_path: Path) -> None:
    src = _write(tmp_path, "a.py", "x = 1\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    fake_output = out_dir / "a.py"
    fake_output.write_text("x\n", encoding="utf-8")

    cache = BuildCache(out_dir)
    sig = cache.build_signature(tmp_path, [src], ObfuscationConfig())
    cache.save_manifest(sig, [str(fake_output)])

    fake_output.unlink()
    hit, reason, _ = cache.can_reuse(sig)
    assert hit is False
    assert "missing" in reason


def test_manifest_version_mismatch_invalidates(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / ".pyobfus-cache").mkdir()
    (out / ".pyobfus-cache" / "manifest.json").write_text(
        json.dumps({"version": 999, "signature": {}, "output_files": []}),
        encoding="utf-8",
    )
    cache = BuildCache(out)
    assert cache.load_manifest() is None


# ---------------------------------------------------------------------------
# CLI end-to-end
# ---------------------------------------------------------------------------


def test_incremental_first_run_builds_and_writes_manifest(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _write(src, "a.py", "def foo(): return 1\n")
    out = tmp_path / "dist"

    runner = CliRunner()
    result = runner.invoke(main, [str(src), "-o", str(out), "--incremental"])
    assert result.exit_code == 0, result.output
    assert (out / "a.py").exists()
    assert (out / ".pyobfus-cache" / "manifest.json").exists()


def test_incremental_second_run_hits_cache(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _write(src, "a.py", "def foo(): return 1\n")
    out = tmp_path / "dist"

    runner = CliRunner()
    # First run
    r1 = runner.invoke(main, [str(src), "-o", str(out), "--incremental"])
    assert r1.exit_code == 0
    first_output = (out / "a.py").read_text(encoding="utf-8")
    first_manifest_mtime = (out / ".pyobfus-cache" / "manifest.json").stat().st_mtime

    # Touch output file's mtime back so we can detect whether it got rewritten
    time.sleep(0.01)

    # Second run — same inputs
    r2 = runner.invoke(main, [str(src), "-o", str(out), "--incremental"])
    assert r2.exit_code == 0
    assert "skipping" in r2.output
    # Output unchanged
    assert (out / "a.py").read_text(encoding="utf-8") == first_output
    # Manifest not rewritten (cache hit doesn't save a new manifest)
    assert (out / ".pyobfus-cache" / "manifest.json").stat().st_mtime == first_manifest_mtime


def test_incremental_rebuilds_after_source_edit(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    a = _write(src, "a.py", "def foo(): return 1\n")
    out = tmp_path / "dist"

    runner = CliRunner()
    runner.invoke(main, [str(src), "-o", str(out), "--incremental"])
    # Change source
    a.write_text("def foo(): return 42\n", encoding="utf-8")

    result = runner.invoke(main, [str(src), "-o", str(out), "--incremental", "--verbose"])
    assert result.exit_code == 0
    # Verbose message signals rebuild reason
    assert "rebuilding" in result.output or "Discovered" in result.output


def test_incremental_json_reports_skipped_files(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _write(src, "a.py", "def foo(): return 1\n")
    _write(src, "b.py", "def bar(): return 2\n")
    out = tmp_path / "dist"

    runner = CliRunner()
    # First run (builds cache)
    r1 = runner.invoke(main, [str(src), "-o", str(out), "--incremental"])
    assert r1.exit_code == 0

    # Second run in JSON mode — should skip
    r2 = runner.invoke(main, [str(src), "-o", str(out), "--incremental", "--json"])
    assert r2.exit_code == 0, r2.output
    data = json.loads(r2.output)
    assert data["status"] == "success"
    assert data["stats"]["files_skipped"] >= 1


def test_incremental_noop_on_single_file_mode(tmp_path: Path) -> None:
    """Single file inputs should skip the incremental machinery entirely."""
    src = _write(tmp_path, "a.py", "def foo(): return 1\n")
    out = tmp_path / "a_obf.py"

    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--incremental"])
    assert result.exit_code == 0
    assert out.exists()
    # No cache dir because single-file mode doesn't use it
    assert not (tmp_path / ".pyobfus-cache").exists()
