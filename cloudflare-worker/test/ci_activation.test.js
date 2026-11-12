import assert from 'node:assert/strict';
import test from 'node:test';
import { webcrypto } from 'node:crypto';
import worker from '../src/index.js';
if (!globalThis.crypto) globalThis.crypto = webcrypto;
const key = 'PYOB-AAAA-BBBB-CCCC-DDDD';
async function verify(record, body = { license_key: key, activation: 'ci' }, limiter) {
  let stored = structuredClone(record);
  let writes = 0;
  const res = await worker.fetch(new Request('https://example.com/api/verify', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
  }), { LICENSES: {
    async get() { return structuredClone(stored); },
    async put(k, value) { assert.equal(k, key); stored = JSON.parse(value); writes++; }
  }, CI_RATE_LIMITER: limiter });
  return { res, data: await res.json(), stored, writes };
}
const active = { status: 'active', email: 'synthetic@example.com', expires_at: null,
  devices: ['legacy', { id: 'desktop', last_seen: null }] };
test('CI valid: no devices touched, no email or key, usage in existing record', async () => {
  const { res, data, stored, writes } = await verify(active);
  assert.equal(res.status, 200);
  assert.equal(data.activation, 'ci');
  assert.equal(data.valid, true);
  assert.deepEqual(stored.devices, active.devices);
  assert.equal(writes, 1);
  assert.ok(stored.ci_usage.first_seen);
  assert.ok(stored.ci_usage.last_used);
  assert.equal(data.email, undefined);
  assert.equal(data.license_key, undefined);
  const second = await verify(stored);
  assert.equal(second.writes, 0);
  assert.deepEqual(second.stored.ci_usage, stored.ci_usage);
  stored.ci_usage.day = '2000-01-01';
  assert.equal((await verify(stored)).writes, 1);
  stored.ci_usage.day = new Date().toISOString().slice(0, 10);
  stored.ci_usage.last_used = new Date(Date.now() - 3601 * 1000).toISOString();
  const hourly = await verify(stored);
  assert.equal(hourly.writes, 1);
  assert.equal(hourly.stored.ci_usage.first_seen, stored.ci_usage.first_seen);
});
for (const [name, record, status] of [
  ['revoked', { ...active, status: 'revoked' }, 403],
  ['expired', { ...active, expires_at: '2000-01-01' }, 403],
  ['invalid', null, 404],
]) test(`CI ${name} denied without writes`, async () => {
  const r = await verify(record);
  assert.equal(r.res.status, status);
  assert.equal(r.writes, 0);
});
test('CI missing key', async () => {
  assert.equal((await verify(active, { activation: 'ci' })).res.status, 400);
});
test('CI optional limiter hashes key and denies without writes', async () => {
  const r = await verify(active, undefined, { async limit({ key: hashed }) {
    assert.match(hashed, /^[a-f0-9]{64}$/);
    assert.notEqual(hashed, key);
    return { success: false };
  } });
  assert.equal(r.res.status, 429);
  assert.equal(r.data.code, 'rate_limited');
  assert.equal(r.writes, 0);
});
test('legacy verification keeps response and device registration', async () => {
  const r = await verify(active, { license_key: key, device_id: 'runner' });
  assert.equal(r.res.status, 200);
  assert.equal(r.data.email, active.email);
  assert.equal(r.data.license_key, key);
  assert.equal(r.data.activation, undefined);
  assert.equal(r.stored.ci_usage, undefined);
  assert.ok(r.stored.devices.some(d => d.id === 'runner'));
  assert.equal((await verify(active, { license_key: key })).res.status, 400);
});

for (const size of [1, 32]) test(`CI telemetry put failure: ${size} concurrent verifications stay valid`, async (t) => {
  const warnings = [];
  t.mock.method(console, 'warn', (...args) => warnings.push(args.join(' ')));
  let writes = 0;
  const env = { LICENSES: {
    async get() { return structuredClone(active); },
    async put() { writes++; throw new Error(`private ${key}`); }
  } };
  const results = await Promise.all(Array.from({ length: size }, async () => {
    const res = await worker.fetch(new Request('https://example.com/api/verify', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_key: key, activation: 'ci' })
    }), env);
    assert.equal(res.status, 200);
    assert.equal((await res.json()).valid, true);
  }));
  assert.equal(results.length, size);
  assert.equal(writes, size);
  assert.deepEqual(warnings, Array(size).fill('CI usage telemetry write failed'));
});

for (const ci of [true, false]) test(`legacy endpoint IP limiter only for CI: ${ci}`, async () => {
  let reads = 0, calls = 0;
  const res = await worker.fetch(new Request('https://example.com/api/verify', {
    method: 'POST', body: JSON.stringify({ license_key: key, ...(ci ? { activation: 'ci' } : { device_id: 'runner' }) })
  }), { CI_IP_RATE_LIMITER: { async limit({ key: identifier }) {
    calls++; assert.equal(identifier, 'no-ip'); return { success: false };
  } }, LICENSES: { async get() { reads++; return structuredClone(active); }, async put() {} } });
  assert.equal(res.status, ci ? 429 : 200);
  assert.equal(reads, ci ? 0 : 1);
  assert.equal(calls, ci ? 1 : 0);
});
