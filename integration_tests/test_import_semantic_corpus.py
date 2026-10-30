"""Bounded import semantics, runnable against checkout or a public interpreter.

Set PYOBFUS_VALIDATION_PYTHON to an interpreter with a released pyobfus wheel
to repeat the same cases independently. No project code or real home is used.
"""

import json
import os
import subprocess
import sys

import pytest

CASES = {
    "relative_alias": {
        "pkg/__init__.py": "",
        "pkg/core.py": "def calculate(x):\n    return x + 7\n",
        "main.py": "from pkg.core import calculate as action\nprint(action(5))\n",
    },
    "reexport": {
        "pkg/__init__.py": "from .core import calculate\n",
        "pkg/core.py": "def calculate(x):\n    return x + 7\n",
        "main.py": "from pkg import calculate\nprint(calculate(5))\n",
    },
    "cycle": {
        "pkg/__init__.py": "VERSION = 7\nfrom .core import calculate\n",
        "pkg/core.py": "from pkg import VERSION\ndef calculate(x):\n    return x + VERSION\n",
        "main.py": "from pkg import core\nprint(core.calculate(5))\n",
    },
    "try_init": {
        "pkg/__init__.py": "try:\n    import missing_synthetic_dependency\nexcept ImportError:\n    VERSION = 7\n",
        "pkg/core.py": "def calculate(x):\n    return x + 7\n",
        "main.py": "import pkg.core as engine\nprint(engine.calculate(5))\n",
    },
    "local_shadow": {
        "pkg/__init__.py": "",
        "pkg/core.py": "def calculate(x):\n    return x + 7\n",
        "pkg/other.py": "def calculate(x):\n    return x - 3\n",
        "main.py": "from pkg.core import calculate as action\ndef run():\n    from pkg.other import calculate as action\n    return action(5)\nprint(action(5), run())\n",
    },
    "star_forward": {
        "pkg/__init__.py": "",
        "pkg/core.py": "__all__ = ['calculate']\ndef calculate(x):\n    return x + 7\n",
        "pkg/shim.py": "from .core import *\n",
        "main.py": "from pkg.shim import calculate\nprint(calculate(5))\n",
    },
    "module_getattr": {
        "pkg/__init__.py": "",
        "pkg/core.py": "def calculate(x):\n    return x + 7\ndef __getattr__(name):\n    if name == 'dynamic':\n        return 8\n    raise AttributeError(name)\n",
        "main.py": "from pkg import core\nprint(core.calculate(5), core.dynamic)\n",
    },
    "exception": {
        "pkg/__init__.py": "",
        "pkg/core.py": "def calculate(x):\n    raise ValueError('synthetic failure')\n",
        "main.py": "from pkg import core\ncore.calculate(5)\n",
    },
}


@pytest.mark.parametrize("case", sorted(CASES))
@pytest.mark.parametrize("conservative", [False, True], ids=["default", "preserve"])
def test_import_semantic_corpus(tmp_path, case, conservative):
    python = os.environ.get("PYOBFUS_VALIDATION_PYTHON", sys.executable)
    source = tmp_path / "src"
    output = tmp_path / "output"
    mapping = tmp_path / "private" / "mapping.json"
    env = {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
    env.pop("PYTHONPATH", None)
    for name, code in CASES[case].items():
        file = source / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code, encoding="utf-8")

    def run(args, cwd):
        return subprocess.run(
            [python, *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=30
        )

    baseline = run(["-B", "main.py"], source)
    args = [
        "-m",
        "pyobfus",
        str(source),
        "-o",
        str(output),
        "--no-config",
        "--save-mapping",
        str(mapping),
        "--verify-syntax",
        "--json",
        "--jobs",
        "1",
    ]
    if conservative:
        args.append("--preserve-unproved-module-attributes")
    built = run(args, tmp_path)
    assert built.returncode == 0, built.stderr + built.stdout
    payload = json.loads(built.stdout)
    actual = run(["-B", "main.py"], output)
    same = (actual.returncode, actual.stdout) == (baseline.returncode, baseline.stdout)
    if baseline.returncode:
        same = same and actual.stderr.splitlines()[-1] == baseline.stderr.splitlines()[-1]
    if not same and not conservative:
        # Known default proof limits must be visible; preservation is tested
        # separately and must restore behavior for this bounded corpus.
        # Do not accept a new regression merely because it emits a warning.
        assert case in {"cycle", "try_init", "module_getattr"}, actual.stderr
        assert payload["stats"]["module_attribute_accesses_unproved"] > 0
        assert "warn" in (built.stderr + built.stdout).lower()
        return
    assert same, actual.stderr + actual.stdout
    if case == "exception":
        trace = tmp_path / "trace.txt"
        trace.write_text(actual.stderr, encoding="utf-8")
        restored = run(
            [
                "-m",
                "pyobfus",
                "--unmap",
                "--trace",
                str(trace),
                "--mapping",
                str(mapping),
                "--json",
            ],
            tmp_path,
        )
        assert restored.returncode == 0, restored.stderr
        assert "in calculate" in json.loads(restored.stdout)["unmapped_trace"]
