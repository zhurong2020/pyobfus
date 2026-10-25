"""Slice E: real CLI artifacts, trace restoration, guards and failed publication."""

from __future__ import annotations

import base64
import json
import os
import pickle
import subprocess
import sys

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core.delivery_check import check_delivery
from pyobfus.core.mapping import ObfuscationMapping
from pyobfus.core.staged_release import StagedRelease, recover_staging
from pyobfus_pro import crossfile_opacity_build as builder

_REAL_AUTHORIZATION = builder._require_authorization


@pytest.fixture
def project(tmp_path, monkeypatch):
    # Synthetic authorization only: no real license/trial reads or network.
    monkeypatch.setattr(builder, "_require_authorization", lambda: None)
    monkeypatch.setattr("pyobfus.cli.is_trial_active", lambda: True)
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_text(
        '"""Module documentation."""\nfrom __future__ import annotations\n'
        "OFFSET = 3\ndef calculate(value, *, scale=2):\n"
        "    return (value + OFFSET) * scale\n"
        'def crash():\n    raise ValueError("expected")\n',
        encoding="utf-8",
    )
    (source / "b.py").write_text(
        "from a import calculate\ndef run():\n    return calculate(4, scale=3)\n",
        encoding="utf-8",
    )
    opacity = tmp_path / "opacity.toml"
    opacity.write_text('[[rules]]\npattern="a.*"\nlayer="encrypted"\n', encoding="utf-8")
    monkeypatch.setenv("TEST_APP_KEY", base64.b64encode(bytes(range(32))).decode())
    return source, tmp_path / "output", tmp_path / "mapping.json", tmp_path / "report.json", opacity


def build(project, *extra):
    source, output, mapping, report, opacity = project
    return CliRunner().invoke(
        main,
        [
            str(source),
            "-o",
            str(output),
            "--level",
            "pro",
            "--crossfile-opacity",
            "--opacity-config",
            str(opacity),
            "--bind-key-env",
            "TEST_APP_KEY",
            "--jobs",
            "1",
            "--save-mapping",
            str(mapping),
            "--build-report",
            str(report),
            "--keep-docstrings",
            "--json",
            *extra,
        ],
    )


def execute(project, code, *, env=None):
    return subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=project[1],
        env=env or dict(os.environ),
        text=True,
        capture_output=True,
    )


def test_real_cli_build_runs_crossfile_and_restores_saved_mapping(project):
    result = build(project)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "success"
    source, output, private, report, _ = project
    mapping = ObfuscationMapping.load(private)
    run_name = mapping.modules["b"]["run"]
    executed = execute(project, f"import b; print(b.{run_name}())")
    assert executed.returncode == 0, executed.stderr
    assert executed.stdout.strip() == "21"
    failed = execute(project, f"import a; a.{mapping.modules['a']['crash']}()")
    assert failed.returncode == 1
    trace = output.parent / "trace.txt"
    trace.write_text(failed.stderr, encoding="utf-8")
    restored = CliRunner().invoke(
        main, ["--unmap", str(trace), "--mapping", str(private), "--json"]
    )
    assert restored.exit_code == 0, restored.output
    decoded = json.loads(restored.output)
    assert "in crash" in decoded["unmapped_trace"]
    assert any(f["status"] == "name_only" and f["original_line"] is None for f in decoded["frames"])
    assert check_delivery(output, build_report=report)["status"] != "fail"
    data = json.loads(report.read_text())
    assert data["disabled_transforms"] == []
    assert "calculate" not in json.dumps(data)
    assert "calculate" in private.read_text()
    if os.name != "nt":
        assert private.stat().st_mode & 0o777 == 0o600
    assert not list(output.parent.glob(".pyobfus-release-*"))


def test_provider_bootstrap_and_missing_wrong_key_stages(project):
    assert build(project).exit_code == 0
    mapping = ObfuscationMapping.load(project[2])
    name = mapping.modules["a"]["calculate"]
    env = dict(os.environ)
    env.pop("TEST_APP_KEY")
    missing = execute(project, "import a", env=env)
    assert missing.returncode != 0
    provider = execute(
        project,
        "from pyobfus_runtime import set_key_provider; "
        f"set_key_provider(lambda: bytes(range(32))); import a; print(a.{name}(1))",
        env=env,
    )
    assert provider.returncode == 0, provider.stderr
    assert provider.stdout.strip() == "8"
    env["TEST_APP_KEY"] = base64.b64encode(b"x" * 32).decode()
    assert execute(project, "import a", env=env).returncode == 0
    assert execute(project, f"import a; a.{name}(1)", env=env).returncode != 0


def test_missing_completion_manifest_detected_without_private_report(project):
    assert build(project).exit_code == 0
    (project[1] / builder.RELEASE_MANIFEST).unlink()
    checked = check_delivery(project[1])
    assert checked["status"] == "fail"
    assert any(f["code"] == "delivery.l3_build_mismatch" for f in checked["findings"])


