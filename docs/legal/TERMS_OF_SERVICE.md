# Terms of Service and End User License Agreement (EULA)

**Draft for maintainer review**

**Effective Date: [to be set — at least 30 days after existing customers are notified]**
**Last Updated**: 2026-11-16

This End User License Agreement ("Agreement") is a legal agreement between you (either an individual or a single entity, "Licensee" or "You") and Rong Zhu ("Licensor", "We", "Us") for the use of pyobfus Professional Edition software ("Software").

By purchasing, downloading, installing, or using the Software, you agree to be bound by the terms of this Agreement. If you do not agree to these terms, do not purchase, install, or use the Software.

## 1. License Grant

### 1.1 Grant of License
Subject to your compliance with this Agreement and payment of applicable fees, Licensor grants you a limited, non-exclusive, non-transferable, non-sublicensable license to:

- Install and use the Software on up to three (3) devices that you own or control at a time
- Use the Software for personal or commercial purposes
- Receive all Software updates and upgrades released during the license term

### 1.2 License Type
pyobfus Professional Edition is licensed, not sold. This Agreement only gives you some rights to use the Software. The Licensor reserves all other rights.

### 1.3 Lifetime License
Your license is perpetual and does not expire, subject to compliance with this Agreement. "Lifetime updates" means you will receive all future versions and updates of pyobfus Professional Edition at no additional cost.

## 2. Restrictions

You may NOT:

### 2.1 Distribution and Resale
- Sell, rent, lease, lend, or sublicense the Software
- Distribute, share, or transfer your license key to any third party
- Use a single license for more than three (3) devices at a time
- Provide your license key on public forums, websites, or repositories

### 2.2 Modification and Reverse Engineering
- Reverse engineer, decompile, or disassemble the Professional Edition features
- Modify, adapt, translate, or create derivative works of the Pro features
- Remove, alter, or obscure any proprietary notices or labels on the Software
- Attempt to circumvent or defeat any license verification or protection mechanisms

### 2.3 Prohibited Uses
- Use the Software for any illegal or unauthorized purpose
- Use the Software to create malware or malicious code intended to harm users
- Use the Software in violation of any applicable laws or regulations
- Use the Software in safety-critical applications where failure could lead to death, personal injury, or severe environmental damage

### 2.4 Open Source Components
- The Community Edition of pyobfus remains open source under Apache 2.0
- Professional Edition features are proprietary and not open source
- You may not extract or isolate Professional features to create derivative works

## 3. Device Limit and License Management

### 3.1 Device Limit
- Each license permits activation on up to three (3) devices at a time; activating another device releases the least recently used one
- A "device" is identified by a device identifier, normally a random value saved in `~/.pyobfus/device_id`; if it cannot be saved, a hash of local hardware and system information is used
- You may deactivate the Software on a device to free up an activation slot

### 3.2 Device Management
- To remove only the local license cache, without releasing the server slot: `pyobfus-license remove`
- To transfer to a new device: Run `pyobfus-license deactivate` on the old device to release its server activation slot and remove its local license cache, then activate on the new device
- One-time device reset may be available by contacting support
- A verified device license uses the local cache for three days, then attempts online re-verification. If that fails, including while offline, it falls back to a matching, unexpired cached license. A server response identifying revocation or expiry prevents fallback. Automatic device replacement does not erase the released device's local cache; CI licensing requires online verification for each build

### 3.3 Abuse Detection
- We reserve the right to monitor license usage for abuse (e.g., rapid device switching, excessive activations)
- Suspected license sharing or abuse may result in license suspension
- We will provide warning before suspension when possible

## 4. Payment and Pricing

### 4.1 Payment
- pyobfus Professional Edition is sold for a one-time payment of $45.00 USD
- Payment is processed securely through Stripe
- All prices are in U.S. Dollars unless otherwise stated

### 4.2 Taxes
- Prices do not include applicable sales tax, VAT, or other local taxes
- You are responsible for any taxes required by your jurisdiction
- Stripe may collect tax automatically depending on your location

