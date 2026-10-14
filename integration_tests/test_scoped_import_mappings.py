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
    assert (
        actual.stdout.replace(b"\r\n", b"\n") == original.stdout.replace(b"\r\n", b"\n") == b"300\n"
    )


# Independent round-two review: execute each artifact, including expected failures.
REVIEW_CASES = {
    "generic_default_lambda": {
        "app": "from pkg.core import helper\ndef g[T](x=lambda: helper(1)):\n    return x()\nprint(g())\n"
    },
    "type_alias_genexpr": {
        "app": "from pkg.core import helper\ntype A = tuple(x for x in ())\nprint(helper(1), A.__name__)\n"
    },
    "type_alias_lambda": {
        "app": "from pkg.core import helper\ntype A = (lambda: helper(1))\nprint(A.__value__())\n"
    },
    "generic_realistic_key": {
        "app": "from pkg.core import helper\ndef first[T](items: list[T], key=lambda x: x) -> T:\n    return min(items, key=key)\nprint(first([3, 1, 2]), helper(1))\n"
    },
    "generic_kwdefault_lambda": {
        "app": "from pkg.core import helper\ndef g[T](*, k=lambda: 4):\n    return k()\nprint(g(), helper(1))\n"
    },
    "generic_default_genexpr": {
        "app": "from pkg.core import helper\ndef g[T](x=tuple(i for i in range(2))):\n    return x\nprint(g(), helper(1))\n"
    },
    "generic_method_default_lambda": {
        "app": "from pkg.core import helper\nclass Box:\n    def get[T](self, f=lambda: 1):\n        return f()\nprint(Box().get(), helper(1))\n"
    },
    "type_alias_generic_lambda": {
        "app": "from pkg.core import helper\ntype A[T] = (lambda: T)\nprint(helper(1))\n"
    },
    "ann_lambda_module": {
        "app": "from pkg.core import helper\nx: (lambda: helper(1)) = 3\nprint(__annotations__['x'](), x)\n"
    },
    "ann_lambda_class": {
        "app": "from pkg.core import helper\nclass K:\n    x: (lambda: helper(1)) = 3\nprint(K.__annotations__['x']())\n"
    },
    "annotated_lambda_class": {
        "app": "from typing import Annotated\nfrom pkg.core import helper\nclass Cfg:\n    port: Annotated[int, lambda v: v > 0] = 80\nprint(Cfg.port, helper(1))\n"
    },
    "except_as_rebind": {
        "app": "from pkg.core import helper\ndef f():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(1), f())\ntry:\n    raise ValueError(3)\nexcept ValueError as helper:\n    print(helper, f())\nprint('helper' in dir(), f())\n"
    },
    "match_capture_rebind": {
        "app": "from pkg.core import helper\ndef f():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(1), f())\nmatch 5:\n    case helper:\n        print(helper, f())\n"
    },
    "global_except_in_fn": {
        "app": "from pkg.core import helper\ndef f():\n    from pkg.core import scale as helper\n    return helper(2)\ndef g():\n    global helper\n    try:\n        raise KeyError(1)\n    except KeyError as helper:\n        return str(type(helper))\nprint(helper(1), f())\nprint(g())\n"
    },
    "except_as_fncoll_only_fn": {
        "app": "from pkg.core import helper\ndef f():\n    from pkg.core import scale as helper\n    return helper(2)\ntry:\n    raise ValueError(3)\nexcept ValueError as helper:\n    print(helper, f())\n"
    },
    "except_as_nocoll": {
        "app": "from pkg.core import helper\nprint(helper(1))\ntry:\n    raise ValueError(3)\nexcept ValueError as helper:\n    print(helper)\n"
    },
    "match_capture_nocoll": {
        "app": "from pkg.core import helper\nprint(helper(1))\nmatch 5:\n    case helper:\n        print(helper)\n"
    },
    "match_star_nocoll": {
        "app": "from pkg.core import helper\nprint(helper(1))\nmatch [1, 2]:\n    case [*helper]:\n        print(helper)\n"
    },
    "match_rest_nocoll": {
        "app": "from pkg.core import helper\nprint(helper(1))\nmatch {'a': 1}:\n    case {**helper}:\n        print(helper)\n"
    },
    "module_globals_write": {
        "app": "from pkg.core import helper\ndef f():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(1), f())\nglobals()['helper'] = lambda v: v * 9\nprint(helper(1), f())\n"
    },
    "module_exec_rebind": {
        "app": "from pkg.core import helper\ndef f():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(1), f())\nexec('helper = lambda v: v * 9')\nprint(helper(1), f())\n"
    },
    "module_exec_read": {
        "app": "from pkg.core import helper\ndef f():\n    from pkg.core import scale as helper\n    return helper(2)\nprint(helper(1), f())\nexec('print(helper(1))')\n"
    },
    "globals_write_nocoll": {
        "app": "from pkg.core import helper\nprint(helper(1))\nglobals()['helper'] = lambda v: v * 9\nprint(helper(1))\n"
    },
    "exec_rebind_nocoll": {
        "app": "from pkg.core import helper\nprint(helper(1))\nexec('helper = lambda v: v * 9')\nprint(helper(1))\n"
    },
    "exec_read_nocoll": {
        "app": "from pkg.core import helper\nprint(helper(1))\nexec('print(helper(1))')\n"
    },
    "eval_read_nocoll": {"app": "from pkg.core import helper\nprint(eval('helper(1)'))\n"},
}


