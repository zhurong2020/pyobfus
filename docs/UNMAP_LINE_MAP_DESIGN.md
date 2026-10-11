# Statement locations in mapping files

PR1 adds Community build metadata and a read-only API; CLI/MCP traceback
presentation follows in PR2. The user is a developer debugging a shipped `.py`
artifact. Repeated AI debugging advice and the 0.6.1 reproductions demonstrate
that name restoration alone leaves the developer searching the source.
This is basic local debugging under the edition boundary policy, with no license
gate and no change to the Pro/Core source boundary.

## Format and compatibility

The top-level `version` remains **1**. Optional `files` contains
`line_map_version: 1` and `entries`, keyed by output-root-relative POSIX paths
(single-file builds use the output basename). Each entry has `source` (relative
to the input root), `module`, `lines`, and optional `reason`. `lines` is a sorted
list of `[output_start, source_line_or_null]` runs, starting at line 1, plus
`line_count` to bound the last run. Null denotes generated code, comments or
blank lines without a source statement. Unavailable alignment uses `lines: null`
and a reason. No source text, comments, string values or absolute paths are
stored in this section; the existing top-level `root` is unchanged.

Older version-1 readers ignore `files`; new readers accept its absence or an
unknown line-map version. Name tables, stats and `marker_id()` are unchanged.
The existing `global[*].module` can identify a referencing module rather than
the defining file; file records come directly from each file transform instead.
Fixing that existing field is outside this change.

## Alignment and final text

Before transforms, annotate each original statement with its starting line.
Unannotated statements created by transforms are synthetic (including helper
bodies and replacement `__all__` assignments); copied AST locations alone do
not confer source provenance. Parse final generated text after the build marker
and align statements in depth-first preorder by count and node type. Paint
parent statement spans first, then child spans, so nested bodies take precedence.
Decorators are included in a definition's span. Compress adjacent equal entries.
A mismatch or parse failure disables that file's table without failing the build;
verbose builds report the reason. Workers return pickleable records separately
from numeric statistics; serial and parallel aggregation are equivalent.

Single-file mapping is saved after the final text is written. The subsequent
trace-marker insertion shifts runs after the preserved shebang/encoding prologue
and inserts four generated lines, then saves the mapping with the same marker ID.
Incremental cache hits retain their existing mapping. Pro fusion pre/post text
passes disable alignment explicitly; this does not attempt to map Pro mechanisms.

## Query and precision

`resolve_location(path, line)` returns an immutable location with status
`mapped` or `generated`, or None for absent/unsupported metadata, an out-of-range
line, or ambiguous path. Normalize slash direction, dot segments and drive-letter
case, then compare path components from the end. The longest unique suffix wins;
equal-length candidates are ambiguous. Filenames remain case-sensitive.

Precision is **statement-level**: every output line of a multiline statement
maps to the original statement start, including lambda/comprehension expression
frames. Nested statements supersede the enclosing statement. Original expression
columns, comments, formatting and source text cannot be reconstructed. A removed
statement has no output location. Generated helpers must never claim source line
1. Type/count alignment cannot prove semantic equivalence for arbitrary third-party
transformers that reorder same-type statements; supported transforms preserve order.
