# Cross-file module attribute access design

Status: **implemented 2026-10-11** (PR #83 strict proofs/edits, PR #84 remaining v1 forms, and PR #85 default rollout; pending Claude Code review). Any merge or release remains a separate maintainer decision.
Date: 2026-10-11. Baseline: main
`bc04a1ee8bd283b5e89ed7bb86be0c85d7afe2da`, Core 0.6.1, including the
unreleased PR #80 advisories. The historical design baseline below precedes those implementation PRs.

## Background and evidence

Directory builds rename project module definitions and synchronize direct
`from` imports. They leave attribute spellings unchanged, so a successful build
can produce an artifact that fails when reading a configuration constant or
calling a function through its module. Limitation H in [TODO](TODO.md) records
this problem; defect G was fixed by #66 and shipped in 0.6.1. Explicit import
aliases now retain their local spelling while the imported symbol changes.

The 2026-10-11 private-project observation reported 29 instances of the generic
pattern `from pkg import config; config.ROLE_X`. This is reported downstream
evidence, not a private project reproduced here. No downstream project name,
path, actual identifier or source is included in this design or its fixtures.

Local synthetic evidence is in the gitignored directory
`docs/internal/codex-2026-10/h-design-evidence/` (**E** below): `probe.py`,
`results.json`, `summary.txt`, source/generated fixtures and mappings. The probe
logs the baseline SHA, interpreter, exact commands, exit codes, stdout and
stderr. It runs the clone through the repository's WSL Python 3.12 venv,
using isolated HOME/USERPROFILE for CLI and product subprocesses. It performs
no private-project analysis, license activation or production state access.
Normal Python executes both source and artifacts; this is a current-main
baseline, not independent public-release verification of a future fix.

Each fixture defines `pkg/core.py` with `LIMIT = 7` and
`def scale(): return LIMIT * 2`. Packages have an empty `__init__.py` unless
specified. Builds use the default Community cross-file path and save mapping;
checks use `--check --offline --no-config --json`. Original runs all exit 0.

| Synthetic fixture | Original stdout | Built run | #80 H advisories |
|---|---|---|---|
| `from pkg import core; print(core.LIMIT)` | `7` | AttributeError: module `pkg.core` has no attribute `LIMIT` | 1 |
| `import pkg.core as engine; print(engine.scale())` | `14` | AttributeError: module `pkg.core` has no attribute `scale` | 1 |
| `import pkg.core; print(pkg.core.scale())` | `14` | AttributeError: module `pkg.core` has no attribute `scale` | 1 |
| `import pkg; print(pkg.LIMIT)`; init imports LIMIT and lists it in `__all__` | `7` | AttributeError: module `pkg` has no attribute `LIMIT` | 1 |
| `from . import core; print(core.LIMIT)` in `pkg/entry.py`, run with `-m pkg.entry` | `7` | AttributeError: module `pkg.core` has no attribute `LIMIT` | 1 |
| Function-local `from pkg import core; return core.LIMIT` | `7` | AttributeError: module `pkg.core` has no attribute `LIMIT` | 1 |
| Init imports `LIMIT as PUBLIC`, lists PUBLIC in `__all__`; consumer reads `pkg.PUBLIC` | `7` | `7`, exit 0 | 0 |
| `from pkg import core; c = core; print(c.LIMIT)` | `7` | AttributeError: module `pkg.core` has no attribute `LIMIT` | 0 |

All eight builds exit 0. Medium compatibility advisories do not reject a build.
The assignment-alias result shows that absence of an H advisory does not prove
safety. These counts describe the synthetic fixtures, not the 29 downstream
occurrences. Other interpreters/platforms and proposed transformations are not
yet verified.

## Scope and minimal examples

The unit of rewriting is an `ast.Attribute` attached to a proved project module
binding, using the final export spelling of that module. It is not arbitrary
attribute, method or field obfuscation. Assume the imported package is included
in the build and its relevant binding is stable.

| Form and minimal example | Proposed completed-v1 result |
|---|---|
| `from pkg import core; core.LIMIT` | Rewrite LIMIT using pkg.core's mapping, after proving the package binding is its submodule. |
| `import pkg.core as engine; engine.scale()` | Rewrite scale; keep the explicit import alias engine. |
| `import pkg.core; pkg.core.scale()` | Rewrite scale; preserve module path segments pkg/core. Resolve each segment as a module edge, not by concatenating arbitrary attributes. |
| Init: `from .core import LIMIT; __all__ = ["LIMIT"]`; consumer: `import pkg; pkg.LIMIT` | Rewrite LIMIT using the package re-export mapping, which shares the definition's emitted identifier. |
| Init: `from .core import LIMIT as PUBLIC`; consumer: `import pkg; pkg.PUBLIC` | Leave PUBLIC unchanged: explicit re-export alias is preserved under G. A retained spelling is a successful resolved no-op. |
| `from . import core; core.LIMIT` in a package module or init | Rewrite LIMIT after package-relative resolution and module-binding proof. |
| `def run(): from pkg import core; return core.LIMIT` | Rewrite LIMIT using that function's binding identity, including with local renaming disabled. |
| `from pkg import core; c = core; c.LIMIT` | No assignment-alias propagation in v1. Leave c.LIMIT unchanged, add an escape advisory at c = core, require LIMIT in exclude_names (or module exports if usage is unknown). |
| `obj.LIMIT`, where obj is an instance or parameter | No module attribute rewrite. Same spelling alone is irrelevant. |
| `if flag: import pkg.core as engine` then `engine.scale()` | No rewrite in v1; --check retains/adds an uncertainty advisory and recommends preservation. |

V1 supports reads/calls (Load context) only. `core.LIMIT = 9`, `del core.LIMIT`
and `core.LIMIT += 1` introduce module mutation: do not rewrite them in v1;
preserve affected export names via configuration and report the mutation.
Submodule reassignment, package attribute injection and dynamic module
`__getattr__` are also outside the proof. A mutable *value* of LIMIT is not by
itself a binding-identity hazard; a replaced module path is.

## Alternatives and recommendation

| Option | Correctness risk | Protection | Implementation | Existing-user behavior |
|---|---|---|---|---|
| A: rewrite proved module attributes through final export table | False identity proofs are the main risk; unresolved uses remain limitations with diagnostics and explicit exclusions | Keeps module-name mangling for proved reads | Shared resolver, immutable edit plan, scope/control-flow guards, transform integration | Common H fixtures run correctly after rebuild; dynamic patterns still require configuration |
| B: preserve all names observed through module objects | Avoids many mismatches if detection is complete; still misses aliases, dynamic keys and external consumers | Weaker; common config/function spellings remain readable | Must plan preservation before export allocation and propagate through re-exports | Previously mangled exports become readable; generated mappings and identifiers change |
| C: A plus automatic B fallback on unresolved uses | Safer only with a bounded candidate set and complete preservation closure; a guessed fallback can still break output | Strong on proved paths, weaker on uncertain components | Largest: identity analysis plus preservation/re-export closure and allocation rollback | Implicit preservation varies with source use; protection changes need explanation |

Recommend **A with conservative proofs, explicit exclude_names for unsupported
accesses, and diagnostics derived from the same plan**. Do not advertise whole
project safety when unresolved uses remain. A directly fixes the observed H
patterns without silently lowering protection throughout a project. V1 must
report uncertainties it detects; silence cannot mean that every dynamic use has
been found. B is a documented configuration workaround. Defer C until evidence
justifies automatic preservation and a separately reviewed closure algorithm.

This choice means uncertain paths can still fail if users ignore diagnostics.
It must be stated in support/help/release notes. A successful syntax check is
not runtime validation. No speculative edit should be emitted to hide a risk.

## Rewrite rules and correctness argument

### Reuse of PR #80

`import_advisories.ImportedAccessVisitor` already traverses lexical scopes,
parameters, defaults/annotations, lambdas and comprehensions, avoids closing
over class namespaces, and recognizes dotted explicit imports.
`preflight._check_module_attributes` builds a read-only orchestrator export
plan, resolves relative imports through `_resolve_source_module`, looks up
`get_obfuscated_import`, and deduplicates findings by module/name per file.
Reuse the traversal structure, import syntax normalization, package aliases,
relative-resolution helper and export lookup. Keep preflight read-only and
never import the target project to inspect it.

The visitor's own contract says bindings are lexical candidates, **not runtime
identity proofs**. `_Bindings` scans a complete scope without execution order;
it visits conditional imports, suppresses reassigned names and does not model
branch joins or explicit global/nonlocal binding identity. `resolve` appends
attribute strings without proving each intermediate value is a module.
`from pkg import core` can bind pkg's own non-module export named core even
when a file pkg/core.py exists. A matching filename/table key cannot settle
that ambiguity. Do not turn the #80 callback directly into a mutating pass.

Extract a shared resolver API that separates candidate discovery from proof.
Preflight may report candidates even when proof fails, with appropriately
conditional wording; build edits require the strict result. Initially keep
#80 behavior under regression tests while adding strict results alongside it.
Unsupported modern annotation/type scopes must yield uncertainty rather than
borrow an outer import accidentally.

### Identity and control flow

1. Build a project module inventory from the **selected** files and package
   aliases, without executing imports. Excluded/external modules have no
   rewrite eligibility. Treat namespace packages, ambiguous roots and import
   search-path collisions as unsupported until independently tested; require
   the deployment import root to match the build's modeled root.
2. Give each lexical binding a scope identity, distinct from its spelling.
   Model Python local/global/nonlocal rules, parameters, stores/deletes,
   walrus/pattern/exception targets and comprehension bindings. Function
   definitions establish locals throughout their scope; defaults/decorators
   evaluate in the enclosing scope. Class namespaces do not supply method
   closure bindings. Use symtable where useful but reject unsupported layouts.
3. Recognize an unconditional explicit import reaching the access. For import
   aliases use the imported module identity; for dotted imports use the actual
   top-level bound package plus proved submodule edges. For from-import module
   candidates inspect the package's effective binding: an explicit static
   module re-export may prove it; a conflicting assignment/import of a value,
   unresolved export cycle or dynamic init invalidates it. File existence is
   insufficient. Prefer rejecting the entire conflicting binding in v1 to
   reasoning about import-order-dependent package mutation.
4. Require dominance/order within straight-line code: an access before import
   is not proved by a later import. For globals used by function bodies, require
   a stable module import and reject observable calls before initialization,
   circular/partial initialization and unresolved execution order. V1 can
   conservatively reject accesses within cycles rather than solve execution
   timing. A function-local import followed by access is the simplest proof.
5. V1 rejects imports under if/match/loop/try and any binding with competing
   writes, deletion, global/nonlocal mutation, or opaque exec/eval. Example
   `try: import pkg.core as engine; except ImportError: import external as engine`
   cannot share an edit: engine might be external. Leave the access unchanged,
   report uncertainty and require preservation of the possible project export.
   Even two branches importing the same module remain unsupported initially;
   later branch support may join only equal module identities on every
   reachable path, with no unbound path. TYPE_CHECKING imports are not runtime
   bindings.
6. Resolve every intermediate dotted component against module-binding edges.
   Stop at a value/class/instance/function result: `core.factory().LIMIT` and
   `core.Settings.LIMIT` do not make LIMIT a module export. Rewriting the proved
   module export Settings may be valid; rewriting its class member is not.
   Dynamic init, module replacement, module-path writes and detected escapes
   invalidate the involved proof; unsupported code gets a reason, not a
   guessed identity. External monkey-patching/plugins require an explicit
   configuration preservation contract because static source cannot rule them
   out.
7. For a proved Load attribute obtain its final name from the global table,
   including package aliases and re-export chains. No mapping means unchanged
   (preserved, external, or unresolved); distinguish these reasons in analysis.
   Replace only attr, never infer a mapping by matching a spelling in another
   module. Do not change call keywords or parameter signatures.

The local correctness claim is conditional and precise: the base evaluates to
the same project module in source and artifact, the selected export's emitted
spelling is known, and the binding is not supplied dynamically or mutated.
Replacing attr by that emitted spelling makes the read select the same value.
No evaluation order, argument, ctx or source location changes. Other object's
attributes receive no edits. These conditions explain why lexical candidates
alone, conditional fallback and assignment propagation are insufficient.

### Planning and application

Plan against the original AST before local/export/import transformations.
After export/re-export policy is finalized, record immutable per-file edits:
relative file, scope/binding identity, original source span, expected attribute
spelling, canonical target module and emitted spelling. One identity may have
multiple access sites; every site must be validated. Plans allocate no new
names. Export allocation remains the only source of attribute spellings.

Apply validated attribute edits early in `_transform_single_file`, before
local-name transformations can replace a base identifier (the evidence shows
function-local core becomes I3). Preserve the original tree used by
ImportCollector, class/local binding markers, statement metadata and existing
content-transform order. Reparse/match source coordinates or use validated
node identities; never resolve again from a partially renamed tree. Edits must
be serializable for ProcessPoolExecutor. Reject conflicting edits and source
hash mismatches. Same-file workers 1/N must consume the identical final plan.

This feature is a correctness transform, so a required planned edit that cannot
be applied must fail before publishing a successful build; leaving renamed
definitions with old attributes is not a valid fallback. Observation/planning
uncertainty emits no edit and retains an advisory. A future C downgrade would
have to preserve definitions, imports, __all__, re-exports and all access sites
atomically and recompute allocation before workers; it is not included here.
Reset plans on orchestrator reuse and retain deterministic file/export ordering.

## Unsupported and dynamic access policy

These are proposed diagnostics, not claims that #80 already covers them.
Recognize aliases of reflection/import helpers when statically possible; an
unknown helper is not evidence of safety. Never rewrite general strings or
arbitrary dictionary keys. `exclude_names` currently preserves spellings across
the build; do not invent a module-qualified exclusion syntax in this feature.

| Pattern | V1 strategy |
|---|---|
| `getattr(core, "LIMIT")` | No string rewrite. --check advisory; require LIMIT in exclude_names. A computed key requires preserving all possibly accessed exports or excluding the module from mangling under a documented boundary. |
| `hasattr(core, "LIMIT")` | Same preservation; test original boolean so silent false is caught. Include setattr/delattr as mutation hazards. |
| `core.__dict__["LIMIT"]` | Leave magic attribute/key unchanged, advise preservation of LIMIT; computed/enumerated keys require preserving affected module exports. |
| `vars(core)` | No dictionary/key rewrite; advise preserving module exports if dictionary lookup/enumeration escapes analysis. |
| `sys.modules["pkg.core"].LIMIT` | Module path strings stay unchanged; no identity proof/rewrite in v1. Add targeted advisory where recognizable, require LIMIT preservation. Replacement of sys.modules entries invalidates direct-import proofs for affected modules. |
| `importlib.import_module("pkg.core").LIMIT` | No dynamic-import proof in v1. --check keeps dynamic-import advice and adds project-export preservation guidance when the literal target is known. Computed target needs a configured plugin/API boundary. |
| `consume(core)` or returning/storing core | Module-object escape advisory at the source use, no interprocedural rewrite. Preserve exports the consumer may inspect; preserve the module's exports if unknown. No claim to discover arbitrary external consumption. |
| `from pkg import *; core.LIMIT` | No star-created module binding inference in v1, even with literal __all__. --check reports the star uncertainty; preserve potentially consumed exports. Existing direct-symbol star behavior is separate. |
| Plugins/entry points importing across packages | No closed-world assumption for external consumers. Preserve externally consumed export names via exclude_names/configuration; add advice for recognizable registration/dynamic imports. Unseen consumers require documentation and maintainer knowledge, not a clean-scan guarantee. |
| `c = core; c.LIMIT` | No alias propagation; report the assignment as escape and preservation guidance. The existing #80 silence is a gap to cover, not a support guarantee. |

When a literal or finite candidate set identifies the affected name, the advice
is bounded to that spelling. Unknown keys/targets must not silently turn into
a guessed single-name exclusion. For preserved names, report an informational
mitigation instead of saying the attribute will raise AttributeError.

## Interactions with existing mechanisms

- **__all__ and re-exports:** use the orchestrator's two-pass registration and
  package aliases, not a second rename allocator. Non-aliased internal
  re-exports share the source identifier and AllListUpdater keeps the emitted
  list consistent. Imported external names keep the spelling supplied by their
  import (the 0.5.25 rule); do not invent a definition mapping for them. Explicit
  `as` re-exports keep their local alias under G, including `X as X`. Chained
  module re-exports need binding identity as well as an export table. Dynamic
  __all__, unresolved cycles and dynamically injected exports remain advisory
  cases; limitation C is not fixed by this proposal.
- **Defect G:** `from pkg.core import scale as action` must still import the
  emitted scale name but call action; `import pkg.core as engine` keeps engine
  while its proved scale attribute changes. Do not reuse ImportCollector's
  flat spelling map as the new binding model. TODO defect I demonstrates
  function imports overwriting module imports when locals are disabled; D
  demonstrates global rebinding. New strict analysis must reject those hazards
  and tests must distinguish H correctness from unresolved existing I/D bugs.
  If an existing pass prevents a promised H scope from being correct, fix that
  prerequisite in a separate reviewed PR before enabling the scope.
- **exclude_names / presets:** the effective preservation policy wins before
  allocation. A retained LIMIT is a no-op both in the definition and access;
  unrelated names may still be mangled. Framework presets and class fields
  retain their current policies. No preset or Pro entitlement can override
  proof guards. `preserve_param_names` affects signatures, not these module
  attributes; retain it and do not rewrite keyword keys. H must work with
  crossfile_local_names both true and false.
- **--no-cross-file:** the feature runs only in CrossFileOrchestrator. The
  separate per-file path, its current attributes and behavior are unchanged.
  Check wording must reflect the effective build mode; do not suppress its
  existing risks by pretending this cross-file feature protects that path.
- **Mapping / --unmap:** no new identifier is allocated for an access. Reuse
  existing mapping v1 `modules` and `global` entries for the exported definition;
  `reverse_qualified` / token-based unmap_text already restore dotted segments.
  No attribute-access section or format bump is needed for name restoration.
  Preserve statement metadata so existing optional `files` line tables and
  `unmap_trace` still restore locations. This is a design conclusion requiring
  generated-trace tests, not a claim that a future emitter has passed them.
  Mapping marker verification, save/load/merge and CLI/MCP envelopes remain
  intact. Do not add per-use aliases to global_map or pollute locals.
- **#80 diagnostics:** a proved, scheduled rewrite no longer gets the H
  AttributeError advisory when the feature is on. A proved preserved spelling
  is a no-op. Feature off retains legacy H warnings. Ambiguous bindings,
  dynamic/escaped/mutated accesses and unsupported forms continue to warn,
  using “may fail” where identity is uncertain. Diagnostics consume the same
  eligibility result/config as the build; do not suppress merely because a
  syntactic candidate exists. Keep separate parameter and injected-name advice.
  Preserve status/ai_hint/next_tool and risk/SARIF contracts. New reason/count
  fields, if needed, are additive and reviewed with CLI/MCP schema tests.

## Defaults and migration

Recommend the final correctness fix **on by default for cross-file builds**,
with `crossfile_module_attributes: true` and the CLI pair
`--crossfile-module-attributes / --no-crossfile-module-attributes`. The negative
switch restores legacy attribute behavior and advisories; it is a compatibility
escape hatch, not a promise that the legacy artifact runs. It does not disable
module export/local renaming. Explicit exclude_names is the safer workaround
for unsupported forms. CLI overrides YAML; presets must not secretly disable
this correctness pass. No new general attribute-mangling switch is proposed.

PR 1 introduces the false-default opt-in switch for its narrow scope (see the
revised plan). Flip the default in PR 3 only after all completed-v1
forms and negative guards pass. This design itself adds no config or switch.
A rollback to false restores the old limitation and check warnings; keep
previous artifact/mapping pairs available, never mix versions within an output
tree. Incremental cache identity must include tool version and effective switch
so upgrading/reconfiguring cannot reuse an old unsafe build.

Proposed implementation CHANGELOG entry (not added by this design PR):
“Fixed cross-file reads and calls through statically proved project module
imports, including package re-exports and relative/function-local imports.
Dynamic imports, module escapes, ambiguous bindings and reflection still need
preserved export names; --check explains detected unsupported patterns.”
At the default-change release, say **rebuild the complete project and retain
its matching mapping**. Existing artifacts are not repaired by upgrading the
installed tool; rebuilt source/mapping/build identifiers may change. Update
support matrix, config/help/schema, README and relevant edition-facing docs
with actual support and limitations; do not announce broad attribute support.

## Edition decision

Recommend Community under [Edition Boundary Policy](EDITION_BOUNDARY_POLICY.md).
Users are Python application/library maintainers; there is no distinct managed
service buyer. Evidence is the current-main runtime failure and the reported
configuration-module pattern. This is correctness and compatibility for existing
free project-wide mangling, with local verification/debugging, not stronger
cryptography, runtime control or buyer attribution. No existing capability is
removed or moved to Pro. Source remains in Apache-2.0 Core; Pro builds reuse the
same correctness primitive. Each implementation PR records user/buyer/problem/
evidence and updates affected product surfaces together. This design changes no
tier and does not introduce a paywall.

## Behavioral acceptance plan

Every positive fixture builds then runs source and artifact in separate fresh
processes and compares stdout, exit code and relevant error/side-effect behavior.
Syntax-only assertions are insufficient; negative tests also inspect emitted
AST to establish which attribute did or did not change.

- All scope-table forms, constants/classes/functions, alias imports, multi-name
  imports, relative levels and init imports; package re-export chains, explicit
  alias/no-alias/X as X, external re-exports, static __all__ and star direct
  symbols. Test real external consumers with explicitly preserved API names.
- Non-module same-spelled attributes, parameter/local/class/comprehension/
  exception/walrus/pattern shadowing, nested functions, decorators/defaults,
  closures, class-to-method boundaries, global/nonlocal writes and deletes.
  Access before import, caller before initialization, conditional imports,
  TYPE_CHECKING, loops, try/except fallback and equal/different branch targets.
  Unsupported cases must be unchanged and get accurate uncertainty advice;
  run preserved configurations to show their supported recovery works.
- Package exports a value named core beside core.py; submodule monkey-patching,
  sys.modules replacement, circular/partial imports, dynamic __getattr__,
  __all__, injected exports and missing/excluded/namespace package modules.
  Prove no module proof is fabricated by concatenating object attribute names.
- Reflection table forms, computed keys, helper aliases, assignment/return/
  argument/container escapes, writes/deletes/augassign and plugin entry points.
  Test hasattr's boolean and dictionary key enumeration as well as crashes.
  Do not report all dynamic patterns as statically solved.
- A synthetic config-module application with several ROLE_X-style constants,
  multiple consumers, a package-relative consumer and a function-local import;
  no private names/paths/data. Compare original/generated behavior and show
  preserving one explicit name does not disable unrelated eligible rewrites.
- G regression combinations plus locals on/off, exclude_names, all framework
  presets, preserve_param_names on/off (attribute behavior only), and unchanged
  --no-cross-file behavior. Track I/D separately; do not mark them fixed by H
  or hide a failing combination with a broad exclusion.
- Real generated traceback through module.scale and a failing access inside a
  callee; CLI --unmap and MCP unmap recover names and statement locations.
  Check mapping v1 save/load/merge, preserved-name absence, matching/wrong
  marker warnings, qualified names and old-reader name restoration. Compare
  canonical semantic maps; ignore timestamp/root metadata where intentional.
- Worker counts 1/2, reversed discovery order, varying hash seed, repeat builds,
  repeated orchestrator use and source mutation between plan/apply. Inject
  mismatched span/hash and ensure no successful half-rewritten product.
  Benchmark analysis on a fixed synthetic corpus; set the performance budget
  during PR 1 review, not an invented result in this document.

Before each implementation commit/merge run scripts/check.sh and the four
Python test roots separately with normal HOME and tmp_path state isolation.
CI covers Python 3.9–3.14 and supported platforms. Before release use fresh-wheel
canaries and an independent public-release baseline, normal Python execution,
schema validation and hosted artifact checks as appropriate under the
self-dogfooding policy. No implementation tests, full interpreter matrix or
performance results are claimed by this design-only PR.

## Independently reviewable PR plan

Revised at acceptance (decision 8): the first PR combines strict binding
observation with the first attribute edits, and covers the configuration-module
form seen in the reported evidence instead of deferring it.

| PR | Boundary | Acceptance / default |
|---|---|---|
| 1: strict proof + first edits | Extract the candidate/proof API; prove and rewrite Load attributes for **unconditional** `from pkg import mod; mod.X` and `import pkg.mod as alias; alias.X`, at module level and function-local; original-AST edit plans, export lookup, early worker application; false-default config `crossfile_module_attributes` and CLI pair; #80 advisories unchanged when off and suppressed only for scheduled rewrites when on. | Opt-in original/artifact runtime equality for both forms, including a synthetic config module with several constants and multiple consumers; negative guards (same-spelled object attribute, package value shadowing a submodule, late/conditional/try import, reassignment, writes) leave AST unchanged; locals on/off; mapping/`--unmap` with a real traceback; workers 1/N identical; plan/apply mismatch fails the build. Off preserves old bytes and diagnostics. Performance budget agreed here. |
| 2: remaining v1 forms | Dotted `import pkg.mod` edges, relative `from . import mod`, package `__init__` re-exports including `__all__` and G aliases; escape advisories for `c = mod`, arguments/returns and reflection. Fix interfering I/D prerequisites separately first. | All scope-table forms rebuilt correctly when eligible; adversarial package shadowing rejected; preserved-name recovery runs; #80 gap for assignment aliases closed by an advisory. Default remains false. |
| 3: default correctness rollout | Flip default true; support matrix, migration/cache handling, check/build parity, edition-facing docs and full contract verification. | Full scope/negative/runtime/mapping matrix plus fresh-wheel/public-baseline checks pass. Release note requires complete rebuild. No automatic C preservation. |
| Later proposals | Assignment propagation, branch joins, literal reflection handling, or C preservation closure, each separately justified. | New proof contracts and runtime evidence required; no silent scope expansion or blanket preservation. |

Every PR is reviewed by Claude Code; the maintainer decides merge and any
release separately. This design PR neither merges changes nor tags/publishes.

## Historical design-only delivery boundary

Only this document and its MkDocs exclusion are proposed. Like
CROSSFILE_PARAMETER_RENAMING_DESIGN.md, it remains outside product-site
navigation while the proposal is reviewed on GitHub. Internal evidence remains
gitignored in the main checkout; the public conclusions and synthetic examples
above are self-contained. No pyobfus source, test implementation, version or
CHANGELOG is changed. Future PR acceptance criteria are plans, not results.

## Questions for maintainer decision

These were Codex recommendations; the accepted outcomes are under Maintainer decisions below.

1. **Choose A, B or C?** Recommend A with conservative proofs and explicit
   exclusions for unsupported paths. It repairs common H patterns while
   retaining mangling and avoids an unproved automatic preservation closure.
2. **Default and rollback switch?** Recommend final default true with
   crossfile_module_attributes and the CLI pair above; false during PR 2/3,
   default flip only after completed-v1 acceptance. A correctness fix should
   eventually protect ordinary existing directory builds without opt-in.
3. **V1 eligibility boundary?** Recommend all completed-v1 scope-table import
   forms and Load reads/calls, rejecting conditional/try fallback, ambiguous
   package bindings and writes. Assignment aliases and dynamic access remain
   unsupported with preservation advice; reliable identity outweighs coverage.
4. **Failure policy?** Recommend fail a build on validated-plan application
   mismatch, and leave pre-analysis uncertainty advisory-only. A partial edit
   cannot claim correctness; uncertain legacy patterns retain documented risk.
5. **Automatic preservation?** Recommend defer C and require exclude_names
   for detected escapes/reflection/plugins initially. Unknown consumers and
   computed keys need an explicit API boundary rather than guessed exclusions.
6. **Mapping contract?** Recommend reuse v1 without an attribute section;
   edits use existing definition identifiers and preserve statement locations.
   Require actual CLI/MCP traceback and marker regressions before rollout.
7. **Edition and product surfaces?** Recommend Community across all presets
   and tiers; correctness stays free. Update actual help/schema/support and
   CHANGELOG in implementation PRs, with a complete-rebuild release notice.
8. **Sequence and review gates?** Recommend the four PRs above, beginning with
   observation of one alias-import binding and no output edits. Agree corpus/
   performance budget in PR 1, handle interfering I/D prerequisites separately,
   and require Claude review plus maintainer merge/release decisions.

## Maintainer decisions (2026-10-11)

Recorded after Claude Code review; the maintainer accepted Claude's recommendations.

1. Option **A**: rewrite statically proved project module attributes only; unsupported accesses keep advisories and require `exclude_names`.
2. Opt-in (`crossfile_module_attributes: false`) during PRs 1–2; default **true** in PR 3 after acceptance, with `--no-crossfile-module-attributes` as the compatibility escape hatch.
3. V1 boundary as proposed: unconditional import forms, Load reads/calls only; conditional/try imports, assignment aliases, writes and dynamic access are not rewritten.
4. A validated plan that cannot be applied fails the build; analysis uncertainty stays advisory.
5. No automatic preservation (C) for now.
6. Reuse mapping v1 with no attribute section; real-traceback CLI/MCP `--unmap` regressions are required before the default flip.
7. Community, all presets and tiers.
8. Three PRs as revised above: the first combines proof and edits and covers `from pkg import mod; mod.X`, the most common reported form, together with `import pkg.mod as alias`.

