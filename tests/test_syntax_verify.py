from pathlib import Path

from pyobfus.core.syntax_verify import verify_generated_syntax


def test_directory_syntax_verification_reports_relative_error(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    output = tmp_path / "dist"
    output.mkdir()
    (output / "good.py").write_text("value = 1\n", encoding="utf-8")
    nested = output / "pkg"
    nested.mkdir()
    (nested / "bad.py").write_text("def broken(:\n", encoding="utf-8")

    result = verify_generated_syntax(source, output)

    assert result["syntax_valid"] is False
    assert result["files_checked"] == 1
    assert result["errors"][0]["path"] == "pkg/bad.py"
    assert result["errors"][0]["line"] == 1
    assert not list(output.rglob("__pycache__"))


def test_syntax_verification_reports_missing_output(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    output = tmp_path / "missing"

    result = verify_generated_syntax(source, output)

    assert result["syntax_valid"] is False
    assert result["files_checked"] == 0
    assert result["errors"][0]["message"].startswith("No generated")
