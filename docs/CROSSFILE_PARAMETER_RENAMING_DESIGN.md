# Parameter renaming and keyword-call compatibility design

Status: **proposal for Claude and maintainer review; not implemented**.
Date: 2026-10-08. Baseline: post-release main
`130b8c15cde8e3eeb1becd9ef64ab323b00d8d5f`, Core 0.6.0.
This document changes no defaults, CLI contracts or edition boundaries.

## Problem and measured baseline

Parameter spellings are a callable API. Renaming an `ast.arg` without changing
its keyword callers breaks binding, even when both occur in one file. With
`**kwargs`, the same mistake can silently redirect a keyword into the extra
arguments dictionary instead of binding its intended parameter.

Evidence is retained locally in the gitignored directory
`docs/internal/geo-2026-10/param-design-evidence/` (called **E** below).
`probe.py`, `counts.py` and `architecture.py` record inputs, exact commands,
stdout, stderr, exit codes, generated AST signatures, mappings and products.
Public design conclusions below refer to those experiments, not to untested
support guarantees. Run them from the WSL checkout with `venv/bin/python`.
All CLI/product subprocesses use an isolated HOME/USERPROFILE. Public versions
were installed in separate Python 3.12 venvs using
`python -m pip install pyobfus==0.5.32` and `pyobfus==0.6.0`; version and import
locations are logged. No license or trial state was fabricated.

### Defect F: single-file keyword calls

Input, also retained as `fixtures/*/F/single/*/src/entry.py`:

```python
def scale(value, factor=2, *, offset=0):
    return value * factor + offset
print(scale(1, factor=3, offset=1))
```

Equivalent minimal reproduction commands, using either installed interpreter:

```bash
python entry.py                           # 4; exit 0
python -m pyobfus entry.py -o built.py
python built.py                           # TypeError; exit 1
python -m pyobfus entry.py -o kept.py --preserve-param-names
python kept.py                            # 4; exit 0
```

`probe-results.json` and `checkout.log`, `0.5.32.log`, `0.6.0.log` record the
same result for checkout, public 0.5.32 and public 0.6.0. Default single-file
products rename the signature but retain call keyword strings `factor` and
`offset`. `safe` also fails. `fastapi`, `flask` and the explicit preservation
flag pass. `NameMangler.visit_arg` changes argument bindings; its file-wide
map does not provide callable-aware keyword edits.

**Correction to the design premise:** current `safe` does not set
`preserve_param_names=True`. It only changes docstring handling. The runtime
safe failure and `presets.json` verify this; framework presets and `library`
set preservation. This design proposes making safe explicitly preserve
parameters, rather than describing that setting as already present.

### Directory mode

Minimal project (entry filename avoids framework preset file exclusions):

```python
# pkg/core.py
def scale(value, factor=2, *, offset=0):
    return value * factor + offset
# pkg/__init__.py
from .core import scale
# entry.py
from pkg.core import scale
print(scale(1, factor=3, offset=1))
```

```bash
python src/entry.py                       # 4; exit 0
python -m pyobfus src -o dist --save-mapping mapping.json
python dist/entry.py                      # 4; exit 0
```

The F/directory rows pass under default, safe, explicit preservation, fastapi
and flask in both public versions and checkout. Product signatures retain
`value`, `factor`, `offset`; keywords remain unchanged. A separate re-export
fixture (`from .core import scale`, `__all__ = ["scale"]`) with a local
`total` binding passes and records module exports separately from locals.

### Additional measured constraints

| Experiment in E | Current single-file default | Current directory default |
|---|---|---|
| `positional` | Positional invocation succeeds | Succeeds |
| `alias` (assignment), `escape`, `partial`, `decorated`, `lambda`, `method` | Original keyword binding fails | Recorded fixtures succeed with parameters retained |
| `kwargs` | A dictionary's original keyword keys fail to bind | Succeeds |
| `reflection` | `inspect.signature` and `getfullargspec` expose mangled parameters | Original parameter spellings retained |
| `kinds` | **7 instead of 11**, exit 0: renamed `offset` receives its default; original `offset` enters `**kwargs` | 11, original signature |
| `generated` | 0.6.0 dataclass `Point(x=1)` and `asdict` pass; public 0.5.32 fails | Recorded dataclass example passes |
| `check-F.log` | `--check --offline --json`: exit 0, zero risks | No parameter-specific diagnostic claimed |

