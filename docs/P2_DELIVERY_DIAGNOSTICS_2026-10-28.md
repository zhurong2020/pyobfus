# P2 delivery diagnostics: bounded bytecode evidence and frozen packages

Status: implemented on the development branch; **not released in Core 0.10.0**.

`--check-delivery` now accepts a directory, wheel, or a file with PE, ELF, or
Mach-O magic. It still checks ordinary delivered files for the known mapping,
private-key, original-source, build-output, and L3 mistakes. The new
`inspection` object in JSON format version 1 reports what it could and could
not inspect.

## Bytecode origin

For at most 64 `.pyc`/`.pyo` files, the checker looks for an adjacent `.py`
using a standard `__pycache__` or legacy sibling name. It requires the
current interpreter's bytecode magic, recompiles that delivered source under
up to three optimization levels, and compares the **entire bytecode body** to
the delivered file. It never unmarshals or executes delivered bytecode.
Sources over 1 MiB are left `unknown`.

The result is one of:

| JSON status | Meaning |
|---|---|
| `matched_recorded_output` | Exact bytecode body matches adjacent source whose SHA-256 occurs in the supplied build report outputs. This is build evidence, not a signature. |
| `matched_adjacent_source` | Exact body matches adjacent source, but that source is not in the supplied report (or no report was supplied). Protection is not established. |
| `unknown` | Missing source, different Python bytecode version/build path, malformed bytecode, comparison limit, or body mismatch. Origin remains unproved. |

Any `unknown` produces a medium finding and overall `warn`; the existing
`delivery.bytecode_present` information finding remains. This avoids a clean
looking status for bytecode whose origin is unknown. A comparison match does
not prove confidentiality or that no other original source exists in the
package. The current checker does not validate `.pyc` timestamp/hash
invalidation headers; only the body is compared.

## Frozen executables

For a standalone executable, the result is `warn` with
`delivery.frozen_uninspected`; `inspection.frozen_executables` reports one
found and zero inspected. For an onedir package, the same warning is added
when a top-level executable is recognized by magic. PE/ELF/Mach-O detection
identifies an outer container, **not** the packager or its embedded contents.
This does not unpack PyInstaller PYZ/PKG or Nuitka payloads, and does not
validate mapping, keys or original source embedded inside them. Use the
packager's archive tools and independent staging checks for that work.

Warnings retain the existing CLI exit code 0 contract; the machine-readable
`status` and finding code distinguish them from `ok`. High findings still
exit 1, and malformed targets exit 2. No new CI matrix or private repository
workflow was added.

## Local acceptance

- A real protected output compiled to `.pyc` reports
  `matched_recorded_output`.
- A malformed bytecode header returns `unknown` and `warn` without
  deserialization.
- PE, ELF and Mach-O outer files, plus an onedir executable, return
  `frozen_uninspected` and `warn` without claiming to inspect inner code.

Sources for the safety boundary:
[Python `marshal` documentation](https://docs.python.org/3/library/marshal.html),
[Python `py_compile` documentation](https://docs.python.org/3/library/py_compile.html),
and [PyInstaller archive viewer](https://pyinstaller.org/en/latest/advanced-topics.html).
