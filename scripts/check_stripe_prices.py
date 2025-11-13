#!/usr/bin/env python3
"""Check Stripe prices in both test and live mode."""

import os
import sys

try:
    import stripe  # type: ignore[import]
except ImportError:
    print("[ERROR] stripe module not found. Install with: pip install -r scripts/requirements.txt")
    sys.exit(1)

def load_env_file():
    """Load .env.stripe file."""
    env_vars = {}
    with open('.env.stripe', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip()
    return env_vars

env_vars = load_env_file()

# Test mode
print("=" * 60)
print("TEST MODE PRICES")
print("=" * 60)
try:
    stripe.api_key = env_vars['STRIPE_TEST_SECRET_KEY']
    prices = stripe.Price.list(limit=5)
    for p in prices.data:
        print(f"Price ID: {p.id}")
        print(f"  Amount: ${p.unit_amount/100:.2f} {p.currency.upper()}")
        print(f"  Product: {p.product}")
        print()
except Exception as e:
    print(f"Error: {e}")

# Live mode
print("=" * 60)
print("LIVE MODE PRICES")
print("=" * 60)
try:
    stripe.api_key = env_vars['STRIPE_LIVE_SECRET_KEY']
    prices = stripe.Price.list(limit=5)
    for p in prices.data:
        print(f"Price ID: {p.id}")
        print(f"  Amount: ${p.unit_amount/100:.2f} {p.currency.upper()}")
        print(f"  Product: {p.product}")
        print()
except Exception as e:
    print(f"Error: {e}")
