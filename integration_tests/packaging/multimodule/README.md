# Multi-module packaging fixture

A small stdlib-only project for `integration_tests/test_packaging.py`:
a package with a subpackage, relative imports (`.` and `..`), a class used
across modules, and an entry script outside the package. The test obfuscates
the whole directory, then freezes it with PyInstaller `--onefile` and compiles
it with Nuitka `--mode=standalone`, and compares the output with the original.

For opt-in local public-wheel acceptance, run
`scripts/validate_packaged_delivery.py --work-dir /tmp/new-delivery-run`
with the target environment's Python from the repository root. It uses this
fixture with a resource file and checks PyInstaller onedir and onefile.
`--l3` additionally exercises an application key with an isolated local trial;
it never reads the developer's real trial state. Keep the work directory
private: it holds mapping, build records and logs. See
[`docs/ENGINEERING_VALIDATION_2026-10-30.md`](../../../docs/ENGINEERING_VALIDATION_2026-10-30.md)
for exact tested versions, limitations and reproducible commands. This does
not add new jobs to the hosted packaging matrix.
