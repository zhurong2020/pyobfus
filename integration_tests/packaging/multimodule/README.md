# Multi-module packaging fixture

A small stdlib-only project for `integration_tests/test_packaging.py`:
a package with a subpackage, relative imports (`.` and `..`), a class used
across modules, and an entry script outside the package. The test obfuscates
the whole directory, then freezes it with PyInstaller `--onefile` and compiles
it with Nuitka `--mode=standalone`, and compares the output with the original.
