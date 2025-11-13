# Email Automation Implementation Plan

**Created**: 2025-11-12
**Status**: Planning Phase
**Priority**: Medium (Operations improvement)

---

## Executive Summary

Implement professional email system using Cloudflare Email Routing to replace personal Gmail addresses, improve brand image, and automate common support tasks.

**Key Benefits**:
- 🎯 Professional brand presence (support@pyobfus.dev vs zhurong0525@gmail.com)
- ⚡ Instant automated responses for common inquiries
- 📊 Better organization and tracking of customer communications
- 🔄 Scalable foundation for team growth
- 💰 Zero cost for basic setup (Cloudflare free tier)

---

## Phase 1: Professional Email Setup

**Timeline**: 1 hour
**Cost**: Free
**Priority**: High

### 1.1 Domain Configuration

**Prerequisites**:
- Domain registered (e.g., pyobfus.dev)
- Domain managed in Cloudflare
- MX records configured for Email Routing

**Email Addresses to Create**:

```yaml
Primary Support:
  support@pyobfus.dev:
    purpose: General customer support
    forward_to: zhurong0525@gmail.com
    auto_reply: true
    priority: high

License Management:
  license@pyobfus.dev:
    purpose: License activation, status, issues
    forward_to: zhurong0525@gmail.com
    auto_reply: true
    priority: high

Sales:
  sales@pyobfus.dev:
    purpose: Pre-purchase questions
    forward_to: zhurong0525@gmail.com
    auto_reply: true
    priority: medium

Refunds:
  refund@pyobfus.dev:
    purpose: Refund requests
    forward_to: zhurong0525@gmail.com
    auto_reply: true
    priority: high
    sla: 2 business days

General:
  hello@pyobfus.dev:
    purpose: General inquiries
    forward_to: zhurong0525@gmail.com
    auto_reply: true
    priority: low

Catch-all:
  *@pyobfus.dev:
    forward_to: zhurong0525@gmail.com
    purpose: Catch unmatched addresses
```

### 1.2 Cloudflare Email Routing Setup

**Steps**:
1. Navigate to Cloudflare Dashboard → Email → Email Routing
2. Enable Email Routing for domain
3. Configure destination address (zhurong0525@gmail.com)
4. Verify destination email
5. Add email addresses as listed above
6. Test each address with sample emails

**Configuration Export** (for reference):
```json
{
  "email_routing": {
    "enabled": true,
    "destination_addresses": ["zhurong0525@gmail.com"],
    "routing_rules": [
      {
        "matcher": { "type": "literal", "value": "support@pyobfus.dev" },
        "action": { "type": "forward", "value": ["zhurong0525@gmail.com"] }
      },
      {
        "matcher": { "type": "literal", "value": "license@pyobfus.dev" },
        "action": { "type": "forward", "value": ["zhurong0525@gmail.com"] }
      },
      {
        "matcher": { "type": "literal", "value": "sales@pyobfus.dev" },
        "action": { "type": "forward", "value": ["zhurong0525@gmail.com"] }
      },
      {
        "matcher": { "type": "literal", "value": "refund@pyobfus.dev" },
        "action": { "type": "forward", "value": ["zhurong0525@gmail.com"] }
      },
      {
        "matcher": { "type": "literal", "value": "hello@pyobfus.dev" },
        "action": { "type": "forward", "value": ["zhurong0525@gmail.com"] }
      },
      {
        "matcher": { "type": "all" },
        "action": { "type": "forward", "value": ["zhurong0525@gmail.com"] }
      }
    ]
  }
}
```

### 1.3 Documentation Updates

**Files to Update**:

1. **README.md**:
   ```markdown
   Before: Contact: zhurong0525@gmail.com
   After:  Support: support@pyobfus.dev
   ```

2. **docs/index.md** (GitHub Pages):
   - Update contact email in purchase section
   - Update support information

3. **docs/legal/TERMS_OF_SERVICE.md**:
   - Update contact information
   - Refund contact: refund@pyobfus.dev

4. **docs/legal/REFUND_POLICY.md**:
   - Update refund request email

5. **docs/legal/PRIVACY_POLICY.md**:
   - Update contact information

6. **pyobfus/cli.py**:
   - Update support email in Pro feature hints
   - Update error messages

7. **docs/LICENSE_ACTIVATION_GUIDE.md**:
   - Update support contact

