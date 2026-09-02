import assert from 'node:assert/strict';
import test from 'node:test';

import { validateWordPressBaseUrl } from '../src/content_webhook.js';

test('accepts and canonicalizes a public HTTPS WordPress origin', () => {
  assert.equal(validateWordPressBaseUrl('https://www.example.com/'), 'https://www.example.com');
});

test('rejects non-HTTPS and credential-bearing WordPress URLs', () => {
  assert.throws(() => validateWordPressBaseUrl('http://www.example.com'), /HTTPS/);
  assert.throws(() => validateWordPressBaseUrl('https://admin:secret@example.com'), /without credentials/);
});

test('rejects paths and private or loopback targets', () => {
  assert.throws(() => validateWordPressBaseUrl('https://example.com/wordpress'), /without credentials/);
  assert.throws(() => validateWordPressBaseUrl('https://127.0.0.1'), /public hostname/);
  assert.throws(() => validateWordPressBaseUrl('https://192.168.1.20'), /public hostname/);
  assert.throws(() => validateWordPressBaseUrl('https://[::1]'), /public hostname/);
});
