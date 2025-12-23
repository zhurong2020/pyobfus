"""
Tests for license verification system (pyobfus Pro).

These tests verify the license verification, caching, and management functionality.
"""

import hashlib
import io
import json
import tempfile
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Import Pro license module
# Pylance/mypy may show type conflicts between real and stub implementations - this is expected
try:
    from pyobfus_pro.license import (  # type: ignore[import-not-found,import-untyped]
        CACHE_FILE,  # type: ignore[no-redef]
        LicenseExpiredError,  # type: ignore[no-redef]
        LicenseRevokedError,  # type: ignore[no-redef]
        LicenseVerificationError,  # type: ignore[no-redef]
        cache_license,  # type: ignore[no-redef]
        generate_license_key,  # type: ignore[no-redef]
        get_license_status,  # type: ignore[no-redef]
        load_cached_license,  # type: ignore[no-redef]
        remove_cached_license,  # type: ignore[no-redef]
        verify_license,  # type: ignore[no-redef]
    )
    from pyobfus_pro.fingerprint import get_device_fingerprint  # type: ignore[import-not-found,import-untyped,no-redef]

    PRO_AVAILABLE = True
except ImportError:
    # Define stub implementations for type checking when Pro features not available
    PRO_AVAILABLE = False

    # Stub constants
    CACHE_FILE: Any = ""  # type: ignore[no-redef]

    # Stub exception classes
    class LicenseExpiredError(Exception):  # type: ignore[no-redef]
        """Stub for LicenseExpiredError."""

        pass

    class LicenseRevokedError(Exception):  # type: ignore[no-redef]
        """Stub for LicenseRevokedError."""

        pass

    class LicenseVerificationError(Exception):  # type: ignore[no-redef]
        """Stub for LicenseVerificationError."""

        pass

    # Stub functions - marked with type: ignore to avoid conflicts with real implementations
    def cache_license(*args: Any, **kwargs: Any) -> None:  # type: ignore[no-redef]
        """Stub for cache_license."""
        pass

    def generate_license_key(*args: Any, **kwargs: Any) -> str:  # type: ignore[no-redef]
        """Stub for generate_license_key."""
        return "PYOB-0000-0000-0000-0000"

    def get_license_status(*args: Any, **kwargs: Any) -> dict[str, Any]:  # type: ignore[no-redef]
        """Stub for get_license_status."""
        return {}

    def load_cached_license(*args: Any, **kwargs: Any) -> dict[str, Any] | None:  # type: ignore[no-redef]
        """Stub for load_cached_license."""
        return None

    def remove_cached_license(*args: Any, **kwargs: Any) -> None:  # type: ignore[no-redef]
        """Stub for remove_cached_license."""
        pass

    def verify_license(*args: Any, **kwargs: Any) -> dict[str, Any]:  # type: ignore[no-redef]
        """Stub for verify_license."""
        return {}

    def get_device_fingerprint(*args: Any, **kwargs: Any) -> str:  # type: ignore[no-redef]
        """Stub for get_device_fingerprint."""
        return "stub-fingerprint"


class TestLicenseKeyGeneration:
    """Test license key generation."""

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_generate_license_key_format(self):
        """Test that generated license keys have correct format."""
        key = generate_license_key()

        # Should match format: PYOB-XXXX-XXXX-XXXX-XXXX
        parts = key.split("-")
        assert len(parts) == 5
        assert parts[0] == "PYOB"

        # Remaining parts should be 4-character hex strings
        for part in parts[1:]:
            assert len(part) == 4
            # Should be valid hex
            int(part, 16)

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_generate_unique_keys(self):
        """Test that generated keys are unique."""
        keys = [generate_license_key() for _ in range(100)]
        assert len(set(keys)) == 100  # All keys should be unique