@pytest.mark.parametrize("local_names", [True, False])
@pytest.mark.parametrize("case", REVIEW_CASES)
def test_independent_review_artifact(tmp_path, case, local_names):
    if (case.startswith("generic_") or case.startswith("type_alias_")) and sys.version_info < (
        3,
        12,
    ):
        pytest.skip("PEP 695 syntax requires Python 3.12+")
    if case in {
        "ann_lambda_module",
        "ann_lambda_class",
        "annotated_lambda_class",
    } and sys.version_info < (3, 14):
        pytest.skip("Deferred variable annotation scopes require Python 3.14+")
    if case.startswith("match_") and sys.version_info < (3, 10):
        pytest.skip("Pattern matching requires Python 3.10+")
    spec = REVIEW_CASES[case]
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg/__init__.py").write_text("")
    (src / "pkg/core.py").write_text(CORE + "def other(value):\n    return value - 1\nLIMIT = 7\n")
    for relative, content in spec.get("extra", {}).items():
        path = src / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    (src / "app.py").write_text(spec["app"])
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))

    def run(args, cwd):
        return subprocess.run(
            [sys.executable, *map(str, args)], cwd=cwd, env=env, capture_output=True, timeout=60
        )

    original = run(["-B", "app.py"], src)
    out = tmp_path / "out"
    flags = [] if local_names else ["--no-crossfile-local-names"]
    built = run(
        [
            "-m",
            "pyobfus",
            src,
            "-o",
            out,
            "--no-config",
            "--verify-names",
            *spec.get("flags", []),
            *flags,
        ],
        None,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    actual = run(["-B", "app.py"], out)
    assert (actual.returncode, actual.stdout) == (
        original.returncode,
        original.stdout,
    ), actual.stderr


@pytest.mark.parametrize("operation", ["update", "setdefault", "__setitem__"])
def test_globals_mutation_keeps_import_binding(tmp_path, operation):
    source = tmp_path / "src"
    (source / "pkg").mkdir(parents=True)
    (source / "pkg/__init__.py").write_text("")
    (source / "pkg/core.py").write_text(CORE)
    mutation = {
        "update": "globals().update(helper=lambda x: 9)",
        "setdefault": "del helper\nglobals().setdefault('helper', lambda x: 9)",
        "__setitem__": "globals().__setitem__('helper', lambda x: 9)",
    }[operation]
    (source / "app.py").write_text(PREFIX + mutation + "\nprint(helper(1))\n")
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))
    output = tmp_path / "out"
    built = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(source),
            "-o",
            str(output),
            "--no-config",
            "--verify-names",
        ],
        env=env,
        capture_output=True,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    actual = subprocess.run([sys.executable, "app.py"], cwd=output, env=env, capture_output=True)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout.replace(b"\r\n", b"\n") == b"9\n"


