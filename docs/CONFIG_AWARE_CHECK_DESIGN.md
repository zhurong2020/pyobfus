# Config-aware `--check` — implementation plan

Status: implementation complete on `main`; versioned as the local 0.5.18 / MCP
0.3.9 release candidate pending the final publish gate. Follows
`docs/FEATURE_EXPANSION_RESEARCH_2026-08-26.md` (candidate 1, GO/P1) and turns
its research decisions into a concrete, code-grounded plan. The implementation
gate was opened by the user on 2026-08-28; this document remains the contract
and review checklist for the held release.

Release boundary confirmed 2026-08-28: this version contains config-aware
`--check` only. The dry-run plan and syntax-only verification previews below
remain separate future increments. Do not bump versions, tag, or publish until
the user explicitly approves the release after reviewing tests and timing.

The config-resolution plumbing introduced by this plan is the prerequisite for
candidate 2 (`--dry-run --json` plan object), so that is sketched at the end.

## Problem being solved

`pyobfus --check PATH` today runs `PreflightChecker(check_dependencies=True,
offline=...)` and never looks at any obfuscation config
(`pyobfus/cli.py::_handle_check`, ~line 2048). An actual build, by contrast,
auto-discovers `pyobfus.yaml` / `.pyobfus.yaml`
and applies its `exclude_patterns` (`main()` ~line 546-583,
`config_validator.find_config_file`).

Consequences:

- `--check` scans files the build will never obfuscate (`tests/`, generated
  code, vendored trees) and reports risks in them, inflating the risk count and
  producing false "high-risk" `exit_code == 1` results in CI.
- A `getattr(obj, "route")` finding stays MEDIUM even when `route` is already in
  the config's `exclude_names` — the check has no way to know it is mitigated.
- P2-29 already recorded this exact gap: "後續機會（未併入本輪）：`--check` 接入
  已配置 `--config` / `exclude_patterns` 以減少真實組合的誤報".

## Non-goals (from the research decision)

- No new transforms, no new severity levels.
- Do not change `severity_counts`, `exit_code`, or the shape of `risks[]` for
  existing consumers (VS Code `diagnostics/diagnosticsProvider.ts` iterates
  `report.risks` and reads `.file/.line/.col/.category/.severity/.message`; MCP
  `check_obfuscation_risks` returns `report.to_dict()` almost verbatim).
- All JSON additions are additive keys.
- Excluded-file findings are **bucketed separately, never silently dropped**.
- The dependency-hallucination advisory stays project-level and is unaffected by
  source excludes.
- Never emit a "compatible" verdict from static scanning.

## CLI surface

`--check` starts honoring the config inputs it currently ignores:

| Flag | Behavior with `--check` |
|---|---|
| `--config PATH` | Load that file as the effective config (already a global option, line 62). |
| `--preset NAME` | Use that preset as the effective config (already global, line 267). Pro presets do **not** require a license for `--check` — it writes nothing. |
| _(neither)_ | Auto-discover from the working directory, same rule as a build. |
| `--no-config` _(new flag, `is_flag=True`)_ | Skip discovery and config loading entirely — exact current behavior. Back-compat escape hatch and the documented way to get an unfiltered scan. |

`--config` + `--preset` together keeps today's precedence (`main()` treats an
explicit/auto config as winning over `--preset`).

`_handle_check` gains parameters and the dispatch call passes the already-parsed
values through:

```python
# main(), ~line 465
if check:
    _handle_check(
        Path(input_path),
        json_output=json_output,
        offline=offline,
        config_path=config,          # NEW — was in scope, never forwarded
        preset=preset,               # NEW
        no_config=no_config,         # NEW
        level=level,                 # NEW (for level-default provenance only)
        verbose=verbose,
    )
```

## Shared config resolution helper

Config resolution is currently inline in `main()` (lines ~546-660: discover,
`ObfuscationConfig.from_file` / `.get_preset` / `.pro_edition` / level default).
The first increment adds a pure resolver for `--check` and MCP that mirrors the
build path's precedence. Refactoring the mature build path onto the same helper
is deliberately deferred to the future dry-run increment, avoiding an unrelated
build/licensing behavior change in this small release:

