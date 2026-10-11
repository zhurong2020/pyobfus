"""Module attribute and runtime enum injection advisories stay non-blocking."""

import inspect
import json

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core.preflight import PreflightChecker

H_CASES = [
    ("from pkg import core", "core.LIMIT", "LIMIT = 7\n"),
    ("import pkg.core as engine", "engine.scale()", "def scale(): return 7\n"),
    ("import pkg.core", "pkg.core.Number()", "class Number: pass\n"),
]


def project(tmp_path, entry, core="LIMIT = 7\n"):
    source = tmp_path / "src"
    (source / "pkg").mkdir(parents=True)
    (source / "pkg/__init__.py").write_text("", encoding="utf-8")
    (source / "pkg/core.py").write_text(core, encoding="utf-8")
    (source / "entry.py").write_text(entry, encoding="utf-8")
    return source


def check_json(path, *args):
    runner = CliRunner(
        **({"mix_stderr": False} if "mix_stderr" in inspect.signature(CliRunner).parameters else {})
    )
    result = runner.invoke(
        main, [str(path), "--check", "--json", "--offline", "--no-config", *args]
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)


def advisories(report, marker="AttributeError"):
    risks = report["risks"] if isinstance(report, dict) else [r.to_dict() for r in report.risks]
    return [
        r for r in risks if r["category"] == "compatibility_advisory" and marker in r["message"]
    ]


@pytest.mark.parametrize("import_line,expression,core", H_CASES)
def test_directory_module_attributes_json(tmp_path, import_line, expression, core):
    source = project(tmp_path, f"{import_line}\nprint({expression})\nprint({expression})\n", core)
    payload = check_json(source)
    findings = advisories(payload)
    assert len(findings) == 1
    risk = findings[0]
    assert risk["severity"] == "medium"
    assert expression.rstrip("()") in risk["message"]
    assert (
        "directory builds do not rename attribute access through a module object" in risk["message"]
    )
    assert "from pkg.core import" in risk["suggestion"]
    assert "exclude_names" in risk["suggestion"]
    assert payload["ai_hint"].startswith("Low risk. Run:")
    assert not advisories(check_json(source / "entry.py"))


@pytest.mark.parametrize(
    "entry,core,preserve",
    [
        ("import json\njson.dumps({})\n", "LIMIT = 7\n", []),
        ('import requests as client\nclient.get("example")\n', "LIMIT = 7\n", []),
        ("from requests import sessions\nsessions.Session()\n", "LIMIT = 7\n", []),
        ("from pkg import core\ncore.LIMIT\n", "LIMIT = 7\n", ["LIMIT"]),
        ("from pkg import core\ncore.LIMIT\n", "LIMIT = 7\n__all__ = []\n", []),
        ("from pkg import core\ncore._private\n", "_private = 7\n", []),
        ("from pkg import core\ncore.__all__\n", "__all__ = []\n", []),
        ("from pkg import core\ndef use(core): return core.LIMIT\n", "LIMIT = 7\n", []),
        ("from pkg import core\ncore = object()\ncore.LIMIT\n", "LIMIT = 7\n", []),
        ("from pkg import core\n[core.LIMIT for core in []]\n", "LIMIT = 7\n", []),
        (
            "def bind():\n    from pkg import core\ndef use(): return core.LIMIT\n",
            "LIMIT = 7\n",
            [],
        ),
    ],
)
def test_unchanged_or_unresolved_attributes(tmp_path, entry, core, preserve):
    source = project(tmp_path, entry, core)
    assert not advisories(PreflightChecker(preserve_names=preserve).check_path(source))


def test_relative_import_and_alias_dedupe(tmp_path):
    source = project(tmp_path, "")
    (source / "pkg/use.py").write_text(
        "from . import core\nfrom .core import LIMIT\nimport pkg.core as engine\n"
        "def use(): return core.LIMIT + engine.LIMIT\n",
        encoding="utf-8",
    )
    assert len(advisories(PreflightChecker().check_path(source))) == 1


