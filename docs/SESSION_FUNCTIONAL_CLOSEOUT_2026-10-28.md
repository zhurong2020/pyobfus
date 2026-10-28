# 2026-10-28 functional session closeout: P0 → P2 and Python 3.15t

Cold start: this record → [current plan](CURRENT_PLAN_ZH.md) →
[ordered TODO](TODO.md) → [support matrix](SUPPORT_MATRIX.md). The earlier
[10-28 content and operations closeout](SESSION_CLOSEOUT_2026-10-28.md)
remains a dated snapshot of the DEV article, cover, dependency alerts and
backup. The public versions remain Core **0.10.0**, MCP **0.3.16** and runtime
**0.1.1**; this session did not publish a package or tag.

## Completed in order

| Stage | Outcome and evidence | Boundary |
|---|---|---|
| P0 correctness | [PR #154](https://github.com/zhurong2020/pyobfus/pull/154) merged as `0852784`: package-root module identity, clearer unproved-attribute warnings and opt-in `--preserve-unproved-module-attributes`. Native 3.15 `json` and `unittest` cases ran with the option. [Details](P0_MODULE_ATTRIBUTE_COMPAT_2026-10-28.md). | Default output can still be unusable at unproved dynamic accesses; the option preserves recognized names and may reduce obfuscation. Unreleased. |
| P1 delivery and L3 usability | Public 0.10.0 wheel tested with PyInstaller onedir/onefile on Linux and Windows, Nuitka onefile on Linux, and a runtime-only offline L3 application with correct/missing/wrong keys and mapped exceptions. [PR #155](https://github.com/zhurong2020/pyobfus/pull/155) recorded the bounded results. [Details](P1_PACKAGING_VALIDATION_2026-10-28.md). | No new packaging code was justified. These small combinations do not establish all platforms, plugins, Python versions or frozen L3 support. |
| P2 delivery diagnostics | [PR #156](https://github.com/zhurong2020/pyobfus/pull/156) merged as `5b26085`: bounded `.pyc` source/body comparison, explicit `unknown` warning, and PE/ELF/Mach-O outer executable warnings. Core 4,652 passed/55 skipped; MCP 153; integration 352 passed/10 skipped; runtime 24; `scripts/check.sh` passed. PR checks: 44 success/2 skipped. [Details](P2_DELIVERY_DIAGNOSTICS_2026-10-28.md). | Frozen payloads are not unpacked; `warn` retains exit code 0. No confidentiality guarantee. Unreleased. |
| P2 gates | [PR #157](https://github.com/zhurong2020/pyobfus/pull/157) recorded the real-case requirements for methods/nested L3, resource/Vault key providers, parameter renaming and complex cycles. The P1 application did not expose a blocker for any of them. [Gate](P2_CONDITIONAL_COVERAGE_GATE_2026-10-28.md). | Do not expand those APIs from synthetic coverage alone. |
| 3.15 free threading | An isolated Linux Python 3.15.2 no-GIL build was obtained on retry after two temporarily slow download attempts. `Py_GIL_DISABLED=1`, runtime GIL off; Community build/run and three-frame unmap worked, five `.pyc` matched recorded output, targeted 44 + 68 tests passed, and two threads completed 400 key-provider calls. [PR #158](https://github.com/zhurong2020/pyobfus/pull/158) recorded the result. [Details](PYTHON315_FREETHREADING_VALIDATION_2026-10-28.md). | Cross-file L3 deliberately rejects free-threaded builds; no encrypted artifact was validated. Not a clean public-wheel or other-OS validation. |
| Next Core release preparation | [PR #159](https://github.com/zhurong2020/pyobfus/pull/159) added the missing P2 `[Unreleased]` changelog entry and a [release-readiness record](CORE_NEXT_RELEASE_READINESS_2026-10-28.md). Required CI result and CodeQL passed; 41 checks succeeded/1 skipped. | 0.11.0 is a proposal. No version bump, release approval, tag, PyPI upload or Zenodo archive occurred. |

## State at closeout

- Public `pyobfus` `main` is synchronized with `origin/main` at `e1a52ff`;
  no open PR or uncommitted change was found before this closeout edit. This
  closeout itself will be merged and the resulting head recorded after CI.
- No private GitHub Actions run or `workspace-meta` push was made. That
  private `main` has four previously queued local documentation commits; wait
  until the account billing limit clears after 2026-11-01, then inspect
  duplicate triggers, timeout and cost before a necessary Guard run and push.
- `pyobfus-action` is on clean, unpushed branch
  `docs/core-0.10.0-runtime-guide` (`5c6fa1c`); its repository-specific push
  authorization has not been supplied. The unrelated hospital worktree on
  `feat/hospital-edition-v2.6.0` still has seven pre-existing modifications;
  this session did not touch them.
- The 3.15t interpreter, compatible wheels, evidence scripts and P1 fixtures
  remain under `/tmp`. They are disposable local validation artifacts, not
  tracked deliverables or proof of a fresh public-wheel installation.

## Next ordered work

1. If a real minimized case arrives, take the first matching P2 conditional
   item through its compatibility gate; do not batch all four. Cross-file L3
   on 3.15t requires a separate encrypted-artifact design and validation.
2. At a separately approved Core release gate, confirm scope/version
   (0.11.0 proposed), update release metadata together, build and verify
   artifacts, then publish and check PyPI provenance, GitHub and Zenodo.
3. After 2026-11-01, review `workspace-meta` private CI cost before queued
   synchronization. Keep the DEV article's 24-hour and one-week observations
   on their original dates; do not write future metrics as already observed.
