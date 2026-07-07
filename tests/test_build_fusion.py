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
