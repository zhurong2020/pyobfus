"""Registry mutators share the subscript-store proof boundary."""

import ast
import json

import pytest

from pyobfus.cli import main
from pyobfus.core.module_attributes import discover_modules_stores
from tests.test_crossfile_module_attributes import project, runner
from tests.test_modules_store_precision import execute

MUTATIONS = [
    "REG.update({'defect_p_unused': None})",
    "REG.setdefault('defect_p_unused', None)",
    "REG.pop('defect_p_unused', None)",
    "REG.popitem()",
    "REG.clear()",
    "REG.__setitem__('defect_p_unused', None)",
    "REG.__delitem__('defect_p_unused')",
    "REG |= {'defect_p_unused': None}",
]
ALIASES = [
    ("import sys", "sys.modules"),
    ("import sys as s", "s.modules"),
    ("from sys import modules", "modules"),
    ("import sys\nmods = sys.modules", "mods"),
    ("import sys\ns = sys", "s.modules"),
]


@pytest.mark.parametrize("mutation", MUTATIONS)
@pytest.mark.parametrize("setup,receiver", ALIASES)
@pytest.mark.parametrize("nested", [False, True])
def test_registry_mutator_resolution(mutation, setup, receiver, nested):
    source = setup + "\n" + mutation.replace("REG", receiver) + "\n"
    if nested:
        source = "def mutate():\n" + "".join("    " + line + "\n" for line in source.splitlines())
    assert discover_modules_stores(ast.parse(source), lambda n: n.module)


@pytest.mark.parametrize("mutation", MUTATIONS)
@pytest.mark.parametrize(
    "setup,receiver",
    [
        ("class Registry: pass\nself = Registry()\nself.modules = {}", "self.modules"),
        ("mods = {}", "mods"),
        ("", "arg.modules"),
        ("import sys as s", "s.modules"),
    ],
)
def test_ordinary_and_shadowed_receivers(mutation, setup, receiver):
    source = "def mutate(arg, s):\n" + "".join(
        "    " + line + "\n"
        for line in (setup + "\n" + mutation.replace("REG", receiver)).splitlines()
    )
    # An explicit import inside the function deliberately supplies a sys candidate.
    expected = setup == "import sys as s"
    assert bool(discover_modules_stores(ast.parse(source), lambda n: n.module)) is expected


@pytest.mark.parametrize(
    "expression", ["REG.get('sys')", "REG.keys()", "REG.items()", "'sys' in REG"]
)
@pytest.mark.parametrize("setup,receiver", ALIASES)
def test_readonly_registry(expression, setup, receiver):
    assert not discover_modules_stores(
        ast.parse(setup + "\n" + expression.replace("REG", receiver)), lambda n: n.module
    )


@pytest.mark.parametrize("mutation", MUTATIONS[:-1])
def test_dynamic_possible_sys_receiver(mutation):
    source = "import sys as s\n" + mutation.replace("REG", 'getattr(s, "modules")')
    assert discover_modules_stores(ast.parse(source), lambda n: n.module)
    source = "def f(obj):\n    " + mutation.replace("REG", 'getattr(obj, "modules")')
    assert not discover_modules_stores(ast.parse(source), lambda n: n.module)


