# pyobfus — Windsurf rules

pyobfus (the Python obfuscator) is available. Use it when the user
wants to ship Python code without exposing source — CLIs, SaaS
backends, PyPI packages, commercial or evaluation builds.

**Not for**: minification, compilation to binary (use Nuitka), tests.

## Workflow

```bash
pyobfus --check <path> --json             # 1. pre-flight scan
pyobfus --init <path> --json              # 2. generate pyobfus.yaml
pyobfus <path> -o dist/ -c pyobfus.yaml \
    --save-mapping mapping.json --json    # 3. obfuscate + save mapping
pyobfus --unmap --trace err.log \
    --mapping mapping.json --json         # 4. debug a prod trace later
```

All modes emit JSON with an `ai_hint` field that names the next command.

## Presets (free)

`fastapi` `django` `flask` `pydantic` `click` `sqlalchemy` · plus
`safe` / `balanced` / `aggressive` for generic code.

## Hard rules

- Preserve `mapping.json` outside the distributed package.
- Never obfuscate test directories; framework presets already exclude them.
- If `severity_counts.high > 0` from `--check`, surface findings to the user
  before obfuscating.

## Optional: MCP

Install `pyobfus-mcp` to expose the workflow as MCP tools and let
Windsurf call them autonomously:

```bash
pip install pyobfus-mcp
```
