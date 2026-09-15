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
pipeline; they do not selectively undo or downgrade Core mangling. The full
four-layer model is available through the Pro API, but the CLI should not be
read as providing four independently materialized per-function transformations.

Only top-level functions and async functions are matched by the CLI pre-pass.
Methods and nested functions are not currently selected by `opacity.toml`.

## Delivery requirement

Encrypted output imports the Pro runtime. Until the runtime redistribution
work tracked as Y-1 is complete, do not assume an L3-protected file is
self-contained or may be delivered without the applicable Pro runtime and
licence terms. Test the protected output in the same clean offline environment
in which the recipient will run it.

## Validation errors

The build fails for malformed TOML, unknown layer names, missing or empty
patterns, non-string values, or a `rules` value that is not a list of TOML
tables. Overlapping patterns are resolved by first-match precedence, so order
rules from most specific to most general.
