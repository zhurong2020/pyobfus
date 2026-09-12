# pyobfus License Server - Cloudflare Worker

Serverless license verification and Stripe webhook handling for pyobfus Pro.

The draft content-membership webhook requires `WP_BASE_URL` to be a public
HTTPS origin only (for example, `https://www.example.com`): credentials,
paths, query strings, fragments, localhost, and private/link-local addresses
are rejected before WordPress administrator credentials are constructed or
sent.

## 🎉 Production Status

**Status**: ✅ **LIVE PRODUCTION** (Deployed 2025-11-12)

- **Worker URL**: https://pyobfus-license-server.zhurong0525.workers.dev
- **Environment**: Live (production Stripe keys configured)
- **KV Namespace**: `61072fc72c35405c850427da381ccdbf`
- **Webhook**: Configured in Stripe (Live mode)
- **Tests**: All integration tests passing ✅

### Quick Links
- **Stripe Dashboard**: https://dashboard.stripe.com/payments
- **Webhook Events**: https://dashboard.stripe.com/webhooks
- **Monitor Logs**: `wrangler tail`

---

## 🚀 Quick Start

### Prerequisites
- Node.js and npm installed
- Cloudflare account with Workers enabled

### Installation

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

## 📦 Deployment

### Deploy Worker

```bash
cd cloudflare-worker
wrangler deploy
```

### View Logs

```bash
wrangler tail
```

## 🗄️ KV Management

### Add a License

```bash
# Add test license
wrangler kv key put --remote \
  --namespace-id=61072fc72c35405c850427da381ccdbf \
  "PYOBFUS-TEST-1234-5678-ABCD" \
  '{"license_key":"PYOBFUS-TEST-1234-5678-ABCD","email":"test@example.com","status":"active","created_at":"2025-11-12T00:00:00Z","stripe_session_id":"test_session","stripe_customer_id":"test_customer","devices":[],"expires_at":null}'
```

### Get a License

```bash
wrangler kv key get --remote \
  --namespace-id=61072fc72c35405c850427da381ccdbf \
  "PYOBFUS-TEST-1234-5678-ABCD"
```

### List All Licenses

```bash
wrangler kv key list --remote \
  --namespace-id=61072fc72c35405c850427da381ccdbf
```

### Delete a License

```bash
wrangler kv key delete --remote \
  --namespace-id=61072fc72c35405c850427da381ccdbf \
  "PYOBFUS-TEST-1234-5678-ABCD"
```

## 🧪 Testing

### Run Integration Tests

```bash
# From project root
python scripts/test_license_server.py
```

### Test Endpoints Manually

```bash
# Health check
curl https://pyobfus-license-server.zhurong0525.workers.dev/api/health

# Verify license
curl -X POST https://pyobfus-license-server.zhurong0525.workers.dev/api/verify \
  -H "Content-Type: application/json" \
  -d '{"license_key":"PYOBFUS-TEST-1234-5678-ABCD","device_id":"test-device-123"}'
```

## 📋 API Endpoints

### GET /api/health
Health check endpoint.

**Response**:
```json
{
  "status": "ok",
  "service": "pyobfus-license-server",
  "version": "1.0.0",
  "timestamp": "2025-11-12T00:00:00Z"
}
```

### POST /api/verify
Verify a license key and register device.

**Request**:
```json
{
  "license_key": "PYOBFUS-XXXX-XXXX-XXXX-XXXX",
  "device_id": "unique-device-id"
}
```

**Response (Success)**:
```json
{
  "valid": true,
  "license_key": "PYOBFUS-XXXX-XXXX-XXXX-XXXX",
  "email": "customer@example.com",
  "created_at": "2025-11-12T00:00:00Z",
  "expires_at": null,
  "features": {
    "string_encryption": true,
    "anti_debug": true,
    "control_flow": false
  }
}
```

**Response (Invalid)**:
```json
{
  "valid": false,
  "error": "Invalid license key"
}
```

### POST /api/webhook/stripe
Stripe webhook handler (creates licenses on payment).

**Headers**:
- `stripe-signature`: Stripe webhook signature

## 🔧 Configuration

### wrangler.toml

```toml
name = "pyobfus-license-server"
main = "src/index.js"
compatibility_date = "2025-11-12"

[[kv_namespaces]]
binding = "LICENSES"
id = "61072fc72c35405c850427da381ccdbf"
```

### Environment Variables (Configured)

Production secrets (already configured):

```bash
# Stripe Secret Key (configured 2025-11-12)
echo "sk_live_..." | wrangler secret put STRIPE_SECRET_KEY

# Stripe Webhook Secret (configured 2025-11-12)
echo "whsec_..." | wrangler secret put STRIPE_WEBHOOK_SECRET
```

To update secrets, use the same commands above with new values.

## 📊 Monitoring

### View Real-time Logs

```bash
wrangler tail --format pretty
```

### View Metrics

Visit: https://dash.cloudflare.com/workers/pyobfus-license-server

## 🔗 URLs

- **Production**: https://pyobfus-license-server.zhurong0525.workers.dev
- **Dashboard**: https://dash.cloudflare.com/
- **KV Namespace ID**: `61072fc72c35405c850427da381ccdbf`

## 🚀 Deployment History

1. ✅ Worker deployed and tested (2025-11-12)
2. ✅ Stripe webhook configured in live mode (2025-11-12)
3. ✅ Production secrets configured (2025-11-12)
4. ✅ End-to-end payment flow tested (2025-11-12)
5. ✅ **Production deployment complete** (2025-11-12)

### Optional Next Steps
- [ ] Update Python client to use Worker URL
- [ ] Add email delivery for license keys
- [ ] Create checkout session script

## 📝 License Data Schema

```json
{
  "license_key": "PYOBFUS-XXXX-XXXX-XXXX-XXXX",
  "email": "customer@example.com",
  "status": "active",
  "created_at": "2025-11-12T00:00:00Z",
  "stripe_session_id": "cs_xxx",
  "stripe_customer_id": "cus_xxx",
  "devices": [
    {"id": "device-id-1", "last_seen": "2026-09-13T00:00:00.000Z"},
    {"id": "device-id-2", "last_seen": null}
  ],
  "expires_at": null
}
```

Records written before `last_seen` existed hold bare id strings. Those are
still read; they are normalised on the next write and, having no date, are the
first to be retired.

**Status Values**:
- `active`: License is valid
- `suspended`: License temporarily disabled
- `revoked`: License permanently disabled
- `expired`: License past expiration date

Every error response carries a stable `code` (`invalid_key`, `revoked`,
`inactive`, `expired`, `bad_request`, `unauthorized`) alongside its prose
`error`. Clients branch on the code: only `revoked` and `expired` are
definitive enough to override a client's offline cache.

**Device limit**: 3 per licence, and reaching it is not an error. A fourth
device retires the least recently used one. Refusing instead made lockout
inevitable, because nothing ever removed a device: reinstalls, replacement
machines and drifting fingerprints each permanently consumed a slot the
customer could not reclaim.

## Releasing devices

`POST /api/deactivate` with `{license_key, device_id}` removes one device.
This is what `pyobfus-license deactivate` calls, so retiring a machine is a
customer operation rather than a support ticket.

`POST /api/admin/reset-devices` sets the list outright, for when the customer
cannot reach the machine. It requires `Authorization: Bearer $ADMIN_TOKEN`,
compared in constant time, and checks that **before** touching storage so an
unauthenticated caller cannot learn whether a licence exists. The reset is
recorded on the licence in `devices_reset` with the previous list, an optional
reason, and a timestamp.

```bash
wrangler secret put ADMIN_TOKEN        # a long random string, not a Cloudflare API token

curl -X POST https://<worker>/api/admin/reset-devices \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"license_key":"PYOB-...","reason":"customer request"}'
```

With no `ADMIN_TOKEN` configured the endpoint answers 401 to everything, which
is the correct resting state. Use a dedicated secret: a Cloudflare API token
can also read every customer record and deploy code, and an application
endpoint has no business holding infrastructure credentials.

**Before editing licence data by any other means, export it.** KV is the only
copy, and a bad write cannot be undone.
