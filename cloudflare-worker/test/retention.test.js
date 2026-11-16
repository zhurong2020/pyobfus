import assert from 'node:assert/strict';
import { createHash, createHmac, webcrypto } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import worker from '../src/worker.js';
import { deriveLicenseKey } from '../src/index.js';
import {
  pruneRetainedDeviceRecords, retainLicenseData, retainTrialData,
  sweepRetainedData, writeLicenseRecord,
} from '../src/retention.js';

if (!globalThis.crypto) globalThis.crypto = webcrypto;
const DAY = 24 * 3600 * 1000;
const NOW = Date.parse('2026-11-16T12:00:00Z');
const iso = ms => new Date(ms).toISOString();
const KEY = 'PYOB-AAAA-BBBB-CCCC-DDDD';
const AUDIT_FIELDS = ['last_released', 'last_evicted', 'devices_reset'];
const staleAudit = Object.fromEntries(AUDIT_FIELDS.map(field => [field, {
  at: '2000-01-01T00:00:00Z', device: 'old-private-device',
}]));
const active = { status: 'active', devices: ['desktop'], expires_at: null };
const fullTrial = {
  email: 'synthetic@example.com', email_hash: 'synthetic-hash', first_device: 'private-device',
  started: iso(NOW - 200 * DAY), expires: iso(NOW - 180 * DAY), token: 'private-token', v: 1,
};
const tombstone = record => ({ expires: record.expires, started: record.started, tombstone: true });

function fakeKv(seed = {}, pageSize = 2) {
  const store = new Map(Object.entries(seed).map(([key, record]) => [key, JSON.stringify(record)]));
  const writes = [], lists = [], reads = [];
  return {
    store, writes, lists, reads,
    read(key) { return JSON.parse(store.get(key)); },
    async get(key, options) {
      reads.push(key);
      assert.equal(options.type, 'json');
      return store.has(key) ? JSON.parse(store.get(key)) : null;
    },
    async put(key, value, options) {
      assert.equal(options, undefined, 'no TTL may erase licence records or trial dedup');
      writes.push(key);
      store.set(key, value);
    },
    async list(options) {
      lists.push(options);
      const keys = [...store.keys()].filter(key => key.startsWith(options.prefix)).sort();
      const offset = Number(options.cursor || 0);
      const end = offset + pageSize;
      return {
        keys: keys.slice(offset, end).map(name => ({ name })),
        list_complete: end >= keys.length,
        cursor: end < keys.length ? String(end) : '',
      };
    },
  };
}

