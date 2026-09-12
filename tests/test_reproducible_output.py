"""Reproducibility guarantees for generated output.

Why these tests exist
---------------------

0.5.24 shipped `--build-report`, which records a SHA-256 for every generated
file as delivery evidence. A digest is only evidence if somebody else can
rebuild the same input and arrive at the same value. They could not: in
directory / cross-file mode the obfuscated names were assigned by iterating a
`set`, so the interpreter's per-process string hash seed decided which symbol
became `I0`. Two runs of the same input produced different bytes.

`PYTHONHASHSEED` has to be set before the interpreter starts, so these tests
drive the CLI through subprocesses rather than calling the API in-process.

What is deliberately *not* covered: `--numeric-obfuscation` and AES string
encryption draw from a CSPRNG on every run and must keep doing so. The last
test pins that exception so nobody "fixes" it into determinism.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

SEED_A = "0"
SEED_B = "12345"


def _write_project(root: Path) -> Path:
    """Create a small multi-module project with enough exports to permute."""
    src = root / "src"
    (src / "pkg").mkdir(parents=True)

    (src / "alpha.py").write_text(
        "TOLERANCE = 3\n"
        "\n"
        "\n"
        "def collect(items):\n"
        "    gathered = [item for item in items if item]\n"
        "    return gathered\n"
        "\n"
        "\n"
        "def summarise(items):\n"
        "    total = sum(collect(items))\n"
        "    return total\n",
        encoding="utf-8",
    )
    (src / "beta.py").write_text(
        "class Accumulator:\n"
        "    def __init__(self):\n"
        "        self.entries = []\n"
        "\n"
        "    def push(self, value):\n"
        "        self.entries.append(value)\n"
        "        return self\n"
        "\n"
        "\n"
        "def build_accumulator(values):\n"
        "    acc = Accumulator()\n"
        "    for value in values:\n"
        "        acc.push(value)\n"
        "    return acc\n",
        encoding="utf-8",
    )
    (src / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (src / "pkg" / "gamma.py").write_text(
        "SCALE = 7\n"
        "\n"
        "\n"
        "def rescale(value):\n"
        "    adjusted = value * SCALE\n"
        "    return adjusted\n"
        "\n"
        "\n"
        "def describe(value):\n"
        "    label = 'scaled'\n"
        "    return label, rescale(value)\n",
        encoding="utf-8",
    )
    return src


def _build(
    root: Path,
    src: Path,
    out: Path,
    seed: str,
    extra_args: Optional[List[str]] = None,
) -> None:
    """Run the CLI in a child process with a fixed string hash seed."""
    home = root / f"home-{seed}"
    home.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    # Keep the developer's real ~/.pyobfus out of this (AGENTS.md test policy).
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)

    command = [sys.executable, "-m", "pyobfus", str(src), "-o", str(out)]
    command.extend(extra_args or [])
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=180,
        # cwd must not be the repo root: the CLI auto-discovers pyobfus.yaml
        # from the working directory, and a stray config would silently change
        # what this test measures.
        cwd=str(root),
        env=env,
    )
    assert proc.returncode == 0, f"build failed (seed={seed}): {proc.stderr}"


def _tree_bytes(root: Path) -> Dict[str, bytes]:
    """Map each generated file to its content, keyed by path relative to root."""
    return {
        str(path.relative_to(root)).replace(os.sep, "/"): path.read_bytes()
        for path in sorted(root.rglob("*.py"))
    }


class TestCrossFileReproducibility:
    """Directory mode must not depend on the interpreter's hash seed."""

    def test_directory_build_is_byte_identical_across_hash_seeds(self, tmp_path):
        src = _write_project(tmp_path)
        out_a = tmp_path / "out-a"
        out_b = tmp_path / "out-b"

        _build(tmp_path, src, out_a, SEED_A)
        _build(tmp_path, src, out_b, SEED_B)

        tree_a = _tree_bytes(out_a)
        tree_b = _tree_bytes(out_b)

        assert tree_a, "no output was generated"
        assert sorted(tree_a) == sorted(tree_b)
        differing = [name for name in tree_a if tree_a[name] != tree_b[name]]
        assert not differing, f"hash-seed dependent output in: {differing}"

    def test_mapping_content_is_identical_across_hash_seeds(self, tmp_path):
        """Every mapping field but the wall-clock stamp must be reproducible.

        `created_at` is a timestamp and is expected to differ between builds;
        `marker_id` is documented as derived from the name map, so it must not.
        """
        import json

        src = _write_project(tmp_path)
        map_a = tmp_path / "map-a.json"
        map_b = tmp_path / "map-b.json"

        _build(tmp_path, src, tmp_path / "m-a", SEED_A, ["--save-mapping", str(map_a)])
        _build(tmp_path, src, tmp_path / "m-b", SEED_B, ["--save-mapping", str(map_b)])

        loaded_a = json.loads(map_a.read_text(encoding="utf-8"))
        loaded_b = json.loads(map_b.read_text(encoding="utf-8"))
        assert loaded_a.pop("created_at") != ""
        assert loaded_b.pop("created_at") != ""

        assert loaded_a == loaded_b
        assert loaded_a["marker_id"] == loaded_b["marker_id"]

    def test_build_report_output_digests_are_identical_across_hash_seeds(self, tmp_path):
        """The point of the fix: a third party can re-derive the reported digests."""
        import json

        src = _write_project(tmp_path)
        report_a = tmp_path / "report-a.json"
        report_b = tmp_path / "report-b.json"

        _build(tmp_path, src, tmp_path / "r-a", SEED_A, ["--build-report", str(report_a)])
        _build(tmp_path, src, tmp_path / "r-b", SEED_B, ["--build-report", str(report_b)])

        digests_a = {
            record["path"]: record["sha256"]
            for record in json.loads(report_a.read_text(encoding="utf-8"))["outputs"]["files"]
        }
        digests_b = {
            record["path"]: record["sha256"]
            for record in json.loads(report_b.read_text(encoding="utf-8"))["outputs"]["files"]
        }

        assert digests_a == digests_b


