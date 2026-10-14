"""Run actual CLI artifacts for lexical import collisions (defect I)."""

import os
import subprocess
import sys

import pytest

CORE = """def helper(value):
    return value + 1
def scale(value):
    return value * 10
def decorate(fn):
    return fn
"""
PREFIX = "from pkg.core import helper\n"
CASES = {
    "control": PREFIX
    + "def local():\n    from pkg.core import scale as other\n    return other(2)\nprint(helper(3), local())\n",
    "function": PREFIX
    + "def local():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(3), local())\n",
    "reverse": "def local():\n    from pkg.core import scale as helper\n    return helper(2)\n"
    + PREFIX
    + "print(helper(3), local())\n",
    "nested": PREFIX
    + "def outer():\n    def local():\n        from pkg.core import scale as helper\n        return helper(2)\n    return local()\nprint(helper(3), outer())\n",
    "async": "import asyncio\n"
    + PREFIX
    + "async def local():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(3), asyncio.run(local()))\n",
    "unaliased": "def local():\n    from pkg.core import helper\n    return helper(3)\nprint(local())\n",
    "default": PREFIX
    + "def local(value=helper(3)):\n    from pkg.core import scale as helper\n    return value, helper(2)\nprint(helper(3), local())\n",
    "decorator": "from pkg.core import decorate as helper\n@helper\ndef local():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(local())\n",
    "class": PREFIX
    + "class C:\n    from pkg.core import scale as helper\n    value = helper(2)\n    def method(self):\n        return helper(3)\nprint(helper(3), C.value, C().method())\n",
    "global": PREFIX + "def local():\n    global helper\n    return helper(3)\nprint(local())\n",
    "nonlocal": PREFIX
    + "def outer():\n    from pkg.core import scale as helper\n    def inner():\n        nonlocal helper\n        return helper(2)\n    return inner()\nprint(helper(3), outer())\n",
    "comprehension": PREFIX
    + "def local():\n    from pkg.core import scale as helper\n    return [helper(i) for i in range(3)], [helper for helper in range(3)]\nprint(helper(3), local(), [helper(i) for i in range(3)])\n",
    "parameter": PREFIX
    + "def local(helper):\n    return helper(2)\nprint(helper(3), local(lambda x: x*10))\n",
    "module-alias": PREFIX
    + "def local():\n    import pkg.core as helper\n    return helper.scale(2)\nprint(helper(3), local())\n",
    "lambda": PREFIX
    + "print((lambda helper=helper: helper(3))(), (lambda helper: helper(2))(lambda x: x*10))\n",
    "relative": PREFIX
    + "def local():\n    from .core import scale as helper\n    return helper(2)\nprint(helper(3), local())\n",
    "mixed-import": "from pkg.core import helper, scale as action\nprint(helper(3), action(2))\n",
    "module-rebind": PREFIX + "import math as helper\nprint(helper.floor(3.2))\n",
    "exec": PREFIX
    + "def local():\n    from pkg.core import scale as helper\n    exec('value = 5')\n    return helper(2)\nprint(helper(3), local())\n",
    "locals": PREFIX
    + "def local():\n    from pkg.core import helper\n    return locals()['helper'](3)\nprint(helper(3), local())\n",
    "global-import": PREFIX
    + "def local():\n    global helper\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(3), local(), helper(3))\n",
    "annotation": PREFIX
    + "def local(value: helper = helper(3)) -> helper:\n    from pkg.core import scale as helper\n    return value, helper(2)\nprint(local())\n",
    "walrus": PREFIX
    + "def local():\n    values = [helper := i for i in range(3)]\n    return values, helper\nprint(helper(3), local())\n",
    "nonlocal-unaliased": PREFIX
    + "def outer():\n    from pkg.core import helper\n    def inner():\n        nonlocal helper\n        return helper(2)\n    return inner()\nprint(helper(3), outer())\n",
    "module-assignment": PREFIX + "helper = lambda value: value*10\nprint(helper(3))\n",
    "del": PREFIX
    + "def local():\n    try:\n        del helper\n    except UnboundLocalError:\n        return 'unbound'\nprint(helper(3), local())\n",
    "duplicate-name": "from pkg.core import helper, helper as again\n"
    + "def local():\n    from pkg.core import scale as again\n    return again(2)\nprint(helper(3), again(3), local())\n",
    "module-del": PREFIX + "print(helper(3))\ndel helper\nprint('helper' in globals())\n",
    "module-globals": PREFIX
    + "def names():\n    return sorted(k for k in globals() if not k.startswith('_'))\n"
    + "def local():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(3), local(), len(names()))\n",
    "pep695-function": PREFIX
    + "def local[T](value: T) -> T:\n    from pkg.core import scale as helper\n    return helper(value)\n"
    + "def plain[T](value: T) -> T:\n    return helper(value)\nprint(local(2), plain(2))\n",
    "pep695-class": PREFIX + "class Box[T]:\n    value = helper(1)\nprint(Box.value)\n",
}

