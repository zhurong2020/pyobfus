"""Execute internal wildcard forwarding artifacts in every name mode."""

import json
import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("local_names", [False, True])
@pytest.mark.parametrize("verify", [False, True])
@pytest.mark.parametrize(
    "core,shim,bridge,app",
    [
        (
            "def helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "__all__ = ['helper', '_private']\ndef helper(value): return value + 1\n_private = 7\n",
            "from .core import *\n__all__ = ['helper', '_private']\n",
            "from .shim import *\n",
            "from pkg.bridge import helper, _private\nprint(helper(1), _private)\n",
        ),
        (
            "def helper(value): return value + 10\nLIMIT = 7\n",
            "from pkg.core import *\ndef helper(value): return value + 1\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\n_hidden = 99\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nimport pkg.shim as s\nprint(helper(1), LIMIT)\nassert not hasattr(s, '_hidden')\n",
        ),
        (
            "__all__ = list(('helper', 'LIMIT'))\ndef helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\n",
            "def helper(value): return value + 10\nfrom pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\nfrom pkg.bridge import helper\n",
            "def helper(value): return value + 1\n",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\nfrom pkg.shim import *\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "__all__ = ['helper']\n__all__.append('LIMIT')\ndef helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\ndef __getattr__(name): raise AttributeError(name)\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n__all__ = []\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\n",
            "from math import *\nfrom pkg.core import helper, LIMIT\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "",
            "import pkg.shim as s\nprint(s.helper(1), s.LIMIT)\n",
        ),
        (
            "from math import sqrt\nLIMIT = 7\n",
            "from pkg.core import *\nprint(sqrt(4))\ndef sqrt(value): return value + 1\n",
            "",
            "from pkg.shim import sqrt, LIMIT\nprint(sqrt(1), LIMIT)\n",
        ),
        (
            "__all__ = ('helper',) + ('LIMIT',)\ndef helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "from pkg.bridge import inject\n_ignored = inject()\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "def inject():\n    import sys\n    sys.modules['pkg.core'].helper = lambda value: value + 1\n",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\nfrom pkg.bridge import getter as __getattr__\n",
            "from pkg.core import *\n",
            "def getter(name): raise AttributeError(name)\n",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "def helper(value): return value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "",
            "import pkg\nprint(pkg.helper(1), pkg.LIMIT)\n",
        ),
        (
            "from pkg.bridge import inject\n@inject\nclass Marker: pass\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "def inject(cls):\n    import sys\n    sys.modules['pkg.core'].helper = lambda value: value + 1\n    return cls\n",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "from pkg.bridge import Meta\nclass Marker(metaclass=Meta): pass\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "class Meta(type):\n    def __new__(mcls, name, bases, namespace):\n        import sys\n        sys.modules['pkg.core'].helper = lambda value: value + 1\n        return super().__new__(mcls, name, bases, namespace)\n",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
        (
            "class Namespace:\n    global helper\n    helper = lambda value: value + 1\nLIMIT = 7\n",
            "from pkg.core import *\n",
            "",
            "from pkg.shim import helper, LIMIT\nprint(helper(1), LIMIT)\n",
        ),
    ],
)
def test_star_forwarding(tmp_path, local_names, verify, core, shim, bridge, app):
    src = tmp_path / "src"
    pkg = src / "pkg"
    pkg.mkdir(parents=True)
    for name, text in {
        "__init__.py": "",
        "core.py": core,
        "shim.py": shim,
        "bridge.py": bridge,
    }.items():
        if name == "__init__.py" and app.startswith("import pkg\n"):
            text = shim
        (pkg / name).write_text(text, encoding="utf-8")
    (src / "app.py").write_text(app, encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    out = tmp_path / "out"
    args = [sys.executable, "-m", "pyobfus", str(src), "-o", str(out), "--no-config", "--json"]
    if not local_names:
        args.append("--no-crossfile-local-names")
    if verify:
        args.append("--verify-names")
    build = subprocess.run(args, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=180)
    assert build.returncode == 0, build.stdout + build.stderr
    if (
        verify
        and core == "def helper(value): return value + 1\nLIMIT = 7\n"
        and shim == "from pkg.core import *\n"
    ):
        assert json.loads(build.stdout)["name_verification"]["coverage_complete"] is True
    if app.startswith("import pkg\n"):
        checked = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyobfus",
                str(src),
                "--check",
                "--json",
                "--offline",
                "--no-config",
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert checked.returncode in {0, 1}, checked.stderr
        assert not any(
            "attribute access through a module" in risk["message"]
            for risk in json.loads(checked.stdout)["risks"]
        )
    results = [
        subprocess.run(
            [sys.executable, "app.py"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        for root in (src, out)
    ]
    for result in results:
        assert result.returncode == 0, result.stderr
    assert (
        results[0].stdout.replace("\r\n", "\n")
        == results[1].stdout.replace("\r\n", "\n")
        == ("2.0\n2 7\n" if "print(sqrt(4))" in shim else "2 7\n")
    )
