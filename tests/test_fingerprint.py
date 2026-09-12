"""Tests for device fingerprinting."""

from pyobfus_pro.fingerprint import (
    get_device_fingerprint,
    get_device_name,
    get_device_info,
)


def test_fingerprint_format():
    """Test fingerprint format."""
    fp = get_device_fingerprint()

    assert isinstance(fp, str)
    assert len(fp) == 16
    assert fp.isalnum()


def test_fingerprint_consistency():
    """Test that fingerprint is consistent across calls."""
    fp1 = get_device_fingerprint()
    fp2 = get_device_fingerprint()

    assert fp1 == fp2


def test_device_name():
    """Test device name retrieval."""
    name = get_device_name()

    assert isinstance(name, str)
    assert len(name) > 0


def test_device_info():
    """Test device info retrieval."""
    info = get_device_info()

    assert "fingerprint" in info
    assert "name" in info
    assert "system" in info
    assert len(info["fingerprint"]) == 16


class TestFingerprintStability:
    """The fingerprint decides whether a customer keeps their licence."""

    def test_an_os_update_does_not_change_the_machine(self):
        """The old fingerprint hashed the OS release, so an update broke it."""
        import platform
        from unittest import mock

        from pyobfus_pro.fingerprint import get_device_fingerprint

        first = get_device_fingerprint()
        real = platform.release()
        with mock.patch("platform.release", return_value=real + ".1"):
            assert get_device_fingerprint() == first
        with mock.patch("platform.node", return_value="renamed-host"):
            assert get_device_fingerprint() == first
        with mock.patch("uuid.getnode", return_value=1234567890):
            assert get_device_fingerprint() == first

    def test_the_identifier_is_created_once_and_reused(self):
        from pyobfus_pro import fingerprint

        assert not fingerprint.DEVICE_ID_FILE.exists()
        created = fingerprint.get_device_fingerprint()
        assert fingerprint.DEVICE_ID_FILE.exists()
        assert fingerprint.DEVICE_ID_FILE.read_text().strip() == created
        assert fingerprint.get_device_fingerprint() == created

    def test_a_corrupt_identifier_is_replaced_rather_than_fatal(self):
        from pyobfus_pro import fingerprint

        fingerprint.DEVICE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        fingerprint.DEVICE_ID_FILE.write_text("not a device id")
        replaced = fingerprint.get_device_fingerprint()
        assert len(replaced) == 16
        assert all(c in "0123456789abcdef" for c in replaced)

    def test_an_unwritable_home_still_yields_a_repeatable_value(self, monkeypatch):
        """Returning a fresh value each run would register a device per build."""
        from pyobfus_pro import fingerprint

        monkeypatch.setattr(
            fingerprint.Path, "mkdir", lambda *a, **k: (_ for _ in ()).throw(OSError())
        )
        first = fingerprint.get_device_fingerprint()
        second = fingerprint.get_device_fingerprint()
        assert first == second
        assert len(first) == 16

    def test_two_machines_do_not_collide(self, tmp_path, monkeypatch):
        from pyobfus_pro import fingerprint

        monkeypatch.setattr(fingerprint, "DEVICE_ID_FILE", tmp_path / "a" / "device_id")
        one = fingerprint.get_device_fingerprint()
        monkeypatch.setattr(fingerprint, "DEVICE_ID_FILE", tmp_path / "b" / "device_id")
        two = fingerprint.get_device_fingerprint()
        assert one != two
