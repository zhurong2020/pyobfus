"""Behavioral checks for directory local bindings and frozen allocation."""

import ast
import subprocess
import sys

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus.core.mapping import ObfuscationMapping


def build(tmp_path, source, *, enabled=True, workers=1):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "app.py").write_text(source)
    out = tmp_path / f"out-{enabled}-{workers}"
    config = ObfuscationConfig(crossfile_local_names=enabled, max_workers=workers)
    ob = CrossFileOrchestrator(config)
    result = ob.obfuscate(src, out)
    assert result.success, result.errors
    run = subprocess.run([sys.executable, str(out / "app.py")], capture_output=True, text=True)
    original = subprocess.run([sys.executable, str(src / "app.py")], capture_output=True, text=True)
    assert run.returncode == original.returncode == 0, run.stderr
    assert run.stdout == original.stdout
    return ob, (out / "app.py").read_text()


@pytest.mark.parametrize(
    "source",
    [
        """def outer(param):
    value = param
    def update():
        nonlocal value
        value += 2
        return value
    def shadow():
        value = 90
        return value
    result = [value + item for item in range(3)]
    callback = lambda value: value + 1
    reader = lambda: value
    return update(), shadow(), result, callback(4), reader()
print(outer(3))
""",
        """from contextlib import nullcontext
def run():
    total: int = 0
    for item in range(3):
        total += item
    with nullcontext(4) as value:
        total += value
    try:
        raise ValueError('problem')
    except ValueError as error:
        total += len(str(error))
    if (extra := 2):
        total += extra
    match {'x': 5, 'y': 6}:
        case {'x': captured, **rest}:
            total += captured + rest['y']
    match [1, 2, 3]:
        case [first, *remaining]:
            total += first + len(remaining)
    return total
print(run())
""",
        """def run():
    import math
    from math import sqrt as root
    class Box:
        constant = 3
        def get(self):
            result = value
            return result
    value = root(16)
    return math.floor(value), Box().get(), Box.constant
print(run())
""",
        """import asyncio
async def run(param=3):
    value = param + 1
    return value
print(asyncio.run(run(param=4)))
""",
        """def run():
    value = 3
    result = [(value := value + 1) for item in range(value)]
    return value, result
print(run())
""",
        """result = 90
def run(param=2):
    result = param + 1
    return result
print(run(param=4), result)
""",
    ],
)
def test_binding_semantics(tmp_path, source):
    if "    match " in source and sys.version_info < (3, 10):
        pytest.skip("match requires Python 3.10")
    ob, output = build(tmp_path, source)
    assert ob.content_stats["local_names_obfuscated"] > 0
    compile(output, "<output>", "exec")


@pytest.mark.parametrize(
    "expression", ["locals()", "vars()", "dir()", "eval('value')", "exec('value = 8')"]
)
def test_reflection_skips_function(tmp_path, expression):
    ob, output = build(
        tmp_path, f"def run():\n    value = 3\n    {expression}\n    return value\nprint(run())\n"
    )
    assert ob.content_stats["local_functions_skipped"] == 1
    assert "value = 3" in output


def test_nested_reflection_preserves_capture(tmp_path):
    ob, _ = build(
        tmp_path,
        "def run():\n    value = 3\n    def inner():\n        value\n        return eval('value')\n    return inner()\nprint(run())\n",
    )
    assert ob.content_stats["local_functions_skipped"] == 2


