"""Final-artifact provenance, exercised using real CPython tracebacks."""

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from pyobfus.core.line_map import build_line_map, mark_source_statements
from pyobfus.core.mapping import ObfuscationMapping

FRAME = re.compile(r'File "([^"]+)", line (\d+), in (.+)')

APP = '''#!/usr/bin/env python3
# coding: utf-8
"""Module documentation.
More documentation.
"""

# Plenty of comments and whitespace.
def compute_total():
    """Function documentation.
    """
    return check_value(
        1,
        0,
    )

def check_value(left, right):
    """Another docstring."""
    label = """multiline
    string"""
    return left / right



if __name__ == "__main__":
    compute_total()
'''


def run(args, tmp_path):
    # Generated artifacts and CLI subprocesses never consult real user state.
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    return subprocess.run(
        [sys.executable, *map(str, args)], env=env, text=True, capture_output=True
    )


def build(tmp_path, source, flags=()):
    app = tmp_path / "app.py"
    out = tmp_path / "out.py"
    mapping = tmp_path / "mapping.json"
    app.write_text(source)
    result = run(["-m", "pyobfus", app, "-o", out, "--save-mapping", mapping, *flags], tmp_path)
    assert result.returncode == 0, result.stderr + result.stdout
    return app, out, mapping, ObfuscationMapping.load(mapping)


def frames(result):
    assert result.returncode != 0
    return [(path, int(line), name) for path, line, name in FRAME.findall(result.stderr)]


@pytest.mark.parametrize("keep", [False, True])
@pytest.mark.parametrize("marker", [False, True])
@pytest.mark.parametrize("community", [False, True])
def test_actual_single_file_frames(tmp_path, keep, marker, community):
    flags = ["--keep-docstrings" if keep else "--remove-docstrings"]
    if marker:
        flags += ["--trace-marker"]
    if not community:
        flags += ["--no-community-marker"]
    app, out, path, mapping = build(tmp_path, APP, flags)
    original_tree = ast.parse(APP)
    mark_source_statements(original_tree)
    reference = ObfuscationMapping()
    reference.files[app.name] = build_line_map(original_tree, APP, app.name, "app")
    original = frames(run([app], tmp_path))
    obfuscated = frames(run([out], tmp_path))
    assert len(original) == len(obfuscated) == 3
    for (src_path, src_line, _), (obf_path, obf_line, _) in zip(original, obfuscated):
        expected = reference.resolve_location(src_path, src_line)
        actual = mapping.resolve_location(obf_path, obf_line)
        assert actual is not None and expected is not None
        assert (actual.source, actual.line, actual.status) == (app.name, expected.line, "mapped")
    payload = json.loads(path.read_text())
    assert payload["version"] == 1
    assert mapping.marker_id() == payload["marker_id"]
    assert str(tmp_path) not in json.dumps(payload["files"])
    # PR1 leaves name-only CLI presentation intact.
    trace = tmp_path / "trace.txt"
    trace.write_text(run([out], tmp_path).stderr)
    restored = run(["-m", "pyobfus", "--unmap", "--trace", trace, "--mapping", path], tmp_path)
    assert str(out) in restored.stdout


@pytest.mark.parametrize(
    "body",
    [
        "return (lambda: 1 / 0)()",
        "return [1 / n for n in [0]]",
        "def nested():\n            return 1 / 0\n        return nested()",
    ],
)
def test_method_nested_lambda_comprehension(tmp_path, body):
    source = "class Example:\n    def method(self):\n        " + body + "\nExample().method()\n"
    app, out, _, mapping = build(tmp_path, source)
    tree = ast.parse(source)
    mark_source_statements(tree)
    reference = ObfuscationMapping()
    reference.files[app.name] = build_line_map(tree, source, app.name, "app")
    original = frames(run([app], tmp_path))
    emitted = frames(run([out], tmp_path))
    assert len(original) == len(emitted)
    for (src_path, src_line, _), (obf_path, obf_line, _) in zip(original, emitted):
        assert (
            mapping.resolve_location(obf_path, obf_line).line
            == reference.resolve_location(src_path, src_line).line
        )


