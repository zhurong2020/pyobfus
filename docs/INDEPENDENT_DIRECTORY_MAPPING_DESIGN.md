# Independent-directory mapping

Status: implemented and independently reviewed 2026-10-22; local validation complete, not merged or released. See [validation evidence](INDEPENDENT_DIRECTORY_MAPPING_VALIDATION.md). Community correctness/debugging primitive under `EDITION_BOUNDARY_POLICY.md`.

## Problem and boundary

The released `--no-cross-file --save-mapping` directory build warns and writes no mapping. Independently allocated short names collide across files. The user needs to debug these artifacts without installing the builder on the target, changing obfuscation behavior, or moving Pro code into Core. Audit evidence: `ADOPTION_WORKFLOW_AUDIT_2026-10-22.md`.

## Format and construction

Continue writing version 1 for current single-file and cross-file modes. Write version 2 only for new `independent_files` mode; new readers accept versions 1 and 2, while old readers reject version 2 instead of silently misdecoding. Preserve existing CLI/MCP response keys.

Add `file_names`: output-relative POSIX path -> obfuscated name -> list of possible original spellings. Normalize renamed identifiers using Python NFKC identifier rules, preserving ambiguous candidate lists. Reject no valid build solely because optional metadata failed: retain file names with a reasoned absent line table, or mark nonportable POSIX filename spellings unavailable with a warning. Keep separate `files.entries` line metadata, including unavailable-line reasons for fusion. Module display names are not file identities; `a.py`, `a/__init__.py`, and `b/a.py` must remain distinct. Do not populate a whole-project reverse dictionary in independent mode or backfill it when loading. Unqualified `reverse()` / `unmap_text()` leave names untouched without file context. Lexically repeated spellings restore only the spelling; no qualified scope is inferred. Multiple possible spellings remain unchanged.

Collect each successfully emitted file's existing mangler table and statement map in memory through the single-file path; save the aggregate once at directory completion. Dry-run writes nothing. If some files fail under the existing tolerant directory behavior, include successful file tables only, preserve warnings and record failed or residual output keys separately in `unmapped_files` as negative identity evidence. Include excluded/removed `.py` files still in the output directory as unavailable, but never stamp them or attribute names/locations to them. Hash this exclusion map into the marker id; do not invent positive entries for them. A file with no renamed names still participates in path/location metadata.

The independent marker id hashes sorted per-file name candidates, relative source labels and output keys, and per-file original-source and pre-trace-marker output digests. Original-source bytes bind source whitespace and statement positions even when AST output is unchanged. Digests make changed code distinguishable without depending on the build timestamp or marker insertion's line shift. Trace markers stay opt-in and shift the existing line records once; only this build's successful file keys may be stamped, never stale or excluded outputs. The marker is a consistency hint, not an authenticated artifact identity.

## Restoration contract

In v2, collect every complete suffix candidate and infer one deployment root jointly across frames. Every matching path frame participates, including `<module>` and preserved names, so one foreign short name cannot overrule contradictory application paths. Intersect those candidate sets with file-specific name evidence. Never use majority counts. An unavailable/stale candidate has no name table, but its absence must not eliminate its root from an ambiguous frame's name evidence. If a trace has no renamed-name evidence and supplies no matching marker, require at least two distinct mapped file keys corroborating the root; a lone external `__init__.py` frame is not enough.

One root must satisfy all this evidence. Repeated frames have no extra weight. A deployment directory named like a nested package makes the longest suffix unsafe: `cli.py` and `pkg/cli.py` under `/srv/pkg` are ambiguous alone; a distinct `main.py` frame, even `<module>`, can establish the root. Conflicting external suffixes can conservatively make the entire trace unresolved. This is an intentional accuracy-first limit, not proof that every matching frame belongs to the build. Version-1 behavior is unchanged.

Accept POSIX/Windows separators and full relative or relocated absolute paths; no bare-basename fallback for nested keys, no POSIX case folding. Select file identity before checking its line range, and never retry another key because the selected file's line is invalid. Keep the direct `resolve_location()` API conservative if multiple suffix keys match. File identity remains useful when fusion disables line tables, while out-of-range frame lines remain negative evidence.

For an accepted frame, restore only its function display name using that file's unique name candidates. Recognize CPython ExceptionGroup tree-prefixed frame headers and preserve the prefix. Do not carry a file context across any lines: source excerpts, exception messages and unframed logs retain artifact text, including globally unique names. This deliberate scope avoids guessing whether indented multi-line exception text is a source excerpt, and prevents leakage across exception chains/branches. Unknown frames remain untouched. The hint explains these limits; carets/columns remain artifact positions. No source files are read during unmapping.

If an explicitly supplied trace marker differs from the mapping's marker id (including a mix of marker ids), restore neither names nor locations; return unresolved frame metadata and a clear mismatch hint. An absent marker is reported as unverified, not a proven match. Legacy version-1 restoration behavior remains unchanged.

## Acceptance and surfaces

Tests must exercise real CLI build/target traceback/unmap with two colliding files, nested repeated basenames, preserved names and repeated lexical spellings; absolute/relative/Windows paths, unknown/external frames, root ties, multiple frames and multiple exception sections; marker match/mismatch/absence and changed-content marker ids; no-line-table records; dry-run and partial build; malformed optional file-name metadata; version-1 fixture compatibility and version-2 old-reader rejection. Keep the target runtime builder-free for Community.

Update CLI help, dry-run/build report artifact availability, README and debugging/line-map docs, existing unsupported-mode assertions, MCP contract tests, and Core Unreleased notes. Independent name tables and line maps remain private developer artifacts. No release, version bump or publishing is implied.

## Review decisions (2026-10-22)

Independent review identified source-position identity, stale-output stamping, exception-tree context and competing-root risks. The contract above now binds source bytes, limits marker targets, restores frame headers only (no inferred excerpt context), and requires a root consistent with all named evidence. The independent Claude review additionally identified nested suffix ambiguity and malformed v2 loading; v2 now uses joint candidate-set inference, requires file identity, drops orphan names, degrades malformed optional line runs to name-only, and never backfills legacy global tables. Markers are stamped after collection/save, so no extra in-memory output staging is required. These are conservative v2 rules; v1 remains unchanged.

Independent mappings requested with `--incremental` force a rebuild: cached generated files cannot reconstruct current private metadata. Dry-run still writes nothing. This does not change the other build modes' cache contract.

Final code-review counterexamples added a path-only veto, failed/stale/excluded path evidence, re-unmap idempotence, physical-line parser consistency, Unicode/NFKC prefixes and metadata degradation. V2 frame JSON adds `resolved_file` for name-only cases while retaining existing location/status keys. The incremental override was already inside the directory-only guard; the reported single-file concern was a diff-context false positive.
