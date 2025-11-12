# Privacy Policy

**Effective Date**: November 12, 2025
**Last Updated**: November 12, 2025

This Privacy Policy describes how pyobfus ("we", "us", or "our") collects, uses, and shares your personal information when you purchase and use pyobfus Professional Edition.

## What Information We Collect

### 1. Information You Provide

**During Purchase:**
- Email address (for license delivery)
- Payment information (processed securely by Stripe, we do not store credit card details)
- Name (optional, if provided during checkout)

**During License Activation:**
- Device fingerprint (generated locally, used to enforce 3-device limit)
- License key
- Activation timestamp

### 2. Information Automatically Collected

**License Verification:**
- Device fingerprint (hashed hardware identifiers)
- Activation count
- Timestamp of verification requests

**We do NOT collect:**
- Your obfuscated code or any source code you process
- Browsing history or cookies
- Location data beyond country (for tax purposes via Stripe)
- Any personal information beyond what's necessary for license operation

## How We Use Your Information

We use your information solely for the following purposes:

### License Delivery
- Send your license key via email after purchase
- Provide activation instructions and support documentation

### License Verification
- Verify that your license is valid and active
- Enforce the 3-device limit per license
- Prevent license abuse and unauthorized sharing

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

**Cloudflare Workers KV** (License data):
- License keys and activation status
- Device fingerprints (hashed)
- Activation timestamps
- Location: Cloudflare global network

**Stripe** (Payment data):
- Customer email and payment information
- Transaction records
- Location: Stripe servers (https://stripe.com/privacy)

**Resend** (Email delivery):
- Email addresses and delivery logs
- Location: Resend servers (https://resend.com/legal/privacy-policy)

### Data Security

We implement industry-standard security measures:
- All data transmission uses HTTPS/TLS encryption
- License verification uses secure API endpoints
- No credit card data is stored on our systems (handled by Stripe)
- Device fingerprints are hashed before storage

## How Long We Keep Your Information

**License Data**: As long as your license is active
- If you deactivate: Device data is removed immediately
- If you request deletion: All data removed within 30 days

**Email Records**: Stored in Stripe and Resend systems according to their retention policies
- Stripe: For tax compliance and fraud prevention (typically 7 years)
- Resend: Email logs retained for 30 days

**Payment Records**: Stripe retains payment data according to their privacy policy and legal requirements

## Sharing Your Information

We do NOT sell, rent, or trade your personal information to third parties.

### Third-Party Service Providers

We share minimal information with these trusted partners:

**Stripe** (Payment processing):
- Email address, payment information
- Purpose: Process payments, handle refunds, tax compliance
- Privacy Policy: https://stripe.com/privacy

**Resend** (Email delivery):
- Email address, license key
- Purpose: Send license keys and support emails
- Privacy Policy: https://resend.com/legal/privacy-policy

**Cloudflare** (Infrastructure):
- License verification requests, device fingerprints
- Purpose: License storage and verification
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
- We'll remove data from our systems within 30 days
- Note: Some data may be retained by payment processors for legal compliance

### Device Management
- View your activated devices: `pyobfus-license status`
- Remove a device: `pyobfus-license remove`
- This removes device data immediately

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

**The pyobfus CLI tool does NOT:**
- Track your usage
- Collect analytics
- Send telemetry data
- Phone home (except for license verification)

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

Last Updated: November 12, 2025
