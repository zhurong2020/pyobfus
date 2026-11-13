# AGENTS.md — pyobfus

Canonical, tool-agnostic guide for AI coding agents (and humans) working **on**
the pyobfus codebase. Tool-specific files defer here: `CLAUDE.md` imports this
file; Cursor / Windsurf / Aider / Codex read `AGENTS.md` natively.

> Looking to *use* pyobfus to protect your own code, not develop it? See the
> [`pyobfus-review`](skills/pyobfus-review/SKILL.md) skill (read-only: should
> we obfuscate this, and what breaks?), the
> [`pyobfus-protect`](skills/pyobfus-protect/SKILL.md) skill (do it, and verify
> the result), and the [`templates/ai-integration/`](templates/ai-integration/)
> rule files instead.

## What this project is

pyobfus is an **AST-based Python code obfuscator** — framework-aware presets,
reverse stack-trace mapping for AI-assisted debugging, and a machine-readable
JSON CLI. A transparent, open-source alternative to PyArmor. The repo ships
**three Python distributions**:

- `pyobfus/` — the obfuscator (CLI + library). Published as `pyobfus`.
- `pyobfus_mcp/` — an MCP server exposing the tools to AI agents. Published as
  `pyobfus-mcp`.
- `pyobfus_runtime/` — the minimal redistributable runtime used by generated
  Pro artifacts. Published separately as `pyobfus-runtime`; it is not part of
  the Apache-2.0 core.

Plus `pyobfus_pro/` (commercial, license-gated features) kept source-separated
from the Apache-2.0 core.

## Setup

Use the repository-local **`venv/`** on WSL/Linux. If a `.venv/` directory
shows up, it is a Windows-side legacy environment (the checkout moved from a
Windows-synced folder into WSL on 2026-09-21 and did not carry it over); WSL
cannot reliably run its executables, so don't use it. Either activate `venv/`
first, or call tools through `venv/bin/...` directly.

