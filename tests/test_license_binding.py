"""Tests for P2-8 license binding combo runtime primitives.

Three orthogonal axes, tested independently + in combination with the
existing P2-1 / P2-11 transformer infrastructure.

- ``current_machine_id`` + ``bind_device_key``: stable per-machine
  identifier + PBKDF2-HMAC-SHA256 derivation
- ``expire_check``: ISO-date comparison with explicit ``now`` override
- ``period_check``: atomic file counter with crash-safe rename pattern
- Integration: derived key feeds opacity / vault transformers' ``layer_key=``
  parameter, producing a build that decrypts only on the issuing device
"""

import datetime as _datetime
import secrets

import pytest

from pyobfus_pro import OpacityRuntimeError, VaultError
from pyobfus_pro.license_binding import (
    LicenseBindingError,
    LicenseExpired,
    bind_device_key,
    current_machine_id,
    expire_check,
    period_check,
)
from pyobfus_pro.transformers.opacity import transform_module as opacity_transform
from pyobfus_pro.transformers.vault import transform_module as vault_transform

# ---------------------------------------------------------------------------
# current_machine_id
# ---------------------------------------------------------------------------


class TestCurrentMachineId:
    def test_returns_non_empty_string(self):
        mid = current_machine_id()
        assert isinstance(mid, str)
        assert len(mid) > 0

    def test_stable_across_calls(self):
        # Two calls in the same process must return the same value.
        a = current_machine_id()
        b = current_machine_id()
        assert a == b

    def test_returns_string_suitable_for_pbkdf2(self):
        # Whatever source path produced the ID, the result must be a
        # UTF-8 string we can feed straight into bind_device_key.
        mid = current_machine_id()
        salt = secrets.token_bytes(32)
        key = bind_device_key(mid, salt)
        assert len(key) == 32


# ---------------------------------------------------------------------------
# bind_device_key
# ---------------------------------------------------------------------------


class TestBindDeviceKey:
    def test_returns_32_bytes(self):
        key = bind_device_key("test-machine-id", secrets.token_bytes(32))
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_deterministic_for_same_inputs(self):
        salt = b"\x42" * 32
        a = bind_device_key("device-A", salt)
        b = bind_device_key("device-A", salt)
        assert a == b

    def test_different_machine_id_produces_different_key(self):
        salt = b"\x42" * 32
        a = bind_device_key("device-A", salt)
        b = bind_device_key("device-B", salt)
        assert a != b

    def test_different_salt_produces_different_key(self):
        a = bind_device_key("device-A", b"\x42" * 32)
        b = bind_device_key("device-A", b"\x43" * 32)
        assert a != b

    def test_machine_id_must_be_non_empty_string(self):
        with pytest.raises(LicenseBindingError, match="non-empty"):
            bind_device_key("", secrets.token_bytes(32))
        with pytest.raises(LicenseBindingError, match="must be a string"):
            bind_device_key(42, secrets.token_bytes(32))  # type: ignore[arg-type]

    def test_salt_must_be_at_least_16_bytes(self):
        with pytest.raises(LicenseBindingError, match="at least 16"):
            bind_device_key("device-A", b"short")
        with pytest.raises(LicenseBindingError, match="at least 16"):
            bind_device_key("device-A", b"\x00" * 15)
        # 16 bytes is the floor; 16 must succeed
        key = bind_device_key("device-A", b"\x00" * 16)
        assert len(key) == 32

    def test_iterations_must_be_above_floor(self):
        with pytest.raises(LicenseBindingError, match=">="):
            bind_device_key("device-A", b"\x00" * 16, iterations=1000)
        with pytest.raises(LicenseBindingError, match=">="):
            bind_device_key("device-A", b"\x00" * 16, iterations=99_999)

    def test_higher_iterations_produces_different_key(self):
        # PBKDF2 output depends on iteration count; same inputs + different
        # iterations -> different key. Required so future migrations can
        # safely raise iterations without colliding with old keys.
        salt = b"\x42" * 32
        a = bind_device_key("device-A", salt, iterations=100_000)
        b = bind_device_key("device-A", salt, iterations=200_000)
        assert a != b


