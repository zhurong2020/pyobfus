# Feature Expansion Research — 2026-09-02

Status: research complete; no feature implementation authorized by this document.

This review refreshes the 2026-08-26 feature study after Core 0.5.18--0.5.20
and MCP 0.3.9--0.3.10 shipped. It covers competitors, public user-demand
signals, Python/tooling changes, and AI-agent product direction. Historical
snapshots are not treated as current facts without a new primary-source check.

## Executive decision

The highest-value next increment is **CI/review interoperability for the
existing preflight engine**, not another obfuscation transform:

1. **P1 — SARIF 2.1.0 output for `pyobfus --check`.** Add an opt-in output
   mode that maps existing compatibility, dependency and source-risk findings
   into stable rules/results without changing JSON or exit-code behavior.
2. **P1 — read-only agent-review skill/template.** Package a separate
   `pyobfus-preflight-review` skill for `.github/skills/` and generic skill
   consumers. It may run `--check --json`/SARIF and inspect a dry-run plan, but
   must not obfuscate or write delivery output during code review.
3. **P1 small — Python 3.14 remote-debugging advisory.** Detect/recommend the
   interpreter-startup controls `-X disable_remote_debug` or
   `PYTHON_DISABLE_REMOTE_DEBUG=1` for protected deployments that request
   anti-debug hardening. Do not claim an injected runtime check can disable a
   facility that must be controlled at interpreter startup.
4. **P2 — MCP conformance evidence.** Run the official conformance suite
   against the stdio server and record the supported protocol baseline. Do not
   add Tasks, elicitation, OAuth or Server Cards merely because they exist.
5. **Hold — import/runtime verification expansion, delivery archives, hosted
   MCP and new transforms.** Existing `protect_project` already byte-compiles
   and import-smoke-tests in isolated subprocesses; further expansion needs a
   concrete failure or repeated user request.

## Evidence reviewed

### Direct pyobfus feedback

As of 2026-09-02 the repository still has 6 stars, 2 forks, zero open issues or
PRs, six Discussions and no new external comment. The latest traffic/download
review remains release-spike dominated. One paying customer reported that use
was going well, but the only concrete request was company invoicing. There is
still no direct request for mapping encryption, a delivery archive, a hosted
server, team-license administration, or another transform.

This absence is not proof that no demand exists. It means large product bets
remain gated, while low-cost integrations that expose already-working analysis
to more workflows are preferable.

### Competitors and adjacent tools

- **PyArmor remains 9.2.6**, released 2026-07-23; the prior 08-31 scan's 9.2.7
  statement was incorrect. Its public 9.3 plan is still developing and names
  RFT performance/refactoring and `build --pack`, not an AI-debug or structured
  review surface. Open issues continue to show the cost of opaque transforms:
  RFT crashes, stochastic `frame.f_code` crashes, slow RFT, group-device
  registration failure and requests for complete examples.
- **Nuitka 4.2** shipped 2026-08-24 with official Python 3.14 support,
  experimental 3.15 support, Windows/Linux installer generation, richer report
  totals, and explicit agent guidance/verification matrices. This strengthens
  the case for composing pyobfus with packaging tools and publishing verifiable
  reports; it does not justify copying a compiler or installer builder.
- The newer competitors recorded on 08-31 remain below pyobfus on
  framework-aware transforms, reverse mapping and agent integration. No new
  evidence changes the decision against VM/native/loader competition.

Primary sources:

- PyArmor PyPI and release plan:
  <https://pypi.org/project/pyarmor/>,
  <https://github.com/dashingsoft/pyarmor/blob/master/docs/ReleasePlan.md>
- PyArmor public issues: <https://github.com/dashingsoft/pyarmor/issues>
- Nuitka 4.2 release:
  <https://nuitka.net/posts/nuitka-release-42.html>

### AI-agent product direction

The market is moving from chat commands to long-running, reviewable agent
workflows:

- GitHub Copilot code review made **Agent Skills and read-only MCP generally
  available**. Skills live under `.github/skills/<name>/SKILL.md`; MCP calls in
  review are read-only and attributed in comments. This is a direct distribution
  path for pyobfus preflight, but not for the mutating `protect_project` tool.
- Copilot/VS Code and JetBrains now emphasize custom agents, subagents, hooks,
  remote sessions, resumability, sandboxed MCP and explicit tool-state handling.
- OpenAI reports agent usage shifting toward delegated tasks lasting hours,
  increasing the value of deterministic plans, verification evidence and
  machine-readable review findings over one-shot prose hints.
- The MCP 2026-07-28 core became stateless and added discovery/caching and
  conformance work. The new roadmap prioritizes agent messaging, HTTP transport,
  identity/security and improved primitives. These primarily benefit hosted
  HTTP servers; tier-1 SDKs preserve compatibility for existing stdio servers.

Primary sources:

- Copilot code review Skills + MCP:
  <https://github.blog/changelog/2026-07-29-copilot-code-review-agent-skills-and-mcp-now-generally-available/>
- Copilot JetBrains harness/MCP:
  <https://github.blog/changelog/2026-08-24-copilot-harness-generally-available-in-copilot-for-jetbrains/>
- MCP roadmap:
  <https://blog.modelcontextprotocol.io/posts/mcp-roadmap/>
- OpenAI long-horizon agent adoption:
  <https://openai.com/index/how-agents-are-transforming-work/>

