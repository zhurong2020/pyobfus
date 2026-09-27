# Affiliate Program Design

**Status:** approved design, not launched. No affiliate is currently enrolled,
no commission is currently earned, and the implementation and production
deployment remain separate approval gates.

This document defines a deliberately small affiliate pilot for the one-time
USD 45 pyobfus Professional Edition licence. Affiliate attribution is a
commerce concern: it belongs in Stripe, the Cloudflare Worker and an internal
commission ledger. It must not enter the CLI, the Pro runtime, generated
artifacts, licence files or release cadence.

## Decision

Start with an invitation-only, cookie-free pilot rather than building a public
affiliate platform or adopting Stripe Connect.

- Invite at most 3–5 partners who already publish relevant Python, software
  security or software-distribution content.
- Give each partner a first-party `/r/<slug>` redirect to the existing Stripe
  Payment Link.
- Attach a signed, opaque affiliate reference through Stripe Payment Link's
  `client_reference_id`; never trust a bare query-string affiliate ID.
- Pay 20% of eligible product revenue after the existing 30-day refund window.
- Review and pay monthly, with a USD 50 minimum; unpaid balances roll forward.
- Do not offer a buyer discount in the initial pilot. Promotion codes are a
  separate policy surface, not the attribution identity.
- Do not use attribution cookies or build an affiliate dashboard in v1.
- Review the pilot after three months. Stop rather than expand if it produces
  no attributable paid sale.

Stripe documents that `client_reference_id` is delivered on the Checkout
Session webhook and must not contain secrets or sensitive information:
<https://docs.stripe.com/payment-links/url-parameters>. The reference therefore
contains an internal affiliate ID, timestamp/version and HMAC, not an email,
name, payout address or licence key.

## Economics and policy

The initial commission contract is intentionally simple:

| Item | Pilot rule |
|---|---|
| Product | pyobfus Professional Edition, one-time licence only |
| Commission | 20% (`2000` basis points) |
| Basis | Product amount actually collected, excluding tax and later refunds/chargebacks |
| Payment fees | Not deducted from the affiliate's basis |
| Hold | 30 days from successful payment |
| Payout | Monthly, after manual review |
| Minimum payout | USD 50 equivalent; otherwise roll forward |
| Refund / dispute | Reverse in full, or proportionally for a partial refund |
| Self-referral | Ineligible |
| Attribution | Valid direct reference; an explicit valid promotion code may override it in a later version |

All money is stored as integer minor units plus an ISO currency code. Never use
floating point for a commission. The rate is snapshotted onto each commission
record so a later programme change cannot rewrite historical balances.

## Request and event flow

```text
affiliate content
    -> /r/<slug>
    -> validate active affiliate
    -> create signed opaque client_reference_id
    -> Stripe Payment Link
    -> paid Stripe webhook
       -> verify Stripe signature
       -> deduplicate event and Checkout Session
       -> issue exactly one licence
       -> write one pending commission
    -> refund/dispute event
       -> reverse or adjust commission
       -> apply the existing licence refund policy
    -> 30-day hold expires
       -> manual review -> approved -> monthly payout -> paid
```

The redirect can be implemented by the existing Cloudflare Worker or a
separate narrowly scoped Worker route. A copied referral link may still credit
the affiliate; that is intended. The HMAC prevents a buyer from inventing or
altering a valid affiliate identity, but it does not replace self-referral and
fraud policy.

## Required payment hardening before launch

The current Worker fulfils every `checkout.session.completed` event by creating
a random licence. The pilot must not launch until the common fulfilment path
has all of the following properties:

1. **Event idempotency.** Persist `stripe_event:<event.id>` and reject duplicate
   effects while still returning HTTP 200.
2. **Order idempotency.** Persist a Checkout Session to licence mapping so the
   same paid Session can never mint two licences or two commissions.
3. **Paid-state gating.** Fulfil a completed Session only when payment is paid;
   support `checkout.session.async_payment_succeeded` and do not fulfil failed
   delayed payments. Stripe explicitly requires extra events for delayed
   payment methods: <https://docs.stripe.com/payment-links/url-parameters>.
4. **Refund and dispute handling.** Create auditable reversals, including
   proportional adjustments for partial refunds. Do not delete the original
   commission record.
5. **Stable linkage.** Store the Stripe Session and PaymentIntent identifiers
   on both the licence and commission records.
6. **Privacy-safe logs.** Do not log the full licence key, buyer email, payout
   destination or tax identity. Log event/session IDs, affiliate ID, internal
   record ID and a one-way email hash only where necessary.
7. **Atomic state model.** KV is acceptable for a tiny pilot only with explicit
   idempotency and reconciliation. Reassess Durable Objects or a transactional
   database before concurrent volume makes cross-key races material.

