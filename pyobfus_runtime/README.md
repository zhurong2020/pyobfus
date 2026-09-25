# pyobfus-runtime

Minimal runtime support for artifacts built with pyobfus Pro. This package does
not contain the obfuscator, build-time transformers, payment code, or licence
verification client, and it does not require a pyobfus licence key at runtime.

After its first release, install it in the environment where a protected
artifact runs:

```bash
python -m pip install pyobfus-runtime
```

Creating protected artifacts still requires a valid pyobfus Pro licence.
The first runtime release is `0.1.0`; install it in the environment where a
protected artifact runs. The builder declares `pyobfus-runtime>=0.1,<1`, and a
provenance manifest written with `--provenance-manifest` records that
requirement for any artifact that needs it.

A valid pyobfus Pro licence permits redistribution of this runtime with an
artifact produced by Pro. Packaging-only transformations such as vendoring,
byte-compilation, or application bundling are permitted when runtime behaviour
and the included licence notice remain unchanged. See `LICENSE` for the full
terms.
