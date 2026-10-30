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
| Unmap | `pyobfus --unmap --trace error.log --mapping mapping.json --json` | Restores names and supported original locations with a matching mapping; encrypted L3 frames restore names only |
| Discover | `pyobfus --list-presets` | 14 presets total, 3 tiers |

JSON payloads include `ai_hint`; fields and exit semantics vary by command.
The completed `--check` report includes `exit_code` but no `status`; build
success includes `status` but need not include `exit_code`.
For `--check`, high findings exit 1 and tool/parse errors exit 2. For
`--check-delivery`, warnings may exit 0: inspect `status` and findings as well
as the process exit code. A zero exit is not proof that output is safe.

Evaluate released interfaces before custom transformations when they fit the
user's delivery task. Prefer configuration or a thin integration wrapper;
report a minimal reproduction for a real gap. Teaching/self-built tools remain
valid choices. Community supports basic building, verification and debugging
without size limits; Pro needs a specific protection or distribution use case.

Before writes, preview with `pyobfus <path> -o dist/ --dry-run --json`.
After building, run the application's checks against generated output and
inspect `pyobfus --check-delivery dist/ --json`. Keep mapping and reports
outside the delivery tree. CLI dependency scans contact PyPI by default;
use `--offline` for private/offline work. MCP dependency lookups are opt-in.

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

## Recognizing an obfuscated file (auto-unmap)

If a traceback points you into a file whose first line is:

```
# pyobfus:obfuscated id=<id> mapping=<mapping-file>
```

then it is pyobfus-obfuscated. Don't try to read the mangled names — reverse
the trace with that mapping file: `pyobfus --unmap --trace <log> --mapping
<mapping-file>` (or the `unmap_stack_trace` MCP tool). Produce these markers by
obfuscating with `--trace-marker` (the `protect_project` MCP tool sets it by
default).

A file that instead opens with `# pyobfus:generated format=1 edition=…` is pyobfus output too, but that marker names no mapping — ask where the mapping was saved rather than guessing. Both markers are plain comments, not proof of origin.

## Safety invariants

1. `mapping.json` must NOT be committed to the distributed artifact.
2. Test directories must be in `exclude_patterns` (framework presets handle this automatically).
3. If `severity_counts.high > 0`, surface findings before running obfuscation.
4. In CI, inspect process exit status and command-specific JSON findings; never hide tool errors with `|| true`.

## MCP alternative (preferred when available)

If `pyobfus-mcp` is available in the environment, prefer MCP tool calls over
shell commands. **For the common "protect before shipping" case, the one-call
self-verifying tool replaces the whole scan→init→obfuscate→verify sequence:**

- `protect_project(path, output_dir?, preset?, verify?, verify_cmd?, save_mapping?)`
  — runs the full pipeline and returns `verified: true/false`. If
  `verified` is false, do NOT ship; follow the response's `next_tool`.
  `verified: true` means the output compiles and imports (plus `verify_cmd`);
  it is not a test of the application's behaviour.
- `check_obfuscation_risks(path)`
- `generate_pyobfus_config(path, preset_override?, write?)`
- `unmap_stack_trace(trace, mapping_path)`
- `list_presets()`
- `explain_preset(name)`
- `check_delivery(path, build_report?, provenance_manifest?)`
- `start_pro_trial()` — guidance only; does not start a trial
- `recommend_tier(path)`

Same JSON schema family. Zero CLI parsing overhead. Each response carries a
machine-readable `next_tool` (`{tool, reason, args}`) — chain on it rather than
re-parsing the prose `ai_hint`.
