# pyobfus Threat Model

Threat modeling and attack-surface analysis for pyobfus (OSPS-SA-03.02). This
is a living document; it records what we defend, what we deliberately do **not**
claim to defend, and the status of each mitigation. Honesty about non-goals is
part of the model — over-claiming protection is itself a risk to users.

Companion documents: [`SECURITY.md`](https://github.com/zhurong2020/pyobfus/blob/main/SECURITY.md) (reporting + trust
boundary), [`COMPARISON.md`](COMPARISON.md) ("bytecode protection is not
magic"), [`SELF_DOGFOODING_BEST_PRACTICES.md`](SELF_DOGFOODING_BEST_PRACTICES.md),
and the not-yet-launched [`AFFILIATE_PROGRAM_DESIGN.md`](AFFILIATE_PROGRAM_DESIGN.md).

## Assets

1. **Integrity of published artifacts** — the `pyobfus` / `pyobfus-mcp` wheels,
   the VS Code extension (Marketplace + Open VSX), and the `pyobfus-action`.
   Users must get what the maintainer built.
2. **Project secrets** — no long-lived PyPI token (OIDC), the Stripe webhook
   secret, the trial signing secret, Open VSX / publisher tokens, KV contents.
3. **License / trial records** — the Cloudflare KV store (paying customers +
   registered trials, including email addresses).
4. **Users' own source code** — passed to the obfuscator locally, and the
   reverse-mapping files it emits.
5. **Planned affiliate ledger** — referral identity, attributed Stripe order,
   commission state and payout evidence. This surface does not exist in
   production yet and must remain separate from customer licence material.

## Actors and trust boundaries

- **End user / evaluator** — runs the CLI/library locally on their own code.
  Trusted with their own machine and source.
- **AI agent** — drives the MCP server. Input is **untrusted**.
- **Paying customer** — holds a Pro license; interacts with the license Worker.
- **Anonymous internet** — can reach the public Worker endpoints and the public
  repo. Untrusted.
- **Contributor** — opens PRs. Untrusted until reviewed; write access is not
  granted casually (see [`GOVERNANCE.md`](https://github.com/zhurong2020/pyobfus/blob/main/GOVERNANCE.md)).
- **Maintainer** — trusted; holds release authority.
- **Affiliate (planned)** — an invited external promoter. Their link, claims,
  traffic and payout instructions are untrusted until validated and reviewed.

Boundaries: (a) the local machine ↔ the license Worker (network); (b) the AI
agent ↔ the MCP server (process input); (c) the public repo/CI ↔ release
publishing (OIDC); (d) untrusted PR code ↔ privileged CI credentials; and,
only after an affiliate pilot launches, (e) referral input ↔ Stripe Checkout ↔
the commission ledger.

## Assumptions (read these first)

- **Pro ships as readable source.** `pyobfus_pro/` is present in the public
  wheel. Any client-side license/trial check is therefore patchable by whoever
  runs it. This is a deliberate distribution choice, not an oversight.
- **Obfuscation is not encryption.** AST-level transformation raises the cost of
  reading and reverse-engineering; it does not make recovery impossible. A
  determined analyst with the artifact can recover behavior.
- **The user's machine is theirs.** pyobfus does not sandbox the code it
  produces or protect the host that runs it.

## Threats and mitigations

| ID | Threat | Mitigation | Status |
|----|--------|------------|--------|
| F1 | Tampered published artifact (wheel / extension / action) served to users | GitHub OIDC Trusted Publishing (no long-lived token), PEP 740 attestations, verifiable build report with output SHA-256, CodeQL on every push | **Mitigated** |
| F2 | Malicious or typosquatted dependency enters the build | Minimal declared deps, CodeQL, Dependabot security updates, SHA-pinned Actions (hardening ongoing) | **Partial** |
| F3 | Secret committed to the public repo | Pre-commit credential scan (`.githooks`, prints `file:line` only), GitHub secret scanning + push protection, OIDC removes the PyPI token entirely | **Mitigated + hardening** |
| F4 | License / trial bypass by a non-paying user | Server-side license verification; server-registered trial with per-email dedup and fail-closed issuance. **Explicitly NOT claimed tamper-proof** — see Assumptions | **Accepted residual risk (documented)** |
| F5 | Abuse of the license Worker | Stripe webhook HMAC-SHA256 signature verification (a missing check here was a real 2026-08 vuln, now fixed + deployed); trial endpoint validates input, dedups, rate-limit, fails closed without `TRIAL_SIGNING_SECRET`; admin endpoint uses constant-time token compare | **Mitigated** |
| F6 | Untrusted AI-agent input to the MCP server | Input validation in `pyobfus_mcp/_security.py`; analysis tools are read-only and do not execute scanned content; stable JSON contract | **Mitigated** |
| F7 | User over-trusts obfuscation as security | Honest documentation (COMPARISON, SECURITY trust boundary, this doc). Making it cryptographic is a non-goal | **Documented (non-goal)** |
| F8 | Reverse-mapping file leaks original symbol names | Mapping is sensitive by design; docs advise protecting it; build report/marker use relative labels only, never source, exclude patterns, or license/buyer values | **Documented** |
| F9 | Malformed input crashes obfuscation / corrupts output | Broad test suite (Py 3.9–3.14), opt-in `--verify-syntax` (in-memory `compile()`, no import/exec), cross-file correctness fixes | **Partial** |
| F10 | Release workflow mis-triggered by an unrelated tag | `release.yml` tag glob excludes `vscode-v*` after a real 2026-08 mis-fire; extension tags no longer touch PyPI publishing | **Fixed** |
| F11 | Replayed/out-of-order Stripe events mint duplicate licences or affiliate commissions | Launch gate: event + Checkout Session idempotency, paid-state gating and one shared fulfilment path; current Worker does not yet satisfy this gate | **Planned — affiliate launch blocked** |
| F12 | Forged/self-attributed referral, cookie stuffing or misleading endorsement earns commission | Launch gate: signed allowlisted reference, cookie-free v1, manual hold/review, self-referral and traffic-abuse policy, clear disclosure terms | **Planned — affiliate launch blocked** |
| F13 | Refund/dispute leaves an affiliate paid or a refunded licence active | Launch gate: auditable partial/full reversals linked to Session/PaymentIntent and the licence refund policy | **Planned — affiliate launch blocked** |
| F14 | Affiliate or buyer PII leaks through logs, reports or public repo | Launch gate: data minimization, hashed/redacted logs, aggregate affiliate reports, private tax/payout records, privacy-policy update | **Planned — affiliate launch blocked** |

## Out of scope / non-goals

- **Cryptographic protection of source.** pyobfus is obfuscation, not a code
  vault. If irrecoverability is the requirement, a compiled or VM-based tool
  (e.g. PyArmor's VMC/ECC, Nuitka) is the right layer — see
  [`compare/pyarmor.md`](compare/pyarmor.md).
- **Client-side license enforcement as a security boundary.** See Assumptions.
- **Protecting the host that runs obfuscated code.** Not a sandbox.
- **Vulnerabilities in the user's own dependencies.** Reported upstream, per
  SECURITY.md.
- **Protecting affiliates from ordinary commercial risk.** The proposed pilot
  does not guarantee traffic, conversion or minimum earnings.

## Review cadence

Revisit on any material change to the license Worker, the MCP surface, the
release pipeline, or the distribution model. Findings from CodeQL, self-scan,
and third-party scanners (e.g. `mcp-scanner`) feed back into this table.
