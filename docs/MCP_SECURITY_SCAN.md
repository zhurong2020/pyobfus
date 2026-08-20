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

## Reproducing this yourself

The commands above are the complete reproduction — no pyobfus-specific
tooling is involved, and no account/API key is required for the analyzers
used. If you want the deeper LLM/behavioral/API analyzers too, see
`mcp-scanner --help` for the relevant flags and environment variables.