### 4.3 No Subscription
- This is a one-time payment with no recurring charges
- No subscription fees or renewal costs

## 5. Refund Policy

### 5.1 Money-Back Guarantee
We offer a **30-day money-back guarantee** from the date of purchase.

### 5.2 Refund Eligibility
You may request a full refund within 30 days if:
- You are unsatisfied with the Software for any reason
- The Software does not work as described
- You are unable to activate your license

### 5.3 Refund Process
To request a refund:
1. Email: zhurong0525@gmail.com
2. Subject: "Refund Request - [Your License Key]"
3. Include your purchase email and reason (optional)

We will process your refund within 2 business days. Refunds are issued to the original payment method via Stripe.

### 5.4 After Refund
- Your license will be deactivated
- You may continue using the Community Edition (free version)
- No questions asked policy

## 6. Support and Maintenance

### 6.1 Email Support
Professional Edition includes email support:
- Email: zhurong0525@gmail.com
- Response time goal: Within 24 hours for general inquiries, 12 hours for critical license issues
- Support is provided on a best-effort basis

### 6.2 Updates and Upgrades
- You will receive all future updates and upgrades at no additional cost
- Updates are delivered via PyPI: `pip install --upgrade pyobfus`
- We reserve the right to discontinue updates at any time, but will provide notice

### 6.3 No Service Level Agreement (SLA)
- Support is provided as-is without guaranteed response times
- No uptime guarantees for license verification services
- We will make reasonable efforts to maintain service availability

## 7. Warranty Disclaimer

### 7.1 "AS IS" Basis
THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

### 7.2 No Guarantee of Results
- We do not guarantee that the Software will meet your requirements
- We do not guarantee that operation will be uninterrupted or error-free
- We do not guarantee that all bugs will be corrected
- Use of the Software is at your own risk

### 7.3 Third-Party Services
License verification reads records hosted by Cloudflare. Stripe processes payments and provides payment events used to issue licenses. Resend delivers license and transactional emails. We are not responsible for outages or issues with these services.

## 8. Limitation of Liability

### 8.1 Maximum Liability
TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY SPECIAL, INCIDENTAL, INDIRECT, OR CONSEQUENTIAL DAMAGES WHATSOEVER (INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF BUSINESS PROFITS, BUSINESS INTERRUPTION, LOSS OF BUSINESS INFORMATION, OR ANY OTHER PECUNIARY LOSS) ARISING OUT OF THE USE OF OR INABILITY TO USE THE SOFTWARE.

### 8.2 Liability Cap
Licensor's total liability to you for all damages, losses, and causes of action shall not exceed the amount paid by you for the Software (i.e., $45.00 USD).

### 8.3 Limitations Apply
These limitations apply even if:
- Licensor has been advised of the possibility of such damages
- Any remedy fails of its essential purpose
- The damages were foreseeable

## 9. Intellectual Property

### 9.1 Ownership
- The Software and Professional Edition features are owned by Rong Zhu
- This Agreement does not transfer any ownership rights
- All rights not expressly granted are reserved by Licensor

### 9.2 Trademarks
- "pyobfus" and associated logos are trademarks of Rong Zhu
- You may not use these trademarks without written permission

### 9.3 Feedback
- Any feedback, suggestions, or ideas you provide may be used freely
- You grant Licensor a perpetual, royalty-free license to use such feedback

## 10. Privacy and Data Collection

### 10.1 Data Collected
We collect minimal data for license operation and optional email trials:
- Your email address (for license delivery and support)
- License key and activation status
- Device identifiers (for enforcing 3-device limit)
- Latest license verification/activity times
- Payment information (processed and stored by Stripe)
- Optional email trial: normalised email (trimmed and lowercased), email hash, a trial device identifier (the first 16 hexadecimal characters of a locally generated SHA-256 hash of the MAC-address value and hostname), trial start and end times, and token

### 10.2 Data Use
We use this data solely to:
- Deliver your license key via email
- Verify license validity
- Enforce device limits
- Provide customer support
- Process refunds if requested
- Issue one optional trial per email address, prevent repeat trials, and follow up about your trial

