import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';

test('deployment declares both CI rate limiting bindings', () => {
  const text = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
  const bindings = text.split(/^\[\[ratelimits\]\]\s*$/m).slice(1).map(block => {
    const fields = Object.fromEntries([...block.matchAll(/^(name|namespace_id|limit|period)\s*=\s*"?([^"\s]+)"?\s*$/gm)].map(m => [m[1], m[2]]));
    assert.match(block, /^\[ratelimits.simple\]$/m);
    return fields;
  });
  assert.deepEqual(bindings, [
    { name: 'CI_RATE_LIMITER', namespace_id: '2101', limit: '30', period: '60' },
    { name: 'CI_IP_RATE_LIMITER', namespace_id: '2102', limit: '60', period: '60' }
  ]);
});
