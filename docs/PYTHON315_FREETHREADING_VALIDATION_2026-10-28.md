# Python 3.15 free-threaded validation: bounded Linux run

Date: 2026-10-28. This is one local validation of the current `main` checkout,
not a released-package or cross-platform support claim. The public Core
version remains 0.10.0; P0/P2 changes in `main` have not been released.

## Isolated interpreter and dependencies

The first two download attempts were stopped because transfer rates fell to
single-digit KiB/s: a PyPI `uv` wheel, then APT's first `.deb`. On retry,
direct requests to the configured deadsnakes APT repository completed. Three
matching `3.15.2-1+noble1` packages (`python3.15-nogil`,
`libpython3.15-nogil`, `libpython3.15-stdlib`) were checked against the SHA-512
values in APT metadata and extracted under `/tmp`; no system package was
installed. Python reported `3.15.2 free-threading build`,
`Py_GIL_DISABLED=1`, and `sys._is_gil_enabled() == False`.

The existing Python 3.12 `cryptography` extension could not load under 3.15t.
The isolated run used the PyPI `cryptography==50.0.2` Linux wheel tagged for
`abi3t` and `cffi==2.1.1` tagged `cp315t`; their SHA-256 values matched the
PyPI release metadata. Both imported while the GIL remained disabled. Core
CLI smoke used the current checkout, system Click 8.1.6/PyYAML 6.0.1 and these
isolated wheels. Pytest was borrowed from the local 3.12 development venv as
pure Python test tooling; plugin autoload was disabled. This is not a clean
`pip install` of the public wheel under 3.15t.

## Outcomes

- Community multi-file example: current Core built four files; original and
  protected output matched exactly, and the protected run ended with GIL
  disabled.
- Packaging fixture: current Core built six files; protected `pro` run printed
  `pro: 65.88`. An intentional unknown-tier error mapped all three project
  frames to original files and lines with `unmatched_names=[]`.
- Delivery check after running the protected fixture: all five generated
  `.pyc` files matched adjacent source recorded in the build report; `unknown=0`.
  This is source/body evidence, not confidentiality proof.
- Runtime suite plus targeted P0/delivery tests: **44 passed**. Separate
  opacity, vault, traceback-encryption and seal runtime tests: **68 passed**;
  GIL remained disabled after the latter run.
- Two threads each performed 200 repeated imports and
  `pyobfus_runtime.provided_key()` calls against one registered synthetic
  provider: **400/400 matched**, no exception, GIL still disabled. This does
  not establish general thread safety for arbitrary protected applications.

## Explicit L3 boundary

Cross-file L3 **still rejects free-threaded CPython during preflight** with
`crossfile_opacity does not yet support free-threaded CPython builds.` The
bounded attempt to run L3 build tests under 3.15t showed 17 tests that expect
successful builds failing at that guard; 64 other tests passed and one skipped.
These are expected failures against an intentionally unsupported mode. No
encrypted cross-file L3 artifact was built or run under 3.15t, and this run
does not justify removing the guard. The same-implementation/minor/GIL-mode
artifact identity remains enforced.

## Follow-up gate

Keep cross-file L3 on 3.15t unsupported. If a real application needs it,
review the bytecode/marshal and runtime contract, then validate correct,
missing and wrong keys, traceback restoration, target-only installation,
concurrent calls and same-mode artifact identity before changing preflight.
For broader Core 3.15t support, repeat the smoke from a clean public-wheel
environment and on another OS; do not infer those results from this one Linux
checkout. No new CI matrix or private repository workflow was created.

References: [Python free-threading guide](https://docs.python.org/3.15/howto/free-threading-python.html),
[cryptography 50.0.2 release files](https://pypi.org/project/cryptography/50.0.2/),
[cffi release files](https://pypi.org/project/cffi/).
