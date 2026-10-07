"""Directory builds must rename module names in decorators, bases and lambdas.

Up to and including 0.5.31, the cross-file transformers visited these
expressions but discarded the renamed node they returned, so a same-module
decorator (`@logged`), base class (`class Child(Base)`), metaclass, or a
lambda whose default or body is a bare module name kept its original
spelling while the definition was renamed. The obfuscated module then failed
with NameError on import. Imported decorators on functions had the same
defect in the imported-name pass.

The fixture covers every position for both same-module and imported names,
builds it as a directory (the default cross-file mode), runs the original and
the output, and requires identical stdout.
"""

import subprocess
import sys

from click.testing import CliRunner

from pyobfus.cli import main

HELPERS = 'def imported_deco(fn):\n    fn.imported = True\n    return fn\nclass ImportedBase:\n    kind = "imported"\nclass ImportedMeta(type):\n    pass\nIMPORTED_LIMIT = 7\n'

APP = 'from helpers import imported_deco, ImportedBase, ImportedMeta, IMPORTED_LIMIT\nimport asyncio\ndef local_deco(fn):\n    fn.local = True\n    return fn\nclass LocalBase:\n    kind = "local"\nclass LocalMeta(type):\n    pass\nLIMIT = 5\n@local_deco\ndef f1():\n    return 1\n@local_deco\nasync def f2():\n    return 2\n@imported_deco\ndef f3():\n    return 3\n@imported_deco\nasync def f4():\n    return 4\n@local_deco\nclass A(LocalBase, metaclass=LocalMeta):\n    pass\n@imported_deco\nclass B(ImportedBase, metaclass=ImportedMeta):\n    pass\nclass C(LocalBase, ImportedBase):\n    pass\nget_local = lambda: LIMIT\nget_imported = lambda: IMPORTED_LIMIT\ndflt_local = lambda n=LIMIT: n\ndflt_imported = lambda n=IMPORTED_LIMIT: n\nkwd_local = lambda *, n=LIMIT: n\ndef outer():\n    @local_deco\n    def inner():\n        return LIMIT\n    class Inner(LocalBase):\n        pass\n    return inner(), Inner.kind\nprint(f1(), f1.local, asyncio.run(f2()), f2.local, f3.imported, asyncio.run(f4()), f4.imported)\nprint(A.kind, type(A).__name__ == type(A).__name__, A.local, B.kind, B.imported, C.kind)\nprint(get_local(), get_imported(), dflt_local(), dflt_imported(), kwd_local(), outer())\n'


def _run(cwd):
    return subprocess.run(
        [sys.executable, "app.py"], cwd=cwd, capture_output=True, text=True, timeout=60
    )


def test_decorators_bases_metaclasses_and_lambdas_keep_working(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "helpers.py").write_text(HELPERS, encoding="utf-8")
    (src / "app.py").write_text(APP, encoding="utf-8")
    expected = _run(src)
    assert expected.returncode == 0, expected.stderr

    out = tmp_path / "out"
    result = CliRunner().invoke(main, [str(src), "-o", str(out)])
    assert result.exit_code == 0, result.output

    built = (out / "app.py").read_text(encoding="utf-8")
    for original in ("local_deco", "LocalBase", "LocalMeta", "imported_deco", "LIMIT"):
        assert original not in built, original

    actual = _run(out)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout
