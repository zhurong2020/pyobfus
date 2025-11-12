# pyobfus License Server - Cloudflare Worker

Serverless license verification and Stripe webhook handling for pyobfus Pro.

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
  "devices": ["device-id-1", "device-id-2"],
  "expires_at": null
}
```

**Status Values**:
- `active`: License is valid
- `suspended`: License temporarily disabled
- `revoked`: License permanently disabled
- `expired`: License past expiration date

**Device Limit**: Maximum 3 devices per license
