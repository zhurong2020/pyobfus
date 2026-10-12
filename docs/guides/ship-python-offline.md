---
description: Ship an obfuscated Python application to machines without internet access — what to stage, how to install the Pro runtime with pip --no-index, which key option fits which offline setup, and what each protects against.
---

# Ship an obfuscated Python application offline

This guide is for applications delivered to machines that cannot reach PyPI:
air-gapped sites, factory or hospital networks, customer servers behind strict
firewalls. Everything here was checked against pyobfus 0.7.0 and
`pyobfus-runtime` 0.1.1; the repository test
`integration_tests/test_offline_target.py` repeats the Pro steps on every CI run
(Linux and Windows).

## 1. Build, then keep private files out of what you ship

```bash
pyobfus src/ -o dist/ --save-mapping private/mapping.json --build-report private/build-report.json
pyobfus --check src/            # before you ship, not after
```

- **The mapping restores your original names.** Keep it outside `dist/`; the
  CLI warns if `--save-mapping` points inside the output directory. You need it
  to read customer tracebacks with `pyobfus --unmap`.
- **`--scrub-traceback` writes a private key next to each output file**
  (`<file>.py.scrub.key.pem`). Move those files out of `dist/` before you
  package it, and keep them to decode error IDs with `pyobfus-unscrub`.
- Ship `dist/`, not `src/`. A `.pyc`-only build is not protection: public
  decompilers recover source from nearly all CPython 3.8–3.14 bytecode.
- Optional, from other tools: `check-wheel-contents` for stray `.pyc` or
  test directories in a wheel, `gitleaks dir dist/` for credentials.

## 2. Community builds need nothing extra on the target

Obfuscated Community output is plain Python with no pyobfus dependency. Ship it
the way you already ship the application (a wheel, a folder, an embedded
Python, a PyInstaller or Nuitka bundle — see the
[PyInstaller](../PYINSTALLER_COOKBOOK.md) and
[Nuitka / Cython](../COMPILED_PACKAGING_COOKBOOK.md) cookbooks).

## 3. Pro builds need `pyobfus-runtime` on the target

Pro protections (encrypted functions, vault, expiry, device or key binding,
embedded data) generate code that imports the small redistributable
`pyobfus-runtime` package, never the builder. Your Pro licence permits
redistributing it with your artifact.

Stage it on a machine with internet access, for the target's platform and
Python version (the runtime depends on `cryptography`, which has platform
wheels):

```bash
pip download "pyobfus-runtime>=0.1.1,<1" -d wheelhouse \
    --only-binary=:all: --platform win_amd64 --python-version 3.12
```

Copy `wheelhouse/` with your application and install on the target without a
network:

```bash
python -m pip install --no-index --find-links wheelhouse pyobfus-runtime
```

For an embedded or vendored Python, unpack the same wheels into its
`site-packages` instead. Then run the protected program once on a clean
machine of the same kind before you send it; that is what the repository's
offline test does.

**These Pro options apply only to single-file builds or `--no-cross-file`
directory builds.** A default directory build skips them and prints which ones
it skipped; `--build-report` lists them under `disabled_transforms`.

## 4. Choose a key option for your offline setup

Encrypted functions (`--selective-opacity` / `--opacity-config`) need a key at
run time. Where that key lives decides what the encryption protects against.

| Setup | Option | Key location | Protects against | Does not protect against |
|---|---|---|---|---|
| Simple delivery | default | inside the artifact | casual reading of the file | anyone with the file: the key is beside the ciphertext |
| Air-gapped, known machines | `--bind-device-id <id>` (one build per machine) | derived from the target's machine id | copying the file to another machine | the operator of that machine |
| Site has its own licence server or key store | `--bind-key-env NAME`, application calls `pyobfus_runtime.set_key_provider(fn)` | supplied by your application at run time | anyone with the file but without your key | the operator of a machine you supplied the key to |

To get a target's machine id, run on that machine
`python -c "import pyobfus_runtime; print(pyobfus_runtime.current_machine_id())"`.

**Whoever runs the program with a valid key can see the decrypted code.** The
runtime decrypts in-process; `benchmarks/llm_resistance/key_exposure.py`
demonstrates this with a standard Python audit hook. Encryption here protects
the file at rest, not the running process. Logic that must stay secret from the
operator belongs on a server you control, or in a compiled layer (Nuitka,
Cython) as defence in depth.

`--fingerprint` (per-buyer key) only works with the default key location; with
`--bind-device` or `--bind-key-env` the CLI warns that it has no effect.

## 5. Expiry, renewal and revocation offline

- `--expire-hard YYYY-MM-DD` stops the program after a date;
  `--expire-warn-days N` warns before it. The date is fixed at build time, so
  **renewal means a new build**, and the check trusts the machine's clock.
- `--period N` limits the number of runs, counted in a local file on that machine (a determined user can reset it).
- There is **no remote revocation offline**: a copy that never connects keeps
  working until its expiry. If you need revocation, use `--bind-key-env` with a
  provider that asks your server, and decide what the application does when the
  server is unreachable (a grace period is a product decision, not a pyobfus
  feature).

## 6. Two licences, two boundaries

Your **pyobfus Pro licence** covers building protected artifacts and
redistributing `pyobfus-runtime` with them. **Your customer's licence for your
application** is yours to design and enforce; pyobfus provides building blocks
(expiry, device binding, an application key hook), not a licence server.

## Troubleshooting on the target

| Message | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'pyobfus_runtime'` | runtime not installed beside the artifact | install it from the staged wheelhouse |
| `ImportError: cannot import name 'provided_key'` or `TypeError: ... 'warn_days'` | runtime 0.1.0 with a 0.5.30+ artifact | install `pyobfus-runtime` 0.1.1 or later |
| `LicenseBindingError: no key provider registered ...` | `--bind-key-env` build, no key supplied | register the provider before importing the protected module, or set the variable |
| `OpacityRuntimeError` on first call | wrong key, wrong machine, or a modified file | check the key source or the machine id the build was bound to |

Read obfuscated tracebacks with your private mapping:
`pyobfus --unmap trace.txt --mapping private/mapping.json`.