class TestLicenseCaching:
    """Test license caching functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.original_cache_file = CACHE_FILE

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove any cached license
        if PRO_AVAILABLE:
            remove_cached_license()

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_cache_and_load_license(self):
        """Test caching and loading license data."""
        license_data = {
            "key": "PYOB-TEST-1234-5678-ABCD",
            "type": "professional",
            "expires": "2026-12-31",
            "verified": datetime.now().isoformat(),
        }

        # Cache the license
        cache_license(license_data)

        # Load it back
        loaded = load_cached_license()
        assert loaded is not None
        assert loaded["key"] == license_data["key"]
        assert loaded["type"] == license_data["type"]
        assert loaded["expires"] == license_data["expires"]

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_remove_cached_license(self):
        """Test removing cached license."""
        license_data = {
            "key": "PYOB-TEST-1234-5678-ABCD",
            "type": "professional",
            "expires": "2026-12-31",
            "verified": datetime.now().isoformat(),
        }

        # Cache a license
        cache_license(license_data)
        assert load_cached_license() is not None

        # Remove it
        result = remove_cached_license()
        assert result is True
        assert load_cached_license() is None

        # Trying to remove again should return False
        result = remove_cached_license()
        assert result is False

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_get_license_status_masked(self):
        """Test getting license status with masked key."""
        license_data = {
            "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
            "type": "professional",
            "expires": "2026-12-31",
            "verified": datetime.now().isoformat(),
        }

        cache_license(license_data)

        # Get status with masked key (default)
        status = get_license_status(masked=True)
        assert status is not None
        assert "..." in status["key"]  # Key should be masked
        assert status["type"] == "professional"

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_get_license_status_unmasked(self):
        """Test getting license status with full key."""
        license_data = {
            "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
            "type": "professional",
            "expires": "2026-12-31",
            "verified": datetime.now().isoformat(),
        }

        cache_license(license_data)

        # Get status with unmasked key
        status = get_license_status(masked=False)
        assert status is not None
        assert status["key"] == "PYOB-AAAA-BBBB-CCCC-DDDD"
        assert "..." not in status["key"]  # Key should NOT be masked

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_get_license_status_no_license(self):
        """Test getting status when no license is cached."""
        # Ensure no license is cached
        remove_cached_license()

        status = get_license_status()
        assert status is None


class TestLicenseVerification:
    """Test license verification functionality."""

    def teardown_method(self):
        """Clean up test fixtures."""
        if PRO_AVAILABLE:
            remove_cached_license()

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_verify_license_invalid_format(self):
        """Test that invalid license format raises error."""
        with pytest.raises(LicenseVerificationError, match="Invalid license key format"):
            verify_license("INVALID-KEY")

        with pytest.raises(LicenseVerificationError, match="Invalid license key format"):
            verify_license("PYOB-123")  # Too short

        with pytest.raises(LicenseVerificationError, match="Invalid license key format"):
            verify_license("WRONG-AAAA-BBBB-CCCC-DDDD")  # Wrong prefix

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("pyobfus_pro.license.urllib.request.urlopen")
    def test_verify_license_online_success(self, mock_urlopen):
        """Test successful online license verification."""
        # Mock the Worker API response
        api_response = {
            "valid": True,
            "license_key": "PYOB-AAAA-BBBB-CCCC-DDDD",
            "email": "test@example.com",
            "created_at": "2025-01-01T00:00:00Z",
            "expires_at": None,  # Lifetime license
            "features": {
                "string_encryption": True,
                "anti_debug": True,
                "control_flow": False,
            },
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(api_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        # Verify the license
        result = verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

        assert result["valid"] is True
        assert result["type"] == "pro"
        assert "success" in result["message"].lower()

        # Check that license was cached
        cached = load_cached_license()
        assert cached is not None
        assert cached["key"] == "PYOB-AAAA-BBBB-CCCC-DDDD"

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("pyobfus_pro.license.urllib.request.urlopen")
    def test_verify_license_revoked(self, mock_urlopen):
        """Test verification of revoked license."""
        # Worker returns 403 for revoked licenses
        import urllib.error

        # Use BytesIO for proper file-like object behavior
        error_body = io.BytesIO(
            json.dumps({"valid": False, "error": "License is revoked"}).encode()
        )

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=error_body
        )

        # Should raise LicenseVerificationError (revoked is handled as verification failure)
        with pytest.raises(LicenseVerificationError, match="revoked"):
            verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("pyobfus_pro.license.urllib.request.urlopen")
    def test_verify_license_expired(self, mock_urlopen):
        """Test verification of expired license."""
        # Worker returns 403 for expired licenses
        import urllib.error

        # Use BytesIO for proper file-like object behavior
        error_body = io.BytesIO(
            json.dumps({"valid": False, "error": "License has expired"}).encode()
        )

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=error_body
        )

        # Should raise LicenseVerificationError
        with pytest.raises(LicenseVerificationError, match="expired"):
            verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("pyobfus_pro.license.urllib.request.urlopen")
    def test_verify_license_not_found(self, mock_urlopen):
        """Test verification of non-existent license key."""
        # Worker returns 404 for not found
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )

        # Should raise LicenseVerificationError
        with pytest.raises(LicenseVerificationError, match="not found"):
            verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("pyobfus_pro.license.urllib.request.urlopen")
    def test_verify_license_uses_cache(self, mock_urlopen):
        """Test that valid cached license is used without online verification."""
        # Cache a valid license from "yesterday"
        yesterday = datetime.now() - timedelta(days=1)
        future_date = datetime.now() + timedelta(days=365)

        license_data = {
            "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
            "type": "professional",
            "expires": future_date.strftime("%Y-%m-%d"),
            "verified": yesterday.isoformat(),
        }
        cache_license(license_data)

        # Verify - should use cache without calling urlopen
        result = verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

        assert result["valid"] is True
        assert "cached" in result["message"].lower()
        # urlopen should NOT have been called
        mock_urlopen.assert_not_called()

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("pyobfus_pro.license.urllib.request.urlopen")
    def test_verify_license_network_error_fallback_to_cache(self, mock_urlopen):
        """Test fallback to cache when network verification fails."""
        # Cache a valid license
        future_date = datetime.now() + timedelta(days=365)
        license_data = {
            "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
            "type": "professional",
            "expires": future_date.strftime("%Y-%m-%d"),
            "verified": (datetime.now() - timedelta(days=35)).isoformat(),  # Expired cache
        }
        cache_license(license_data)

        # Simulate network error
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Network error")

        # Should fall back to cached license
        result = verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

        assert result["valid"] is True
        assert "cached" in result["message"].lower()
        assert "failed" in result["message"].lower()


class TestDeviceFingerprint:
    """Test device fingerprinting (v0.1.4)."""

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_get_fingerprint(self):
        """Test fingerprint generation."""
        fp = get_device_fingerprint()
        assert isinstance(fp, str)
        assert len(fp) == 16
        assert fp.isalnum()

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_fingerprint_consistency(self):
        """Test fingerprint consistency."""
        fp1 = get_device_fingerprint()
        fp2 = get_device_fingerprint()
        assert fp1 == fp2


class TestCacheSigning:
    """Test cache file signing (v0.1.4)."""

    def teardown_method(self):
        """Clean up test fixtures."""
        if PRO_AVAILABLE:
            remove_cached_license()

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_cache_has_signature(self):
        """Test that cached license includes signature."""
        # Cache a license
        license_data = {
            "key": "PYOB-TEST-TEST-TEST-TEST",
            "type": "pro",
            "expires": "2026-01-01",
            "verified": datetime.now().isoformat(),
        }
        cache_license(license_data)

        # Load raw cache file to inspect structure
        import pyobfus_pro.license as lic

        with open(lic.CACHE_FILE) as f:
            cached = json.load(f)

        # Verify v2 structure
        assert "v" in cached
        assert cached["v"] == 2
        assert "data" in cached
        assert "sig" in cached
        assert "ts" in cached
        assert "device_id" in cached["data"]

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_tampered_cache_rejected(self):
        """Test that tampered cache is rejected."""
        # Cache a license
        license_data = {
            "key": "PYOB-TEST-TEST-TEST-TEST",
            "type": "pro",
            "expires": "2026-01-01",
            "verified": datetime.now().isoformat(),
        }
        cache_license(license_data)

        # Tamper with cache - modify expires date
        import pyobfus_pro.license as lic

        with open(lic.CACHE_FILE) as f:
            cached = json.load(f)

        cached["data"]["expires"] = "2099-12-31"  # Extend expiration

        with open(lic.CACHE_FILE, "w") as f:
            json.dump(cached, f)

        # Try to load - should return None due to signature mismatch
        result = load_cached_license()
        assert result is None

        # Cache file should be deleted
        assert not lic.CACHE_FILE.exists()

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_device_mismatch_rejected(self):
        """Test that cache from different device is rejected."""
        # Cache a license
        license_data = {
            "key": "PYOB-TEST-TEST-TEST-TEST",
            "type": "pro",
            "expires": "2026-01-01",
            "verified": datetime.now().isoformat(),
        }
        cache_license(license_data)

        # Modify device_id in cache (simulate different device)
        import pyobfus_pro.license as lic
        import hmac

        with open(lic.CACHE_FILE) as f:
            cached = json.load(f)

        # Change device_id to simulate different device
        cached["data"]["device_id"] = "different_device_fp"

        # Recalculate signature for the tampered data (to bypass signature check)
        data_str = json.dumps(cached["data"], sort_keys=True)
        cached["sig"] = hmac.new(
            lic.LICENSE_SECRET.encode(), data_str.encode(), hashlib.sha256
        ).hexdigest()

        with open(lic.CACHE_FILE, "w") as f:
            json.dump(cached, f)

        # Try to load - should return None due to device mismatch
        result = load_cached_license()
        assert result is None

        # Cache file should NOT be deleted (might be network drive)
        assert lic.CACHE_FILE.exists()

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    def test_legacy_cache_v1_accepted(self):
        """Test that legacy v1 cache (v0.1.2-0.1.3) is still accepted."""
        # Create a v1 cache structure (old format without signature)
        import pyobfus_pro.license as lic

        legacy_cache = {
            "key": "PYOB-TEST-TEST-TEST-TEST",
            "type": "pro",
            "expires": "2026-01-01",
            "verified": datetime.now().isoformat(),
            # No "v", "sig", "ts", or "device_id" - this is v1 format
        }

        lic.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(lic.CACHE_FILE, "w") as f:
            json.dump(legacy_cache, f, indent=2)

        # Load should succeed (backward compatibility)
        result = load_cached_license()
        assert result is not None
        assert result["key"] == "PYOB-TEST-TEST-TEST-TEST"
