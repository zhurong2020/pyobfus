/**
 * 嵘说 Content Membership - Stripe Webhook Handler
 *
 * Status: DRAFT — wired into index.js but not yet deployed.
 * Handoff doc: ~/projects/openclaw-server/docs/HANDOFF_2026-04-27_CONTENT_TIERED_PAYWALL.md
 * Purpose: 处理嵘说会员/Pro 的 Stripe Checkout 完成事件，
 *          通过 WP Simple-JWT-Login API 给 WordPress 用户加角色。
 *
 * KV layout (shared with pyobfus license namespace, prefix-isolated):
 *   content:order:{stripe_session_id}  → { email, tier, granted_at, wp_user_id }
 *   content:event:{stripe_event_id}    → "1"   (idempotency marker, TTL 30d)
 *
 * Required env (configure via `wrangler secret put`, NOT in wrangler.toml):
 *   STRIPE_WEBHOOK_SECRET_CONTENT  — 嵘说 webhook 单独的 whsec_  (与 pyobfus 隔离)
 *   WP_BASE_URL                    — 例: https://www.arong.eu.org
 *   WP_JWT_AUTH_KEY                — Simple-JWT-Login plugin AUTH_KEY
 *   WP_ADMIN_USERNAME              — WP 管理员用户名 (用于 JWT 自登录)
 *   WP_ADMIN_APP_PASSWORD          — WP Application Password (NOT 主密码)
 *
 * Required Stripe Product metadata:
 *   metadata.product_kind = "rongshuo_membership"
 *   metadata.tier         = "member" | "pro"
 *   (用 metadata 区分 vs pyobfus 订单, 避免误处理)
 */

/**
 * Verify Stripe webhook signature (Web Crypto, no Stripe SDK needed)
 * @returns {Promise<object|null>} parsed event if valid, null otherwise
 */
