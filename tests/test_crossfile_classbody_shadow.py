"""Execute directory artifacts to check ordered class LOAD_NAME resolution."""

import ast
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from pyobfus.core.class_bindings import mark_class_bindings
from pyobfus.config import ObfuscationConfig
from pyobfus.core.orchestrator import CrossFileOrchestrator

MINIMAL = """from pkg.util import helper
def setfirst(v):
    return v
class Cal:
    early = setfirst(1)
    def helper(self):
        return "method"
    alias = helper
    def getfirst(self):
        return 1
    def setfirst(self, v):
        self.v = v
    first = property(getfirst, setfirst)
c = Cal(); c.first = 3
print(c.v, setfirst(2), Cal.early, Cal().alias(), helper(0))
"""

CASES = [
    """class C:
    early = helper()
    def helper(self):
        return 9
    alias = helper
    def method(self, default=helper):
        return helper(), default(self)
print(C.early, C().alias(), C().method(), helper())
""",
    """class C:
    helper = helper() + 1
    a = helper
    helper: int = helper + 1
    b = helper
    del helper
    c = helper()
    helper: int
    d = helper()
    helper = 10
    helper += 1
    e = helper
    f = (helper := helper + 1)
print(C.a, C.b, C.c, C.d, C.e, C.f, C.helper, sorted(C.__annotations__), helper())
""",
    """class C:
    helper = [1, 2]
    same = [helper for helper in helper]
    xs = [helper() for _ in helper]
    ys = {helper() for _ in helper}
    zs = {i: helper() for i in helper}
    gs = tuple(helper() for _ in helper)
    nested = [helper() for _ in helper for j in range(helper()) if helper()]
    callback = staticmethod(lambda default=helper: (helper(), default))
print(C.same, C.xs, sorted(C.ys), C.zs, C.gs, C.nested, C.callback(), helper())
""",
    """class C:
    class helper:
        value = 9
    saved = helper.value
    class Inner(helper):
        early = helper()
        helper = 11
        saved = helper
        del helper
        after_delete = helper()
        def method(self):
            return helper()
    outer = helper.value
print(C.saved, C.Inner.early, C.Inner.saved, C.Inner.after_delete, C.Inner().method(), C.outer)
""",
    """from contextlib import nullcontext
class C:
    for helper in [9]:
        in_loop = helper
    after_loop = helper
    del helper
    with nullcontext(10) as helper:
        in_with = helper
    after_with = helper
    del helper
    if True:
        helper = 11
    after_if = helper
    del helper
    try:
        helper = 12
    except ValueError:
        helper = 13
    after_try = helper
    del helper
    while True:
        helper = 14
        break
    after_while = helper
print(C.in_loop, C.after_loop, C.in_with, C.after_with, C.after_if, C.after_try, C.after_while)
""",
    """class C:
    import math as helper
    a = helper.floor(1.5)
    del helper
    b = helper()
    from math import ceil as helper
    c = helper(1.5)
    del helper
    from pkg.util import helper
    d = helper()
    def method(self):
        from pkg.util import helper
        return helper()
    def shadow(self):
        helper = lambda: 15
        return helper()
print(C.a, C.b, C.c, C.d, C().method(), C().shadow(), helper())
""",
    """class C:
    helper = 9
    __all__ = ["helper"]
    class Inner:
        __all__: list = ["helper"]
print(C.__all__, C.Inner.__all__, helper())
""",
]


