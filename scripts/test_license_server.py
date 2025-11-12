#!/usr/bin/env python3
"""
Test script for pyobfus License Server (Cloudflare Worker)

Tests license verification and device tracking functionality.
"""

import json
import sys
import uuid
import requests


# Worker URL
WORKER_URL = "https://pyobfs-license-server.zhurong0525.workers.dev"


def test_health():
    """Test health check endpoint."""
    print("[TEST] Testing health check...")
    response = requests.get(f"{WORKER_URL}/api/health")

    if response.status_code == 200:
        data = response.json()
        print(f"[PASS] Health check passed: {data}")
        return True
    else:
        print(f"[FAIL] Health check failed: {response.status_code}")
        return False


def test_license_verification(license_key: str, device_id: str = None):
    """Test license verification endpoint."""
    if device_id is None:
        device_id = str(uuid.uuid4())

    print(f"\n[TEST] Testing license verification...")
    print(f"   License key: {license_key}")
    print(f"   Device ID: {device_id}")

    payload = {
        "license_key": license_key,
        "device_id": device_id
    }

    response = requests.post(
        f"{WORKER_URL}/api/verify",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"   Status: {response.status_code}")

    try:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")

        if response.status_code == 200 and data.get("valid"):
            print(f"[PASS] License verification passed")
            return True, device_id
        else:
            print(f"[FAIL] License verification failed")
            return False, device_id
    except Exception as e:
        print(f"[FAIL] Error parsing response: {e}")
        print(f"   Raw response: {response.text}")
        return False, device_id


def test_device_limit(license_key: str):
    """Test device limit (max 3 devices)."""
    print(f"\n[TEST] Testing device limit...")

    devices = []
    for i in range(4):
        device_id = str(uuid.uuid4())
        print(f"\n   Device {i+1}: {device_id}")

        payload = {
            "license_key": license_key,
            "device_id": device_id
        }

        response = requests.post(
            f"{WORKER_URL}/api/verify",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        data = response.json()

        if i < 3:
            # First 3 devices should succeed
            if response.status_code == 200 and data.get("valid"):
                print(f"   [PASS] Device {i+1} registered")
                devices.append(device_id)
            else:
                print(f"   [FAIL] Device {i+1} failed unexpectedly")
                return False
        else:
            # 4th device should fail
            if response.status_code == 403:
                print(f"   [PASS] Device {i+1} correctly rejected (device limit reached)")
                return True
            else:
                print(f"   [FAIL] Device {i+1} should have been rejected")
                return False

    return True


def test_invalid_license():
    """Test with invalid license key."""
    print(f"\n[TEST] Testing invalid license...")

    payload = {
        "license_key": "INVALID-LICENSE-KEY",
        "device_id": str(uuid.uuid4())
    }

    response = requests.post(
        f"{WORKER_URL}/api/verify",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 404:
        print(f"[PASS] Invalid license correctly rejected")
        return True
    else:
        print(f"[FAIL] Invalid license should return 404, got {response.status_code}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("pyobfus License Server - Integration Tests")
    print("=" * 60)

    # Test 1: Health check
    if not test_health():
        print("\n[FAIL] Health check failed, aborting tests")
        sys.exit(1)

    # Test 2: Valid license verification
    test_license = "PYOBFUS-TEST-1234-5678-ABCD"
    success, device_id = test_license_verification(test_license)
    if not success:
        print(f"\n[WARN] License verification failed")
        print(f"   Make sure you've created the test license in KV:")
        print(f"   Key: {test_license}")
        print(f'   Value: {{"license_key":"{test_license}","email":"test@example.com","status":"active","created_at":"2025-11-12T00:00:00Z","stripe_session_id":"test_session","stripe_customer_id":"test_customer","devices":[],"expires_at":null}}')
        sys.exit(1)

    # Test 3: Same device verification (should succeed)
    print("\n[TEST] Testing same device re-verification...")
    success, _ = test_license_verification(test_license, device_id)
    if not success:
        print("[FAIL] Same device re-verification failed")
        sys.exit(1)

    # Test 4: Invalid license
    if not test_invalid_license():
        print("\n[FAIL] Invalid license test failed")
        sys.exit(1)

    # Test 5: Device limit (optional - creates many devices)
    # Uncomment to test device limit
    # if not test_device_limit(test_license):
    #     print("\n[FAIL] Device limit test failed")
    #     sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("   1. Configure Stripe webhook (point to your Worker)")
    print("   2. Update Python client to use this Worker URL")
    print("   3. Test end-to-end payment flow")


if __name__ == "__main__":
    main()
