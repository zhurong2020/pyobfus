# Privacy Policy

**Draft for maintainer review**

**Effective Date: [to be set — at least 30 days after existing customers are notified]**
**Last Updated**: 2026-11-16

This Privacy Policy describes how pyobfus ("we", "us", or "our") collects, uses, and shares your personal information when you purchase and use pyobfus Professional Edition or register an optional email trial.

## What Information We Collect

### 1. Information You Provide

**During Purchase:**
- Email address (for license delivery)
- Payment information (processed securely by Stripe, we do not store credit card details)
- Name (optional, if provided during checkout)

**During License Activation:**
- Device identifier (used to enforce the 3-device limit): normally a random value saved in `~/.pyobfus/device_id`; if it cannot be saved, a hash of local hardware and system information is used
- License key
- Latest verification timestamp

**During Optional Email Trial Registration:**
- Email address, normalised by trimming surrounding whitespace and converting it to lowercase
- Trial device identifier: the first 16 hexadecimal characters of a SHA-256 hash of the MAC-address value and hostname, generated locally; the raw values are not sent
- Trial start and end times, an email hash, and a trial token

Without an email address, the trial is recorded locally and no trial registration data is sent to us.

### 2. Information Automatically Collected

**License Verification:**
- Device identifier (as described above)
- Number of currently registered devices
- Latest verification timestamps
- Latest license activity time, including use of the legacy CI verification endpoint

**We do NOT collect:**
- Your source code, obfuscated code, build contents, or usage telemetry from obfuscation
- Browsing history or cookies
- Location data beyond country (for tax purposes via Stripe)

## How We Use Your Information

We use your information solely for the following purposes:

### License Delivery
- Send your license key via email after purchase
- Provide activation instructions and support documentation

### License Verification
- Verify that your license is valid and active
- Enforce the 3-device limit per license
- Prevent license abuse and unauthorized sharing

### Optional Email Trial
- Issue one trial per email address and prevent repeat trials
- Follow up about your trial

### Customer Support
- Respond to your support requests
- Troubleshoot activation issues
- Process refund requests

### Legal Compliance
- Comply with applicable laws and regulations
- Process tax collection (handled by Stripe)
- Respond to legal requests if required

## How We Store Your Information

### Storage Locations

**Cloudflare Workers KV** (License and trial records):
- License keys, purchaser email addresses, activation status, license creation times, and Stripe payment references
- Device identifiers (stored as received, without additional server-side hashing)
- Latest verification/activity times and device release, eviction, and support-reset records
- Optional email trial records: normalised email, email hash, trial device identifier, start and end times, and token
- Location: Cloudflare global network

