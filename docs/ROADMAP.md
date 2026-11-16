# Development Roadmap

pyobfus provides **verifiable and debuggable Python code protection for continuous
delivery**. Its four pillars are **Protect** (local, framework-aware multi-file
protection), **Verify** (build/coverage reports, delivery checks and supply-chain
evidence), **Debug** (private mappings and traceback recovery), and **Deliver**
(validated packaging, CI and offline licensing). The
[2026-11-15 review](COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md) prioritizes a
repeatable delivery workflow before adding transforms.

Baseline: Core **0.15.0** / MCP **0.3.17** / runtime **0.1.1** /
VS Code extension **0.4.3** / Action **v1.1.0**.
Implementation, release, Worker deployment and licence issuance are separate
maintainer gates; a roadmap row authorizes none of them. Each merge also needs
maintainer approval. Follow the [edition policy](EDITION_BOUNDARY_POLICY.md):
correctness, security, compatibility and basic local verification/debugging stay
Community; stronger protection and distribution control belong in Pro.

## Done in the 2026-11-15 cycle

- [Public delivery reference app](DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md):
  self-contained multi-module source, resources, allowlisted plugin, mapped
  exceptions and Community directory contract; [example](../examples/delivery_reference/README.md).
- [Windows Nuitka single-cell acceptance](DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md):
  Windows x64 / CPython 3.12.10 / Nuitka 4.3.1 / Core 0.14.0. **Partial**:
  D9/F is unknown because embedded PE payloads were uninspected; Pro stage C
  is blocked without an isolated licence. The consumer was the builder with
  Python installed, so this is not clean-target or wider-platform evidence.
- [Core 0.15.0](CORE_0_15_0_RELEASE_2026-11-15.md) shipped bounded PyInstaller
  CArchive top-level `--check-delivery` checks. Embedded PYZ/marshalled code and
  unknown members remain explicitly uninspected; no payload is executed.
- The same [release](CORE_0_15_0_RELEASE_2026-11-15.md) pre-distributed standby
  issuer public key `ci-2026-11b`; the Worker still signs with `ci-2026-11`.

## Next 6–12 months

These are evidence-driven candidates, not release commitments. T IDs refer to
[the execution tracker](ROADMAP_EXECUTION_2026-11-16.md); keep one product item
active at a time. No defect means no release; no Core release is planned before
mid-December 2026. Acceptance/stop criteria below bound any later approved work.