@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("attributes", [False, True])
@pytest.mark.parametrize("mutation", MUTATIONS)
@pytest.mark.parametrize("setup,receiver", ALIASES)
@pytest.mark.parametrize("nested", [False, True])
def test_mutator_real_artifact(
    tmp_path, mutation, locals_enabled, attributes, setup, receiver, nested
):
    src = project(tmp_path, "import pkg.hazard\nfrom pkg import mod\nprint(mod.LIMIT)\n")
    # Restore the registry after destructive methods so imports can complete.
    # update / |= reproduce replacement of a project module with changed exports.
    operation = mutation.replace("REG", receiver)
    if "update(" in operation or "|=" in operation:
        operation = operation.replace("'defect_p_unused': None", "'pkg.mod': replacement")
    hazard = (
        "import sys, types\n" + setup + "\nsaved = sys.modules.copy()\n"
        "replacement = types.ModuleType('pkg.mod')\nreplacement.LIMIT = 9\n"
        "mods['defect_p_unused'] = None\n" + operation + "\n"
    )
    # Avoid a subscript store in the fixture: it would mask the missing detector.
    hazard = hazard.replace("mods['defect_p_unused'] = None", "saved['defect_p_unused'] = None")
    if "__delitem__" in operation:
        hazard = hazard.replace("'defect_p_unused')", "'sys')")
    if "update(" not in operation and "|=" not in operation:
        hazard += (
            "restore(sys.modules, saved)\n"  # restore via opaque helper below to avoid masking
        )
        hazard = "def restore(registry, original):\n    registry.update(original)\n" + hazard
    if nested:
        hazard = (
            "def mutate():\n"
            + "".join("    " + line + "\n" for line in hazard.splitlines())
            + "mutate()\n"
        )
    (src / "pkg/hazard.py").write_text(hazard)
    args = [str(src), "-o", str(tmp_path / "out"), "--no-config", "--json"]
    if not locals_enabled:
        args.append("--no-crossfile-local-names")
    if not attributes:
        args.append("--no-crossfile-module-attributes")
    original = execute(src, tmp_path)
    assert original[0] == 0, original
    result = runner().invoke(main, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["stats"]["module_attribute_accesses_unproved"] > 0
    assert "--check" in result.stderr
    artifact = execute(tmp_path / "out", tmp_path)
    assert artifact[:2] == original[:2] or "--check" in result.stderr
    checked = runner().invoke(main, [str(src), "--check", "--json", "--no-config"])
    assert "module_attribute.modules_store" in checked.stdout


@pytest.mark.parametrize("mutation", MUTATIONS)
@pytest.mark.parametrize("receiver", ["mods", "self.modules", "arg.modules"])
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_ordinary_mutator_artifact(tmp_path, mutation, receiver, locals_enabled):
    # Every method executes on a populated ordinary dictionary, including the
    # destructive operations. No registry mutation should mask proof precision.
    operation = mutation.replace("REG", receiver)
    if receiver == "mods":
        body = (
            "def mutate():\n"
            "    mods = {'defect_p_unused': None}\n"
            f"    {operation}\n"
            "mutate()\n"
        )
    else:
        parameter = receiver.split(".")[0]
        body = (
            "class Registry:\n"
            f"    def mutate({parameter}):\n"
            f"        {parameter}.modules = {{'defect_p_unused': None}}\n"
            f"        {operation}\n"
            "Registry().mutate()\n"
        )
    assert_precise_artifact(tmp_path, body, locals_enabled)


@pytest.mark.parametrize(
    "expression", ["mods.get('sys')", "mods.keys()", "mods.items()", "'sys' in mods"]
)
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_readonly_artifact(tmp_path, expression, locals_enabled):
    assert_precise_artifact(
        tmp_path, "from sys import modules as mods\n" + expression + "\n", locals_enabled
    )


def assert_precise_artifact(tmp_path, body, locals_enabled):
    from pyobfus.config import ObfuscationConfig
    from pyobfus.core.orchestrator import CrossFileOrchestrator

    src = project(tmp_path, "import pkg.hazard\nfrom pkg import mod\nprint(mod.LIMIT)\n")
    (src / "pkg/hazard.py").write_text(body)
    ob = CrossFileOrchestrator(
        ObfuscationConfig(max_workers=1, crossfile_local_names=locals_enabled)
    )
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    assert not ob.attribute_inventory.modules_stores
    assert ob.get_statistics()["module_attribute_accesses_unproved"] == 0
    assert any(edit.expected == "LIMIT" for edit in ob.attribute_plans["app"].edits)
    assert execute(out, tmp_path)[:2] == execute(src, tmp_path)[:2] == (0, "7\n")


@pytest.mark.parametrize("mutation", MUTATIONS)
@pytest.mark.parametrize(
    "setup,receiver,expected",
    [
        ("import sys as s\ndef f(s):\n    REG", "s.modules", False),
        ("import os as obj\nREG", "obj.modules", False),
        ("import os as obj\nobj = object()\nREG", "obj.modules", True),
        ("from . import modules as registry\nREG", "registry", True),
        ("from . import owner\nREG", "owner.modules", True),
        ("import sys as s\nif False:\n    s = object()\nREG", "s.modules", True),
        ("import sys as s\na = s.modules\nb = a\nREG", "b", True),
        (
            "import sys as s\nclass C:\n    s = object()\n    def f(self):\n        REG",
            "s.modules",
            True,
        ),
    ],
)
def test_mutator_uncertain_receiver_boundary(mutation, setup, receiver, expected):
    source = setup.replace("REG", mutation.replace("REG", receiver))
    stores = discover_modules_stores(ast.parse(source), lambda n: None if n.level else n.module)
    assert bool(stores) is expected


def test_mutator_incremental_invalidation(tmp_path):
    from pyobfus.core.cache import BuildCache

    src = project(
        tmp_path, "import sys\nsys.modules.update({})\nfrom pkg import mod\nprint(mod.LIMIT)\n"
    )
    out = tmp_path / "out"
    args = [str(src), "-o", str(out), "--no-config", "--json", "--incremental"]
    for cached in (False, True):
        result = runner().invoke(main, args)
        data = json.loads(result.stdout)
        assert result.exit_code == 0, result.output
        assert data["stats"]["module_attribute_accesses_unproved"] == 1
        assert (data["stats"]["files_processed"] == 0) is cached
        assert "--check" in result.stderr
    cache = BuildCache(out)
    manifest = cache.load_manifest()
    manifest["signature"]["module_attribute_analysis_version"] = 2
    cache.manifest_path.write_text(json.dumps(manifest))
    result = runner().invoke(main, args)
    assert json.loads(result.stdout)["stats"]["files_processed"] == 3
