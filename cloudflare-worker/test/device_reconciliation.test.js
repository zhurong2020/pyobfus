import assert from 'node:assert/strict';
import test from 'node:test';

import { MAX_DEVICES, reconcileDevices } from '../src/index.js';

const T1 = '2026-01-01T00:00:00.000Z';
const T2 = '2026-02-01T00:00:00.000Z';
const T3 = '2026-03-01T00:00:00.000Z';
const NOW = '2026-09-13T00:00:00.000Z';

test('a returning device is touched, not duplicated', () => {
  const existing = [{ id: 'a', last_seen: T1 }, { id: 'b', last_seen: T2 }];
  const { devices, evicted } = reconcileDevices(existing, 'a', NOW);
  assert.deepEqual(evicted, []);
  assert.equal(devices.length, 2);
  assert.equal(devices.find((d) => d.id === 'a').last_seen, NOW);
  assert.equal(devices.find((d) => d.id === 'b').last_seen, T2);
});

test('a new device is added while there is room', () => {
  const { devices, evicted } = reconcileDevices([{ id: 'a', last_seen: T1 }], 'b', NOW);
  assert.deepEqual(evicted, []);
  assert.deepEqual(devices.map((d) => d.id), ['a', 'b']);
});

test('the fourth device retires the least recently used one, never refuses', () => {
  const existing = [
    { id: 'oldest', last_seen: T1 },
    { id: 'middle', last_seen: T2 },
    { id: 'newest', last_seen: T3 },
  ];
  const { devices, evicted } = reconcileDevices(existing, 'fourth', NOW);
  assert.deepEqual(evicted, ['oldest']);
  assert.deepEqual(devices.map((d) => d.id), ['middle', 'newest', 'fourth']);
  assert.equal(devices.length, MAX_DEVICES);
});

test('legacy bare-string records are accepted and retired first', () => {
  // Records written before last_seen existed. They cannot be dated, so they
  // must not outrank a device we have actually seen recently.
  const existing = ['legacy-one', { id: 'dated', last_seen: T3 }, 'legacy-two'];
  const { devices, evicted } = reconcileDevices(existing, 'fresh', NOW);
  assert.equal(evicted.length, 1);
  assert.ok(evicted[0].startsWith('legacy-'));
  assert.ok(devices.some((d) => d.id === 'dated'));
  assert.ok(devices.some((d) => d.id === 'fresh'));
  assert.ok(devices.every((d) => typeof d.id === 'string'));
});

test('the device being answered is never the one evicted', () => {
  // Even when it is somehow the oldest entry, answering a request must not
  // deregister the machine that just made it.
  const existing = [
    { id: 'x', last_seen: T2 },
    { id: 'y', last_seen: T3 },
    { id: 'z', last_seen: T3 },
  ];
  const { devices, evicted } = reconcileDevices(existing, 'x', NOW, 1);
  assert.deepEqual(evicted, []);
  assert.equal(devices.find((d) => d.id === 'x').last_seen, NOW);
});

test('missing, malformed and duplicate entries do not corrupt the list', () => {
  const { devices } = reconcileDevices(undefined, 'a', NOW);
  assert.deepEqual(devices, [{ id: 'a', last_seen: NOW }]);

  const messy = reconcileDevices(['dup', 'dup', '', null, { id: 'dup' }, { nope: 1 }], 'a', NOW);
  assert.deepEqual(messy.devices.map((d) => d.id), ['dup', 'a']);
});
