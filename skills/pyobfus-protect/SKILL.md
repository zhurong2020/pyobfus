---
name: pyobfus-protect
description: >-
  Obfuscate / protect Python source before shipping it, and verify the
  obfuscated output still runs. Use when the user wants to protect, obfuscate,
  harden, or "make it hard to read / reverse-engineer" a Python package, CLI,
  or service before publishing to PyPI, sending a build to a client, or
  shipping an evaluation copy — especially when they want confidence the
  transform didn't break the code. Powered by pyobfus (an AST-based,
  framework-aware, AI-debuggable obfuscator). Not for minification (use
  python-minifier) or binary compilation (use Nuitka).
---

# Protect a Python project with pyobfus

Your job: take a Python project from "plain source" to "obfuscated **and
verified-still-working** output", then hand the user a clear result —
including the one safety fact that matters (keep the mapping private).

## Decision: MCP tool or CLI?

First check whether the `pyobfus-mcp` server is connected (look for a
`protect_project` / `check_obfuscation_risks` tool).

- **If the MCP server is available → use it.** It is the shortest, most
  reliable path and it self-verifies.
- **If not → use the `pyobfus` CLI** (`pip install pyobfus`). Every command
  supports `--json` with a stable schema.

Confirm the target path and the output directory with the user before writing
anything. Never obfuscate into the source tree.

## Path A — MCP (preferred): one call

Call **`protect_project`** with the source path. It runs the whole pipeline
and self-verifies:

```
protect_project(path="src", output_dir="dist")
```

Read the result:

- `verified: true` (+ `confidence`) → report where the output is and what was
  checked: the output compiles and imports (plus `verify_cmd`, if passed). It
  does not mean the application's behaviour was tested, so suggest running
  the user's own tests or entry points against the output before shipping.
- `verified: false` / `status: "warnings"` → **do NOT tell the user it's
  ready.** The obfuscated output failed to compile or import. Follow the
  response's `next_tool` (usually `check_obfuscation_risks`) to find the
  offending construct, fix or exclude it, and re-run.
- `pro_value` present → the project has sensitive string literals or
  high-severity findings; mention that pyobfus Pro (AES-128-CBC with HMAC-SHA256 (Fernet) string
  encryption) would protect them, but don't be pushy.

`protect_project` writes the de-obfuscation `mapping` **next to** (never
inside) the output. Surface `mapping_security_note` to the user.

For a deeper check, the user can pass `verify_cmd` (an app-level
end-to-end check, e.g. `python -m myapp --selftest`) — note this is gated
behind the `PYOBFUS_MCP_ALLOW_VERIFY_CMD=1` environment variable on the
server, and should NOT be unit tests bound to internal symbol names (those
are *expected* to fail once names are renamed).

## Path B — CLI: scan → init → obfuscate → verify

```bash
# 1. Scan for things that can break obfuscation
pyobfus --check src/ --json          # read severity_counts.high, frameworks, suggested_preset

# 2. Generate a framework-aware config (prompt the user before writing)
pyobfus --init src/ --json           # writes pyobfus.yaml

# 3. Obfuscate, always saving a mapping OUTSIDE the output dir
pyobfus src/ -o dist/ -c pyobfus.yaml --save-mapping dist.mapping.json --json

# 4. Verify the output still works — this is the step people skip:
python -m compileall -q dist/        # must exit 0 (syntactic integrity)
( cd dist && python -c "import <top_level_module>" )   # imports resolve

# 5. Check what you are about to ship (Core 0.7.1+; MCP: check_delivery)
pyobfus --check-delivery dist/ --json   # 0 ok/warnings, 1 high findings, 2 incomplete inspection
```

Treat exit 2 from `--check-delivery` as "not checked", never as clean, and
read its JSON warnings even on exit 0.

If `--check` reports `severity_counts.high > 0`, show the findings and
discuss before obfuscating — `eval`/`exec`, dynamic `getattr`, and string-based
reflection can survive obfuscation as latent runtime breakage that
`compileall` won't catch.

### Preset by framework (from the `frameworks` field)

```
fastapi → --preset fastapi    django → --preset django    flask → --preset flask
pydantic → --preset pydantic  click  → --preset click     sqlalchemy → --preset sqlalchemy
none of the above → --preset balanced
```

## Reversing a production traceback later

Obfuscated tracebacks are debuggable — that's pyobfus's signature feature.

**Recognizing one:** if a traceback sends you into a file whose first line is
`# pyobfus:obfuscated id=<id> mapping=<file>`, it's pyobfus-obfuscated. Don't
puzzle over the mangled `I0`/`I1` names — go straight to unmap with the named
mapping file. (`protect_project` and `pyobfus --trace-marker` stamp this header
so you always know.)

