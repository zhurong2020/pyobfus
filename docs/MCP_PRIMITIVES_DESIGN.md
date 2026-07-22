# MCP primitives design note

**Status**: research only; not implemented  
**Recorded**: 2026-07-22  
**Decision gate**: revisit after the launch wave produces real MCP-user feedback

This note records a possible evolution of `pyobfus-mcp` from a tools-only
server toward a clearer separation between MCP Tools, Resources, and Prompts.
It is inspired in part by the
[`open-and-async/mcp`](https://github.com/open-and-async/mcp) packaging model.
It does not add committed roadmap scope and must not displace the current
launch, metrics, or benchmark work.

Authoritative protocol references:

- [MCP server primitives overview](https://modelcontextprotocol.io/specification/2025-06-18/server/index)
- [Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources)
- [Prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)

## The separation

| Primitive | Primary control | Responsibility in pyobfus-mcp |
|---|---|---|
| Tools | Model-controlled | Compute or perform an operation against a specific project. |
| Resources | Application-controlled | Supply authoritative, normally read-only pyobfus context. |
| Prompts | User-controlled | Start a repeatable, human-visible workflow that may use Resources and Tools. |

The intended relationship is:

```text
user selects a Prompt
        -> client supplies relevant Resources
        -> model calls Tools
        -> Tools return status / ai_hint / next_tool
```

`next_tool` and Prompts solve different problems. A Prompt is the entry-point
playbook, including explanations and user decisions. `next_tool` is the
machine-readable handoff after a Tool has executed.

## Current Tool layer

The existing eight Tools remain the executable surface:

- `protect_project`
- `check_obfuscation_risks`
- `generate_pyobfus_config`
- `unmap_stack_trace`
- `list_presets`
- `explain_preset`
- `recommend_tier`
- `start_pro_trial`

Do not break their stable response contract: successful calls continue to
return `status`, `ai_hint`, and `next_tool`. `list_presets` and
`explain_preset` may overlap with future Resources, but must remain available
for compatibility.

## Candidate Resources

Resources should hold stable facts that an MCP client can browse or add to
model context without pretending that an operation has occurred.

| Candidate URI | Contents |
|---|---|
| `pyobfus://about` | Package roles: Core, MCP, and source-separated Pro. |
| `pyobfus://version` | Current package and supported-Python versions. |
| `pyobfus://threat-model` | Explicit protection claims and non-claims. |
| `pyobfus://presets` | Available presets and tier grouping. |
| `pyobfus://presets/{name}` | Parameterized details for one preset. |
| `pyobfus://frameworks` | Reflection-sensitive frameworks and preservation rules. |
| `pyobfus://security/mapping-handling` | Rules for storing and distributing reverse mappings. |

Benefits:

- one machine-readable source of truth for security boundaries;
- shorter Tool descriptions without losing important context;
- less need to call a Tool merely to read static documentation;
- more consistent answers across MCP clients;
- a safe target for Resource links returned by Tools.

The private contents of `mapping.json` must **not** become a generally listed
Resource. A mapping is sensitive reverse-engineering material. Any future
mapping access must stay explicit, local, path-scoped, and auditable.

## Candidate Prompts

Prompts should cover workflows that require explanation or a user decision.
They do not execute operations by themselves.

### `protect_project_safely`

1. Load the threat model and mapping-handling Resources.
2. Run `check_obfuscation_risks`.
3. Explain reflection and framework findings.
4. Confirm the output location before writes.
5. Run `protect_project` and inspect `verified`.
6. State which artifacts may be distributed and which must stay private.

### `debug_obfuscated_crash`

1. Warn that traces and mappings may contain sensitive data.
2. Use only the mapping path explicitly selected by the user.
3. Run `unmap_stack_trace`.
4. Distinguish successful identifier restoration from root-cause diagnosis.
5. Suggest the next debugging step without exposing the mapping.

### `choose_protection_profile`

1. Run the risk scan.
2. Load the preset and threat-model Resources.
3. Compare Community, framework-aware, and Pro choices.
4. Explain trade-offs before any commercial suggestion.
5. Let the user decide whether to generate a configuration.

## Security and compatibility constraints

- Keep a human confirmation point for writes, arbitrary verification commands,
  sensitive-file reads, and commercial actions.
- Validate Prompt arguments and treat all project content as untrusted input.
- Preserve the existing path-scope, rate-limit, redaction, and audit controls.
- Never embed reverse mappings in obfuscated output or generic Resources.
- Add capabilities without removing or renaming existing Tools.
- Test capability discovery plus `resources/list`, `resources/read`,
  `prompts/list`, and prompt argument validation separately from Tool tests.
- Treat client UI support as variable; Tools must remain independently usable.

## Evaluation plan

If launch feedback shows that users struggle to understand security boundaries
or choose the correct workflow, evaluate this in three small phases:

1. Add static Resources for version, threat model, presets, and mapping safety.
2. Add `protect_project_safely` and `debug_obfuscated_crash` Prompts.
3. Only then test whether Tool-returned Resource links improve agent behavior.

Success is not a larger primitive count. Success means fewer incorrect safety
claims, fewer misordered Tool calls, and fewer cases where users distribute a
mapping or unverified output by mistake.