`kinds` uses `def kinds(value, /, factor=2, *args, offset=0, **kwargs)` and
`kinds(1, 3, 4, offset=5, bonus=7)`. The preservation flag restores output 11.
This experiment also records that default single-file renaming affects
positional-only, variadic and keyword-only argument binding names. The method
fixture records renaming of `self`; directory method signatures remain intact.
No conclusion about all decorators or arbitrary callables follows from these
small fixtures.

Exploration also found a separate directory alias issue: an import such as
`from pkg import scale as action` can keep `as action` while rewriting its use
to an unbound obfuscated identifier. The original traces are retained in
`alias-and-filter-confound-*`; framework presets can also exclude `main.py`.
Final F measurements use direct imports and `entry.py` to isolate parameter
behavior. Existing alias failures must be regression blockers for future
call-resolution work, not quietly classified as parameter support. Neither
issue is fixed by this document.

## Short-term response to F

Recommend **A before enabling any new parameter renaming**: set the unpreset
configuration default to `preserve_param_names=True`, and make safe explicitly
true. Retain true in library/framework presets. Cover default, balanced and
aggressive inheritance explicitly in the implementation PR. A false value
should not silently recover the unsafe old behavior: propose requiring an
explicit `--unsafe-rename-parameters` opt-in for that legacy single-file path,
with a warning that keyword and signature compatibility are unverified. The
flag name and whether to retain that path need maintainer approval.

| Option | Correctness and scope | Existing artifacts and mapping | Strength / release note |
|---|---|---|---|
| **A. Default preservation** | Immediately fixes measured F calls and signature names, including unknown callers; no resolver required. Does not fix unrelated method/class identity or dynamic-name defects. | Already distributed files do not change; rebuilds retain parameter spellings. Their single-file `modules`/`global` maps lose parameter entries and same-spelled unrelated entries because the map is file-wide. Number allocation shifts, so old mappings must never be used with rebuilt artifacts. | Fewer identifiers renamed; measured below. Requires a Fixed entry plus an explicit default-behavior/migration note in CHANGELOG, config/help, support matrix and examples. |
| **B. Rewrite provably resolved same-file calls** | Can preserve useful renaming, but requires lexical binding/escape analysis, callable identity and atomic definition/body/call edits. Unique textual names alone do not prove identity. Unknown uses preserve the entire candidate signature in v1. | Scoped parameter records become necessary; retain existing `modules` semantics and marker checks. The current spelling map cannot safely rename one `factor` and preserve another without a scope-aware parameter path, or file-wide suppression of both. | Better potential retention, higher correctness risk and implementation time. Requires a Fixed/Changed entry and compatibility documentation even if default strength seems similar. Implement after A, reuse the directory planner. |
| **C. Documentation and `--check` warning only** | Provides a workaround but still emits crashing or silently wrong default products. Scanner must report direct keywords, `**` forwarding and unresolved risk; absence of a finding must not imply safety. Current `--check` misses F. | No artifact or mapping behavior change; same names and allocation remain. New risk fields must preserve existing JSON envelopes. | No reduction in parameter mangling. A diagnostic/documentation entry is needed; it must not claim F fixed. Reject as the sole response. |

### Measured cost of A and indicative scope of B

`counts.py` analyzes each source with `SymbolAnalyzer` and transforms a copy
with `NameMangler`, then repeats with preservation enabled. This is a
counterfactual **configuration-only experiment**, not a product patch or full
CLI framework guarantee. It counts actual changed `ast.arg` occurrences,
per-sample distinct spellings, and removed mapping entries.

| Corpus, default or safe | Samples | Parameter slots | Currently renamed slots | Renamed spellings, summed per sample | Mapping entries removed by A | B syntactic candidate slots |
|---|---:|---:|---:|---:|---:|---:|
| `examples/**/*.py` | 16 | 81 | 79 | 56 | 58 | 31 |
| `tests/**/*.py` source | 91 | 2230 | 2189 | 301 | 301 | 84 |
| Parseable embedded test snippets | 433 | 374 | 359 | 316 | 314 | 25 |

