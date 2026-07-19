# pyobfus Resume Plan — 2026-07-19

> **STATUS 2026-07-19 (end of session): P0.1, P0.2, P1.1, P1.2 and P1.3 are
> DONE and 0.5.4 is published.** What actually happened, including what the
> plan did not anticipate:
>
> - **P0.1 — done.** Both reporters thanked publicly; #20 and #21 answered with
>   the reasoning that a client-side verifier in an open-source package cannot
>   be made tamper-proof, so signing the state file would close #20 and leave
>   #21 untouched. Chose the honest option: keep the trial as a convenience
>   control and say so. Over-claims removed from `trial.py`, `SECURITY.md`,
>   `README.md` and the docs site; trial bypass declared out of scope; four
>   tests added that pin the limitation by asserting tampering *succeeds*.
>   Issues relabeled off `bug` to `documentation` + `trial-boundary`.
>   **Deviation from plan:** no private security advisory was opened, and the
>   public threads were not locked. Neither report is a vulnerability — no user
>   is harmed — and locking a working, accurate bypass guide would have been
>   both misleading and a Streisand invitation. Handled fully in public.
> - **P0.2 — done, and it found more than expected.** `pyobfus_mcp/tests/`
>   (73 tests) had never run in CI. `integration_tests/` was worse than "an
>   empty directory": `.gitignore` excluded it wholesale, so the root
>   documented in `AGENTS.md` had never existed in any clone. Both are real
>   jobs now. Also removed a stale `--ignore=tests/test_pro_features.py` from
>   pytest `addopts`, and extended black/ruff to `pyobfus_pro/` and the MCP
>   package. mypy stays non-blocking; the 8-error baseline is tracked in #22.
> - **P1.1 — done.** PR #19 reviewed against the checklist and verified
>   empirically (build-device decrypt, wrong-device `VaultError`,
>   `--bind-device-id` binding to the supplied id rather than the builder,
>   distinct per-vault salts, no-vault no-op). Squash-merged.
> - **P1.2 — done.** 0.5.4 tagged and published via OIDC with attestations.
>   `pyobfus-mcp` deliberately not bumped, so no Glama re-pin.
> - **Unplanned find:** there is no `pyobfus build` subcommand. 0.5.1–0.5.3
>   release notes documented the headline Pro flags with that syntax, so
>   anyone copying them hit `Path 'build' does not exist`. Corrected.
>
> **Next up, in order:** P1.4 launch wave · #22 mypy gate · P2.1 benchmark
> evidence. The P0 queue is clear, so P2 work is no longer blocked.

**Purpose**: current, executable handoff for the next maintainer/agent session.
Start here, then use [`POST_V0.4_TODO.md`](POST_V0.4_TODO.md) for the longer
historical backlog and [`ROADMAP.md`](ROADMAP.md) for strategic candidates.

**Security note**: this is a public-repository document. It records impact,
decisions, and remediation work without reproducing copy-paste trial-bypass
instructions. Keep detailed reproduction evidence in a private GitHub Security
Advisory.

## 30-second resume

- Branch: `main`, clean and synchronized with `origin/main` at `e8c2564` when
  this handoff was written.
- Published: `pyobfus 0.5.3`; `pyobfus-mcp 0.3.1`.
- Latest `main` CI, CodeQL, and Pages runs are green. Core tests cover Python
  3.9–3.14 on Ubuntu, Windows, and macOS.
- PyPI Trusted Publishing and PEP 740 provenance are confirmed for both current
  packages. The old "re-check provenance" TODO is complete.