**Search and Replace**:
```bash
# Find all instances
grep -r "zhurong0525@gmail.com" . --include="*.md" --include="*.py"

# Replace strategy
zhurong0525@gmail.com → support@pyobfus.dev (general)
zhurong0525@gmail.com → license@pyobfus.dev (license issues)
zhurong0525@gmail.com → refund@pyobfus.dev (refund requests)
```

---

## Phase 2: Email Auto-Responder

**Timeline**: 4-6 hours
**Cost**: Free (Workers free tier)
**Priority**: Medium

### 2.1 Cloudflare Worker Setup

**File Structure**:
```
workers/
├── email-handler/
│   ├── src/
│   │   ├── index.ts              # Main entry point
│   │   ├── handlers/
│   │   │   ├── support.ts        # Support email handler
│   │   │   ├── license.ts        # License email handler
│   │   │   ├── sales.ts          # Sales email handler
│   │   │   └── refund.ts         # Refund email handler
│   │   ├── templates/
│   │   │   ├── support.html      # Support auto-reply template
│   │   │   ├── license.html      # License auto-reply template
│   │   │   ├── sales.html        # Sales auto-reply template
│   │   │   └── refund.html       # Refund auto-reply template
│   │   └── utils/
│   │       ├── email.ts          # Email utility functions
│   │       └── logger.ts         # Logging utilities
│   ├── wrangler.toml             # Worker configuration
│   ├── package.json
│   └── tsconfig.json
```

### 2.2 Worker Implementation

**Main Handler** (`src/index.ts`):
```typescript
export default {
  async email(message: EmailMessage, env: Env, ctx: ExecutionContext) {
    const { to, from, subject } = message;

    // Route to appropriate handler
    const handler = getHandler(to);

    try {
      // Send auto-reply
      await handler.autoReply(message, env);

      // Forward to human
      await message.forward(env.FORWARD_EMAIL);

      // Log for analytics
      await logEmail(message, env);
    } catch (error) {
      console.error('Email handling error:', error);
      // Still forward to human on error
      await message.forward(env.FORWARD_EMAIL);
    }
  }
};

function getHandler(emailAddress: string): EmailHandler {
  if (emailAddress.includes('support@')) return supportHandler;
  if (emailAddress.includes('license@')) return licenseHandler;
  if (emailAddress.includes('sales@')) return salesHandler;
  if (emailAddress.includes('refund@')) return refundHandler;
  return defaultHandler;
}
```

**Support Handler** (`src/handlers/support.ts`):
```typescript
export const supportHandler: EmailHandler = {
  async autoReply(message: EmailMessage, env: Env) {
    const replyEmail = new EmailMessage(
      env.SENDER_EMAIL, // support@pyobfus.dev
      message.from,
      'Re: ' + message.subject,
      await renderTemplate('support', {
        userName: extractName(message.from),
        subject: message.subject,
        ticketId: generateTicketId(),
      })
    );

    await replyEmail.send();
  }
};
```

### 2.3 Email Templates

**Support Auto-Reply** (`src/templates/support.html`):
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white; padding: 20px; text-align: center; }
    .content { padding: 20px; }
    .footer { background: #f8f9fa; padding: 15px; font-size: 0.9em; color: #666; }
    .button { background: #667eea; color: white; padding: 12px 24px;
              text-decoration: none; border-radius: 5px; display: inline-block;
              margin: 10px 0; }
  </style>
</head>
<body>
  <div class="header">
    <h1>pyobfus Support</h1>
  </div>
  <div class="content">
    <p>Hi {{userName}},</p>

    <p>Thank you for contacting pyobfus support. We've received your message:</p>

    <blockquote style="border-left: 3px solid #667eea; padding-left: 15px; color: #555;">
      <strong>Subject:</strong> {{subject}}<br>
      <strong>Ticket ID:</strong> #{{ticketId}}
    </blockquote>

    <p><strong>We'll respond within 24 hours.</strong></p>

    <p>In the meantime, these resources might help:</p>

    <ul>
      <li><a href="https://github.com/zhurong2020/pyobfus/blob/main/README.md">Documentation</a></li>
      <li><a href="https://github.com/zhurong2020/pyobfus/blob/main/docs/LICENSE_ACTIVATION_GUIDE.md">License Activation Guide</a></li>
      <li><a href="https://github.com/zhurong2020/pyobfus/issues">Common Issues</a></li>
    </ul>

    <p>
      <a href="https://zhurong2020.github.io/pyobfus/" class="button">Visit Documentation</a>
    </p>

    <p>Best regards,<br>
    pyobfus Support Team</p>
  </div>
  <div class="footer">
    <p>This is an automated response. A human will review your message shortly.</p>
    <p>pyobfus - Modern Python Code Obfuscator</p>
  </div>
</body>
</html>
```

### 2.4 Deployment

**Commands**:
```bash
# Install dependencies
cd workers/email-handler
npm install

# Development
npx wrangler dev

# Test locally
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"to":"support@pyobfus.dev","from":"test@example.com"}'

