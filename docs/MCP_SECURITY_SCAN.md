# Independent MCP security scan

Public MCP directories currently host servers of widely varying security
quality, and as of mid-2026 there is no widely adopted certification or
vetting system for publicly distributed MCP servers. `pyobfus-mcp-verify`
(see the [main README](../pyobfus_mcp/README.md#verifying-tool-integrity))
already answers one part of that gap — proving the installed package's tool
descriptions match what was shipped at release. This document covers a
different, complementary question: does an independent, third-party scanner
find anything malicious in the running server?

## Tool used

[Cisco's `mcp-scanner`](https://github.com/cisco-ai-defense/mcp-scanner)
(PyPI: `cisco-ai-mcp-scanner`), a maintained open-source MCP security scanner
with static YARA malware-signature analysis, tool-poisoning detection, and
dependency-vulnerability auditing. Chosen over smaller/newer alternatives
(Proximity, mcp-audit, agent-audit) because it's the most credible brand in
this specific space and its offline analyzers (YARA, dependency audit) need
no API keys or external accounts — the whole scan is reproducible by anyone
without signing up for anything.

## What was scanned

The **real published PyPI package**, not a local editable install, to
represent exactly what a user gets:

```bash
python3 -m venv /tmp/pyobfus-mcp-scan-target
/tmp/pyobfus-mcp-scan-target/bin/pip install pyobfus-mcp   # installs 0.3.6 as of this scan
```

```bash
pip install cisco-ai-mcp-scanner
mcp-scanner --analyzers yara,vulnerable_package --stats \
  stdio --stdio-command /tmp/pyobfus-mcp-scan-target/bin/pyobfus-mcp
```

This launches `pyobfus-mcp` as a real stdio MCP server, does a live
`initialize` → `tools/list` handshake against it, and runs each of the 8
exposed tools' descriptions/schemas through the YARA and dependency-audit
analyzers.

## Result (2026-08-20, `pyobfus-mcp` 0.3.6)

```
=== Scan Statistics ===
Total tools: 8
Safe tools: 8
Unsafe tools: 0
Severity breakdown: {'HIGH': 0, 'UNKNOWN': 0, 'MEDIUM': 0, 'LOW': 0, 'SAFE': 16}
Analyzer stats: {'yara_analyzer': {'total': 8, 'with_findings': 0},
                 'vulnerable_package_analyzer': {'total': 8, 'with_findings': 0}}
```

All 8 tools (`protect_project`, `check_obfuscation_risks`,
`generate_pyobfus_config`, `unmap_stack_trace`, `list_presets`,
`explain_preset`, `recommend_tier`, `start_pro_trial`) came back `SAFE` with
zero findings on both analyzers.

The `vulnerable_package_analyzer` result was corroborated independently: the
scanner's own `vulnerable-package` subcommand hit a CLI argument-parsing bug
in this scanner version when pointed at a directory (`pip-audit exited with
code 2`, `--desc: invalid VulnerabilityDescriptionChoice value`), so instead
`pip-audit --strict` was run directly against the same installed environment
as a cross-check: `No known vulnerabilities found`.

## Honest scope — what this does and doesn't prove

- **What it proves**: no known YARA malware signatures matched the tool
  descriptions/schemas, and no dependency in the installed package's tree has
  a publicly known CVE as of the scan date. Same honest register as this
  project's [PEP 740 attestation verification](RELEASE_PROVENANCE_VERIFICATION.md) —
  a real, reproducible, third-party-tool result, not a claim of comprehensive
  security review.
- **What it doesn't prove**: this scan only ran the fully-offline analyzers
  (`yara`, `vulnerable_package`). The scanner also offers `api` (Cisco AI
  Defense cloud API), `llm` (LLM-based prompt-injection/semantic analysis),
  `behavioral` (docstring-vs-behavior mismatch via LLM), and `virustotal`
  analyzers — all of which require an API key or account and were not run.
  A clean YARA/dependency-audit result does not substitute for those deeper
  checks; it substitutes for "nobody has looked at all."
- This is a point-in-time result tied to `pyobfus-mcp` 0.3.6 and whatever
  YARA ruleset / OSV database `cisco-ai-mcp-scanner` shipped with on
  2026-08-20. Re-run it after any release that changes tool descriptions,
  schemas, or dependencies.

## Manual check: SSRF / arbitrary-URL fetch surface

Neither `mcp-scanner`'s offline analyzers nor the scan above specifically test
for server-side request forgery (SSRF) — a class the MCP ecosystem has been
paying closer attention to: a 2025 audit of 7,000+ public MCP servers found
36.7% vulnerable, structurally, wherever a tool accepts a user- or
LLM-supplied URL without validation and fetches it
([OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)).

`pyobfus-mcp`'s 8 tools (`protect_project`, `check_obfuscation_risks`,
`generate_pyobfus_config`, `unmap_stack_trace`, `list_presets`,
`explain_preset`, `recommend_tier`, `start_pro_trial`) all operate on local
file paths and config, not remote resources, so this class shouldn't apply —
but "shouldn't" isn't a security claim, so it was checked directly rather
than assumed:

```bash
grep -rln -i "requests\.\|urlopen\|httpx\|urllib\.request\|aiohttp\|\.get(http" \
  pyobfus_mcp/pyobfus_mcp/*.py pyobfus/core/*.py
```

**Update (post-0.3.7, `[Unreleased]`)**: this now returns one match —
`pyobfus/core/dependency_advisory.py` (`urllib.request.urlopen`), added for
the dependency-hallucination advisory. `check_obfuscation_risks` reaches it
transitively (via `PreflightChecker`), which is why the grep scope above now
also covers `pyobfus/core/`, not just the `pyobfus_mcp` package itself —
scoping the check to only the MCP package's own files would have kept
reporting a stale "zero matches" once a core module it calls into gained
network code. This still isn't the SSRF pattern the OWASP cheat sheet
describes, for a specific reason: the request target is
`https://pypi.org/pypi/{name}/json` with a hardcoded host — the only
caller-influenced input is a PEP-503-normalized package name substituted
into the *path*, not the host, and it's percent-encoded
(`urllib.parse.quote`) before use. No parameter on any tool accepts a URL or
a host, so no caller can redirect the request anywhere but `pypi.org`. It's
also off by default: `check_obfuscation_risks` only makes this call when a
caller explicitly passes `verify_dependencies_online=True` — the MCP
surface's default egress remains zero. This is a point-in-time grep against
the current source, not a standing guarantee — re-check it (and re-confirm
the "hardcoded host, no URL/host parameter" property still holds) after any
release that touches this code path.

## Reproducing this yourself

The commands above are the complete reproduction — no pyobfus-specific
tooling is involved, and no account/API key is required for the analyzers
used. If you want the deeper LLM/behavioral/API analyzers too, see
`mcp-scanner --help` for the relevant flags and environment variables.
