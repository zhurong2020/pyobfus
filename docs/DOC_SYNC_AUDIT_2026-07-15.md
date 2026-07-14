# Doc-Sync Audit + Resume Plan — 2026-07-15

**Purpose**: handoff so a fresh session (scheduled 04:00) can finish without re-deriving.
Context: pyobfus **0.5.3** + pyobfus-mcp 0.3.1 are live. This session committed the P2-18
benchmark as **`d553668` (local only — NOT pushed to origin/main)** and ran a repo-wide
doc-sync audit. Nothing below is fixed yet.

Current facts to sync TO: **1033 tests**, **90% coverage**, **Python 3.9–3.14 × 3 OS**,
main package **Development Status :: 5 - Production/Stable**, latest version **0.5.3**.
Public `pyobfus build` fusion flags (0.5.1+): `--selective-opacity --seal-code --vault
--scrub-traceback --fingerprint --expire-hard` + (0.5.3) `--period --opacity-config
--bind-device[-id]`. Six Pro mechanisms: Selective Opacity, Seal-Code, String Vault,
Scrub-Traceback, Fingerprint, Expire-Hard.

## Part 1 — FIX these (user-facing / factually wrong or missing features)

| File:line | Issue | Fix |
|---|---|---|
| `README.md:545` | "1024 tests" | → "1033 tests" |
| `llms-full.txt:131` | `# pyobfus v0.4.0` (yaml header example) | → `# pyobfus v0.5.3` |
| `llms-full.txt:274` | "v0.4 introduces AI-native features…" | reword to current; AI-native is baseline now, note v0.5 `pyobfus build` Pro fusion |
| `llms.txt` + `docs/llms.txt` | **identical twin copies** (NOT symlinked — edit BOTH, keep byte-identical). No mention of `pyobfus build` / 6 Pro mechanisms | add a "Pro build-fusion mechanisms" section listing the 6 flags + note they compose via `pyobfus build` |
| `docs/index.md` (RTD landing) | Pro-Edition feature list (~line 40-55) predates v0.5; lists CFF/DCI/AES/anti-debug/license but not the 6 named v0.5 mechanisms | add the 6 v0.5 Pro mechanisms to the 💎 Professional Edition list |
| `docs/PROJECT_STRUCTURE.md:53` | "366 tests, 69% coverage" | → "1033 tests, 90% coverage" |
| `docs/ROADMAP.md:22` | "1016+ tests with 89% coverage" | → "1033 tests, 90% coverage" |
| `docs/DISTRIBUTION_CHANNELS.md:18` | "Current version: **0.4.0** (2026-04-22)" | → 0.5.3, or mark "(as of 2026-04-22)" snapshot |
| `docs/AI_INTEGRATION_STRATEGY.md:59` | "561 tests / Alpha→Beta" (low prio; historical planned-action table) | → 1033 tests / Production-Stable, or leave as history |

**Verify (read first, may already be fine):** `docs/COMPARISON.md` (does it mention Pro tier
/ current mechanisms?), `skills/pyobfus-protect/SKILL.md` (community-scoped; may intentionally
omit Pro), `pyobfus_mcp/README.md` (should mention 8 tools incl. `protect_project`; check tool
list currency).

**Decision needed (don't silently change):** `pyobfus_mcp/pyproject.toml:22`
`Development Status :: 4 - Beta` — main pkg is already `5 - Production/Stable`. Bump mcp to match?
Only takes effect on next mcp release. Recommend yes (mcp 0.3.1 is stable, 8 tools, in registries).

## Part 2 — LEAVE (historical records; hygiene rule = don't rewrite history)

`CHANGELOG.md` (655/561/410 test counts are correct per-version), `docs/V0.4_EXECUTION_LOG.md`,
`paper/paper.md` (frozen JOSS submission record), `CLAUDE.md` per-release cells (line 70 already
says 1033; line 23/25 are historical release notes), `docs/V0.5_RELEASE_PLAN.md`,
`docs/POST_V0.4_TODO.md` (the SoT itself — its stale-line callouts are the TODO, not bugs).

## Part 3 — Ordered task queue (after doc-sync)

0. **Doc-sync fixes above** — commit as one `docs:` commit, no version bump. This is also the
   Phase 5.6 checklist item, so it clears a standing release-process debt.
1. **Vault-key device binding (0.5.4 headline)** — extend `--bind-device` to rewrite each
   emitted `_VAULT_KEY_<name>` into a runtime device derivation (same technique as opacity's
   `_LAYER_KEY` rewrite in `62646b6` / `build_fusion._substitute_layer_key_binding`). Vault runs
   in the PRE-pass with PER-vault keys, so pass the device key into
   `_t_vault.transform_module(..., vault_keys=...)` at build AND post-substitute each
   `_VAULT_KEY_*`. Add device-match/mismatch runtime tests. Today only opacity L3 is
   device-locked; vault keys ship as baked literals (documented scope boundary).
2. **`--preset ml` (P2-19)** — new preset: protect inference-wrapper + route model-path/weight
   constants into vault. Preset mechanism already exists (`config.py:620`, no `ml` yet).
3. **Zenodo DOI propagation (repo side)** — README `## Citation` (APA+BibTeX), `[project.urls]`
   Citation in BOTH `pyproject.toml` files, RTD "How to cite" page, CHANGELOG note.
   Concept DOI `10.5281/zenodo.20846053`.
4. **PEP 740 provenance re-check** — fetch 0.5.3 / mcp-0.3.1 PyPI pages; if `provenance:false`
   despite `attestations:true`, debug `release.yml`.
5. **Signed obfuscation provenance manifest (P2-17)** — larger; design first.

## Notes for the resuming session
- `origin/main` is behind: local commit `d553668` (benchmark) is unpushed. Decide push timing.
- Feature work (task 1+) is more than a mechanical edit — if running unattended, prefer to open
  a branch + PR for human review rather than committing straight to main.
- Full context: `docs/POST_V0.4_TODO.md` top "Forward TODO" + memory `pypi_download_tracking.md`.
