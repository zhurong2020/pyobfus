"""Tests for pyobfus constants module."""

from pyobfus.constants import (
    STRIPE_PAYMENT_LINK,
    PRO_PRICE_USD,
    SUPPORT_EMAIL,
    GITHUB_REPO,
    LICENSE_API_URL,
)


class TestConstants:
    def test_stripe_link_is_url(self):
        assert STRIPE_PAYMENT_LINK.startswith("https://")

    def test_price_is_positive_int(self):
        assert isinstance(PRO_PRICE_USD, int)
        assert PRO_PRICE_USD > 0

    def test_support_email_format(self):
        assert "@" in SUPPORT_EMAIL

    def test_github_repo_url(self):
        assert GITHUB_REPO.startswith("https://github.com/")

    def test_license_api_url(self):
        assert LICENSE_API_URL.startswith("https://")
