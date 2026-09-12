import assert from 'node:assert/strict';
import test from 'node:test';

import worker, { constantTimeEqual } from '../src/index.js';

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
    read(key) {
      return JSON.parse(store.get(key));
    },
  };
}

function post(path, body, headers = {}) {
  return new Request(`https://example.workers.dev${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
}

const LICENCE = {
  license_key: 'PYOB-1111-2222-3333-4444',
  email: 'someone@example.com',
  status: 'active',
  devices: [{ id: 'mac', last_seen: '2026-01-01T00:00:00.000Z' }, 'legacy-laptop'],
  expires_at: null,
};

test('constantTimeEqual accepts only an exact match', () => {
  assert.equal(constantTimeEqual('abc', 'abc'), true);
  assert.equal(constantTimeEqual('abc', 'abd'), false);
  assert.equal(constantTimeEqual('abc', 'abcd'), false);
  assert.equal(constantTimeEqual('abc', undefined), false);
  assert.equal(constantTimeEqual(null, null), false);
});

test('deactivate releases the calling device and leaves the rest', async () => {
  const kv = fakeKv({ 'PYOB-1111-2222-3333-4444': LICENCE });
  const res = await worker.fetch(
    post('/api/deactivate', { license_key: 'PYOB-1111-2222-3333-4444', device_id: 'mac' }),
    { LICENSES: kv }
  );
  assert.equal(res.status, 200);
  const payload = await res.json();
  assert.equal(payload.released, true);
  assert.equal(payload.devices_registered, 1);

  const stored = kv.read('PYOB-1111-2222-3333-4444');
  assert.deepEqual(stored.devices.map((d) => d.id), ['legacy-laptop']);
  assert.equal(stored.last_released.device, 'mac');
});

test('deactivating an unknown device is reported honestly, not as success', async () => {
  const kv = fakeKv({ 'PYOB-1111-2222-3333-4444': LICENCE });
  const res = await worker.fetch(
    post('/api/deactivate', { license_key: 'PYOB-1111-2222-3333-4444', device_id: 'never-seen' }),
    { LICENSES: kv }
  );
  const payload = await res.json();
  assert.equal(payload.released, false);
  assert.equal(payload.devices_registered, 2);
});

test('deactivate rejects a missing field and an unknown key', async () => {
  const kv = fakeKv({ 'PYOB-1111-2222-3333-4444': LICENCE });
  const bad = await worker.fetch(post('/api/deactivate', { license_key: 'x' }), { LICENSES: kv });
  assert.equal(bad.status, 400);
  assert.equal((await bad.json()).code, 'bad_request');

  const missing = await worker.fetch(
    post('/api/deactivate', { license_key: 'PYOB-0000-0000-0000-0000', device_id: 'a' }),
    { LICENSES: kv }
  );
  assert.equal(missing.status, 404);
  assert.equal((await missing.json()).code, 'invalid_key');
});

test('admin reset refuses every request when no token is configured', async () => {
  const kv = fakeKv({ 'PYOB-1111-2222-3333-4444': LICENCE });
  const res = await worker.fetch(
    post('/api/admin/reset-devices', { license_key: 'PYOB-1111-2222-3333-4444' }),
    { LICENSES: kv } // no ADMIN_TOKEN
  );
  assert.equal(res.status, 401);
  assert.deepEqual(kv.read('PYOB-1111-2222-3333-4444').devices, LICENCE.devices);
});

test('admin reset does not reveal whether a licence exists to an unauthorised caller', async () => {
  const kv = fakeKv({ 'PYOB-1111-2222-3333-4444': LICENCE });
  const env = { LICENSES: kv, ADMIN_TOKEN: 'correct-horse' };
  const real = await worker.fetch(
    post('/api/admin/reset-devices', { license_key: 'PYOB-1111-2222-3333-4444' },
      { Authorization: 'Bearer wrong-token-xx' }),
    env
  );
  const fake = await worker.fetch(
    post('/api/admin/reset-devices', { license_key: 'PYOB-9999-9999-9999-9999' },
      { Authorization: 'Bearer wrong-token-xx' }),
    env
  );
  assert.equal(real.status, 401);
  assert.equal(fake.status, 401);
  assert.deepEqual(await real.json(), await fake.json());
});

test('admin reset clears the list and records what it replaced', async () => {
  const kv = fakeKv({ 'PYOB-1111-2222-3333-4444': LICENCE });
  const res = await worker.fetch(
    post('/api/admin/reset-devices',
      { license_key: 'PYOB-1111-2222-3333-4444', reason: 'customer asked, slots stuck' },
      { Authorization: 'Bearer correct-horse' }),
    { LICENSES: kv, ADMIN_TOKEN: 'correct-horse' }
  );
  assert.equal(res.status, 200);
  const payload = await res.json();
  assert.deepEqual(payload.devices, []);
  assert.deepEqual(payload.previous, ['mac', 'legacy-laptop']);

  const stored = kv.read('PYOB-1111-2222-3333-4444');
  assert.deepEqual(stored.devices, []);
  assert.equal(stored.devices_reset.reason, 'customer asked, slots stuck');
  assert.deepEqual(stored.devices_reset.previous, ['mac', 'legacy-laptop']);
  // The rest of the record must be untouched.
  assert.equal(stored.email, LICENCE.email);
  assert.equal(stored.status, 'active');
});

test('admin reset can seed a specific device list', async () => {
  const kv = fakeKv({ 'PYOB-1111-2222-3333-4444': LICENCE });
  const res = await worker.fetch(
    post('/api/admin/reset-devices',
      { license_key: 'PYOB-1111-2222-3333-4444', devices: ['only-this-mac'] },
      { Authorization: 'Bearer correct-horse' }),
    { LICENSES: kv, ADMIN_TOKEN: 'correct-horse' }
  );
  assert.deepEqual((await res.json()).devices, ['only-this-mac']);
  assert.deepEqual(kv.read('PYOB-1111-2222-3333-4444').devices, [
    { id: 'only-this-mac', last_seen: null },
  ]);
});
