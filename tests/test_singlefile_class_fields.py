"""Execute single-file products against annotation-driven field APIs."""

import ast
import os
import subprocess
import sys

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.transformers.name_mangler import NameMangler

PRESETS = [None, "safe", "fastapi", "django"]
CLASS_NAMES = (
    "Point",
    "Parent",
    "Child",
    "Options",
    "Pair",
    "Record",
    "ExtPair",
    "ExtRecord",
    "Model",
    "Person",
)
MINIMAL = """from dataclasses import dataclass, asdict
@dataclass
class Point:
    x: int
    y: int = 0
p = Point(x=1, y=2)
print(p, asdict(p))
"""

DATACLASS_FORMS = [
    ("from dataclasses import dataclass", "dataclass"),
    ("import dataclasses", "dataclasses.dataclass"),
    ("from dataclasses import dataclass as dc", "dc"),
    ("from dataclasses import dataclass", "dataclass(frozen=True)"),
]

INHERITANCE = """from dataclasses import dataclass, asdict, field
import json
@dataclass
class Parent:
    x: int = field(default=1)
@dataclass
class Child(Parent):
    y: int = 0
p = Child(x=3, y=4)
print(p, p.x, p.y, asdict(p), json.dumps(asdict(p), sort_keys=True))
"""

OPTIONS = """from dataclasses import dataclass, asdict, field, InitVar
from typing import ClassVar
@dataclass(kw_only=True, slots=True)
class Options:
    x: int = field(default=1)
    seed: InitVar[int] = 0
    tag: ClassVar[str] = "class"
    y: int = field(init=False, default=0)
    def __post_init__(self, seed):
        self.y = self.x + seed
p = Options(x=3, seed=4)
print(p, asdict(p), p.tag, hasattr(p, "__dict__"))
"""

NAMED = """from typing import NamedTuple, TypedDict
import json
class Pair(NamedTuple):
    x: int
    y: int = 0
class Record(TypedDict):
    x: int
    y: int
p = Pair(x=1, y=2)
r: Record = {"x": 3, "y": 4}
print(p, Pair._fields, p._asdict(), p.x, r["x"], r["y"], sorted(Record.__annotations__), json.dumps(r, sort_keys=True))
"""

EXTENSIONS = NAMED.replace(
    "from typing import NamedTuple, TypedDict",
    "from typing_extensions import NamedTuple, TypedDict",
)

PYDANTIC = """from pydantic import BaseModel
class Parent(BaseModel):
    x: int
class Model(Parent):
    y: int = 0
p = Model(x=1, y=2)
print(p.model_dump(), p.model_dump_json(), sorted(Model.model_fields), p.x, p.y)
"""

ATTRS_FORMS = [
    ("import attr", "attr.s(auto_attribs=True)"),
    ("import attrs", "attrs.define"),
    ("from attrs import define", "define"),
    ("from attrs import frozen", "frozen"),
    ("import attr", "attr.s"),
]


def attrs_source(imports, decorator):
    # The legacy @attr.s form also works with explicitly annotated attr.ib().
    fields = (
        "    x: int = attr.ib(default=1)\n    y: int = attr.ib(default=0)"
        if decorator == "attr.s"
        else "    x: int\n    y: int = 0"
    )
    return (
        imports
        + "\nimport attrs\n@"
        + decorator
        + "\nclass Person:\n"
        + fields
        + "\np = Person(x=1, y=2)\nprint(p, attrs.asdict(p), p.x, p.y)\n"
    )


ATTRS_INHERITANCE = """import attrs
@attrs.define
class Parent:
    x: int = attrs.field(default=1)
@attrs.define
class Child(Parent):
    y: int = 0
p = Child(x=3, y=4)
print(p, attrs.asdict(p), p.x, p.y)
"""


def run(command, cwd, home):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=60)


def compare(tmp_path, source, preset, *, driver=None, extra=()):
    (tmp_path / "app.py").write_text(source)
    # Class identities remain subject to the existing module rename policy.
    # Preserve only their names to compare full repr output, not any fields.
    config = "obfuscation:\n  exclude_names: [" + ", ".join(CLASS_NAMES) + "]\n"
    if preset:
        config += "  preset: " + preset + "\n"
    (tmp_path / "config.yml").write_text(config)
    if driver:
        (tmp_path / "consumer.py").write_text(
            driver.replace("from built import", "from app import")
        )
        original_command = [sys.executable, "consumer.py"]
    else:
        original_command = [sys.executable, "app.py"]
    expected = run(original_command, tmp_path, tmp_path / "home")
    assert expected.returncode == 0, expected.stderr
    command = [
        sys.executable,
        "-m",
        "pyobfus",
        "app.py",
        "-o",
        "built.py",
        "--config",
        "config.yml",
        *extra,
    ]
    if preset:
        command += ["--preset", preset]
    build = run(command, tmp_path, tmp_path / "home")
    assert build.returncode == 0, build.stdout + build.stderr
    if driver:
        (tmp_path / "consumer.py").write_text(driver)
        actual_command = [sys.executable, "consumer.py"]
    else:
        actual_command = [sys.executable, "built.py"]
    actual = run(actual_command, tmp_path, tmp_path / "home")
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout
    return actual.stdout


