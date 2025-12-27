# License Activation Guide

This guide explains how to activate and manage your pyobfus Professional Edition license.

## Prerequisites

- Python 3.8 or higher installed
- pyobfus package installed: `pip install pyobfus`
- Valid license key (received via email after purchase)

> **Important**: Your license key email may be in your **Spam/Junk folder**. Please check there if you don't see it in your inbox within a few minutes of purchase.

## Try Before You Buy

Not sure if Pro features are right for you? Try them free for 5 days:

```bash
# Start a free trial (no credit card required)
pyobfus-trial start --email your@email.com

# Test Pro features during trial
pyobfus input.py -o output.py --string-encryption --anti-debug

# Check trial status
pyobfus-trial status
```

The trial includes all Pro features. After 5 days, purchase a license to continue using them.

## Quick Activation

```bash
# 1. Install/upgrade pyobfus
pip install --upgrade pyobfus

# 2. Register your license
pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX

# 3. Verify activation
pyobfus-license status
```

## Detailed Steps

### Step 1: Install pyobfus

If you haven't already installed pyobfus:

```bash
pip install pyobfus
```

Or upgrade to the latest version:

```bash
pip install --upgrade pyobfus
```

### Step 2: Register License Key

Use the `pyobfus-license` command to register your license:

```bash
pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX
```

Replace `PYOB-XXXX-XXXX-XXXX-XXXX` with your actual license key.

**Expected output**:
```
[INFO] Registering license: PYOB-XXXX-XXXX-XXXX-XXXX
[SUCCESS] License registered successfully
[INFO] License cached locally for offline use
```

### Step 3: Verify Activation

Check your license status:

```bash
pyobfus-license status
```

**Expected output**:
```
License Status:
  License Key: PYOB-XXXX-XXXX-XXXX-XXXX
  Status: Active
  Email: your-email@example.com
  Device: 1/3 devices used
  Features:
    - AES-256 String Encryption: Enabled
    - Anti-Debugging: Enabled
  Cache: Valid (expires in 2 days, 23 hours)
```

### Step 4: Start Using Pro Features

Once activated, use Pro features with command-line flags:

```bash
# AES-256 string encryption
pyobfus input.py -o output.py --string-encryption

# Anti-debugging checks
pyobfus input.py -o output.py --anti-debug

# Both features combined
pyobfus input.py -o output.py --string-encryption --anti-debug --preserve-param-names
```

## Managing Your License

### Check Status

View detailed license information:

```bash
pyobfus-license status
```

Add `--verify` flag to force online verification:

```bash
pyobfus-license status --verify
```

### Remove License

To deactivate the license on current device:

```bash
pyobfus-license remove
```

**Note**: This only removes the local cache. Your license remains valid and can be reactivated on this or another device.

### Transfer to Another Device

Each license works on up to 3 devices. To transfer:

1. **On old device** (optional):
   ```bash
   pyobfus-license remove
   ```

2. **On new device**:
   ```bash
   pip install pyobfus
   pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX
   ```

If you've reached the 3-device limit, contact support to reset device bindings.

## Offline Usage

Your license is cached locally for **3 days** after activation. During this period, you can use Pro features offline.

**To refresh cache** (requires internet):
```bash
pyobfus-license status --verify
```

**Cache location**:
- Linux/Mac: `~/.pyobfus/license.json`
- Windows: `%USERPROFILE%\.pyobfus\license.json`

## Troubleshooting

### "License not found" Error

**Problem**: License key not recognized

**Solutions**:
1. Check your email for the correct license key
2. Ensure no typos (use copy-paste)
3. Verify internet connection
4. Contact support if key is definitely correct

### "Device limit reached" Error

**Problem**: License already used on 3 devices

**Solutions**:
1. Remove license from unused devices using `pyobfus-license remove`
2. Contact support to reset device bindings: zhurong0525@gmail.com
3. Include your license key in the email

### "License verification failed" Error

**Problem**: Cannot connect to license server

**Solutions**:
1. Check internet connection
2. Try again in a few minutes (server may be temporarily unavailable)
3. Use offline mode (if cache is still valid)
4. Contact support if problem persists

### Cache Issues

**Problem**: License shows as expired despite being valid

**Solutions**:
1. Force online verification:
   ```bash
   pyobfus-license status --verify
   ```

2. Remove and re-register:
   ```bash
   pyobfus-license remove
   pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX
   ```

## Support

If you encounter any issues:

**Email**: zhurong0525@gmail.com
**Subject**: "License Activation Issue"
**Include**:
- Your license key
- Error message (if any)
- Python version: `python --version`
- pyobfus version: `pip show pyobfus`
- Operating system

We typically respond within 24 hours.

## FAQ

### How many devices can I use?

Each license works on up to **3 devices** simultaneously.

### Do I need internet to use Pro features?

- **Initial activation**: Yes
- **Regular use**: No (cache valid for 3 days)
- **Verification refresh**: Yes (every 3 days or on-demand)

### What happens if my cache expires?

Pro features will stop working until you verify online again using `pyobfus-license status --verify`.

### Can I share my license?

No. Each license is for individual use. Sharing violates the license agreement and may result in license revocation.

### Is the license lifetime?

Yes. Once purchased, your license never expires. You get all updates to Pro features for free.

### What if I lose my license key?

Contact support at zhurong0525@gmail.com with:
- Email address used for purchase
- Approximate purchase date
- Payment confirmation (if available)

We'll resend your license key to the registered email.

---

**Last Updated**: 2025-12-27
