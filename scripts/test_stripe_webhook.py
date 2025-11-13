#!/usr/bin/env python3
"""
Test Stripe webhook integration with Cloudflare Worker

Simulates a Stripe checkout.session.completed event and tests
license key generation.
"""

import json
import sys
import time

try:
    import requests  # type: ignore[import]
except ImportError:
    print("[ERROR] requests module not found. Install with: pip install -r scripts/requirements.txt")
    sys.exit(1)


# Worker URL
WORKER_URL = "https://pyobfus-license-server.zhurong0525.workers.dev"
WEBHOOK_ENDPOINT = f"{WORKER_URL}/api/webhook/stripe"


def create_test_event():
    """Create a test checkout.session.completed event."""
    return {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(time.time()),
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{int(time.time())}",
                "object": "checkout.session",
                "amount_total": 4500,  # $45.00
                "currency": "usd",
                "customer": f"cus_test_{int(time.time())}",
                "customer_details": {
                    "email": "test.customer@example.com",
                    "name": "Test Customer"
                },
                "mode": "payment",
                "payment_status": "paid",
                "status": "complete",
                "created": int(time.time()),
            }
        }
    }


def send_webhook_event(event):
    """Send webhook event to Worker."""
    print("\n[TEST] Sending webhook event...")
    print(f"   Event type: {event['type']}")
    print(f"   Customer email: {event['data']['object']['customer_details']['email']}")

    response = requests.post(
        WEBHOOK_ENDPOINT,
        json=event,
        headers={
            "Content-Type": "application/json",
            # Note: In production, you'd need to generate a proper Stripe signature
            # For testing, we're skipping signature verification
        }
    )

    print(f"   Status: {response.status_code}")

    try:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")

        if response.status_code == 200:
            print(f"[PASS] Webhook processed successfully")
            return True, data
        else:
            print(f"[FAIL] Webhook processing failed")
            return False, data
    except Exception as e:
        print(f"[FAIL] Error parsing response: {e}")
        print(f"   Raw response: {response.text}")
        return False, None


def verify_license_created():
    """
    Verify that a license was created.
    Note: We can't directly query KV from here, but we can check Worker logs.
    """
    print("\n[INFO] License key should have been created")
    print("[INFO] Check Cloudflare Worker logs:")
    print("   cd cloudflare-worker")
    print("   wrangler tail")
    print("\n[INFO] Or check KV directly:")
    print("   wrangler kv key list --remote --namespace-id=61072fc72c35405c850427da381ccdbf")


def main():
    """Run webhook test."""
    print("=" * 60)
    print("Stripe Webhook Integration Test")
    print("=" * 60)

    # Test 1: Health check
    print("\n[TEST] Testing Worker health...")
    response = requests.get(f"{WORKER_URL}/api/health")
    if response.status_code == 200:
        print(f"[PASS] Worker is healthy")
    else:
        print(f"[FAIL] Worker health check failed")
        return

    # Test 2: Send webhook event
    event = create_test_event()
    success, data = send_webhook_event(event)

    if not success:
        print("\n[FAIL] Webhook test failed")
        return

    # Test 3: Verify license creation
    verify_license_created()

    print("\n" + "=" * 60)
    print("[SUCCESS] Webhook test completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("   1. Check Worker logs for license key")
    print("   2. List KV keys to verify license was created")
    print("   3. Test license verification with new key")


if __name__ == "__main__":
    main()