```python
# pyobfus/core/config_resolve.py  (new module)

@dataclass
class ConfigProvenance:
    source: str            # "explicit-config" | "auto-discovered" | "preset"
                           #  | "level-default" | "none"
    config_path: str | None   # repo-relative when possible, else basename
    preset: str | None
    level: str
    config_hash: str | None   # "sha256:<hex>" over canonical effective config

def resolve_effective_config(
    *, config_path: str | None, preset: str | None, level: str,
    cwd: Path, no_config: bool = False,
) -> tuple[ObfuscationConfig, ConfigProvenance]:
    ...
```

Notes:

- Discovery uses `find_config_file(start_path=cwd)` — identical to a build. It
  does **not** walk up from the scanned `PATH` and does not treat a `pyobfus.yaml`
  inside `PATH` specially. Rationale: `--check` should preview what a build in
  this working directory would do; introducing a second discovery convention is
  the kind of divergence the research doc warns against. Documented explicitly.
- `config_hash` reuses whatever `--provenance-manifest` already hashes for its
  `config_hash` field (`pyobfus/core/provenance.py`) so the two never disagree.
- The existing build path remains unchanged in this increment. Moving it onto
  the helper is paired with the future dry-run work and must preserve the same
  config object and Pro-preset license gate.

## PreflightChecker changes

`PreflightChecker.__init__` already accepts `exclude_patterns`
(`preflight.py` line 562). Two additions:

```python
PreflightChecker(
    exclude_patterns=cfg.exclude_patterns,   # from resolved config
    preserve_names=cfg.exclude_names,         # NEW: set[str], for mitigation x-ref
    check_dependencies=True,
    offline=offline,
    report_excluded=True,                     # NEW: scan+bucket excluded files
)
```

### Excluded-file bucketing

`_check_directory` (line 594) currently does
`files = filter_python_files(directory, self.exclude_patterns)` and scans only
those. Change to:

```python
included = filter_python_files(directory, self.exclude_patterns)
if self.report_excluded and self.exclude_patterns:
    all_files = filter_python_files(directory, [])
    excluded = [f for f in all_files if f not in set(included)]
else:
    excluded = []
```

- Included files → `report.risks` and framework detection (matches what a build
  sees).
- Excluded files → new `report.excluded_risks: list[Risk]`. Framework detection
  is **not** run on them.
- `report.files_scanned` counts included only (unchanged meaning). New
  `report.files_excluded: int`.

`PreflightReport` new fields: `files_excluded: int = 0`,
`excluded_risks: list[Risk] = field(default_factory=list)`. Defaults keep every
existing `PreflightChecker()` / `check_path()` caller and test unchanged.

`to_dict()` adds, without touching any existing key:

```jsonc
"files_excluded": 12,
"excluded_findings": {
  "count": 5,
  "severity_counts": {"high": 3, "medium": 2, "low": 0, "info": 0},
  "category_counts": {"dynamic_exec": 3, "all_export": 2},
  "sample": [ /* up to 10 full Risk dicts */ ]
}
```

`excluded_findings` is deliberately **not** merged into `risks`,
`severity_counts`, `category_counts`, or `exit_code`. A project whose only
high-severity constructs live in excluded files gets `exit_code == 0` — correct,
because the build never touches them — with the detail still visible for review.

### Config-aware mitigation annotation

Research decision: "annotate/downgrade the relevant compatibility finding only
when the configuration actually mitigates it." First cut, deliberately narrow:

