# Dependency-hallucination Advisory Cookbook

`--check` can flag declared dependencies (`requirements*.txt`,
`pyproject.toml`) that don't resolve on public PyPI — the signature of
"slopsquatting": an LLM hallucinates a plausible-looking package name, a
developer or an AI coding agent adds it to a dependency file, and if an
attacker has (or later does) register that name, a routine `pip install`
silently pulls in malicious code. The term was coined by Seth Larson,
Security Developer-in-Residence at the Python Software Foundation, in 2025;
a 2026 cross-model study found sets of hallucinated package names that
multiple independent LLMs invented identically.

This is an advisory, same family as `compatibility_advisory` — it doesn't
change `--check`'s exit code, and it's a scan of your dependency files, not
your obfuscation output.

Project config does not hide this project-level check. Source files matched by
`exclude_patterns` are reported in the separate `excluded_findings` bucket,
but dependency declarations beside the scan root remain eligible for the
advisory. Use `--offline` when the public-PyPI lookup is not appropriate.

## Running it

```bash
pyobfus --check src/                  # runs the dependency advisory by default
pyobfus --check src/ --offline        # skip the PyPI network lookups
```

`--check` looks for `requirements*.txt` and `pyproject.toml` (PEP 621
`[project.dependencies]` / `[project.optional-dependencies]`; classic
Poetry-style `[tool.poetry.dependencies]` isn't parsed) next to the scanned
path, verifies each declared name against `https://pypi.org/pypi/<name>/json`,
and reports one `dependency_advisory` risk per name that doesn't resolve:

```json
{
  "category": "dependency_advisory",
  "severity": "medium",
  "file": "requirements.txt",
  "message": "Declared dependency 'some-hallucinated-pkg' does not exist on public PyPI.",
  "suggestion": "Verify this is the package name you intended before installing. ..."
}
```

## The MCP tool defaults to offline

`check_obfuscation_risks` (the MCP-exposed equivalent) does **not** make
this network call unless a caller explicitly asks:

```python
check_obfuscation_risks(path)  # no dependency lookups — zero egress, matches
                                # pyobfus-mcp's default of making no outbound
                                # network calls at all
check_obfuscation_risks(path, verify_dependencies_online=True)  # opts in
```

The CLI and the MCP tool intentionally have different defaults: `pyobfus
--check` is invoked directly by a person who reads `--help`/docs and can see
`--offline`; `check_obfuscation_risks` is invoked by an AI agent on a host's
behalf, where pyobfus-mcp otherwise has zero network egress by design (see
[`MCP_SECURITY_SCAN.md`](MCP_SECURITY_SCAN.md)). Silent default egress on
that surface would be the wrong default even though the same check is
useful there too — so it stays opt-in per call instead.

## Honest limitations — read this before trusting a clean result

- **This only ever proves a useful negative**: "this name does not exist
  yet, verify it before you rely on it." It **cannot** detect the more
  dangerous case where an attacker has *already* registered a hallucinated
  name — the package then correctly resolves as "exists", and this check
  has nothing more to say about it. That's a supply-chain / provenance
  problem (typosquat detection, maintainer reputation, install-script
  auditing); this is not a substitute for a tool built for that.
- **Private package indices produce false positives.** If a requirements
  file has a `-i` / `--index-url` / `--extra-index-url` line, the report
  says so in the affected finding's `suggestion` text — a legitimate
  internal package simply won't resolve on public PyPI, and that's expected,
  not a hallucination.
- **A network failure is reported, not swallowed.** If some names can't be
  checked (DNS/timeout/PyPI outage), you get one `info`-severity risk
  summarizing how many were unverified, rather than a falsely-clean report.
  An explicit `--offline` produces no such note — you asked for it.
- **Scope is intentionally narrow.** No custom blocklist of previously
  reported hallucinated names is bundled — the check is a live existence
  test, not a lookup against a curated dataset. That keeps it honest (no
  claim of "we track known slopsquatting targets") at the cost of not
  flagging a name pre-emptively before anyone's tried to `pip install` it.

See also: [`MCP_SECURITY_SCAN.md`](MCP_SECURITY_SCAN.md) for why this is the
first outbound-network code path in the codebase and how that was reasoned
through for the MCP surface specifically.
