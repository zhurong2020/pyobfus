"""Community hooks share delivery detection without exposing private contents."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from pyobfus import precommit

ROOT = Path(__file__).resolve().parents[1]
MAPPING = {"pyobfus_version": "0.12.0", "global": {"private_original": "renamed"}}
KEY_BODY = "synthetic-key-body-never-display"


@pytest.mark.parametrize("json_mode", [False, True])
@pytest.mark.parametrize("kind", ["clean", "mapping", "private_key", "missing", "directory"])
def test_module(tmp_path, kind, json_mode):
    path = tmp_path / ("map.json" if kind == "mapping" else "arbitrary.dat")
    content = {
        "clean": "print('no execution')",
        "mapping": json.dumps(MAPPING),
        "private_key": "-----BEGIN " + "PRIVATE KEY-----\n" + KEY_BODY,
    }.get(kind)
    if content is not None:
        path.write_text(content)
    if kind == "directory":
        path.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "pyobfus.precommit", *(["--json"] if json_mode else []), str(path)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    expected = 1 if kind in ("mapping", "private_key") else 0
    assert result.returncode == expected
    assert KEY_BODY not in result.stdout + result.stderr
    assert "private_original" not in result.stdout + result.stderr
    if json_mode:
        payload = json.loads(result.stdout)
        assert set(payload) == {"version", "status", "findings", "ai_hint"}
        assert payload["version"] == 1
        assert payload["status"] == {0: "clean", 1: "findings", 2: "error"}[expected]
        assert payload["ai_hint"]
        assert result.stderr == ""
        if expected == 1:
            assert payload["findings"] == [
                {"path": str(path), "kind": kind, "message": payload["findings"][0]["message"]}
            ]
        else:
            assert payload["findings"] == []
    elif expected == 1:
        assert str(path) in result.stdout
        assert len(result.stdout.splitlines()) == 1


def test_io_error_retains_findings(tmp_path, monkeypatch, capsys):
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps(MAPPING))
    unreadable = tmp_path / "unreadable"
    unreadable.touch()
    original = os.open

    def guarded_open(self, *args, **kwargs):
        if Path(self) == unreadable:
            raise PermissionError(KEY_BODY)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(os, "open", guarded_open)
    assert precommit.main(["--json", str(unreadable), str(mapping)]) == 2
    output = capsys.readouterr()
    assert KEY_BODY not in output.out + output.err
    payload = json.loads(output.out)
    assert payload["status"] == "error"
    assert payload["findings"][0]["kind"] == "mapping"


def test_usage_error(capsys):
    assert precommit.main(["--json", "--unknown"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "error"


def test_empty_arguments(capsys):
    assert precommit.main([]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("key", [False, True])
def test_large_json_only_reads_head(tmp_path, monkeypatch, capsys, key):
    monkeypatch.setattr(precommit, "_MAX_JSON_BYTES", 128)
    monkeypatch.setattr(precommit, "_PRIVATE_KEY_HEAD_BYTES", 64)
    path = tmp_path / "large.json"
    data = ("-----BEGIN " + "PRIVATE KEY-----\n") if key else json.dumps(MAPPING)
    path.write_text(data + " " * 1024)

    def unexpected_mapping(entry):
        pytest.fail("Oversized JSON must not be checked as a mapping")

    monkeypatch.setattr(precommit, "_is_mapping", unexpected_mapping)
    original = precommit._is_private_key

    def check_head(entry):
        assert len(entry.data) == 64
        return original(entry)

    monkeypatch.setattr(precommit, "_is_private_key", check_head)
    assert precommit.main(["--json", str(path)]) == (1 if key else 0)
    assert json.loads(capsys.readouterr().out)["status"] == ("findings" if key else "clean")


def test_key_beyond_head_is_not_detected(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(precommit, "_PRIVATE_KEY_HEAD_BYTES", 64)
    path = tmp_path / "file.pem"
    path.write_text(" " * 65 + "-----BEGIN " + "PRIVATE KEY-----\n")
    assert precommit.main([str(path)]) == 0
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("target_exists", [False, True])
def test_symlink_skipped_without_reading(tmp_path, monkeypatch, capsys, target_exists):
    target = tmp_path / "map.json"
    if target_exists:
        target.write_text(json.dumps(MAPPING))
    path = tmp_path / "link.json"
    try:
        path.symlink_to(target)
    except OSError:
        pytest.skip("Symlinks unavailable")

    def unexpected_open(*args, **kwargs):
        pytest.fail("Symlinks must not be opened")

    monkeypatch.setattr(os, "open", unexpected_open)
    assert precommit.main([str(path)]) == 0
    assert capsys.readouterr() == ("", "")


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_fifo_skipped(tmp_path, capsys):
    path = tmp_path / "pipe"
    os.mkfifo(path)
    assert precommit.main([str(path)]) == 0
    assert capsys.readouterr() == ("", "")


def test_manifest():
    hooks = yaml.safe_load((ROOT / ".pre-commit-hooks.yaml").read_text())
    by_id = {hook["id"]: hook for hook in hooks}
    assert set(by_id) == {"pyobfus-no-private-material", "pyobfus-check-delivery"}
    private = by_id["pyobfus-no-private-material"]
    assert private["entry"] == "python -m pyobfus.precommit"
    assert private["pass_filenames"] is True
    assert not any(key in private for key in ("types", "types_or", "files"))
    delivery = by_id["pyobfus-check-delivery"]
    assert delivery["entry"] == "pyobfus --check-delivery"
    assert delivery["pass_filenames"] is False
    assert delivery["always_run"] is True
    assert delivery["stages"] == ["pre-push", "manual"]
    assert "args:" in delivery["description"]
    assert all(hook["language"] == "python" for hook in hooks)


@pytest.fixture
def maintainer_hook(tmp_path, monkeypatch):
    """Run the real shell hook with read-only Git calls over synthetic blobs.

    The shim supplies index reads without creating a repository or staging files;
    matching uses real `git grep --no-index`, including its ERE semantics.
    """
    import shutil

    git = shutil.which("git")
    if not git or not shutil.which("bash"):
        pytest.skip("Maintainer hooks require Git and Bash")
    for key in (
        "PYOBFUS_ALLOW_PII",
        "PYOBFUS_ALLOW_SECRET",
        "PYOBFUS_ALLOW_CUSTOMER_DATA",
        "PYOBFUS_PII_PATTERNS_FILE",
    ):
        monkeypatch.delenv(key, raising=False)
    main = tmp_path / "main checkout"
    common = main / "common-dir"
    common.mkdir(parents=True)
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    patterns = main / "docs/internal/pii-patterns.txt"
    patterns.parent.mkdir(parents=True)
    patterns.write_text("# Synthetic identifiers only\n\nPIITESTTOKEN\n")
    monkeypatch.setenv("PYOBFUS_PII_PATTERNS_FILE", str(patterns))
    monkeypatch.setenv("HOOK_COMMON_DIR", str(common))
    monkeypatch.setenv("HOOK_REAL_GIT", git)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "git"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "files = json.loads(os.environ['HOOK_STAGED_FILES'])\n"
        "if args == ['rev-parse', '--git-common-dir']:\n"
        "    print(os.environ['HOOK_COMMON_DIR'])\n"
        "elif args[:3] == ['diff', '--cached', '--name-only']:\n"
        "    print('\\n'.join(files))\n"
        "elif args[:2] == ['grep', '--cached']:\n"
        "    git = os.environ['HOOK_REAL_GIT']\n"
        "    os.execv(git, [git, 'grep', '--no-index', *args[2:]])\n"
        "elif args[:3] == ['diff', '--cached', '-U0']:\n"
        "    from pathlib import Path\n"
        "    for name in args[args.index('--') + 1:]:\n"
        "        lines = Path(name).read_text().splitlines()\n"
        "        print(f'+++ b/{name}\\n@@ -0,0 +1,{len(lines)} @@')\n"
        "        for line in lines:\n"
        "            print('+' + line)\n"
        "else:\n"
        "    raise SystemExit('Unexpected Git call in read-only hook test')\n"
    )
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])

    def run(files, **env):
        for name, content in files.items():
            path = worktree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return subprocess.run(
            ["bash", str(ROOT / ".githooks/pre-commit")],
            cwd=worktree,
            env={**os.environ, "HOOK_STAGED_FILES": json.dumps(list(files)), **env},
            capture_output=True,
            text=True,
        )

    return run, patterns


@pytest.mark.parametrize(
    "name",
    [
        "notes with spaces.md",
        ".githooks/pre-commit",
        ".githooks/README.md",
        "CLAUDE.md",
        "docs/V0.4_EXECUTION_LOG.md",
    ],
)
def test_maintainer_pii_blocks_locations_only(maintainer_hook, name):
    run, _ = maintainer_hook
    result = run({name: "clean line\nprivate PIITESTTOKEN content\n"})
    assert result.returncode == 1
    assert result.stdout == ""
    assert f"\n{name}:2\n" in result.stderr
    assert "PIITESTTOKEN" not in result.stderr
    assert "private PIITESTTOKEN content" not in result.stderr
    assert "Blocked patterns:" not in result.stderr


@pytest.mark.parametrize("content", ["PIITESTTOKEN42", "OTHERTESTTOKEN"])
def test_maintainer_pii_extended_regex_lines(maintainer_hook, content):
    run, patterns = maintainer_hook
    patterns.write_text("# Comment\n  # Indented comment\n\n  \nPIITESTTOKEN[0-9]+\nOTHERTESTTOKEN")
    result = run({"notes.md": content + "\n"})
    assert result.returncode == 1
    assert "notes.md:1" in result.stderr
    assert content not in result.stdout + result.stderr


@pytest.mark.parametrize("state", ["missing", "empty", "comments_only"])
def test_maintainer_pii_inactive_notice(maintainer_hook, state):
    run, patterns = maintainer_hook
    if state == "missing":
        patterns.unlink()
    elif state == "empty":
        patterns.write_text("")
    else:
        patterns.write_text("# Comment\n  # Another comment\n\n  \n")
    result = run({"notes.md": "PIITESTTOKEN\n"})
    assert result.returncode == 0
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == 1
    assert "PII scan inactive" in result.stderr
    assert "create docs/internal/pii-patterns.txt" in result.stderr
    assert "PYOBFUS_PII_PATTERNS_FILE" in result.stderr
    assert "PIITESTTOKEN" not in result.stderr


def test_maintainer_pii_bypass(maintainer_hook):
    run, _ = maintainer_hook
    result = run({"notes.md": "PIITESTTOKEN\n"}, PYOBFUS_ALLOW_PII="1")
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_maintainer_pii_worktree_shared_default(maintainer_hook, monkeypatch):
    run, _ = maintainer_hook
    monkeypatch.delenv("PYOBFUS_PII_PATTERNS_FILE")
    result = run({"notes.md": "PIITESTTOKEN\n"})
    assert result.returncode == 1
    assert "notes.md:1" in result.stderr
    assert "PIITESTTOKEN" not in result.stderr


@pytest.mark.parametrize("pii_state", ["active", "missing", "bypassed"])
@pytest.mark.parametrize("kind", ["credential", "customer_id", "customer_email"])
def test_maintainer_other_scans_independent(maintainer_hook, pii_state, kind):
    run, patterns = maintainer_hook
    env = {}
    if pii_state == "missing":
        patterns.unlink()
    elif pii_state == "bypassed":
        env["PYOBFUS_ALLOW_PII"] = "1"
    content = {
        "credential": "ghp_" + "X" * 24,
        "customer_id": "cs_live_" + "SYNTHETIC" * 3,
        "customer_email": "synthetic@customer-domain.zzz",
    }[kind]
    result = run({"notes.md": content + "\n"}, **env)
    assert result.returncode == 1
    assert "notes.md:1" in result.stderr
    assert content not in result.stdout + result.stderr
    expected = "credential material" if kind == "credential" else "customer/business data"
    assert expected in result.stderr
    bypass = "PYOBFUS_ALLOW_SECRET" if kind == "credential" else "PYOBFUS_ALLOW_CUSTOMER_DATA"
    result = run({"notes.md": content + "\n"}, **env, **{bypass: "1"})
    assert result.returncode == 0
