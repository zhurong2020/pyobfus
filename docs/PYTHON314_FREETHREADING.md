# Python 3.14 free-threading compatibility

Python 3.14 graduated free-threading (PEP 779, the GIL-optional build) from
experimental to officially supported. pyobfus already claims `>=3.9,<3.15`
support, but that claim had never actually been exercised against a
free-threaded (`python3.14t`) build — this document records the verification.

## What was tested

A [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
free-threaded Python 3.14.7 build (`cpython-3.14.7+20260814-x86_64-unknown-linux-gnu-freethreaded+pgo+lto`),
no system install required. Confirmed the GIL is actually disabled before
testing anything else:

```bash
python3.14t -c "import sys; print(sys._is_gil_enabled())"
# False
```

`pip install -e ".[dev]"` into a venv built from that interpreter, then:

1. **Full core test suite**: `python3.14t -m pytest tests/ -q --no-cov` —
   **1169 passed, 1 skipped**, including every Pro-runtime-focused file:
   `test_license_binding.py`, `test_vault_runtime.py` (Runtime String Vault),
   `test_scrub_runtime.py` (traceback encryption runtime),
   `test_seal_runtime.py` (integrity seal), `test_opacity_runtime.py`.
2. **Real end-to-end smoke test**, not just unit tests — obfuscated a sample
   module with `--seal-code --scrub-traceback` and executed the *protected
   artifact itself* under `python3.14t`:
   - Normal execution path: correct output, confirmed `sys._is_gil_enabled()`
     was still `False` inside the running protected script (i.e. it wasn't
     silently falling back to a GIL build).
   - Exception path: triggered a real `KeyError` inside the protected
     artifact, confirmed the RSA-2048-OAEP + AES-256-GCM hybrid encryption
     hook fired correctly (`PYOBFUS-ERR:<encrypted blob>` on stderr instead
     of a raw traceback, exit code 1), then decrypted it back with
     `pyobfus-unscrub --key <sidecar>.pem` and got the original traceback
     back — full round trip under free-threading.

## Result

No failures, no free-threading-specific crashes, no GIL-assumption
violations surfaced by either the test suite or the manual seal/scrub
round-trip. `pyobfus` 0.5.15 works correctly on `python3.14t` for the
scenarios tested above.

## Honest scope — what this does and doesn't cover

- **What it covers**: import-time behavior, the full existing test suite
  (which already exercises the Pro runtime components' logic extensively),
  and a real single-process obfuscate → execute → crash → decrypt round
  trip. This is the usage pattern pyobfus-protected code actually runs in —
  a script or an imported module, not a shared mutable service.
- **What it doesn't cover**: free-threading's actual point is safe
  *concurrent* execution across threads without GIL serialization. This
  verification did not specifically stress-test concurrent multi-threaded
  access to the Pro runtime's module-level state (the Runtime String Vault's
  cache, license-binding checks) from multiple threads simultaneously — that
  scenario doesn't arise in pyobfus's normal usage (obfuscated output is a
  script/library, not a long-running multi-threaded service holding shared
  vault state), so it wasn't a priority for this pass. If you embed
  pyobfus-protected code inside a heavily multi-threaded free-threaded
  application and call into the same protected module from multiple threads
  concurrently, this document does not claim that's been verified safe.
- Point-in-time result: `pyobfus` 0.5.15 against python-build-standalone's
  `20260814` release of CPython 3.14.7. Re-verify after any release that
  touches the Pro runtime's module-level state.

## Reproducing this yourself

No sudo/root or system package install needed — python-build-standalone
ships self-contained binaries:

```bash
curl -fL -o cpython-314t.tar.zst \
  "https://github.com/astral-sh/python-build-standalone/releases/latest/download/cpython-3.14.7+$(date +%Y%m%d)-x86_64-unknown-linux-gnu-freethreaded+pgo+lto-full.tar.zst"
# (check the actual latest release tag/asset name at
# https://github.com/astral-sh/python-build-standalone/releases — asset
# names are pinned to a specific build date)

python3 -m venv decompress_venv && decompress_venv/bin/pip install zstandard
decompress_venv/bin/python3 -c "
import zstandard
with open('cpython-314t.tar.zst', 'rb') as i, open('cpython-314t.tar', 'wb') as o:
    zstandard.ZstdDecompressor().copy_stream(i, o)
"
tar -xf cpython-314t.tar
python/install/bin/python3.14t -m venv test314t_venv
test314t_venv/bin/pip install -e ".[dev]"
test314t_venv/bin/python3.14t -m pytest tests/ -q --no-cov
```
