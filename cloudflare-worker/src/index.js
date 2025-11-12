/**
 * pyobfus License Server - Cloudflare Worker
 * Handles license verification and Stripe webhook processing
 */

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
        error: 'License has expired'
      }), {
        status: 403,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }

  // Check device limit (allow up to 3 devices)
  if (!licenseData.devices) {
    licenseData.devices = [];
  }

  if (!licenseData.devices.includes(device_id)) {
    if (licenseData.devices.length >= 3) {
      return new Response(JSON.stringify({
        valid: false,
        error: 'Device limit reached (max 3 devices)'
      }), {
        status: 403,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Add new device
    licenseData.devices.push(device_id);
    await env.LICENSES.put(license_key, JSON.stringify(licenseData));
  }

  // Update last verified timestamp
  licenseData.last_verified = new Date().toISOString();
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

  // TODO: Verify Stripe signature (需要 Stripe webhook secret)
  // For now, we'll implement basic processing

  let event;
  try {
    event = JSON.parse(body);
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
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
 * Format: PYOBFUS-XXXX-XXXX-XXXX-XXXX
 */
function generateLicenseKey() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const segments = 4;
  const segmentLength = 4;

  let key = 'PYOBFUS';
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

Your license key is:
${licenseKey}

To activate your license:

1. Install pyobfus:
   pip install --upgrade pyobfus

2. Register your license:
   pyobfus-license register ${licenseKey}

3. Verify activation:
   pyobfus-license status

Documentation: https://github.com/zhurong2020/pyobfus
Support: zhurong0525@gmail.com

Your license includes:
- AES-256 String Encryption
- Anti-Debugging Checks
- Lifetime Updates
- Up to 3 devices

Thank you for supporting pyobfus!

Best regards,
The pyobfus Team`;

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: 'pyobfus <onboarding@resend.dev>',
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
