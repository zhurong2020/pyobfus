/** Versioned CI-only JWS admission. No state, logging, or production defaults. */
export const CI_PROTOCOL = 'pyobfus-ci-lease-v1';
export const CI_ISSUER = 'pyobfus-license';
export const CI_AUDIENCE = 'pyobfus:ci:build';
export const CI_TOKEN_TYPE = 'pyobfus-ci-lease+jwt';
export const CI_TTL_SECONDS = 300;

function b64url(bytes) {
  return btoa(String.fromCharCode(...bytes)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function decode32(value) {
  if (typeof value !== 'string' || value.length !== 43 || !/^[A-Za-z0-9_-]{43}$/.test(value)) throw new Error('invalid');
  const bytes = Uint8Array.from(atob(value.replace(/-/g, '+').replace(/_/g, '/') + '='), c => c.charCodeAt(0));
  if (bytes.length !== 32 || b64url(bytes) !== value) throw new Error('invalid');
  return bytes;
}

export function validNonce(value) {
  try { decode32(value); return true; } catch { return false; }
}

export function ciResponse(data, corsHeaders, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }
  });
}

export async function readCiRequest(request) {
  // Bound actual streamed bytes rather than trusting Content-Length.
  if (!request.body) throw new Error('invalid');
  const reader = request.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let total = 0, text = '';
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      total += value.length;
      if (total > 4096) throw new Error('invalid');
      text += decoder.decode(value, { stream: true });
    }
    text += decoder.decode();
    const body = JSON.parse(text);
    if (!body || Array.isArray(body) || typeof body !== 'object' ||
        Object.keys(body).sort().join(',') !== 'activation,license_key,nonce,protocol' ||
        body.activation !== 'ci' || body.protocol !== CI_PROTOCOL || !validNonce(body.nonce) ||
        typeof body.license_key !== 'string' || body.license_key.length !== 24 ||
        !/^PYOB-(?:[A-Fa-f0-9]{4}-){3}[A-Fa-f0-9]{4}$/.test(body.license_key)) {
      throw new Error('invalid');
    }
    return body;
  } catch {
    await reader.cancel().catch(() => {});
    throw new Error('Invalid CI lease request');
  } finally {
    reader.releaseLock();
  }
}

export async function issueCiLease(env, licenseKey, nonce, licenseExpiry) {
  // This binding must be provisioned separately. Never generate a fallback key.
  const kid = env.CI_SIGNING_KEY_ID;
  if (typeof kid !== 'string' || kid.length < 1 || kid.length > 64 || /[^A-Za-z0-9_-]/.test(kid) ||
      typeof env.CI_SIGNING_PRIVATE_JWK !== 'string' || env.CI_SIGNING_PRIVATE_JWK.length > 2048) {
    throw new Error('CI signer unavailable');
  }
  const secret = JSON.parse(env.CI_SIGNING_PRIVATE_JWK);
  if (!secret || secret.kty !== 'OKP' || secret.crv !== 'Ed25519') throw new Error('CI signer unavailable');
  decode32(secret.d); decode32(secret.x);
  const privateKey = await crypto.subtle.importKey('jwk', {
    kty: 'OKP', crv: 'Ed25519', d: secret.d, x: secret.x,
  }, 'Ed25519', false, ['sign']);
  const publicKey = await crypto.subtle.importKey('jwk', {
    kty: 'OKP', crv: 'Ed25519', x: secret.x,
  }, 'Ed25519', false, ['verify']);
  const issued = Math.floor(Date.now() / 1000);
  let expires = issued + CI_TTL_SECONDS;
  if (licenseExpiry != null) {
    if (typeof licenseExpiry !== 'string') throw new Error('CI signer unavailable');
    const deadline = Math.floor(Date.parse(licenseExpiry) / 1000);
    if (!Number.isSafeInteger(deadline) || deadline <= issued) throw new Error('CI signer unavailable');
    expires = Math.min(expires, deadline);
  }
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(licenseKey));
  const sub = 'sha256:' + [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
  const header = { alg: 'Ed25519', typ: CI_TOKEN_TYPE, kid };
  const claims = { v: 1, iss: CI_ISSUER, aud: CI_AUDIENCE, sub, activation: 'ci',
    entitlements: ['build:pro'], nonce, iat: issued, nbf: issued, exp: expires };
  const encode = value => b64url(new TextEncoder().encode(JSON.stringify(value)));
  const signingInput = encode(header) + '.' + encode(claims);
  const message = new TextEncoder().encode(signingInput);
  const signature = await crypto.subtle.sign('Ed25519', privateKey, message);
  // Catch misconfigured x/d components without exposing key material in logs.
  if (!await crypto.subtle.verify('Ed25519', publicKey, signature, message)) {
    throw new Error('CI signer unavailable');
  }
  return { protocol: CI_PROTOCOL, lease: signingInput + '.' + b64url(new Uint8Array(signature)) };
}