### Standards and Python runtime changes

- GitHub accepts third-party **SARIF 2.1.0** and renders findings in code
  scanning/PR workflows. Public repositories can use code scanning; private
  repositories require the applicable GitHub Code Security entitlement.
- Python 3.14's PEP 768 remote-debugging attachment can schedule code in another
  process. Python documents three startup-time controls: environment variable
  `PYTHON_DISABLE_REMOTE_DEBUG`, `-X disable_remote_debug`, or building CPython
  with `--without-remote-debug`. pyobfus's current `sys.gettrace`, TracerPid,
  `IsDebuggerPresent` and timing heuristics do not disable this facility.

Primary sources:

- GitHub SARIF integration:
  <https://docs.github.com/en/code-security/how-tos/scan-code-for-vulnerabilities/integrate-with-existing-tools/uploading-a-sarif-file-to-github>
- Python 3.14 command-line controls:
  <https://docs.python.org/3.14/using/cmdline.html#envvar-PYTHON_DISABLE_REMOTE_DEBUG>
- Python remote-debugging protocol:
  <https://docs.python.org/3.14/howto/remote_debugging.html>

## Candidate analysis

### 1. `--check` SARIF output — GO / P1

Why now:

- the analysis engine and stable JSON contract already exist;
- SARIF makes findings visible in PR/code-scanning surfaces without creating a
  new scanner product;
- it serves both humans and agents and gives `dependency_advisory` a real CI
  validation channel without splitting it into another package.

Recommended MVP:

- opt-in `--format sarif` or `--sarif PATH`; keep existing default text/JSON;
- SARIF 2.1.0, one stable rule ID per existing category/subcategory;
- repository-relative artifact locations only;
- deterministic `partialFingerprints` derived from rule + relative path + safe
  structural location, so alerts do not churn across runs;
- map severities conservatively; preserve pyobfus's existing exit semantics;
- never include source literals, secrets, absolute home paths, license data,
  mappings or obfuscated output in SARIF messages;
- ship a GitHub Actions recipe, but keep upload/auth outside pyobfus.

Exit criteria: schema validation, GitHub upload smoke test in a disposable/public
test repository or artifact-only CI, stable fingerprints, and JSON byte-shape
regression tests.

### 2. Read-only preflight review Skill — GO / P1 docs/distribution

The current `pyobfus-protect` Skill correctly prefers the mutating
`protect_project` pipeline. Code review requires a different trust boundary.

Create a small template skill that:

- runs `pyobfus --check PATH --json` or consumes SARIF;
- optionally reads `--dry-run --json` plan output generated in a disposable
  location, without applying a build;
- reports high-risk reflection/config mismatches and dependency advisories;
- never starts a Pro trial, changes config, obfuscates, uploads mappings or
  executes arbitrary verification commands;
- links findings to the existing cookbook and recommends `protect_project`
  only as a post-review next step requiring normal user approval.

This should be portable, with `.github/skills/` as one documented install
target rather than a GitHub-only implementation.

### 3. Python 3.14 remote-debug policy — GO / P1 small

Add an advisory when target Python includes 3.14+ and anti-debug/protected
deployment intent is present. The output should explain that pyobfus heuristics
detect some attached debuggers but do not switch off PEP 768.

Prefer a documentation + `compatibility_advisory` increment. A generated
launcher flag or environment policy may be considered later, but silently
changing deployment environment is out of scope. Keep this opt-in and avoid
claiming remote debugging is universally exploitable: attachment normally
requires OS privileges.

### 4. MCP 2026 conformance — GO / P2 evidence

Run conformance tests and publish the protocol/version result. Add CI only if
the suite is stable and runtime cost is reasonable. The server is local stdio,
so do not implement HTTP authorization, Server Cards, Tasks or elicitation
without a concrete hosted-server use case. Cacheable list results and stateless
HTTP changes are not a reason to churn the eight-tool surface.

### 5. Verification/import expansion — HOLD

The 08-26 study proposed syntax-only verification because import executes code.
Since then, the MCP `protect_project` implementation has been confirmed to
already run compile and top-level import checks in isolated subprocesses, with
inconclusive classification and optional gated `verify_cmd`. The gap is CLI/MCP
surface consistency, not an absent verification engine.

Do not add another verifier until one of these signals appears:

- a real package that passes syntax but breaks import/runtime after obfuscation;
- repeated CLI-only demand for the MCP verification behavior;
- a safe sandbox profile with a precise side-effect threat model.

### 6. Packaging/installers and delivery archives — HOLD

Nuitka 4.2 makes installers easier, but pyobfus should remain the source
protection stage composed before PyInstaller/Nuitka/Cython. Improve recipes and
evidence when a real combination fails. Do not build installer generation or
put private mappings into an automatic archive.

## Recommended implementation sequence

1. Design `--check` SARIF as an additive contract; validate privacy and stable
   fingerprints before coding.
2. Build the read-only review Skill/template on the existing JSON contract; it
   can ship independently, then prefer SARIF when available.
3. Add the Python 3.14 remote-debug advisory and deployment recipe.
4. Run MCP conformance as a research/CI spike.
5. Reassess only after the 09-01 release download window and the planned user
   Discussion produce fresh demand evidence.

Formal release remains separately gated by the maintainer. This document does
not authorize a version bump, tag, Registry update or Marketplace upload.
