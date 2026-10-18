"""Regression coverage independent of the builder's CPython patch release."""

import ast
import shutil
import subprocess

import pytest

from pyobfus.core.generator import CodeGenerator

CASES = [
    '''f"{d.get('k', 'z')}"''',
    '''f"{f'{x}'}"''',
    '''f"{('yes' if c else 'no')}"''',
    '''f"{'|'.join(xs)}"''',
    '''f"{x:{'>'}{w}}"''',
    '''f"""{"it's"} {'say "hi"'}"""''',
]


@pytest.mark.parametrize("expression", CASES)
def test_generated_fstring_compiles_on_310(expression):
    interpreter = shutil.which("/usr/bin/python3.10")
    if not interpreter:
        pytest.skip("Python 3.10 is unavailable")
    output = CodeGenerator.generate(ast.parse(expression))
    result = subprocess.run(
        [interpreter, "-c", "import sys; compile(sys.stdin.read(), '<output>', 'exec')"],
        input=output,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, (output, result.stderr)


@pytest.mark.parametrize("expression", CASES)
def test_backport_direct(expression):
    from pyobfus.core.unparse import FStringUnparser
    from pyobfus.core.fstring_compat import pep701_locations

    output = FStringUnparser().visit(ast.parse(expression))
    assert not pep701_locations(output), output
    interpreter = shutil.which("/usr/bin/python3.10")
    if interpreter:
        result = subprocess.run(
            [interpreter, "-c", "import sys; compile(sys.stdin.read(), '<backport>', 'exec')"],
            input=output,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, (output, result.stderr)


@pytest.mark.parametrize(
    "version,backport",
    [
        ((3, 9, 0), False),
        ((3, 11, 9), False),
        ((3, 12, 0), True),
        ((3, 12, 8), True),
        ((3, 12, 9), False),
        ((3, 13, 0), False),
        ((3, 14, 0), False),
    ],
)
def test_version_gate(monkeypatch, version, backport):
    import importlib

    module = importlib.import_module("pyobfus.core.unparse")
    monkeypatch.setattr(module.sys, "version_info", version)
    monkeypatch.setattr(module.ast, "unparse", lambda tree: "native")
    monkeypatch.setattr(module, "_backport_available", lambda: True)
    monkeypatch.setattr(module.FStringUnparser, "visit", lambda self, tree: "backport")
    assert module.unparse(ast.parse("1")) == ("backport" if backport else "native")


@pytest.mark.parametrize("missing", ["precedence", "precedence_member", "base"])
def test_private_api_fallback(monkeypatch, missing):
    import importlib

    module = importlib.import_module("pyobfus.core.unparse")
    monkeypatch.setattr(module.sys, "version_info", (3, 12, 3))
    if missing == "precedence":
        monkeypatch.delattr(module.ast, "_Precedence", raising=False)
    elif missing == "precedence_member":
        monkeypatch.setattr(module.ast, "_Precedence", object, raising=False)
    else:
        monkeypatch.setattr(module, "_BaseUnparser", object)
    monkeypatch.setattr(module.ast, "unparse", lambda tree: "native")
    assert module.unparse(ast.parse("1")) == "native"
    assert module.FStringUnparser().visit(ast.parse("1")) == "native"


PEP701 = [
    'f"{x:{w:{d}}}"',
    "f'{d.get('k')}'",
    'f"{f"{x}"}"',
    'f"{x # comment\n}"',
    "f\"{chr(10) + '\\n'}\"",
    'f"{(\n x\n)}"',
    'f"{x:{">"}{w}}"',
]


@pytest.mark.skipif(__import__("sys").version_info < (3, 12), reason="PEP 701 tokenizer")
@pytest.mark.parametrize("source", PEP701)
def test_detector_positive(source):
    from pyobfus.core.fstring_compat import pep701_locations

    ast.parse(source)
    assert pep701_locations(source)


@pytest.mark.parametrize(
    "source",
    CASES
    + [
        "\"f'{not_a_field['x']}'\"",
        'f"literal # text \\n {{braces}} {x}"',
        'f"""{(\n x\n)}"""',
        r'f"{1:\\>3}"',
    ],
)
def test_detector_negative(source):
    from pyobfus.core.fstring_compat import pep701_locations

    ast.parse(source)
    assert not pep701_locations(source)


@pytest.mark.skipif(__import__("sys").version_info < (3, 12), reason="PEP 701 tokenizer")
def test_guard(tmp_path):
    from pyobfus.core.fstring_compat import ensure_fstring_compatibility
    from pyobfus.exceptions import FStringCompatibilityError

    with pytest.raises(FStringCompatibilityError, match=r"fixture.py:2:"):
        ensure_fstring_compatibility("x = 1", "x = 1\nf'{d['k']}'", "fixture.py")
    ensure_fstring_compatibility(PEP701[0], PEP701[1], "fixture.py")


@pytest.mark.parametrize("mode", ["file", "directory", "legacy"])
def test_real_artifact(tmp_path, monkeypatch, mode):
    import os
    import sys
    from pyobfus.core.fstring_compat import pep701_locations

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    directory = mode != "file"
    src = tmp_path / "src"
    src.mkdir()
    program = "d={'k':'value'}; x=3; c=True; xs=['a','b']; w=5\n"
    program += "\n".join(f"print({expr})" for expr in CASES) + "\n"
    (src / "app.py").write_text(program)
    out = tmp_path / ("out" if directory else "out.py")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(src if directory else src / "app.py"),
            "-o",
            str(out),
            "--no-config",
            "--json",
            "--verify-names",
            *(["--no-cross-file"] if mode == "legacy" else []),
        ],
        env=dict(os.environ),
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    artifact = out / "app.py" if directory else out
    assert not pep701_locations(artifact.read_text())
    expected = subprocess.run([sys.executable, str(src / "app.py")], capture_output=True, text=True)
    for interpreter in [sys.executable, shutil.which("/usr/bin/python3.10")]:
        if not interpreter:
            continue
        actual = subprocess.run([interpreter, str(artifact)], capture_output=True, text=True)
        assert actual.returncode == 0, actual.stderr
        assert actual.stdout.splitlines() == expected.stdout.splitlines()


@pytest.mark.skipif(__import__("sys").version_info < (3, 12), reason="PEP 701 parser")
@pytest.mark.parametrize(
    "floor,metadata,severity",
    [
        (None, None, "info"),
        ("3.9", None, "medium"),
        ("3.12", None, "info"),
        (None, ">=3.9", "medium"),
        (None, ">=3.12", "info"),
        ("3.12", ">=3.10", "medium"),
    ],
)
def test_preflight_pep701(tmp_path, floor, metadata, severity):
    from pyobfus.core.preflight import PreflightChecker

    source = tmp_path / "app.py"
    source.write_text("d = {'k': 1}\nprint(f'{d['k']}')\n")
    if metadata:
        (tmp_path / "pyproject.toml").write_text(f'[project]\nrequires-python = "{metadata}"\n')
    report = PreflightChecker(target_python_min=floor).check_path(source)
    risks = [risk for risk in report.risks if "output requires Python >= 3.12" in risk.message]
    assert len(risks) == 1
    assert risks[0].severity == severity
    assert report.exit_code() == 0


@pytest.mark.skipif(__import__("sys").version_info < (3, 12), reason="PEP 701 tokenizer")
@pytest.mark.parametrize("mode", ["file", "directory", "legacy"])
@pytest.mark.parametrize("attributes", [False, True])
def test_guard_cli_json(tmp_path, monkeypatch, mode, attributes):
    import json
    from click.testing import CliRunner
    from pyobfus.cli import main
    from pyobfus.core.generator import CodeGenerator

    directory = mode != "file"
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("print('safe')\n")
    out = tmp_path / ("out" if directory else "out.py")
    monkeypatch.setattr(CodeGenerator, "generate", lambda tree: "print(f'{dict(k=1)['k']}')")
    flags = [] if attributes else ["--no-crossfile-module-attributes"]
    if mode == "legacy":
        flags.append("--no-cross-file")
    result = CliRunner().invoke(
        main,
        [
            str(src if directory else src / "app.py"),
            "-o",
            str(out),
            "--no-config",
            "--json",
            "--jobs",
            "1",
            *flags,
        ],
    )
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["error_type"] == "FStringCompatibilityError", payload
    assert "app.py:5:" in payload["message"], payload
    assert not (out / "app.py" if directory else out).exists()


@pytest.mark.skipif(__import__("sys").version_info < (3, 12), reason="PEP 701 tokenizer")
def test_guard_cached_output(tmp_path, monkeypatch):
    import json
    from click.testing import CliRunner
    from pyobfus.cli import main
    from pyobfus.core.cache import BuildCache

    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("print('safe')\n")
    out = tmp_path / "out"
    out.mkdir()
    (out / "app.py").write_text("print(f'{dict(k=1)['k']}')\n")
    monkeypatch.setattr(BuildCache, "can_reuse", lambda *args: (True, "fixture", []))
    result = CliRunner().invoke(
        main,
        [
            str(src),
            "-o",
            str(out),
            "--no-config",
            "--json",
            "--incremental",
        ],
    )
    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["error_type"] == "FStringCompatibilityError"