def test_unresolved_import_scope_preserves_module_and_consumers(tmp_path, monkeypatch):
    from pyobfus.config import ObfuscationConfig
    from pyobfus.core.orchestrator import CrossFileOrchestrator
    from pyobfus.transformers import imported_name_transformer
    from pyobfus.transformers.scoped_imports import ScopeResolutionError

    source = tmp_path / "src"
    source.mkdir()
    (source / "dep.py").write_text("def helper(value):\n    return value + 1\n")
    (source / "middle.py").write_text(
        "from dep import helper\ndef run(value):\n    return helper(value)\n"
    )
    (source / "bridge.py").write_text("from middle import run\n__all__ = ['run']\n")
    (source / "app.py").write_text("from bridge import run\nprint(run(3))\n")
    plan = imported_name_transformer.import_plan

    def unresolved(tree, table, module):
        if module == "middle":
            raise ScopeResolutionError("injected unknown compiler scope")
        return plan(tree, table, module)

    monkeypatch.setattr(imported_name_transformer, "import_plan", unresolved)
    orchestrator = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    table = orchestrator.phase1_scan(source)
    assert table.get_obfuscated_import("middle", "run") == "run"
    assert table.get_obfuscated_import("bridge", "run") == "run"
    assert any(
        "middle.py: injected unknown compiler scope" in w for w in orchestrator.planning_warnings
    )
    output = tmp_path / "out"
    assert orchestrator.phase2_transform(source, output) == []
    assert " as helper" in (output / "middle.py").read_text()
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))
    actual = subprocess.run([sys.executable, "app.py"], cwd=output, env=env, capture_output=True)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout.replace(b"\r\n", b"\n") == b"4\n"


@pytest.mark.parametrize("local_names", [True, False])
@pytest.mark.parametrize("binding", ["except", "match", "star", "rest"])
def test_local_string_binder_respects_local_plan(tmp_path, local_names, binding):
    if binding != "except" and sys.version_info < (3, 10):
        pytest.skip("Pattern matching requires Python 3.10+")
    bodies = {
        "except": "try:\n    raise ValueError(3)\nexcept ValueError as helper:\n    return str(helper)",
        "match": "match 3:\n    case helper:\n        return helper",
        "star": "match [3, 4]:\n    case [*helper]:\n        return helper",
        "rest": "match {'a': 3}:\n    case {**helper}:\n        return helper",
    }
    source = tmp_path / "src"
    (source / "pkg").mkdir(parents=True)
    (source / "pkg/__init__.py").write_text("")
    (source / "pkg/core.py").write_text(CORE)
    body = "\n".join("    " + line for line in bodies[binding].splitlines())
    (source / "app.py").write_text(
        PREFIX
        + "def f():\n    from pkg.core import scale as helper\n"
        + body
        + "\nprint(helper(1), f())\n"
    )
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))
    original = subprocess.run([sys.executable, "app.py"], cwd=source, env=env, capture_output=True)
    assert original.returncode == 0, original.stderr
    output = tmp_path / "out"
    flags = [] if local_names else ["--no-crossfile-local-names"]
    built = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyobfus",
            str(source),
            "-o",
            str(output),
            "--no-config",
            "--verify-names",
            *flags,
        ],
        env=env,
        capture_output=True,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    actual = subprocess.run([sys.executable, "app.py"], cwd=output, env=env, capture_output=True)
    assert (actual.returncode, actual.stdout) == (
        original.returncode,
        original.stdout,
    ), actual.stderr
