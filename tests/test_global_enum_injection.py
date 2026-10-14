"""Execute real CLI artifacts for runtime enum exports and global rebinding."""

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
ENUM_VARIANTS += [
    "import enum\n@enum.global_enum\nclass Color(enum.IntEnum):\n    RED = 1\n    BLUE = 2\n    def label(self):\n        return self.name.lower()\n",
    "import enum\n@enum.global_enum\nclass Color(enum.IntFlag):\n    RED = 1 << 3\n    GREEN = 2\n    BLUE = RED | GREEN\n    __str__ = object.__str__\n",
    "import enum\n@enum.global_enum\n@enum._simple_enum(enum.IntFlag, boundary=enum.KEEP)\nclass Color:\n    RED = 1\n    BLUE = 2\n    __str__ = object.__str__\n",
    "import enum\n@enum.global_enum\nclass Color(enum.StrEnum):\n    RED = enum.auto()\n    BLUE = enum.auto()\n",
    "import enum\ndef extra(cls):\n    return cls\n@enum.global_enum\n@extra\nclass Color(enum.IntEnum):\n    RED = 1\n    BLUE = 2\n",
    "import enum\nclass Color(enum.IntEnum):\n    RED = 1\n    BLUE = 2\nColor = enum.global_enum(Color)\n",
    'import enum\n@enum.global_enum\nclass Color(enum.IntEnum):\n    _ignore_ = "key value"\n    for key, value in [("RED", 1), ("BLUE", 2)]:\n        locals()[key] = value\n    del key, value\n',
]


def execute(args, cwd, home):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    env.pop("PYTHONPATH", None)
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=90)


def artifact(tmp_path, files, local, verify, single=False, exclude=False):
    src = tmp_path / "src"
    src.mkdir()
    for name, text in files.items():
        target = src / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    expected = execute([sys.executable, "-S", "app.py"], src, tmp_path / "home")
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
    if exclude:
        config = tmp_path / "config.yaml"
        config.write_text("exclude_names: [RED, BLUE, label]\n", encoding="utf-8")
        args.remove("--no-config")
        args.extend(["--config", str(config)])
    if not local:
        args.append("--no-crossfile-local-names")
    if verify:
        args.append("--verify-names")
    result = execute(args, tmp_path, tmp_path / "home")
    assert result.returncode == 0, result.stdout + result.stderr
    actual = execute([sys.executable, "-S", "app.py"], out, tmp_path / "home")
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout.replace("\r\n", "\n") == expected.stdout.replace("\r\n", "\n")
    return out


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("exclude", [False, True])
@pytest.mark.parametrize("definition", ENUM_VARIANTS)
@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_injected_enum_names(tmp_path, definition, single, local, verify, exclude):
    definition += (
        "__all__ = ['RED', 'BLUE', 'read']\ndef read():\n    return (RED.value, BLUE.value)\n"
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
    out = artifact(tmp_path, files, local, verify, single, exclude)
    statement = "import app as m" if single else "from pkg import colors as m"
    checked = execute(
        [
            sys.executable,
            "-S",
            "-c",
            statement + "; assert 'RED' in m.__all__ and 'BLUE' in m.__all__; "
            "assert type(m.RED).RED is m.RED and type(m.BLUE).BLUE is m.BLUE",
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
            "-S",
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
def test_dynamic_enum_build_falls_back(tmp_path, body, single, local, verify):
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
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Preserved all module names" in result.stderr


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


def stdlib_re_source():
    if sys.version_info < (3, 11):
        pytest.skip("requires a re package with global_enum")
    source = Path(sysconfig.get_path("stdlib")) / "re"
    system_source = Path("/usr/lib/python3.12/re")
    if sys.version_info[:2] == (3, 12) and system_source.is_dir():
        source = system_source
    if not source.is_dir():
        pytest.skip("requires compatible re package sources")
    # re's Python opcodes must match the running interpreter's native _sre.
    return source


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_stdlib_re_package(tmp_path, local, verify):
    source = stdlib_re_source()
    files = {
        "app.py": "import re; from pathlib import Path; "
        "assert str(re.__file__).startswith(str(Path.cwd())); print(re.compile('abc', re.I).search('ABC').group()); "
        "print(re.I is re.IGNORECASE, bool(re.search('a', 'A', re.IGNORECASE)))\n"
    }
    for path in source.rglob("*.py"):
        files["re/" + path.relative_to(source).as_posix()] = path.read_text(encoding="utf-8")
    artifact(tmp_path, files, local, verify)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_custom_enum_method_is_callable(tmp_path, single, local, verify):
    definition = (
        "import enum\n@enum.global_enum\nclass Color(enum.IntEnum):\n"
        "    RED = 1\n    GREEN = 2\n    def label(self):\n        return self.name.lower()\n"
        "def pick():\n    return RED.label()\n"
    )
    app = "print(RED, Color.GREEN.label(), pick())\n"
    files = (
        {"app.py": definition + app}
        if single
        else {
            "pkg/__init__.py": "",
            "pkg/colors.py": definition,
            "app.py": "from pkg.colors import RED, Color, pick\n" + app,
        }
    )
    artifact(tmp_path, files, local, verify, single)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_non_static_enum_package_preserves_dependencies(tmp_path, local, verify):
    artifact(
        tmp_path,
        {
            "pkg/__init__.py": "import enum\nfrom . import reader\n@enum.global_enum\n"
            "class Color(enum.IntEnum):\n    RED = 1\n    def label(self):\n"
            "        return self.name.lower()\ndef read():\n    return reader.read()\n",
            "pkg/constants.py": "LIMIT = 7\n",
            "pkg/reader.py": "from .constants import *\ndef read():\n    return LIMIT\n",
            "app.py": "from pkg import RED, read\nimport pkg\nprint(RED.label(), read(), pkg.read())\n",
        },
        local,
        verify,
    )


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_stdlib_re_direct_directory(tmp_path, local, verify):
    import shutil

    source = stdlib_re_source()
    src = tmp_path / "src" / "re"
    shutil.copytree(source, src, ignore=shutil.ignore_patterns("__pycache__"))
    out = tmp_path / "out" / "re"
    args = [sys.executable, "-m", "pyobfus", str(src), "-o", str(out), "--no-config", "--json"]
    if not local:
        args.append("--no-crossfile-local-names")
    if verify:
        args.append("--verify-names")
    build = execute(args, tmp_path, tmp_path / "home")
    assert build.returncode == 0, build.stdout + build.stderr
    probe = (
        "import re; from pathlib import Path; "
        "assert str(re.__file__).startswith(str(Path.cwd())); "
        "assert re.compile('abc', re.I).search('ABC').group() == 'ABC'; "
        "assert re.I is re.IGNORECASE; assert re.search('a', 'A', re.IGNORECASE)"
    )
    result = execute([sys.executable, "-S", "-c", probe], out.parent, tmp_path / "home")
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(sys.version_info < (3, 11), reason="global_enum requires Python 3.11")
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("verify", [False, True])
def test_dynamic_injection_reserves_consumer_binding(tmp_path, local, verify):
    # The earlier A export shifts main's class allocation away from I0,
    # keeping the baseline executable while exposing consumer capture.
    artifact(
        tmp_path,
        {
            "a_owner.py": "import enum\ndef A():\n    pass\n@enum.global_enum\n"
            "class Color(enum.IntEnum):\n    locals()['I0'] = 1\n",
            "b_app.py": "from a_owner import I0\ndef helper():\n    return 3\n"
            "print(I0.value, helper())\n",
            "app.py": "import b_app\n",
        },
        local,
        verify,
    )
