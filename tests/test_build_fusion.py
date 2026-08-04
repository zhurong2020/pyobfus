"""End-to-end CLI tests for the v0.5.1 build-fusion Pro mechanisms.

Exercises `pyobfus build --selective-opacity / --seal-code / --vault /
--scrub-traceback / --fingerprint / --expire-hard` through the real CLI (with
trial mocked active), verifying the obfuscated output composes with Core's
name-mangling and runs correctly — the combined pipeline the 2026-06-18 probe
proved out (vault PRE-pass, opacity/seal/scrub POST-pass).
"""

import importlib.util
import sys

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from pyobfus.cli import main

try:
    import pyobfus_pro  # noqa: F401

    PRO_AVAILABLE = True
except ImportError:
    PRO_AVAILABLE = False

requires_pro = pytest.mark.skipif(not PRO_AVAILABLE, reason="pyobfus_pro not installed")


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def marked_file(tmp_path):
    """A module using all four marker forms + a global reference."""
    f = tmp_path / "mod.py"
    f.write_text(
        "from pyobfus_pro import opacity, seal_code, vault_secrets, Layer\n"
        "MULT = 2\n"
        'CFG = vault_secrets({"API_KEY": "sk-secret-xyz", "ENV": "prod"})\n\n'
        "@opacity(Layer.ENCRYPTED)\n"
        "def compute(x):\n"
        "    return x * MULT + 7\n\n"
        "@seal_code\n"
        "def guard(y):\n"
        "    return y - 1\n\n"
        "def run():\n"
        "    return compute(5) + guard(10)\n"
    )
    return f


def _invoke(runner, src, out, *flags):
    with patch("pyobfus.cli.is_trial_active", return_value=True):
        return runner.invoke(main, [str(src), "-o", str(out), "--level", "pro", *flags])


def _compiles(path):
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
    return True


def _load_module(path, name):
    """exec the obfuscated module, restoring sys.excepthook afterward."""
    saved = sys.excepthook
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    finally:
        sys.excepthook = saved