The webhook secret remains the trust boundary. Affiliate parameters never
authorize licence issuance; only a verified, paid Stripe event does.

## Data model

Recommended logical records (exact storage may change during implementation):

```text
affiliate:<affiliate_id>       partner policy/status; no buyer data
affiliate_slug:<slug>          public slug -> internal ID
stripe_event:<event_id>        processed marker/result
stripe_session:<session_id>    single fulfilment and licence mapping
commission:<session_id>        immutable sale facts + state transitions
```

A commission record needs at least:

```json
{
  "stripe_session_id": "cs_...",
  "affiliate_id": "aff_...",
  "currency": "usd",
  "gross_amount": 4500,
  "eligible_amount": 4500,
  "commission_bps": 2000,
  "commission_amount": 900,
  "status": "pending",
  "hold_until": "ISO-8601 timestamp",
  "refund_amount": 0,
  "created_at": "ISO-8601 timestamp",
  "approved_at": null,
  "paid_at": null
}
```

Allowed state transitions are `pending -> approved -> paid`, with `pending` or
`approved` able to move to `reversed`; corrections are explicit adjustment
records. A payout must never be inferred from a missing record.

Affiliate tax and payout documents must not be placed in the public repository
or the licence KV. Store only the minimum operational status/reference needed
by the commission ledger and keep the authoritative documents in the approved
private accounting system.

## Attribution and abuse rules

- Accept only active, allowlisted affiliates and server-validated references.
- Reject self-referrals and obvious affiliate/buyer identity overlap.
- Do not pay on refunded, disputed, fraudulent, test-mode or zero-value orders.
- Ban cookie stuffing, browser-extension injection, coupon-site leakage,
  misleading redirects and forced clicks.
- Ban bidding on `pyobfus`, confusing variants, maintainer names or lookalike
  domains without written approval.
- Affiliates may not impersonate the project or promise unbreakable protection,
  guaranteed outcomes or capabilities absent from current documentation.
- Review anomalous velocity, repeated buyer/payment identities and concentrated
  refunds before approval; do not automatically reject solely by country.
- Keep an appeal/audit trail for every manual reversal or suspension.

FTC guidance requires the financial relationship to be disclosed clearly and
conspicuously near the endorsement; a bare “affiliate link” or Buy button may
not be enough: <https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking>.
Provide affiliates a plain-language template such as:

> I may earn a commission if you purchase pyobfus through this link.

The disclosure must be in the language of the endorsement and adapted to other
applicable local advertising rules.

## Privacy, legal and accounting gates

Before production launch:

- Finalize the separate affiliate terms from
  [`legal/AFFILIATE_PROGRAM_TERMS_DRAFT.md`](legal/AFFILIATE_PROGRAM_TERMS_DRAFT.md).
- Update the effective Privacy Policy to describe referral identifiers,
  commission records, purposes, retention, processors and affiliate rights.
  Do not change the policy early: it currently truthfully says that the site
  uses no tracking cookies, and the proposed v1 preserves that statement.
- Update the EULA only where customer refund/revocation behaviour changes; do
  not make affiliates parties to the customer licence agreement.
- Have the actual paying entity's accountant determine onboarding documents,
  cross-border payment evidence, withholding and information reporting. Do not
  infer tax treatment from an affiliate's email or country alone.
- Record payout currency, amount, date, method, recipient and evidence in the
  private accounting system; never collect bank credentials in pyobfus KV.
- Define retention/deletion rules that preserve legally required accounting
  evidence without keeping referral data indefinitely.

## Rollout and acceptance criteria

### Phase 0 — documentation (this document)

- Architecture, economics, abuse policy and legal gates are explicit.
- Status remains “not launched”; there is no public enrolment promise.

### Phase 1 — hardened pilot

- Tests cover duplicate/out-of-order events, paid vs unpaid/delayed methods,
  bad and expired HMAC references, unknown/inactive affiliates, partial/full
  refunds, disputes, self-referral review and replayed payout actions.
- Existing licence purchase/activation remains unchanged without a referral.
- Production test-mode exercise proves one Session creates one licence and one
  pending commission; no raw PII or licence appears in logs.
- KV backup validation and restore documentation understand every new record
  type before the first production record is written.
- Privacy policy and final terms are live before invitations are sent.

### Phase 2 — evidence review after three months

Track clicks, Checkout starts where available, paid conversions, eligible net
revenue, refunds/disputes, approved/paid commission and support time. Aggregate
metrics must not expose buyer identity to affiliates.

Do not add cookies, a portal, Stripe Connect or a third-party affiliate SaaS
unless there are at least 5–10 active affiliates, recurring manual workload or
enough monthly commission to justify the added processor, privacy and tax
surface. Zero attributable sales means stop the pilot rather than automate it.
