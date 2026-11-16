"""Build and execute maintained examples using optional packaging toolchains.

These are Linux/CPython 3.12 examples, not guarantees for arbitrary projects,
platforms, compiler modes or third-party dependencies. Normal dev installs skip
missing toolchains; packaging-lane.yml installs the pinned stack.
"""

import ast
import base64
import importlib.util
import json
import marshal
import os
from pathlib import Path
import re
import secrets
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


def _assert_no_material(data, materials):
    # Do not let pytest's assertion rewriting print application keys on failure.
    if any(material in data for material in materials):
        pytest.fail("Private key material or original encrypted-function source leaked")


class _ReferenceSecrets:
    """Default object repr keeps pytest fixture diagnostics free of keys."""

    def __init__(self):
        raw = secrets.token_bytes(32)
        self.key = base64.b64encode(raw).decode("ascii")
        self.material = (raw, self.key.encode(), repr(raw).encode())


def _run(command, *, cwd, env=None, expected_code=0, secret_material=()):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=600)
    _assert_no_material((result.stdout + result.stderr).encode(), secret_material)
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


def _unmap_cli(trace, work, *, details=False):
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
    return payload if details else payload["unmapped_trace"]


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


@pytest.mark.parametrize("include_mapping", [False, True])
def test_pyinstaller_onefile_delivery_inspection(tmp_path, include_mapping):
    """Inspect real onefile outputs without executing them or opening their PYZ."""
    _require_tool("PyInstaller")
    from pyobfus.core.delivery_check import FROZEN_UNINSPECTED, MAPPING_FILE, check_delivery

    source = tmp_path / "tiny.py"
    source.write_text("print('delivery canary')\n", encoding="utf-8")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name",
        "tiny",
        "--distpath",
        str(tmp_path / "dist"),
        "--workpath",
        str(tmp_path / "build"),
        "--specpath",
        str(tmp_path / "spec"),
    ]
    if include_mapping:
        mapping = tmp_path / "mapping.json"
        mapping.write_text(json.dumps({"pyobfus_version": "0.14.0", "global": {}}))
        command.extend(["--add-data", f"{mapping}{os.pathsep}."])
    else:
        command.extend(
            [
                "--runtime-tmpdir",
                "../pyobfus-delivery-tmp",
                "--python-option",
                "W ignore::DeprecationWarning",
                "--python-option",
                "W ignore::DeprecationWarning",
            ]
        )
    command.append(str(source))
    _run(
        command,
        cwd=tmp_path,
        env={**os.environ, "PYINSTALLER_CONFIG_DIR": str(tmp_path / "cache")},
    )
    result = check_delivery(tmp_path / "dist" / "tiny")
    inspection = result["inspection"]["frozen_executables"]
    assert inspection["format"] == "pyinstaller-carchive"
    assert inspection["inspected"] == 1
    assert inspection["unknown_members"] >= 1
    codes = sorted(finding["code"] for finding in result["findings"])
    assert result["status"] == ("fail" if include_mapping else "warn")
    assert codes == sorted(
        [FROZEN_UNINSPECTED, MAPPING_FILE] if include_mapping else [FROZEN_UNINSPECTED]
    )


