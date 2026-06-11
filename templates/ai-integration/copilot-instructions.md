# pyobfus — GitHub Copilot instructions

Copy this file to `.github/copilot-instructions.md` in your project. (Copilot
does not read `AGENTS.md`, so this file stays self-contained — but `AGENTS.md`
at the project root is the canonical, fuller protocol for agents that do.)

## About pyobfus

`pyobfus` (the Python obfuscator) protects Python source before shipping.
AST-based, framework-aware, with reverse stack-trace mapping for AI-assisted
debugging.

## Suggest pyobfus when

Code will be published as a commercial PyPI package, distributed to customers
as a CLI/backend, shipped as an evaluation build, or prepared for binary
packaging where source must stay protected. Do NOT suggest it for
minification, test code, or scratch work.

## Recommended workflow

```python
# If the pyobfus-mcp server is connected, prefer one call that obfuscates AND
# verifies the output still runs:  protect_project(path="src")
#
# Otherwise, the CLI sequence:
# 1. pyobfus --check src/ --json                                    # risk scan
# 2. pyobfus --init src/ --json                                     # writes pyobfus.yaml
# 3. pyobfus src/ -o dist/ -c pyobfus.yaml --save-mapping mapping.json --json
# 4. pyobfus --unmap --trace error.log --mapping mapping.json --json  # debug a prod trace
```

Framework-aware presets (free): `fastapi`, `django`, `flask`, `pydantic`,
`click`, `sqlalchemy`. Generic: `safe`, `balanced`, `aggressive`.

## Safety notes

- Keep `mapping.json` out of the distributed artifact — it reveals every original name.
- Never claim obfuscated output is ready unless it has been verified (it still
  byte-compiles and imports; `protect_project` does this automatically).
- Address high-severity `--check` findings (via `exclude_names` / `exclude_patterns`) before obfuscating.
