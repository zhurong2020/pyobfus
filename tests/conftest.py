"""Shared test isolation.

Trial status, license caches and the device identifier live under the caller's
home directory, where a test could quietly read, create or overwrite them. Tests
must never touch a developer's own pyobfus state, so bind it to pytest's
per-test directory everywhere, not only in the test modules that happen to
think about licences.
"""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_device_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import pyobfus.trial as trial

    state_dir = tmp_path / ".pyobfus"
    monkeypatch.setattr(trial, "TRIAL_DIR", state_dir)
    monkeypatch.setattr(trial, "TRIAL_FILE", state_dir / "trial.json")
    try:
        import pyobfus_pro.license as license_module
        import pyobfus_pro.fingerprint as fingerprint
    except ImportError:  # pragma: no cover - Pro edition not installed
        return

    monkeypatch.setattr(license_module, "CACHE_DIR", state_dir)
    monkeypatch.setattr(license_module, "CACHE_FILE", state_dir / "license.json")
    device_file = state_dir / "device_id"
    monkeypatch.setattr(fingerprint, "DEVICE_ID_FILE", device_file)
    assert fingerprint.DEVICE_ID_FILE.is_relative_to(tmp_path)