A reduces those renamed slots to zero. FastAPI, Flask, Django and library
counterfactual rows already rename zero parameters and remove zero entries;
these four configurations were independently measured. `presets.json` also
records current safe/balanced/aggressive and other available framework flags.
These counts include methods and lambdas, duplicates across functions, and
ordinary pytest fixture parameters; they are **not application performance or
protection scores**. Runtime fixture-specific exclusions are not reconstructed.
Two embedded samples fail standalone baseline transformation with nonlocal
binding errors, under each of six presets: 12 skipped sample/preset pairs,
retained in `counts.json`. Invalid or dynamically assembled strings are not
counted. No existing test or example was modified.

The B column is only an illustrative syntactic estimate: unique undecorated
top-level definitions whose references are bare direct calls, with no
`**` calls or simple reflection markers. It is **not an eligible count or
soundness proof**: external callers, lexical rebinding and coarse-name
collisions still require analysis. B can range from preserving every signature
(unknown callers) to the measured current mangling upper bound (if each binding
and incoming edge were proved). C retains the current counts. More exact B
strength claims must wait for a reviewed resolver and representative projects.

## Cross-file design: conservative opt-in v1

Proposed configuration: `crossfile_parameter_names: false`, with CLI switches
`--crossfile-parameter-names` / `--no-crossfile-parameter-names`.
`preserve_param_names=True` is an absolute veto, independent of option order,
local-name settings and tier. With A's proposed new default, a parameter-plan
build requires both `crossfile_parameter_names: true` and an explicit
`preserve_param_names: false` in config. Conflicting CLI preservation should
report that parameter renaming was disabled, rather than silently overriding
it. No flag in this section exists yet.

The unsafe legacy single-file switch and a planned parameter-renaming switch
must be mutually exclusive. A legacy YAML false value alone should warn and
preserve, or require migration, rather than bypassing the planner. With all
new switches off, directory module/local renaming keeps its existing policy;
the new default changes single-file parameter handling.

### Function identity, planning and allocation

Use a stable identity `(relative module, lexical qualified name, definition
line, column, node kind)` from the original AST, not a global original-name
map or a transient symtable object id. Qualified names distinguish nested
scopes; position distinguishes repeated definitions. Normalize paths relative
to the input root. Anonymous lambdas need span-based identities if supported
later. Do not infer instance type or override relationships from method spelling.

1. Discover definitions, import/re-export bindings and call edges on original
   source; record source hashes, scopes, eligibility reasons and unresolved uses.
2. Resolve callable identities conservatively and propagate escape/ABI vetoes
   to a fixed point **before allocation**. Unknown bindings are evidence of
   uncertainty, not permission to guess.
3. Reserve all source identifiers and exclusion spellings across the build.
   Register module names as today; allocate existing locals next; allocate
   parameters last, through the same build-global collision-avoiding allocator.
   Sort module paths, function identities and argument declaration order.
   Keeping parameters last protects existing local allocations when toggling
   the new feature; compare actual mappings in tests rather than assuming it.
4. Produce finalized pickleable plans: signature `arg` edits, binding-resolved
   body/closure/nonlocal references and keyword `arg` edits at call sites.
   Use the existing full-span/node-type/attribute edit-key approach. Defaults,
   decorators and annotations retain Python's enclosing-scope evaluation order;
   a same-spelled name there need not refer to the parameter.
5. Validate all plans against source hashes and original coordinates before
   worker mutation. Workers apply precomputed edits; they perform no allocation
   or call-target guessing. AST validation and compile checks remain mandatory.

Coordinate local and parameter plans on the same original AST: a parameter
binding is excluded from local allocation, while its body/closure references
use the parameter plan. Retain local-binding protection so module/import
transformers cannot rewrite preserved or newly renamed parameters as exports.
Reject conflicting edits to the same source-coordinate/attribute key. Turning
`crossfile_local_names` off must not disable parameter binding analysis or
protection; the two rename switches control different allocations.