**Stripe** (Payment data):
- Customer email and payment information
- Transaction records
- Location: Stripe servers (https://stripe.com/privacy)

**Resend** (Email delivery):
- Recipient email addresses, license keys and other transactional email contents, and delivery records
- Location: Resend servers (https://resend.com/legal/privacy-policy)

### Data Security

We implement industry-standard security measures:
- All data transmission uses HTTPS/TLS encryption
- License verification uses secure API endpoints
- No credit card data is stored on our systems (handled by Stripe)
- Device identifiers are stored as received, without additional server-side hashing

## How Long We Keep Your Information

**License Records**: Kept while the license exists and as needed for refunds, disputes, or legal obligations. Active device identifiers are kept to manage activation slots. Deactivation removes the active-device entry.

**Device History**: Device identifiers in the most recent release (`last_released`), eviction (`last_evicted`), and support-reset (`devices_reset`) records expire after 90 days. Expired records are removed on the next record update or weekly cleanup.

**Optional Email Trial Records**: We keep the normalised plaintext email, trial device identifier, and token until 180 days after the trial ends. After that, on the next trial-record access or weekly cleanup, we replace the record with a hash-only record to prevent repeat trials. It retains the email hash and minimal trial timing/status information, with no plaintext email, device identifier, or token.

The 90-day and 180-day limits apply from the retention server update's deployment date, which is still pending for this draft. Cleanup runs on record updates/access as described above and weekly, rather than at the exact expiry time. With that update, legacy CI usage records are reduced to the latest-use time on writes and weekly cleanup.

**Email Delivery and Payment Records**: Resend retains email delivery records under its policy. Stripe holds payment records under its privacy policy and legal requirements. Purchaser email addresses in our Cloudflare license records follow the license-record retention above; optional trial emails follow the trial-record retention above.

**Deletion Requests**: Contact zhurong0525@gmail.com to request deletion, including optional trial data or the hash-only trial record. We remove data from our systems within 30 days where law allows; records needed for legal obligations may be retained.

## Sharing Your Information

We do NOT sell, rent, or trade your personal information to third parties.

### Third-Party Service Providers

We share minimal information with these trusted partners:

**Stripe** (Payment processing):
- Email address, payment information
- Purpose: Process payments, handle refunds, tax compliance
- Privacy Policy: https://stripe.com/privacy

**Resend** (Email delivery):
- Recipient email address, license key and other transactional email contents
- Purpose: Deliver license and transactional emails
- Privacy Policy: https://resend.com/legal/privacy-policy

**Cloudflare** (Infrastructure):
- License records including purchaser email, license keys, device identifiers, latest verification/activity times, and payment references; optional trial records including normalised email, email hash, trial device identifier, trial times, and token
- Purpose: Host license records and verification, manage devices, and register and deduplicate optional email trials
- Privacy Policy: https://www.cloudflare.com/privacypolicy/

### Legal Disclosure

We may disclose your information if required by law or in response to:
- Court orders or subpoenas
- Legal processes or government requests
- Protection of our rights or safety

## Your Rights

Depending on your location, you may have the following rights:

### Access and Portability
- Request a copy of your data
- Export your license information
- Contact: zhurong0525@gmail.com

### Correction
- Update your email address
- Correct inaccurate information
- Contact: zhurong0525@gmail.com

### Deletion (Right to be Forgotten)
- Request deletion of your personal data
- Deactivate and remove your license
- Contact zhurong0525@gmail.com, including for deletion of optional trial data or the hash-only trial record
- We'll remove data from our systems within 30 days where law allows
- Note: Some data may be retained by payment processors for legal compliance

### Device Management
- View this machine's information and cached license status: `pyobfus-license status`
- Release this machine's server activation slot and remove its local license cache on success: `pyobfus-license deactivate`
- Remove only the local license cache, without releasing the server slot: `pyobfus-license remove`
- You can activate on up to three devices at a time; activating another device releases the least recently used one
- Device release retains a release record subject to the 90-day limit and deployment timing described above
- A verified device license uses the local cache for three days, then attempts online re-verification. If that fails, including while offline, it falls back to a matching, unexpired cached license. A server response identifying revocation or expiry prevents fallback. Automatic device replacement does not erase the released device's local cache; CI licensing requires online verification for each build

## GDPR Compliance (EU Users)

If you are located in the European Economic Area (EEA), you have additional rights under GDPR:

### Legal Basis for Processing
- **Contract performance**: License delivery and verification
- **Legitimate interests**: Fraud prevention, customer support
- **Legal obligation**: Tax compliance, payment processing

### Your GDPR Rights
- Right to access your personal data
- Right to rectification of inaccurate data
- Right to erasure ("right to be forgotten")
- Right to restrict processing
- Right to data portability
- Right to object to processing
- Right to withdraw consent

### Exercising Your Rights
Contact us at: zhurong0525@gmail.com
- We'll respond within 30 days
- You may file a complaint with your local data protection authority

## Children's Privacy

pyobfus is not intended for users under 13 years of age. We do not knowingly collect personal information from children. If you believe we have collected information from a child, contact us immediately for deletion.

## International Data Transfers

Your information may be transferred to and processed in:
- United States (Stripe, Resend headquarters)
- European Union (Cloudflare data centers)
- Other countries where our service providers operate

We ensure appropriate safeguards are in place for international transfers in compliance with applicable data protection laws.

## Cookies and Tracking

### Our Website and Software

**We do NOT use cookies or tracking on our GitHub Pages website.**

The pyobfus CLI does not collect your code, build contents, or usage telemetry from obfuscation. The license server records latest verification/activity times to enforce licenses. These are license administration records.

Outbound requests cover license verification, device release, dependency-name lookups on PyPI, and optional email trial registration; see [Network behavior](../NETWORK_BEHAVIOR.md).

### Third-Party Services

When you use Stripe Checkout or visit third-party websites (Stripe, Resend), their privacy policies and cookie policies apply.

## Changes to This Privacy Policy

We may update this Privacy Policy from time to time. Changes will be posted on this page with an updated "Last Updated" date.

**Significant changes** will be communicated via:
- Email to active license holders
- Notice on our GitHub repository
- Updated documentation

Continued use of the Software after changes constitutes acceptance of the updated policy.

## Data Breach Notification

In the unlikely event of a data breach affecting your personal information:
- We will notify affected users within 72 hours
- We will provide details of the breach and steps being taken
- We will offer guidance on protecting your information

## Contact Us

If you have questions or concerns about this Privacy Policy or our data practices:

**Email**: zhurong0525@gmail.com
**GitHub**: https://github.com/zhurong2020/pyobfus
**Response time**: Within 48 hours

For GDPR-related requests, please include "GDPR Request" in your email subject line.

## Transparency

We believe in transparency. If you have questions about:
- What data we have about you
- How we use your data
- How to exercise your rights

Please contact us. We're happy to explain our practices in detail.

---

**pyobfus Professional Edition**
Copyright (c) 2025 Rong Zhu

Last Updated: 2026-11-16

## Summary of changes

- Explained optional email trial data, follow-up, and how to request deletion.
- Clarified what Cloudflare, Stripe, and Resend process.
- Added 90-day device-history and 180-day post-trial retention limits, applying from the server update's deployment, with weekly cleanup.
- Clarified license activity records, automatic device replacement, and local cache/offline behavior.