# PEP 695 syntax: the source itself only runs on Python 3.12+.
NEEDS_312 = {"pep695-function", "pep695-class"}
# Collision-free module bindings keep the main-branch rewriting: `del` and a
# read of globals() alone must not fall back to the original spelling.
OBFUSCATED_IMPORT = {"module-del", "module-globals"}


@pytest.mark.parametrize("cross_file", [True, False])
@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("local_names", [True, False])
@pytest.mark.parametrize("verify", [True, False])
def test_scoped_import_artifact(tmp_path, case, local_names, verify, cross_file):
    if case in NEEDS_312 and sys.version_info < (3, 12):
        pytest.skip("PEP 695 syntax requires Python 3.12+")
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg/__init__.py").write_text("")
    (src / "pkg/core.py").write_text(CORE)
    relative = "pkg/app.py" if case == "relative" else "app.py"
    (src / relative).write_text(CASES[case])
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))

    def run(args, cwd):
        return subprocess.run(
            [sys.executable, *map(str, args)], cwd=cwd, env=env, capture_output=True, timeout=60
        )

    entry = ["-m", "pkg.app"] if case == "relative" else ["app.py"]
    original = run(entry, src)
    assert original.returncode == 0, original.stderr
    out = tmp_path / "out"
    flags = [] if local_names else ["--no-crossfile-local-names"]
    if verify:
        flags.append("--verify-names")
    config_flags = ["--no-config"]
    if not cross_file:
        # Independent per-file builds require public dependency names to be
        # preserved: this mode deliberately performs no import synchronization.
        config = tmp_path / "config.yaml"
        config.write_text("obfuscation:\n  exclude_names: [helper, scale, decorate]\n")
        config_flags = ["--config", config]
        flags.append("--no-cross-file")
    built = run(["-m", "pyobfus", src, "-o", out, *config_flags, *flags], None)
    assert built.returncode == 0, built.stdout + built.stderr
    actual = run(entry, out)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == original.stdout
    if cross_file and case in OBFUSCATED_IMPORT:
        emitted = (out / relative).read_text().splitlines()
        module_imports = [line for line in emitted if line.startswith("from pkg.core import")]
        assert module_imports and all(" as " not in line for line in module_imports), emitted


@pytest.mark.parametrize("local_names", [True, False])
def test_dynamic_module_rebinding_requires_preservation(tmp_path, local_names):
    """Reject an unsafe dynamic binding; execute its precise preservation fallback."""
    source = tmp_path / "src"
    (source / "pkg").mkdir(parents=True)
    (source / "pkg/__init__.py").write_text("")
    (source / "pkg/core.py").write_text(CORE)
    (source / "app.py").write_text(
        PREFIX + "helper = lambda value: value * 10\n"
        "exec('helper = lambda value: value * 100')\nprint(helper(3))\n"
    )
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))

    def run(args, cwd=None):
        return subprocess.run(
            [sys.executable, *map(str, args)], cwd=cwd, env=env, capture_output=True, timeout=60
        )

    original = run(["app.py"], source)
    assert original.returncode == 0, original.stderr
    output = tmp_path / "out"
    flags = [] if local_names else ["--no-crossfile-local-names"]
    built = run(["-m", "pyobfus", source, "-o", output, "--no-config", *flags])
    assert built.returncode == 1
    assert b"Cannot safely synchronize dynamic module import binding" in built.stdout + built.stderr
    assert b"exclude_names" in built.stdout + built.stderr
    config = tmp_path / "config.yaml"
    config.write_text("obfuscation:\n  exclude_names: [helper]\n")
    rebuilt = run(
        ["-m", "pyobfus", source, "-o", output, "--config", config, "--verify-names", *flags]
    )
    assert rebuilt.returncode == 0, rebuilt.stdout + rebuilt.stderr
    actual = run(["app.py"], output)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == original.stdout == b"300\n"