@requires_pro
class TestFusionStructural:
    def test_vault_strips_secret_and_emits_vault(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(runner, marked_file, out, "--vault")
        assert res.exit_code == 0, res.output
        text = out.read_text()
        assert "sk-secret-xyz" not in text  # plaintext secret gone
        assert "Vault(" in text
        assert _compiles(out)

    def test_selective_opacity_encrypts(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(runner, marked_file, out, "--selective-opacity")
        assert res.exit_code == 0, res.output
        text = out.read_text()
        assert "_l3_dispatch(" in text and "_CIPHER_" in text
        assert _compiles(out)

    def test_seal_code_emits_verify(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(runner, marked_file, out, "--seal-code")
        assert res.exit_code == 0, res.output
        assert "_verify_seal(" in out.read_text()
        assert _compiles(out)

    def test_scrub_emits_excepthook_and_keyfile(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(runner, marked_file, out, "--scrub-traceback")
        assert res.exit_code == 0, res.output
        assert "install_scrub_excepthook(" in out.read_text()
        assert (tmp_path / "o.py.scrub.key.pem").exists()
        assert _compiles(out)

    def test_expire_hard_injects_check(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(runner, marked_file, out, "--expire-hard", "2099-01-01")
        assert res.exit_code == 0, res.output
        assert "_pyobfus_expire_check(" in out.read_text()
        assert _compiles(out)

    def test_period_injects_check(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(runner, marked_file, out, "--period", "5")
        assert res.exit_code == 0, res.output
        text = out.read_text()
        assert "_pyobfus_period_check(" in text
        assert "_pyobfus_counter_path(" in text
        assert _compiles(out)

    def test_requires_runtime_injects_check(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(
            runner,
            marked_file,
            out,
            "--requires-os",
            "Linux,Darwin",
            "--requires-python-min",
            "3.9",
            "--requires-arch",
            "x86_64,arm64",
        )
        assert res.exit_code == 0, res.output
        text = out.read_text()
        assert "_pyobfus_requires_runtime(" in text
        assert "os_allowed=('Linux', 'Darwin')" in text
        assert "python_min='3.9'" in text
        assert "arch_allowed=('x86_64', 'arm64')" in text
        assert _compiles(out)

    def test_all_combined_compiles(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        res = _invoke(
            runner,
            marked_file,
            out,
            "--selective-opacity",
            "--seal-code",
            "--vault",
            "--scrub-traceback",
            "--fingerprint",
            "buyer-007",
            "--expire-hard",
            "2099-01-01",
        )
        assert res.exit_code == 0, res.output
        text = out.read_text()
        for marker in (
            "_l3_dispatch(",
            "_verify_seal(",
            "Vault(",
            "install_scrub_excepthook(",
            "_pyobfus_expire_check(",
        ):
            assert marker in text, marker
        assert "sk-secret-xyz" not in text
        assert _compiles(out)


@requires_pro
class TestFusionRuntime:
    def test_combined_runs_correctly(self, runner, marked_file, tmp_path):
        """opacity (L3, references a global) + seal + vault all execute right."""
        cfg = tmp_path / "pyobfus.yaml"
        cfg.write_text("obfuscation:\n  exclude_names: [run, CFG]\n")
        out = tmp_path / "o.py"
        with patch("pyobfus.cli.is_trial_active", return_value=True):
            res = runner.invoke(
                main,
                [
                    str(marked_file),
                    "-o",
                    str(out),
                    "--level",
                    "pro",
                    "--config",
                    str(cfg),
                    "--selective-opacity",
                    "--seal-code",
                    "--vault",
                ],
            )
        assert res.exit_code == 0, res.output
        saved = sys.excepthook
        try:
            spec = importlib.util.spec_from_file_location("fused_mod", str(out))
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        finally:
            sys.excepthook = saved
        # compute(5)=5*2+7=17 (L3-encrypted, reads global MULT); guard(10)=9
        assert m.run() == 26
        assert m.CFG.get("API_KEY") == "sk-secret-xyz"


@requires_pro
class TestOpacityConfig:
    """`--opacity-config opacity.toml` drives L3 encryption by pre-mangle qualname
    (via decorator injection in the pre-pass), no name-map coupling needed."""

    def _write_src(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text(
            "MULT = 3\n\n"
            "def secret_compute(x):\n"
            "    return x * MULT + 1\n\n"
            "def plain_helper(y):\n"
            "    return y - 1\n"
        )
        return f

    def test_config_encrypts_only_matched(self, runner, tmp_path):
        src = self._write_src(tmp_path)
        cfg = tmp_path / "opacity.toml"
        cfg.write_text(
            'default_layer = "obfuscated"\n\n'
            "[[rules]]\n"
            'pattern = "*.secret_*"\n'
            'layer = "encrypted"\n'
        )
        out = tmp_path / "o.py"
        res = _invoke(runner, src, out, "--opacity-config", str(cfg))
        assert res.exit_code == 0, res.output
        text = out.read_text()
        # exactly one function (secret_compute) got L3-encrypted; plain_helper did not
        assert text.count("_l3_dispatch(") == 1
        assert "_CIPHER_" in text
        assert _compiles(out)

    def test_config_no_match_is_noop(self, runner, tmp_path):
        src = self._write_src(tmp_path)
        cfg = tmp_path / "opacity.toml"
        cfg.write_text('[[rules]]\npattern = "*.nonexistent_*"\nlayer = "encrypted"\n')
        out = tmp_path / "o.py"
        res = _invoke(runner, src, out, "--opacity-config", str(cfg))
        assert res.exit_code == 0, res.output
        assert "_l3_dispatch(" not in out.read_text()
        assert _compiles(out)

    def test_config_encrypted_runs_correctly(self, runner, tmp_path):
        src = self._write_src(tmp_path)
        cfg = tmp_path / "opacity.toml"
        cfg.write_text('[[rules]]\npattern = "*.secret_*"\nlayer = "encrypted"\n')
        yaml_cfg = tmp_path / "pyobfus.yaml"
        yaml_cfg.write_text("obfuscation:\n  exclude_names: [secret_compute, plain_helper]\n")
        out = tmp_path / "o.py"
        with patch("pyobfus.cli.is_trial_active", return_value=True):
            res = runner.invoke(
                main,
                [
                    str(src),
                    "-o",
                    str(out),
                    "--level",
                    "pro",
                    "--config",
                    str(yaml_cfg),
                    "--opacity-config",
                    str(cfg),
                ],
            )
        assert res.exit_code == 0, res.output
        assert "_l3_dispatch(" in out.read_text()
        saved = sys.excepthook
        try:
            spec = importlib.util.spec_from_file_location("opcfg_mod", str(out))
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        finally:
            sys.excepthook = saved
        assert m.secret_compute(5) == 16  # L3-encrypted, reads global MULT=3
        assert m.plain_helper(10) == 9


@requires_pro
class TestBindDevice:
    """`--bind-device` rewrites the baked L3 `_LAYER_KEY` into a runtime
    device-derived key, so decryption only succeeds on the bound device."""

    def _src(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text(
            "from pyobfus_pro import opacity, Layer\n"
            "MULT = 4\n\n"
            "@opacity(Layer.ENCRYPTED)\n"
            "def compute(x):\n"
            "    return x * MULT + 2\n\n"
            "def run():\n"
            "    return compute(6)\n"
        )
        return f

    def test_bind_device_rewrites_layer_key(self, runner, tmp_path):
        src = self._src(tmp_path)
        out = tmp_path / "o.py"
        res = _invoke(runner, src, out, "--selective-opacity", "--bind-device")
        assert res.exit_code == 0, res.output
        text = out.read_text()
        assert "_pyobfus_bind_device_key(" in text
        assert "_pyobfus_build_salt" in text
        # the raw key literal must be gone
        assert "_LAYER_KEY = b'" not in text and '_LAYER_KEY = b"' not in text
        assert _compiles(out)

    def test_bind_device_runs_on_build_machine(self, runner, tmp_path):
        src = self._src(tmp_path)
        yaml_cfg = tmp_path / "pyobfus.yaml"
        yaml_cfg.write_text("obfuscation:\n  exclude_names: [run]\n")
        out = tmp_path / "o.py"
        with patch("pyobfus.cli.is_trial_active", return_value=True):
            res = runner.invoke(
                main,
                [
                    str(src),
                    "-o",
                    str(out),
                    "--level",
                    "pro",
                    "--config",
                    str(yaml_cfg),
                    "--selective-opacity",
                    "--bind-device",
                ],
            )
        assert res.exit_code == 0, res.output
        m = _load_module(out, "bd_match")
        # build machine == run machine -> re-derived key matches -> decrypts
        assert m.run() == 26  # compute(6) = 6*4+2

    def test_bind_device_wrong_device_fails(self, runner, tmp_path):
        src = self._src(tmp_path)
        yaml_cfg = tmp_path / "pyobfus.yaml"
        yaml_cfg.write_text("obfuscation:\n  exclude_names: [run]\n")
        out = tmp_path / "o.py"
        with patch("pyobfus.cli.is_trial_active", return_value=True):
            res = runner.invoke(
                main,
                [
                    str(src),
                    "-o",
                    str(out),
                    "--level",
                    "pro",
                    "--config",
                    str(yaml_cfg),
                    "--selective-opacity",
                    "--bind-device-id",
                    "not-this-machine-xyz",
                ],
            )
        assert res.exit_code == 0, res.output
        m = _load_module(out, "bd_mismatch")
        from pyobfus_pro import OpacityRuntimeError

        # ciphertext was keyed to a different device -> GCM tag fails on decrypt
        with pytest.raises(OpacityRuntimeError):
            m.run()


@requires_pro
class TestVaultBindDevice:
    """`--bind-device --vault` rewrites each baked `_VAULT_KEY_<name>` into a
    runtime device-derived key, so vault decryption only succeeds on the bound
    device. Per-vault salts keep the vault keys mutually independent."""

    def _src(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text(
            'CFG = vault_secrets({"API_KEY": "sk-secret-xyz", "ENV": "prod"})\n'
            'DB = vault_secrets({"DSN": "postgres://secret"})\n\n'
            "def run():\n"
            "    return CFG.get('API_KEY') + '|' + DB.get('DSN')\n"
        )
        return f

    def _yaml(self, tmp_path):
        y = tmp_path / "pyobfus.yaml"
        y.write_text("obfuscation:\n  exclude_names: [run]\n")
        return y

    def test_bind_device_rewrites_vault_keys(self, runner, tmp_path):
        src = self._src(tmp_path)
        out = tmp_path / "o.py"
        res = _invoke(runner, src, out, "--vault", "--bind-device")
        assert res.exit_code == 0, res.output
        text = out.read_text()
        assert "_pyobfus_bind_device_key(" in text
        # both vaults' raw key literals must be gone
        assert "_VAULT_KEY_CFG = b'" not in text and '_VAULT_KEY_CFG = b"' not in text
        assert "_VAULT_KEY_DB = b'" not in text and '_VAULT_KEY_DB = b"' not in text
        assert _compiles(out)

    def test_bind_device_runs_on_build_machine(self, runner, tmp_path):
        src = self._src(tmp_path)
        yaml_cfg = self._yaml(tmp_path)
        out = tmp_path / "o.py"
        with patch("pyobfus.cli.is_trial_active", return_value=True):
            res = runner.invoke(
                main,
                [
                    str(src),
                    "-o",
                    str(out),
                    "--level",
                    "pro",
                    "--config",
                    str(yaml_cfg),
                    "--vault",
                    "--bind-device",
                ],
            )
        assert res.exit_code == 0, res.output
        m = _load_module(out, "vbd_match")
        # build machine == run machine -> both vaults re-derive their key -> decrypt
        assert m.run() == "sk-secret-xyz|postgres://secret"

    def test_bind_device_wrong_device_fails(self, runner, tmp_path):
        src = self._src(tmp_path)
        yaml_cfg = self._yaml(tmp_path)
        out = tmp_path / "o.py"
        with patch("pyobfus.cli.is_trial_active", return_value=True):
            res = runner.invoke(
                main,
                [
                    str(src),
                    "-o",
                    str(out),
                    "--level",
                    "pro",
                    "--config",
                    str(yaml_cfg),
                    "--vault",
                    "--bind-device-id",
                    "not-this-machine-xyz",
                ],
            )
        assert res.exit_code == 0, res.output
        m = _load_module(out, "vbd_mismatch")
        from pyobfus_pro.runtime.vault import VaultError

        # ciphertext keyed to a different device -> GCM tag fails on decrypt
        with pytest.raises(VaultError):
            m.run()

    def test_bind_device_no_vault_secrets_is_noop(self, runner, tmp_path):
        # --vault --bind-device on a module with no vault_secrets({...}) must
        # not crash and must not emit a device-binding import.
        src = tmp_path / "mod.py"
        src.write_text("VALUE = 41\n\ndef run():\n    return VALUE + 1\n")
        out = tmp_path / "o.py"
        res = _invoke(runner, src, out, "--vault", "--bind-device")
        assert res.exit_code == 0, res.output
        assert _compiles(out)
        assert "_pyobfus_bind_device_key(" not in out.read_text()


@requires_pro
def test_vault_device_binding_uses_distinct_per_vault_salts():
    """Each vault gets its own salt (checked pre-Core so names are unmangled),
    so the two device-derived keys are independent."""
    import ast

    from pyobfus_pro import build_fusion

    class _Cfg:
        vault = True
        bind_device = True
        bind_device_id = "device-under-test"
        opacity_config = None

    src = 'CFG = vault_secrets({"A": "x"})\n' 'DB = vault_secrets({"B": "y"})\n'
    out = build_fusion._apply_vault_device_binding(src, _Cfg())
    assert "_pyobfus_bind_device_key(" in out
    salts = [
        node.value.value
        for node in ast.walk(ast.parse(out))
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id.startswith("_pyobfus_vault_salt_")
        and isinstance(node.value, ast.Constant)
    ]
    assert len(salts) == 2
    assert salts[0] != salts[1]
    # raw key literals replaced, not baked
    assert "_VAULT_KEY_CFG = b'" not in out
    assert "_VAULT_KEY_DB = b'" not in out


@requires_pro
def test_period_runtime_enforces_limit(runner, tmp_path, monkeypatch):
    """The injected run-counter raises LicenseExpired past the limit, and the
    counter path is resolved at runtime via $PYOBFUS_COUNTER_DIR (not baked in
    at build time)."""
    src = tmp_path / "simple.py"
    src.write_text("VALUE = 42\n")
    out = tmp_path / "o.py"
    res = _invoke(runner, src, out, "--period", "2")
    assert res.exit_code == 0, res.output
    assert "_pyobfus_period_check(" in out.read_text()

    from pyobfus_pro.license_binding import LicenseExpired

    counter_dir = tmp_path / "counters"
    monkeypatch.setenv("PYOBFUS_COUNTER_DIR", str(counter_dir))

    def _load():
        spec = importlib.util.spec_from_file_location("period_mod", str(out))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    _load()  # run 1 -> counter 1, ok
    _load()  # run 2 -> counter 2, ok
    with pytest.raises(LicenseExpired):
        _load()  # run 3 -> counter 3 > max 2
    # counter file lives under the env-overridden dir, proving runtime resolution
    assert list(counter_dir.rglob("runs"))


@requires_pro
def test_requires_runtime_enforces_python_min(runner, tmp_path):
    """The injected requires_runtime() raises RuntimePolicyError on the
    real running interpreter when python_min exceeds it, and imports
    cleanly when python_min is satisfied -- exercised against the actual
    interpreter running the test, not a mock."""
    src = tmp_path / "simple.py"
    src.write_text("VALUE = 42\n")

    from pyobfus_pro import RuntimePolicyError

    # Unsatisfiable minimum -> import must fail.
    out_fail = tmp_path / "o_fail.py"
    res = _invoke(runner, src, out_fail, "--requires-python-min", "99.0")
    assert res.exit_code == 0, res.output

    def _load(path, name):
        spec = importlib.util.spec_from_file_location(name, str(path))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    with pytest.raises(RuntimePolicyError):
        _load(out_fail, "requires_runtime_fail")

    # Trivially satisfiable minimum -> import succeeds (name mangling renames
    # VALUE, so just confirm the module loads without raising).
    out_ok = tmp_path / "o_ok.py"
    res = _invoke(runner, src, out_ok, "--requires-python-min", "3.0")
    assert res.exit_code == 0, res.output
    _load(out_ok, "requires_runtime_ok")


class TestFusionGating:
    def test_fusion_requires_pro_access(self, runner, marked_file, tmp_path):
        out = tmp_path / "o.py"
        with (
            patch("pyobfus.cli.is_trial_active", return_value=False),
            patch("pyobfus.cli.PRO_AVAILABLE", False),
        ):
            res = runner.invoke(main, [str(marked_file), "-o", str(out), "--vault"])
        assert res.exit_code == 1
        assert "Pro features require a license or active trial" in res.output