async function verifyStripeSignature(rawBody, signatureHeader, webhookSecret) {
  if (!signatureHeader || !webhookSecret) return null;

  // Stripe-Signature: t=1234567890,v1=abc123...,v0=...
  const parts = Object.fromEntries(
    signatureHeader.split(',').map(p => p.split('='))
  );
  if (!parts.t || !parts.v1) return null;

  // Reject events older than 5 minutes (replay protection)
  const timestamp = parseInt(parts.t, 10);
  if (Math.abs(Date.now() / 1000 - timestamp) > 300) return null;

  // HMAC-SHA256 of "{timestamp}.{rawBody}"
  const payload = `${parts.t}.${rawBody}`;
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(webhookSecret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const sig = await crypto.subtle.sign(
    'HMAC',
    key,
    new TextEncoder().encode(payload)
  );
  const expected = Array.from(new Uint8Array(sig))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  // Constant-time compare
  if (expected.length !== parts.v1.length) return null;
  let mismatch = 0;
  for (let i = 0; i < expected.length; i++) {
    mismatch |= expected.charCodeAt(i) ^ parts.v1.charCodeAt(i);
  }
  if (mismatch !== 0) return null;

  try {
    return JSON.parse(rawBody);
  } catch {
    return null;
  }
}

/**
 * Map Stripe session to membership tier.
 * Reads from session.metadata or expanded line_items product metadata.
 */
function extractTier(session) {
  // Preferred: set in Stripe Checkout Session creation
  if (session.metadata?.product_kind === 'rongshuo_membership') {
    const tier = session.metadata.tier;
    if (tier === 'member' || tier === 'pro') return tier;
  }
  return null; // not our product, ignore
}

/**
 * Grant WP role via Simple-JWT-Login + WP REST API.
 *
 * Flow:
 *  1. Look up user by email via WP REST /wp/v2/users (admin auth)
 *  2. If not found, register via Simple-JWT-Login /users endpoint
 *  3. Add role (rongshuo_member or rongshuo_pro) via /wp/v2/users/{id}
 *
 * NOTE: WP Application Password is recommended over Simple-JWT-Login token
 *       for server-to-server. This draft uses Application Password basic auth.
 */
async function grantWpRole(env, email, tier) {
  if (!env.WP_BASE_URL || !env.WP_ADMIN_USERNAME || !env.WP_ADMIN_APP_PASSWORD) {
    throw new Error('WP credentials not configured');
  }

  const role = tier === 'pro' ? 'rongshuo_pro' : 'rongshuo_member';
  const authHeader = 'Basic ' + btoa(
    `${env.WP_ADMIN_USERNAME}:${env.WP_ADMIN_APP_PASSWORD}`
  );

  // 1. Find or create user
  let userId = null;

  // Search by email (requires admin auth)
  const searchUrl = `${env.WP_BASE_URL}/wp-json/wp/v2/users?search=${encodeURIComponent(email)}&context=edit`;
  const searchRes = await fetch(searchUrl, {
    headers: { 'Authorization': authHeader }
  });

  if (searchRes.ok) {
    const users = await searchRes.json();
    const match = users.find(u => u.email?.toLowerCase() === email.toLowerCase());
    if (match) userId = match.id;
  }

  // 2. Register if not found (via Simple-JWT-Login /users)
  if (!userId) {
    if (!env.WP_JWT_AUTH_KEY) {
      throw new Error('WP_JWT_AUTH_KEY not configured (required for new user registration)');
    }
    const registerRes = await fetch(
      `${env.WP_BASE_URL}/?rest_route=/simple-jwt-login/v1/users&AUTH_KEY=${env.WP_JWT_AUTH_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: crypto.randomUUID(), // user resets via "Forgot Password"
          // role: role,  // ⚠️ Simple-JWT-Login does not allow setting custom role here
        })
      }
    );
    if (!registerRes.ok) {
      const err = await registerRes.text();
      throw new Error(`User registration failed: ${registerRes.status} ${err}`);
    }
    const reg = await registerRes.json();
    userId = reg.data?.user?.ID || reg.data?.ID;
    if (!userId) throw new Error('Registered user but got no ID back');
  }

  // 3. Set role via WP REST (Application Password auth)
  const updateRes = await fetch(
    `${env.WP_BASE_URL}/wp-json/wp/v2/users/${userId}`,
    {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ roles: [role] })
    }
  );
  if (!updateRes.ok) {
    const err = await updateRes.text();
    throw new Error(`Role grant failed: ${updateRes.status} ${err}`);
  }

  return { userId, role };
}

/**
 * Main handler — wire into index.js as:
 *   if (url.pathname === '/api/webhook/stripe-content' && request.method === 'POST') {
 *     return await handleContentWebhook(request, env, corsHeaders);
 *   }
 */
export async function handleContentWebhook(request, env, corsHeaders) {
  const rawBody = await request.text();
  const signatureHeader = request.headers.get('stripe-signature');

  // 1. Verify signature
  const event = await verifyStripeSignature(
    rawBody,
    signatureHeader,
    env.STRIPE_WEBHOOK_SECRET_CONTENT
  );
  if (!event) {
    return new Response(
      JSON.stringify({ error: 'Invalid signature' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // 2. Idempotency: skip if event already processed
  const eventKey = `content:event:${event.id}`;
  const seen = await env.LICENSES.get(eventKey);
  if (seen) {
    return new Response(
      JSON.stringify({ received: true, status: 'already_processed' }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // 3. Only handle checkout.session.completed
  if (event.type !== 'checkout.session.completed') {
    return new Response(
      JSON.stringify({ received: true, status: 'ignored', reason: 'not a relevant event' }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  const session = event.data.object;
  const tier = extractTier(session);

  // 4. Not our product (likely pyobfus or other) → ignore silently
  if (!tier) {
    return new Response(
      JSON.stringify({ received: true, status: 'ignored', reason: 'not a rongshuo_membership product' }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  const email = session.customer_details?.email || session.customer_email;
  if (!email) {
    console.error('No email in session', session.id);
    return new Response(
      JSON.stringify({ error: 'No customer email' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // 5. Grant role on WP
  let result;
  try {
    result = await grantWpRole(env, email, tier);
  } catch (err) {
    console.error('grantWpRole failed:', err.message);
    // Return 500 so Stripe retries (up to 3 days, exp backoff)
    return new Response(
      JSON.stringify({ error: 'Role grant failed', message: err.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // 6. Persist order record + idempotency marker
  await env.LICENSES.put(
    `content:order:${session.id}`,
    JSON.stringify({
      email,
      tier,
      stripe_session_id: session.id,
      stripe_customer_id: session.customer,
      wp_user_id: result.userId,
      wp_role: result.role,
      granted_at: new Date().toISOString(),
      stripe_event_id: event.id
    })
  );
  await env.LICENSES.put(eventKey, '1', { expirationTtl: 30 * 24 * 3600 });

  // 7. TODO: Send welcome email via Resend (mirror sendLicenseEmail pattern in index.js)
  //         Include: WP login URL, "forgot password" reminder, Discord invite link, member benefits.

  console.log(`Granted ${result.role} to ${email} (WP user ${result.userId}) for session ${session.id}`);

  return new Response(
    JSON.stringify({
      received: true,
      status: 'granted',
      tier,
      wp_user_id: result.userId
    }),
    { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}
