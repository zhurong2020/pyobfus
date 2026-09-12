"""Shared test isolation.

The device identifier is now a real file under the caller's home directory,
which makes it something a test run could quietly create or overwrite. Tests
must never touch a developer's own pyobfus state, so bind it to pytest's
per-test directory everywhere, not only in the test modules that happen to
think about licences.
"""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_device_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        import pyobfus_pro.fingerprint as fingerprint
    except ImportError:  # pragma: no cover - Pro edition not installed
        return

    device_file = tmp_path / ".pyobfus" / "device_id"
    monkeypatch.setattr(fingerprint, "DEVICE_ID_FILE", device_file)
    assert fingerprint.DEVICE_ID_FILE.is_relative_to(tmp_path)
