# License Activation Guide

This guide explains how to activate and manage your pyobfus Professional Edition license.

## Prerequisites

- Python 3.9 or higher
- pyobfus installed: `pip install --upgrade pyobfus` (0.5.26 or later recommended; see
  [Troubleshooting](#license-verification-failed-access-denied-or-request-blocked) if you are on an older version)
- Your license key (`PYOB-XXXX-XXXX-XXXX-XXXX`), sent by email right after purchase

> **Important**: The license key email comes from `license@arong.eu.org` and may land in your **Spam/Junk folder**. Check there if it has not arrived within a few minutes of purchase.

## Try Before You Buy

Not sure Pro is right for you? Try it free for 5 days. No credit card is required and the email is optional:

```bash
pyobfus-trial start                        # or: pyobfus-trial start --email you@example.com
pyobfus input.py -o output.py --string-encryption --anti-debug
pyobfus-trial status
```

## Quick Activation

```bash
# 1. Install or upgrade pyobfus
pip install --upgrade pyobfus

# 2. Register your license (verifies it online and registers this machine)
pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX

# 3. Check it
pyobfus-license status
```

A successful registration prints `✓ License verified successfully!`. After that, Pro features are
available, for example:

```bash
pyobfus input.py -o output.py --level pro
pyobfus input.py -o output.py --string-encryption --anti-debug --control-flow
```

Run `pyobfus --help` for the full list of Pro options (string encryption, control-flow flattening,
dead-code injection, anti-debugging, runtime string vault, expiry and device binding, and more).

## Managing Your License

### Check status

```bash
pyobfus-license status            # local information: key, type, expiry, last verification, this device
pyobfus-license status --verify   # also re-check the license online
pyobfus-license status --json     # machine-readable output
```

### Devices

Each license can be active on **up to 3 devices** at a time. Registering a fourth device does not fail:
the device you have not used for the longest time is released automatically to make room.

### Move to another machine

1. **On the old machine**, release its device slot (needs internet):

   ```bash
   pyobfus-license deactivate
   ```

   This frees the slot on the license server and removes the local license from that machine.

2. **On the new machine**:

   ```bash
   pip install --upgrade pyobfus
   pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX
   ```

If the old machine is gone or no longer works, skip step 1. Once you register more than 3 devices, the
least recently used one is released automatically.

> `pyobfus-license remove` only deletes the license stored on this machine. It does **not** free the
> device slot on the server. Use `deactivate` when you want the slot back.

## Offline Use

After a successful online verification the license is stored locally (`~/.pyobfus/license.json`, or
`%USERPROFILE%\.pyobfus\license.json` on Windows) and pyobfus does not need to contact the server
again for 3 days.

After that, pyobfus tries to re-verify online. **If the server cannot be reached, Pro keeps working from
the stored license.** It stops only if the server actively reports that the license has been revoked
or has expired.

## Troubleshooting

### "License verification failed ... Access denied" or "request blocked"

Versions of pyobfus **before 0.5.26** cannot reach the license server: a network filter in front of
the server rejects their requests, which older versions report as `Access denied`. Your key is fine.

- **Recommended**: upgrade, then register again:

  ```bash
  pip install --upgrade pyobfus
  pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX
  ```

- **If you cannot upgrade right now**, register without the online check:

  ```bash
  pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX --no-verify
  ```

  This unlocks Pro on this machine immediately and keeps working, but the machine is not recorded on
  the server.

### "License not found" or "Invalid license key"

1. Copy and paste the key from the purchase email instead of typing it.
2. Make sure the key starts with `PYOB-`.
3. If the key is definitely correct, contact support (below).

### "Could not reach the license server"

Check your internet connection or proxy and try again later. With an already stored license, Pro keeps
working in the meantime (see [Offline Use](#offline-use)). With `deactivate`, nothing is changed
locally, so you can simply retry.

### "License is revoked" or "License has expired"

The server reports that this license is no longer valid. Contact support with your license key.

## Support

For license or billing questions (lost key, invoice, activation problems), email
**zhurong0525@gmail.com** with the subject "License Activation Issue" and include:

- your license key, or the email address used for purchase
- the exact error message
- `pyobfus --version`, `python --version`, and your operating system

For bugs and feature requests, please use
[GitHub Issues](https://github.com/zhurong2020/pyobfus/issues).

## FAQ

### How many devices can I use?

Up to **3 devices** at a time. Use `pyobfus-license deactivate` to release one yourself; otherwise the
least recently used device is released when you register a fourth.

### Do I need internet to use Pro features?

Only to register a machine and, occasionally, to re-verify. If the server cannot be reached, Pro keeps
working from the stored license.

### Is the license lifetime?

Yes. The license does not expire, and future Pro updates are included at no extra cost.

### What if I lose my license key?

Email support from the address you used for the purchase (or include it, plus the approximate purchase
date). We will resend the key to that address.

### Can I share my license?

No. Each license is for the purchaser's own use. See the Terms of Service.

---

**Last Updated**: 2026-10-05
