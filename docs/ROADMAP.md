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
| Sensitive-resource / original-asset leak check | Community | Reference-app audit identifies a reusable detection gap; define sensitive-resource scope first | Bounded local inspection with positive/negative fixtures and explicit unknown/truncation results | No actionable gap; never infer clean from unparsed data | Candidate; scope first |
| Python 3.15t | Community / Pro | T4 demand gate plus a real free-threaded interpreter; ordinary 3.15 is insufficient | Public-wheel evidence; GIL state after cryptography/cffi imports, provider concurrency and exception recovery | Interpreter unavailable, unsupported dependency or unsafe runtime behavior; keep rejection | Unscheduled; prior bounded smoke is not full support |
| Automatic mapping selection | Community | Real multi-build debugging need beyond trace-marker IDs and mismatch warnings | Select the correct private mapping or report ambiguity/mismatch | No user need or unreliable identification | Demand-gated |

### Delivery

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| Reference app PyInstaller onedir/onefile (T3) | Community | Reuse public app with Core 0.15.0; fixed tool versions and artifact hashes | Run after hiding source; restore traceback; actually inspect CArchive top-level members, explicitly leave PYZ uninspected; no false clean. Correct the stale Windows workflow v4.6.2 comment during maintenance | Baseline/toolchain failure or sensitive artifact; code changes only for a demonstrated defect; no automatic matrix expansion | Planned 2026-11-23–29 |
| Pro stage C frozen delivery (T5) | Pro | Maintainer separately approves isolated CI trial licence issuance | Same app L3: correct key matches baseline, missing/wrong key fail closed, truthful coverage and mapped traces; isolate HOME/state | No isolated licence, real keys/state required or unsafe artifacts | Blocked; awaiting maintainer decision |
| Second frozen format / Nuitka payload parsing | Community | T4 gate and actual blocked delivery after the first format's feedback | Documented format, bounded non-executing inspection; checked/unknown/tool-missing/truncated distinguished | No demand, no safe parser, exceeded limits; never call uninspected payload clean | Demand-gated; unscheduled |

### Protection

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| Resource key provider | Pro | T4 demand gate; actual protected-resource use case | Define key injection timing, scope, rotation, concurrency, missing/wrong-key behavior before a primitive; application owns keys | No real need or no agreed contract; no hosted key service; do not reuse L3 provider as a resource Vault contract | Demand-gated; unscheduled |
| L3 methods / nested functions | Pro | T4 demand gate; minimized real coverage blocker | Define descriptors, classmethod/staticmethod, decorator order, `super()`, closures/nonlocal, inheritance/override, exception mapping and coverage skip reasons before implementation | Undefined semantics or compatibility regression; no blanket coverage claim | Demand-gated; unscheduled |

### Trust

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| Planned CI issuer-key rotation | Pro | Trusting Core 0.15.0 released for 180 days; at least 60 days' formal notice specifying minimum client version and switch date | Separately approved rotation, compatible-client admission and rollback evidence | Before approximately **2027-05-14**, notice period unmet or acceptance incomplete; workstation/offline migration remains a separate deferred decision | Standby distributed; no switch scheduled |
| Proprietary patent clauses / offline migration | Pro | Professional clause review; maintainer decides F2 compatibility/acceptance and lifetime-entitlement preservation | Reviewed Pro/runtime terms; separately agreed migration contract and tests | Review or compatibility decision missing | Decision pending; no release implied |

### Distribution

| Item | Edition (Community/Pro) | Trigger / evidence needed | Acceptance | Stop condition | Status |
|---|---|---|---|---|---|
| COMPARISON refresh (T2) | Community / Pro | 11-15 review; recheck changeable facts before publication | Dated official version/price sources, PyLocket coverage and honest strengths/limits under the comparison policy | Unverifiable claim; no Core release for docs | Planned 2026-11-17–22 |
| Demand intake and thresholds (T4) | Community / Pro | Delivery-blocker/frozen-format issue template and reference-app feedback | Three metrics and explicit P1/P2 thresholds entered in this table | No evidence for thresholds; demand-gated work stays unscheduled | Planned 2026-11-23–29 |
| Search / AI visibility (T6) | Community / Pro | December first-week observation; Core 0.12.0 T+30d around 12-04 | Comparable search/AI observations; later per-version observations join weekly review | Missing data stays unknown; release spikes are not growth | Scheduled 2026-12-01–05 |
| Pro purchase path (T7) | Pro | Explain self-managed, verifiable delivery using reference-app evidence | Buyer can understand protection, private debugging, key ownership and delivery-check limits | Unsupported protection claims or hosted commerce expansion | Planned December; scope/acceptance to confirm |

## Demand triggers

Thresholds are defined in task T4 (see ROADMAP_EXECUTION_2026-11-16.md); until then demand-gated items stay unscheduled.

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
