"""
Centralized constants for pyobfus.

This file contains all URLs and configuration that may need to change.
Update values here instead of searching through multiple files.

Single Source of Truth Pattern:
- All Python files import from here
- Documentation files reference these values (update manually when changed)
"""

# =============================================================================
# PAYMENT & PURCHASE
# =============================================================================

# Stripe Payment Link (Live Mode)
# To update: Change this value, then update docs manually (see DOCS_TO_UPDATE below)
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/00w4gr8ta9F78Fj8oI9k400"

# Price
PRO_PRICE_USD = 45

# =============================================================================
# SUPPORT & CONTACT
# =============================================================================

SUPPORT_EMAIL = "zhurong0525@gmail.com"
GITHUB_REPO = "https://github.com/zhurong2020/pyobfus"

# =============================================================================
# LICENSE SERVER
# =============================================================================
# Note: This URL is also defined in pyobfus_pro/license.py (for package independence)
# Keep both in sync if the URL changes!

LICENSE_API_URL = "https://pyobfus-license-server.zhurong0525.workers.dev/api/verify"

# =============================================================================
# DOCUMENTATION FILES TO UPDATE MANUALLY
# =============================================================================
# When changing STRIPE_PAYMENT_LINK, also update these files:
#
# DOCS_TO_UPDATE = [
#     "README.md (line ~96)",
#     "docs/index.md (lines ~43, ~141)",
#     "CHANGELOG.md (line ~204)",
# ]
# =============================================================================