@pytest.mark.parametrize("preset", PRESETS)
def test_minimal(tmp_path, preset):
    assert compare(tmp_path, MINIMAL, preset) == "Point(x=1, y=2) {'x': 1, 'y': 2}\n"


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize("imports,decorator", DATACLASS_FORMS)
def test_dataclass_decorators(tmp_path, preset, imports, decorator):
    source = (
        imports
        + "\nfrom dataclasses import asdict\nimport json\n@"
        + decorator
        + "\nclass Point:\n    x: int\n    y: int = 0\np = Point(x=1, y=2)\nprint(p, asdict(p), json.dumps(asdict(p), sort_keys=True))\n"
    )
    compare(tmp_path, source, preset)


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize(
    "source",
    [INHERITANCE, OPTIONS, NAMED, EXTENSIONS],
    ids=["inheritance", "initvar-classvar-kwonly-slots", "typing", "typing-extensions"],
)
def test_generated_apis(tmp_path, preset, source):
    if source == OPTIONS and sys.version_info < (3, 10):
        pytest.skip("dataclass kw_only/slots require Python 3.10")
    if source == EXTENSIONS:
        pytest.importorskip("typing_extensions")
    compare(tmp_path, source, preset)


@pytest.mark.parametrize("preset", PRESETS)
def test_external_keyword_consumer(tmp_path, preset):
    compare(
        tmp_path,
        MINIMAL.split("p = Point")[0],
        preset,
        driver="from built import Point\nfrom dataclasses import asdict\np = Point(x=1, y=2)\nprint(p, asdict(p))\n",
    )


@pytest.mark.parametrize("preset", PRESETS)
def test_pydantic(tmp_path, preset):
    pydantic = pytest.importorskip("pydantic")
    if not hasattr(pydantic.BaseModel, "model_dump"):
        pytest.skip("model_dump requires pydantic v2")
    compare(tmp_path, PYDANTIC, preset)


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize("imports,decorator", ATTRS_FORMS)
def test_attrs(tmp_path, preset, imports, decorator):
    pytest.importorskip("attrs")
    compare(tmp_path, attrs_source(imports, decorator), preset)


@pytest.mark.parametrize("preset", PRESETS)
def test_attrs_inheritance(tmp_path, preset):
    pytest.importorskip("attrs")
    compare(tmp_path, ATTRS_INHERITANCE, preset)


@pytest.mark.parametrize("preserve_params", [False, True])
@pytest.mark.parametrize("analyzed", [False, True])
def test_scope_filter_and_mapping(analyzed, preserve_params):
    source = """module_only: int = 1
class Point:
    x: int
    I0: int = 1
    plain = 2
    if True:
        conditional: int = 3
    class Nested:
        nested: int = 4
    def method(self, param):
        local_only: int = param
        self.instance_only: int = 5
        return local_only
x = 7
keep = 8
"""
    config = ObfuscationConfig(preserve_param_names=preserve_params)
    config.exclude_names.add("keep")
    # Analyzer-free parameter preservation has no parameter symbol table;
    # exercise its normal non-preserving mode without changing that contract.
    if not analyzed and preserve_params:
        config.exclude_names.add("param")
    tree = ast.parse(source)
    analyzer = SymbolAnalyzer(config) if analyzed else None
    if analyzer:
        analyzer.analyze(tree)
    mangler = NameMangler(config, analyzer)
    mangler.transform(tree)
    mapping = mangler.get_name_mapping()
    fields = {"x", "I0", "conditional", "nested"}
    assert fields.isdisjoint(mapping)
    assert fields.isdisjoint(mapping.values())
    assert "keep" not in mapping
    assert ("param" not in mapping) == preserve_params
    assert {"Point", "Nested", "plain", "method", "local_only", "module_only"} <= set(mapping)
    if analyzer:
        expected = analyzer.obfuscatable_names - fields
        if preserve_params:
            expected -= analyzer.parameter_names
        assert set(mapping) == expected


@pytest.mark.parametrize("preset", PRESETS)
def test_preserve_param_names_cli(tmp_path, preset):
    source = MINIMAL + "\ndef total(value):\n    return value\nprint(total(value=3))\n"
    compare(tmp_path, source, preset, extra=("--preserve-param-names",))
