#!/usr/bin/env python3
"""
Create Stripe Checkout Session for pyobfus Professional Edition

This script generates a payment link for customers to purchase licenses.
"""

import os
import sys
import argparse

try:
    import stripe  # type: ignore[import]
except ImportError:
    print("[ERROR] stripe module not found. Install with: pip install -r scripts/requirements.txt")
    sys.exit(1)


def load_stripe_config():
    """Load Stripe configuration from .env.stripe file."""
    env_file = ".env.stripe"

    if not os.path.exists(env_file):
        print(f"[ERROR] {env_file} not found!")
        print(f"   Please create {env_file} with your Stripe credentials")
        sys.exit(1)

    # Load environment variables
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip()

    # Check environment mode
    environment = env_vars.get('STRIPE_ENVIRONMENT', 'test')
    print(f"[INFO] Environment mode: {environment}")

    # Load appropriate keys based on environment
    if environment == 'live':
        secret_key = env_vars.get('STRIPE_LIVE_SECRET_KEY')
        key_name = 'STRIPE_LIVE_SECRET_KEY'
    else:
        secret_key = env_vars.get('STRIPE_TEST_SECRET_KEY')
        key_name = 'STRIPE_TEST_SECRET_KEY'

    if not secret_key:
        print(f"[ERROR] {key_name} not found in {env_file}")
        sys.exit(1)

    # Load Price ID based on environment
    if environment == 'live':
        price_id = env_vars.get('STRIPE_LIVE_PRICE_ID')
        price_key_name = 'STRIPE_LIVE_PRICE_ID'
    else:
        price_id = env_vars.get('STRIPE_TEST_PRICE_ID')
        price_key_name = 'STRIPE_TEST_PRICE_ID'

    if not price_id:
        print(f"[ERROR] {price_key_name} not found in {env_file}")
        sys.exit(1)

    return secret_key, price_id, environment


def create_checkout_session(price_id, quantity=1, customer_email=None):
    """Create a Stripe Checkout Session."""
    print(f"\n[INFO] Creating checkout session...")
    print(f"   Price ID: {price_id}")
    print(f"   Quantity: {quantity}")
    if customer_email:
        print(f"   Customer email: {customer_email}")

    try:
        # Create checkout session
        session_params = {
            'mode': 'payment',
            'line_items': [{
                'price': price_id,
                'quantity': quantity,
            }],
            'success_url': 'https://github.com/zhurong2020/pyobfus?tab=readme-ov-file#pyobfus',
            'cancel_url': 'https://github.com/zhurong2020/pyobfus',
        }

        # Add customer email if provided
        if customer_email:
            session_params['customer_email'] = customer_email

        session = stripe.checkout.Session.create(**session_params)

        print(f"[SUCCESS] Checkout session created!")
        print(f"   Session ID: {session.id}")
        print(f"   Payment URL: {session.url}")

        return session

    except Exception as e:
        print(f"[ERROR] Failed to create checkout session: {e}")
        sys.exit(1)


def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Create Stripe Checkout Session for pyobfus Professional Edition'
    )
    parser.add_argument(
        '--email',
        type=str,
        help='Customer email address (optional)'
    )
    parser.add_argument(
        '--quantity',
        type=int,
        default=1,
        help='Number of licenses (default: 1)'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Stripe Checkout Session Generator")
    print("pyobfus Professional Edition")
    print("=" * 60)

    # Load configuration
    api_key, price_id, environment = load_stripe_config()
    stripe.api_key = api_key

    print(f"[INFO] Stripe API key loaded")
    print(f"[INFO] API key: {api_key[:7]}...{api_key[-4:]}")

    # Create checkout session
    session = create_checkout_session(price_id, args.quantity, args.email)

    # Display results
    print("\n" + "=" * 60)
    print("Checkout Session Created!")
    print("=" * 60)
    print("\n[Payment Link]")
    print(f"   {session.url}")
    print("\n[Instructions]")
    print("   1. Copy the payment link above")
    print("   2. Send it to the customer")
    print("   3. Customer completes payment")
    print("   4. License key auto-generated and stored in KV")
    print("   5. Check license in Cloudflare KV or Worker logs")
    print("\n[Monitoring]")
    if environment == 'live':
        print("   - Stripe Dashboard: https://dashboard.stripe.com/payments")
        print("   - Webhooks: https://dashboard.stripe.com/webhooks")
    else:
        print("   - Stripe Dashboard: https://dashboard.stripe.com/test/payments")
        print("   - Webhooks: https://dashboard.stripe.com/test/webhooks")
    print("   - Worker Logs: cd cloudflare-worker && wrangler tail")
    print("   - KV Storage: wrangler kv key list --remote --namespace-id=61072fc72c35405c850427da381ccdbf")

    print("\n[Note]")
    if environment == 'live':
        print("   Running in LIVE mode - Real payments will be processed!")
    else:
        print("   Running in TEST mode - Use test card: 4242 4242 4242 4242")


if __name__ == "__main__":
    main()
