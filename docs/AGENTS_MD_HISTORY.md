# AGENTS.md history archive

## 2026-11-16 — Where to look next consolidation (historical)

Source: `git show 3171ef7f97bf9df68356b83ef1bda09fe5ffba59:AGENTS.md`.
The two dated bullet runs below are preserved verbatim from “Where to look next”.
They are historical snapshots, not current instructions or authorization.
Current work follows [the execution tracker](ROADMAP_EXECUTION_2026-11-16.md),
[TODO](TODO.md) and [the current plan](CURRENT_PLAN_ZH.md).

<!-- BEGIN VERBATIM AGENTS DATED BULLETS 1 -->
- **Latest (2026-11-16)**: Core **0.15.0 release follow-up is complete**. #242 (`e5e3cc2`) synced CITATION to verified Zenodo record `24248676`; #241 (`4204699`) upgraded upload-artifact to v7.0.2. Post-merge CI/CodeQL and the relevant IndexNow/Dogfood/PDF workflows succeeded. Upgrade-notice obligations are complete; details remain only in private `docs/internal/CUSTOMER_SUPPORT_LOG.md`. Versions and Worker signer are unchanged. Resume from [current handoff](docs/SESSION_CLOSEOUT_2026-11-16.md): routine feedback/backup/search observations, December first-week search/AI review, and Core 0.12.0 T+30d around December 4. Earlier entries below are historical.
- **Session closeout (2026-11-13)**: [closeout](docs/SESSION_CLOSEOUT_2026-11-13.md). Glama channel 0.14.0 confirmed; #230 (upgrade hint for an untrusted CI issuer key) and #231 (standby issuer key `ci-2026-11b`, not on the Worker) merged, shipping with the next Core release; planned key rotation needs 180 days after the trusting release plus 60 days' notice. #233 plans a Pro customer notice after the next Core release (no mass mail now). No release or deployment. Next: Nov 16 weekly review.
- **Latest (2026-11-11 night)**: Core **0.14.0 is published and verified** (signed CI build admission), tag `v0.14.0` / `96e6340`; see [release evidence](docs/CORE_0_14_0_RELEASE_2026-11-11.md). Production issuer key `ci-2026-11` and Worker `13aaa4a8` are live. Follow-up done 2026-11-12: CITATION synced to Zenodo record 24140234 (#224), Glama channel 0.13.1 installs Core 0.14.0 (the maintainer's second manual Build & Release on 2026-11-12 19:57 UTC published channel release 0.14.0; its test page shows the same pins installing Core 0.14.0 / MCP 0.3.17 and nine tools). Independent review of #221 done 2026-11-12 (one low finding: CI rate limit not actually configured), fixed by #227 and deployed as Worker `209eb969` (rollback `13aaa4a8`).
- **Session follow-up (2026-11-11)**: [closeout](docs/SESSION_CLOSEOUT_2026-11-11.md). Signed CI denial hardening `74769cd` passed 48 hosted checks (2 configured skips) and local regressions (Worker 70). #220 source review found no blockers; its merge decision remains pending. #221 still needs independent external review and key/rotation/release acceptance. No merge, production key, deployment or release was performed.
- **Earlier operations handoff (2026-11-11)**: [operations review](docs/OPERATIONS_REVIEW_2026-11-11.md). Core 0.13.0 remains current; T+7d and download/inbox/search/backup checks are recorded. Next: obtain the affected URL for the GSC redirect error, Nov 16 weekly review, F2 compatibility and offline migration decisions, and professional review of proprietary patent clauses. Earlier entries below are historical.
- **Session closeout (2026-11-07)**: [final handoff](docs/SESSION_CLOSEOUT_2026-11-07.md).
  Core 0.13.0 was released later that day, including Community
  pre-commit hooks (#194). IndexNow and Search Console/Bing registration were
  completed (keep `docs/google03878b382b498ff9.html` and the IndexNow key
  files). Next at that time: weekly checks, T+7d, monthly
  search/AI observation. The 2026-11-04 entry below is historical.
- **Session closeout (2026-11-04)**: [final handoff](docs/SESSION_CLOSEOUT_2026-11-04.md)
  and [cold-start prompt](docs/COLD_START_PROMPT_2026-11-04.md). Core/Action/Glama
  rollout and DEV review are complete; continue scheduled observations and verify
  new evidence in the next natural backup. Earlier pending-release notes are historical.

<!-- END VERBATIM AGENTS DATED BULLETS 1 -->

<!-- BEGIN VERBATIM AGENTS DATED BULLETS 2 -->
- **Latest (2026-11-07)**: Core **0.13.0 is published and verified** (Community
  pre-commit hooks; patent-pending notice), tag `v0.13.0` / `0f2c7b0`; see
  [release evidence](docs/CORE_0_13_0_RELEASE_2026-11-07.md). Zenodo (record
  24031969), CITATION and the Glama build are complete. The 0.12.0 entry below is historical.
- **Previous (2026-11-04)**: Core **0.12.0 is published and verified**, tag
  `v0.12.0` / `73ff6a8`; final full CI 47/47, CodeQL, PyPI dual-artifact
  cryptographic provenance and fresh installs passed. MCP 0.3.17 / runtime
  0.1.1 / extension 0.4.3 remain unchanged. See
  [release evidence](docs/CORE_0_12_0_RELEASE_2026-11-04.md) and
  [channel follow-up](docs/CORE_012_CHANNEL_FOLLOWUP_2026-11-04.md). Action
  v1.1.0 / `v1`, Glama channel 0.12.0 (Nov 5; 0.11.3 on Nov 4) and DEV one-week review are complete;
  future observation, LinkedIn and natural backup inclusion remain pending.
- **Status review and remediation (2026-11-03)**: [engineering and operations evidence](docs/EXECUTION_PROGRESS_2026-11-03.md). Local suites pass; Nov 2 scheduled Guard passed. Downloads and Gmail were refreshed; extension minimatch/glob remediation and ESLint v10 migration are recorded there. Core 0.12.0 remains scheduled for Nov 4, subject to release approval.
- **Previous execution tracker (2026-11-01)**: [session closeout](docs/SESSION_CLOSEOUT_2026-11-01.md) → [execution progress](docs/EXECUTION_PROGRESS_2026-11-01.md) → [current plan](docs/CURRENT_PLAN_ZH.md). Three maintenance PRs are merged; RTD deployment and backup verification are complete. Next: Nov 2 scheduled Guard, Nov 4 DEV review, and around Nov 5 LinkedIn review. Core 0.11.1 / MCP 0.3.17 / runtime 0.1.1 are unchanged. Earlier session records are historical.
<!-- END VERBATIM AGENTS DATED BULLETS 2 -->

