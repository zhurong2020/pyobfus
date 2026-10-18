"""H4 project-wide registry stores must carry a sys.modules identity."""

import ast
import json
import os
import subprocess
import sys

import pytest

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus.core.preflight import PreflightChecker
from tests.test_crossfile_module_attributes import project, runner

ORDINARY = [
    "class Registry:\n    def write(self):\n        self.modules = {}\n        self.modules['k'] = 1\nRegistry().write()\n",
    "class Registry:\n    pass\nobj = Registry()\nobj.modules = {}\nobj.modules['k'] = 1\n",
    "class Registry:\n    pass\nobj = Registry()\nobj.modules = {'k': 1}\ndel obj.modules['k']\n",
]
REGISTRIES = [
    "import sys\nsys.modules['h4_unused'] = None\n",
    "import sys as s\ns.modules['h4_unused'] = None\n",
    "from sys import modules\nmodules['h4_unused'] = None\n",
    "import sys\nsys.modules['h4_unused'] = None\ndel sys.modules['h4_unused']\n",
    "import sys as s\nif False:\n    s = object()\ns.modules['h4_unused'] = None\n",
    "import sys\ns = sys\ns.modules['h4_unused'] = None\n",
]


def execute(root, home):
    result = subprocess.run(
        [sys.executable, "-B", "app.py"],
        cwd=root,
        env=dict(os.environ, HOME=str(home), USERPROFILE=str(home)),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.replace("\r\n", "\n"), result.stderr


@pytest.mark.parametrize("statement", ORDINARY)
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("attributes", [False, True])
def test_ordinary_registry_artifact(tmp_path, statement, locals_enabled, attributes):
    src = project(tmp_path, statement + "from pkg import mod\nprint(mod.LIMIT)\n")
    out = tmp_path / "out"
    ob = CrossFileOrchestrator(
        ObfuscationConfig(
            crossfile_local_names=locals_enabled,
            crossfile_module_attributes=attributes,
            max_workers=1,
        )
    )
    assert ob.obfuscate(src, out).success
    if attributes:
        assert not ob.attribute_inventory.unsafe
        assert execute(out, tmp_path)[:2] == execute(src, tmp_path)[:2] == (0, "7\n")
    else:
        # Existing opt-out semantics intentionally retain the attribute spelling.
        assert "LIMIT" in [
            n.attr
            for n in ast.walk(ast.parse((out / "app.py").read_text()))
            if isinstance(n, ast.Attribute)
        ]
        assert execute(src, tmp_path)[:2] == (0, "7\n")
        artifact = execute(out, tmp_path)
        assert artifact[:2] == (1, "")
        assert "AttributeError" in artifact[2]


@pytest.mark.parametrize("statement", REGISTRIES)
def test_sys_registry_still_closes_all_proofs(tmp_path, statement):
    src = project(tmp_path, statement + "from pkg import mod\nprint(mod.LIMIT)\n")
    ob = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    ob.phase1_scan(src)
    inventory = ob.attribute_inventory
    assert inventory.unsafe == set(inventory.trees)
    risks = PreflightChecker(obfuscation_config=ob.config).check_path(src).risks
    risk = next(r for r in risks if "mod.LIMIT accesses" in r.message)
    assert risk.to_dict()["reason"] == "module_attribute.modules_store"
    assert "sys.modules" in risk.message


def test_build_unproved_count_and_hint(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\nprint(mod.LIMIT)\n",
        init="try:\n    pass\nexcept Exception:\n    pass\n",
    )
    report = tmp_path / "report.json"
    result = runner().invoke(
        main,
        [
            str(src),
            "-o",
            str(tmp_path / "out"),
            "--json",
            "--no-config",
            "--build-report",
            str(report),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["stats"]["module_attribute_accesses_unproved"] == 1
    assert "--check" in payload["ai_hint"]
    assert "--check" in result.stderr
    assert (
        json.loads(report.read_text())["transformations"]["module_attribute_accesses_unproved"] == 1
    )
    risk = next(
        r for r in PreflightChecker().check_path(src).risks if "mod.LIMIT accesses" in r.message
    )
    assert risk.to_dict()["reason"] == "module_attribute.package_init_not_static"


@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("attributes", [False, True])
@pytest.mark.parametrize("statement", REGISTRIES[:4])
def test_registry_artifact_with_preserved_export(tmp_path, statement, locals_enabled, attributes):
    # A preserved export is executable even when registry mutation closes H.
    # This verifies the real output independently of the proof diagnostics.
    src = project(tmp_path, statement + "from pkg import mod\nprint(mod.LIMIT)\n")
    config = ObfuscationConfig(
        max_workers=1, crossfile_local_names=locals_enabled, crossfile_module_attributes=attributes
    )
    config.exclude_names.add("LIMIT")
    ob = CrossFileOrchestrator(config)
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    assert execute(out, tmp_path)[:2] == execute(src, tmp_path)[:2] == (0, "7\n")
    assert ob.get_statistics()["module_attribute_accesses_unproved"] == 0


@pytest.mark.parametrize(
    "statement,guard",
    [
        ("def f(obj):\n    obj.modules[0] = 1\n", False),
        ("def f(sys):\n    sys.modules[0] = 1\n", True),
        ("import sys as s\ndef f(s):\n    s.modules[0] = 1\n", False),
        ("import os as obj\nobj.modules[0] = 1\n", False),
        ("import os as obj\nobj = object()\nobj.modules[0] = 1\n", True),
        ("import sys as s\nregistry = s.modules\nregistry[0] = 1\n", True),
        (
            "from sys import modules as registry\nif False:\n    registry = {}\ndel registry[0]\n",
            True,
        ),
        (
            "import sys as s\nclass C:\n    s = object()\n    def f(self):\n        s.modules[0] = 1\n",
            True,
        ),
    ],
)
def test_uncertain_receiver_boundary(tmp_path, statement, guard):
    src = project(tmp_path, statement + "from pkg import mod\nprint(mod.LIMIT)\n")
    ob = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    ob.phase1_scan(src)
    assert bool(ob.attribute_inventory.modules_stores) is guard
    for stores in ob.attribute_inventory.modules_stores.values():
        assert all(reason for _, _, reason in stores)


def test_zero_count_has_no_warning(tmp_path):
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n")
    result = runner().invoke(main, [str(src), "-o", str(tmp_path / "out"), "--json", "--no-config"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["stats"]["module_attribute_accesses_unproved"] == 0
    assert "could not be proved" not in result.stderr
    assert "unproved module attribute" not in json.loads(result.stdout)["ai_hint"]
    report = tmp_path / "single-report.json"
    single = runner().invoke(
        main,
        [
            str(src / "pkg/mod.py"),
            "-o",
            str(tmp_path / "single.py"),
            "--json",
            "--no-config",
            "--build-report",
            str(report),
        ],
    )
    assert single.exit_code == 0, single.output
    assert json.loads(single.stdout)["stats"]["module_attribute_accesses_unproved"] == 0
    assert (
        json.loads(report.read_text())["transformations"]["module_attribute_accesses_unproved"] == 0
    )
    assert "could not be proved" not in single.stderr


def test_incremental_count_and_pre_h4_invalidation(tmp_path):
    from pyobfus.core.cache import BuildCache

    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n", init="import os\n")
    out = tmp_path / "out"
    args = [str(src), "-o", str(out), "--json", "--no-config", "--incremental"]
    for cached in (False, True):
        result = runner().invoke(main, args)
        assert result.exit_code == 0, result.output
        data = json.loads(result.stdout)
        assert data["stats"]["module_attribute_accesses_unproved"] == 1
        assert "--check" in data["ai_hint"] and "--check" in result.stderr
        assert (data["stats"]["files_processed"] == 0) is cached
    cache = BuildCache(out)
    manifest = cache.load_manifest()
    del manifest["signature"]["module_attribute_analysis_version"]
    cache.manifest_path.write_text(json.dumps(manifest))
    result = runner().invoke(main, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["stats"]["files_processed"] == 3


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("cycle", "import_cycle"),
        ("hazard", "module_hazard"),
        ("nested", "nested_reimport"),
        ("order", "other"),
    ],
)
def test_refusal_reason_codes(tmp_path, kind, expected):
    app = "from pkg import mod\nprint(mod.LIMIT)\n"
    src = project(tmp_path, app)
    if kind == "cycle":
        (src / "pkg/mod.py").write_text("import app\nLIMIT = 7\n")
    elif kind == "hazard":
        (src / "pkg/mod.py").write_text('LIMIT = 7\nexec("pass")\n')
    elif kind == "nested":
        (src / "app.py").write_text(
            "from pkg import mod\ndef f():\n    from pkg.mod import LIMIT as mod\nprint(mod.LIMIT)\n"
        )
    else:
        (src / "app.py").write_text("print(mod.LIMIT)\nfrom pkg import mod\n")
    risks = PreflightChecker().check_path(src).risks
    risk = next(r for r in risks if "mod.LIMIT accesses" in r.message)
    assert risk.to_dict()["reason"] == f"module_attribute.{expected}"
    assert "Reason:" in risk.message


def test_self_copy_reports_remaining_package_and_cycle_boundaries(tmp_path):
    import shutil
    from pathlib import Path

    src = tmp_path / "src"
    src.mkdir()
    package = Path(__file__).resolve().parents[1] / "pyobfus"
    shutil.copytree(package, src / "pyobfus", ignore=shutil.ignore_patterns("__pycache__"))
    report = PreflightChecker().check_path(src)
    reasons = {code for risk in report.risks for code in risk.reasons or []}
    assert "module_attribute.modules_store" not in reasons
    assert {"module_attribute.package_init_not_static", "module_attribute.import_cycle"} <= reasons
    out = tmp_path / "out"
    ob = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    assert ob.obfuscate(src, out).success
    assert not ob.attribute_inventory.modules_stores
    assert len(ob.attribute_inventory.unsafe) < len(ob.attribute_inventory.trees)
    assert ob.get_statistics()["module_attribute_accesses_unproved"] > 0
    result = subprocess.run(
        [sys.executable, "-B", "-c", "import pyobfus.cli"],
        cwd=out,
        env=dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path)),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "AttributeError" in result.stderr


@pytest.mark.parametrize(
    "source",
    [
        "from . import owner\nowner.modules[0] = 1\n",
        "from . import modules\ndel modules[0]\n",
    ],
)
def test_unresolved_relative_import_is_conservative(source):
    from pyobfus.core.module_attributes import discover_modules_stores

    stores = discover_modules_stores(ast.parse(source), lambda node: None)
    assert len(stores) == 1
    assert stores[0][2] == "unresolved imported or possible sys receiver"
    if "from . import modules" in source:
        aliased = source.replace("import modules", "import modules as registry").replace(
            "del modules[", "del registry["
        )
        assert discover_modules_stores(ast.parse(aliased), lambda node: None)


@pytest.mark.parametrize(
    "expression",
    [
        '[0 for s.modules["h4_unused"] in [None]]',
        '{0 for s.modules["h4_unused"] in [None]}',
        '{0: 0 for s.modules["h4_unused"] in [None]}',
        'list(0 for s.modules["h4_unused"] in [None])',
    ],
)
def test_comprehension_target_closes_registry_proofs(tmp_path, expression):
    src = project(
        tmp_path, "import sys as s\n" + expression + "\nfrom pkg import mod\nprint(mod.LIMIT)\n"
    )
    ob = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    ob.phase1_scan(src)
    assert ob.attribute_inventory.unsafe == set(ob.attribute_inventory.trees)
    assert ob.attribute_inventory.modules_stores