- Open security/product reports:
  [#20](https://github.com/zhurong2020/pyobfus/issues/20) and
  [#21](https://github.com/zhurong2020/pyobfus/issues/21), both concerning
  client-side trial bypasses. Both were open with no maintainer response at the
  time of this snapshot.
- Open feature PR:
  [#19](https://github.com/zhurong2020/pyobfus/pull/19), which device-binds
  String Vault keys for the planned 0.5.4 release. It is mergeable and CI-green,
  but has no human review yet.
- Adoption remains the project-level constraint (1 GitHub star / 2 forks at
  snapshot time). Do not start another large feature before the P0/P1 queue
  below is cleared.
- JOSS desk-rejected the software paper for insufficient demonstrated external
  reuse/open collaboration, not for software quality. Do not re-submit until
  those facts materially change.

## Ordered execution queue

### P0.1 — Contain and triage the public trial-bypass reports

**Why first**: the reports affect the commercial boundary, contain public bypass
claims, and have passed the 48-hour acknowledgement target in `SECURITY.md`.

The two reports are related but not identical:

- **#20 — mutable local trial state**: the trial expiry is read from an unsigned
  local record. A user who controls the machine can alter that record.
- **#21 — mutable installed client code**: because the trial implementation is
  shipped as readable Python and enforcement is local, a user can patch the
  duration or verification path itself.

Important limitation: signing a local data file can prevent casual data edits,
but it cannot make a client-side, source-distributed verifier unpatchable. Do
not describe any local-only fix as complete piracy prevention.

#### First-session actions

- [ ] Preserve the current issue bodies and timestamps as private evidence.
- [ ] Acknowledge both reporters publicly and ask that further reproduction
      details move to a private GitHub Security Advisory.
- [ ] Open/link one private advisory that treats #20 and #21 as two attack paths
      under one trust-boundary decision.
- [ ] Decide whether the trial is:
  - a low-friction convenience control, with explicit documentation that it is
    not a strong security boundary; or
  - a commercial enforcement boundary requiring a server-issued entitlement
    and potentially a different Pro distribution model.
- [ ] After evidence is preserved, close or lock public exploit-instruction
      threads according to the repository security policy.
- [ ] Update the issue labels/status so they are not left as generic unattended
      `bug` reports.

#### Recommended near-term design

Use an anonymously requested, short-lived entitlement signed by a server-side
private key and verified locally with a bundled public key. This blocks simple
expiry-file editing without requiring continuous phone-home. Be explicit that a
user who patches the distributed verifier can still bypass it. If stronger
enforcement is a business requirement, design a separately delivered/hosted Pro
boundary rather than adding more secrets to public client code.

#### Definition of done

- [ ] Public acknowledgement posted; private advisory exists.
- [ ] Threat model and product decision are written down.
- [ ] Misleading "one-time/device-bound" claims are corrected or backed by the
      chosen implementation.
- [ ] Tampered-state tests exist for the selected design.
- [ ] A security release or explicit "known limitation" resolution is planned.

### P0.2 — Make CI enforce all three documented test roots

**Current gap**: `.github/workflows/ci.yml` is green, but it does not run the
complete MCP or integration pytest roots required by `AGENTS.md`. The existing
"Integration Tests" job is a CLI smoke test, and the MCP job only instantiates
the server. `mypy` is also non-blocking via `continue-on-error: true`.

- [ ] Add a dedicated MCP test job running:

  ```bash
  pytest pyobfus_mcp/tests/
  ```

- [ ] Add a dedicated end-to-end test job running:

  ```bash
  pytest integration_tests/
  ```

- [ ] Keep the existing CLI smoke test, but rename it accurately or make it a
      separate job.
- [ ] Record the current mypy baseline (PR #19 reports eight existing errors),
      fix or explicitly track them, then remove `continue-on-error: true`.
- [ ] Decide whether formatting/lint should also cover `pyobfus_pro/` and the MCP
      package; add coverage without mixing unrelated baseline cleanup into PR
      #19.

#### Definition of done

- [ ] Core, MCP, and integration suites are separate required CI jobs.
- [ ] A failure in any of the three roots makes CI fail.
- [ ] The mypy gate is blocking, or a dated issue documents the remaining
      non-blocking baseline and owner.

### P1.1 — Human-review and merge PR #19

PR #19 extends `--bind-device` from opacity L3 keys to each String Vault key.
Every vault receives an independent salt; the raw `_VAULT_KEY_<name>` literal is
replaced by a runtime device-derived key. The build device succeeds; another
device should fail AES-GCM authentication.

Snapshot: 1 commit, 6 changed files, +333/-8, 8 new tests; reported result is
1041 passed / 1 skipped / 90% coverage. The PR is mergeable and CI-green but has
no review comments or approvals.

#### Review checklist

- [ ] Confirm no raw vault key remains in generated output.
- [ ] Confirm every vault receives a distinct salt and derived key.
- [ ] Confirm build-device success and wrong-device failure.
- [ ] Confirm `--bind-device-id` behaves consistently with build-machine binding.
- [ ] Confirm `--vault --bind-device` is a no-op, not a crash, when no vault is
      declared.
- [ ] Confirm imports are injected after any `from __future__` imports and are
      not duplicated.
- [ ] Exercise combinations with `--selective-opacity` / `--opacity-config`.
- [ ] Run the three test roots separately, as required by `AGENTS.md`:

  ```bash
  pytest tests/
  pytest pyobfus_mcp/tests/
  pytest integration_tests/
  ```

- [ ] Run formatting, lint, and type checks over the touched packages.
- [ ] Merge only after P0.2 makes the missing suites visible in CI or after the
      equivalent full results are recorded on the PR.

#### Definition of done

- [ ] Human review completed with no unresolved comments.
- [ ] All three test roots pass.
- [ ] PR #19 is merged to `main`; post-merge CI is green.

### P1.2 — Ship pyobfus 0.5.4

Do this after P0.1 has a chosen disposition and PR #19 is merged.

- [ ] Decide whether the trial-boundary change ships in 0.5.4 or a separate
      security patch; avoid silently combining incompatible product decisions.
- [ ] Bump `pyproject.toml` from 0.5.3 to 0.5.4.
- [ ] Finalize the `[Unreleased]` section in `CHANGELOG.md`.
- [ ] Update README/llms/docs headline facts and remove the old statement that
      Vault keys remain unbound.
- [ ] Run all required tests and quality checks.
- [ ] Build wheel + sdist and run artifact checks.
- [ ] Tag and publish through the OIDC `release.yml` workflow.
- [ ] Verify PyPI provenance for both artifacts.
- [ ] Do not bump `pyobfus-mcp` solely for this change: PR #19 does not change
      its tool surface. Consequently, no Glama Build-steps pin change is needed
      unless an MCP release is made for another reason.

### P1.3 — Repair the current-source-of-truth documents

The implementation/docs are ahead of the open checkboxes in
`POST_V0.4_TODO.md` and `DOC_SYNC_AUDIT_2026-07-15.md`.

- [ ] Update the Forward TODO date and snapshot in `POST_V0.4_TODO.md`.
- [ ] Mark PEP 740 verification complete.
- [ ] Mark DOI propagation complete: README Citation section, `CITATION.cff`,
      both package project URLs, RTD citation page, and CHANGELOG are present.
- [ ] Replace the "Vault binding not implemented" item with the live PR/merge
      state.
- [ ] Mark the July 15 doc-sync audit completed or clearly historical.
- [ ] Update `SECURITY.md` supported versions from pyobfus 0.4.x to the current
      0.5.x line.
- [ ] Decide whether `pyobfus-mcp` remains Beta or moves to
      Production/Stable on its next release.
- [ ] Treat old v0.4/version counts in historical release records as history;
      do not mechanically rewrite them.

### P1.4 — Execute the launch wave

After the public trial issue is contained and 0.5.4 is ready, distribution is
the highest-leverage work. Do not hold the launch for another large feature.

- [ ] Refresh the existing `_drafts/` posts with 0.5.4 facts and the current DOI.
- [ ] Re-check all anecdotes and claims against
      `docs/V0.4_EXECUTION_LOG.md`; do not reintroduce previously removed
      fabricated narrative texture.
- [ ] Publish in this order: dev.to → Show HN → Reddit → Chinese channels.
- [ ] Publish the GitHub Discussions priority poll.
- [ ] Add answer-first/AEO framing and concrete, reproducible examples.
- [ ] Capture 24-hour and 7-day outcomes: stars, external issues, installs,
      trial starts, and sales—not download totals alone.

### P2.1 — Turn the P2-18 LLM-resistance harness into real evidence

The benchmark harness is on `main`, but its documented state is still "design +
first-cut harness". Do not advertise a resistance percentage until real runs are
versioned and reproducible.

- [ ] Run the control condition and confirm it scores near 100%; otherwise fix
      the harness/prompt before measuring obfuscation.
- [ ] Run the planned attacker-model/condition matrix.
- [ ] Freeze prompts, model identifiers, tool versions, raw results, and hashes.
- [ ] Publish a reproducible report with limitations and confidence intervals.
- [ ] Use results to decide whether a `--llm-resistant` preset is justified.

### P2.2 — Choose later features from external signal

Do not start all candidates. Recommended selection order if launch feedback does
not point elsewhere:

1. `--preset ml` — low implementation cost; reuses presets and Vault.
2. Signed obfuscation provenance manifest — enterprise/supply-chain wedge.
3. MCP tool-description integrity manifest.
4. PyInstaller cookbook, then `scan_secrets` if users request it.

## Explicitly defer

- VSCode extension until there is adoption/channel evidence.
- Import obfuscation, anti-debug expansion, embed-data, and `--output-pyc` until
  user or sales demand is visible.
- JOSS re-submission until the repository has demonstrated third-party reuse,
  sustained open issue/PR collaboration, and external contributors. Keep the
  Zenodo DOI as the current citation path.
- New patent-sensitive mechanism work outside the controlled Pro/Core boundary.

## First 60 minutes of the next session

1. Re-read this file, `SECURITY.md`, issues #20/#21, and PR #19.
2. Check whether the issues or PR changed since this snapshot.
3. Acknowledge/contain #20 and #21; open the private advisory.
4. Create the CI-hardening branch and add the two missing pytest jobs.
5. Once CI coverage is real, perform the PR #19 human review.

Do not begin P2 feature work while any P0 item above remains open.

