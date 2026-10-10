"""Execute CLI products: imported export names and local aliases are distinct.

PYOBFUS_ALIAS_PYTHON selects an independent public-wheel interpreter for the
same regression suite; all CLI and product processes use a temporary home.
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

CORE = """def scale(value, factor=2):
    return value * factor

def decorate(fn):
    return fn

class Number(int):
    pass
"""

CASES = {
    "absolute-package": {
        "entry.py": "from pkg import scale as action\nfrom pkg.core import scale as direct\nprint(action(2), direct(3))\n",
    },
    "relative": {
        "pkg/use.py": "from .core import scale as action\ndef run():\n    return action(4)\n",
        "entry.py": "from pkg.use import run\nprint(run())\n",
    },
    "same-name-and-direct": {
        "entry.py": "from pkg.core import scale as scale\nfrom pkg.core import scale as action\nfrom pkg.use import run\nprint(scale(2), action(3), run())\n",
        "pkg/use.py": "from .core import scale as action\nfrom .core import scale\ndef run():\n    return action(4), scale(5)\n",
    },
    "same-name-reexport": {
        "pkg/api.py": "from .core import scale as scale\n__all__ = ['scale']\n",
        "entry.py": "from pkg.api import scale\nprint(scale(2))\n",
    },
    "alias-allocation-collision": {
        "entry.py": "from pkg.core import scale as I0\nprint(I0(2))\n",
    },
    "nested-scopes": {
        "entry.py": """from pkg.core import scale as action
from pkg.core import decorate as deco
from pkg.core import Number as Kind
@deco
def declared(value: Kind = action(2)) -> Kind:
    return value

def outer():
    from pkg.core import scale as inner_action
    from pkg.core import decorate as local_deco
    from pkg.core import Number as LocalKind
    @local_deco
    def annotated(value: LocalKind = inner_action(5)) -> LocalKind:
        return value
    def closure():
        nonlocal inner_action
        inner_action = lambda value: value + 10
        return inner_action(3)
    before = (lambda: inner_action(2))()
    values = [inner_action(i) for i in range(3)]
    return before, values, annotated(), closure(), inner_action(4)

def global_use():
    global action
    action = lambda value: value + 20
    return action(2)

class Box:
    from pkg.core import scale as class_action
    value = class_action(3)
    typed: Kind = class_action(4)
    @deco
    def method(self, value=class_action(5)):
        return value

if True:
    from pkg.core import scale as conditional
print(declared(), outer(), Box.value, Box.typed, Box().method(), conditional(6))
print(global_use(), action(3))
""",
    },
    "local-global-import": {
        "entry.py": """def bind():
    global action
    from pkg.core import scale as action
bind()
print(action(2))
""",
    },
    "reexport-chain": {
        "pkg/api.py": "from .core import scale as action\n__all__ = ['action']\n",
        "pkg/bridge.py": "from .api import action\n__all__ = ['action']\n",
        "pkg/__init__.py": "from .bridge import action as action\n__all__ = ['action']\n",
        "entry.py": "from pkg import action\nfrom pkg.api import action as direct\nfrom pkg.bridge import *\nprint(action(2), direct(3))\n",
    },
    "implicit-reexport": {
        "pkg/api.py": "from .core import scale as action\n",
        "pkg/bridge.py": "from .api import action\n",
        "entry.py": "from pkg.bridge import action\nprint(action(2))\n",
    },
    "third-party": {
        "entry.py": """from json import dumps as d
def run():
    from json import dumps as local_d
    return local_d([1, 2])
print(d({'answer': 42}), run())
""",
    },
}


@pytest.fixture
def processes(tmp_path):
    interpreter = os.environ.get("PYOBFUS_ALIAS_PYTHON", sys.executable)
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))
    # A public-wheel comparison must not accidentally import this checkout.
    if "PYOBFUS_ALIAS_PYTHON" in os.environ:
        env.pop("PYTHONPATH", None)
    cwd = tmp_path if "PYOBFUS_ALIAS_PYTHON" in os.environ else Path(__file__).resolve().parents[1]

    def run(args, directory=cwd):
        command = [interpreter, *map(str, args)]
        result = subprocess.run(
            command, cwd=directory, env=env, capture_output=True, text=True, timeout=60
        )
        with (tmp_path / "processes.jsonl").open("a", encoding="utf-8") as log:
            log.write(
                json.dumps(
                    {
                        "command": command,
                        "cwd": str(directory),
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                )
                + "\n"
            )
        return result

    return run


def write_project(tmp_path, files):
    source = tmp_path / "src"
    contents = {"pkg/core.py": CORE, "pkg/__init__.py": "from .core import scale\n"}
    contents.update(files)
    for relative, text in contents.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return source


@pytest.mark.parametrize("local_names", [True, False], ids=["locals-on", "locals-off"])
@pytest.mark.parametrize("case", CASES)
def test_alias_product(tmp_path, processes, case, local_names):
    source = write_project(tmp_path, CASES[case])
    baseline = processes([source / "entry.py"], source)
    assert baseline.returncode == 0, baseline.stderr
    output = tmp_path / "out"
    flags = [] if local_names else ["--no-crossfile-local-names"]
    built = processes(["-m", "pyobfus", source, "-o", output, *flags])
    assert built.returncode == 0, built.stdout + built.stderr
    product = processes([output / "entry.py"], output)
    assert product.returncode == 0, product.stderr
    assert product.stdout == baseline.stdout
    # Execution proves semantics; also lock the chosen alias-preservation policy.
    for relative in CASES[case]:
        original = ast.parse((source / relative).read_text())
        generated = ast.parse((output / relative).read_text())
        aliases = [
            a.asname
            for n in ast.walk(original)
            if isinstance(n, (ast.Import, ast.ImportFrom))
            for a in n.names
            if a.asname
        ]
        generated_aliases = [
            a.asname
            for n in ast.walk(generated)
            if isinstance(n, (ast.Import, ast.ImportFrom))
            for a in n.names
            if a.asname
        ]
        assert set(aliases) <= set(generated_aliases)


@pytest.mark.parametrize("local_names", [True, False])
def test_module_alias_limitation_h(tmp_path, processes, local_names):
    source = write_project(
        tmp_path,
        {"entry.py": "import pkg.core as engine\nprint(engine.__name__)\nprint(engine.scale(2))\n"},
    )
    baseline = processes([source / "entry.py"], source)
    assert baseline.returncode == 0, baseline.stderr
    output = tmp_path / "out"
    flags = [] if local_names else ["--no-crossfile-local-names"]
    built = processes(["-m", "pyobfus", source, "-o", output, *flags])
    assert built.returncode == 0, built.stdout + built.stderr
    product = processes([output / "entry.py"], output)
    assert product.stdout == "pkg.core\n"  # module alias itself resolves correctly
    assert product.returncode != 0
    assert "AttributeError" in product.stderr and "scale" in product.stderr
    assert "NameError" not in product.stderr


def test_singlefile_alias_unchanged(tmp_path, processes):
    source = tmp_path / "entry.py"
    source.write_text("from json import dumps as d\nprint(d([2, 3]))\n", encoding="utf-8")
    baseline = processes([source], tmp_path)
    assert baseline.returncode == 0, baseline.stderr
    output = tmp_path / "out.py"
    built = processes(["-m", "pyobfus", source, "-o", output])
    assert built.returncode == 0, built.stdout + built.stderr
    product = processes([output], tmp_path)
    assert product.returncode == 0, product.stderr
    assert product.stdout == baseline.stdout
