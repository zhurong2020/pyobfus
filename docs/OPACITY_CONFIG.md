# Selective opacity configuration

`--opacity-config` assigns protection layers to top-level functions using their
original qualified names, before name mangling changes them. It is a Pro
feature and accepts a TOML file:

```toml
default_layer = "obfuscated"

[[rules]]
pattern = "myapp.api.public_*"
layer = "transparent"

[[rules]]
pattern = "myapp.crypto.secret_*"
layer = "encrypted"
```

Use it during a build:

```bash
pyobfus src/ -o protected/ --level pro --opacity-config opacity.toml
```

## Fields

- `default_layer` is optional and defaults to `"obfuscated"`.
- Each `[[rules]]` entry requires a non-empty `pattern` and a `layer`.
- Patterns use case-sensitive Unix shell-style matching against the original
  qualified name, such as `myapp.crypto.secret_hash`.
- Rules are evaluated in declaration order; the first match wins.
- An explicit `@opacity(...)` decorator on a function takes precedence over
  configuration rules.

The four accepted layer names are:

| Value | Intended layer |
|---|---|
| `transparent` | Keep source structure readable |
| `ai_readable` | Preserve an analysis-friendly form |
| `obfuscated` | Apply the normal Core obfuscation pipeline |
| `encrypted` | Encrypt the function body and materialize it lazily at runtime |

## Current CLI boundary

In the current command-line fusion pipeline, `encrypted` is the only configured
layer that adds per-function behavior: matching top-level functions receive L3
encryption. The other three values currently fall through to the normal Core
pipeline; they do not selectively undo or downgrade Core mangling. The Pro API
names four layers, but only `encrypted` has an implementation today: the
`transparent` and `ai_readable` values are descriptive and add no behavior
anywhere, so do not read the model as four independently materialized
per-function transformations.

Only top-level functions and async functions are matched by the CLI pre-pass.
Methods and nested functions are not currently encrypted even when an
`opacity.toml` rule matches them; the build warns with how many were skipped,
and `--build-report` records the counts (`l3_skipped_methods`,
`l3_skipped_nested`). The pass does not run in default cross-file directory
builds (the CLI warns and lists the skipped options); build single files, use
`--no-cross-file`, or opt into the restricted cross-file preview below.

## Delivery requirement

Encrypted output imports the redistributable `pyobfus-runtime` package, not
the builder. Install the runtime beside the artifact on the target (for an
offline target, stage its wheel and dependencies and use
`pip install --no-index --find-links <dir> pyobfus-runtime`); the builder's
declared floor (`pyobfus-runtime>=0.1.1`) is the version the artifact needs.
Test the protected output in the same clean offline environment in which the
recipient will run it; `integration_tests/test_offline_target.py` is the
repository's version of that check.

## Validation errors

The build fails for malformed TOML, unknown layer names, missing or empty
patterns, non-string values, or a `rules` value that is not a list of TOML
tables. Overlapping patterns are resolved by first-match precedence, so order
rules from most specific to most general.

## Cross-file L3 preview (since 0.10.0)

The default cross-file behavior described above remains unchanged. Core 0.10.0
adds explicit `--crossfile-opacity` for directory L3 with
application-provided keys.

```bash
# Set APP_L3_KEY securely to a base64-encoded 32-byte application key.
# Create the metadata parent first; all destination paths must be new.
pyobfus src/ -o protected-v1/ --level pro --crossfile-opacity \
  --opacity-config opacity.toml --bind-key-env APP_L3_KEY --jobs 1 \
  --save-mapping private/mapping-v1.json --build-report private/report-v1.json
```

Only unconditional, stable, undecorated, synchronous module-top functions can
be encrypted. Matching unsupported methods, nested/async/generator functions
or rebound definitions fails the build. Other layer values retain the normal
Core transformations. Rules use the original module path relative to `src/`;
for `src/pkg/algorithm.py`, use `pkg.algorithm.function_name`.

All destination parents must already exist on one filesystem, outside the
source tree. Output, mapping and report must be distinct fresh paths; mapping
and report stay outside delivery. Incremental builds, handwritten Pro markers,
other fusion mechanisms, free-threaded builds, and unproved project module
attribute accesses are refused. Use `--check` and `exclude_names` to resolve
uncertain module accesses. `--trace-marker`, `--provenance-manifest`, and
`--verify-names` are not supported by this preview transaction; syntax is always
compiled in staging without executing user code. `--dry-run` validates without
writing a release.

Register the provider **outside** the protected package and before importing
it. `python -m package`, console scripts and spawn workers can execute package
`__init__` too early; each spawned child needs its own bootstrap/initializer:

```python
from pyobfus_runtime import set_key_provider

set_key_provider(load_authorized_application_key)  # stable 32-byte key
from protected_app import main
```

Environment fallback is also supported. Missing or invalid-length keys fail at
import; a wrong 32-byte key fails on the first encrypted call. Registering a
provider later does not revoke or change keys already held by modules.

Artifacts require the build's CPython minor, bytecode magic and GIL build mode.
The guard runs before runtime/provider initialization. Encrypted frames restore
only original function names; their original line is unavailable. Ordinary
functions in an L3 module may retain their obfuscated names and locations.
Unknown encrypted frame identities remain unchanged, including when supplied
the wrong mapping. Keep the private mapping; readers need Core 0.10.0 or later.

Deliver the completed directory including `.pyobfus-release.json`, then run
`pyobfus --check-delivery protected-v1/ --build-report private/report-v1.json`.
The completion manifest and file digests detect accidental mixing and edits;
they are not signatures. Keep mappings and staging ownership journals private.
A failed build removes only metadata hard-linked to its own stage. After an
interruption, inspect the known private `.pyobfus-release-*` stage and use the
Community Python API `pyobfus.core.staged_release.recover_staging(stage_path)`;
it never deletes an existing application directory or replaced metadata.
This is not a crash-durable multi-path transaction.

Runtime-only delivery uses the public `pyobfus-runtime==0.1.1` API. Validation
results and platform scope are recorded in
[CROSSFILE_OPACITY_VALIDATION.md](CROSSFILE_OPACITY_VALIDATION.md).