# ---------------------------------------------------------------------------
# expire_check
# ---------------------------------------------------------------------------


class TestExpireCheck:
    def test_future_date_passes(self):
        future = _datetime.date.today() + _datetime.timedelta(days=30)
        # Should not raise
        expire_check(future.isoformat())

    def test_past_date_raises(self):
        past = _datetime.date.today() - _datetime.timedelta(days=1)
        with pytest.raises(LicenseExpired, match="expired on"):
            expire_check(past.isoformat())

    def test_today_passes(self):
        today = _datetime.date.today()
        # Today is the LAST valid day; check uses `now > expire_date`
        expire_check(today.isoformat())

    def test_explicit_now_used(self):
        # Using the now= parameter for testability.
        expire_check("2030-01-01", now=_datetime.date(2029, 12, 31))
        with pytest.raises(LicenseExpired):
            expire_check("2025-01-01", now=_datetime.date(2025, 1, 2))

    def test_now_must_be_a_date(self):
        with pytest.raises(LicenseBindingError, match="datetime.date"):
            expire_check("2030-01-01", now="2029-12-31")  # type: ignore[arg-type]

    def test_malformed_date_raises_binding_error(self):
        with pytest.raises(LicenseBindingError, match="ISO-8601"):
            expire_check("not-a-date")
        with pytest.raises(LicenseBindingError, match="ISO-8601"):
            expire_check("01/01/2030")  # wrong format

    def test_date_only_no_time_component(self):
        # The check is date-only; a user on UTC+8 and UTC-8 see the same
        # result on the boundary day.
        expire_check("2030-01-01", now=_datetime.date(2030, 1, 1))


# ---------------------------------------------------------------------------
# period_check
# ---------------------------------------------------------------------------


class TestPeriodCheck:
    def test_first_call_creates_counter_at_one(self, tmp_path):
        counter_file = tmp_path / "runs"
        result = period_check(counter_file, max_runs=10)
        assert result == 1
        assert counter_file.read_text() == "1"

    def test_increments_across_calls(self, tmp_path):
        counter_file = tmp_path / "runs"
        for expected in (1, 2, 3, 4, 5):
            assert period_check(counter_file, max_runs=10) == expected

    def test_raises_when_exceeded(self, tmp_path):
        counter_file = tmp_path / "runs"
        # Use up the budget
        for _ in range(3):
            period_check(counter_file, max_runs=3)
        # 4th call -> exceeded
        with pytest.raises(LicenseExpired, match="exceeded"):
            period_check(counter_file, max_runs=3)

    def test_creates_parent_directory(self, tmp_path):
        # period_check creates intermediate directories as needed.
        nested = tmp_path / "deep" / "path" / "runs"
        assert period_check(nested, max_runs=5) == 1
        assert nested.exists()

    def test_advance_false_does_not_increment(self, tmp_path):
        counter_file = tmp_path / "runs"
        # Run 3 times to set counter to 3
        for _ in range(3):
            period_check(counter_file, max_runs=10)
        # advance=False reads current counter without changing it
        assert period_check(counter_file, max_runs=10, advance=False) == 3
        # Counter file unchanged
        assert counter_file.read_text() == "3"
        # Then a real call advances normally
        assert period_check(counter_file, max_runs=10) == 4

    def test_advance_false_still_raises_when_already_exceeded(self, tmp_path):
        counter_file = tmp_path / "runs"
        counter_file.write_text("100")
        with pytest.raises(LicenseExpired):
            period_check(counter_file, max_runs=10, advance=False)

    def test_max_runs_must_be_positive_int(self, tmp_path):
        with pytest.raises(LicenseBindingError, match=">= 1"):
            period_check(tmp_path / "x", max_runs=0)
        with pytest.raises(LicenseBindingError, match=">= 1"):
            period_check(tmp_path / "x", max_runs=-1)

    def test_corrupt_counter_file_raises(self, tmp_path):
        counter_file = tmp_path / "runs"
        counter_file.write_text("not an int")
        with pytest.raises(LicenseBindingError, match="corrupted"):
            period_check(counter_file, max_runs=10)

    def test_negative_counter_value_rejected(self, tmp_path):
        counter_file = tmp_path / "runs"
        counter_file.write_text("-5")
        with pytest.raises(LicenseBindingError, match="negative"):
            period_check(counter_file, max_runs=10)

    def test_atomic_rename_no_temp_files_left_behind(self, tmp_path):
        counter_file = tmp_path / "runs"
        for _ in range(5):
            period_check(counter_file, max_runs=10)
        # No leftover .counter.*.tmp files
        leftover = list(tmp_path.glob(".counter.*"))
        assert leftover == []