def test_config_and_preset_exclusions(tmp_path):
    source = project(tmp_path, "from pkg import core\ncore.LIMIT\n")
    config = tmp_path / "config.yaml"
    config.write_text("obfuscation:\n  exclude_names: [LIMIT]\n", encoding="utf-8")
    runner = CliRunner(
        **({"mix_stderr": False} if "mix_stderr" in inspect.signature(CliRunner).parameters else {})
    )
    for args in [["--config", str(config)], ["--preset", "safe"]]:
        if args[0] == "--preset":
            (source / "pkg/core.py").write_text("main = 7\n", encoding="utf-8")
            (source / "entry.py").write_text("from pkg import core\ncore.main\n", encoding="utf-8")
        result = runner.invoke(main, [str(source), "--check", "--json", "--offline", *args])
        assert result.exit_code == 0, result.output
        assert not advisories(json.loads(result.stdout))


@pytest.mark.parametrize(
    "imports,decorator,base",
    [
        ("import enum", "enum.global_enum", "enum.Enum"),
        ("from enum import Enum, global_enum", "global_enum", "Enum"),
        ("import enum as e", "e.global_enum", "e.Enum"),
        ("from enum import Enum, global_enum as export", "export", "Enum"),
    ],
)
def test_global_enum_json(tmp_path, imports, decorator, base):
    source = tmp_path / "colors.py"
    source.write_text(
        f"{imports}\n@{decorator}\nclass Color({base}):\n    RED = 1\n    BLUE = 2\n",
        encoding="utf-8",
    )
    payload = check_json(source)
    findings = advisories(payload, "enum.global_enum")
    assert len(findings) == 1
    assert findings[0]["severity"] == "medium"
    assert "Color" in findings[0]["message"]
    assert "exclude_names: RED, BLUE." in findings[0]["suggestion"]
    assert payload["ai_hint"].startswith("Low risk. Run:")


def test_global_enum_truncation(tmp_path):
    source = tmp_path / "colors.py"
    source.write_text(
        "import enum\n@enum.global_enum\nclass Color(enum.Enum):\n"
        + "".join(f"    MEMBER_{i} = {i}\n" for i in range(13)),
        encoding="utf-8",
    )
    suggestion = advisories(check_json(source), "enum.global_enum")[0]["suggestion"]
    assert "MEMBER_9" in suggestion and "MEMBER_10" not in suggestion
    assert "and 3 more" in suggestion


@pytest.mark.parametrize(
    "code",
    [
        "import enum\nclass Color(enum.Enum):\n    RED = 1\n",
        "from other import global_enum\n@global_enum\nclass Color:\n    RED = 1\n",
        "import other as enum\n@enum.global_enum\nclass Color:\n    RED = 1\n",
        "import enum\ndef use(enum):\n    @enum.global_enum\n    class Color:\n        RED = 1\n",
    ],
)
def test_only_known_enum_decorator(tmp_path, code):
    source = tmp_path / "colors.py"
    source.write_text(code, encoding="utf-8")
    assert not advisories(PreflightChecker().check_path(source), "enum.global_enum")


def test_parse_errors_keep_existing_result(tmp_path):
    source = project(tmp_path, "from pkg import core\ncore.LIMIT\n")
    (source / "broken.py").write_text("def :", encoding="utf-8")
    report = PreflightChecker().check_path(source)
    assert report.exit_code() == 2
    assert report.parse_errors


def test_annotations_and_lambda_defaults(tmp_path):
    source = project(
        tmp_path,
        "import pkg.core as core\ndef use(x: core.LIMIT): pass\n"
        + "fn = lambda value=core.LIMIT: value\n",
    )
    assert len(advisories(PreflightChecker().check_path(source))) == 1


def test_enum_private_and_ignored_members(tmp_path):
    source = tmp_path / "colors.py"
    source.write_text(
        "import enum\n@enum.global_enum\nclass Color(enum.Enum):\n"
        + '    _ignore_ = "ignored"\n    ignored = 0\n    _RED = 1\n    BLUE: int = 2\n',
        encoding="utf-8",
    )
    suggestion = advisories(check_json(source), "enum.global_enum")[0]["suggestion"]
    assert "exclude_names: _RED, BLUE." in suggestion
    assert "ignored" not in suggestion


def test_conflicting_import_binding_is_unresolved(tmp_path):
    source = project(tmp_path, "import pkg.core as core\nimport other as core\ncore.LIMIT\n")
    assert not advisories(PreflightChecker().check_path(source))


@pytest.mark.parametrize("expression", ["lambda: core.LIMIT", "[core.LIMIT for value in []]"])
def test_class_import_does_not_escape_into_child_scope(tmp_path, expression):
    source = project(tmp_path, f"class Box:\n    from pkg import core\n    value = {expression}\n")
    assert not advisories(PreflightChecker().check_path(source))
