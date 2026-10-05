import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import test from 'node:test';

import worker, { buildLicenseEmailBody, deriveLicenseKey } from '../src/index.js';

const SECRET = 'whsec_test_only';

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

/** A webhook request signed the way Stripe signs it. */
function stripeRequest(event, secret = SECRET) {
  const body = JSON.stringify(event);
  const t = Math.floor(Date.now() / 1000);
  const v1 = createHmac('sha256', secret).update(`${t}.${body}`).digest('hex');
  return new Request('https://example.workers.dev/api/webhook/stripe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'stripe-signature': `t=${t},v1=${v1}` },
    body,
  });
}

function sessionEvent(type, paymentStatus, id = 'cs_live_example') {
  return {
    type,
    data: {
      object: {
        id,
        payment_status: paymentStatus,
        customer: null,
        customer_details: { email: 'buyer@example.com' },
      },
    },
  };
}

// No RESEND_API_KEY: sendLicenseEmail returns early without any network call.
const env = (kv) => ({ LICENSES: kv, STRIPE_WEBHOOK_SECRET: SECRET });

test('derived keys are stable, distinct per session and pass the CLI format', async () => {
  const a = await deriveLicenseKey('cs_live_a', SECRET);
  assert.equal(a, await deriveLicenseKey('cs_live_a', SECRET));
  assert.notEqual(a, await deriveLicenseKey('cs_live_b', SECRET));
  assert.notEqual(a, await deriveLicenseKey('cs_live_a', 'another_secret'));
  assert.match(a, /^PYOB-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$/);
});

test('a paid checkout issues exactly one licence for the buyer', async () => {
  const kv = fakeKv();
  const res = await worker.fetch(
    stripeRequest(sessionEvent('checkout.session.completed', 'paid')),
    env(kv)
  );
  assert.equal(res.status, 200);
  assert.equal(kv.store.size, 1);

  const [key, raw] = [...kv.store.entries()][0];
  const record = JSON.parse(raw);
  assert.equal(key, await deriveLicenseKey('cs_live_example', SECRET));
  assert.equal(record.license_key, key);
  assert.equal(record.email, 'buyer@example.com');
  assert.equal(record.stripe_session_id, 'cs_live_example');
  assert.deepEqual(record.devices, []);
});

test('an unpaid checkout (delayed payment method) issues nothing yet', async () => {
  const kv = fakeKv();
  const res = await worker.fetch(
    stripeRequest(sessionEvent('checkout.session.completed', 'unpaid')),
    env(kv)
  );
  assert.equal(res.status, 200);
  assert.equal((await res.json()).issued, false);
  assert.equal(kv.store.size, 0);
});

test('the later async success issues the licence', async () => {
  const kv = fakeKv();
  await worker.fetch(stripeRequest(sessionEvent('checkout.session.completed', 'unpaid')), env(kv));
  const res = await worker.fetch(
    stripeRequest(sessionEvent('checkout.session.async_payment_succeeded', 'paid')),
    env(kv)
  );
  assert.equal(res.status, 200);
  assert.equal(kv.store.size, 1);
});

test('async failure and unrelated events issue nothing', async () => {
  const kv = fakeKv();
  for (const type of ['checkout.session.async_payment_failed', 'checkout.session.expired']) {
    const res = await worker.fetch(stripeRequest(sessionEvent(type, 'unpaid')), env(kv));
    assert.equal(res.status, 200);
  }
  assert.equal(kv.store.size, 0);
});

test('a redelivered event keeps the original record untouched', async () => {
  const kv = fakeKv();
  const event = sessionEvent('checkout.session.completed', 'paid');
  await worker.fetch(stripeRequest(event), env(kv));
  const [key, first] = [...kv.store.entries()][0];

  const res = await worker.fetch(stripeRequest(event), env(kv));
  assert.equal(res.status, 200);
  assert.equal((await res.json()).duplicate, true);
  assert.equal(kv.store.size, 1);
  assert.equal(kv.store.get(key), first);
});

test('a key collision never overwrites another customer', async () => {
  const key = await deriveLicenseKey('cs_live_example', SECRET);
  const other = { license_key: key, stripe_session_id: 'cs_live_someone_else', devices: ['x'] };
  const kv = fakeKv({ [key]: other });
  const res = await worker.fetch(
    stripeRequest(sessionEvent('checkout.session.completed', 'paid')),
    env(kv)
  );
  assert.equal(res.status, 500);
  assert.deepEqual(JSON.parse(kv.store.get(key)), other);
});

test('a forged event without a valid signature is rejected', async () => {
  const kv = fakeKv();
  const res = await worker.fetch(
    stripeRequest(sessionEvent('checkout.session.completed', 'paid'), 'wrong_secret'),
    env(kv)
  );
  assert.equal(res.status, 400);
  assert.equal(kv.store.size, 0);
});

test('the licence email matches current licence behaviour', () => {
  const body = buildLicenseEmailBody('PYOB-AAAA-BBBB-CCCC-DDDD');
  assert.match(body, /pyobfus-license register PYOB-AAAA-BBBB-CCCC-DDDD/);
  assert.match(body, /pyobfus-license deactivate/);
  assert.match(body, /LICENSE_ACTIVATION_GUIDE\.md/);
  assert.doesNotMatch(body, /cannot be recovered/);
});
