"""Native 3.15 syntax regressions; keep sources strings for older collectors."""

import subprocess
import sys

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.orchestrator import CrossFileOrchestrator

pytestmark = pytest.mark.skipif(sys.version_info < (3, 15), reason="Python 3.15 syntax")


@pytest.mark.parametrize("jobs", [1, 4])
@pytest.mark.parametrize(
    "source",
    [
        'lazy from calculator import Calculator\nprint("START")\nprint(Calculator() is not None)\n',
        '__lazy_modules__ = ["calculator"]\nfrom calculator import Calculator\nprint("START")\nprint(Calculator() is not None)\n',
        'rows = [{"a": 1}, {"b": 2}]\nvalues = {**row for row in rows}\nprint(values)\n',
    ],
    ids=["lazy-from", "lazy-control", "dict-unpacking"],
)
def test_native_directory_semantics(tmp_path, source, jobs):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "app.py").write_text(source, encoding="utf-8")
    (src / "calculator.py").write_text(
        'print("LOADED")\nclass Calculator: pass\n', encoding="utf-8"
    )
    config = ObfuscationConfig.community_edition()
    config.max_workers = jobs
    result = CrossFileOrchestrator(config).obfuscate(src, out)
    assert result.success, result.errors
    original = subprocess.run(
        [sys.executable, "app.py"], cwd=src, text=True, capture_output=True, timeout=30
    )
    built = subprocess.run(
        [sys.executable, "app.py"], cwd=out, text=True, capture_output=True, timeout=30
    )
    assert original.returncode == 0, original.stderr
    assert built.returncode == 0, built.stderr
    assert built.stdout.splitlines() == original.stdout.splitlines()


@pytest.mark.parametrize("jobs", [1, 4])
@pytest.mark.parametrize(
    "expression",
    [
        "[*part for part in [[1, 2], [3]]]",
        "{*part for part in [[1, 2], [2, 3]]}",
        "tuple((*part for part in [[1, 2], [3]]))",
        "{**part for part in [{'a': 1}, {'b': 2}]}",
        "[[*part for part in group] for group in [[[1], [2]], [[3]]]]",
        "{**(bound := part) for part in [{'a': 1}, {'b': 2}]}",
        "{**{str(index): index} for index in range(3)}",
        "{**part async for part in stream()}",
        "[*part async for part in stream_lists()]",
        "{*part async for part in stream_lists()}",
        "tuple([item async for item in (*part async for part in stream_lists())])",
    ],
)
def test_unpacking_scopes(tmp_path, expression, jobs):
    source = (
        "import asyncio\n"
        "async def stream():\n"
        '    for part in [{"a": 1}, {"b": 2}]: yield part\n'
        "async def stream_lists():\n"
        "    for part in [[1, 2], [3]]: yield part\n"
        "async def evaluate():\n"
        '    part = "outer"\n'
        f"    value = {expression}\n"
        "    print(value, part)\n"
        "asyncio.run(evaluate())\n"
    )
    test_native_directory_semantics(tmp_path, source, jobs)


@pytest.mark.parametrize("jobs", [1, 4])
@pytest.mark.parametrize(
    "statement, usage",
    [
        ("lazy import calculator as calc", "calc.Calculator()"),
        ("lazy from calculator import Calculator as Alias", "Alias()"),
        ("lazy from calculator import Calculator, OTHER", "(Calculator(), OTHER)"),
        ("lazy import pkg.worker as calc", "calc.Calculator()"),
        ("lazy from .worker import Calculator", "Calculator()"),
    ],
)
def test_lazy_import_variants(tmp_path, statement, usage, jobs):
    src, out = tmp_path / "src", tmp_path / "out"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    worker = 'print("LOADED")\nclass Calculator: pass\nOTHER = 2\n'
    (src / "calculator.py").write_text(worker, encoding="utf-8")
    (src / "pkg" / "worker.py").write_text(worker, encoding="utf-8")
    source = f'{statement}\nprint("START")\nprint({usage} is not None)\n'
    (src / "pkg" / "entry.py").write_text(source, encoding="utf-8")
    (src / "app.py").write_text("import pkg.entry\n", encoding="utf-8")
    config = ObfuscationConfig.community_edition()
    config.max_workers = jobs
    result = CrossFileOrchestrator(config).obfuscate(src, out)
    assert result.success, result.errors
    for directory in (src, out):
        run = subprocess.run(
            [sys.executable, "app.py"], cwd=directory, text=True, capture_output=True, timeout=30
        )
        assert run.returncode == 0, run.stderr
        assert run.stdout.splitlines() == ["START", "LOADED", "True"]


@pytest.mark.parametrize("statement", ["lazy import os", "lazy from os import path"])
def test_function_lazy_import_is_syntax_error(tmp_path, statement):
    path = tmp_path / "invalid.py"
    path.write_text(f"def function():\n    {statement}\n", encoding="utf-8")
    run = subprocess.run([sys.executable, str(path)], text=True, capture_output=True, timeout=30)
    assert run.returncode != 0
    assert "SyntaxError" in run.stderr