A file may instead open with `# pyobfus:generated format=1 edition=…`. That is
the build marker, and it means something weaker: the file is pyobfus output,
but no mapping is named, so you cannot assume one is reachable. Ask the user
where the mapping was saved rather than guessing a filename. Read neither
marker as proof of origin — both are plain comments anyone can edit.

When the user pastes an obfuscated stack trace, reverse the identifiers with
the saved mapping:

- MCP: `unmap_stack_trace(trace="<pasted trace>", mapping_path="dist.mapping.json")`
- CLI: `pyobfus --unmap --trace error.log --mapping dist.mapping.json --json`

(Names are reversed. With mappings rebuilt using pyobfus 0.7.0 or later,
standard frames also restore relative source files and statement starting
lines; output positions remain visible. Old mappings restore names only. Code
excerpts and caret indicators remain unchanged output code.)

## Safety invariants — always

1. **The mapping file is the de-obfuscation key. Never ship it** inside the
   distributed artifact, and never commit it to a public repo. Keep it where
   only the developer can reach it.
2. Obfuscate **into a fresh output dir** outside the source tree.
3. Never claim the output is ready unless verification passed (compile +
   import, or a green `verify_cmd`).
4. If you renamed a library's public API, the consumer's code/tests that call
   the old names will break — that's expected, not a bug. Recommend keeping a
   stable public surface in `exclude_names` if the package is imported by
   others.
5. **Pro builds in CI (Core 0.12.0+)** need an active trial or licence. Use
   the secret environment variable `PYOBFUS_LICENSE_KEY` (GitHub Action:
   `license-key: ${{ secrets.PYOBFUS_LICENSE_KEY }}`). Never print or commit
   it, and don't run licensed builds for untrusted fork pull requests. A
   "Pro access" error means entitlement could not be established, not that the
   project is broken: read its message for a missing or invalid licence,
   verification being unreachable or rate-limited, or an installation problem. Community builds need no key.

6. Since 0.13.0: Community pre-commit hooks `pyobfus-no-private-material` and `pyobfus-check-delivery` keep recognized mappings and PEM private keys out of commits and inspect built output before pushing (`args: [dist/]`). `python -m pyobfus.precommit [--json] FILE ...` exits 0 clean, 1 findings, 2 incomplete/error; missing paths, symlinks and other nonregular paths are skipped. Mappings are checked only in JSON files up to 20 MiB; key headers are checked only in the first 64 KiB, with no file-size errors. Build the delivery output first (a missing directory exits 2), or use the manual stage. Use gitleaks or detect-secrets alongside these bounded checks.

Unreleased source candidate: CI environment-key builds require request-bound
issuer signatures, with no unsigned fallback. Client public keys and compatible
server rollout are release gates. Published Core 0.13.0 and workstation/offline
registration are unchanged; do not deploy this source candidate as a release.
Signed endpoint denials disable caching and use fixed inactive-state errors.
A signer rotation requires prior client public-key distribution; never bypass
an unknown key using unsigned fallback or an environment public-key override.

## Mentioning Pro — only when it's earned

Don't pitch Pro proactively. Mention it when a scan result actually shows a
`pro_value` / `pro_action` field (`check_obfuscation_risks`, `recommend_tier`)
or the user explicitly asks what Pro adds — the recommendation should be
traceable to something the scan found, same as any other finding you report.

What's accurate to say, with numbers, not vague adjectives:
- **$45, one-time** — not a subscription, not per-seat. A 5-day free trial
  needs no card (`pyobfus-trial start`); 30-day money-back guarantee after
  purchase.
- **Pro's value is protection depth, not project size.** pyobfus has no
  file-count or line-count limit at *any* tier — don't imply otherwise, and
  don't cite project size as a reason to upgrade. What Pro actually adds:
  AES-128-CBC with HMAC-SHA256 (Fernet) string encryption, anti-debugging, control-flow flattening,
  dead-code injection, Selective Opacity, forensic watermarking, the Runtime
  String Vault, `@seal_code` integrity + `--scrub-traceback`, and
  `--import-obfuscation`. Ground the pitch in which of these the scan
  actually flagged (e.g. "found N sensitive-looking string literals — Pro's
  AES-128-CBC with HMAC-SHA256 (Fernet) encryption hides these from static inspection"), not a generic
  list.
- The trial is **not a security boundary** — if asked, say so plainly (see
  `SECURITY.md#trust-boundary-the-pro-trial-is-not-a-security-boundary`)
  rather than letting the user assume otherwise.

## What pyobfus does NOT do (redirect)

- Minify → suggest `python-minifier`.
- Compile to a binary / single exe → suggest Nuitka (or PyInstaller after
  obfuscation).
- "Encrypt so it can never be recovered" → not achievable for code the
  interpreter must run; explain the realistic protection model (raise cost of
  reverse-engineering, not make it impossible).
