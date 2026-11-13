# Session closeout — 2026-11-13

## What changed

| Item | Result |
|---|---|
| Glama channel | Maintainer's second manual Build & Release (test `01a1d155-5ae8-767a-816e-dc0d2966670a`) published channel release **0.14.0**; its test page shows Core 0.14.0 / MCP 0.3.17 / runtime 0.1.1 and nine tools. Auto-Release is enabled on Glama, but it builds with the current Build steps pins, so after a Core release the pins must still be updated by hand. Recorded in #229 (`be06f30`). |
| Untrusted issuer key hint | #230 (`dc47f26`): a well-formed but untrusted CI lease `kid` now yields a fixed "upgrade pyobfus" message; the build is still denied. Implemented by headless Codex, reviewed by Claude. |
| Standby issuer key | #231 (`d3ff339`): `ci-2026-11b` added to `TRUSTED_PUBLIC_KEYS`. Not configured on the Worker. Pairing and an end-to-end signed lease were verified locally; the private key is backed up in the maintainer's secret store and checked byte-for-byte against the local copy. |
| Rotation policy | Planned (non-emergency) signer switch: no earlier than 180 days after the first release that trusts the new key, with at least 60 days' notice to Pro customers. Chosen because a switch can affect existing customers who pin an older ≥0.14.0 client in CI. Documented in `docs/CI_LICENSING.md`. |

Hosted CI: #229 6 success / 9 skipped (docs-only), #230 47 / 2 skipped, #231 46 / 2 skipped. Local: Core 5091 passed / 55 skipped, MCP 167, integration 368 / 10 skipped, `scripts/check.sh` OK.

No Core, MCP, runtime, extension or Action release; no Worker deployment. #230 and #231 ship with the next natural Core release, which still needs explicit approval.

## Status snapshot

- Downloads (pypistats through 11-11): Core last-7-day quiet-day median 58 (only 3 quiet days), 30-day 86; MCP 7 / 12. No customer mail waiting.
- Public versions unchanged: Core 0.14.0, MCP 0.3.17, runtime 0.1.1, extension 0.4.3, Action v1.1.0; Worker `209eb969` (rollback `13aaa4a8`).

## Next

1. Nov 16 weekly review: downloads, inbox, GSC (`/zh-cn/` indexing, both properties' sitemaps; RTD sitemap after #226), Bing IndexNow record.
2. Around Dec 4: Core 0.12.0 T+30d.
3. First week of December: monthly search / AI observation.
4. Next Core release: carries #230 and #231; follow the release checklist (README banner, Agent docs check, Glama pins).
5. Maintainer-side: professional review of proprietary licence patent clauses, channel trial, other items in [TODO](TODO.md).

Private detail: `docs/internal/f2-ci-implementation-2026-11-11/KEY_ROTATION_PLAN_2026-11-13.md`.