Current `architecture.py` experiments verify local-plan pickle round trips,
identical emitted source hashes and semantic `modules`/`locals`/`global` maps
for workers 1/2 and forward/reverse physical file creation order. Mapping
creation timestamps/root metadata are not part of that equality. This is
baseline evidence, not a tested parameter implementation. Current LocalPlan is
a mutable dataclass used as a finalized plan; proposed parameter plans should
use immutable records or an enforced freeze boundary.

### Call edges and binding rules

| Call form | Proposed v1 rule |
|---|---|
| Direct same-file/nested calls | Resolve lexical binding and reaching definition; reject shadowing/reassignment/ambiguous control flow. Rewrite only keywords bound to renamed formal parameters. Closures must reference the same parameter binding. |
| Cross-file import / module attribute | Resolve against the project import graph and actual export binding. Preserve signatures on unresolved external imports or dynamic module attributes. |
| Import aliases / re-export chains | Follow binding identity through static imports and `__all__` re-exports, detect cycles and ambiguous origins; qualify imported `asname` references correctly. Gate enablement on the observed alias regression. |
| Assignment alias | Later phase: only stable, unescaped aliases whose definitions and uses are proved. Until then a non-callee reference vetoes the signature. |
| `functools.partial` | V1 treats use as an escape and preserves the target signature. Later support must rewrite bound keyword keys and subsequent partial calls, tracking accumulated arguments and overrides. Never rewrite every keyword passed to every `partial`. |
| Decorators / wrappers | Preserve decorated definitions in v1, including `functools.wraps`; preserved introspection metadata does not prove forwarding semantics. Later opt-in recognition needs tested wrapper contracts and transitive argument forwarding. |
| Unknown target / callable container / callback | Preserve all candidate signatures that may flow to that use. If discovery cannot bound the candidate set, preserve the affected parameter component or skip parameter renaming for the build; do not rewrite the call speculatively. |
| `**mapping` / forwarded `**kwargs` | V1 vetoes the affected signature and forwarding chain. Do not rewrite dictionary keys generally. Literal dictionaries, copied/mutated dictionaries and mixed explicit keywords require separate future proofs. |

Only change a keyword whose binding is a renamed positional-or-keyword or
keyword-only formal of the proved target. Do not change unknown extra keyword
keys, or keywords with the spelling of a positional-only formal: those can
legitimately belong to `**kwargs`. Preserve duplicate-key/type-error behavior,
evaluation order and annotations. Unknown incoming edges veto renaming the
callee; known calls are not sufficient if other uses escape.

### Mandatory preservation and eligibility

V1 favors whole-signature preservation over per-parameter partial decisions.
Record a reason per function and count preserved parameter occurrences.

- **Policy:** safe, library and every framework preset, explicit
  `--preserve-param-names`, exclusions and reflected/opaque scopes veto changes.
  The proposed safe behavior is a new correction; current safe is false.
- **External/public API:** static `__all__`, public re-exports, configured public
  entry points and callable exports consumed outside the project preserve
  signatures. A function with no observed project calls is preserved, including
  private names. Absence of a detected external caller is not proof of privacy.
  Recommend v1 eligibility only for private/internal functions with direct
  observed calls and no escape. Public opt-in needs an explicit closed-world
  deployment contract; the export table alone does not establish one.
- **Reflection:** `inspect.signature`, `getfullargspec`, signature binding,
  `__signature__`, code-object parameter inspection and string/dynamic lookups
  veto the target. Unresolved reflective operations taint the containing
  candidate component. Recognize static import aliases; uncertain aliases
  preserve rather than evade the guard. `eval`, `exec`, `locals` and similar
  opaque scope behavior follow or extend existing local-planner vetoes.
- **Escape/callbacks:** returning a function, passing it as an argument,
  registering it, storing it in a container or attribute, exposing it through
  a property, or using it in a decorator is an escape unless a later reviewed
  contract proves all downstream calls. Propagate through aliases/closures.
- **Methods:** preserve instance/class/static methods and explicit `__init__`
  signatures, including `self`/`cls`. Overriding, descriptors, dispatch and
  external callback methods require type information beyond this v1 design.