# Deploy to production
npx wrangler publish

# Configure email routing
npx wrangler email route create support@pyobfus.dev email-handler
```

**Environment Variables**:
```toml
# wrangler.toml
[env.production]
vars = { SENDER_EMAIL = "support@pyobfus.dev" }

[env.production.email]
forward_to = "zhurong0525@gmail.com"
```

---

## Phase 3: Smart Email Processing

**Timeline**: 1-2 weeks
**Cost**: $5-10/month
**Priority**: Low (nice to have)

### 3.1 License Status Auto-Query

**Features**:
- Parse email content for license keys (regex: `PYOBFUS-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}`)
- Query Cloudflare KV for license status
- Generate status report
- Send detailed response automatically

**Implementation**:
```typescript
async function handleLicenseEmail(message: EmailMessage, env: Env) {
  const licenseKey = extractLicenseKey(message.raw);

  if (licenseKey) {
    // Query KV store
    const license = await env.LICENSE_KV.get(licenseKey, 'json');

    if (license) {
      // Generate status report
      const report = generateStatusReport(license);
      await sendEmail(message.from, 'License Status Report', report);

      // 90% of queries resolved without human intervention
      return;
    }
  }

  // Fallback: forward to human
  await message.forward(env.FORWARD_EMAIL);
}
```

### 3.2 Refund Request Tracking

**Features**:
- Log all refund requests to D1 database
- Send confirmation email immediately
- Create task for manual review
- Track SLA (2 business days)

**Database Schema**:
```sql
CREATE TABLE refund_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  license_key TEXT,
  subject TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'pending',
  processed_at DATETIME,
  processed_by TEXT,
  notes TEXT
);
```

### 3.3 FAQ Auto-Matching

**Features**:
- Keyword extraction from email
- Match against FAQ database
- Send relevant articles
- Track resolution rate

---

## Success Metrics

### Phase 1 (Immediate)
- ✅ All documentation updated with new email addresses
- ✅ Email forwarding working correctly
- ✅ Professional brand image established

### Phase 2 (1-2 weeks)
- 🎯 Auto-reply sent within 30 seconds for 100% of emails
- 🎯 Customer satisfaction: 4.5+/5.0
- 🎯 Response time improved by 50%

### Phase 3 (1-2 months)
- 🎯 90% of license inquiries resolved automatically
- 🎯 50% reduction in support workload
- 🎯 2-business-day SLA met for 95%+ of refunds

---

## Maintenance

### Weekly Tasks
- Review forwarded emails
- Check auto-reply effectiveness
- Update templates based on common questions

### Monthly Tasks
- Analyze email metrics
- Update FAQ content
- Review SLA compliance

### Quarterly Tasks
- Evaluate system performance
- Consider upgrades (Phase 3, Phase 4)
- User satisfaction survey

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Email not forwarded | High | Always forward to human as fallback |
| Auto-reply too generic | Medium | Use templates, personalize with name |
| Spam/abuse | Medium | Cloudflare spam filtering |
| Cost overrun | Low | Monitor usage, set alerts |
| Wrong auto-reply sent | Medium | Test thoroughly, log all actions |

---

## References

- [Cloudflare Email Routing Docs](https://developers.cloudflare.com/email-routing/)
- [Cloudflare Workers Email](https://developers.cloudflare.com/workers/runtime-apis/email-event/)
- [Resend API Docs](https://resend.com/docs)
- Internal: `docs/ROADMAP.md` - Operations & Support Automation section

---

**Last Updated**: 2025-11-12
**Next Review**: When ready to implement Phase 1
