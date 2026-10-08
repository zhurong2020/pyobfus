"""Single-file artifacts retain names used by endpoint/command registries."""

import ast
import os
import subprocess
import sys

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.transformers.name_mangler import NameMangler

MINIMAL = """import click
REG = {}
def register(f):
    REG[f.__name__] = f
    return f
def build():
    @register
    def index():
        return "home"
    @click.group()
    def cli():
        pass
    @cli.command()
    def hello():
        click.echo("hi")
    return cli
build()(["hello"], standalone_mode=False)
print(sorted(REG))
"""

REGISTRY = """REG = {}
def register(f):
    REG[f.__name__] = f
    return f
def build():
    @register
    def index():
        return "home"
    return index
view = build()
print(view.__name__, sorted(REG), REG["index"]())
"""

DATACLASS = """from dataclasses import dataclass
def build():
    @dataclass
    class Point:
        x: int
    return Point(1)
p = build()
print(type(p).__name__, p)
"""

EMPTY_DATACLASS = """from dataclasses import dataclass
def build():
    @dataclass
    class Marker:
        pass
    return Marker()
p = build()
print(type(p).__name__, p)
"""

EXCEPTION = """def build():
    class RequestError(Exception):
        pass
    return RequestError
error = build()
try:
    raise error("bad request")
except error as exc:
    print(type(exc).__name__, str(exc))
"""

ROUTES = """from routes import Router
def create_app():
    app = Router()
    def index():
        return "home"
    app.add_url_rule(view_func=index)
    return app
app = create_app()
print(app.url_for("index"), app.views["index"]())
"""

ASYNC = """import asyncio
async def build():
    async def fetch():
        return "data"
    def regular():
        return "sync"
    class LocalError(Exception):
        pass
    return fetch.__name__, await fetch(), regular.__name__, LocalError.__name__
print(asyncio.run(build()))
"""

PREFIX_COLLISION = """def build():
    def I0():
        return 9
    aaa = 3
    return I0() + aaa
print(build())
"""

FLASK = """from flask import Flask, url_for
def create_app():
    app = Flask(__name__)
    @app.route("/")
    def index():
        return "home"
    def detail():
        return "detail"
    app.add_url_rule("/detail", view_func=detail)
    return app
app = create_app()
with app.test_request_context():
    print(url_for("index"), url_for("detail"))
client = app.test_client()
print(client.get("/").data.decode(), client.get("/detail").data.decode())
"""


def _run(command, tmp_path):
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))
    return subprocess.run(
        command, cwd=tmp_path, env=env, text=True, capture_output=True, timeout=60
    )


def _compare(tmp_path, source, preset, exclusions=(), options=()):
    original = tmp_path / "app.py"
    original.write_text(source)
    (tmp_path / "routes.py").write_text(
        "class Router:\n"
        "    def __init__(self):\n        self.views = {}\n"
        "    def add_url_rule(self, view_func):\n        self.views[view_func.__name__] = view_func\n"
        '    def url_for(self, endpoint):\n        return "/" + endpoint if endpoint in self.views else "missing"\n'
    )
    expected = _run([sys.executable, "app.py"], tmp_path)
    assert expected.returncode == 0, expected.stderr
    command = [sys.executable, "-m", "pyobfus", "app.py", "-o", "out.py"]
    if preset:
        command += ["--preset", preset]
    if exclusions:
        # Isolate the class-name regression; field-name compatibility is an
        # observed, explicitly out-of-scope defect, not silently fixed here.
        config = "obfuscation:\n  exclude_names: [" + ", ".join(exclusions) + "]\n"
        if preset:
            config += "  preset: " + preset + "\n"
        (tmp_path / "config.yml").write_text(config)
        command += ["--config", "config.yml"]
    else:
        command += ["--no-config"]
    command += list(options)
    built = _run(command, tmp_path)
    assert built.returncode == 0, built.stdout + built.stderr
    actual = _run([sys.executable, "out.py"], tmp_path)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout
    return actual.stdout


@pytest.mark.parametrize("preset", [None, "safe", "flask"], ids=["default", "safe", "flask"])
@pytest.mark.parametrize(
    "source,exclusions",
    [
        (MINIMAL, ()),
        (REGISTRY, ()),
        (DATACLASS, ("x", "build")),
        (EMPTY_DATACLASS, ("build",)),
        (EXCEPTION, ()),
        (ROUTES, ()),
        (ASYNC, ()),
        (PREFIX_COLLISION, ()),
    ],
    ids=[
        "click",
        "registry",
        "dataclass-preserved-field",
        "empty-dataclass",
        "exception",
        "add-url-rule",
        "async",
        "prefix-collision",
    ],
)
def test_singlefile_runtime_names(tmp_path, preset, source, exclusions):
    output = _compare(tmp_path, source, preset, exclusions)
    if source == MINIMAL:
        assert output == "hi\n['index']\n"


@pytest.mark.parametrize("preset", [None, "safe", "flask"], ids=["default", "safe", "flask"])
def test_real_flask_factory(tmp_path, preset):
    pytest.importorskip("flask")
    assert _compare(tmp_path, FLASK, preset) == "/ /detail\nhome detail\n"


SCOPE_FIXTURE = """def shared():
    return 1
class SharedClass:
    pass
class Top:
    flag = 1
    def method(self, param):
        def method_inner():
            return param
        return method_inner()
def outer(param):
    temporary = param
    if True:
        def shared():
            return temporary
        async def nested_async():
            return shared()
        class SharedClass:
            flag = 2
            def local_method(self):
                def deep():
                    return 3
                return deep()
            class ClassBodyNested:
                pass
    return shared, SharedClass, nested_async
"""


@pytest.mark.parametrize("analyzed,preserve_params", [(True, True), (True, False), (False, False)])
def test_only_function_parent_definitions_are_preserved(analyzed, preserve_params):
    tree = ast.parse(SCOPE_FIXTURE)
    config = ObfuscationConfig(preserve_param_names=preserve_params)
    config.exclude_names.add("temporary")
    analyzer = SymbolAnalyzer(config) if analyzed else None
    if analyzer:
        analyzer.analyze(tree)
    mangler = NameMangler(config, analyzer)
    transformed = mangler.transform(tree)
    mapping = mangler.get_name_mapping()
    protected = {"shared", "SharedClass", "nested_async", "method_inner", "deep"}
    assert protected.isdisjoint(mapping)
    # The map is file-wide: same-named module definitions also stay unchanged.
    assert transformed.body[0].name == "shared"
    assert transformed.body[1].name == "SharedClass"
    assert "temporary" not in mapping
    for name in {"outer", "Top", "method", "local_method", "flag", "ClassBodyNested"}:
        assert name in mapping, name
    assert ("param" not in mapping) == preserve_params
    if analyzer:
        expected = analyzer.obfuscatable_names - protected
        if preserve_params:
            expected -= analyzer.parameter_names
        assert set(mapping) == expected


@pytest.mark.parametrize("preset", [None, "safe", "flask"], ids=["default", "safe", "flask"])
def test_preserve_param_names_cli(tmp_path, preset):
    source = """def outer(value):
    def nested(item):
        return item + value
    return nested(item=value)
print(outer(value=3))
"""
    assert _compare(tmp_path, source, preset, options=("--preserve-param-names",)) == "6\n"
