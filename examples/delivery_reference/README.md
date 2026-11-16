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

The Windows Nuitka standalone lane is an acceptance step, not a default
example command; use the versions recorded by the acceptance plan.

## Pro lane (trial)

This is a **local-trial demonstration**, verified on Linux. Run from the
repository root with pyobfus and its Pro runtime dependencies installed in
`venv/`. The trial command below is the module form of `pyobfus-trial start`;
without `--email`, it starts a 5-day local trial without a network call.
The subshell keeps HOME and USERPROFILE isolated for the entire build and
run sequence. No key is stored in the repository.

```bash
(
export HOME="$(mktemp -d)"
export USERPROFILE="$HOME"
export PYTHONPATH="$PWD"
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONHOME PYOBFUS_LICENSE_KEY
work="$(mktemp -d)"
mkdir -p "$work/private"

venv/bin/python -m pyobfus.trial_cli start

cat > "$work/private/opacity.toml" <<'TOML'
[[rules]]
pattern = "storefront.checkout.quote_order"
layer = "encrypted"

[[rules]]
pattern = "storefront.catalog.lookup_unit_price"
layer = "encrypted"
TOML

export PYOBFUS_DELIVERY_REFERENCE_KEY="$(venv/bin/python -c 'import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())')"

venv/bin/python -m pyobfus examples/delivery_reference \
  -o "$work/protected" \
  --config examples/delivery_reference/pyobfus.yaml \
  --level pro --crossfile-opacity \
  --opacity-config "$work/private/opacity.toml" \
  --bind-key-env PYOBFUS_DELIVERY_REFERENCE_KEY \
  --save-mapping "$work/private/mapping.json" \
  --build-report "$work/private/build.json" \
  --verify-syntax --jobs 1 --json

mkdir -p "$work/protected/storefront/data"
cp examples/delivery_reference/storefront/data/label.txt \
  "$work/protected/storefront/data/label.txt"

venv/bin/python "$work/protected/main.py" pro
# exits 0, matching the baseline:
# pricing-v1
# pro: 65.88

env -u PYOBFUS_DELIVERY_REFERENCE_KEY \
  venv/bin/python "$work/protected/main.py" pro
# exits 1 with LicenseBindingError

PYOBFUS_DELIVERY_REFERENCE_KEY="$(venv/bin/python -c 'import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())')" \
  venv/bin/python "$work/protected/main.py" pro
# exits 1 with OpacityRuntimeError
)
```

Only `protected/` is the delivery directory; keep `private/` (mapping,
report and opacity rules) and the trial HOME outside it. The generated code
reads the environment variable through `--bind-key-env`; `key_provider.py`
documents the same application-owned input name and contains no key. The
Community baseline does not use it.

The [Pro stage C acceptance record](../../docs/DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md#2026-11-16-pro-stage-c-local-trial-linux-cpython-312)
and [`pro_reference` / `test_delivery_reference_pro_pyinstaller`](../../integration_tests/test_packaging.py)
cover this configuration and its Linux PyInstaller onefile/onedir runs.
The opacity report recorded 6 eligible targets, 2 encrypted and 0 rejected.
The encrypted `quote_order` traceback frame was restored by name only, with
`original_line: null`. Frozen payload contents (PYZ) remain uninspected by
`--check-delivery`; frozen checks are not evidence of clean payload contents.
This recipe demonstrates the protected directory, not a clean target machine
or Pro-lane verification on Windows/macOS.

## Feedback

For real delivery problems, use the
[Delivery blocker / frozen format issue template](https://github.com/zhurong2020/pyobfus/issues/new?template=delivery_blocker.md).
This example is the shared reproduction baseline: reproduce against it when
possible and describe any minimal changes needed. Use synthetic inputs and
remove secrets and personal data; never attach licence keys, private keys,
mapping files or proprietary source.
