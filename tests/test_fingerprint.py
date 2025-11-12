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