def test_pro_import_obfuscation_preserves_lazy():
    import ast

    from pyobfus_pro.import_obfuscation import ImportObfuscator

    tree = ast.parse("lazy import missing\nlazy from missing import name\n")
    transformed = ImportObfuscator().transform(tree)
    assert all(getattr(node, "is_lazy", False) for node in transformed.body)


def test_new_builtin_and_lazy_control_names_preserved():
    config = ObfuscationConfig.community_edition()
    for name in (
        "ImportCycleError",
        "__lazy_import__",
        "frozendict",
        "sentinel",
        "__lazy_modules__",
    ):
        assert config.should_exclude_name(name)


@pytest.mark.parametrize(
    "statement", ["lazy import missing_dependency", "lazy from missing_dependency import item"]
)
def test_lazy_failure_occurs_only_on_first_use(tmp_path, statement):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    name = "item" if " from " in statement else "missing_dependency"
    (src / "app.py").write_text(
        f'{statement}\nprint("BEFORE", flush=True)\nprint({name})\n', encoding="utf-8"
    )
    result = CrossFileOrchestrator(ObfuscationConfig.community_edition()).obfuscate(src, out)
    assert result.success, result.errors
    for directory in (src, out):
        run = subprocess.run(
            [sys.executable, "app.py"], cwd=directory, text=True, capture_output=True, timeout=30
        )
        assert run.returncode != 0
        assert run.stdout.splitlines() == ["BEFORE"]
        assert "ModuleNotFoundError" in run.stderr


def test_pro_import_obfuscation_preserves_lazy_control():
    import ast

    from pyobfus_pro.import_obfuscation import ImportObfuscator

    tree = ast.parse('__lazy_modules__ = ["missing"]\nimport missing\n')
    expected = ast.dump(tree)
    transformed = ImportObfuscator().transform(tree)
    assert ast.dump(transformed) == expected


def test_builtin_values_and_utf8_artifact(tmp_path):
    source = (
        "import json\n"
        'marker = sentinel("未加载")\n'
        'value = frozendict({"结果": 42})\n'
        "print(json.dumps(dict(value), ensure_ascii=False), bool(marker), ImportCycleError.__name__)\n"
    )
    test_native_directory_semantics(tmp_path, source, 1)


def test_pro_source_and_marshal_artifacts_execute(tmp_path, monkeypatch):
    from click.testing import CliRunner

    from pyobfus.cli import main

    monkeypatch.setattr("pyobfus.cli.is_trial_active", lambda: True)
    source = tmp_path / "source.py"
    marked_source = (
        "from pyobfus_pro import opacity, seal_code, vault_secrets, Layer\n"
        'CFG = vault_secrets({"message": "你好"})\n'
        "@opacity(Layer.ENCRYPTED)\n"
        "def compute(value):\n    return value * 2 + 7\n"
        "@seal_code\n"
        "def guard(value):\n    return value - 1\n"
        'print(compute(5) + guard(10), CFG.get("message"))\n'
    )
    for label, flags in [
        ("source", ["--string-encryption", "--import-obfuscation"]),
        ("marshal", ["--selective-opacity", "--seal-code", "--vault"]),
    ]:
        source.write_text(
            (
                marked_source
                if label == "marshal"
                else 'import math\nprint(int(math.sqrt(676)), "你好")\n'
            ),
            encoding="utf-8",
        )
        out = tmp_path / f"{label}.py"
        result = CliRunner().invoke(
            main, [str(source), "-o", str(out), "--no-config", "--level", "pro", *flags]
        )
        assert result.exit_code == 0, result.output
        run = subprocess.run(
            [sys.executable, out.name], cwd=tmp_path, text=True, capture_output=True, timeout=30
        )
        assert run.returncode == 0, run.stderr
        assert run.stdout.splitlines() == ["26 你好"]


@pytest.mark.parametrize(
    "statement, proved",
    [
        ("import pkg.mod", True),
        ("lazy import pkg.mod", False),
        ('__lazy_modules__ = ["pkg.mod"]\nimport pkg.mod', False),
    ],
)
def test_lazy_dotted_bindings_do_not_prove_eager_package_edges(tmp_path, statement, proved):
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg/__init__.py").write_text("", encoding="utf-8")
    (src / "pkg/mod.py").write_text("LIMIT = 7\n", encoding="utf-8")
    (src / "app.py").write_text(f"{statement}\nprint(pkg.mod.LIMIT)\n", encoding="utf-8")
    planner = CrossFileOrchestrator(ObfuscationConfig.community_edition())
    planner.phase1_scan(src)
    assert planner.global_table.get_obfuscated_import("pkg.mod", "LIMIT") != "LIMIT"
    assert bool(planner.attribute_plans["app"].edits) is proved