def test_uniqueness_parallel_mapping_and_determinism(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    source = "def first(I10=1):\n    value = I10\n    return value\ndef second():\n    value = 2\n    return value\nprint(first(), second())\n"
    for filename in ("app.py", "other.py"):
        (src / filename).write_text(source)
    outputs = []
    for workers in (1, 2):
        ob = CrossFileOrchestrator(ObfuscationConfig(max_workers=workers))
        out = tmp_path / str(workers)
        assert ob.obfuscate(src, out).success
        outputs.append([(p.name, p.read_bytes()) for p in sorted(out.glob("*.py"))])
        names = [name for plan in ob.local_plans.values() for name in plan.mappings]
        assert len(names) == len(set(names)) == 4
        assert not set(names).intersection(
            {v for mod in ob.global_table.module_exports.values() for v in mod.values()}
        )
        assert "I10" not in names
        mapping = ObfuscationMapping.from_global_table(ob.global_table)
        path = tmp_path / "mapping.json"
        mapping.save(path)
        loaded = ObfuscationMapping.load(path)
        assert all(loaded.reverse(name) == "value" for name in names)
        trace = " ".join(names)
        assert loaded.unmatched_names(trace) == []
        trace_path = tmp_path / "trace.txt"
        trace_path.write_text(trace)
        result = CliRunner().invoke(
            main, ["--unmap", str(trace_path), "--mapping", str(path), "--json"]
        )
        assert result.exit_code == 0, result.output
        assert "value" in result.output
    assert outputs[0] == outputs[1]


def test_switch_and_exclusions(tmp_path):
    source = "def run(param):\n    value = param\n    return value\nprint(run(3))\n"
    ob, output = build(tmp_path, source, enabled=False)
    assert not ob.local_plans
    assert "value = param" in output
    src = tmp_path / "src"
    config = ObfuscationConfig(exclude_names={"value"}, name_prefix="local")
    ob = CrossFileOrchestrator(config)
    assert ob.obfuscate(src, tmp_path / "excluded").success
    assert not ob.local_plans["app"].mappings
    tree = ast.parse(output)
    assert any(isinstance(n, ast.arg) and n.arg == "param" for n in ast.walk(tree))


def test_yaml_cli_validation_and_override(tmp_path):
    config = tmp_path / "pyobfus.yaml"
    config.write_text("obfuscation:\n  crossfile_local_names: false\n")
    result = CliRunner().invoke(main, ["--validate-config", str(config), "--json"])
    assert result.exit_code == 0, result.output
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def run():\n    value = 3\n    return value\n")
    for flag, expected in [
        ("--no-crossfile-local-names", True),
        ("--crossfile-local-names", False),
    ]:
        out = tmp_path / flag
        result = CliRunner().invoke(main, [str(src), "-o", str(out), "-c", str(config), flag])
        assert result.exit_code == 0, result.output
        assert ("value = 3" in (out / "app.py").read_text()) == expected


def test_global_declaration_and_outer_shadow(tmp_path):
    build(
        tmp_path,
        """value = 9
def run():
    value = 2
    def inner():
        global value
        value += 1
        return value
    return inner(), value
print(run(), value)
""",
    )


def test_same_line_scopes_and_class_shadow(tmp_path):
    build(
        tmp_path,
        """def run():
    value = 3
    callbacks = [lambda: value, lambda value=4: value]
    pairs = [(value, [value for value in range(2)]) for item in range(value)]
    class Box:
        value = 90
        def read(self):
            return value
    return [f() for f in callbacks], pairs, Box.value, Box().read()
print(run())
""",
    )


def test_comprehension_first_iter_and_generator(tmp_path):
    build(
        tmp_path,
        """def run():
    value = 3
    result = [value for value in range(value)]
    gen = (value + item for item in range(3))
    other = {item: value for item in range(2)}
    return result, list(gen), other, value
print(run())
""",
    )


def test_local_project_import_and_cli_mapping(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "helper.py").write_text("def answer():\n    value = 4\n    return value\n")
    (src / "app.py").write_text(
        "def run():\n    from helper import answer\n    value = answer()\n    return value\nprint(run())\n"
    )
    out = tmp_path / "out"
    mapping_path = tmp_path / "mapping.json"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--save-mapping", str(mapping_path)]
    )
    assert result.exit_code == 0, result.output
    proc = subprocess.run([sys.executable, str(out / "app.py")], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "4"
    mapping = ObfuscationMapping.load(mapping_path)
    assert "value" in [info[1] for info in mapping.global_map.values()]
    assert "from helper import answer" not in (out / "app.py").read_text()


def test_reused_orchestrator_is_deterministic(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def run():\n    value = 3\n    return value\n")
    ob = CrossFileOrchestrator(ObfuscationConfig())
    assert ob.obfuscate(src, tmp_path / "one").success
    assert ob.obfuscate(src, tmp_path / "two").success
    assert (tmp_path / "one/app.py").read_bytes() == (tmp_path / "two/app.py").read_bytes()


def test_preserved_parameter_cannot_capture_module_name(tmp_path):
    build(
        tmp_path,
        """def helper():
    return 3
def run(I0=4):
    value = helper()
    return value + I0
print(run())
""",
    )


def test_strings_dunders_and_super(tmp_path):
    ob, output = build(
        tmp_path,
        """def run():
    class Base:
        def read(self):
            return 2
    class Child(Base):
        def read(self):
            __special__ = 3
            value = super().read()
            return value + __special__, __class__ is Child, f'value:{value}'
    return Child().read()
print(run())
""",
    )
    assert "__special__ = 3" in output
    assert "value:" in output
    assert "super()" in output
    assert "__class__" in output


def test_dotted_import_is_conservative(tmp_path):
    ob, output = build(
        tmp_path,
        """def run():
    import os.path
    value = os.path.basename('a/b')
    return value
print(run())
""",
    )
    assert ob.content_stats["local_functions_skipped"] == 1
    assert "value =" in output


def test_local_string_annotation_and_private_class(tmp_path):
    build(
        tmp_path,
        """def run():
    class Box:
        __value = 3
        def read(self):
            return self.__value
    def inner(arg: 'Box'):
        value = arg.read()
        return value
    return inner(Box()), Box()._Box__value
print(run())
""",
    )


def test_annotation_expression_scope(tmp_path):
    build(
        tmp_path,
        """def run():
    value = 3
    def inner(arg: (lambda: value)()):
        result = arg
        return result
    return inner(4), inner.__annotations__['arg']
print(run())
""",
    )


def test_class_and_unevaluated_local_annotations(tmp_path):
    build(
        tmp_path,
        """def run():
    value = 3
    unused: (lambda: missing)()
    class Box:
        attr: (lambda: value)()
    return Box.__annotations__['attr']
print(run())
""",
    )


def test_reflective_match_local_shadows_export(tmp_path):
    if sys.version_info < (3, 10):
        pytest.skip("match requires Python 3.10")
    ob, output = build(
        tmp_path,
        """value = 90
def run():
    locals()
    match 3:
        case value:
            return value
print(run(), value)
""",
    )
    assert ob.content_stats["local_functions_skipped"] == 1
    assert "case value:" in output


def test_reflective_local_shadows_project_import(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "helper.py").write_text("def answer():\n    return 9\n")
    (src / "app.py").write_text(
        "from helper import answer\ndef run():\n    locals()\n    answer = 3\n    return answer\nprint(run())\n"
    )
    ob = CrossFileOrchestrator(ObfuscationConfig())
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    result = subprocess.run([sys.executable, str(out / "app.py")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "3"
    assert "answer = 3" in (out / "app.py").read_text()


def test_same_line_dict_comprehension_lambda_scopes(tmp_path):
    build(
        tmp_path,
        """def run():
    value = 3
    result = {(lambda key: key): (lambda: value) for item in range(1)}
    return [(key(4), val()) for key, val in result.items()]
print(run())
""",
    )


def test_same_line_lambda_default_scope_order(tmp_path):
    build(
        tmp_path,
        """def run():
    value = 3
    callback = lambda arg=(lambda: value), *, keyword=(lambda named: named): (arg(), keyword(4))
    return callback()
print(run())
""",
    )


def test_comprehension_attribute_target_reads_outer(tmp_path):
    build(
        tmp_path,
        """def run():
    class Box:
        pass
    obj = Box()
    result = [obj.value for obj.value in range(3)]
    return result, obj.value
print(run())
""",
    )


def test_skipped_local_project_import_keeps_binding(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "helper.py").write_text("def answer():\n    return 9\n")
    (src / "app.py").write_text(
        "def run():\n    from helper import answer\n    locals()\n    return answer()\nprint(run())\n"
    )
    ob = CrossFileOrchestrator(ObfuscationConfig())
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    result = subprocess.run([sys.executable, str(out / "app.py")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "9"
    assert "as answer" in (out / "app.py").read_text()