# ---------------------------------------------------------------------------
# Integration: device-bound layer key with opacity transformer
# ---------------------------------------------------------------------------


class TestOpacityIntegration:
    def test_correct_machine_id_decrypts_correctly(self):
        # Build with a key derived from the current machine; decrypt on
        # the same machine succeeds.
        import textwrap

        src = textwrap.dedent("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """).strip() + "\n"

        salt = secrets.token_bytes(32)
        key = bind_device_key(current_machine_id(), salt)
        out, _ = opacity_transform(src, layer_key=key)

        ns: dict = {}
        exec(compile(out, "<t>", "exec"), ns)  # noqa: S102
        assert ns["critical"](3) == 21

    def test_wrong_machine_id_fails_decryption(self):
        # Simulate a different machine: build for machine A, attempt to
        # decrypt with key derived for machine B. GCM tag should mismatch
        # and surface as OpacityRuntimeError.
        import textwrap

        src = textwrap.dedent("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """).strip() + "\n"

        salt = secrets.token_bytes(32)
        key_machine_a = bind_device_key("machine-A", salt)
        out, _ = opacity_transform(src, layer_key=key_machine_a)

        # Replace _LAYER_KEY in the emitted source with the key derived
        # for a different machine. (Simulates the "wrong device" case
        # where the build orchestrator emitted a runtime call to
        # bind_device_key but the user is on the wrong machine, so the
        # derived key is different.)
        import re

        wrong_key = bind_device_key("machine-B", salt)
        wrong_key_repr = repr(wrong_key)
        tampered = re.sub(
            r"^_LAYER_KEY = .+$",
            lambda _m: f"_LAYER_KEY = {wrong_key_repr}",
            out,
            count=1,
            flags=re.MULTILINE,
        )

        ns: dict = {}
        exec(compile(tampered, "<t>", "exec"), ns)  # noqa: S102
        with pytest.raises(OpacityRuntimeError):
            ns["critical"](3)


class TestVaultIntegration:
    def test_correct_machine_id_decrypts_vault(self):
        import textwrap

        src = textwrap.dedent("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"K": "v"})
        """).strip() + "\n"

        salt = secrets.token_bytes(32)
        key = bind_device_key(current_machine_id(), salt)
        out, _ = vault_transform(src, vault_keys={"SECRETS": key})

        ns: dict = {}
        exec(compile(out, "<t>", "exec"), ns)  # noqa: S102
        assert ns["SECRETS"].get("K") == "v"

    def test_wrong_machine_id_fails_vault(self):
        import re
        import textwrap

        src = textwrap.dedent("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"K": "v"})
        """).strip() + "\n"

        salt = secrets.token_bytes(32)
        key_a = bind_device_key("machine-A", salt)
        out, _ = vault_transform(src, vault_keys={"SECRETS": key_a})

        wrong_key = bind_device_key("machine-B", salt)
        wrong_key_repr = repr(wrong_key)
        tampered = re.sub(
            r"^_VAULT_KEY_SECRETS = .+$",
            lambda _m: f"_VAULT_KEY_SECRETS = {wrong_key_repr}",
            out,
            count=1,
            flags=re.MULTILINE,
        )

        ns: dict = {}
        exec(compile(tampered, "<t>", "exec"), ns)  # noqa: S102
        with pytest.raises(VaultError):
            ns["SECRETS"].get("K")
