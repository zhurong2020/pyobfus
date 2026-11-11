import assert from 'node:assert/strict';
import test from 'node:test';
import { webcrypto } from 'node:crypto';
import worker from '../src/index.js';
import { CI_PROTOCOL, CI_TOKEN_TYPE } from '../src/ci_lease.js';

if (!globalThis.crypto) globalThis.crypto = webcrypto;
const licenseKey = 'PYOB-AAAA-BBBB-CCCC-DDDD';
const nonce = Buffer.alloc(32, 1).toString('base64url');
const active = { status: 'active', expires_at: null, devices: ['existing-device'], email: 'private-field' };

async function issuer() {
  const pair = await crypto.subtle.generateKey('Ed25519', true, ['sign', 'verify']);
  return { CI_SIGNING_KEY_ID: 'test-issuer',
    CI_SIGNING_PRIVATE_JWK: JSON.stringify(await crypto.subtle.exportKey('jwk', pair.privateKey)),
    publicKey: pair.publicKey };
}

async function verify({ config, record = active, body, raw, limiter } = {}) {
  let reads = 0, writes = 0;
  const env = { ...config, CI_RATE_LIMITER: limiter, LICENSES: {
    async get(key) { reads++; assert.equal(key, licenseKey); return structuredClone(record); },
    async put() { writes++; throw new Error('signed CI must not rewrite license records'); }
  } };
  const req = new Request('https://example.com/api/ci/lease', { method: 'POST',
    body: raw === undefined ? JSON.stringify(body || { license_key: licenseKey, activation: 'ci', protocol: CI_PROTOCOL, nonce }) : raw });
  const res = await worker.fetch(req, env);
  return { res, data: await res.json(), reads, writes };
}

test('signed CI: fixed profile, verifiable signature, no key/email/devices/KV writes', async () => {
  const config = await issuer();
  const { res, data, reads, writes } = await verify({ config });
  assert.equal(res.status, 200);
  assert.equal(res.headers.get('Cache-Control'), 'no-store');
  assert.deepEqual(Object.keys(data).sort(), ['lease', 'protocol']);
  assert.equal(data.protocol, CI_PROTOCOL);
  const [h, p, s] = data.lease.split('.');
  const header = JSON.parse(Buffer.from(h, 'base64url'));
  const payload = JSON.parse(Buffer.from(p, 'base64url'));
  assert.deepEqual(header, { alg: 'Ed25519', typ: CI_TOKEN_TYPE, kid: 'test-issuer' });
  assert.equal(payload.nonce, nonce);
  assert.equal(payload.activation, 'ci');
  assert.equal(payload.iss, 'pyobfus-license');
  assert.equal(payload.aud, 'pyobfus:ci:build');
  assert.deepEqual(payload.entitlements, ['build:pro']);
  assert.match(payload.sub, /^sha256:[a-f0-9]{64}$/);
  assert.equal(payload.iat, payload.nbf);
  assert.equal(payload.exp - payload.iat, 300);
  assert.equal(reads, 1); assert.equal(writes, 0);
  assert.ok(await crypto.subtle.verify('Ed25519', config.publicKey,
    Buffer.from(s, 'base64url'), Buffer.from(h + '.' + p)));
  assert.ok(!JSON.stringify(data).includes(licenseKey));
  assert.ok(!Buffer.from(p, 'base64url').toString().includes('private-field'));
});

for (const [label, change] of [
  ['missing protocol', { protocol: undefined }], ['wrong protocol', { protocol: 'old' }],
  ['wrong activation', { activation: 'offline' }], ['bad nonce', { nonce: 'x' }],
  ['noncanonical nonce', { nonce: nonce.slice(0, -1) + 'B' }],
  ['device input', { device_id: 'runner' }], ['object license', { license_key: {} }],
]) test(`request rejection before storage: ${label}`, async () => {
  const r = await verify({ body: { license_key: licenseKey, activation: 'ci', protocol: CI_PROTOCOL, nonce, ...change } });
  assert.equal(r.res.status, 400); assert.equal(r.reads, 0); assert.equal(r.writes, 0);
});
for (const raw of ['null', '[]', '{', 'x'.repeat(4097)]) test(`invalid or oversized body ${raw.length}`, async () => {
  const r = await verify({ raw });
  assert.equal(r.res.status, 400); assert.equal(r.reads, 0);
});

for (const [label, record, status] of [
  ['invalid', null, 404], ['revoked', { ...active, status: 'revoked' }, 403],
  ['expired', { ...active, expires_at: '2000-01-01' }, 403],
]) test(`signed CI ${label} denied`, async () => {
  const r = await verify({ record });
  assert.equal(r.res.status, status); assert.equal(r.writes, 0);
});

test('rate limiter uses a digest and does not invoke a signer or mutate records', async () => {
  const r = await verify({ limiter: { async limit({ key }) {
    assert.match(key, /^[a-f0-9]{64}$/); return { success: false };
  } } });
  assert.equal(r.res.status, 429); assert.equal(r.writes, 0);
});

test('license term caps admission proof lifetime', async () => {
  const deadline = Math.floor(Date.now() / 1000) + 90;
  const r = await verify({ config: await issuer(), record: { ...active, expires_at: new Date(deadline * 1000).toISOString() } });
  assert.equal(r.res.status, 200);
  assert.equal(JSON.parse(Buffer.from(r.data.lease.split('.')[1], 'base64url')).exp, deadline);
});

test('misconfigured signer fails closed without exposing secrets or logging exceptions', async (t) => {
  const logs = [];
  t.mock.method(console, 'error', (...args) => logs.push(args));
  const config = await issuer();
  const other = await issuer();
  const mismatched = JSON.parse(config.CI_SIGNING_PRIVATE_JWK);
  mismatched.x = JSON.parse(other.CI_SIGNING_PRIVATE_JWK).x;
  for (const candidate of [undefined, { ...config, CI_SIGNING_PRIVATE_JWK: licenseKey },
    { ...config, CI_SIGNING_KEY_ID: '../key' },
    { ...config, CI_SIGNING_PRIVATE_JWK: JSON.stringify(mismatched) }]) {
    const r = await verify({ config: candidate });
    assert.equal(r.res.status, 503);
    assert.equal(r.writes, 0);
    assert.deepEqual(r.data, { valid: false, code: 'unavailable', error: 'CI verification unavailable' });
  }
  assert.deepEqual(logs, []);
});

test('invalid stored expiry never yields a signed success', async () => {
  const r = await verify({ config: await issuer(), record: { ...active, expires_at: 'not-a-date' } });
  assert.equal(r.res.status, 503); assert.equal(r.writes, 0);
});