1. **`dynamic_attr` string-literal MEDIUM** ("`getattr()` with string literal —
   ensure the target name is preserved", `preflight.py` ~line 331). The visitor
   already knows the literal is a constant string; capture its value. In
   `_finalize` (which now has `preserve_names`), if the literal ∈
   `preserve_names`, downgrade `high`→ keep, `medium`→`info`, set
   `mitigated_by = "exclude_names"` and rewrite the message to name the covered
   symbol.
2. **`all_export` MEDIUM** ("Module defines `__all__`", ~line 259). If the
   resolved preset is `safe` (auto-preserves `__all__`) **or** every name in
   that module's `__all__` is in `preserve_names`, downgrade `medium`→`info`,
   `mitigated_by = "preset:safe"` / `"exclude_names"`.

`Risk` gains `mitigated_by: str | None = None` (dataclass field; `asdict`
includes it — additive, unknown-key-tolerant consumers ignore it). VS Code can
later render `mitigated_by` findings as Hints; no extension change is required
for this release.

Severity-change safety: mitigation only ever lowers `medium`/`low`→`info` and
never rewrites `high`. `exit_code` keys on `high` only, so it cannot move.
Everything except the narrow two rules above is untouched in cut 1; broader
cross-referencing (preserve_patterns, `__name__`-comparison sites,
framework-preset-specific reflection) is a follow-up, tracked in
`docs/CURRENT_PLAN_ZH.md` candidate list.

### Dependency advisory — unchanged path, one clarification

`_finalize` keeps calling `check_dependency_hallucination(Path(report.root),
offline=self.offline)`. `report.root` is the scanned `PATH`, so excluding a
Python source subdirectory never hides `requirements*.txt` /
`pyproject.toml` findings. Add a one-line code comment and a cookbook note
stating this is intentional. Private-index allowlist from config is candidate 7,
out of scope here.

## JSON contract (full `--check --json` shape after this change)

```jsonc
{
  "version": 1,
  "root": "src",
  "files_scanned": 34,
  "files_excluded": 12,                 // NEW
  "parse_errors": [],
  "severity_counts": { "high": 0, "medium": 2, "low": 5, "info": 3 },
  "category_counts": { "...": 0 },
  "frameworks": [ /* unchanged */ ],
  "suggested_preset": "fastapi",
  "suggested_excludes": [ "**/routers/**" ],
  "effective_config": {                 // NEW
    "source": "auto-discovered",
    "config_path": "pyobfus.yaml",
    "preset": null,
    "level": "community",
    "exclude_patterns": ["test_*.py", "**/tests/**"],
    "exclude_names_count": 41,
    "config_hash": "sha256:1f3c…"
  },
  "excluded_findings": {                // NEW (see above)
    "count": 5, "severity_counts": {…}, "category_counts": {…}, "sample": [ … ]
  },
  "risks": [
    { "category": "dynamic_attr", "severity": "info",
      "mitigated_by": "exclude_names",           // NEW optional key
      "file": "src/api.py", "line": 12, "col": 4,
      "message": "getattr() target 'route' is covered by exclude_names.",
      "suggestion": "…", "snippet": "" }
  ],
  "ai_hint": "Low risk. 3 high-severity patterns are in excluded files and will not be obfuscated.",
  "exit_code": 0
}
```

`--no-config` → `effective_config.source == "none"`, no `files_excluded` /
`excluded_findings` keys (or zero/empty), `risks` exactly as today.

Text output (`format_report_text`) gains a compact block after "Files scanned":

```
  Effective config: pyobfus.yaml (auto-discovered)   excludes: 2 patterns, 41 names
  Excluded files: 12 scanned separately — 3 high, 2 medium (not counted above)
```

## MCP

`check_obfuscation_risks(path, verify_dependencies_online=False)` gains
`use_project_config: bool = True`:

- `True` (default): resolve config via the same helper, root = validated path,
  discovery from the validated path's directory (MCP has no ambient cwd concept
  the way the CLI does — document this as the one intentional discovery
  difference). Read-only, introduces no new egress.
- `False`: current behavior.
- `payload` gains `effective_config`, `files_excluded`, `excluded_findings`.
  This is an additive change to the MCP JSON contract → note it in
  `pyobfus_mcp/CHANGELOG.md` and bump the tool-manifest description; no
  `next_tool` / `ai_hint` shape change.

VS Code: no change required. `diagnosticsProvider.ts` keeps iterating
`report.risks`; excluded-file findings correctly do not become editor
diagnostics. Optional later polish: a separate "N findings in excluded files"
line in the pyobfus output channel.

## Tests

New / extended:

- `tests/test_preflight.py`
  - excluded file's `eval()` lands in `excluded_risks`, not `risks`;
    `exit_code == 0` when that is the only high finding.
  - `getattr(o, "route")` with `route` in `exclude_names` → `severity == "info"`,
    `mitigated_by == "exclude_names"`.
  - `__all__` module under `--preset safe` → downgraded.
  - dependency advisory still fires when the source subdir is excluded.
  - `PreflightChecker()` with no args → byte-identical `to_dict()` to pre-change
    (guard the additive-only promise).
- `tests/test_json_cli.py`
  - `--check --json` has `effective_config` with the right `source` for each of:
    explicit `--config`, discovered file, `--preset`, nothing, `--no-config`.
  - `--check --json --no-config` preserves pre-change scan/count/exit behavior
    while identifying the effective config source as `none`.
