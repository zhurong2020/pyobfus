#!/usr/bin/env python3
"""
Create a permanent Stripe Payment Link for pyobfus Professional Edition.
This link can be used for self-service purchases without email requests.
"""

import os
import sys
from pathlib import Path

try:
    import stripe  # type: ignore[import]
except ImportError:
    print("[ERROR] stripe module not found. Install with: pip install -r scripts/requirements.txt")
    sys.exit(1)

try:
    from dotenv import load_dotenv  # type: ignore[import]
except ImportError:
    print("[ERROR] dotenv module not found. Install with: pip install -r scripts/requirements.txt")
    sys.exit(1)

# Load environment variables
env_file = Path(__file__).parent.parent / ".env.stripe"
if not env_file.exists():
    print("[ERROR] .env.stripe not found!")
    sys.exit(1)

load_dotenv(env_file)

# Get environment mode
mode = os.getenv("STRIPE_ENVIRONMENT", "test")

# Load appropriate keys
if mode == "live":
    stripe.api_key = os.getenv("STRIPE_LIVE_SECRET_KEY")
    price_id = os.getenv("STRIPE_LIVE_PRICE_ID")
else:
    stripe.api_key = os.getenv("STRIPE_TEST_SECRET_KEY")
    price_id = os.getenv("STRIPE_TEST_PRICE_ID")

print("=" * 60)
print("Stripe Payment Link Generator")
print("pyobfus Professional Edition")
print("=" * 60)
print(f"[INFO] Environment mode: {mode}")
print(f"[INFO] Price ID: {price_id}")
print()

try:
    # Create Payment Link
    print("[INFO] Creating permanent payment link...")

    payment_link = stripe.PaymentLink.create(
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        after_completion={
            'type': 'redirect',
            'redirect': {
                'url': 'https://github.com/zhurong2020/pyobfus/blob/main/docs/LICENSE_ACTIVATION_GUIDE.md',
            },
        },
    )

    print("[SUCCESS] Payment link created!")
    print()
    print("=" * 60)
    print("Permanent Payment Link")
    print("=" * 60)
    print()
    print(f"[Payment Link]")
    print(f"   {payment_link.url}")
    print()
    print(f"[Payment Link ID]")
    print(f"   {payment_link.id}")
    print()
    print("[Usage]")
    print("   1. Add this link to your website/documentation")
    print("   2. Customers click the link to purchase")
    print("   3. After payment, they're redirected to activation guide")
    print("   4. License key is auto-delivered via email")
    print()
    print("[Where to Add]")
    print("   - docs/index.md (GitHub Pages)")
    print("   - README.md (GitHub repo)")
    print("   - Social media / launch announcements")
    print()
    print(f"[Note]")
    print(f"   Running in {mode.upper()} mode")
    if mode == "live":
        print("   ⚠️  Real payments will be processed!")
    else:
        print("   🧪 Test mode - Use test cards only")
    print()

except stripe.error.StripeError as e:
    print(f"[ERROR] Stripe API error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)
