"""Tests for the dependency-hallucination advisory (pyobfus/core/dependency_advisory.py)."""

from __future__ import annotations

import urllib.error
from pathlib import Path
from unittest import mock

from pyobfus.core.dependency_advisory import (
    check_dependency_hallucination,
    collect_declared_dependencies,
    find_dependency_files,
    normalize_name,
    _pypi_exists,
)
from pyobfus.core.preflight import (
    CAT_DEPENDENCY_ADVISORY,
    SEVERITY_INFO,
    SEVERITY_MEDIUM,
    PreflightChecker,
)

# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------


def test_normalize_name_lowercases_and_collapses_separators() -> None:
    assert normalize_name("Some_Package.Name") == "some-package-name"
    assert normalize_name("already-normal") == "already-normal"
    assert normalize_name("multi___under---dash") == "multi-under-dash"


# ---------------------------------------------------------------------------
# find_dependency_files
# ---------------------------------------------------------------------------


def test_find_dependency_files_in_directory(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("click\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("pytest\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "setup.py").write_text("# not a dependency file\n", encoding="utf-8")

    found = {p.name for p in find_dependency_files(tmp_path)}
    assert found == {"requirements.txt", "requirements-dev.txt", "pyproject.toml"}


def test_find_dependency_files_from_file_root_uses_parent(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("click\n", encoding="utf-8")
    script = tmp_path / "app.py"
    script.write_text("print('hi')\n", encoding="utf-8")

    found = {p.name for p in find_dependency_files(script)}
    assert found == {"requirements.txt"}


def test_find_dependency_files_empty_when_none_present(tmp_path: Path) -> None:
    assert find_dependency_files(tmp_path) == []


# ---------------------------------------------------------------------------
# requirements.txt parsing
# ---------------------------------------------------------------------------


def test_collect_declared_dependencies_parses_requirements_txt(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "\n".join(
            [
                "# a comment",
                "",
                "click>=8.0",
                "pyyaml==5.4.1  # inline comment",
                "some-pkg[extra1,extra2]>=1.0,<2.0",
                'pkg-with-marker; python_version >= "3.9"',
                "-r other.txt",
                "-e .",
                "git+https://github.com/example/repo.git@main#egg=vcspkg",
                "https://example.com/some.whl",
            ]
        ),
        encoding="utf-8",
    )

    by_name = collect_declared_dependencies(tmp_path)
    assert set(by_name) == {"click", "pyyaml", "some-pkg", "pkg-with-marker"}


def test_collect_declared_dependencies_normalizes_names(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("Some_Package==1.0\n", encoding="utf-8")
    by_name = collect_declared_dependencies(tmp_path)
    assert "some-package" in by_name


# ---------------------------------------------------------------------------
# pyproject.toml parsing
# ---------------------------------------------------------------------------


def test_collect_declared_dependencies_parses_pyproject_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
        [project]
        name = "demo"
        dependencies = [
            "click>=8.0",
            "pyyaml>=5.4",
        ]

        [project.optional-dependencies]
        dev = ["pytest>=7.0", "black>=22.0"]
        """,
        encoding="utf-8",
    )

    by_name = collect_declared_dependencies(tmp_path)
    assert set(by_name) == {"click", "pyyaml", "pytest", "black"}


def test_collect_declared_dependencies_handles_malformed_toml_gracefully(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("not [ valid toml", encoding="utf-8")
    by_name = collect_declared_dependencies(tmp_path)
    assert by_name == {}


# ---------------------------------------------------------------------------
# _pypi_exists (network layer, mocked)
# ---------------------------------------------------------------------------


def test_pypi_exists_true_on_200() -> None:
    resp = mock.MagicMock()
    resp.status = 200
    resp.__enter__.return_value = resp
    with mock.patch("urllib.request.urlopen", return_value=resp):
        assert _pypi_exists("click", timeout=1.0) is True


def test_pypi_exists_false_on_404() -> None:
    err = urllib.error.HTTPError("url", 404, "Not Found", {}, None)  # type: ignore[arg-type]
    with mock.patch("urllib.request.urlopen", side_effect=err):
        assert _pypi_exists("definitely-not-a-real-package-xyz", timeout=1.0) is False


def test_pypi_exists_none_on_network_error() -> None:
    with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no network")):
        assert _pypi_exists("click", timeout=1.0) is None


def test_pypi_exists_none_on_other_http_error() -> None:
    err = urllib.error.HTTPError("url", 503, "Service Unavailable", {}, None)  # type: ignore[arg-type]
    with mock.patch("urllib.request.urlopen", side_effect=err):
        assert _pypi_exists("click", timeout=1.0) is None


# ---------------------------------------------------------------------------
# check_dependency_hallucination
# ---------------------------------------------------------------------------


def test_no_dependency_files_yields_no_risks(tmp_path: Path) -> None:
    result = check_dependency_hallucination(tmp_path)
    assert result.risks == []
    assert result.checked == 0
    assert result.skipped_offline is False


def test_offline_skips_network_and_yields_no_risks(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("click>=8.0\n", encoding="utf-8")
    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists") as mocked:
        result = check_dependency_hallucination(tmp_path, offline=True)
        mocked.assert_not_called()
    assert result.risks == []
    assert result.skipped_offline is True


def test_existing_package_yields_no_risk(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("click>=8.0\n", encoding="utf-8")
    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists", return_value=True):
        result = check_dependency_hallucination(tmp_path)
    assert result.risks == []
    assert result.checked == 1


def test_hallucinated_package_yields_medium_risk(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "totally-made-up-hallucinated-pkg==1.0\n", encoding="utf-8"
    )
    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists", return_value=False):
        result = check_dependency_hallucination(tmp_path)

    assert len(result.risks) == 1
    risk = result.risks[0]
    assert risk.category == CAT_DEPENDENCY_ADVISORY
    assert risk.severity == SEVERITY_MEDIUM
    assert "totally-made-up-hallucinated-pkg" in risk.message
    assert "slopsquatting" in risk.suggestion


def test_custom_index_softens_message(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "--extra-index-url https://internal.example.com/simple\n" "our-internal-pkg==1.0\n",
        encoding="utf-8",
    )
    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists", return_value=False):
        result = check_dependency_hallucination(tmp_path)

    assert len(result.risks) == 1
    assert "custom package index" in result.risks[0].suggestion.lower()


def test_network_errors_produce_one_info_risk(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("click>=8.0\npyyaml>=5.4\n", encoding="utf-8")
    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists", return_value=None):
        result = check_dependency_hallucination(tmp_path)

    assert len(result.risks) == 1
    assert result.risks[0].severity == SEVERITY_INFO
    assert "could not be verified" in result.risks[0].message


# ---------------------------------------------------------------------------
# Integration through PreflightChecker
# ---------------------------------------------------------------------------


def test_preflight_checker_default_does_not_run_dependency_check(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "totally-made-up-hallucinated-pkg==1.0\n", encoding="utf-8"
    )
    f = tmp_path / "a.py"
    f.write_text("x = 1\n", encoding="utf-8")

    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists", return_value=False) as mocked:
        report = PreflightChecker().check_path(f)
        mocked.assert_not_called()
    assert CAT_DEPENDENCY_ADVISORY not in report.category_counts()


def test_preflight_checker_offline_finds_no_dependency_files_network_call(
    tmp_path: Path,
) -> None:
    (tmp_path / "requirements.txt").write_text(
        "totally-made-up-hallucinated-pkg==1.0\n", encoding="utf-8"
    )
    f = tmp_path / "a.py"
    f.write_text("x = 1\n", encoding="utf-8")

    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists") as mocked:
        report = PreflightChecker(check_dependencies=True, offline=True).check_path(f)
        mocked.assert_not_called()
    assert CAT_DEPENDENCY_ADVISORY not in report.category_counts()


def test_preflight_checker_opted_in_reports_hallucinated_dependency(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "totally-made-up-hallucinated-pkg==1.0\n", encoding="utf-8"
    )
    f = tmp_path / "a.py"
    f.write_text("x = 1\n", encoding="utf-8")

    with mock.patch("pyobfus.core.dependency_advisory._pypi_exists", return_value=False):
        report = PreflightChecker(check_dependencies=True).check_path(f)

    assert report.category_counts().get(CAT_DEPENDENCY_ADVISORY) == 1
    assert any(r.category == CAT_DEPENDENCY_ADVISORY for r in report.risks)