- `pyobfus_mcp/tests/`
  - `check_obfuscation_risks(..., use_project_config=False)` reproduces the old
    payload; default `True` adds `effective_config`.
- `tests/test_config_schema.py` / `config_resolve` unit tests: provenance
  `source` classification, `config_hash` stability, `main()` refactor parity
  (resolve helper vs. a captured pre-refactor config for each preset).

Run the three roots separately (`tests/`, `pyobfus_mcp/tests/`,
`integration_tests/`) per `AGENTS.md`, plus `black` / `ruff` / the CI's joint
`mypy pyobfus/ pyobfus_pro/ pyobfus_mcp/pyobfus_mcp/`.

## Rollout

- One `pyobfus` minor bump (next is 0.5.18): `config_resolve.py`, `preflight.py`,
  `cli.py`, docs, tests. CHANGELOG `[Unreleased]` only — **do not tag/publish**
  until the user gates a release (current standing rule).
- MCP change can ride the same wave as `pyobfus-mcp` 0.3.9 or a later bump;
  it depends only on the new `pyobfus` version for the helper.
- Docs: extend `docs/DEPENDENCY_ADVISORY_COOKBOOK.md` note; add a short
  "`--check` and your config" section to the README `--check` example block and
  `docs/llms.txt`; mention `effective_config` in
  `docs/AI_INTEGRATION_STRATEGY.md` if it enumerates the contract.
- `scripts/check_unreleased_changelogs.py` already guards the release-prep step.

## Decisions resolved by the user

1. **Discovery root for `--check PATH`**: match a build (working directory,
   proposed) vs. discover relative to `PATH`. Proposed = working directory, to
   avoid a second convention.
2. **`mitigated_by` downgrade** changes a `severity` string in `--check --json`
   output (never `high`, never `exit_code`). Acceptable, or keep the original
   severity and only add `mitigated_by` as an annotation?
3. **Cut-1 mitigation scope**: only `exclude_names ↔ dynamic_attr` literal +
   `safe`-preset `__all__`. Confirm that is enough for a first release, rest
   deferred.

---

## Candidate 2 preview — `--dry-run --json` plan object

Shares `resolve_effective_config` + `ConfigProvenance`. Today
`--dry-run --json` emits `_emit_obfuscate_success_json` (cli.py ~1861): aggregate
`stats` only, no file list, no effective config. Add one additive key:

```jsonc
"plan": {
  "schema": 1,
  "effective_config": { /* same ConfigProvenance dict as --check */ },
  "mode": "cross_file",              // cross_file | single_file | directory
  "jobs": 8,
  "selected":  ["src/a.py", "src/b.py"],
  "copied":    ["src/data.json"],
  "excluded":  [ {"path": "src/tests/x.py", "reason": "matches **/tests/**"} ],
  "artifacts": {
    "output": "dist/",
    "mapping": {"path": "mapping.json", "delivery": "retain-internal"},
    "trace_marker": null,
    "provenance_manifest": null
  },
  "compatibility": [ /* compat_advisory Risk dicts, if any */ ],
  "ai_hint": "…",
  "next_command": "pyobfus src/ -o dist/ --preset balanced"
}
```

Never include literal config values, vault contents, license keys, device
fingerprints, absolute home paths, or source text (Terraform's own plan-file
sensitivity warning). First version is **not** apply-able — a saved plan that
could be replayed would be a second state-management system; config/input drift
makes that unsafe without more machinery than the value justifies.

`selected` / `copied` / `excluded` come from the existing
`filter_python_files(input, config.exclude_patterns)` plus the copy-list logic
already in `_obfuscate_directory_crossfile`; the `delivery` classification
(`ship` / `retain-internal` / `optional`) is candidate 5 and can land in the
same key later. Priority: P1, after config-aware `--check` (they can even be one
release).

## Candidate 3 preview — syntax-only post-build verification

Separate spike, lower urgency. Verify each produced `.py` with an in-memory
`compile(source, filename, "exec")` (no `__pycache__` in the delivery dir, no
import, no execution). Report per-file `syntax_valid` in the existing JSON
envelope; never label it `runtime_verified`. Rejected: `--verify-command`
(command-execution/quoting risk) and importing output (runs user code). Not an
MCP tool. Feed the result into the dry-run/provenance report rather than a new
command.
