# Open-source Python obfuscators on a multi-module project

Opy, pyminifier, python-minifier and python-obfuscator are the open-source
tools most often suggested for "obfuscate Python but keep `.py` output". This
page records what each one did with the same small multi-module project on
the same machine, including where pyobfus itself failed.

**Review date:** 2026-10-11. **Platform:** Linux x86_64, CPython 3.12.3. Every
tool was installed from PyPI into its own virtual environment and run with its
default settings first. These are results for one project and one platform,
not a general verdict on any tool. See the
[comparison scope and disclaimer](../COMPARISON.md).

## The test project

The project was the stdlib-only fixture that pyobfus's packaging lane uses,
[`integration_tests/packaging/multimodule/`](https://github.com/zhurong2020/pyobfus/tree/main/integration_tests/packaging/multimodule).
It has a package with a subpackage, `.` and `..` relative imports, a class
used from another module, f-strings, and an entry script outside the package.
We added one module with Python 3.12 syntax and a second entry script that
imports it:

```python
type Pair[T] = tuple[T, T]


def first_of[T](items: list[T]) -> T:
    return items[0]


def describe(order):
    match order:
        case {"tier": tier, "total": total} if (rounded := round(total, 1)) > 0:
            return f"{tier}: {f'{rounded:.1f}'}"
        case _:
            return "empty"
```

A run passed when the output printed exactly what the original printed for
three pricing tiers and for the Python 3.12 entry script. We also checked
whether the original names of module-level functions and classes, such as
`quote_order` and `DiscountPolicy`, were still in the output.

## Results

| Tool and version (PyPI) | Last release | Multi-module project | Python 3.12 module | Module-level names |
|---|---|---|---|---|
| **pyobfus 0.6.1** | 2026-10-10 | Passed | **Failed:** `NameError` (directory build dropped `[T]` from `def first_of[T]`) | Renamed across modules |
| pyobfus, current `main` | not released | Passed | Passed ([fix](https://github.com/zhurong2020/pyobfus/pull/78)) | Renamed across modules |
| **Opy 1.1.28** | 2018-01-04 | Failed: `NameError` | Failed: `SyntaxError` | Renamed, including file and package names |
| **pyminifier 2.1** | 2014-05-31 | Not run: install fails | Not run | — |
| **python-minifier 3.4.0** | 2026-09-29 | Passed (default) | Passed (default) | Kept by default |
| python-minifier, `--rename-globals` | | Failed: `ImportError` | Not reached | Renamed per file |
| **python-obfuscator 0.1.0** | 2026-04-03 | Failed: `ImportError` | Failed: `SyntaxError` | Renamed per file |

### pyobfus

Directory builds renamed module-level names consistently across modules and
rewrote the imports, and the multi-module part matched the original output.
On 0.6.1 the Python 3.12 module failed: a directory build dropped the PEP 695
type parameter list from renamed functions and classes, so `def first_of[T]`
became `def I1(items: list[T]) -> T` and the import raised `NameError`.
Single-file builds were not affected. We found this defect while preparing
this page. It is fixed on `main` and will ship in the next release; until then,
build Python 3.12 generics as single files or exclude those names.

### Opy

Opy renames identifiers across all modules of a project, including module,
file and package names, and can obfuscate string literals. It is configured
through a Python file that Opy executes. The PyPI release is from January
2018; the repository's last code change is from December 2018.

With its default configuration the output failed with `NameError`, because
the generated code calls a string-decoding helper for f-strings that it never
defines. With string obfuscation turned off and the Python 3.12 module
removed, the output still failed with `NameError`: names referenced inside
f-strings, such as `f"{tier}"`, were not renamed, and `__all__` kept the old
names. The Python 3.12 module failed with `SyntaxError`, because the soft
keyword `match` was renamed like an ordinary name.

### pyminifier

`pip install pyminifier` failed on CPython 3.12: its build step requires the
`2to3` tool, which recent Python versions no longer provide. The last release
is from 2014. We did not try older interpreters.

### python-minifier

python-minifier is actively maintained and supports a wide range of Python
versions. Its default settings passed both checks, including the Python 3.12
syntax, and cut the project from 1,936 to 1,531 bytes. It is a minifier rather than an
obfuscator: by default it shortens local names and keeps module-level
functions and classes under their original names, which is what keeps imports
between modules working. With `--rename-globals`, each file is processed on
its own, so the first cross-module import failed with `ImportError`.

If your goal is smaller source rather than hiding names, python-minifier is a
well-maintained choice and can be run after pyobfus.

### python-obfuscator

python-obfuscator (command `pyobfuscate`) takes one file at a time and
combines identifier renaming, hexadecimal string encoding, dead-code
insertion and an `exec` wrapper; each technique can be turned off. Renaming
is per file, so the first cross-module import failed with `ImportError`.
With renaming turned off, the Python 3.12 module still failed with
`SyntaxError`: the string encoder replaced the string keys in a `match`
pattern with function calls, which patterns do not allow. Code wrapped in
`exec` also reports tracebacks against `<string>` instead of a file.

## About "opy2"

AI assistants sometimes recommend "opy2". On 2026-10-11 there was no PyPI
package with that name, and the GitHub repositories with that name were not
obfuscators. The recommendation most likely refers to Opy.

## Reproduce it

```bash
git clone https://github.com/zhurong2020/pyobfus
cp -r pyobfus/integration_tests/packaging/multimodule proj
# add proj/storefront/modern.py (above) and a script that imports it

python -m venv v && v/bin/pip install pyobfus
v/bin/pyobfus proj -o out
cd out && python main.py pro
```

For the other tools, use a separate virtual environment for each:

- **Opy:** `python opy.py proj out opy_config.txt`, using the config file
  shipped in the package.
- **python-minifier:** `pyminify proj --in-place` on a copy of the project.
- **python-obfuscator:** `pyobfuscate -i <file>` for each file. It writes
  the result under `obfuscated/`.

---

Part of the [pyobfus tool comparison](../COMPARISON.md). For browser-based
tools and other loaders see [other tools](other-tools.md).
