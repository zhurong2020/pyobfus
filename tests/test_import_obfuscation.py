"""Tests for Pro import obfuscation (P2-4)."""

import ast
import importlib.util
import sys
from unittest.mock import patch

from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus_pro.import_obfuscation import ImportObfuscator


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(name, None)


def test_import_obfuscator_rewrites_top_level_imports_and_preserves_semantics():
    source = '''"""module docstring"""
from __future__ import annotations
import math
import json as js
from pathlib import Path as P
from os import path

def run() -> tuple[float, str, str]:
    return math.sqrt(9), js.dumps({"x": 1}), path.basename(str(P("a/b")))
'''
    tree = ast.parse(source)
    transformer = ImportObfuscator()

    transformed = transformer.transform(tree)
    output = ast.unparse(transformed)
    ns = {}
    exec(compile(output, "<import-obfuscation-test>", "exec"), ns)

    assert ns["run"]() == (3.0, '{"x": 1}', "b")
    assert "import math" not in output
    assert "import json as js" not in output
    assert "from pathlib import Path" not in output
    assert "from os import path" not in output
    assert "import importlib as _pyobfus_importlib" in output
    assert transformer.get_statistics()["imports_obfuscated"] == 4


def test_import_obfuscator_skips_relative_future_and_star_imports():
    source = "from __future__ import annotations\nfrom . import local\nfrom math import *\n"
    tree = ast.parse(source)
    transformer = ImportObfuscator()

    output = ast.unparse(transformer.transform(tree))

    assert "from __future__ import annotations" in output
    assert "from . import local" in output
    assert "from math import *" in output
    assert "_pyobfus_importlib" not in output
    assert transformer.get_statistics()["imports_obfuscated"] == 0


def test_cli_import_obfuscation_encrypts_import_strings(tmp_path):
    src = tmp_path / "sample.py"
    out = tmp_path / "out.py"
    src.write_text(
        "import math\n"
        "from os import path\n\n"
        "def run():\n"
        "    return math.sqrt(16), path.basename('a/b')\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    with patch("pyobfus.cli.is_trial_active", return_value=True):
        result = runner.invoke(
            main,
            [str(src), "-o", str(out), "--level", "pro", "--import-obfuscation", "--stats"],
        )

    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "import math" not in text
    assert "from os import path" not in text
    assert "_pyobfus_importlib.import_module" in text
    assert "_decrypt_str(" in text
    assert "'math'" not in text and '"math"' not in text
    assert "'os'" not in text and '"os"' not in text
    assert "Imports obfuscated:" in result.output

    module = _load_module(out, "import_obfuscation_cli_out")
    assert module.I0() == (4.0, "b")


def test_cli_import_obfuscation_preserves_future_import_position(tmp_path):
    src = tmp_path / "sample_future.py"
    out = tmp_path / "out_future.py"
    src.write_text(
        '"""sample module"""\n'
        "from __future__ import annotations\n"
        "import math\n\n"
        "def run() -> float:\n"
        "    return math.sqrt(25)\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    with patch("pyobfus.cli.is_trial_active", return_value=True):
        result = runner.invoke(
            main,
            [str(src), "-o", str(out), "--level", "pro", "--import-obfuscation"],
        )

    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert text.index("from __future__ import annotations") < text.index("_ENCRYPTION_KEY")
    compile(text, str(out), "exec")

    module = _load_module(out, "import_obfuscation_future_out")
    assert module.I0() == 5.0
