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
import shutil
import subprocess
import sys

import pytest

from pyobfus.core.mapping import ObfuscationMapping

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
MULTIMODULE = Path(__file__).resolve().parent / "packaging" / "multimodule"
# Names the directory build renames; none may survive into a packaged artifact.
MULTIMODULE_NAMES = (
    "quote_order",
    "lookup_unit_price",
    "DiscountPolicy",
    "TIER_RATES",
    "UNIT_PRICES",
)
MULTIMODULE_TIERS = ("free", "pro", "enterprise")


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


def _obfuscate_project(work):
    """Copy the multi-module fixture into ``work`` and obfuscate the directory."""
    source = work / "src"
    shutil.copytree(MULTIMODULE, source, ignore=shutil.ignore_patterns("__pycache__", "README.md"))
    output = work / "obfuscated"
    mapping_path = work / "private" / "mapping.json"
    _run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(source),
            "-o",
            str(output),
            "--save-mapping",
            str(mapping_path),
            "--verify-syntax",
        ],
        cwd=work,
    )
    mapping = ObfuscationMapping.load(mapping_path)
    for name in MULTIMODULE_NAMES:
        _mapped(mapping, name)
    return source, output, mapping


def _check_multimodule_artifact(executable, source, output, mapping, work, env=None):
    """Run the packaged project with its source hidden, compare it with the
    original, and reverse-map a traceback that crosses three modules."""
    output.rename(work / "obfuscated.hidden")
    for tier in MULTIMODULE_TIERS:
        original = _run([sys.executable, "-B", "main.py", tier], cwd=source)
        packaged = _run([str(executable), tier], cwd=work, env=env)
        assert packaged.stdout == original.stdout
    crash = _run([str(executable), "bogus_tier"], cwd=work, env=env, expected_code=1)
    assert "Unknown pricing tier: bogus_tier" in crash.stderr
    quote = _mapped(mapping, "quote_order")
    assert quote in crash.stderr
    restored = _unmap_cli(crash.stderr, work)
    assert "quote_order" in restored
    assert "quote_order" in mapping.unmap_text(crash.stderr)
    assert mapping.unmatched_names(crash.stderr) == []


def test_multimodule_pyinstaller_onefile(tmp_path):
    _require_tool("PyInstaller")
    source, output, mapping = _obfuscate_project(tmp_path)
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
            "storefront_app",
            "--distpath",
            str(tmp_path / "dist"),
            "--workpath",
            str(tmp_path / "build"),
            "--specpath",
            str(tmp_path / "spec"),
            str(output / "main.py"),
        ],
        cwd=tmp_path,
        env=env,
    )
    executable = tmp_path / "dist" / "storefront_app"
    assert executable.is_file()
    assert not list(executable.parent.rglob("*.json"))
    # Every module of the package must be frozen from the obfuscated tree.
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(executable))
    assert not [entry for entry in archive.toc if "mapping" in entry.lower()]
    pyz = archive.open_embedded_archive("PYZ.pyz")
    modules = [
        "storefront",
        "storefront.catalog",
        "storefront.checkout",
        "storefront.rules",
        "storefront.rules.discounts",
    ]
    assert set(modules) <= set(pyz.toc)
    names = _code_names(marshal.loads(archive.extract("main")))
    for module in modules:
        names |= _code_names(pyz.extract(module))
    assert not names & set(MULTIMODULE_NAMES)
    _check_multimodule_artifact(executable, source, output, mapping, tmp_path, env=env)


def test_multimodule_nuitka_standalone(tmp_path):
    _require_tool("nuitka")
    if shutil.which("patchelf") is None:
        pytest.skip("Nuitka standalone on Linux needs patchelf on PATH")
    source, output, mapping = _obfuscate_project(tmp_path)
    build = tmp_path / "nuitka"
    _run(
        [
            sys.executable,
            "-m",
            "nuitka",
            "--mode=standalone",
            "main.py",
            f"--output-dir={build}",
            "--remove-output",
            "--jobs=2",
        ],
        cwd=output,
    )
    dist = build / "main.dist"
    executable = dist / "main.bin"
    assert executable.is_file()
    # Compiled into the binary: no Python source, no mapping, no original names.
    assert not list(dist.rglob("*.py"))
    assert not list(dist.rglob("*mapping*.json"))
    binary = executable.read_bytes()
    for name in MULTIMODULE_NAMES:
        assert name.encode() not in binary, name
    _check_multimodule_artifact(executable, source, output, mapping, tmp_path)