def test_guard_precedes_runtime_provider_and_user_imports(project):
    assert build(project).exit_code == 0
    # Change the interpreter magic seen by the guard; a provider side effect
    # would expose an incorrect injection order.
    result = execute(
        project,
        "import importlib.util; importlib.util.MAGIC_NUMBER = b'bad!'; "
        "from pyobfus_runtime import set_key_provider; "
        "set_key_provider(lambda: print('PROVIDER CALLED')); import a",
    )
    assert result.returncode != 0
    assert "pyobfus L3 requires interpreter" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("change", ["mixed", "modified", "missing", "extra", "manifest", "report"])
def test_delivery_rejects_incomplete_or_mixed_build(project, change):
    assert build(project).exit_code == 0
    output, report = project[1], project[3]
    if change == "mixed":
        p = output / "a.py"
        p.write_text(p.read_text().replace("# pyobfus:l3-build ", "# pyobfus:l3-build other-"))
    elif change == "modified":
        with (output / "a.py").open("a") as stream:
            stream.write("\n# changed\n")
    elif change == "missing":
        (output / "b.py").unlink()
    elif change == "extra":
        (output / "extra.py").write_text("print(1)")
    elif change == "manifest":
        (output / builder.RELEASE_MANIFEST).unlink()
    else:
        data = json.loads(report.read_text())
        data["build_id"] = "wrong"
        report.write_text(json.dumps(data))
    checked = check_delivery(output, build_report=report)
    assert checked["status"] == "fail"
    assert any(f["code"] == "delivery.l3_build_mismatch" for f in checked["findings"])


@pytest.mark.parametrize("existing", [1, 2, 3])
def test_existing_release_or_metadata_never_overwritten(project, existing):
    target = project[existing]
    if existing == 1:
        target.mkdir()
        (target / "old.txt").write_text("old release")
    else:
        target.write_text("old metadata")
    result = build(project)
    assert result.exit_code != 0
    assert (
        (target / "old.txt").read_text() == "old release"
        if existing == 1
        else target.read_text() == "old metadata"
    )


def test_late_failure_removes_only_owned_metadata(project, monkeypatch):
    def fail(*args):
        raise OSError("simulated rename failure")

    monkeypatch.setattr("pyobfus.core.staged_release._rename_new", fail)
    result = build(project)
    assert result.exit_code != 0
    assert not any(p.exists() for p in project[1:4])
    assert not list(project[0].parent.glob(".pyobfus-release-*"))


def test_raced_empty_output_never_replaced(project, monkeypatch):
    from pyobfus.core.staged_release import _rename_new

    def race(source, destination):
        destination.mkdir()
        _rename_new(source, destination)

    monkeypatch.setattr("pyobfus.core.staged_release._rename_new", race)
    result = build(project)
    assert result.exit_code != 0
    assert project[1].is_dir()
    assert not list(project[1].iterdir())
    assert not project[2].exists()


def test_crash_recovery_retains_unowned_metadata(tmp_path):
    output, private = tmp_path / "out", tmp_path / "private.json"
    stage = StagedRelease(output, {"mapping.json": private}, "build")
    (stage.root / "mapping.json").write_text("owned")
    os.link(stage.root / "mapping.json", private)
    private.unlink()
    private.write_text("different owner")
    recover_staging(stage.root)
    assert private.read_text() == "different owner"
    assert not stage.root.exists()


@pytest.mark.parametrize(
    "text",
    [
        "async def bad():\n    return 1\n",
        "class C:\n    def bad(self):\n        return 1\n",
        "if True:\n    def bad():\n        return 1\n",
        "def bad():\n    return 1\nbad = 2\n",
        "from pyobfus_pro import opacity\ndef bad():\n    return 1\n",
    ],
)
def test_requested_unsupported_targets_fail_before_publication(project, text):
    (project[0] / "a.py").write_text(text)
    result = build(project)
    assert result.exit_code != 0
    assert not project[1].exists()
    assert not project[2].exists()


def test_dry_run_does_not_publish(project):
    result = build(project, "--dry-run")
    assert result.exit_code == 0, result.output
    assert not any(p.exists() for p in project[1:4])


def test_unauthorized_yaml_build_cannot_publish(project, monkeypatch):
    # Real authorization against pytest-isolated empty state, not a fake error.
    monkeypatch.setattr(builder, "_require_authorization", _REAL_AUTHORIZATION)
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    result = build(project)
    assert result.exit_code != 0
    assert not project[1].exists()


def test_build_key_redacted_and_unpickleable():
    key = builder._BuildKey(b"s" * 32)
    assert "ssss" not in repr(key)
    with pytest.raises(TypeError):
        pickle.dumps(key)


