# Check generated names before delivery

`--verify-names` is an opt-in Community build check merged in PR #98.
It is not yet published and is absent from PyPI 0.7.0; the commands below
apply to a source checkout or candidate build containing the change. It supplements `--verify-syntax`: valid Python can still refer to
a name that a renaming transform failed to bind.

```bash
pyobfus src/ -o dist/ --verify-syntax --verify-names \
  --build-report evidence/build-report.json --json
```

The checker records source modules before writing output, including for
in-place builds. It then uses `ast` and `symtable` to find newly unbound global
names in each corresponding output module. It never imports or executes source
or generated code. Python encoding declarations and UTF-8 BOMs are respected.

## Results and coverage

- Newly unbound names fail the build with exit 1. JSON output uses
  `error_type: "NameVerificationError"` and carries the result in `verification`.
- Missing, unreadable or unparsable output also fails verification. An unreadable
  source baseline cannot pass verification.
- Star imports make a module's bindings unknown. Such modules are explicitly
  listed as skipped; the build can succeed, but text output warns that coverage
  is partial. Source modules that cannot be parsed are also listed as skipped
  if their output can be parsed. Review those modules separately.
- Successful JSON builds include `name_verification`. With `--build-report`,
  the same result is recorded in the report, separately from the existing
  syntax `verification`. Incremental cache hits retain the name-check result.
- Without `--verify-names`, the JSON and report shapes are unchanged.

`names_valid: true` means no failure was detected among the checked pairs;
it is not a pass for skipped modules. Inspect `coverage_complete` and `skipped`
alongside it. Source/output read failures and output parse failures are errors, not successful
skips; unparsable source baselines are explicitly listed as skipped.

The result includes `files_expected`, `files_checked`, `files_skipped`,
`coverage_complete`, `skipped` (relative path and reason), `errors`,
`names_valid`, and `execution_performed: false`. Full coverage means every
selected source/output pair was analysed; it does not mean the output is safe
to ship. On failure, generated files remain on disk and no completed build
report is written. Do not distribute the failed output.

## What it does not prove

This is a differential global-name check, not a Python interpreter or a
control-flow analysis. It cannot prove import availability, attribute correctness,
the timing of assignments, local-variable binding, or values supplied by dynamic
code. Names already unbound in the source baseline are not reported unchanged.
Decorators or other dynamic code can supply names that static analysis cannot
see, so a finding is a possible `NameError`, not proof that every execution fails.
Reported lines are the first syntactic use of the reported name, when available.

Inspect a finding against the original source. For unsupported dynamic names,
`exclude_names` may be appropriate; do not suppress a finding without checking
the generated code. Continue to run the application's tests against the output.
The check is not enabled automatically by `--verify-syntax`; no new MCP tool or
MCP build option is introduced by this change.
