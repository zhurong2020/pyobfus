"""Execute real CLI artifacts for runtime enum exports and global rebinding."""

import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

import pytest

ENUM_VARIANTS = [
    "import enum\n@enum.global_enum\nclass Color(enum.IntEnum):\n    RED = 1\n    BLUE = enum.auto()\n",
    "from enum import global_enum, IntEnum, auto\n@global_enum\nclass Color(IntEnum):\n    RED = 1\n    BLUE = auto()\n",
    "from enum import global_enum as g, _simple_enum, IntEnum, auto\n@g\n@_simple_enum(IntEnum)\nclass Color:\n    RED = 1\n    BLUE = auto()\n",
]


def execute(args, cwd, home):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    env.pop("PYTHONPATH", None)
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=90)


def artifact(tmp_path, files, local, verify, single=False):
    src = tmp_path / "src"
    src.mkdir()
    for name, text in files.items():
        target = src / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    expected = execute([sys.executable, "app.py"], src, tmp_path / "home")
    assert expected.returncode == 0, expected.stderr
    out = tmp_path / "out"
    out.mkdir()
    args = [
        sys.executable,
        "-m",
        "pyobfus",
        str(src / "app.py" if single else src),
        "-o",
        str(out / "app.py" if single else out),
        "--no-config",
        "--json",
    ]
    if not local:
        args.append("--no-crossfile-local-names")
    if verify:
        args.append("--verify-names")
    result = execute(args, tmp_path, tmp_path / "home")
    assert result.returncode == 0, result.stdout + result.stderr
    actual = execute([sys.executable, "app.py"], out, tmp_path / "home")
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout  # text=True normalizes Windows newlines.
    return out


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("definition", ENUM_VARIANTS)
@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_injected_enum_names(tmp_path, definition, single, local, verify):
    definition += (
        "__all__ = ['RED', 'BLUE', 'read']\ndef read():\n    return RED.value + BLUE.value\n"
    )
    if single:
        files = {"app.py": definition + "print(RED.value, BLUE.value, read())\n"}
    else:
        files = {
            "pkg/__init__.py": "",
            "pkg/colors.py": definition,
            "app.py": "from pkg.colors import RED, BLUE, read\nfrom pkg import colors\n"
            "print(RED.value, BLUE.value, read())\n"
            "print(colors.RED.value, colors.BLUE.value, colors.read())\n"
            "import star\n",
            "star.py": "from pkg.colors import *\nprint(RED.value, BLUE.value)\n",
        }
    out = artifact(tmp_path, files, local, verify, single)
    statement = "import app as m" if single else "from pkg import colors as m"
    checked = execute(
        [
            sys.executable,
            "-c",
            statement + "; assert 'RED' in m.__all__ and 'BLUE' in m.__all__; "
            "assert m.RED.value == 1 and m.BLUE.value == 2",
        ],
        out,
        tmp_path / "home",
    )
    assert checked.returncode == 0, checked.stderr


@pytest.mark.parametrize(
    "rebind", ["helper = lambda value: value * 10", "from pkg.core import scale as helper"]
)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_global_import_rebinding(tmp_path, rebind, local, verify):
    artifact(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/core.py": "def helper(value):\n    return value + 1\ndef scale(value):\n    return value * 10\n",
            "app.py": "from pkg.core import helper\ndef change():\n    global helper\n    "
            + rebind
            + "\nprint(helper(3))\nchange()\nprint(helper(3))\n",
        },
        local,
        verify,
    )


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_calendar_injected_and_ordinary_exports(tmp_path, local, verify):
    source = Path(sysconfig.get_path("stdlib")) / "calendar.py"
    if "global_enum" not in source.read_text(encoding="utf-8"):
        source = Path("/usr/lib/python3.12/calendar.py")
        if not source.is_file():
            pytest.skip("requires a calendar source containing global_enum (Python 3.12+)")
    out = artifact(
        tmp_path,
        {
            "lib_calendar.py": source.read_text(encoding="utf-8"),
            "app.py": "import lib_calendar as c\nprint(c.month_name[1], c.JANUARY, c.monthrange(2024, 2))\n",
        },
        local,
        verify,
    )
    result = execute(
        [
            sys.executable,
            "-c",
            "import lib_calendar as c; assert all(hasattr(c, n) for n in c.__all__)",
        ],
        out,
        tmp_path / "home",
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "body",
    [
        '    for name in ["RED"]:\n        locals()[name] = 1\n',
        "    RED = make_value()\n",
        "    __module__ = 'math'\n    RED = 1\n",
        "    RED = 1\nColor = enum.global_enum(Color)\n",
        "    def _generate_next_value_(name, start, count, last_values):\n        return count\n    RED = enum.auto()\n",
    ],
)
@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_dynamic_enum_is_rejected(tmp_path, body, single, local, verify):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text(
        "import enum\n@enum.global_enum\nclass Color(enum.IntEnum):\n" + body, encoding="utf-8"
    )
    args = [
        sys.executable,
        "-m",
        "pyobfus",
        str(src / "app.py" if single else src),
        "-o",
        str(tmp_path / "out.py" if single else tmp_path / "out"),
        "--no-config",
        "--json",
    ]
    if not local:
        args.append("--no-crossfile-local-names")
    if verify:
        args.append("--verify-names")
    result = execute(args, tmp_path, tmp_path / "home")
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error_type"] == "AnalysisError"
    assert payload["ai_hint"]
    assert "Cannot safely obfuscate enum.global_enum injection" in payload["message"]


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_ignored_members_and_missing_method(tmp_path, single, local, verify):
    definition = (
        "import enum\n@enum.global_enum\nclass Color(enum.IntEnum):\n"
        '    _ignore_ = "ignored"\n    ignored = 9\n    _RED = 1\n    BLUE: int = 2\n'
        "    @classmethod\n    def _missing_(cls, value):\n        return cls._RED\n"
        "print(_RED.value, BLUE.value, Color(0).value)\n"
    )
    artifact(tmp_path, {"app.py": definition}, local, verify, single)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_same_member_in_multiple_modules_and_package_reexport(tmp_path, local, verify):
    artifact(
        tmp_path,
        {
            "pkg/__init__.py": "from .first import RED\n__all__ = ['RED']\n",
            "pkg/first.py": "from enum import global_enum, IntEnum\n@global_enum\nclass Color(IntEnum):\n    RED = 1\n    I0 = 2\n",
            "pkg/second.py": "import enum as e\n@e.global_enum\nclass Color(e.IntEnum):\n    RED = 7\n",
            "app.py": "from pkg import RED\nfrom pkg.first import I0\nfrom pkg.second import RED as second_red\nfrom pkg import first, second\nprint(RED.value, I0.value, second_red.value, first.RED.value, second.RED.value)\n",
        },
        local,
        verify,
    )


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_enum_module_fallback_preserves_internal_imports(tmp_path, local, verify):
    artifact(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/core.py": "def helper(value):\n    return value + 1\n",
            "pkg/colors.py": "from enum import global_enum, IntEnum\nfrom .core import helper\n__all__ = ['helper', 'RED']\n@global_enum\nclass Color(IntEnum):\n    RED = 1\ndef __getattr__(name):\n    raise AttributeError(name)\n",
            "app.py": "from pkg.colors import helper, RED\nfrom pkg import colors\nprint(helper(3), RED.value, colors.helper(4))\nimport star\n",
            "star.py": "from pkg.colors import *\nprint(helper(5), RED.value)\n",
        },
        local,
        verify,
    )
