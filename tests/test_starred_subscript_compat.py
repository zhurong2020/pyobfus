"""Starred subscript tuples must retain the Python 3.9 grammar."""

import ast
import os
import shutil
import subprocess
import sys

import pytest

from pyobfus.core.unparse import unparse

EXPRESSIONS = [
    "a[(1, *xs)]",
    "a[(*xs,)]",
    "a[(1, *xs, *xs)]",
    "a[(a[(*xs,)], *xs)]",
    'f"{a[(1, *xs)]}"',
]
PROGRAM = "class Capture:\n    def __getitem__(self, key):\n        return key\na = Capture()\nxs = (2, 3)\n"


@pytest.mark.parametrize("expr", EXPRESSIONS)
def test_parentheses_and_310_execution(expr):
    source = PROGRAM + f"print({expr})\n"
    output = unparse(ast.parse(source))
    ast.parse(output, feature_version=(3, 9))
    py = shutil.which("/usr/bin/python3.10")
    if not py:
        pytest.skip("Python 3.10 is unavailable")
    expected = subprocess.run([py, "-c", source], capture_output=True, text=True, check=True)
    actual = subprocess.run([py, "-c", output], capture_output=True, text=True, check=True)
    assert actual.stdout.splitlines() == expected.stdout.splitlines()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="PEP 646 parser")
def test_pep646_equivalent():
    source = PROGRAM + "print(a[1, *xs])\n"
    output = unparse(ast.parse(source))
    assert "a[(1, *xs)]" in output
    assert ast.dump(ast.parse(source)) == ast.dump(ast.parse(output))
    runs = [
        subprocess.run([sys.executable, "-c", s], capture_output=True, text=True, check=True)
        for s in (source, output)
    ]
    assert runs[0].stdout.splitlines() == runs[1].stdout.splitlines()


@pytest.mark.parametrize("mode", ["file", "directory", "legacy"])
def test_artifact(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = tmp_path / "src"
    src.mkdir()
    source = PROGRAM + "\n".join(f"print({e})" for e in EXPRESSIONS)
    app = src / "app.py"
    app.write_text(source)
    directory = mode != "file"
    out = tmp_path / ("out" if directory else "out.py")
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(src if directory else app),
            "-o",
            str(out),
            "--no-config",
            "--json",
            "--verify-names",
            *(["--no-cross-file"] if mode == "legacy" else []),
        ],
        env=dict(os.environ),
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (build.stdout, build.stderr)
    artifact = out / "app.py" if directory else out
    ast.parse(artifact.read_text(), feature_version=(3, 9))
    expected = subprocess.run(
        [sys.executable, str(app)], capture_output=True, text=True, check=True
    )
    for py in (sys.executable, shutil.which("/usr/bin/python3.10")):
        if py:
            actual = subprocess.run([py, str(artifact)], capture_output=True, text=True, check=True)
            assert actual.stdout.splitlines() == expected.stdout.splitlines()


def test_guard():
    from pyobfus.core.fstring_compat import ensure_fstring_compatibility
    from pyobfus.exceptions import FStringCompatibilityError

    with pytest.raises(FStringCompatibilityError, match=r"fixture.py:2:.*Python >= 3.11"):
        ensure_fstring_compatibility("a[(x, *y)]", "x = 1\na[x, *y]", "fixture.py")


@pytest.mark.parametrize(
    "expr", ["a[x, y]", "a[(x,)]", "a[()]", "a[x:y]", "[x, *y]", "'a[x, *y]'", "a[((x, *y), z)]"]
)
def test_unrelated_native_bytes(expr):
    from pyobfus.core.unparse import SubscriptUnparser

    tree = ast.parse(expr)
    assert SubscriptUnparser().visit(tree) == ast.unparse(tree)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="PEP 646 parser")
@pytest.mark.parametrize(
    "expr,bare",
    [
        ("a[(x, *y)]", False),
        ("a[((x, *y))]", False),
        ("a[x, *y]", True),
        ("a[(x), *(y)]", True),
        ("a[(x, *y), z]", False),
        ("a[(*y,)]", False),
        ("a[*y]", True),
        ("a[\n (x), # comment\n *y\n]", True),
        ("a['é', *y]", True),
    ],
)
def test_detector(expr, bare):
    from pyobfus.core.fstring_compat import pep646_locations

    assert bool(pep646_locations(expr)) == bare


@pytest.mark.parametrize("mode", ["file", "directory", "legacy", "cached"])
def test_guard_cli_json(tmp_path, monkeypatch, mode):
    import json
    from click.testing import CliRunner
    from pyobfus.cli import main
    from pyobfus.core.cache import BuildCache
    from pyobfus.core.generator import CodeGenerator

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("print('safe')\n")
    out = tmp_path / ("out.py" if mode == "file" else "out")
    bad = "print(tuple[1, *[2]])"
    monkeypatch.setattr(CodeGenerator, "generate", lambda tree: bad)
    flags = []
    if mode == "legacy":
        flags.append("--no-cross-file")
    if mode == "cached":
        out.mkdir()
        (out / "app.py").write_text(bad)
        monkeypatch.setattr(BuildCache, "can_reuse", lambda *args: (True, "fixture", []))
        flags.append("--incremental")
    result = CliRunner().invoke(
        main,
        [
            str(src / "app.py" if mode == "file" else src),
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
    assert "app.py:" in payload["message"] and "Python >= 3.11" in payload["message"]
    if mode != "cached":
        assert not (out if mode == "file" else out / "app.py").exists()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="PEP 646 parser")
def test_mixed_slice_remains_valid():
    from pyobfus.core.fstring_compat import ensure_fstring_compatibility

    source = PROGRAM + "print(a[1:2, *xs])\n"
    output = unparse(ast.parse(source))
    assert ast.dump(ast.parse(output)) == ast.dump(ast.parse(source))
    assert "a[1:2, *xs]" in output
    ensure_fstring_compatibility(source, output, "mixed.py")
    runs = [
        subprocess.run([sys.executable, "-c", s], capture_output=True, text=True, check=True)
        for s in (source, output)
    ]
    assert runs[0].stdout.splitlines() == runs[1].stdout.splitlines()


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 701 parser")
def test_pep701_source_does_not_bypass_subscript_guard():
    from pyobfus.core.fstring_compat import ensure_fstring_compatibility
    from pyobfus.exceptions import FStringCompatibilityError

    with pytest.raises(FStringCompatibilityError, match="generated subscript"):
        ensure_fstring_compatibility("f'{d['k']}'", "a[x, *y]", "fixture.py")