**Operational boundary:** perform all local development, testing, builds,
release preparation, and maintainer commands for pyobfus Core, MCP, runtime,
and `pyobfus-action` from their WSL checkouts under `~/projects/`.
OneDrive copies are migration remnants or backups only: do not edit, execute,
build, commit, tag, or publish from them. Hosted GitHub Actions CI/release jobs
remain the expected remote exception to this local WSL-only rule.

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
git config core.hooksPath .githooks   # once per clone — pre-commit (PII + credentials) and pre-push (scripts/check.sh)
```

## Build / test / lint — run before every commit

```bash
scripts/check.sh                       # black, ruff, mypy, README links, mkdocs --strict (~10 s)
venv/bin/pytest tests/                 # core suite (run each test root separately)
venv/bin/pytest pyobfus_mcp/tests/     # MCP server suite
venv/bin/pytest integration_tests/     # end-to-end CLI
venv/bin/pytest pyobfus_runtime/tests/  # redistributable runtime boundary
venv/bin/pytest benchmarks/llm_resistance/test_smoke.py benchmarks/llm_resistance/test_key_exposure.py
```

`scripts/check.sh` is the only list of lint/type/docs paths: CI's lint and
docs jobs call the same script, and the `pre-push` hook runs it before every
push. Do not replace it with a shorter hand-typed command such as
`black pyobfus/`; CI checks ten paths, and a file that only CI looked at
turned main red for nine pushes on 2026-09-20. To fix formatting, run
`venv/bin/black` on the paths the script reports.

Note: the core and MCP test roots are collected as **separate** pytest
invocations (CI runs them as separate jobs) — don't point one `pytest` at both
roots at once.

Tests must never read, write, or delete a developer's real pyobfus state under
`~/.pyobfus` (notably `trial.json` and `license.json`) or place generated run
counters in the real home directory. Bind module-level state paths and any
generated-code `HOME` / `USERPROFILE` lookup to pytest's per-test `tmp_path`.
The standard commands above must pass with the caller's normal HOME; requiring
`HOME=/tmp/...` is a test-isolation regression, not an accepted prerequisite.

**4th test root — `vscode-extension/`** (Node/npm, not pytest; independent
package, see `docs/VSCODE_EXTENSION_PLAN.md`):

Use Node.js 22.13 or later on the Node 22 line (the ESLint v10 development
toolchain requires it; CI uses Node 22).

```bash
cd vscode-extension
npm ci
npm run lint          # eslint
npm run typecheck     # tsc --noEmit
npm run pretest       # esbuild + compile tests to out/
PYOBFUS_PYTHON_PATH="$(cd .. && pwd)/venv/bin/python3" npm test
```

`npm test` needs a **resolvable interpreter with pyobfus actually
installed** for the real-contract integration tests (`test/suite/
integration.test.ts`) — without `PYOBFUS_PYTHON_PATH` set, interpreter
resolution falls back to a bare `python3`/`python` on PATH (the
`ms-python.python` extension isn't active inside the plain
`@vscode/test-electron` test profile), which on a fresh machine likely
doesn't have pyobfus installed and fails 4 of the tests with a "no module
named pyobfus" error — not a real bug, just a missing env var. WSLg (or
any real X server) is required for `@vscode/test-electron` to launch;
`xvfb-run -a npm test` works too if there's no display available.

The test host defaults to the latest VS Code `stable` release because
`vscode-extension/.vscode-test.mjs` does not pin `version`. A new stable
release therefore downloads a new host into `vscode-extension/.vscode-test/`,
alongside older version caches. This is separate from the Python `venv/`;
an existing older host does not mean the latest host is already cached.
Keep this compatibility check current; do not pin an old host merely to avoid
a download or delete caches as part of a routine status check.

CI runs this as a separate, path-filtered workflow
(`.github/workflows/vscode-extension-ci.yml`, sets the same env var to
`${{ env.pythonLocation }}/bin/python`), not as part of the Python
`ci.yml` jobs above.

**Python 3.15 compatibility** shipped in Core 0.8.0 (2026-10-20, PR #108):
lazy imports (PEP 810) and comprehension unpacking (PEP 798) are preserved,
and CI runs 3.15 on all three platforms. See
[`docs/PYTHON315_SUPPORT_PLAN.md`](docs/PYTHON315_SUPPORT_PLAN.md) and
[`docs/PYTHON315_VALIDATION.md`](docs/PYTHON315_VALIDATION.md) for scope,
validation evidence and known limitations.

Core CI (`.github/workflows/ci.yml`) runs Ubuntu 3.9–3.15 and Windows/macOS
3.9, 3.14 and 3.15 on ordinary code pushes/PRs (13 cells). Scheduled and
manual runs cover all 21 OS/version cells. Core and CLI integration use
`pytest-xdist -n auto`; serial local pytest commands remain supported. Only
Ubuntu 3.11 collects coverage (printed in the job log; no external upload). Non-hidden `docs/**/*.md` prose changes skip
heavy jobs; lint and docs always run, and unknown paths trigger full CI.
`CI result` aggregates all CI jobs, accepting success/skipped and rejecting
failure/cancellation; the `protect-main` ruleset requires only `CI result` and
`CodeQL` (since 2026-10-21). Agents must not edit rulesets. Multi-command test
steps run under bash so the first failing pytest fails the job.
Core jobs time out after 30 minutes, integration after 15, others after 10.
New PR pushes cancel superseded runs; main runs are never cancelled by this policy.

Release validation must cover every maintained workflow pytest command, not
only the four local roots. Verify MCP SDK compatibility and Python 3.15 jobs
through their maintained hosted workflows, and run the complete manual 21-cell
matrix on the final release revision.

A release that changes agent-visible behavior (flags, exit codes, JSON fields,
licensing requirements, MCP tools) updates the agent-facing docs in the same
PR: `llms.txt` and `llms-full.txt` (plus their `docs/` mirrors),
`templates/ai-integration/AGENTS.md`, `skills/*/SKILL.md` and
`docs/.well-known/ai-catalog.json`. Keep `llms-full.txt` to current behavior
and feature minimum versions; history stays in `CHANGELOG.md`.

Every release also checks the patent boundary: mechanisms covered by the
pending patent application live only in `pyobfus_pro/` or `pyobfus_runtime/`,
never in the Apache-2.0 core (Apache-2.0 §3 would grant the patent rights for
core code). Public wording is "patent pending (CN 202610712171X, not yet
granted)", never "patented".

Targets: Python **3.9–3.15** must all pass. (Python 3.8 was dropped in 0.5.0 —
EOL 2024-10 — which removed the old `astunparse`/`@requires_py39` flakiness;
`docs/PYTHON38_COMPATIBILITY.md` is retained only as historical record.)

## Self-dogfooding boundary

Use pyobfus itself for read-only analysis/reporting and exercise obfuscation on
maintained canary fixtures or freshly built wheels; do not replace the public
package sources with a self-obfuscated tree. A current checkout must not be the
only verifier of artifacts it produced: pair it with the latest public release,
normal Python tooling, independent schema validation, hosted attestations, and
fresh-environment install tests as appropriate.

Self-scan findings are initially audit evidence, not an automatic blocking
gate. Do not exclude the whole `pyobfus/` tree or weaken a general detection
merely to make the repository's own report green. Suppress intentional patterns
only through a reviewed, precise rule with a technical reason; claim SARIF
`baselineState` only after a complete comparison. See
[`docs/SELF_DOGFOODING_BEST_PRACTICES.md`](docs/SELF_DOGFOODING_BEST_PRACTICES.md)
for the staged policy and current baseline.

## Repository layout

```
pyobfus/            # core obfuscator: cli.py, config.py, core/, transformers/
pyobfus_mcp/        # MCP server (FastMCP): pyobfus_mcp/{server,tools,_security}.py
pyobfus_pro/        # Pro edition (commercial license) — kept separate from core
skills/             # agent skills (pyobfus-review, pyobfus-protect) + plugin marketplace
templates/          # copy-in AI rule files + python-baseline bootstrap
tests/ · pyobfus_mcp/tests/ · integration_tests/
docs/               # CURRENT_PLAN_ZH.md / TODO.md (current planning), archived roadmap, threat model
cloudflare-worker/  # Pro license verification Worker
```

## Conventions

- **Stable JSON contract.** Every CLI mode and MCP tool returns a dict with
  `status`, `ai_hint`, and (MCP) a machine-readable `next_tool` field. Don't
  break these shapes without a version bump.
- **Dual license, separated source.** Never move Pro logic into the Apache-2.0
  core or vice-versa. Never commit Pro license keys or the Stripe webhook secret
  to this public repo.
- **Public repo.** This is `zhurong2020/pyobfus`, public. The pre-commit hook
  runs three independent scans: a fixed set of personal identifiers,
  credential shapes (Open VSX / PyPI / GitHub / GitLab / npm / Anthropic /
  OpenAI / AWS / Slack / Google tokens, PEM private keys), and — in added
  lines only — Stripe object IDs and e-mail addresses outside an allowlist;
  a `commit-msg` hook applies the last scan to commit messages. Keep all of
  them out of code, commits, and docs. Each scan has its own bypass
  (`PYOBFUS_ALLOW_PII=1` / `PYOBFUS_ALLOW_SECRET=1` /
  `PYOBFUS_ALLOW_CUSTOMER_DATA=1`) — waving through a documented PII string
  does not wave through a token. Credential hits print
  `file:line` only, never the value. If a blocked credential was ever real,
  **rotate it**; deleting it from the file is not a rotation. Details:
  `.githooks/README.md`.
- **Competitor comparisons are dated evidence, not evergreen claims.** State
  the review date, exact version/tier/platform and whether evidence is official
  documentation, public metadata or our own reproducible test. Do not
  generalize one tested configuration, use unsupported superlatives, or turn a
  historical price into a current claim. Link the central scope/disclaimer in
  `docs/COMPARISON.md`, acknowledge genuine competitor strengths, and recheck
  changeable facts before publishing.
- **Public vs private records.** Plans, TODOs, changelogs and commit messages
  in this repo are public and permanent. Sort every fact before writing it:
  - *Personal data* (customer names, emails, addresses, tax IDs, card or bank
    details, the maintainer's identity checks) — never here.
  - *Business-confidential* (per-sale amounts, payouts, customer counts and
    purchase dates, Stripe object IDs such as `cs_live_`/`pi_`/`gcus_`,
    account review or fraud details, support-case narratives) — private by
    default: git-ignored `docs/internal/` (backed up daily) or private memory.
  - *Engineering facts* (a code path was verified by a real case, a
    configuration gap needs a decision) — public, written abstractly: what
    happened and what must be decided, not who, when or how much.

  In a public doc, leave one sentence plus a pointer to the private record.
  With few customers, a date plus country plus "company buyer" identifies
  someone even without a name. The pre-commit hook catches some identifiers
  and Stripe IDs, not judgment calls.

## 🟢 Patent gate — CLEARED 2026-06-17 (v0.5 Pro mechanisms now releasable)

A subset of v0.5 Pro mechanisms was held back under an active patent application
(申请号 202610712171X, priority date 2026-05-22). The gate condition — *patent
formality correction resolved and application status clean* — **was met on
2026-06-17** when CNIPA issued the 初步审查合格通知书 (preliminary examination
passed). Priority is secured, so public disclosure of these mechanisms no longer
risks the application.

These mechanisms now ship to the public repo via a **controlled Phase 5 merge**
(deliberate, one-time public disclosure) — see `docs/V0.5_RELEASE_PLAN.md`. Until
that merge lands, still don't leak unreleased mechanism detail in incidental
commits. The permanent rules remain: `pyobfus-legal/` never enters git (PII), and
Pro/Core source stays separated. See `docs/CURRENT_PLAN_ZH.md` for current
planning state and the archived `docs/POST_V0.4_TODO.md` § P1 for historical
patent/release context.

## Where to look next

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

- **Architecture / repository ownership**: [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md).
- **Community / Pro product boundary**: [`docs/EDITION_BOUNDARY_POLICY.md`](docs/EDITION_BOUNDARY_POLICY.md).
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
- **Current plan / daily source of truth**: [`docs/CURRENT_PLAN_ZH.md`](docs/CURRENT_PLAN_ZH.md).
- **What to pick up next**: [`docs/TODO.md`](docs/TODO.md), ordered, with acceptance criteria.
- **Historical detail**: [`docs/POST_V0.4_TODO.md`](docs/POST_V0.4_TODO.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md) are archived context, not the primary cold-start entry.
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **Security policy**: [`SECURITY.md`](SECURITY.md).

## Edition-boundary rules

- Never paywall correctness, security fixes, compatibility, or the basic local
  ability to inspect, verify, and debug output.
- Put features in Pro when their primary value is stronger protection, broader
  protected assets, runtime/distribution control, buyer accountability, or a
  managed organization service.
- Do not remove an existing Community capability solely to increase conversion.
- For a mixed feature, prefer a Community local primitive plus a Pro managed or
  organizational layer.
- Every new capability or tier change must apply
  `docs/EDITION_BOUNDARY_POLICY.md`, record the user/buyer/problem/evidence in
  the PR, and update the edition-facing docs, config/help, tests, and changelog.
