"""
Tests for license verification system (pyobfus Pro).

These tests verify the license verification, caching, and management functionality.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import Pro license module
try:
    from pyobfus_pro.license import (
        CACHE_FILE,
        LicenseError,
        LicenseExpiredError,
        LicenseRevokedError,
        LicenseVerificationError,
        cache_license,
        generate_license_key,
        get_license_status,
        load_cached_license,
        remove_cached_license,
        verify_license,
    )

    PRO_AVAILABLE = True
except ImportError:
    PRO_AVAILABLE = False


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
    @patch("urllib.request.urlopen")
    def test_verify_license_online_success(self, mock_urlopen):
        """Test successful online license verification."""
        # Mock the GitHub API response
        license_data = {
            "version": "1.0",
            "licenses": [
                {
                    "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
                    "type": "professional",
                    "issued": "2025-01-01",
                    "expires": "2026-01-01",
                    "status": "active",
                }
            ],
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(license_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        # Verify the license
        result = verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

        assert result["valid"] is True
        assert result["type"] == "professional"
        assert result["expires"] == "2026-01-01"
        assert "success" in result["message"].lower()

        # Check that license was cached
        cached = load_cached_license()
        assert cached is not None
        assert cached["key"] == "PYOB-AAAA-BBBB-CCCC-DDDD"

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("urllib.request.urlopen")
    def test_verify_license_revoked(self, mock_urlopen):
        """Test verification of revoked license."""
        license_data = {
            "version": "1.0",
            "licenses": [
                {
                    "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
                    "type": "professional",
                    "issued": "2025-01-01",
                    "expires": "2026-01-01",
                    "status": "revoked",
                }
            ],
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(license_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        # Should raise LicenseRevokedError
        with pytest.raises(LicenseRevokedError, match="revoked"):
            verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("urllib.request.urlopen")
    def test_verify_license_expired(self, mock_urlopen):
        """Test verification of expired license."""
        # License expired yesterday
        expired_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        license_data = {
            "version": "1.0",
            "licenses": [
                {
                    "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
                    "type": "professional",
                    "issued": "2024-01-01",
                    "expires": expired_date,
                    "status": "active",
                }
            ],
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(license_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        # Should raise LicenseExpiredError
        with pytest.raises(LicenseExpiredError, match="expired"):
            verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("urllib.request.urlopen")
    def test_verify_license_not_found(self, mock_urlopen):
        """Test verification of non-existent license key."""
        license_data = {"version": "1.0", "licenses": []}

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(license_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        # Should raise LicenseVerificationError
        with pytest.raises(LicenseVerificationError, match="not found"):
            verify_license("PYOB-AAAA-BBBB-CCCC-DDDD")

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not available")
    @patch("urllib.request.urlopen")
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
    @patch("urllib.request.urlopen")
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
