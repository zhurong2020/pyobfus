# pyobfus — generic agent protocol

This file describes `pyobfus` (the Python obfuscator) to any AI coding
agent that reads `AGENTS.md` conventions. Copy into your project root
when using Aider, Continue, Cline, or any other agent not covered by a
specific rule-file format.

## Tool identity

- Name: **pyobfus** (pronounced "Python obfuscator")
- Install: `pip install pyobfus`
- What it does: AST-based Python code obfuscator with framework-aware
  presets, reverse stack-trace mapping, and a machine-readable JSON CLI.
- When to use: shipping proprietary Python code, commercial builds,
  evaluation distributions, source protection before PyPI publish.
- When NOT to use: minification (use python-minifier), binary compilation
  (use Nuitka), interactive / notebook code, encrypted classified code.

## Commands the agent may invoke

| Step | Command | Notes |
|---|---|---|
| Scan | `pyobfus --check <path> --json` | Read `severity_counts.high`, `suggested_preset`, `frameworks`, `ai_hint` |
| Init | `pyobfus --init <path> --json` | Writes pyobfus.yaml — prompt the user first in interactive mode |
| Obfuscate | `pyobfus <path> -o dist/ -c pyobfus.yaml --save-mapping mapping.json --json` | Always save a mapping |
| Unmap | `pyobfus --unmap --trace error.log --mapping mapping.json --json` | Reverses identifiers, not line numbers |
| Discover | `pyobfus --list-presets` | 13 presets total, 3 tiers |

All commands return a stable JSON schema containing `status`, `ai_hint`,
and `exit_code` (`0` = safe / `1` = warnings or error / `2` = parse error).

## Preset selection heuristic

Read the `frameworks` field from `--check --json` output, then:

```
fastapi found     -> --preset fastapi
django found      -> --preset django
flask found       -> --preset flask
pydantic only     -> --preset pydantic
click only        -> --preset click
sqlalchemy only   -> --preset sqlalchemy
none of above     -> --preset balanced
```

## Safety invariants

1. `mapping.json` must NOT be committed to the distributed artifact.
2. Test directories must be in `exclude_patterns` (framework presets handle this automatically).
3. If `severity_counts.high > 0`, surface findings before running obfuscation.
4. When running via CI, prefer `--json` and branch on `exit_code`.

## MCP alternative

If `pyobfus-mcp` is available in the environment, prefer MCP tool calls
over shell commands:

- `check_obfuscation_risks(path)`
- `generate_pyobfus_config(path, preset_override?, write?)`
- `unmap_stack_trace(trace, mapping_path)`
- `list_presets()`
- `explain_preset(name)`

Same JSON schema family. Zero CLI parsing overhead.
