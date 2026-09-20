import assert from 'node:assert/strict';
import test from 'node:test';

import worker, { isValidEmail, normalizeEmail, TRIAL_DURATION_DAYS } from '../src/index.js';

/** Minimal in-memory stand-in for the LICENSES KV namespace. */
function fakeKv(seed = {}) {
  const store = new Map(Object.entries(seed).map(([k, v]) => [k, JSON.stringify(v)]));
  return {
    store,
    async get(key, opts) {
      const raw = store.get(key);
      if (raw === undefined) return null;
      return opts && opts.type === 'json' ? JSON.parse(raw) : raw;
    },
    async put(key, value) {
      store.set(key, value);
    },
  };
}

function post(body, headers = {}) {
  return new Request('https://example.workers.dev/api/trial/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
}

const ENV = () => ({ LICENSES: fakeKv(), TRIAL_SIGNING_SECRET: 'unit-test-secret' });

test('isValidEmail gates obvious junk without pretending to prove identity', () => {
  assert.equal(isValidEmail('a@b.co'), true);
  assert.equal(isValidEmail('no-at-sign'), false);
  assert.equal(isValidEmail('a@b'), false);
  assert.equal(isValidEmail(''), false);
  assert.equal(isValidEmail(undefined), false);
  assert.equal(isValidEmail('x@y.' + 'z'.repeat(300)), false);
});

test('normalizeEmail lower-cases and trims so casing does not split a trial', () => {
  assert.equal(normalizeEmail('  Foo@Bar.COM '), 'foo@bar.com');
});

test('issues a fresh 5-day trial for a new email', async () => {
  const env = ENV();
  const res = await worker.fetch(post({ email: 'new@example.com', device_id: 'dev-1' }), env);
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.status, 'issued');
  assert.equal(data.active, true);
  assert.equal(data.days_remaining, TRIAL_DURATION_DAYS);
  assert.match(data.token, /^[0-9a-f]{64}$/); // HMAC-SHA256 hex
  const ms = new Date(data.expires) - new Date(data.started);
  assert.equal(Math.round(ms / (24 * 3600 * 1000)), 5);
});

test('dedup: same email never gets a second fresh trial', async () => {
  const env = ENV();
  const first = await (await worker.fetch(post({ email: 'dup@example.com', device_id: 'dev-1' }), env)).json();
  // second request, even from a different device, must NOT extend
  const second = await (await worker.fetch(post({ email: 'dup@example.com', device_id: 'dev-2' }), env)).json();
  assert.equal(second.status, 'already_issued');
  assert.equal(second.email_known, true);
  assert.equal(second.token, first.token);
  assert.equal(second.expires, first.expires);
});

test('dedup is case-insensitive', async () => {
  const env = ENV();
  const a = await (await worker.fetch(post({ email: 'Case@Example.com', device_id: 'd' }), env)).json();
  const b = await (await worker.fetch(post({ email: 'case@example.com', device_id: 'd' }), env)).json();
  assert.equal(b.status, 'already_issued');
  assert.equal(b.token, a.token);
});

test('rejects a missing or malformed email / device_id with 400', async () => {
  const env = ENV();
  for (const body of [
    { device_id: 'd' },
    { email: 'not-an-email', device_id: 'd' },
    { email: 'ok@example.com' },
    { email: 'ok@example.com', device_id: '' },
  ]) {
    const res = await worker.fetch(post(body), env);
    assert.equal(res.status, 400, JSON.stringify(body));
    assert.equal((await res.json()).code, 'bad_request');
  }
});

test('fails closed when the signing secret is not configured', async () => {
  const res = await worker.fetch(
    post({ email: 'ok@example.com', device_id: 'd' }),
    { LICENSES: fakeKv() } // no TRIAL_SIGNING_SECRET
  );
  assert.equal(res.status, 500);
  assert.equal((await res.json()).code, 'not_configured');
});

test('stores email hash under a trial: key and never issues an unsigned token', async () => {
  const env = ENV();
  await worker.fetch(post({ email: 'store@example.com', device_id: 'd' }), env);
  const keys = [...env.LICENSES.store.keys()];
  assert.equal(keys.length, 1);
  assert.match(keys[0], /^trial:[0-9a-f]{64}$/);
});
