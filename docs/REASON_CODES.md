# Reason Codes

Status: catalog v1, shipping in the release that also carries CycloneDX 1.7 and
the server-registered trial.

pyobfus's structured JSON surfaces attach a **stable reason code** to each build
decision, so tools (the VS Code extension, CI, MCP, auditors) branch on a fixed
token instead of parsing English prose whose wording can change between
releases. The single source of truth is `pyobfus/core/reason_codes.py`.

## Versioning contract

- A top-level `reason_codes_version` accompanies the codes on each surface
  (currently `1`).
- **Consumers must ignore unknown codes.** Adding a code is a minor,
  backward-compatible change; removing or repurposing one bumps the version.

## Where codes appear

| Surface | Field | Domains emitted |
|---|---|---|
| `--dry-run --json` (plan) | `files.selected[].reason`, `files.excluded[].reason`, `disabled_transforms[].reason`, `reason_codes_version` | selection, disabled |
| `--build-report` | `selection.selected[].reason`, `selection.excluded[].reason`, `disabled_transforms[].reason`, `reason_codes_version` | selection, disabled |
| `--check --json` | risk findings use their own stable `category` field (unchanged) | — |

## Catalog

### File selection (`selected.*` / `excluded.*`) — emitted

| Code | Meaning |
|---|---|
| `selected.included` | File selected for obfuscation. |
| `excluded.pattern` | File skipped because it matched a configured exclude pattern. |

### Disabled transforms (`disabled.*`) — emitted

Only **requested-but-suppressed** transforms are listed (a config flag is set
but the mode or level prevents it), so `disabled_transforms` says "you asked for
X, it won't run because Y" without noise from every off-by-default transform.

| Code | Meaning |
|---|---|
| `disabled.cross_file_mode` | A build-fusion mechanism (`--selective-opacity` / `--seal-code` / `--vault` / `--scrub-traceback` / `--bind-device`) operates on generated source and is not applied in cross-file directory mode. Use `--no-cross-file` or a single file. |
| `disabled.requires_pro` | A Pro transform (e.g. `--string-encryption`, control-flow, dead-code, import-obfuscation, anti-debug) was requested while the effective level is community. |
| `disabled.not_selected` | Reserved: a transform is not enabled in the effective configuration. |

### Preserved symbols (`preserved.*`) — reserved, not yet emitted

These codes are **defined and documented so consumers can rely on them once
emission lands**, but no surface emits them yet. The analyzer prunes preserved
categories (imports, config excludes, dunders) at collection time, so a
per-symbol reason cannot be reconstructed after the fact; emitting them needs
the analyzer to record a reason as it prunes. That is a deliberate follow-up,
not part of this release.

| Code | Meaning |
|---|---|
| `preserved.dunder` | Symbol is a dunder (e.g. `__init__`) and is never renamed. |
| `preserved.imported` | Symbol is bound by an import; renaming would break it. |
| `preserved.config_exclude` | Symbol is listed in the configuration's `exclude_names`. |
| `preserved.public_api` | Symbol was auto-detected as part of the public API. |
| `preserved.other` | Preserved for another reason (e.g. global scope). |
