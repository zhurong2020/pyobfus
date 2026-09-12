/**
 * pyobfus License Server - Cloudflare Worker
 * Handles license verification and Stripe webhook processing
 */

// DRAFT: 嵘说 content membership webhook (not yet enabled in production)
import { handleContentWebhook, verifyStripeSignature } from './content_webhook.js';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // CORS headers for client requests
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Route handler
    try {
      if (url.pathname === '/api/verify' && request.method === 'POST') {
        return await handleVerify(request, env, corsHeaders);
      }

      if (url.pathname === '/api/webhook/stripe' && request.method === 'POST') {
        return await handleStripeWebhook(request, env, corsHeaders);
      }

      // DRAFT route — 嵘说 content membership. Activate by:
      //   1. wrangler secret put STRIPE_WEBHOOK_SECRET_CONTENT / WP_BASE_URL / WP_ADMIN_USERNAME / WP_ADMIN_APP_PASSWORD / WP_JWT_AUTH_KEY
      //   2. Add Stripe webhook endpoint pointing to /api/webhook/stripe-content with this whsec_
      //   3. Test with Stripe CLI: stripe trigger checkout.session.completed --add 'metadata[product_kind]=rongshuo_membership' --add 'metadata[tier]=member'
      if (url.pathname === '/api/webhook/stripe-content' && request.method === 'POST') {
        return await handleContentWebhook(request, env, corsHeaders);
      }

      if (url.pathname === '/api/health') {
        return new Response(JSON.stringify({
          status: 'ok',
          service: 'pyobfus-license-server',
          version: '1.0.0',
          timestamp: new Date().toISOString()
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      return new Response('Not Found', { status: 404 });

    } catch (error) {
      console.error('Error:', error);
      return new Response(JSON.stringify({
        error: 'Internal Server Error',
        message: error.message
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
};

/**
 * Maximum devices kept per licence. Reaching it is no longer an error.
 */
export const MAX_DEVICES = 3;

/**
 * Decide the device list for a verification.
 *
 * This used to refuse the request once three devices were registered, which
 * made lockout inevitable rather than merely possible: nothing ever removed a
 * device, so every reinstall, replacement machine or drifting fingerprint
 * permanently consumed a slot the customer could not reclaim. A customer hit
 * exactly that in 2026-06.
 *
 * Now the oldest device makes way for the newest, so a paying customer is
 * never blocked, while a single key still cannot be used across an unbounded
 * number of machines at once. Legacy records stored bare id strings; those are
 * normalised here and treated as never-seen, so they are evicted first.
 *
 * @param {Array<string|{id: string, last_seen: ?string}>} existing
 * @param {string} deviceId - the device making this request
 * @param {string} nowIso - timestamp to record for it
 * @param {number} maxDevices
 * @returns {{devices: Array<{id: string, last_seen: ?string}>, evicted: string[]}}
 */
export function reconcileDevices(existing, deviceId, nowIso, maxDevices = MAX_DEVICES) {
  const seen = new Set();
  const devices = [];
  for (const entry of Array.isArray(existing) ? existing : []) {
    const id = typeof entry === 'string' ? entry : entry && entry.id;
    if (typeof id !== 'string' || id.length === 0 || seen.has(id)) continue;
    seen.add(id);
    const lastSeen = typeof entry === 'string' ? null : (entry.last_seen ?? null);
    devices.push({ id, last_seen: lastSeen });
  }

  const known = devices.find((d) => d.id === deviceId);
  if (known) {
    known.last_seen = nowIso;
    return { devices, evicted: [] };
  }

  devices.push({ id: deviceId, last_seen: nowIso });
  if (devices.length <= maxDevices) {
    return { devices, evicted: [] };
  }

  // Oldest first. A device with no last_seen has not been used since the field
  // existed, so it goes before any dated one.
  const rank = (d) => (d.last_seen ? Date.parse(d.last_seen) || 0 : 0);
  const byAge = [...devices].sort((a, b) => rank(a) - rank(b));
  const doomed = new Set(byAge.slice(0, devices.length - maxDevices).map((d) => d.id));
  doomed.delete(deviceId); // never evict the device we are answering right now

  return {
    devices: devices.filter((d) => !doomed.has(d.id)),
    evicted: [...doomed],
  };
}

/**
 * Handle license verification request
 * POST /api/verify
 * Body: { license_key: string, device_id: string }
 */
async function handleVerify(request, env, corsHeaders) {
  const body = await request.json();
  const { license_key, device_id } = body;

  // Validate input
  if (!license_key || !device_id) {
    return new Response(JSON.stringify({
      valid: false,
      code: 'bad_request',
      error: 'Missing license_key or device_id'
    }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Fetch license from KV
  const licenseData = await env.LICENSES.get(license_key, { type: 'json' });

  if (!licenseData) {
    return new Response(JSON.stringify({
      valid: false,
      code: 'invalid_key',
      error: 'Invalid license key'
    }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Check if license is active
  if (licenseData.status !== 'active') {
    return new Response(JSON.stringify({
      valid: false,
      code: licenseData.status === 'revoked' ? 'revoked' : 'inactive',
      error: `License is ${licenseData.status}`
    }), {
      status: 403,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Check expiration (if applicable)
  if (licenseData.expires_at) {
    const expiresAt = new Date(licenseData.expires_at);
    if (expiresAt < new Date()) {
      return new Response(JSON.stringify({
        valid: false,
        code: 'expired',
        error: 'License has expired'
      }), {
        status: 403,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }

  // Record this device. Exceeding the cap retires the least recently used
  // device instead of refusing a paying customer (see reconcileDevices).
  const now = new Date().toISOString();
  const { devices, evicted } = reconcileDevices(licenseData.devices, device_id, now);
  licenseData.devices = devices;
  licenseData.last_verified = now;
  if (evicted.length > 0) {
    licenseData.last_evicted = { at: now, devices: evicted };
  }

  // One write, not two: the previous code stored the record twice per request.
  await env.LICENSES.put(license_key, JSON.stringify(licenseData));

  // Return success
  return new Response(JSON.stringify({
    valid: true,
    license_key: license_key,
    email: licenseData.email,
    created_at: licenseData.created_at,
    expires_at: licenseData.expires_at || null,
    features: {
      string_encryption: true,
      anti_debug: true,
      control_flow: false  // v0.3.0
    }
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

/**
 * Handle Stripe webhook
 * POST /api/webhook/stripe
 */
async function handleStripeWebhook(request, env, corsHeaders) {
  const signature = request.headers.get('stripe-signature');
  const body = await request.text();

  // Verify the webhook actually came from Stripe (HMAC-SHA256 over the raw
  // body using STRIPE_WEBHOOK_SECRET, configured via `wrangler secret put`
  // since 2025-11-12 -- this had never actually been checked before,
  // meaning anyone who knew this URL could POST a fake
  // checkout.session.completed payload and mint a free license. Reuses the
  // same verifyStripeSignature() already proven in content_webhook.js
  // (constant-time compare, 5-minute replay window, no Stripe SDK needed).
  const event = await verifyStripeSignature(body, signature, env.STRIPE_WEBHOOK_SECRET);
  if (!event) {
    console.error('Rejected webhook: invalid or missing Stripe signature');
    return new Response(JSON.stringify({ error: 'Invalid signature' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Handle payment success
  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;

    // Generate license key
    const licenseKey = generateLicenseKey();

    // Store license in KV
    const licenseData = {
      license_key: licenseKey,
      email: session.customer_details?.email || session.customer_email,
      status: 'active',
      created_at: new Date().toISOString(),
      stripe_session_id: session.id,
      stripe_customer_id: session.customer,
      devices: [],
      expires_at: null  // Lifetime license
    };

    await env.LICENSES.put(licenseKey, JSON.stringify(licenseData));

    // Send email to customer with license key
    const emailSent = await sendLicenseEmail(
      env.RESEND_API_KEY,
      licenseData.email,
      licenseKey
    );

    console.log('License created:', licenseKey, 'for', licenseData.email, 'Email sent:', emailSent);
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

/**
 * Generate a unique license key
 * Format: PYOB-XXXX-XXXX-XXXX-XXXX (hex characters only)
 */
function generateLicenseKey() {
  const chars = '0123456789ABCDEF';  // HEX only - required by CLI validation
  const segments = 4;
  const segmentLength = 4;

  let key = 'PYOB';
  for (let i = 0; i < segments; i++) {
    key += '-';
    for (let j = 0; j < segmentLength; j++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
  }

  return key;
}

/**
 * Send license key email to customer using Resend
 * @param {string} apiKey - Resend API key
 * @param {string} toEmail - Customer email address
 * @param {string} licenseKey - Generated license key
 * @returns {boolean} - True if email sent successfully
 */
async function sendLicenseEmail(apiKey, toEmail, licenseKey) {
  if (!apiKey) {
    console.error('Resend API key not configured');
    return false;
  }

  if (!toEmail) {
    console.error('No recipient email address');
    return false;
  }

  const emailBody = `Hello,

Thank you for purchasing pyobfus Professional Edition!

════════════════════════════════════════════
YOUR LICENSE KEY
════════════════════════════════════════════

${licenseKey}

════════════════════════════════════════════

IMPORTANT: Please save this email! Your license key cannot be recovered without it.

To activate your license:

1. Install/upgrade pyobfus:
   pip install --upgrade pyobfus

2. Register your license:
   pyobfus-license register ${licenseKey}

3. Verify activation:
   pyobfus-license status

4. Start using Pro features:
   pyobfus input.py -o output.py --level pro

Your license includes:
- AES-256 String Encryption
- Anti-Debugging Checks
- Lifetime Updates (never expires)
- Up to 3 devices

Documentation: https://github.com/zhurong2020/pyobfus
Full Activation Guide: https://github.com/zhurong2020/pyobfus/blob/main/docs/LICENSE_ACTIVATION_GUIDE.md
Support: zhurong0525@gmail.com

Thank you for supporting pyobfus!

Best regards,
The pyobfus Team

---
Note: If you found this email in your spam/junk folder, please mark it as "Not Spam" to ensure you receive future updates.`;

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: 'pyobfus <license@arong.eu.org>',
        to: [toEmail],
        subject: 'Your pyobfus Professional License Key',
        text: emailBody
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Email sent successfully:', data.id);
      return true;
    } else {
      const error = await response.text();
      console.error('Failed to send email:', response.status, error);
      return false;
    }
  } catch (error) {
    console.error('Error sending email:', error);
    return false;
  }
}