- **Generated APIs:** never invent AST parameters for dataclass/pydantic/attrs
  generated constructors. Preserve calls to these classes; retain 0.6.0 field
  preservation separately. User-written constructors are methods and preserved.
- **Kinds:** v1 preserves lambdas and every signature containing positional-only
  parameters, `*args` or `**kwargs`, even though some binding names are not
  ordinary keyword APIs. This avoids mixed-kind introspection and forwarding
  complexity. Positional-only local-name obfuscation can be a separate reviewed
  phase, preserving the distinction between its binding and an extra keyword.
  Ordinary positional-or-keyword and keyword-only parameters of eligible plain
  functions can be renamed; decorators, methods and escapes still veto them.
- **Advanced scopes:** generic/lazy annotation scopes, ambiguous repeated
  definitions, symtable failures or unsupported syntax preserve the candidate
  scope. Keep nested definition `__name__` preservation from 0.6.0 independent
  of whether parameters are eligible.

### Failure downgrade and observability

Resolve and validate before publishing any parameter edits. Allocation uses
snapshot/rollback of counters/reservations, as the current locals planner does.
Discard a failed function's signature, body and all incoming keyword edits
atomically; discard a file's parameter plan when lexical/source matching fails.
Keep independent module and local transforms when their own plans remain valid.
Do not change a successfully planned unrelated function merely because another
file's parameter plan failed.

The **safe dependency closure** can be larger than the failed file: if a caller
cannot receive keyword edits, restore the affected callees' signatures too.
Recompute that closure and its call edits before workers run. If a failure makes
all incoming edges unknowable, disable the optional parameter feature for that
build with a warning rather than emitting half-rewritten APIs. A worker mismatch
after validation must cancel/restart with the affected component preserved,
or fail the build before shipping output; a successful partial tree is not a
valid downgrade. Preservation policy is not an error or a planner failure.

Propose additive stats `parameter_names_obfuscated`,
`parameter_keywords_rewritten`, `parameter_functions_preserved`,
`parameter_functions_skipped`, `parameter_files_skipped` and a reason histogram.
The first counts formal parameter bindings, not all body edits; keyword count
counts edited keyword nodes. Functions/files skipped count distinct identities/
paths with planning failures, excluding deliberate policy preservation.
Dependency-induced preservation gets its own reason. Maintain existing
`local_files_skipped` meaning and stable status/ai_hint/next_tool envelopes.
Warnings use relative paths, function identity and reason; JSON ai_hint mentions
successful builds that kept parameter names. `architecture.py` injects a
ValueError into current planning: only pkg/core.py gets `files_skipped=1`, the
build reports no errors and retains a warning. That tests the baseline pattern,
not the proposed cross-file dependency invalidation.

## Mapping and unmapping

Keep mapping format **v1** and `modules` as module-level forward/export mapping.
Add optional `parameters`, keyed by module then globally unique obfuscated
identifier; include original spelling, function identity and parameter kind:

```json
{
  "version": 1,
  "modules": {"pkg.core": {"scale": "I0"}},
  "locals": {"pkg.core": {"I1": "total"}},
  "parameters": {
    "pkg.core": {
      "I2": {
        "original": "factor",
        "function": {"qualname": "scale", "line": 1, "column": 0},
        "kind": "positional_or_keyword"
      }
    }
  },
  "global": {
    "I0": {"module": "pkg.core", "original": "scale"},
    "I1": {"module": "pkg.core", "original": "total"},
    "I2": {"module": "pkg.core", "original": "factor"}
  }
}
```

All parameter records also populate `global` for text unmapping. Distinct
functions with the same original `factor` get different identifiers; they must
not overwrite a module forward entry. New loaders preserve/validate metadata,
backfill missing global entries from parameters, and reject inconsistent or
colliding reverse names rather than silently overriding them. Merge, save/load,
schema and marker hashing must include the new section deterministically.