def test_runtime_only_public_install(project):
    target_python = os.environ.get("PYOBFUS_L3_RUNTIME_PYTHON")
    if not target_python:
        pytest.skip("Set PYOBFUS_L3_RUNTIME_PYTHON to a clean public-runtime-only environment")
    assert build(project).exit_code == 0
    mapping = ObfuscationMapping.load(project[2])
    name = mapping.modules["b"]["run"]
    env = dict(os.environ)
    env.pop("TEST_APP_KEY")
    result = subprocess.run(
        [
            target_python,
            "-I",
            "-B",
            "-c",
            "import sys, importlib.util, importlib.metadata; "
            "assert importlib.util.find_spec('pyobfus') is None; "
            "assert importlib.util.find_spec('pyobfus_pro') is None; "
            "assert importlib.util.find_spec('pyobfus_mcp') is None; "
            "assert importlib.metadata.version('pyobfus-runtime') == '0.1.1'; "
            "from pyobfus_runtime import set_key_provider; "
            "set_key_provider(lambda: bytes(range(32))); "
            f"sys.path.insert(0, {str(project[1])!r}); import b; print(b.{name}())",
        ],
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "21"


def test_relative_reexport_same_names_and_comprehensions(project):
    source = project[0]
    package = source / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("from .left import compute\n__all__ = ['compute']\n")
    (package / "left.py").write_text(
        "from .right import compute as other\ndef compute(n):\n"
        "    return sum([other(x) for x in range(n)])\n"
    )
    (package / "right.py").write_text("def compute(n):\n    return (lambda x: x * 2)(n)\n")
    project[4].write_text('[[rules]]\npattern="pkg.*"\nlayer="encrypted"\n')
    result = build(project)
    assert result.exit_code == 0, result.output
    mapping = ObfuscationMapping.load(project[2])
    final = mapping.modules["pkg.left"]["compute"]
    executed = execute(project, f"import pkg; print(pkg.{final}(4))")
    assert executed.returncode == 0, executed.stderr
    assert executed.stdout.strip() == "12"
    assert len(mapping.encrypted_code) == 2


def test_ordinary_l3_module_frames_and_unknown_build_are_never_guessed(project):
    project[4].write_text('[[rules]]\npattern="a.calculate"\nlayer="encrypted"\n')
    assert build(project).exit_code == 0
    mapping = ObfuscationMapping.load(project[2])
    name = mapping.modules["a"]["crash"]
    failed = execute(project, f"import a; a.{name}()")
    restored = mapping.unmap_trace(failed.stderr)
    assert f"in {name}" in restored["unmapped_trace"]
    unknown = f'  File "<pyobfus-l3:wrong:a.py>", line 1, in {name}\n'
    assert mapping.unmap_trace(unknown)["unmapped_trace"] == unknown


def test_failure_during_second_metadata_commit_recovers_first(project, monkeypatch):
    original = os.link
    calls = 0

    def fail_second(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated metadata failure")
        return original(source, destination)

    monkeypatch.setattr("pyobfus.core.staged_release.os.link", fail_second)
    assert build(project).exit_code != 0
    assert not any(p.exists() for p in project[1:4])


def test_fresh_spawn_registers_provider_in_child(project):
    assert build(project).exit_code == 0
    mapping = ObfuscationMapping.load(project[2])
    name = mapping.modules["a"]["calculate"]
    bootstrap = project[0].parent / "bootstrap.py"
    bootstrap.write_text(
        "import sys\nfrom multiprocessing import get_context\n"
        f"sys.path.insert(0, {str(project[1])!r})\n"
        "def worker(queue):\n"
        "    from pyobfus_runtime import set_key_provider\n"
        "    set_key_provider(lambda: bytes(range(32)))\n"
        f"    import a\n    queue.put(a.{name}(1))\n"
        "if __name__ == '__main__':\n"
        "    context = get_context('spawn')\n    queue = context.Queue()\n"
        "    child = context.Process(target=worker, args=(queue,))\n"
        "    child.start()\n    child.join(15)\n"
        "    assert child.exitcode == 0\n    print(queue.get(timeout=5))\n"
    )
    env = dict(os.environ)
    env.pop("TEST_APP_KEY")
    result = subprocess.run(
        [sys.executable, "-B", str(bootstrap)], env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "8"


def test_unproved_module_attributes_fail_without_publishing(project):
    (project[0] / "b.py").write_text(
        "import a\ndef run():\n    return a.calculate(4)\n"
        "def change():\n    a.calculate = lambda n: n\n"
    )
    result = build(project)
    assert result.exit_code != 0
    assert "unproved project module attribute" in result.output
    assert not project[1].exists()


def test_direct_module_attribute_call(project):
    (project[0] / "b.py").write_text("import a\ndef run():\n    return a.calculate(4, scale=3)\n")
    result = build(project)
    assert result.exit_code == 0, result.output
    name = ObfuscationMapping.load(project[2]).modules["b"]["run"]
    run = execute(project, f"import b; print(b.{name}())")
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "21"
