const DAY_MS = 24 * 60 * 60 * 1000;
const DEVICE_RETENTION_MS = 90 * DAY_MS;
const TRIAL_RETENTION_MS = 180 * DAY_MS;

// Missing/non-string/unparseable timestamps are expired, not an excuse to
// retain identifiers indefinitely. Only parse strings to avoid coercion.
function timestamp(value) {
  return typeof value === 'string' ? Date.parse(value) : NaN;
}

/** Pure: return the original record if unchanged, otherwise a shallow copy.
 * Exactly 90 days is retained; only older audit entries are removed.
 * `now` is epoch milliseconds (or a Date), supplied by the caller for tests.
 */
export function pruneRetainedDeviceRecords(licenseData, now) {
  let result = licenseData;
  for (const field of ['last_released', 'last_evicted', 'devices_reset']) {
    if (!Object.hasOwn(licenseData, field)) continue;
    const at = timestamp(licenseData[field]?.at);
    if (!Number.isFinite(at) || now - at > DEVICE_RETENTION_MS) {
      if (result === licenseData) result = { ...licenseData };
      delete result[field];
    }
  }
  return result;
}

/** Remove obsolete legacy CI telemetry on writes and during the sweep. */
export function retainLicenseData(licenseData, now) {
  const result = pruneRetainedDeviceRecords(licenseData, now);
  const usage = result.ci_usage;
  if (!Object.hasOwn(result, 'ci_usage')) return result;
  if (!usage || !Object.hasOwn(usage, 'last_used')) {
    const withoutUsage = { ...result };
    delete withoutUsage.ci_usage;
    return withoutUsage;
  }
  if (Object.keys(usage).length !== 1) {
    return { ...result, ci_usage: { last_used: usage.last_used } };
  }
  return result;
}

/** All request-side licence writes share the same retention boundary. */
export async function writeLicenseRecord(env, key, licenseData, now = Date.now()) {
  await env.LICENSES.put(key, JSON.stringify(retainLicenseData(licenseData, now)));
}

/** Keep dedup forever, but no email/device/token after expires + 180 days.
 * Invalid/missing expiry is treated as expired. Existing tombstones are also
 * whitelisted so accidental extra personal fields cannot persist.
 */
export function retainTrialData(record, now) {
  const expires = timestamp(record.expires);
  if (!record.tombstone && Number.isFinite(expires) && now - expires <= TRIAL_RETENTION_MS) {
    return record;
  }
  if (record.tombstone === true &&
      Object.keys(record).every(key => ['expires', 'started', 'tombstone'].includes(key))) {
    return record;
  }
  return { expires: record.expires, started: record.started, tombstone: true };
}

/** Sequential, paginated sweep; unrelated KV namespaces are never read.
 * KV offers no compare-and-set, as with the existing device/telemetry writes.
 */
export async function sweepRetainedData(env, now = Date.now()) {
  // Licence keys are bare PYOB-..., not license:... .
  for (const [prefix, retain] of [['PYOB-', retainLicenseData], ['trial:', retainTrialData]]) {
    let cursor;
    do {
      const page = await env.LICENSES.list({ prefix, ...(cursor ? { cursor } : {}) });
      for (const { name } of page.keys) {
        const record = await env.LICENSES.get(name, { type: 'json' });
        if (!record) continue; // key may have disappeared since list()
        const retained = retain(record, now);
        if (retained !== record) {
          await env.LICENSES.put(name, JSON.stringify(retained));
        }
      }
      if (page.list_complete) break;
      cursor = page.cursor;
    } while (cursor);
  }
}
