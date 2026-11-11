// Actual workerd signer -> Python verifier canary. All keys are ephemeral.
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(path.join(path.resolve(process.argv[2]), 'canary.cjs'));
const { Miniflare } = require('miniflare');
let raw = '';
for await (const chunk of process.stdin) raw += chunk;
const input = JSON.parse(raw);
const pair = await webcrypto.subtle.generateKey('Ed25519', true, ['sign', 'verify']);
const secret = await webcrypto.subtle.exportKey('jwk', pair.privateKey);
const pub = await webcrypto.subtle.exportKey('jwk', pair.publicKey);
const mf = new Miniflare({
  cf: false,
  modules: true,
  modulesRules: [{ type: 'ESModule', include: ['**/*.js'] }],
  scriptPath: path.resolve('cloudflare-worker/src/worker.js'),
  compatibilityDate: '2025-11-12',
  kvNamespaces: ['LICENSES'],
  bindings: { CI_SIGNING_KEY_ID: 'workerd-canary', CI_SIGNING_PRIVATE_JWK: JSON.stringify(secret) },
});
try {
  const kv = await mf.getKVNamespace('LICENSES');
  const record = JSON.stringify({ status: 'active', expires_at: null, devices: ['untouched'] });
  await kv.put(input.license_key, record);
  const res = await mf.dispatchFetch('https://example.com/api/ci/lease', {
    method: 'POST', body: JSON.stringify(input),
  });
  assert.equal(res.status, 200);
  assert.equal(await kv.get(input.license_key), record);
  const response = await res.json();
  // The same runtime entrypoint must continue serving old CI and registered
  // workstation clients. Their historical side effects are separate from v1.
  const legacyCi = await mf.dispatchFetch('https://example.com/api/verify', {
    method: 'POST', body: JSON.stringify({ license_key: input.license_key, activation: 'ci' }),
  });
  assert.equal(legacyCi.status, 200);
  assert.equal((await legacyCi.json()).valid, true);
  const workstation = await mf.dispatchFetch('https://example.com/api/verify', {
    method: 'POST', body: JSON.stringify({ license_key: input.license_key, device_id: 'legacy-client' }),
  });
  assert.equal(workstation.status, 200);
  assert.equal((await workstation.json()).valid, true);
  const saved = JSON.parse(record);
  await kv.put(input.license_key, JSON.stringify({ ...saved, status: 'revoked' }));
  const rejected = await mf.dispatchFetch('https://example.com/api/ci/lease', {
    method: 'POST', body: JSON.stringify(input),
  });
  assert.equal(rejected.status, 403);
  process.stdout.write(JSON.stringify({ response, public_key: pub.x }));
} finally {
  await mf.dispose();
}