We do not collect your code, build contents, or usage telemetry from obfuscation. The license server records latest verification/activity times to enforce licenses.

### 10.3 Data Storage
- Cloudflare Workers KV: License records including purchaser email, license keys, device identifiers, latest verification/activity times, and payment references; optional email trial records described above
- Stripe: Payment information, purchaser email, and transaction records
- Resend: Recipient email addresses, license keys and other transactional email contents, and delivery records
- License records: Kept while the license exists and as needed for refunds, disputes, or legal obligations
- Device identifiers: Stored as received, without additional server-side hashing. Deactivation removes the active-device entry. Identifiers in the most recent release, eviction, and support-reset records expire after 90 days and are removed on the next record update or weekly cleanup
- Optional email trial records: Plaintext email, trial device identifier, and token are kept until 180 days after the trial ends, then replaced on the next trial-record access or weekly cleanup with a hash-only record to prevent repeat trials. The remaining record contains the email hash and minimal trial timing/status information, with no plaintext email, device identifier, or token
- The 90-day and 180-day limits apply from the retention server update's deployment date, which is still pending for this draft. Cleanup runs on record updates/access as described above and weekly, rather than at the exact expiry time. With that update, legacy CI usage records are reduced to the latest-use time on writes and weekly cleanup
- Stripe holds payment records, and Resend holds email delivery records, under their respective policies and legal requirements

### 10.4 Your Rights
You have the right to:
- Request license deactivation and removal
- Request data deletion, including optional trial data or the hash-only trial record, at zhurong0525@gmail.com (we will remove data from our systems within 30 days where law allows; records needed for legal obligations may be retained)
- Export your license data by contacting support

### 10.5 No Selling of Data
We do not sell, rent, or share your personal information with third parties for marketing purposes.

### 10.6 GDPR Compliance
For users in the European Union, we comply with GDPR requirements. Contact zhurong0525@gmail.com to exercise your data rights.

See the [Privacy Policy](PRIVACY_POLICY.md) for details.

## 11. Termination

### 11.1 Termination by You
You may terminate this Agreement at any time by:
- Uninstalling the Software
- Deactivating this device: `pyobfus-license deactivate`
- Requesting a refund (within 30 days)

### 11.2 Termination by Licensor
We may terminate this Agreement and revoke your license if:
- You violate any terms of this Agreement
- You engage in license abuse or sharing
- You use the Software for illegal purposes
- Chargeback is filed without contacting support first

### 11.3 Effect of Termination
Upon termination:
- Your license will be deactivated
- You must cease all use of Professional Edition features
- You may continue using the Community Edition (free version)
- No refund after 30-day period (unless terminated by Licensor without cause)

## 12. General Provisions

### 12.1 Entire Agreement
This Agreement constitutes the entire agreement between you and Licensor regarding the Software and supersedes all prior agreements and understandings.

### 12.2 Amendments
We reserve the right to modify this Agreement at any time. Changes will be posted with a new "Last Updated" date. Continued use after changes constitutes acceptance.

### 12.3 Governing Law
This Agreement shall be governed by and construed in accordance with the laws of the United States and the State of Washington, without regard to conflict of law principles.

### 12.4 Severability
If any provision of this Agreement is held to be invalid or unenforceable, the remaining provisions shall remain in full force and effect.

### 12.5 Waiver
Failure to enforce any provision of this Agreement shall not constitute a waiver of that provision or any other provision.

### 12.6 Assignment
You may not assign this Agreement or your license without our prior written consent. We may assign this Agreement without restriction.

### 12.7 Contact Information
For questions about this Agreement:
- Email: zhurong0525@gmail.com
- GitHub: https://github.com/zhurong2020/pyobfus

## 13. Acceptance

By completing the purchase and activating your license key, you acknowledge that you have read this Agreement, understand it, and agree to be bound by its terms and conditions.

---

**pyobfus Professional Edition**
Copyright (c) 2025 Rong Zhu
All Rights Reserved