`proposed-mapping.json` is an exploratory synthetic v1 document, not a generated
parameter artifact. CLI `--unmap` under checkout, public 0.5.32 and public 0.6.0
and current MCP unmap all restore `I0/I1/I2` through its global section.
Current loaders ignore the extra parameters section and **drop it on save**
(`old-loader-resaved.json`); this is not metadata round-trip compatibility.
Upgrade readers/schema before emitting new records. Keep existing fields,
marker mismatch warnings and MCP return envelopes intact. Text unmapping restores
names, not original source line numbers or full signatures. Canonical marker
hashing must be reviewed: old readers may compute an identity without the new
metadata, so old marker verification cannot be advertised as compatible merely
because text unmapping succeeds. Include explicit old/new marker tests in rollout.

## Edition decision

Recommend **Community** for F correctness, callable-aware basic AST parameter
mangling, resolver safety, diagnostics, deterministic plans and local
mapping/unmapping. Users are Python application/library maintainers; there is no
separate managed-service buyer here. Evidence is the reproduced crashing/silent
misbinding and existing free single-file parameter mangling. Under
[Edition Boundary Policy](EDITION_BOUNDARY_POLICY.md), correctness and
compatibility are the free floor, as are project-wide name mangling and basic
local debugging. Extending that workflow safely does not justify moving an
existing basic capability into Pro. Although identifier mangling contributes
protection, this work adds no stronger encryption, protected asset, runtime
control or buyer attribution. A future managed policy service may be Pro;
correct keyword rewrites and honest fallback must never depend on payment.
Record this decision in implementation PRs and update affected edition-facing
surfaces together. This design itself changes no tier.

## Behavioral acceptance plan

Each implementation test builds then runs original and generated code, compares
stdout, exit status and relevant signature/error behavior. Syntax-only tests
cannot catch `kinds` silent misbinding. Include:

- Default/safe F migration; all framework presets and preservation veto;
  explicit legacy opt-in warnings; YAML/CLI precedence; exclude_names and
  same-spelled parameters versus unrelated module/local names.
- Eligible same-file/cross-file positional and keyword-only calls, multiple
  identities with equal spellings, closures/nonlocal references, defaults and
  annotations evaluated outside parameter scope, async functions and recursion.
- Static imports, import aliases, re-export chains/cycles, shadowing and repeated
  definitions; unresolved dynamic calls; partials/wrappers preserved in v1;
  dictionary/kwargs forwarding and mixed explicit/extra keys; duplicate keywords
  and expected TypeErrors retained. Freeze the observed import-alias failure
  before resolver enablement.
- Public `__all__`, external consumer calls, unused functions, reflection through
  aliases, callbacks, registry/container/return escapes and transitive taint.
  Methods, overrides, generated constructors, positional-only/variadic/lambda
  cases must demonstrate preservation, not merely lack of crashes.
- Real FastAPI dependencies/query/body/model construction and TestClient request
  schemas; real Flask factory routes, variable kwargs, url_for and test-client
  responses. Run in independent venvs with exact dependency versions recorded.
- Python 3.10/3.12/3.13/3.14 new-test environments, plus supported 3.9/3.11 and
  Windows/macOS in CI. Cover PEP 695/649 differences through preservation or
  supported scope proofs, never by assuming one symtable layout.
- Workers 1/2, reversed discovery/creation order, varied hash seed, repeated
  orchestrator use and source mutation after planning. Compare generated source
  bytes and canonical semantic mapping; exclude intentionally variable creation
  metadata or freeze the clock for full mapping-byte comparisons.
- Inject file/function planning failures and mid-plan allocation; assert rollback,
  dependency-closure invalidation, bounded preservation, warnings/stats, and no
  half-rewritten call sites. Compile and run the fallback artifacts.
- Mapping absent/empty/new parameters, old v1 files, duplicate identifiers,
  metadata loss/round-trip, merged maps, marker mismatches and CLI/MCP unmap.
  Prove no module export-map pollution.

Before every implementation merge: `scripts/check.sh`, four separate pytest
roots, targeted interpreter matrix, actual framework environments and
`python scripts/dogfood/run.py all --out <temporary-dir>` (A/B/D).
Before release: fresh wheel install and dogfood C, paired public-release canary,
full hosted platform matrix, schema/CLI/MCP contract verification, inspect real
artifact signatures and mappings, accurate CHANGELOG/support/help/examples,
performance/strength counts on representative projects, no real-home state
access, documented opt-out and recovery of matching artifact/mapping pairs.
Maintainer approval is separately required for release; none is requested here.

