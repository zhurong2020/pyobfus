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
Until the first runtime release is published, install the wheel built from this
directory; do not release a builder that emits `pyobfus_runtime` imports first.