### Correctness

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| Semantic fixes before broader renaming | Community | Real minimized behavior/diagnostic failure; parameter renaming and complex import cycles need their own scope | Original/output parity and supported-interpreter regressions; conservative reasons for skipped proofs | No reproducible defect or no compatibility contract | Case-triggered |
| Sensitive-resource / original-asset leak check | Community | [Resource leak check demand trigger](#demand-triggers); define sensitive-resource scope first | Bounded local inspection with positive/negative fixtures and explicit unknown/truncation results | No actionable gap; never infer clean from unparsed data | Candidate; scope first |
| Python 3.15t | Community / Pro | [Python 3.15t validation demand trigger](#demand-triggers); real free-threaded interpreter required; ordinary 3.15 is insufficient | Public-wheel evidence; GIL state after cryptography/cffi imports, provider concurrency and exception recovery | Interpreter unavailable, unsupported dependency or unsafe runtime behavior; keep rejection | Unscheduled; prior bounded smoke is not full support |
| Automatic mapping selection | Community | Real multi-build debugging need beyond trace-marker IDs and mismatch warnings | Select the correct private mapping or report ambiguity/mismatch | No user need or unreliable identification | Demand-gated |

### Delivery

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| Reference app PyInstaller onedir/onefile (T3) | Community | Reuse public app with Core 0.15.0; fixed tool versions and artifact hashes | Run after hiding source; restore traceback; actually inspect CArchive top-level members, explicitly leave PYZ uninspected; no false clean. Correct the stale Windows workflow v4.6.2 comment during maintenance | Baseline/toolchain failure or sensitive artifact; code changes only for a demonstrated defect; no automatic matrix expansion | Done 2026-11-16: PR #244 merged (`4c00a7c`), packaging lane green with PyInstaller 6.22.3 |
| Pro stage C frozen delivery (T5) | Pro | Maintainer separately approves isolated CI trial licence issuance | Same app L3: correct key matches baseline, missing/wrong key fail closed, truthful coverage and mapped traces; isolate HOME/state | No isolated licence, real keys/state required or unsafe artifacts | Blocked; awaiting maintainer decision |
| Directory scan applies the CArchive check to executables inside an onedir output | Community | T3 evidence (2026-11-16): scanning the onedir directory reports the bootloader as `found=1, inspected=0`, while checking the executable directly inspects its CArchive | Directory scan reports the same per-executable inspection as the single-file path; bounded by the existing limits; unknown stays unknown | No safe reuse of the existing bounded reader | Candidate; needs implementation approval |
| Second frozen format / Nuitka payload parsing | Community | [Second frozen format / Nuitka payload inspection demand trigger](#demand-triggers) | Documented format, bounded non-executing inspection; checked/unknown/tool-missing/truncated distinguished | No demand, no safe parser, exceeded limits; never call uninspected payload clean | Demand-gated; unscheduled |

### Protection

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| Resource key provider | Pro | [Resource key provider demand trigger](#demand-triggers); actual protected-resource use case | Define key injection timing, scope, rotation, concurrency, missing/wrong-key behavior before a primitive; application owns keys | No real need or no agreed contract; no hosted key service; do not reuse L3 provider as a resource Vault contract | Demand-gated; unscheduled |
| L3 methods / nested functions | Pro | [L3 methods / nested functions demand trigger](#demand-triggers); define the semantics listed in Acceptance before scheduling | Define descriptors, classmethod/staticmethod, decorator order, `super()`, closures/nonlocal, inheritance/override, exception mapping and coverage skip reasons before implementation | Undefined semantics or compatibility regression; no blanket coverage claim | Demand-gated; unscheduled |

### Trust

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| Planned CI issuer-key rotation | Pro | Trusting Core 0.15.0 released for 180 days; at least 60 days' formal notice specifying minimum client version and switch date | Separately approved rotation, compatible-client admission and rollback evidence | Before approximately **2027-05-14**, notice period unmet or acceptance incomplete; workstation/offline migration remains a separate deferred decision | Standby distributed; no switch scheduled |
| Proprietary patent clauses / offline migration | Pro | Professional clause review; maintainer decides F2 compatibility/acceptance and lifetime-entitlement preservation | Reviewed Pro/runtime terms; separately agreed migration contract and tests | Review or compatibility decision missing | Decision pending; no release implied |

### Distribution

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| COMPARISON refresh (T2) | Community / Pro | 11-15 review; recheck changeable facts before publication | Dated official version/price sources, PyLocket coverage and honest strengths/limits under the comparison policy | Unverifiable claim; no Core release for docs | Refreshed 2026-11-16 (key facts rechecked live); merge pending |
| Demand intake and thresholds (T4) | Community / Pro | [Delivery-blocker/frozen-format issue template](../.github/ISSUE_TEMPLATE/delivery_blocker.md) and reference-app feedback | Three signals and explicit [demand triggers](#demand-triggers) referenced by the corresponding table rows | No trigger met; demand-gated work stays unscheduled | Intake and thresholds defined; review weekly |
| Search / AI visibility (T6) | Community / Pro | December first-week observation; Core 0.12.0 T+30d around 12-04 | Comparable search/AI observations; later per-version observations join weekly review | Missing data stays unknown; release spikes are not growth | Scheduled 2026-12-01–05 |
| Pro purchase path (T7) | Pro | Explain self-managed, verifiable delivery using reference-app evidence | Buyer can understand protection, private debugging, key ownership and delivery-check limits | Unsupported protection claims or hosted commerce expansion | Planned December; scope/acceptance to confirm |

## Demand triggers

Signals counted:

1. Open/closed issues labelled `delivery-blocker` from distinct reporters:
   `gh issue list --label delivery-blocker --state all`. Use the
   [Delivery blocker / frozen format template](../.github/ISSUE_TEMPLATE/delivery_blocker.md).
2. Direct support requests that name a blocked delivery, counted privately.
   The public doc records counts only abstractly; customer, payment, personal
   and support-case details stay in private records.
3. Core quiet-day download median from `scripts/download_snapshot.py` as context,
   never as a trigger.

Count independent requests across issues and support without double-counting
the same request or reporter.

Triggers: a demand-gated item becomes schedulable, still subject to
implementation approval:

- **Resource leak check (Community):** 1 delivery-blocker report or support
  request involving a leaked/raw asset, or the maintainer's own T3 evidence
  showing a gap.
- **Resource key provider (Pro):** ≥2 independent requests, or 1 paying customer
  blocked.
- **L3 methods / nested functions (Pro):** 1 real minimal reproduction from a
  user that blocks shipping, after the semantics list in the table is defined.
- **Second frozen format / Nuitka payload inspection (Community):** ≥2
  independent requests naming that format.
- **Python 3.15t validation:** a user request, or the project's crypto
  dependencies publishing free-threaded wheels — whichever comes first;
  evidence must use a real free-threaded build.

Review cadence: the Monday weekly check counts signals. A trigger met is
recorded in [ROADMAP_EXECUTION_2026-11-16.md](ROADMAP_EXECUTION_2026-11-16.md)
(or its successor) with the evidence link before work starts. For private
support evidence, use a pointer to the private record and an abstract public
statement without identifying details.

Stop rule: if no trigger fires in 90 days, the item stays unscheduled and the
next quarterly roadmap review decides whether to drop it.

## Not doing

- Native VM/VMC/BCC or a new compiler backend.
- Cloud obfuscation service, store, automatic updates or hosted downloads.
- Anti-VM, AV bypass or strong anti-debug races.
- `--output-pyc` beyond a bounded feasibility spike.
- AI-generated transformers as a roadmap priority.

## Where to continue

- [TODO](TODO.md): what next, in which order.
- [Execution tracker](ROADMAP_EXECUTION_2026-11-16.md): T0–T7 progress and gates.
- [Current plan](CURRENT_PLAN_ZH.md): operational truth.
- [Historical roadmap](ROADMAP_HISTORY_2026-11-16.md): verbatim rationale at
  `764ead1`, including superseded Glama passages; not live status.
