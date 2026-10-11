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
`--no-cross-file` directory builds do not write a mapping: independent per-file
renaming can collide, requiring file-specific name tables and frame-aware name
lookup; requesting `--save-mapping` warns in stderr and JSON.
Incremental cache hits retain their existing mapping. Pro fusion pre/post text
passes disable alignment explicitly; this does not attempt to map Pro mechanisms.

## Query and precision

`resolve_location(path, line)` returns an immutable location with status
`mapped` or `generated`, or None for absent/unsupported metadata, an out-of-range
line, or ambiguous path. Normalize slash direction, dot segments and drive-letter
case, then match **all** components of each mapping key from the end (a basename
alone cannot match `app/b/util.py`). The longest complete unique suffix wins;
equal-length candidates are ambiguous. Filenames remain case-sensitive.

Precision is **statement-level**: every output line of a multiline statement
maps to the original statement start, including lambda/comprehension expression
frames. Nested statements supersede the enclosing statement. Original expression
columns, comments, formatting and source text cannot be reconstructed. A removed
statement has no output location. Generated helpers must never claim source line
1. Type/count alignment cannot prove semantic equivalence for arbitrary third-party
transformers that reorder same-type statements; supported transforms preserve order.

## PR2 presentation contract

CLI and MCP share `ObfuscationMapping.unmap_trace()`, which uses
complete file-key suffix matching on original frame paths before restoring names.
Only frames for which `resolve_location(path, line)` succeeds vote for the
deployment root formed by removing the matched key from its normalized path
(absolute and relative prefixes remain distinct). Out-of-range lines and
unavailable line tables contribute no votes; resolvable generated lines do.
Each root's score is the pair `(known_obfuscated_name_frames, resolvable_frames)`,
compared lexicographically. Exact identifiers in `global_map` or any `locals`
key set are strong name evidence; `<module>`, `<lambda>`, `<listcomp>` and other
CPython labels are not. One strong frame outweighs any number of ordinary
frames; repeated frames count individually. The unique highest-scoring root
wins; frames with another root remain verbatim and `unmapped`, never `generated`.
If both score components tie, all matching frames remain unresolved and the
hint explains that the deployment root cannot be determined. A single
resolvable matching frame has one root and restores normally. Standalone
`resolve_location()` only checks suffixes and has no root context; its signature
is unchanged. CLI and MCP both use `unmap_trace()`.
For example, a directly built package has keys `__init__.py` and `core.py`:
`/run/pkg/core.py:8` resolves, but `/stdlib/json/__init__.py:346` exceeds the
user package initializer's line count and cannot vote. The user root wins and
json frames remain unchanged. If both foreign and user lines resolve, a known
obfuscated function name in the user frame breaks the ordinary-frame tie.
This heuristic is not proof of ownership: a foreign identifier can collide with
a mapping key, foreign frames can win without user name evidence, and a sole
resolvable foreign frame can be selected. Deployments spanning roots lose
restoration outside the selected root.
Only whole standard CPython `File "path", line N, in name` lines receive
location changes. Mapped frames retain editor-recognizable source locations:
`File "pkg/core.py", line 15, in divide  [obfuscated: /deploy/pkg/core.py:17]`.
Generated frames keep the output path/line with `[generated by pyobfus]`;
unresolved frames keep their output locations. Names in eligible frames are
reversed; deployment-root rejection preserves the entire frame.
Code excerpts receive the existing `unmap_text()` identifier replacement, as in
0.6.1, without reconstructing source text or changing indentation. `^`/`~`
indicator lines remain verbatim; their columns follow artifact text, even when
restored names change width, and do not correspond to original source columns.
Other log text retains the existing identifier replacement behavior; other location formats are not rewritten.
Exception-group prefixed frames are outside this standard-frame parser.

JSON adds `frames` (in trace order, including repeated frames) with
`obfuscated_file`, `obfuscated_line`, nullable `original_file`/`original_line`,
and `status` (`mapped`, `generated`, `unmapped`). `line_map` is `absent` when
no usable tables exist, `partial` when a file table is disabled or a recognized
frame cannot resolve, otherwise `available`. Availability describes metadata,
not proof that a mapping belongs to this build. Existing unmatched-name
warnings also explain that line restoration may be untrustworthy; no heuristic
can detect every wrong mapping. Hints explain statement precision and artifact
excerpts with restored names, or tell old-mapping users to rebuild using a
line-map-capable release
of pyobfus after 0.6.1. No release number is assigned by these PRs.

MCP discovers `unmap_trace` with `getattr`: older supported Core versions retain
their existing name-only text and hint, with additive `frames: []` and
`line_map: "absent"`. The VS Code JSON runner parses ordinary objects and its
unmap command reads only existing fields, so additional fields require no plugin
change. This remains Community local debugging, without license checks.