def test_encoded_helper_is_generated(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("obfuscation:\n  string_encoding: true\n")
    _, out, _, mapping = build(
        tmp_path, 'def fail():\n    return "hello"\nfail()\n', ["--config", config]
    )
    tree = ast.parse(out.read_text())
    helpers = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert len(helpers) >= 2
    for node in ast.walk(helpers[0]):
        if isinstance(node, ast.stmt):
            location = mapping.resolve_location(str(out), node.lineno)
            assert location.status == "generated" and location.line is None
    # Break helper dependencies to obtain a real helper traceback.
    helper = helpers[0]
    arg = helper.args.args[0].arg
    execution = run(
        ["-c", f"exec(compile({out.read_text()!r}, {str(out)!r}, 'exec')); {helper.name}(None)"],
        tmp_path,
    )
    helper_frames = [(p, n) for p, n, _ in frames(execution) if p == str(out)]
    assert helper_frames, arg
    assert mapping.resolve_location(*helper_frames[-1]).status == "generated"


DIRECTORY = {
    "main.py": "from pkg.core import divide\n\ndef invoke():\n    # Multiline call.\n    return divide(\n        1,\n        0,\n    )\n\n\ninvoke()\n",
    "pkg/__init__.py": "",
    "pkg/identity.py": "def identity(value):\n    return value\n",
    "pkg/core.py": '''from functools import wraps
from .identity import identity


def logged(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@logged
def divide(left, right):
    """Documentation.
    More documentation."""
    return identity(left) / right
''',
    "a/util.py": "def value():\n    return 1\n",
    "b/util.py": "def value():\n    return 2\n",
}


@pytest.mark.parametrize("trace_marker", [False, True])
def test_directory_parallel_and_paths(tmp_path, trace_marker):
    from pyobfus.config import ObfuscationConfig
    from pyobfus.core.orchestrator import CrossFileOrchestrator

    source = tmp_path / "proj"
    source.mkdir()
    for name, text in DIRECTORY.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    records = []
    for workers in (1, 2):
        out = tmp_path / f"out{workers}"
        orchestrator = CrossFileOrchestrator(ObfuscationConfig(max_workers=workers))
        orchestrator.phase1_scan(source)
        assert not orchestrator.phase2_transform(source, out)
        mapping = ObfuscationMapping.from_global_table(orchestrator.global_table)
        mapping.files = orchestrator.file_line_maps
        if trace_marker:
            from pyobfus.cli import _apply_trace_markers

            mapping_path = tmp_path / f"mapping{workers}.json"
            mapping.save(mapping_path)
            marker = mapping.marker_id()
            assert _apply_trace_markers(out, str(mapping_path)) == marker
            first = mapping_path.read_bytes()
            assert _apply_trace_markers(out, str(mapping_path)) == marker
            assert mapping_path.read_bytes() == first
            mapping = ObfuscationMapping.load(mapping_path)
        records.append(mapping.files)
        original = frames(run([source / "main.py"], tmp_path))
        emitted = frames(run([out / "main.py"], tmp_path))
        assert len(original) == len(emitted) == 4
        for (src_path, src_line, _), (obf_path, obf_line, _) in zip(original, emitted):
            rel = Path(src_path).relative_to(source).as_posix()
            tree = ast.parse(DIRECTORY[rel])
            mark_source_statements(tree)
            reference = ObfuscationMapping()
            reference.files[rel] = build_line_map(tree, DIRECTORY[rel], rel, "")
            actual = mapping.resolve_location(obf_path, obf_line)
            assert (actual.source, actual.line) == (
                rel,
                reference.resolve_location(rel, src_line).line,
            )
        assert (
            mapping.resolve_location("C:\\app\\pkg\\core.py", emitted[-1][1]).source
            == "pkg/core.py"
        )
        assert mapping.resolve_location("util.py", 5) is None
        assert (
            mapping.resolve_location("/deployed/a/util.py", 9 if trace_marker else 5).source
            == "a/util.py"
        )
    assert records[0] == records[1]


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("mode", ["independent_directory", "crossfile_directory", "single_file"])
def test_mapping_save_modes(tmp_path, json_output, mode):
    source = tmp_path / "src"
    fixture = {
        "main.py": "def run():\n    return 1 / 0\nrun()\n",
        "app/a/util.py": "def parse_amount():\n    return 1\n",
        "app/b/util.py": "def scaled():\n    return 2\n",
    }
    for name, text in fixture.items():
        file = source / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
    single = mode == "single_file"
    independent = mode == "independent_directory"
    input_path = source / "main.py" if single else source
    out = tmp_path / ("out.py" if single else "out")
    path = tmp_path / "mapping.json"
    flags = [] if mode == "crossfile_directory" else ["--no-cross-file"]
    if json_output:
        flags.append("--json")
    result = run(["-m", "pyobfus", input_path, "-o", out, "--save-mapping", path, *flags], tmp_path)
    assert result.returncode == 0, result.stderr + result.stdout
    warning = (
        "--save-mapping is not supported for --no-cross-file directory builds: "
        "each file is renamed independently, so names collide; no mapping was written."
    )
    assert (warning in result.stderr) == independent
    assert path.exists() != independent
    if json_output:
        payload = json.loads(result.stdout)
        assert payload["status"] == "success"
        if independent:
            assert payload["warning"] == warning
            assert warning in payload["stats"]["warnings"]
            assert payload["mapping"] is None
        else:
            assert "warning" not in payload
            assert payload["mapping"] == str(path)
    if independent:
        # Show the actual collision which makes a combined name table unsafe.
        names = []
        for name in fixture:
            tree = ast.parse((out / name).read_text())
            names.append(next(node.name for node in tree.body if isinstance(node, ast.FunctionDef)))
        assert names == ["I0", "I0", "I0"]
    else:
        mapping = ObfuscationMapping.load(path)
        assert set(mapping.files) == ({"out.py"} if single else set(fixture))
    # Both directory modes and the single-file mode still produce runnable output.
    trace = frames(run([out if single else out / "main.py"], tmp_path))
    assert len(trace) == 2
    if not independent:
        assert mapping.resolve_location(trace[-1][0], trace[-1][1]).line == 2


def test_alignment_unavailable_and_legacy(tmp_path):
    tree = ast.parse("x = 1\n")
    mark_source_statements(tree)
    failed = build_line_map(tree, "pass\n", "app.py", "app")
    assert failed["lines"] is None and "mismatch" in failed["reason"]
    assert (
        build_line_map(tree, "x = 1", "app.py", "app", "Pro fusion text passes enabled")["lines"]
        is None
    )
    mapping = ObfuscationMapping.from_single_file({"function": "I0"})
    marker = mapping.marker_id()
    mapping.files["out.py"] = failed
    assert mapping.marker_id() == marker
    path = tmp_path / "map.json"
    mapping.save(path)
    assert ObfuscationMapping.load(path).resolve_location("out.py", 1) is None
    payload = json.loads(path.read_text())
    payload.pop("files")
    path.write_text(json.dumps(payload))
    legacy = ObfuscationMapping.load(path)
    assert legacy.unmap_text("I0()") == "function()"
    assert legacy.resolve_location("out.py", 1) is None


def test_malformed_and_unknown_optional_metadata(tmp_path):
    mapping = ObfuscationMapping.from_single_file({"function": "I0"})
    mapping.files["out.py"] = {
        "source": "/private/source.py",
        "module": "",
        "lines": [[1, 1]],
        "line_count": 1,
    }
    path = tmp_path / "mapping.json"
    mapping.save(path)
    assert ObfuscationMapping.load(path).files == {}
    payload = json.loads(path.read_text())
    payload["files"]["line_map_version"] = 99
    path.write_text(json.dumps(payload))
    assert ObfuscationMapping.load(path).unmap_text("I0") == "function"


def test_marker_after_shebang_encoding_prologue(tmp_path):
    from pyobfus.cli import _apply_trace_markers

    text = "#!/usr/bin/python3\n# coding: utf-8\nx = 1\n"
    tree = ast.parse(text)
    mark_source_statements(tree)
    mapping = ObfuscationMapping()
    mapping.files["out.py"] = build_line_map(tree, text, "app.py", "app")
    out = tmp_path / "out.py"
    path = tmp_path / "mapping.json"
    out.write_text(text)
    mapping.save(path)
    _apply_trace_markers(out, str(path))
    restored = ObfuscationMapping.load(path)
    assert out.read_text().splitlines()[:2] == text.splitlines()[:2]
    assert restored.resolve_location("out.py", 7).line == 3
    assert restored.resolve_location("out.py", 3).status == "generated"
    assert restored.resolve_location("out.py", 8) is None


def test_real_061_fixture(tmp_path):
    path = Path(__file__).parents[1] / "fixtures" / "mapping_061.json"
    mapping = ObfuscationMapping.load(path)
    assert mapping.pyobfus_version == "0.6.1"
    assert not mapping.files
    assert mapping.reverse("I1") == "compute_total"
    _, out, _, _ = build(tmp_path, APP)
    trace = tmp_path / "trace.txt"
    trace.write_text(run([out], tmp_path).stderr)
    restored = run(["-m", "pyobfus", "--unmap", "--trace", trace, "--mapping", path], tmp_path)
    assert restored.returncode == 0
    assert "in compute_total" in restored.stdout
    assert "in check_value" in restored.stdout


def test_encoded_user_frames(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("obfuscation:\n  string_encoding: true\n")
    _, out, _, mapping = build(tmp_path, APP, ["--config", config, "--trace-marker"])
    emitted = frames(run([out], tmp_path))
    assert [mapping.resolve_location(path, line).line for path, line, _ in emitted] == [25, 11, 20]


def test_fusion_boundary_disables_locations(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    import pyobfus.cli as cli
    from pyobfus.config import ObfuscationConfig

    # Exercise the actual save path without invoking a proprietary mechanism.
    monkeypatch.setattr(
        cli,
        "_build_fusion",
        SimpleNamespace(
            fusion_enabled=lambda config: True,
            apply_pre_passes=lambda text, config, **kwargs: text,
            apply_post_passes=lambda text, config, **kwargs: text + "\n# post pass\n",
            assignments_summary=lambda text: (0, 0),
        ),
    )
    app = tmp_path / "app.py"
    out = tmp_path / "out.py"
    path = tmp_path / "mapping.json"
    app.write_text("def fail():\n    return 1 / 0\nfail()\n")
    cli._obfuscate_file(app, out, ObfuscationConfig(level="pro"), True, save_mapping_path=str(path))
    record = ObfuscationMapping.load(path).files[out.name]
    assert record["lines"] is None
    assert record["reason"] == "Pro fusion text passes enabled"
    assert "Line map unavailable" in capsys.readouterr().out
    assert len(frames(run([out], tmp_path))) == 2


def test_new_metadata_does_not_change_names(tmp_path):
    from pyobfus.core.analyzer import SymbolAnalyzer
    from pyobfus.config import ObfuscationConfig
    from pyobfus.transformers.name_mangler import NameMangler

    _, _, _, mapping = build(tmp_path, APP)
    tree = ast.parse(APP)
    config = ObfuscationConfig()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)
    mangler = NameMangler(config, analyzer)
    mangler.transform(tree)
    before = ObfuscationMapping.from_single_file(mangler.get_name_mapping(), module="app")
    assert before.modules == mapping.modules
    assert before.global_map == mapping.global_map
    assert before.marker_id() == mapping.marker_id()
