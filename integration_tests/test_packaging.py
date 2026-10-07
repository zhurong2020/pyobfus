"""Build and execute maintained examples using optional packaging toolchains.

These are Linux/CPython 3.12 examples, not guarantees for arbitrary projects,
platforms, compiler modes or third-party dependencies. Normal dev installs skip
missing toolchains; packaging-lane.yml installs the pinned stack.
"""

import importlib.util
import json
import marshal
import os
from pathlib import Path
import subprocess
import sys

import pytest

from pyobfus.core.mapping import ObfuscationMapping

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture(autouse=True)
def isolated_packaging_home(tmp_path, monkeypatch):
    """CLI subprocesses must never inspect the developer's pyobfus state."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))


def _run(command, *, cwd, env=None, expected_code=0):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=600)
    assert result.returncode == expected_code, result.stdout + result.stderr
    return result


def _require_tool(module):
    if sys.platform != "linux":
        pytest.skip("packaging lane currently covers Linux only")
    if importlib.util.find_spec(module) is None:
        pytest.skip(f"optional packaging toolchain {module} is not installed")


def _obfuscate(source, work):
    output = work / "obfuscated"
    output.mkdir()
    mapping_path = work / "private" / "mapping.json"
    _run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(source),
            "-o",
            str(output / source.name),
            "--save-mapping",
            str(mapping_path),
            "--verify-syntax",
        ],
        cwd=work,
    )
    return output, ObfuscationMapping.load(mapping_path)


def _mapped(mapping, name):
    matches = [
        obfuscated for obfuscated, (_, original) in mapping.global_map.items() if original == name
    ]
    assert len(matches) == 1, (name, matches)
    return matches[0]


def _code_names(code):
    names = {code.co_name, *code.co_names, *code.co_varnames}
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            names |= _code_names(const)
    return names


def _unmap_cli(trace, work):
    trace_path = work / "private" / "trace.txt"
    trace_path.write_text(trace, encoding="utf-8")
    result = _run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            "--unmap",
            "--trace",
            str(trace_path),
            "--mapping",
            str(work / "private" / "mapping.json"),
            "--json",
        ],
        cwd=work,
    )
    payload = json.loads(result.stdout)
    assert payload["version"] == 1
    assert payload["ai_hint"]
    assert payload["unmatched_names"] == []
    return payload["unmapped_trace"]


@pytest.mark.parametrize("compiler", ["cython", "nuitka"])
def test_compiled_module_behavior_and_reverse_traceback(tmp_path, compiler):
    _require_tool("Cython" if compiler == "cython" else "nuitka")
    source = EXAMPLES / "compiled_packaging" / "module.py"
    output, mapping = _obfuscate(source, tmp_path)
    if compiler == "cython":
        command = [sys.executable, "-m", "Cython.Build.Cythonize", "-i", "module.py"]
    else:
        command = [
            sys.executable,
            "-m",
            "nuitka",
            "--module",
            "module.py",
            "--no-pyi-file",
            "--remove-output",
            "--jobs=2",
        ]
    _run(command, cwd=output)
    binaries = list(output.glob("module*.so"))
    assert len(binaries) == 1
    assert not list(output.glob("*.pyi"))
    assert not list(output.rglob("*mapping*.json"))
    binary = binaries[0].read_bytes()
    for name in (b"proprietary_transform", b"ConfidentialEngine"):
        assert name not in binary

    # Hide the generated Python source, so import must load the native module.
    (output / "module.py").rename(output / "module.py.hidden")
    function = _mapped(mapping, "proprietary_transform")
    engine = _mapped(mapping, "ConfidentialEngine")
    method = _mapped(mapping, "run")
    # Nuitka deliberately reports the source path in __file__/__spec__.origin.
    native_check = (
        "assert module.__compiled__.extension_filename.endswith('.so')\n"
        if compiler == "nuitka"
        else "assert module.__spec__.origin.endswith('.so'), module.__spec__\n"
    )
    driver = (
        "import json, module, traceback\n"
        + native_check
        + f"print(json.dumps([module.{function}(2), module.{engine}().{method}('demo')]))\n"
        "try:\n"
        f"    module.{function}(None)\n"
        "except TypeError:\n"
        "    traceback.print_exc()\n"
        "else:\n"
        "    raise AssertionError('expected TypeError')\n"
    )
    result = _run([sys.executable, "-c", driver], cwd=output)
    original = _run(
        [
            sys.executable,
            "-c",
            "import json, module; print(json.dumps([module.proprietary_transform(2), "
            "module.ConfidentialEngine().run('demo')]))",
        ],
        cwd=source.parent,
    )
    assert json.loads(result.stdout) == json.loads(original.stdout)
    assert function in result.stderr
    assert "proprietary_transform" in mapping.unmap_text(result.stderr)
    assert "proprietary_transform" in _unmap_cli(result.stderr, tmp_path)
    assert mapping.unmatched_names(result.stderr) == []


def test_pyinstaller_onefile_behavior_and_reverse_traceback(tmp_path):
    _require_tool("PyInstaller")
    source = EXAMPLES / "pyinstaller" / "app.py"
    output, mapping = _obfuscate(source, tmp_path)
    # Keep PyInstaller's cache and build intermediates inside this test too.
    env = {**os.environ, "PYINSTALLER_CONFIG_DIR": str(tmp_path / "cache")}
    _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--clean",
            "--noconfirm",
            "--name",
            "pricing",
            "--distpath",
            str(tmp_path / "dist"),
            "--workpath",
            str(tmp_path / "build"),
            "--specpath",
            str(tmp_path / "spec"),
            str(output / "app.py"),
        ],
        cwd=tmp_path,
        env=env,
    )
    executable = tmp_path / "dist" / "pricing"
    assert executable.is_file()
    assert not list(executable.parent.rglob("*.json"))
    # Inspect the bundle itself: no mapping entry, and the frozen entry script
    # carries obfuscated identifiers rather than the original function name.
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(executable))
    assert not [entry for entry in archive.toc if "mapping" in entry.lower()]
    assert "apply_discount" not in _code_names(marshal.loads(archive.extract("app")))
    # The frozen artifact must run after its obfuscated source is removed.
    (output / "app.py").rename(output / "app.py.hidden")
    for tier in ("free", "pro", "enterprise"):
        original = _run([sys.executable, str(source), tier], cwd=tmp_path)
        bundled = _run([str(executable), tier], cwd=tmp_path, env=env)
        assert bundled.stdout == original.stdout
    crash = _run([str(executable), "bogus_tier"], cwd=tmp_path, env=env, expected_code=1)
    function = _mapped(mapping, "apply_discount")
    assert function in crash.stderr
    assert "apply_discount" in mapping.unmap_text(crash.stderr)
    assert "apply_discount" in _unmap_cli(crash.stderr, tmp_path)
    assert "Unknown pricing tier: bogus_tier" in crash.stderr
    assert mapping.unmatched_names(crash.stderr) == []
