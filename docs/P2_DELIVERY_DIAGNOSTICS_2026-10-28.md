# P2 delivery diagnostics: bounded bytecode evidence and frozen packages

Status: merged via [PR #156](https://github.com/zhurong2020/pyobfus/pull/156)
as `5b26085` after 44 successful and 2 skipped checks; **released in Core
0.11.0**. The original October 28 validation used the then-unreleased change;
see [release verification](CORE_0_11_0_RELEASE_2026-10-29.md).

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

### Unreleased robustness changes (2026-10-30)

The current checkout aborts incomplete inspection with CLI exit 2 (MCP
`InvalidInput`) for unsafe/duplicate wheel paths, external or directory
symlinks, special files, malformed evidence shapes and resource limits.
In-root regular-file symlinks remain supported. Limits are 100,000 entries,
256 MiB per entry, 1 GiB total content, and 20 MiB per evidence JSON. No
partial result is reported as clean. These changes are **not in 0.11.0**.
See the [engineering validation](ENGINEERING_VALIDATION_2026-10-30.md).

### Original 0.11.0 acceptance

- A real protected output compiled to `.pyc` reports
  `matched_recorded_output`.
- A malformed bytecode header returns `unknown` and `warn` without
  deserialization.
- PE, ELF and Mach-O outer files, plus an onedir executable, return
  `frozen_uninspected` and `warn` without claiming to inspect inner code.
- P1's real Linux PyInstaller onedir/onefile and Nuitka onefile artifacts
  returned `warn` with `frozen_uninspected`.

Local full-suite results: Core 4,652 passed/55 skipped; MCP 153 passed;
integration 352 passed/10 skipped; runtime 24 passed; `scripts/check.sh`
passed. After tightening PE/ELF header validation, 19 targeted delivery
tests and `scripts/check.sh` passed again. The PR's required CI result and
CodeQL both passed.

Sources for the safety boundary:
[Python `marshal` documentation](https://docs.python.org/3/library/marshal.html),
[Python `py_compile` documentation](https://docs.python.org/3/library/py_compile.html),
and [PyInstaller archive viewer](https://pyinstaller.org/en/latest/advanced-topics.html).


## Bytecode comparison canonicalisation

The exact-byte comparison has a bounded pure-bytes fallback (2026-11-15).
Marshal reference flags and indices can vary with process state. Both the fresh
compilation and delivered body are parsed into bytes with FLAG_REF cleared and
TYPE_REF expanded. Delivered bytes are never unmarshalled, imported or executed.
The current interpreter's magic and the same candidate filename and optimization
level are still required. JSON fields and match reasons remain unchanged.

The implementation was checked against CPython `Python/marshal.c` tags v3.9.0,
v3.10.0, v3.11.0, v3.12.0, v3.13.0, v3.14.0 and v3.15.0
([CPython source](https://github.com/python/cpython/blob/v3.15.0/Python/marshal.c)).
Leaf `r_ref` inserts after reading its payload; containers insert or reserve
before reading children (`r_ref_reserve` / `r_ref_insert` for code, frozen
containers and slices). The parser uses that same index order, publishing spans
only after completion; recursive references fail closed. Singleton tags do not
add reference slots, even when flagged, matching the reader.

Code layouts use six raw integers and eight object fields before firstlineno
on 3.9/3.10, five integers and eight objects on 3.11–3.15, then one or two
line/exception table objects respectively. Slice is supported on 3.14+, and
frozendict on 3.15+. Other supported marshal scalar/container encodings retain
their bytes; this is not general Python object equality.

Unknown tags, incomplete or trailing data, invalid/unresolved references, depth
over 200, counts or work above min(input bytes, 1,000,000), input above 16 MiB,
or output above min(8 × input bytes, 16 MiB) fail closed to unknown origin.
References store spans in a single bounded output buffer rather than copied
trees. Existing source-size and comparison-count limits remain in force.
