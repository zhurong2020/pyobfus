# Verifiable delivery reference application

This stdlib-only storefront is the public input for pyobfus's delivery
acceptance path. It deliberately combines a package and subpackage, relative
imports, a packaged resource, a fixed-allowlist dynamic plugin, and a stable
failure that can be reverse-mapped.

The scope and pass/fail contract live in
[`docs/DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md`](../../docs/DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md).
This example is not proof that every freezer or application is supported.

## Baseline

```bash
venv/bin/python examples/delivery_reference/main.py pro
# pricing-v1
# pro: 65.88

venv/bin/python examples/delivery_reference/main.py bogus_tier
# exits non-zero with ValueError: Unknown pricing tier: bogus_tier
```

Only the fixed plugin name `standard` is accepted. User input is never turned
into an arbitrary import path.

## Community protected directory

Keep all private evidence outside the deliverable:

```bash
work="$(mktemp -d)"
venv/bin/python -m pyobfus examples/delivery_reference \
  -o "$work/protected" \
  --config examples/delivery_reference/pyobfus.yaml \
  --save-mapping "$work/mapping.json" \
  --build-report "$work/build.json" \
  --verify-syntax --jobs 1 --json

mkdir -p "$work/protected/storefront/data"
cp examples/delivery_reference/storefront/data/label.txt \
  "$work/protected/storefront/data/label.txt"
venv/bin/python "$work/protected/main.py" pro
```

The explicit resource copy is intentional: pyobfus protects Python source; it
does not silently decide how an application's non-code assets should be
packaged. Do not put `mapping.json`, `build.json`, source trees, keys, trial
state, or raw traces in the delivery directory.

The Pro L3 and Windows Nuitka standalone lanes are acceptance steps, not
default example commands. They require isolated state and the frozen versions
recorded by the acceptance plan. `key_provider.py` demonstrates application
ownership of key input; it contains no key and is not used by the Community
baseline.

## Feedback

For real delivery problems, use the
[Delivery blocker / frozen format issue template](https://github.com/zhurong2020/pyobfus/issues/new?template=delivery_blocker.md).
This example is the shared reproduction baseline: reproduce against it when
possible and describe any minimal changes needed. Use synthetic inputs and
remove secrets and personal data; never attach licence keys, private keys,
mapping files or proprietary source.
