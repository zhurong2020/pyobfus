#!/usr/bin/env python3
"""
Setup Stripe webhook for pyobfus License Server

This script configures Stripe webhook endpoints using the Stripe API.
"""

import os
import sys

try:
    import stripe  # type: ignore[import]
except ImportError:
    print("[ERROR] stripe module not found. Install with: pip install -r scripts/requirements.txt")
    sys.exit(1)


# Cloudflare Worker URL
WORKER_URL = "https://pyobfus-license-server.zhurong0525.workers.dev"
WEBHOOK_ENDPOINT = f"{WORKER_URL}/api/webhook/stripe"


def load_stripe_key():
    """Load Stripe API key from .env.stripe file based on environment."""
    env_file = ".env.stripe"

    if not os.path.exists(env_file):
        print(f"[ERROR] {env_file} not found!")
        print(f"   Please create {env_file} with your Stripe secret key:")
        print(f"   STRIPE_TEST_SECRET_KEY=sk_test_xxx")
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

    # Load appropriate key based on environment
    if environment == 'live':
        key = env_vars.get('STRIPE_LIVE_SECRET_KEY')
        key_name = 'STRIPE_LIVE_SECRET_KEY'
    else:
        key = env_vars.get('STRIPE_TEST_SECRET_KEY')
        key_name = 'STRIPE_TEST_SECRET_KEY'

    if not key:
        print(f"[ERROR] {key_name} not found in {env_file}")
        sys.exit(1)

    return key, environment


def list_existing_webhooks():
    """List all existing webhook endpoints."""
    print("\n[INFO] Checking existing webhooks...")

    webhooks = stripe.WebhookEndpoint.list(limit=100)

    if not webhooks.data:
        print("[INFO] No existing webhooks found")
        return []

    print(f"[INFO] Found {len(webhooks.data)} existing webhooks:")
    for i, webhook in enumerate(webhooks.data, 1):
        print(f"   {i}. URL: {webhook.url}")
        print(f"      Status: {webhook.status}")
        print(f"      Events: {', '.join(webhook.enabled_events)}")
        print(f"      ID: {webhook.id}")

    return webhooks.data


def create_webhook():
    """Create webhook endpoint for license server."""
    print(f"\n[INFO] Creating webhook endpoint...")
    print(f"   URL: {WEBHOOK_ENDPOINT}")

    # Events to listen for
    events = [
        'checkout.session.completed',  # When payment succeeds
    ]

    try:
        webhook = stripe.WebhookEndpoint.create(
            url=WEBHOOK_ENDPOINT,
            enabled_events=events,
        )

        print(f"[SUCCESS] Webhook created successfully!")
        print(f"   Webhook ID: {webhook.id}")
        print(f"   Webhook Secret: {webhook.secret}")
        print(f"\n[IMPORTANT] Save this webhook secret for Worker configuration:")
        print(f"   wrangler secret put STRIPE_WEBHOOK_SECRET")
        print(f"   (then paste: {webhook.secret})")

        return webhook

    except stripe.error.StripeError as e:
        print(f"[ERROR] Failed to create webhook: {e}")
        sys.exit(1)


def delete_webhook(webhook_id):
    """Delete a webhook endpoint."""
    try:
        stripe.WebhookEndpoint.delete(webhook_id)
        print(f"[SUCCESS] Webhook {webhook_id} deleted")
        return True
    except stripe.error.StripeError as e:
        print(f"[ERROR] Failed to delete webhook: {e}")
        return False


def main():
    """Main function."""
    print("=" * 60)
    print("Stripe Webhook Configuration for pyobfus")
    print("=" * 60)

    # Load API key
    api_key, environment = load_stripe_key()
    stripe.api_key = api_key

    print(f"[INFO] Stripe API key loaded")
    print(f"[INFO] API key: {api_key[:7]}...{api_key[-4:]}")

    # List existing webhooks
    existing = list_existing_webhooks()

    # Check if webhook already exists
    webhook_exists = False
    for webhook in existing:
        if webhook.url == WEBHOOK_ENDPOINT:
            webhook_exists = True
            print(f"\n[INFO] Webhook already exists for {WEBHOOK_ENDPOINT}")
            print(f"   Webhook ID: {webhook.id}")
            print(f"   Status: {webhook.status}")

            # Ask if user wants to recreate
            response = input("\n[PROMPT] Do you want to delete and recreate? (y/N): ")
            if response.lower() == 'y':
                if delete_webhook(webhook.id):
                    webhook_exists = False
            break

    # Create webhook if it doesn't exist
    if not webhook_exists:
        webhook = create_webhook()
    else:
        print("\n[INFO] No changes made")

    print("\n" + "=" * 60)
    print("Configuration Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("   1. Save the webhook secret to Worker:")
    print("      cd cloudflare-worker")
    print("      wrangler secret put STRIPE_WEBHOOK_SECRET")
    print("   2. Test the webhook:")
    print("      stripe trigger checkout.session.completed")
    print("   3. Monitor webhook events:")
    if environment == 'live':
        print("      https://dashboard.stripe.com/webhooks")
    else:
        print("      https://dashboard.stripe.com/test/webhooks")


if __name__ == "__main__":
    main()
