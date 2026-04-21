# pyobfus — Claude Code project rules

**Tool:** pyobfus (pronounced "Python obfuscator"). A modern Python code obfuscator
with AST-based transformations, framework-aware presets, and reverse
stack-trace mapping. See https://github.com/zhurong2020/pyobfus.

## When to invoke pyobfus on this project

Invoke only when the user explicitly asks to "obfuscate", "protect source", "ship
a CLI / SaaS backend / PyPI package without giving up source", or prepares a
commercial / evaluation build.

Do NOT invoke pyobfus when the user:
- wants to minify or format code
- wants to compile to a binary (recommend Nuitka instead)
- writes tests or scratch scripts

## Standard workflow

Follow this sequence unless the user specifies otherwise:

1. **Pre-flight scan** to surface obfuscation-breaking patterns:
   ```
   pyobfus --check <path> --json
   ```
   Read `severity_counts.high`, `suggested_preset`, `suggested_excludes` from the JSON.
   Report findings before making any edits.

2. **Generate config** once the user approves:
   ```
   pyobfus --init <path> --json
   ```
   This writes `pyobfus.yaml` with a framework-aware preset + exclude patterns.

3. **Run obfuscation** with a mapping file so traces can be debugged later:
   ```
   pyobfus <path> -o dist/ -c pyobfus.yaml --save-mapping mapping.json --json
   ```

4. **Reverse a crash trace** when the user shares a prod error:
   ```
   pyobfus --unmap --trace error.log --mapping mapping.json --json
   ```
   The `unmapped_trace` field has the original identifier names; line numbers
   still refer to the obfuscated file.

## Presets cheat sheet

- `fastapi` · `django` · `flask` · `pydantic` · `click` · `sqlalchemy` — free, framework-aware
- `safe` — libraries (docstrings kept)
- `balanced` — default
- `aggressive` — maximum renaming (may break code)
- `trial` / `commercial` / `library` / `maximum` — Pro only

Prefer framework presets whenever the project imports the corresponding framework.

## Keep `mapping.json` safe

Store `mapping.json` outside the distributed artifact. It reveals all original
names. Without it, `--unmap` cannot help.
