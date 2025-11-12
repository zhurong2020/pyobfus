#!/usr/bin/env python3
"""
Switch Stripe configuration from test mode to production mode

This script helps migrate from test environment to production after KYC approval.
"""

import os
import sys


def check_env_file():
    """Check if .env.stripe exists."""
    if not os.path.exists(".env.stripe"):
        print("[ERROR] .env.stripe file not found!")
        sys.exit(1)


def display_current_config():
    """Display current Stripe configuration."""
    print("=" * 60)
    print("Current Stripe Configuration")
    print("=" * 60)

    with open(".env.stripe", 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("STRIPE_ENVIRONMENT="):
                env = line.split('=')[1]
                print(f"\nCurrent Environment: {env}")
            if line.startswith("STRIPE_TEST_SECRET_KEY="):
                key = line.split('=')[1]
                print(f"Test Secret Key: {key[:15]}...{key[-4:]}")
            if line.startswith("STRIPE_LIVE_SECRET_KEY="):
                key = line.split('=')[1]
                if key:
                    print(f"Live Secret Key: {key[:15]}...{key[-4:]}")
                else:
                    print("Live Secret Key: [NOT SET]")


def update_live_keys():
    """Guide user to update live keys."""
    print("\n" + "=" * 60)
    print("Update Production Keys")
    print("=" * 60)

    print("\n[IMPORTANT] You need to get your LIVE mode keys from Stripe:")
    print("   1. Go to: https://dashboard.stripe.com/apikeys")
    print("   2. Switch to 'LIVE' mode (toggle on the left)")
    print("   3. Copy your 'Secret key' (sk_live_...)")
    print("   4. Copy your 'Publishable key' (pk_live_...)")

    print("\n[PROMPT] Do you have your LIVE keys ready? (y/N): ", end='')
    response = input().strip().lower()

    if response != 'y':
        print("\n[INFO] Please get your LIVE keys first, then run this script again.")
        sys.exit(0)

    # Get live keys from user
    print("\n[PROMPT] Enter LIVE Secret Key (sk_live_...): ", end='')
    live_secret = input().strip()

    print("[PROMPT] Enter LIVE Publishable Key (pk_live_...): ", end='')
    live_publishable = input().strip()

    # Validate keys
    if not live_secret.startswith("sk_live_"):
        print("[ERROR] Invalid LIVE secret key! Must start with 'sk_live_'")
        sys.exit(1)

    if not live_publishable.startswith("pk_live_"):
        print("[ERROR] Invalid LIVE publishable key! Must start with 'pk_live_'")
        sys.exit(1)

    return live_secret, live_publishable


def update_env_file(live_secret, live_publishable):
    """Update .env.stripe with live keys and switch environment."""
    print("\n[INFO] Updating .env.stripe file...")

    with open(".env.stripe", 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith("STRIPE_LIVE_SECRET_KEY="):
            new_lines.append(f"STRIPE_LIVE_SECRET_KEY={live_secret}\n")
        elif line.strip().startswith("STRIPE_LIVE_PUBLISHABLE_KEY="):
            new_lines.append(f"STRIPE_LIVE_PUBLISHABLE_KEY={live_publishable}\n")
        elif line.strip().startswith("STRIPE_ENVIRONMENT="):
            new_lines.append("STRIPE_ENVIRONMENT=live\n")
        else:
            new_lines.append(line)

    with open(".env.stripe", 'w') as f:
        f.writelines(new_lines)

    print("[SUCCESS] .env.stripe updated!")


def update_worker_secret(live_secret):
    """Update Cloudflare Worker with live Stripe secret key."""
    print("\n[INFO] Updating Cloudflare Worker...")
    print("[IMPORTANT] You need to manually update the Worker secret:")
    print(f"\n   cd cloudflare-worker")
    print(f"   echo \"{live_secret}\" | wrangler secret put STRIPE_SECRET_KEY")
    print("\n[NOTE] The webhook secret (STRIPE_WEBHOOK_SECRET) stays the same.")


def recreate_webhook():
    """Guide user to recreate webhook in live mode."""
    print("\n" + "=" * 60)
    print("Recreate Webhook in LIVE Mode")
    print("=" * 60)

    print("\n[IMPORTANT] You need to recreate the webhook for LIVE mode:")
    print("   1. Delete test webhook:")
    print("      python scripts/setup_stripe_webhook.py")
    print("      (Select 'y' to delete existing test webhook)")
    print("\n   2. Switch to LIVE mode in .env.stripe (already done above)")
    print("\n   3. Create LIVE webhook:")
    print("      python scripts/setup_stripe_webhook.py")
    print("\n[NOTE] This will create a new webhook endpoint in LIVE mode.")


def main():
    """Main function."""
    check_env_file()

    print("=" * 60)
    print("Stripe Production Migration Tool")
    print("=" * 60)

    display_current_config()

    print("\n[WARNING] This will switch your Stripe configuration to LIVE mode!")
    print("[WARNING] Make sure:")
    print("   1. Your Stripe account KYC is approved")
    print("   2. You have your LIVE API keys ready")
    print("   3. You've tested everything in TEST mode")

    print("\n[PROMPT] Continue with production migration? (yes/NO): ", end='')
    confirm = input().strip().lower()

    if confirm != 'yes':
        print("\n[INFO] Migration cancelled.")
        sys.exit(0)

    # Get and update live keys
    live_secret, live_publishable = update_live_keys()
    update_env_file(live_secret, live_publishable)

    # Show next steps
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)

    print("\nNext steps:")
    print("   1. Update Worker secret (see instructions above)")
    update_worker_secret(live_secret)
    print("\n   2. Recreate webhook in LIVE mode")
    recreate_webhook()
    print("\n   3. Test with a real payment:")
    print("      - Use Stripe's test card: 4242 4242 4242 4242")
    print("      - Or make a real $1 test purchase")
    print("\n   4. Monitor Stripe Dashboard:")
    print("      https://dashboard.stripe.com/payments")

    print("\n[SUCCESS] Production migration preparation complete!")
    print("[REMINDER] Complete the manual steps above before going live.")


if __name__ == "__main__":
    main()