## Independently reviewable implementation phases

| PR | Scope | Default / rollback | Main risk and gate |
|---|---|---|---|
| 1: F correctness | A default preservation, explicit safe policy, migration/diagnostic/help/changelog and actual keyword/signature regressions. No new parameter planner. | `preserve_param_names=true`; proposed explicit unsafe legacy flag defaults false. Withdraw unsafe path if maintaining it cannot be justified. | Rebuilt naming changes and reduced file-wide mangling; preserve old artifact/map pairs, publish migration note. |
| 2: reader and analysis primitives | Add optional v1 metadata readers/schema/merge/marker tests; stable function identities, call/escape reason reporting, finalized plans in observation mode. | `crossfile_parameter_names=false`; no signature or keyword edits emitted. | False callable proofs, metadata compatibility; existing products must be unchanged with feature off. |
| 3: minimal parameter edits | Private/internal plain functions with uniquely proved direct same-file calls; no decorators, escapes, methods or complex kinds. Signature/body/calls edited atomically; can share planner with single-file B. | Explicit opt-in plus preservation false; negative switch disables it. Single-file `singlefile_parameter_names=false` if that path is exposed. | Scope correctness and whole-signature consistency; passing fallback/mapping/determinism suites required. |
| 4: cross-file identities | Extend to direct imports, module attributes and tested re-exports/aliases; dependency invalidation and cross-file keyword edits. | Same false defaults; disabling the feature restores parameter preservation plus existing module/locals behavior. Reverting PR 4 restores PR 3 eligibility. | Imported identity and incomplete caller discovery; observed alias regression must already be resolved in its own code review. |
| 5: optional extensions | Separate proposals for stable assignment aliases, partial contracts, supported wrappers or positional-only binding obfuscation. Real framework canaries remain mandatory. | Each capability requires explicit reviewed eligibility; unsupported forms preserve signatures. | Do not infer safety from wraps, annotations or method names. Methods/type inference and general dictionary rewriting remain deferred. |

No proposal flips parameter renaming on automatically for existing builds.
A later default change requires new evidence and a separate maintainer decision.
A per-function allowlist for public-but-closed-world functions may be introduced
only with explicit API-contract documentation; it cannot override framework,
reflection or unresolved-call preservation silently.

## Maintainer decisions (2026-10-10)

1. **Option A is approved.** Unpreset, `safe`, `balanced` and `aggressive`
   builds preserve parameter names by default. No new
   `--unsafe-rename-parameters` flag: an explicit `preserve_param_names: false`
   in YAML or on the command line keeps working but emits a warning that
   keyword calls may break. The `--init` template writes
   `preserve_param_names: true`, since its current `false` was never a user
   choice.
2. **v1 eligibility is private/internal only:** ordinary functions that are
   private, only called directly and never escape. No allowlist is required
   for v1. Public APIs stay preserved.
3. **Community feature.** The cross-file switch is `crossfile_parameter_names`,
   default false; `preserve_param_names: true` always wins. Whether single-file
   B gets its own switch is decided in that phase's PR.
4. **Optional `parameters` section in mapping v1.** The reader is upgraded
   first, so load/save keeps the section, before any build emits it. Marker
   canonicalization is decided in the reader PR; if old-marker compatibility
   cannot be shown without weakening verification, that PR proposes a format
   bump instead.
5. **Dependency-closure preservation and the build-wide parameter-off fallback
   are approved.** A strict-failure mode is deferred until a user asks for it.
6. **Order:** fix import-alias defect G first, then Option A for F (PR 1), then
   the resolver work. The performance budget and corpus are set in the PR that
   introduces the resolver.

## Scope of this design review

Only this document and its MkDocs exclusion are proposed for merge. No product
code, existing tests, versions or public behavior were changed. Current-state
experiments ran on Python 3.12/WSL with two public wheels; future parameter
implementation, actual FastAPI/Flask applications for it, other Python/platform
versions, performance and production API inventories are **not yet verified**.
The acceptance section is a plan, not a passing-results claim. Implementation
and release each require their own review and authorization.
