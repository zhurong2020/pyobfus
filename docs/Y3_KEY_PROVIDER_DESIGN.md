# Runtime key-provider hook design (Y-3)

Status: v1 designed and implemented, held in `[Unreleased]` pending a release
gate. This document is the record of the contract and the scope decisions.

## Problem

`--bind-device` binds the Selective Opacity L3 key (and Vault keys) to
pyobfus's own machine identity (`current_machine_id()`). An application that
already runs its own authorization system — its own JWT, its own per-machine
key escrow on a server it controls — cannot bind the L3 decryption key to
*its* authorization without building a separate artifact per machine, because
the runtime key is derived from pyobfus's fingerprint rather than material the
application supplies.

Downstream driver: CAC Plus hospital edition (offline Windows, torch/MONAI,
Python 3.13 embedded). It wants one artifact whose L3 layer decrypts only when
its own server, after verifying the site's authorization, provides the key
material.

## Decision (v1)

Add a build mode `--bind-key-env NAME` that binds the L3 key to **application-
supplied key material** instead of the machine fingerprint. It reuses the
existing `_LAYER_KEY` runtime-rewrite channel; only the key source changes.

- The application supplies the actual 32-byte AES-256 key. pyobfus does not
  derive it from a machine id and does not run PBKDF2 over it — the key is the
  application's to manage, wrap per machine on its own server, and deliver after
  its own auth check. The same artifact therefore runs on any machine the
  application authorizes; no per-machine build.
- Two runtime channels, both handled by one emitted call
  `_LAYER_KEY = _pyobfus_provided_key("NAME")`:
  1. **Registered provider** — the application calls
     `pyobfus_runtime.set_key_provider(fn)` before importing the protected
     module, where `fn` is a zero-argument callable returning the 32-byte key
     (`bytes`). This is the rich path: verify a JWT, fetch the per-machine key
     from the application's server, return it.
  2. **Environment-variable fallback** — if no provider is registered,
     `provided_key("NAME")` reads `os.environ["NAME"]`, base64-decodes it, and
     uses it. This is the zero-code path for simple deployments.
  If neither yields a valid 32-byte key, the runtime raises
  `LicenseBindingError` at import, so a missing key fails loudly rather than
  producing a mystery decryption error.

## Build-time key source

`--bind-key-env NAME` reads the build-time key from environment variable
`NAME`: a base64-encoded 32-byte key. The build uses it directly to encrypt the
L3 ciphertext, and bakes `NAME` into the artifact as the runtime environment
fallback name. Supplying the key by environment variable (not a CLI value)
keeps it out of the process argv and shell history. The build fails with a
clear error if `NAME` is unset or does not decode to exactly 32 bytes.

Build and runtime are symmetric: the same 32 bytes that encrypted the artifact
must be what the provider or the runtime env var yields.

## Scope decisions (v1)

- **L3 (Selective Opacity) only.** This is the downstream's stated target.
  Runtime String Vault keys are **not** covered in v1.
- **`--bind-key-env` with `--vault` is rejected** with a clear error, rather
  than silently leaving Vault keys baked (which would ship raw Vault keys and
  quietly weaken protection). Vault coverage is a documented follow-up.
- **Mutually exclusive with `--bind-device` / `--bind-device-id`.** Both rewrite
  the same `_LAYER_KEY`; a build picks one binding source.
- **Requires an L3 layer to be active** (`--selective-opacity` or
  `--opacity-config`), same as `--bind-device` — binding a key with nothing to
  bind is a no-op and is rejected.

## Runtime API additions (`pyobfus_runtime`)

- `set_key_provider(provider)` — register a `Callable[[], bytes]` returning the
  32-byte key, or `None` to clear. Global, process-wide.
- `provided_key(env_name)` — resolve the key: registered provider first, then
  `os.environ[env_name]` (base64). Validates 32 bytes. Raises
  `LicenseBindingError` on absence or wrong length. This is the frozen v1 call
  shape the emitted code depends on.

Both are added to `pyobfus_runtime.__all__`. Adding them does not change any
existing call shape, so artifacts built before this release are unaffected.

## Emitted code shape

For `--selective-opacity --bind-key-env PYOBFUS_L3_KEY`:

```python
from pyobfus_runtime import provided_key as _pyobfus_provided_key
_LAYER_KEY = _pyobfus_provided_key("PYOBFUS_L3_KEY")
```

The raw key never ships in the artifact; only the environment-variable *name*
does.

## Security notes

- The application owns the key. pyobfus's guarantee is only that the L3
  ciphertext + AES-GCM tag decrypt iff the supplied key is byte-identical to the
  build key — the "license check is the AES-GCM tag check" property is preserved,
  now keyed to the application's material instead of a machine fingerprint.
- A registered provider runs arbitrary application code at import; that is the
  application's own code, by design.
- The environment-variable channel is only as strong as the application's
  protection of that variable; the registered-provider channel is preferred for
  anything beyond simple deployments.

## Follow-ups (not in v1)

- Vault key coverage (`_VAULT_KEY_<name>`), with per-vault derivation from the
  provided key so vaults stay mutually isolated.
- An optional key-wrapping helper (provider returns a wrapped key + the runtime
  unwraps with a per-machine secret) if a downstream needs escrow without the
  application handling raw AES keys.