class TestSingleFileReproducibility:
    """Single-file mode already sorted its names; keep it that way."""

    def test_single_file_build_is_byte_identical_across_hash_seeds(self, tmp_path):
        src = _write_project(tmp_path)
        target = src / "alpha.py"
        out_a = tmp_path / "alpha-a.py"
        out_b = tmp_path / "alpha-b.py"

        _build(tmp_path, target, out_a, SEED_A)
        _build(tmp_path, target, out_b, SEED_B)

        assert out_a.read_bytes() == out_b.read_bytes()


class TestDiscoveryOrder:
    """File discovery feeds name assignment, the cache signature and manifests."""

    def test_filter_python_files_returns_sorted_paths(self, tmp_path):
        from pyobfus.utils import filter_python_files

        for name in ("zeta.py", "alpha.py", "middle.py"):
            (tmp_path / name).write_text("value = 1\n", encoding="utf-8")
        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "inner.py").write_text("value = 2\n", encoding="utf-8")

        found = filter_python_files(tmp_path, [])

        assert found == sorted(found)


class TestDocumentedNonDeterminism:
    """Randomised transforms must stay randomised; this pins the exception."""

    def test_numeric_obfuscation_is_deliberately_not_reproducible(self, tmp_path):
        # The fixture carries three integer literals. Each is rewritten with a
        # CSPRNG strategy choice plus a 32-bit mask, so two runs colliding on
        # all three is far below any threshold that could make this flaky.
        src = tmp_path / "src"
        src.mkdir()
        (src / "numbers.py").write_text(
            "FIRST = 11\nSECOND = 2244\nTHIRD = 990011\n",
            encoding="utf-8",
        )
        out_a = tmp_path / "num-a"
        out_b = tmp_path / "num-b"

        _build(tmp_path, src, out_a, SEED_A, ["--numeric-obfuscation"])
        _build(tmp_path, src, out_b, SEED_A, ["--numeric-obfuscation"])

        assert (out_a / "numbers.py").read_bytes() != (out_b / "numbers.py").read_bytes()