@pytest.fixture
def protected_reference(tmp_path, monkeypatch):
    """README Community build, with all evidence and state outside the input."""
    _require_tool("PyInstaller")
    # Keep the caller's PYTHONPATH so CLI subprocesses exercise this checkout
    # when the venv's editable install points at a different worktree.
    for name in ("PYTHONHOME", "PYOBFUS_LICENSE_KEY"):
        monkeypatch.delenv(name, raising=False)
    source = tmp_path / "source"
    shutil.copytree(
        EXAMPLES / "delivery_reference", source, ignore=shutil.ignore_patterns("__pycache__")
    )
    baseline = {}
    for args in (("pro",), (), ("bogus_tier",)):
        baseline[args] = _run(
            [sys.executable, "-B", "main.py", *args],
            cwd=source,
            expected_code=1 if args == ("bogus_tier",) else 0,
        )
    assert baseline[("pro",)].stdout.splitlines() == ["pricing-v1", "pro: 65.88"]
    assert baseline[()].stdout == baseline[("pro",)].stdout
    assert baseline[("bogus_tier",)].stderr.splitlines()[-1] == (
        "ValueError: Unknown pricing tier: bogus_tier"
    )
    output = tmp_path / "protected"
    private = tmp_path / "private"
    private.mkdir()
    _run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(source),
            "-o",
            str(output),
            "--config",
            str(source / "pyobfus.yaml"),
            "--save-mapping",
            str(private / "mapping.json"),
            "--build-report",
            str(private / "build.json"),
            # Evidence only: needed to recognise a byte-identical source leak.
            "--provenance-manifest",
            str(private / "provenance.json"),
            "--verify-syntax",
            "--jobs",
            "1",
            "--json",
        ],
        cwd=tmp_path,
    )
    (output / "storefront/data").mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "storefront/data/label.txt", output / "storefront/data/label.txt")
    for args, original in baseline.items():
        protected = _run(
            [sys.executable, "-B", "main.py", *args],
            cwd=output,
            expected_code=original.returncode,
        )
        assert protected.stdout == original.stdout
        if original.returncode:
            assert protected.stderr.splitlines()[-1] == original.stderr.splitlines()[-1]
    import pyobfus

    cli_import = _run(
        [sys.executable, "-c", "import pyobfus; print(pyobfus.__file__)"], cwd=tmp_path
    ).stdout.strip()
    assert Path(cli_import).resolve() == Path(pyobfus.__file__).resolve()
    (private / "baseline.json").write_text(
        json.dumps(
            {
                "pytest_pyobfus_file": pyobfus.__file__,
                "cli_pyobfus_file": cli_import,
                "runs": {
                    " ".join(args)
                    or "default": {
                        "stdout": run.stdout,
                        "stderr": run.stderr,
                        "exit_code": run.returncode,
                    }
                    for args, run in baseline.items()
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return source, output, ObfuscationMapping.load(private / "mapping.json"), baseline


def _build_reference_pyinstaller(work, output, mode, extra_data=(), *, secret_material=()):
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--{mode}",
        "--clean",
        "--noconfirm",
        "--name",
        "delivery_reference",
        "--distpath",
        str(work / "dist"),
        "--workpath",
        str(work / "build"),
        "--specpath",
        str(work / "spec"),
        "--hidden-import",
        "storefront.plugins.standard",
        "--hidden-import",
        "storefront.data",
        "--add-data",
        f"{output / 'storefront/data/label.txt'}{os.pathsep}storefront/data",
    ]
    for data in extra_data:
        command.extend(["--add-data", f"{data}{os.pathsep}."])
    command.append(str(output / "main.py"))
    _run(
        command,
        cwd=work,
        env={**os.environ, "PYINSTALLER_CONFIG_DIR": str(work / "cache")},
        secret_material=secret_material,
    )
    return work / "dist" / "delivery_reference"


def _reference_delivery(target, work, *, expected_code=0, label="delivery", provenance=True):
    """Compare the library result with the CLI JSON and its process exit code."""
    from pyobfus.core.delivery_check import check_delivery

    private = work / "private"
    result = check_delivery(
        target,
        build_report=private / "build.json",
        provenance_manifest=private / "provenance.json" if provenance else None,
    )
    evidence = ["--build-report", str(private / "build.json")]
    if provenance:
        evidence += ["--provenance-manifest", str(private / "provenance.json")]
    cli = _run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            "--check-delivery",
            str(target),
            *evidence,
            "--json",
        ],
        cwd=work,
        expected_code=expected_code,
    )
    assert json.loads(cli.stdout) == result
    (private / f"{label}.json").write_text(cli.stdout, encoding="utf-8")
    return result


@pytest.mark.parametrize("mode", ["onedir", "onefile"])
def test_delivery_reference_pyinstaller(tmp_path, protected_reference, mode):
    from PyInstaller.archive.readers import CArchiveReader

    from pyobfus.core.delivery_check import FROZEN_UNINSPECTED, MISSING_OUTPUT

    source, output, mapping, baseline = protected_reference
    dist = _build_reference_pyinstaller(tmp_path, output, mode)
    consumer = tmp_path / "consumer"
    if mode == "onedir":
        shutil.copytree(dist, consumer)
        executable = consumer / dist.name
        assert (consumer / "_internal" / "storefront/data/label.txt").is_file()
    else:
        consumer.mkdir()
        executable = consumer / dist.name
        shutil.copy2(dist, executable)
        assert list(consumer.iterdir()) == [executable]
    # Only dist output is copied. Remove the source/build paths before consumption.
    for directory in (source, output, tmp_path / "build"):
        directory.rename(directory.with_name(directory.name + ".hidden"))
    assert not list(consumer.rglob("*.py"))
    assert not list(consumer.rglob("*.json"))
    # Confirm that the uninspected code/archive members really include a PYZ;
    # merely reading its TOC entry does not inspect or unmarshal its contents.
    archive = CArchiveReader(str(executable))
    assert archive.toc["PYZ.pyz"][-1] == "z"
    env = {
        name: value
        for name, value in os.environ.items()
        if name not in {"PYTHONPATH", "PYTHONHOME", "PYOBFUS_LICENSE_KEY"}
    }
    for args, original in baseline.items():
        frozen = _run(
            [str(executable), *args], cwd=consumer, env=env, expected_code=original.returncode
        )
        assert frozen.stdout.splitlines() == original.stdout.splitlines()
        if not original.returncode:
            continue
        error = original.stderr.splitlines()[-1]
        assert error in frozen.stderr.splitlines()
        for name in ("render_order", "quote_order"):
            assert _mapped(mapping, name) in frozen.stderr
        restored = _unmap_cli(frozen.stderr, tmp_path)
        frames = re.compile(r'^\s*File "([^"]+)", line \d+, in (\S+)(?:  \[.*\])?$', re.MULTILINE)
        original_frames = [
            (Path(path).relative_to(source).as_posix(), function)
            for path, function in frames.findall(original.stderr)
        ]
        frozen_frames = frames.findall(frozen.stderr)
        restored_frames = frames.findall(restored)
        assert len(frozen_frames) == len(restored_frames) == len(original_frames)
        assert restored_frames == original_frames  # No extra, missing or fabricated frames.
        (tmp_path / "private" / "restored.txt").write_text(restored, encoding="utf-8")

    result = _reference_delivery(executable, tmp_path, label="executable-delivery")
    inspection = result["inspection"]["frozen_executables"]
    assert inspection["format"] == "pyinstaller-carchive"
    assert inspection["inspected"] == 1
    assert (
        inspection["members_total"] == inspection["members_checked"] + inspection["unknown_members"]
    )
    assert inspection["unknown_members"] > 0
    if mode == "onefile":
        assert inspection["members_checked"] > 0
    else:
        # onedir puts the resource and native dependencies in _internal; its
        # bootloader CArchive contains only uninspected code/archive members.
        assert inspection["members_checked"] == 0
    assert result["status"] == "warn"
    assert result["summary"]["high"] == 0
    assert {finding["code"] for finding in result["findings"]} == {FROZEN_UNINSPECTED}
    if mode == "onedir":
        # Directory scans inspect the bootloader's top-level CArchive members
        # too, while keeping its code and embedded PYZ explicitly unknown.
        directory = _reference_delivery(consumer, tmp_path, label="directory-delivery")
        assert directory["status"] == "warn"
        assert directory["summary"]["high"] == 0
        assert directory["inspection"]["frozen_executables"] == inspection
        assert {finding["code"] for finding in directory["findings"]} == {
            FROZEN_UNINSPECTED,
            MISSING_OUTPUT,
        }


@pytest.mark.parametrize("leak", ["mapping", "source", "private-key"])
def test_delivery_reference_pyinstaller_onefile_mutation(tmp_path, protected_reference, leak):
    from pyobfus.core.delivery_check import (
        FROZEN_UNINSPECTED,
        MAPPING_FILE,
        ORIGINAL_SOURCE,
        PRIVATE_KEY,
    )

    source, output, _, _ = protected_reference
    private = tmp_path / "private"
    if leak == "mapping":
        planted, code = private / "mapping.json", MAPPING_FILE
    elif leak == "source":
        planted, code = source / "storefront/catalog.py", ORIGINAL_SOURCE
    else:
        planted, code = private / "dummy.pem", PRIVATE_KEY
        # Intentionally invalid test data; never store a key-looking literal.
        marker = "-" * 5
        kind = "PRIVATE" + " KEY"
        planted.write_text(
            f"{marker}BEGIN {kind}{marker}\nobviously-fake-test-data\n"
            f"{marker}END {kind}{marker}\n",
            encoding="ascii",
        )
    executable = _build_reference_pyinstaller(tmp_path, output, "onefile", [planted])
    result = _reference_delivery(executable, tmp_path, expected_code=1)
    assert result["status"] == "fail"
    assert result["summary"]["high"] == 1
    assert [
        (finding["code"], finding["path"])
        for finding in result["findings"]
        if finding["severity"] == "high"
    ] == [(code, planted.name)]
    assert {finding["code"] for finding in result["findings"]} == {code, FROZEN_UNINSPECTED}


@pytest.fixture
def pro_reference(tmp_path, monkeypatch):
    """Local-only trial and application key; never inspect real user state."""
    _require_tool("PyInstaller")
    import pyobfus

    for name in ("PYTHONHOME", "PYOBFUS_LICENSE_KEY", "PYOBFUS_DELIVERY_REFERENCE_KEY"):
        monkeypatch.delenv(name, raising=False)
    home = Path(os.environ["HOME"])
    assert home == Path(os.environ["USERPROFILE"]) == tmp_path / "home"
    private = tmp_path / "private"
    private.mkdir()
    # Audit Python builders/CLIs without reading or stat'ing real trial/license
    # files. A state access outside this test fails before the filesystem call.
    guard = private / "guard"
    guard.mkdir()
    access_log = private / "state-access.jsonl"
    (guard / "sitecustomize.py").write_text(
        "import json, os, sys\n"
        f"root = {str(tmp_path)!r}\nlog = {str(access_log)!r}\n"
        "def audit(event, args):\n"
        "    if event not in ('open', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir'):\n"
        "        return\n"
        "    for arg in args[:2] if event == 'os.rename' else args[:1]:\n"
        "        if not isinstance(arg, (str, bytes)):\n"
        "            continue\n"
        "        path = os.path.abspath(os.fsdecode(arg))\n"
        "        if '.pyobfus' not in path.split(os.sep):\n"
        "            continue\n"
        "        allowed = os.path.commonpath((root, path)) == root\n"
        "        with open(log, 'a') as stream:\n"
        "            stream.write(json.dumps({'path': path, 'allowed': allowed}) + '\\n')\n"
        "        if not allowed:\n"
        "            raise RuntimeError('Test attempted to access non-isolated pyobfus state')\n"
        "sys.addaudithook(audit)\n",
        encoding="utf-8",
    )
    checkout = EXAMPLES.parent
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join((str(guard), str(checkout))))
    cli_import = _run(
        [sys.executable, "-c", "import pyobfus; print(pyobfus.__file__)"], cwd=tmp_path
    ).stdout.strip()
    assert Path(cli_import).resolve() == Path(pyobfus.__file__).resolve()
    trial = _run(
        [
            sys.executable,
            "-c",
            "from pyobfus.trial import start_trial; r=start_trial(); assert r['success'], r",
        ],
        cwd=tmp_path,
    )
    assert (home / ".pyobfus/trial.json").is_file()
    assert not list(tmp_path.rglob("license.json"))
    assert list(tmp_path.rglob("trial.json")) == [home / ".pyobfus/trial.json"]
    secret = _ReferenceSecrets()
    material = secret.material
    monkeypatch.setenv("PYOBFUS_DELIVERY_REFERENCE_KEY", secret.key)
    source = tmp_path / "source"
    shutil.copytree(
        EXAMPLES / "delivery_reference", source, ignore=shutil.ignore_patterns("__pycache__")
    )
    baseline = {
        args: _run(
            [sys.executable, "-B", "main.py", *args],
            cwd=source,
            expected_code=1 if args == ("bogus_tier",) else 0,
            secret_material=material,
        )
        for args in (("pro",), (), ("bogus_tier",))
    }
    assert baseline[("pro",)].stdout == baseline[()].stdout == "pricing-v1\npro: 65.88\n"
    assert baseline[("bogus_tier",)].stderr.splitlines()[-1] == (
        "ValueError: Unknown pricing tier: bogus_tier"
    )
    targets = {
        "storefront.checkout.quote_order": "storefront/checkout.py",
        "storefront.catalog.lookup_unit_price": "storefront/catalog.py",
    }
    rules = private / "opacity.toml"
    rules.write_text(
        "".join(f'[[rules]]\npattern="{name}"\nlayer="encrypted"\n' for name in targets),
        encoding="utf-8",
    )
    output = tmp_path / "protected"
    build = _run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(source),
            "-o",
            str(output),
            "--config",
            str(source / "pyobfus.yaml"),
            "--level",
            "pro",
            "--crossfile-opacity",
            "--opacity-config",
            str(rules),
            "--bind-key-env",
            "PYOBFUS_DELIVERY_REFERENCE_KEY",
            "--save-mapping",
            str(private / "mapping.json"),
            "--build-report",
            str(private / "build.json"),
            # crossfile-opacity intentionally does not support provenance.
            "--verify-syntax",
            "--jobs",
            "1",
            "--json",
        ],
        cwd=tmp_path,
        secret_material=material,
    )
    report = json.loads((private / "build.json").read_text())
    opacity = report["opacity"]
    assert opacity["mode"] == "crossfile_opacity"
    assert opacity["encrypted_targets"] == len(targets)
    assert report["transformations"]["encrypted_targets"] == len(targets)
    assert type(opacity["eligible_targets"]) is int
    assert opacity["eligible_targets"] >= len(targets)
    assert type(opacity["rejected_targets"]) is int
    assert isinstance(opacity["rejection_histogram"], dict)
    assert all(type(n) is int and n > 0 for n in opacity["rejection_histogram"].values())
    assert opacity["rejected_targets"] == sum(opacity["rejection_histogram"].values())
    mapping = ObfuscationMapping.load(private / "mapping.json")
    assert {
        (item["file"], item["binding"]["name"], item["final_name"])
        for item in mapping.opacity_plan["targets"]
    } == {
        (file, name.rsplit(".", 1)[1], _mapped(mapping, name.rsplit(".", 1)[1]))
        for name, file in targets.items()
    }
    assert {
        (path.split(":", 2)[-1].rstrip(">"), final, original)
        for path, names in mapping.encrypted_code.items()
        for final, original in names.items()
    } == {
        (file, _mapped(mapping, name.rsplit(".", 1)[1]), name.rsplit(".", 1)[1])
        for name, file in targets.items()
    }
    original_functions = []
    for name, file in targets.items():
        text = (source / file).read_text()
        node = next(
            n
            for n in ast.parse(text).body
            if isinstance(n, ast.FunctionDef) and n.name == name.rsplit(".", 1)[1]
        )
        original_functions.append(ast.get_source_segment(text, node).encode())
    secret.material = forbidden = (*material, *original_functions)
    for file in (*output.rglob("*"), *private.rglob("*.json")):
        if file.is_file():
            _assert_no_material(file.read_bytes(), forbidden)
    _assert_no_material((trial.stdout + trial.stderr).encode(), material)
    (private / "protect.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    (output / "storefront/data").mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "storefront/data/label.txt", output / "storefront/data/label.txt")
    for args, original in baseline.items():
        protected = _run(
            [sys.executable, "-B", "main.py", *args],
            cwd=output,
            expected_code=original.returncode,
            secret_material=material,
        )
        assert protected.stdout == original.stdout
        if original.returncode:
            assert protected.stderr.splitlines()[-1] == original.stderr.splitlines()[-1]
    evidence = {
        "pytest_pyobfus_file": pyobfus.__file__,
        "cli_pyobfus_file": cli_import,
        "opacity": opacity,
        "transformations": report["transformations"],
    }
    yield source, output, mapping, baseline, secret, evidence
    accesses = [json.loads(line) for line in access_log.read_text().splitlines()]
    assert accesses and all(item["allowed"] for item in accesses)
    assert all(Path(item["path"]).is_relative_to(home) for item in accesses)
    assert list(tmp_path.rglob("trial.json")) == [home / ".pyobfus/trial.json"]
    assert not list(tmp_path.rglob("license.json"))
    (private / "pro-evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")


@pytest.mark.parametrize("mode", ["onefile", "onedir"])
def test_delivery_reference_pro_pyinstaller(tmp_path, pro_reference, mode):
    from PyInstaller.archive.readers import CArchiveReader

    from pyobfus.core.delivery_check import (
        FROZEN_UNINSPECTED,
        L3_PARTIAL,
        L3_UNVERIFIED_FROZEN,
        MISSING_OUTPUT,
    )

    source, output, mapping, baseline, secret, evidence = pro_reference
    forbidden = secret.material
    dist = _build_reference_pyinstaller(tmp_path, output, mode, secret_material=forbidden)
    consumer = tmp_path / "consumer"
    if mode == "onedir":
        shutil.copytree(dist, consumer)
    else:
        consumer.mkdir()
        shutil.copy2(dist, consumer / dist.name)
    executable = consumer / dist.name
    for directory in (source, output, tmp_path / "build"):
        directory.rename(directory.with_name(directory.name + ".hidden"))
    assert not list(consumer.rglob("*.py"))
    # cryptography's PyInstaller hook legitimately ships SBOM JSON metadata.
    private_names = {
        "mapping.json",
        "build.json",
        "provenance.json",
        "trial.json",
        "license.json",
        ".pyobfus-release.json",
        "opacity.toml",
        "trace.txt",
    }
    assert not any(file.name in private_names for file in consumer.rglob("*"))
    for root in (tmp_path / "dist", consumer):
        for file in root.rglob("*"):
            if file.is_file():
                _assert_no_material(file.read_bytes(), forbidden)
    archive = CArchiveReader(str(executable))
    assert archive.toc["PYZ.pyz"][-1] == "z"
    assert not any("mapping" in name.lower() or "private" in name.lower() for name in archive.toc)
    for name, entry in archive.toc.items():
        if entry[-1] not in ("z", "o"):
            _assert_no_material(archive.extract(name), forbidden)
    # Consumers receive only the artifact and app-owned key input. No trial,
    # licence, PYTHONPATH, or builder environment is needed by the runtime.
    runtime_tmp = tmp_path / "runtime-tmp"
    runtime_tmp.mkdir()
    env = {
        "HOME": str(tmp_path / "home"),
        "USERPROFILE": str(tmp_path / "home"),
        "PATH": os.defpath,
        "TMPDIR": str(runtime_tmp),
        "PYOBFUS_DELIVERY_REFERENCE_KEY": secret.key,
    }
    runs = {}
    for args, original in baseline.items():
        frozen = _run(
            [str(executable), *args],
            cwd=consumer,
            env=env,
            expected_code=original.returncode,
            secret_material=forbidden,
        )
        assert frozen.stdout == original.stdout
        runs[" ".join(args) or "default"] = {
            "exit_code": frozen.returncode,
            "stdout": frozen.stdout,
        }
        if not original.returncode:
            continue
        assert original.stderr.splitlines()[-1] in frozen.stderr.splitlines()
        restored = _unmap_cli(frozen.stderr, tmp_path, details=True)
        frames = re.compile(r'^\s*File "([^"]+)", line (\d+), in (\S+)(?:  \[.*\])?$', re.MULTILINE)
        before = frames.findall(frozen.stderr)
        after = frames.findall(restored["unmapped_trace"])
        original_frames = [
            (Path(path).relative_to(source).as_posix(), line, name)
            for path, line, name in frames.findall(original.stderr)
        ]
        assert len(before) == len(after) == len(original_frames) + 1 == 5
        assert before[2][0::2] == ("pyobfus_runtime/opacity.py", "wrapper")
        encrypted_path, encrypted_line, encrypted_name = before[3]
        assert mapping.encrypted_code[encrypted_path][encrypted_name] == "quote_order"
        # All ordinary project frames exactly match the baseline. Preserve the
        # actual runtime frame and encrypted line/path; never invent source lines.
        assert after == [
            original_frames[0],
            original_frames[1],
            before[2],
            (encrypted_path, encrypted_line, "quote_order"),
            original_frames[3],
        ]
        assert before[0][0::2] == ("main.py", "<module>")
        assert before[1][0::2] == ("storefront/app.py", _mapped(mapping, "render_order"))
        assert before[4][0::2] == ("storefront/rules/discounts.py", "__init__")
        named = [f for f in restored["frames"] if f["status"] == "name_only"]
        assert len(named) == 1
        assert named[0]["name"] == "quote_order" and named[0]["original_line"] is None
        assert not any(f["status"] == "unmatched_l3" for f in restored["frames"])
        evidence["traceback"] = {"frozen": before, "restored": after, "frames": restored["frames"]}
        (tmp_path / "private/restored.txt").write_text(restored["unmapped_trace"], encoding="utf-8")
    wrong_raw = secrets.token_bytes(32)
    wrong = base64.b64encode(wrong_raw).decode("ascii")
    if wrong == secret.key:
        pytest.fail("Random wrong key unexpectedly matched")
    for label, value, error in (
        ("missing", None, "LicenseBindingError"),
        ("wrong", wrong, "OpacityRuntimeError"),
    ):
        negative_env = dict(env)
        negative_env.pop("PYOBFUS_DELIVERY_REFERENCE_KEY")
        if value is not None:
            negative_env["PYOBFUS_DELIVERY_REFERENCE_KEY"] = value
        negative = _run(
            [str(executable), "pro"],
            cwd=consumer,
            env=negative_env,
            expected_code=1,
            secret_material=(*forbidden, wrong_raw, wrong.encode()),
        )
        assert negative.stdout == ""
        assert error in negative.stderr
        runs[label] = {"exit_code": negative.returncode, "stdout": negative.stdout, "error": error}
    result = _reference_delivery(executable, tmp_path, provenance=False)
    assert result["status"] == "warn" and result["summary"]["high"] == 0
    codes = {finding["code"] for finding in result["findings"]}
    assert FROZEN_UNINSPECTED in codes
    inspection = result["inspection"]["frozen_executables"]
    assert inspection["inspected"] == 1 and inspection["unknown_members"] > 0
    if mode == "onedir":
        directory = _reference_delivery(
            consumer, tmp_path, provenance=False, label="directory-delivery"
        )
        assert directory["status"] == "warn" and directory["summary"]["high"] == 0
        codes = {f["code"] for f in directory["findings"]}
        # The L3 release lives inside frozen payloads: unverifiable, not a mismatch.
        assert L3_UNVERIFIED_FROZEN in codes and FROZEN_UNINSPECTED in codes
        assert codes <= {FROZEN_UNINSPECTED, MISSING_OUTPUT, L3_PARTIAL, L3_UNVERIFIED_FROZEN}
    evidence.update(
        {
            "mode": mode,
            "runs": runs,
            "inspection": inspection,
            "l3_coverage_findings": [f for f in result["findings"] if f["code"] == L3_PARTIAL],
        }
    )