function post(path, body, headers = {}) {
  return new Request(`https://example.com${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
}

for (const field of AUDIT_FIELDS) {
  test(`${field}: exactly 90 days and newer retained, older removed without mutation`, () => {
    for (const age of [90 * DAY - 1, 90 * DAY, 90 * DAY + 1, -DAY]) {
      const record = { ...active, [field]: { at: iso(NOW - age), device: 'audit-device' } };
      const before = structuredClone(record);
      const result = pruneRetainedDeviceRecords(record, NOW);
      assert.deepEqual(record, before);
      if (age <= 90 * DAY) assert.equal(result, record);
      else {
        assert.equal(Object.hasOwn(result, field), false);
        assert.deepEqual(result, active);
      }
    }
  });

  test(`${field}: missing/invalid timestamps expire without throwing`, () => {
    for (const value of [null, {}, { at: null }, { at: '' }, { at: 'invalid' },
      { at: 123 }, { at: {} }, { at: [] }]) {
      const record = { ...active, [field]: value };
      assert.deepEqual(pruneRetainedDeviceRecords(record, NOW), active);
      assert.ok(Object.hasOwn(record, field));
    }
    assert.equal(pruneRetainedDeviceRecords(active, NOW), active);
  });
}

test('mixed audit ages are pruned independently; operational and unrelated fields survive', () => {
  const record = { ...active, ...staleAudit, last_verified: 'unchanged', email: 'synthetic@example.com',
    last_evicted: { at: iso(NOW - DAY), devices: ['recent'] } };
  const result = pruneRetainedDeviceRecords(record, new Date(NOW));
  assert.deepEqual(result, { ...active, last_verified: 'unchanged', email: record.email,
    last_evicted: record.last_evicted });
  assert.equal(result.devices, record.devices);
});

test('shared licence writer prunes audit and whitelists CI usage; no TTL', async () => {
  const record = { ...active, ...staleAudit,
    ci_usage: { day: 'old-day', first_seen: 'old-start', last_used: iso(NOW) } };
  const before = structuredClone(record);
  const kv = fakeKv();
  await writeLicenseRecord({ LICENSES: kv }, KEY, record, NOW);
  assert.deepEqual(kv.read(KEY), { ...active, ci_usage: { last_used: iso(NOW) } });
  assert.deepEqual(record, before);
  const retained = kv.read(KEY);
  assert.equal(retainLicenseData(retained, NOW), retained);
});

test('legacy usage without last_used is removed once rather than repeatedly rewritten', async () => {
  for (const usage of [{}, { day: 'old', first_seen: 'old' }, null]) {
    const kv = fakeKv({ [KEY]: { ...active, ci_usage: usage } });
    await sweepRetainedData({ LICENSES: kv }, NOW);
    assert.deepEqual(kv.read(KEY), active);
    await sweepRetainedData({ LICENSES: kv }, NOW);
    assert.deepEqual(kv.writes, [KEY]);
  }
});

for (const [name, path, body, overwritten] of [
  ['verify existing device', '/api/verify', { device_id: 'desktop' }],
  ['activate new device', '/api/verify', { device_id: 'new-device' }],
  ['activate with eviction', '/api/verify', { device_id: 'new-device' }, 'last_evicted'],
  ['legacy CI activate', '/api/verify', { activation: 'ci' }],
  ['deactivate', '/api/deactivate', { device_id: 'desktop' }, 'last_released'],
  ['admin reset', '/api/admin/reset-devices', { devices: [], reason: 'synthetic reset' }, 'devices_reset'],
]) {
  test(`${name} applies retention at its licence write`, async () => {
    const record = { ...active, ...staleAudit,
      ci_usage: { day: 'old-day', first_seen: 'old-start', last_used: '2000-01-01' } };
    if (overwritten === 'last_evicted') record.devices = ['desktop', 'other', 'third'];
    const kv = fakeKv({ [KEY]: record });
    const response = await worker.fetch(post(path, { license_key: KEY, ...body }, {
      Authorization: 'Bearer synthetic-admin',
    }), { LICENSES: kv, ADMIN_TOKEN: 'synthetic-admin' });
    assert.equal(response.status, 200);
    assert.deepEqual(kv.writes, [KEY]);
    const stored = kv.read(KEY);
    for (const field of AUDIT_FIELDS) {
      if (field === overwritten) assert.ok(Date.parse(stored[field].at) > NOW - 90 * DAY);
      else assert.equal(Object.hasOwn(stored, field), false);
    }
    assert.deepEqual(Object.keys(stored.ci_usage), ['last_used']);
    assert.equal(stored.status, record.status);
    assert.equal(stored.expires_at, record.expires_at);
    if (body.activation === 'ci') assert.deepEqual(stored.devices, record.devices);
  });
}

for (const type of ['checkout.session.completed', 'checkout.session.async_payment_succeeded']) {
  test(`paid purchase ${type} uses the shared licence writer`, async t => {
    t.mock.method(console, 'error', () => {});
    t.mock.method(console, 'log', () => {});
    const secret = 'synthetic-webhook-secret';
    const session = { id: 'synthetic-retention-session', payment_status: 'paid',
      customer_details: { email: 'synthetic@example.com' } };
    const body = JSON.stringify({ type, data: { object: session } });
    const time = Math.floor(Date.now() / 1000);
    const signature = createHmac('sha256', secret).update(`${time}.${body}`).digest('hex');
    const kv = fakeKv();
    const response = await worker.fetch(new Request('https://example.com/api/webhook/stripe', {
      method: 'POST', headers: { 'stripe-signature': `t=${time},v1=${signature}` }, body,
    }), { LICENSES: kv, STRIPE_WEBHOOK_SECRET: secret });
    assert.equal(response.status, 200);
    const key = await deriveLicenseKey(session.id, secret);
    assert.deepEqual(kv.writes, [key]);
    assert.deepEqual(kv.read(key).devices, []);
    assert.equal(kv.read(key).status, 'active');
  });
}

test('trial retention: before and exactly 180 days kept; older becomes pure dedup', () => {
  assert.equal(retainTrialData(fullTrial, NOW - 1), fullTrial);
  assert.equal(retainTrialData(fullTrial, NOW), fullTrial);
  const retained = retainTrialData(fullTrial, NOW + 1);
  assert.deepEqual(retained, tombstone(fullTrial));
  assert.equal(fullTrial.email, 'synthetic@example.com');
  assert.equal(retainTrialData(retained, NOW + DAY), retained);
  const reordered = { tombstone: true, started: retained.started, expires: retained.expires };
  assert.equal(retainTrialData(reordered, NOW + DAY), reordered);
});

test('invalid/missing trial expiry is expired; tombstones discard unexpected personal fields', () => {
  for (const expires of [undefined, null, 'invalid', {}, 123]) {
    const record = { ...fullTrial, expires };
    assert.deepEqual(retainTrialData(record, NOW), tombstone(record));
  }
  const dirty = { ...fullTrial, tombstone: true, expires: iso(NOW + DAY) };
  assert.deepEqual(retainTrialData(dirty, NOW), tombstone(dirty));
});

test('sweep paginates both prefixes, skips unchanged/missing records and unrelated data', async () => {
  const fresh = { ...active, last_released: { at: iso(NOW - 90 * DAY), device: 'recent' } };
  const oldTrial = { ...fullTrial, expires: iso(NOW - 180 * DAY - 1) };
  const kv = fakeKv({
    'PYOB-A': { ...active, ...staleAudit }, 'PYOB-B': fresh,
    'PYOB-C': { ...active, ci_usage: { last_used: iso(NOW), first_seen: 'old', day: 'old' } },
    'PYOB-D': active,
    'trial:a': oldTrial, 'trial:b': fullTrial, 'trial:c': tombstone(oldTrial),
    'trial:d': { ...tombstone(oldTrial), email: 'synthetic@example.com' },
    'content:order:synthetic': { email: 'synthetic@example.com' },
  });
  const originalGet = kv.get;
  kv.get = async (key, options) => key === 'PYOB-D' ? null : originalGet(key, options);
  await sweepRetainedData({ LICENSES: kv }, NOW);
  assert.deepEqual(kv.writes, ['PYOB-A', 'PYOB-C', 'trial:a', 'trial:d']);
  assert.deepEqual(kv.lists, [
    { prefix: 'PYOB-' }, { prefix: 'PYOB-', cursor: '2' },
    { prefix: 'trial:' }, { prefix: 'trial:', cursor: '2' },
  ]);
  assert.deepEqual(kv.read('PYOB-B'), fresh);
  assert.deepEqual(kv.read('trial:a'), tombstone(oldTrial));
  assert.deepEqual(kv.read('trial:d'), tombstone(oldTrial));
  assert.deepEqual(kv.read('PYOB-C').ci_usage, { last_used: iso(NOW) });
  assert.ok(!kv.reads.some(key => key.startsWith('content:')));
  kv.writes.length = 0;
  await sweepRetainedData({ LICENSES: kv }, NOW);
  assert.deepEqual(kv.writes, [], 'a second sweep is idempotent');
});

test('module entrypoint exposes and awaits scheduled sweep; cron is weekly UTC', async () => {
  const config = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
  assert.match(config, /\[triggers\]\s+crons = \["17 3 \* \* 1"\]/);
  const kv = fakeKv({ [KEY]: { ...active, ...staleAudit } });
  await worker.scheduled({}, { LICENSES: kv }, {});
  assert.deepEqual(kv.read(KEY), active);
  assert.deepEqual(kv.writes, [KEY]);
  await assert.rejects(worker.scheduled({}, {
    LICENSES: { async list() { throw new Error('synthetic storage failure'); } },
  }, {}), /synthetic storage failure/);
});

for (const retained of [false, true]) {
  test(`lazy trial read ${retained ? 'keeps recent full record' : 'tombstones expired data and refuses reuse'}`, async () => {
    const email = 'synthetic@example.com';
    const key = `trial:${createHash('sha256').update(email).digest('hex')}`;
    const record = { ...fullTrial, expires: iso(Date.now() - (retained ? 179 : 181) * DAY) };
    const kv = fakeKv({ [key]: record });
    const env = { LICENSES: kv, TRIAL_SIGNING_SECRET: 'synthetic-trial-secret' };
    for (let i = 0; i < 2; i++) {
      const response = await worker.fetch(post('/api/trial/request', {
        email: i ? email.toUpperCase() : email, device_id: `different-device-${i}`,
      }), env);
      assert.equal(response.status, 200);
      const data = await response.json();
      assert.equal(data.status, 'already_issued');
      assert.equal(data.email_known, true);
      assert.equal(data.active, false);
      assert.equal(data.expires, record.expires);
      assert.equal(data.started, record.started);
      if (retained) assert.equal(data.token, record.token);
      else assert.equal(Object.hasOwn(data, 'token'), false);
    }
    assert.equal(kv.store.size, 1);
    assert.deepEqual(kv.writes, retained ? [] : [key]);
    assert.deepEqual(kv.read(key), retained ? record : tombstone(record));
    if (!retained) {
      for (const privateValue of [email, record.first_device, record.token]) {
        assert.ok(!kv.store.get(key).includes(privateValue));
      }
    }
  });
}
