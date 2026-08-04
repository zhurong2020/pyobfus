# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

**M0 for the upcoming VSCode extension (ROADMAP P2-2)**: `pyobfus-trial status`
and `pyobfus-license status` now support `--json`, returning
`get_trial_status()` / `get_license_status(masked=True)` as structured JSON
(same pattern as `pyobfus --check --json` / `pyobfus --unmap --json`), plus
`--verify` results and structured error envelopes for the license command.
Previously text-only (ANSI-colored `click.echo`), which meant any editor/IDE
integration would have had to scrape colored text — the VSCode extension's
status bar needs a real contract. Text-mode output is unchanged. 12 new
tests. Held for release per the project's release-spacing convention
(see `docs/ROADMAP.md`'s P2-2 entry / `CLAUDE.md` for the eligible date) —
not yet version-bumped or tagged.

## [0.5.11] - 2026-08-04

**Feature release.** Extends `--anti-debug` (P2-15, Pro) with three new
detection methods beyond the original `sys.gettrace()`-only check: TracerPid
(reads `/proc/self/status` — catches native debuggers like gdb/strace on
Linux, which `sys.gettrace()` can't see since it only observes the CPython
trace hook, not OS-level ptrace attachment), WinAPI `IsDebuggerPresent()`
via `ctypes` (Windows native debuggers), and a timing-skew check (times a
trivial tight loop — a debugger single-stepping or evaluating breakpoints
per line adds overhead orders of magnitude above normal execution; the
threshold is deliberately generous to avoid false-positive-killing a
legitimate customer process under CPU throttling or heavy load). Default
stays OFF, opt-in via `--anti-debug`, same as before. Heuristic, not a
security boundary — documented as such, matching this project's existing
license/trial mechanism disclosures. Also fixed a pre-existing README
overclaim ("sys.gettrace, sys.settrace" as two detection methods —
`sys.settrace` sets a trace function, it was never actually a detection
check the code performed). 6 new tests, each exercising the real injected
runtime logic via mocks (TracerPid nonzero/zero, IsDebuggerPresent
true/false, simulated timing slowdown), not just checking the generated
source text looks right. `pyobfus-mcp` unchanged, no Glama re-pin needed.

## [0.5.10] - 2026-08-04

**Feature release.** Adds `--embed-data <path>` (P2-14, Pro) — AES-256-GCM
encrypts a resource file at build time (same cipher construction as the
Runtime String Vault: 12-byte random nonce, 32-byte key, GCM tag) and
embeds it base85-encoded as a module constant, plus a generated
`get_embedded_data()` accessor that decrypts on call, not at import.
Closes the Nuitka Commercial "Protect Data Files" / PyArmor `--bind-data`
gap in pure Python. Not part of the patent-gated combination claims —
reuses the Runtime String Vault's AES-256-GCM primitive for an arbitrary
binary blob rather than a named string KV store. New module
`pyobfus_pro/runtime/embedded_data.py`, 11 new tests (9 unit + 2
build-fusion integration, one of which loads the obfuscated module and
calls the generated accessor to confirm it returns the exact original
file bytes). `pyobfus-mcp` released 0.3.4 the same day for an unrelated
change (P2-12 PII-shape detection, see `pyobfus_mcp/CHANGELOG.md`) — no
Glama Build-steps re-pin needed on the pyobfus side.

## [0.5.9] - 2026-08-04

**Feature release.** Adds `--requires-os` / `--requires-python-min` /
`--requires-arch` (P2-16, Pro) — a pure-Python generalization of PyArmor
BCC's platform-restriction mode. Each flag injects a module-top
`requires_runtime(...)` guard call (same POST-pass shape as
`--expire-hard`/`--period`) that raises `RuntimePolicyError` at import time
if the running OS, Python version, or CPU architecture don't satisfy the
build-time constraint. Not part of the patent-gated combination claims —
a standalone environment check, no cryptographic binding involved. New
module `pyobfus_pro/runtime_policy.py`, 15 new tests (13 unit + 2
build-fusion integration, one of which runs the injected check against the
real interpreter, not a mock). `pyobfus-mcp` is unchanged (no tool-surface
change), so no MCP Registry publish or Glama Build-steps re-pin is needed
for this release.

## [0.5.8] - 2026-08-04

**Content release, no code changes.** Adds a PyInstaller integration
cookbook (P2-13 from the roadmap) for teams that want a single-file
executable but don't need Nuitka Commercial's price or compile times:
obfuscate first, then bundle the obfuscated output with the free,
MIT-licensed PyInstaller. `examples/pyinstaller/` is a verified end-to-end
reproduction (not just described) — including confirming the original
identifier names never reach the compiled binary, and that `pyobfus
--unmap` still reverses a traceback captured from the bundled executable.
New RTD page `docs/PYINSTALLER_COOKBOOK.md`, cross-linked from
`docs/COMPARISON.md`'s Nuitka section and a new README FAQ entry.
`pyobfus-mcp` is unchanged (no tool-surface change), so no MCP Registry
publish or Glama Build-steps re-pin is needed for this release.

## [0.5.7] - 2026-08-02

**Feature + positioning release.** Adds Pro import obfuscation and the matching
comparison copy for the PyArmor-alternative story. `pyobfus-mcp` is unchanged at
0.3.2 (no MCP tool-surface change), so no MCP Registry publish or Glama
Build-steps re-pin is needed for this release.

### Added

- **`--import-obfuscation` (Pro, P2-4)** — rewrites top-level
  `import ...` and absolute `from ... import ...` statements into runtime
  `importlib` / `__import__` calls, then automatically enables AES string
  encryption so module and imported-symbol names do not remain as plaintext
  string literals in the generated output. Relative imports, `from __future__`
  imports, and star imports are deliberately left unchanged in this first pass.
- **P2-22 honest comparison content** — expands `docs/COMPARISON.md` with the
  pure-Python AST vs bytecode-encryption tradeoff, including why public
  static-unpack tooling means client-side bytecode protection should be treated
  as a stronger speed bump rather than irreversible cryptography. The README FAQ
  now points readers to that framing.

## [0.5.6] - 2026-08-02

**Bugfix release.** Closes issue #25, which turned out bigger than
originally filed — a one-line CLI bug was silently overriding preset and
config-file choices for three fields, including `preset_safe`'s docstring
preservation. `pyobfus-mcp` is unchanged at 0.3.1 (no tool-surface change),
so no Glama Build-steps re-pin is needed for this release.

### Fixed

- **`preserve_param_names`/`remove_docstrings`/`remove_comments` no longer
  silently clobber preset/config choices (issue #25).** `cli.py`'s
  "Override config with CLI options" block ran unconditionally after preset
  or config-file loading, so any preset field these three CLI options also
  control got reset to the CLI's own default the moment a user ran the
  normal, documented invocation (`--preset fastapi`, no extra flags) — not
  just for `--preset ml`/`--preset fastapi`'s `preserve_param_names=True`
  as originally filed, but also for `--preset safe` (and all six framework
  presets built on it)'s `remove_docstrings=False`, silently deleting
  docstrings despite `preset_safe`'s entire reason to exist being to keep
  them. `--preserve-param-names`, `--remove-docstrings/--keep-docstrings`,
  and `--remove-comments/--keep-comments` are now tri-state (`None` when
  the user passes neither flag), so the CLI only overrides a preset's or
  config file's choice when the user explicitly asks it to. Fixes the
  `--preset ml` caveat noted in 0.5.5 below — `preserve_param_names=True`
  now actually preserves parameter identifiers end-to-end for every preset
  that sets it.

## [0.5.5] - 2026-08-02

**Feature release.** Two new capabilities implemented by Codex CLI and
reviewed/finished by Claude Code, plus one honesty fix and one new bug report
surfaced along the way. `pyobfus-mcp` is unchanged at 0.3.1 (no tool-surface
change), so no Glama Build-steps re-pin is needed for this release.

### Added

- **`--preset ml`** — community-tier model-serving preset for inference
  wrappers. Preserves the framework-dispatched method names external code
  actually calls by exact name (`predict`/`predict_proba`/`fit`/`transform`/
  `forward`/`generate`/`encode` — sklearn, PyTorch's `nn.Module.__call__`,
  HuggingFace conventions), excludes model/checkpoint/weight artifact
  paths, and pairs with new `--check` guidance for unsafe pickle/
  `torch.load`/model loading plus Runtime String Vault routing hints for
  model-path literals. Sets `preserve_param_names=True` for consistency
  with every other framework preset, though that flag does not currently
  preserve parameter identifiers end-to-end for any preset (issue #25).
- **`--provenance-manifest PATH`** — writes a local JSON provenance manifest
  for obfuscation runs: obfuscated files, effective config hash, pyobfus
  version, mapping digest when `--save-mapping` is used, and a canonical
  SHA-256 integrity digest (self-consistency check, not a cryptographic
  signature — real signing via sigstore is future work). No new dependency
  or phone-home service is required.

## [0.5.4] - 2026-07-19

**Feature + honesty release.** Closes the last device-binding scope boundary
(String Vault keys), makes CI enforce the three test roots that `AGENTS.md`
documents, and corrects several places where the documentation promised more
than the implementation delivers. Published to PyPI via OIDC Trusted Publishing
with PEP 740 attestations. `pyobfus-mcp` is unchanged at 0.3.1 (no tool-surface
change), so no Glama Build-steps re-pin is needed for this release.

### Added

- **`--bind-device` now also device-locks String Vault keys (Pro).** Previously
  `--vault --bind-device` derived a device key but never used it for the vault:
  only the Selective-Opacity L3 `_LAYER_KEY` was bound, while each
  `_VAULT_KEY_<name>` shipped as a baked at-rest literal — so vault secrets
  decrypted on *any* machine. Now each vault is encrypted at build with its own
  device-derived key `bind_device_key(target_id, salt)` and the emitted literal
  is rewritten into a runtime
  `bind_device_key(current_machine_id(), _pyobfus_vault_salt_<name>)`
  re-derivation. The raw key never ships; a wrong device raises `VaultError` on
  first `.get()`. Per-vault salts keep vaults mutually independent.
  `--bind-device-id <id>` binds to the supplied customer machine instead of the
  build machine. No-op (not a crash) on a `--vault` module with no
  `vault_secrets({...})`. Implemented in the vault PRE-pass, since Core
  preserves the constant names and imported symbols through mangling.
  (`pyobfus_pro/build_fusion.py`, `transformers/vault.py::collect_vault_names`.)
- `tests/test_trial.py::TestTrialTrustBoundary` — four tests that pin the
  trial's documented limitation by asserting tampering *succeeds*, so a future
  change that adds signing fails loudly instead of silently contradicting the
  docs.

### Changed

- **The Pro trial is now documented as a convenience control, not a security
  boundary** (reported in [#20](https://github.com/zhurong2020/pyobfus/issues/20)
  and [#21](https://github.com/zhurong2020/pyobfus/issues/21) — thanks to
  @CoderWhoUsesPython and @zcveo5). Trial state is an unsigned JSON file and
  `TRIAL_DURATION` is a plain constant in readable Apache-2.0 source, so a user
  who controls the machine can extend the trial. This was always true; the
  defect was that `pyobfus/trial.py` claimed the trial was "device-bound and
  one-time only," which promised enforcement the implementation cannot deliver.
  No client-side check inside an open-source package can be tamper-proof, so
  rather than add signing that only raises the bar for editing data while
  leaving the verifier equally patchable, the boundary is now stated honestly
  in `trial.py`, `SECURITY.md`, `README.md` and the docs site. Trial bypass is
  explicitly out of scope for the security policy. The Community Edition
  remains fully Apache-2.0 with no file or line limits and needs no trial.
- `SECURITY.md` supported-versions table updated from the stale 0.4.x line to
  0.5.x.
- **CI now enforces all three documented test roots.** `pyobfus_mcp/tests/`
  (73 tests) was never run in CI — only `_build_server()` was called — and
  `integration_tests/` was an empty directory, so the documented
  `pytest integration_tests/` root collected zero tests. Both are now real
  jobs, and the former inline CLI smoke steps became collectible end-to-end
  tests that execute the obfuscated output and compare its stdout against the
  original. `black`/`ruff` coverage extended to `pyobfus_pro/`, the MCP package
  and `integration_tests/`. The mypy baseline (8 errors) is tracked in #22.
- Removed `--ignore=tests/test_pro_features.py` from pytest `addopts`; its
  rationale ("pyobfus_pro is not in the public repo") stopped being true in
  0.5.0 and the test passes.

### Fixed

- **Documented command syntax that does not exist.** Release notes and docs
  described the build-fusion flags as `pyobfus build --<flag>`, but there is no
  `build` subcommand — `pyobfus` is a single command, so copying the documented
  form produced `Error: Invalid value for '[INPUT_PATH]': Path 'build' does not
  exist`. This affected the headline Pro flags for 0.5.1 through 0.5.3. The
  correct form is `pyobfus SRC -o OUT --level pro --<flag>`.

- Docs site showed `pyobfus-trial start --email your@email.com`; the CLI has no
  `--email` option.
- Removed a stale `Raises: TrialAlreadyUsedError` from `start_trial()`'s
  docstring — no such exception exists; the function returns
  `success: False` instead.

### Added

- `tests/test_trial.py::TestTrialTrustBoundary` — four tests that pin the
  documented limitation by asserting tampering *succeeds*. If a future change
  adds signing or server-issued entitlements these fail deliberately, forcing
  the documented boundary to be updated with the implementation.

## [0.5.3] - 2026-07-07

**Feature release.** Completes the three build-fusion Pro flags deferred from
0.5.1 (0.5.2 was a Python 3.9/3.10 patch). Published to PyPI via OIDC Trusted
Publishing with PEP 740 attestations. `pyobfus-mcp` is unchanged at 0.3.1 (no
tool-surface change; its `pyobfus>=0.5.1` floor resolves to 0.5.3).

### Added

- **`--bind-device` / `--bind-device-id <id>` (build fusion) — device-locked L3
  encryption (Pro, 0.5.3).** Encrypts the Selective-Opacity L3 layer key with a
  device fingerprint at build time (`bind_device_key(machine_id, salt)`), then
  rewrites the emitted `_LAYER_KEY = b"..."` literal into a runtime
  `bind_device_key(current_machine_id(), _pyobfus_build_salt)` re-derivation — so
  the raw key never ships and decryption only succeeds on the bound device
  (wrong device → derived key differs → AES-GCM tag fails → `OpacityRuntimeError`
  when the L3 function is first called). Two modes: `--bind-device` binds to the
  build machine (build-on-target); `--bind-device-id <machine-id>` binds to a
  supplied customer device id (implies `--bind-device`). Needs an active L3 layer
  (`--selective-opacity` / `--opacity-config`) to have a key to bind. This is the
  build-fusion, patent-lane counterpart to the older license-embed
  `--bind-machine` (P2-8 device axis).
- **`--opacity-config opacity.toml` (build fusion) — pattern-driven Selective
  Opacity (Pro, 0.5.3).** Assign the ENCRYPTED (L3) layer to functions by glob
  patterns over their **original** qualnames (e.g. `pattern = "*.secret_*"`),
  without hand-annotating each with `@opacity(...)`. Rules are resolved in a
  pre-mangle pass and applied by injecting `@opacity(Layer.ENCRYPTED)` on
  matches, so patterns match original names while the existing (post-mangle)
  opacity encryption pass does the work — no mangled→original name-map coupling
  needed. Reuses the already-shipped `OpacityConfig`/`Resolver` TOML
  infrastructure; implies `--selective-opacity`. Hand-written `@opacity(...)`
  decorators still win over config rules. (In this fusion ordering only the
  ENCRYPTED layer is materialized; transparent/ai-readable/obfuscated layers
  fall through to Core's default mangling.)
- **`--period N` (build fusion) — crypto-bound run-counter limit (Pro, 0.5.3).**
  Injects a module-top `period_check(default_counter_path(<artifact-id>), N)`
  guard that refuses to import once the artifact's run counter exceeds `N`,
  raising `LicenseExpired`. The counter path is resolved at **runtime** on the
  end-user's machine (never baked in at build time) via the new
  `default_counter_path` helper, which honors `$PYOBFUS_COUNTER_DIR` and
  otherwise defaults to `~/.cache/pyobfus/<artifact-id>/runs`; each module keeps
  an independent counter keyed by a truncated sha256 of its qualname. This is
  the build-fusion, patent-lane counterpart to the older license-embed
  `--max-runs` (P2-8 run-counter subset). Composes with the other 0.5.1 fusion
  flags. (`--bind-device` and `--opacity-config` remain the outstanding 0.5.3
  items.)
- **Citable DOI.** The project is archived on Zenodo with concept DOI
  [10.5281/zenodo.20846053](https://doi.org/10.5281/zenodo.20846053) (resolves to
  the latest version). Added `CITATION.cff` (powers GitHub's "Cite this
  repository" widget), a README Citation section + DOI badge, a "How to cite"
  docs page, and a `Citation` project URL on both `pyobfus` and `pyobfus-mcp`.

## [0.5.2] - 2026-06-22

**Patch release.** Fixes two Python-version-specific bugs in the 0.5.1
build-fusion Pro passes that broke `--seal-code` and `--vault` on Python
3.9/3.10. (Published to PyPI via OIDC Trusted Publishing with PEP 740
attestations.)

### Fixed

- **`--seal-code` spurious `IntegrityError` on Python 3.9/3.10.** The integrity
  seal hashed the function's code object with `marshal.dumps` at the default
  version (>= 3), which encodes each string's *interned* status and shares
  object references. The build-time code object (compiled from an in-memory
  AST) and the runtime one (compiled by the import machinery) can differ in
  those identity-level details — on Python 3.9/3.10 they did — so a sealed
  function's runtime hash diverged from its build-time seal and raised a false
  `IntegrityError`, most visibly when `--seal-code` was combined with the other
  build-fusion passes. The seal is now pinned to marshal version 2, which
  serializes by value only. No behavior change on 3.11+. Regression guard:
  `tests/test_seal_runtime.py::TestMarshalVersionStability` plus the existing
  end-to-end `test_build_fusion` suite running on the full 3.9–3.14 CI matrix.
- **`--vault` `TypeError: zip() takes no keyword arguments` on Python 3.9.** The
  vault build transformer used `zip(..., strict=True)`, but the `strict`
  keyword was only added to `zip()` in Python 3.10, so every vault-dependent
  path (the vault transformer, the combined build-fusion passes, device
  binding, and the six-feature integration round-trip) raised on 3.9 — a
  supported floor. Dropped to a plain `zip()`; the `strict` check was redundant
  because an `ast.Dict` always has equal-length `keys`/`values` and the only
  exception (`**`-unpacking) is already rejected upstream.

## [0.5.1] - 2026-06-22

**Build-fusion release.** (Built 2026-06-18; published to PyPI 2026-06-22 via OIDC Trusted Publishing with PEP 740 attestations.) The v0.5 Pro mechanisms are now wired into the main
`pyobfus` CLI as opt-in flags, composing correctly with Core name-mangling and
string-encoding (the interleave validated by the 2026-06-18 design probe: vault
runs as a PRE-pass; opacity and seal as POST-passes over the final mangled
bytecode).

### Added — Pro build flags (single-file / `--no-cross-file`, like existing Pro features)

- **`--selective-opacity`** (P2-1) — AES-256-GCM-encrypt functions marked
  `@opacity(Layer.ENCRYPTED)`; lazy `__code__` materialization at runtime.
- **`--seal-code`** (P2-9) — bytecode integrity seal for `@seal_code` functions,
  hashed against the final obfuscated bytecode (ciphertext for L3 functions).
- **`--vault`** (P2-11) — rewrite `vault_secrets({...})` into an encrypted
  runtime `Vault` (secrets never appear as plaintext in the output).
- **`--scrub-traceback`** (P2-10) — install a production traceback-encrypting
  excepthook; the RSA private key is written to a `<output>.scrub.key.pem`
  sidecar for reversing error IDs with `pyobfus-unscrub`.
- **`--fingerprint <buyer-id>`** (P2-7) — derive a per-buyer deterministic L3
  key for forensic watermarking / piracy traceback.
- **`--expire-hard <ISO-date>`** (P2-8 subset) — inject a module-top expiry
  check that refuses to import past the date.

Note: like the existing Pro AST features (CFF, string-AES, …), these run in
single-file / `--no-cross-file` mode, not cross-file directory mode.

### Deferred to 0.5.3 (renumbered — 0.5.2 became a Python 3.9/3.10 patch)

- `--bind-device` (runtime device-key substitution) and `--period` (run-count
  counter file) — the P2-8 device/period subset needs careful runtime-key AST
  rewriting.
- `--opacity-config` TOML pattern rules — needs name-map coupling so config
  patterns match pre-mangle qualnames; the decorator channel ships now.

### Changed

- README long-description refreshed (the 0.5.0 PyPI page kept the pre-3.8-drop
  text; this release surfaces the corrected Python ≥3.9 / 1016-test copy).

### Testing

- Test suite **1016 → 1024** (+8 end-to-end build-fusion CLI tests). Zero regressions.

## [0.5.0] - 2026-06-18

**Patent milestone release.** The six v0.5 Pro mechanisms that were held back
under an active Chinese invention-patent application (CN 202610712171X, priority
date 2026-05-22) are now public: the application passed preliminary examination
(初步审查合格) on 2026-06-17, securing the priority date, so disclosure no longer
risks the filing.

### Added — Pro Edition mechanisms (patent-targeted)

These ship as the `pyobfus_pro` API, the `pyobfus-unscrub` developer CLI, and
standalone build passes. Fusing them into a single `pyobfus build --flag`
combined run (alongside Core name-mangling) needs additional Core
parameterization and lands in **0.5.1**.

- **Selective Opacity (P2-1)** — per-symbol protection layers (transparent /
  ai-readable / obfuscated / encrypted); L3 functions are AES-256-GCM encrypted
  with lazy `__code__` materialization. `pyobfus_pro.opacity` + `transformers.opacity`.
- **Forensic watermarking (P2-7)** — per-buyer deterministic key derivation
  (`forensic_seed` / `WatermarkRNG` / `derive_layer_key`) for piracy traceback.
- **License binding combo (P2-8)** — device / expiry / run-count binding woven
  into the AES-GCM decryption path (`pyobfus_pro.license_binding`); the license
  gate is the GCM tag check itself, with no separate patchable check.
- **`@seal_code` integrity decorator (P2-9)** — build-time bytecode hash baked
  in; runtime detection of in-memory patching, with layer-aware sealing for L3.
- **`--scrub-traceback` (P2-10)** — production traceback encryption (hybrid
  RSA-2048-OAEP + AES-256-GCM); developer reverses error IDs with the new
  **`pyobfus-unscrub`** CLI.
- **Runtime String Vault (P2-11)** — encrypted KV namespace for runtime secrets
  with lazy per-entry decryption and schema-without-key queries.

### Changed

- **BREAKING: dropped Python 3.8** (EOL 2024-10). `requires-python` is now
  `>=3.9`, removing the recurring `astunparse` CI flakes documented in
  `docs/PYTHON38_COMPATIBILITY.md`.
- Development Status classifier promoted **Beta → Production/Stable**.
- `cryptography>=42.0`; added `tomli` backport for Python < 3.11 (opacity-config
  TOML parser).

### Testing

- Test suite **727 → 1016** (+290 Pro-mechanism tests, 1 skip). Zero regressions.

## [0.4.1] - 2026-06-11

### Added — Core Features

- **Numeric / constant obfuscation (`--numeric-obfuscation`)** — Community-tier AST transformer that replaces integer and float literals with value-preserving opaque expressions, so the original constants no longer appear in shipped source (ROADMAP P2-5). Integers become random XOR / add / sub identities (exact in Python's arbitrary-precision arithmetic, any sign); floats become `float.fromhex(...)` calls (bit-exact round-trip, unlike a naive `a + b` split). Booleans, `None`, strings, bytes, and complex literals are left untouched, as are numeric literals inside `match`/`case` patterns (which must stay literal). Runs after name mangling and string encoding so the emitted `float` builtin reference is never renamed and the hex strings are not re-encoded. 37 new tests covering int/float round-trip exactness, skip rules, and match-case preservation.
- **AI artifact stripping (`--strip-ai-artifacts`)** — Community-tier AST transformer that removes AI-generation *provenance markers* (e.g. `Generated by Claude`, `Co-Authored-By: Claude`, `🤖 Generated with Claude Code`) so code authored with an AI assistant doesn't ship with "this was AI-generated" fingerprints (ROADMAP P2-3). Deliberately conservative for near-zero false positives: only **docstrings** (module/function/class) and **attribution dunders** (`__author__`, `__copyright__`, `__credits__`, `__maintainer__`) whose text matches an unambiguous attribution marker are removed; arbitrary string literals (program data) and conversational AI-tell phrasing are left untouched. Regular comments need no handling — the AST round-trip already drops them. Emptied function/class bodies are backfilled with `pass`. 27 new tests.
- **`python -m pyobfus` module entry point** — Added `pyobfus/__main__.py` so the CLI is invocable as a module via the current interpreter, not only through the `pyobfus` console script on `PATH`. Makes subprocess invocation reliable for tooling (used by the pyobfus-mcp `protect_project` orchestration tool).
- **`--trace-marker` auto-unmap convention** — Opt-in flag (requires `--save-mapping`) that prepends a stable `# pyobfus:obfuscated id=<id> mapping=<file>` header — plus the exact `--unmap` command — to each obfuscated file. An AI agent that lands in an obfuscated file from a traceback immediately knows the artifact is pyobfus output and how to reverse the names. The mapping file gains a deterministic `marker_id` (stable across runs with the same name map) that cross-references the header. Shebang and PEP 263 encoding cookies are preserved; stamping is idempotent. The `--json` obfuscate output gains a `trace_marker_id` field. Comment-only — does not affect execution. 7 new tests.

### Testing

- Test suite **655 → 727** (+37 numeric obfuscation, +27 AI artifact stripping, +7 trace marker, +1 misc). Zero regressions.

## [0.4.0] - 2026-04-22

**AI-native release.** Ten features shipped in one day around a single theme: making pyobfus the Python obfuscator that AI coding agents (Claude Code, Cursor, Windsurf, Zed) can actually use. Reshape v0.4 goals toward adoption + AI-native integration (see `docs/ROADMAP.md`, `docs/AI_INTEGRATION_STRATEGY.md`, `docs/V0.4_EXECUTION_LOG.md`).

### Added — P0 Core Features

- **`pyobfus --check` pre-flight risk scanner** — Detects `eval`/`exec`/`compile`, dynamic `getattr`/`setattr` with non-literal names, `__import__` / `importlib.import_module`, `vars`/`locals`/`globals`/`dir`/`inspect.*`, `.__name__`/`.__qualname__`/`.__class__` string references, `__all__` exports, and `__main__` entry-point guards. Auto-detects imports of FastAPI, Django, Flask, Pydantic, Click, SQLAlchemy and suggests a matching preset. Exit codes: `0` safe / `1` high-risk / `2` parse errors.
- **`pyobfus --unmap` reverse mapping** — Reverses obfuscated identifiers in a production stack trace using a `mapping.json`. Identifier-boundary-aware (no false replacements inside longer names). Solves the "I can't debug obfuscated code with my AI assistant" dead end.
- **`pyobfus --save-mapping PATH`** — Writes a versioned JSON mapping during obfuscation (both single-file and cross-file modes). Format v1 includes pyobfus version, scan root, mode, per-module forward map, and a precomputed reverse index.
- **Framework-aware presets** — `--preset fastapi | django | flask | pydantic | click | sqlalchemy`. All community-tier (free), built on `preset_safe`, with `preserve_param_names=True` and framework-specific `exclude_names` + `exclude_patterns` bundled in.
- **AI-friendly global `--json`** — Every CLI mode (obfuscate, `--check`, `--init`, `--unmap`) emits a stable JSON schema with `version`, `status`, `ai_hint`, and `exit_code` fields. Errors follow `{error_type, message, suggestion, ai_hint, exit_code}`. `ai_hint` contains the single next command for an AI agent to run.
- **`pyobfus --init`** — Zero-config onboarding. Scans project → detects framework → writes `pyobfus.yaml` with the matching preset, auto-assembled `exclude_patterns`, and explanatory comments aimed at both humans and AI assistants.
- **`preset:` YAML key support** — `ObfuscationConfig.from_file()` now accepts a top-level `preset:` that's applied first; other fields override individual settings. `exclude_patterns` and `exclude_names` merge additively. Unknown keys raise a clear `ValueError`.

### Added — P1 AI Ecosystem

- **`pyobfus-mcp` (new sibling package)** — Model Context Protocol server exposing five tools (`check_obfuscation_risks`, `generate_pyobfus_config`, `unmap_stack_trace`, `list_presets`, `explain_preset`) to Claude Desktop, Claude Code, Cursor, Windsurf, Zed, and any MCP-capable agent. See `pyobfus_mcp/README.md`.
- **`llms.txt` + `llms-full.txt`** (llmstxt.org standard) — Concise project overview + full JSON schema reference at the repo root and docs site.
- **AI integration templates** — `templates/ai-integration/` contains drop-in rule files for Claude Code (`CLAUDE.md`), Cursor (`cursor-rules.mdc`, `.cursorrules`), Windsurf, GitHub Copilot, and a generic `AGENTS.md`.
- **`--incremental` flag** — Project-level skip-if-unchanged cache at `<output>/.pyobfus-cache/manifest.json`. Unchanged rebuilds become O(scan) instead of O(transform).

### Changed

- **Package description + keywords** — PyPI description rewritten for keyword density; adds `python-obfuscator`, `py-obfuscator`, `pyobfuscator`, all 6 framework names, `mcp`, `claude-code`, `cursor`, `llm-tools`, `ai-native`. README headline now reads **"pyobfus — the Python obfuscator"** with a pronunciation line to build AI training-corpus association.
- **Development Status classifier** — `3 - Alpha` → `4 - Beta` (consistent with 655 tests / 91% coverage).
- **GitHub repo topics** — 12 new topics including `python-obfuscator`, `mcp-server`, `claude-code`, `cursor`, `pyarmor-alternative`.

### Testing

- Test suite grew **561 → 655** (+94 tests in main package). New test files: `test_preflight.py`, `test_mapping.py`, `test_unmap_cli.py`, `test_framework_presets.py`, `test_json_cli.py`, `test_init_config.py`, `test_incremental.py`. Plus 16 tests in `pyobfus_mcp/tests/test_tools.py`.
- Coverage **90% → 91%**.
- Zero regressions.

### Documentation

- New: `docs/AI_INTEGRATION_STRATEGY.md`, `docs/V0.4_EXECUTION_LOG.md`.
- Updated: `docs/ROADMAP.md` fully reshaped around P0/P1 priorities with effort estimates.
- Updated: `README.md` AI-native features section, `CHANGELOG.md` (this entry).

## [0.3.3] - 2026-03-24

### Added
- **Parallel File Processing**: New `-j/--jobs` CLI option for multi-process obfuscation
  - `-j 0` (default): auto-detect CPU cores
  - `-j 1`: sequential processing
  - `-j N`: use N worker processes
  - Phase 1 (scan) remains sequential; Phase 2 (transform) runs in parallel
  - Real-time progress display with percentage
- **`max_workers`** config option in `ObfuscationConfig` for programmatic control

### Changed
- **Test Coverage**: 56% -> 90% (410 -> 561 tests)
  - Comprehensive CLI tests (single file, directory, cross-file, Pro features, presets)
  - Pro feature path tests using mock (control flow, dead code, string encryption, anti-debug, license embedding)
  - Trial CLI tests (start, status, features commands)
  - Extended analyzer, transformer, plugin, and exception tests

## [0.3.2] - 2025-12-27

### Added
- **Python 3.14 Support**: Full support for Python 3.14 (latest stable release)
  - CI testing on Python 3.8-3.14 across all platforms
  - Updated documentation and SEO keywords
- **Statistics Summary**: New `--stats` CLI flag to display obfuscation statistics
  - Files processed, names obfuscated, strings encoded/encrypted
  - Pro feature counts (control flow, dead code, anti-debug)
- **PyPI Badges**: Version and download count badges in README
- **Dual Licensing Documentation**: Synced Open Core license model across all docs

### Changed
- **Version Management**: Refactored to Single Source of Truth pattern
  - `pyproject.toml` is now the only place version is defined
  - `pyobfus.__version__` reads from package metadata via `importlib.metadata`
  - Removed hardcoded versions from README.md, ROADMAP.md, and other docs
- Improved documentation consistency for Apache 2.0 (core) + Proprietary (Pro) licensing

## [0.3.1] - 2025-12-25

### Fixed
- Fixed mypy type errors in control flow, dead code, and license embedding modules
- Synced `__version__` across all modules

## [0.3.0] - 2025-12-25

### Added
- **License Embedding** (Pro): Embed restrictions directly into obfuscated code
  - `--expire YYYY-MM-DD`: Set expiration date
  - `--bind-machine`: Bind to specific machine
  - `--max-runs N`: Limit executions

- **Configuration Presets**: Simplified setup with pre-built presets
  - `--preset trial/commercial/library/maximum`
  - `--list-presets`: View all presets

- **Control Flow Flattening** (Pro): Transform control flow into state machines
  - Supports if/else, for loops, while loops
  - CLI: `--control-flow`

- **Dead Code Injection** (Pro): Inject unreachable code
  - Four strategies: After Return, False Branches, Opaque Predicates, Decoy Functions
  - CLI: `--dead-code`

### Example
```bash
# Create a 30-day trial version
pyobfus src/ -o dist/ --preset trial

# Commercial distribution with machine binding
pyobfus src/ -o dist/ --preset commercial

# Custom restrictions
pyobfus src/ -o dist/ --expire 2025-12-31 --bind-machine
```

## [0.2.4] - 2025-12-22

### Added
- **5-Day Pro Trial**: Try Pro features FREE without registration
  - `pyobfus-trial start` - Start trial
  - `pyobfus-trial status` - Check status
  - Works seamlessly with main CLI

## [0.2.3] - 2025-12-11

### Fixed
- **[P0] Python 3.6-3.11 Compatibility**: F-string quote handling now works on ALL Python versions

### Added
- `--upgrade` CLI command: Display Pro features and purchase info
- FAQ section in README
- Comparison documentation (`docs/COMPARISON.md`)

## [0.2.2] - 2025-12-11

### Fixed
- **[P0] F-String Quote Bug**: Fixed syntax errors with dictionary subscripts in f-strings

## [0.2.1] - 2025-12-10

### Added
- **Configuration Templates**: `pyobfus --init-config django/flask/library/general`
- **Configuration Validation**: `pyobfus --validate-config`
- **Auto-Discovery**: Automatically find `pyobfus.yaml` without `-c` flag

## [0.2.0] - 2025-11-19

### Added
- **Cross-File Obfuscation**: Consistent name obfuscation across multiple files
  - Automatic import statement rewriting
  - `__all__` list updates
  - Global symbol table with collision detection

- **CLI Enhancements**:
  - `--cross-file/--no-cross-file` flag (default: enabled)
  - `--dry-run` for preview without writing

### Fixed
- **[CRITICAL]** Local name references now updated after export renaming

### Breaking Changes
- Cross-file mode now default (use `--no-cross-file` for legacy behavior)

## [0.1.6] - 2025-11-12

### Added
- **String Encoding (Base64)**: Community Edition feature
- **Pro Features** (require license):
  - AES-256 String Encryption
  - Anti-Debugging Checks
- **Parameter Preservation**: `--preserve-param-names` for keyword argument support
- Self-service purchase flow with Stripe

### Fixed
- **[CRITICAL]** StringEncoder F-string bug (Issue #10)

## [0.1.5] - 2025-11-12

### Fixed
- **[CRITICAL]** Class attribute renaming inconsistency (Issue #7)

### Added
- Class attribute tracking and consistent renaming

## [0.1.4] - 2025-11-12

### Added
- Device fingerprint for license validation
- Enhanced cache security

## [0.1.3] - 2025-11-11

### Fixed
- Added `cryptography` to required dependencies
- Fixed `__version__` attribute

## [0.1.2] - 2025-11-11

### Added
- **License Verification System** for Pro Edition
- Pro Edition features: AES-256 encryption, Anti-debugging

### Breaking Changes
- Pro edition now requires license registration

## [0.1.1] - 2025-11-11

### Fixed
- **[CRITICAL]** Method name obfuscation now updates all call sites (Issue #4)

### Added
- Configuration presets: `preset_safe()`, `preset_balanced()`, `preset_aggressive()`
- Auto-detection of public APIs

## [0.1.0] - 2025-11-11

### Added
- Core obfuscation engine with AST-based name mangling
- Multi-file obfuscation support
- YAML configuration system
- Command-line interface
- Python 3.8-3.12 support

## [0.0.1] - 2025-11-10

### Added
- Initial project structure