def _run(directory, home, interpreter=sys.executable):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    return subprocess.run(
        [interpreter, "main.py"],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _project(tmp_path, source, enabled, workers):
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg" / "__init__.py").write_text("")
    (src / "pkg" / "util.py").write_text(
        'def helper(v=0):\n    return "module"\n'
        if source == MINIMAL
        else "def helper(v=0):\n    return 7\n"
    )
    (src / "main.py").write_text(source)
    out = tmp_path / "out"
    expected = _run(src, tmp_path / "home")
    assert expected.returncode == 0, expected.stderr
    config = ObfuscationConfig(crossfile_local_names=enabled, max_workers=workers)
    result = CrossFileOrchestrator(config).obfuscate(src, out)
    assert result.success, result.errors
    actual = _run(out, tmp_path / "home")
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout
    return expected.stdout


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("workers", [1, 2])
def test_minimal(tmp_path, enabled, workers):
    assert _project(tmp_path, MINIMAL, enabled, workers) == "3 2 1 method module\n"


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("workers", [1, 2])
@pytest.mark.parametrize("imported", [False, True], ids=["module", "import"])
@pytest.mark.parametrize(
    "body",
    CASES,
    ids=[
        "def",
        "assign-delete",
        "comprehensions-lambda",
        "nested-class",
        "conditional-targets",
        "imports",
        "class-all",
    ],
)
def test_classbody_resolution(tmp_path, enabled, workers, imported, body):
    prefix = "from pkg.util import helper\n" if imported else "def helper(v=0):\n    return 7\n"
    _project(tmp_path, prefix + body, enabled, workers)


# global_enum generates these module names at runtime. They are a separate
# dynamic-export limitation, so keep them explicit while testing class scopes.
CALENDAR_DYNAMIC_EXPORTS = set(
    "JANUARY FEBRUARY MARCH APRIL MAY JUNE JULY AUGUST SEPTEMBER OCTOBER NOVEMBER "
    "DECEMBER MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY SUNDAY".split()
)

CALENDAR_MAIN = """from lib_calendar import (month, monthrange, isleap, Calendar, HTMLCalendar, TextCalendar)
print(month(2024, 2))
print(monthrange(2024, 2), isleap(2024))
print([str(day) for day in Calendar(6).itermonthdates(2024, 2)])
print(HTMLCalendar().formatmonth(2024, 2))
c = TextCalendar()
print(c.firstweekday)
c.firstweekday = 6
print(c.firstweekday, c.formatmonth(2024, 2))
"""


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("workers", [1, 2])
def test_calendar_project(tmp_path, enabled, workers):
    stdlib = Path("/usr/lib/python3.12/calendar.py")
    if not stdlib.is_file() or not Path("/usr/bin/python3.12").is_file():
        pytest.skip("requires the Python 3.12 stdlib calendar fixture")
    src = tmp_path / "src"
    src.mkdir()
    (src / "lib_calendar.py").write_text(stdlib.read_text())
    (src / "main.py").write_text(textwrap.dedent(CALENDAR_MAIN))
    # The unchanged 3.12 source requires enum.global_enum (absent in 3.10).
    # Build on the current interpreter; execute this stdlib fixture on 3.12.
    expected = _run(src, tmp_path / "home", "/usr/bin/python3.12")
    assert expected.returncode == 0, expected.stderr
    out = tmp_path / "out"
    config = ObfuscationConfig(crossfile_local_names=enabled, max_workers=workers)
    config.exclude_names.update(CALENDAR_DYNAMIC_EXPORTS)
    result = CrossFileOrchestrator(config).obfuscate(src, out)
    assert result.success, result.errors
    actual = _run(out, tmp_path / "home", "/usr/bin/python3.12")
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout


@pytest.mark.parametrize(
    "suite",
    [
        "if False:\n        helper = 9",
        "for helper in []:\n        pass",
        "while False:\n        helper = 9",
        "try:\n        pass\n    except ValueError:\n        helper = 9",
    ],
)
def test_conditional_may_bind_policy(suite):
    # Freeze the explicitly conservative policy even when the suite does not
    # execute: the following LOAD_NAME is preserved, not rewritten as a global.
    tree = ast.parse("class C:\n    " + suite + "\n    saved = helper\n")
    mark_class_bindings(tree)
    reference = tree.body[0].body[-1].value
    assert reference.id == "helper"
    assert getattr(reference, "_pyobfus_class_binding", False)
