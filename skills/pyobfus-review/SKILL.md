---
name: pyobfus-review
description: >-
  Review a Python project for source-protection readiness without changing
  anything: what would break under obfuscation, which framework preset fits,
  which files the current config already excludes, and exactly which artifacts
  a build would emit. Use when the user asks "is this safe to obfuscate?",
  "what would protecting this break?", "review before we ship", or wants a
  pre-merge / CI check. Read-only by design — it never obfuscates, never
  writes deliverables, and never runs project commands. To actually produce a
  protected build, use the pyobfus-protect skill instead.
---

# Review a Python project with pyobfus (read-only)

Your job: tell the user what protecting this project would cost them, before
anyone changes a byte. You produce a judgement, not an artifact.

## Boundary — read this before running anything

This skill is read-only. Within it:

- **Never** run an obfuscation build, not even into a temp directory.
- **Never** write, move, or delete project files. `--check`, `--dry-run` and
  `--sarif` are the only pyobfus modes you use here. `--sarif PATH` writes one
  report file, so only use it when the user asked for CI output and name the
  path they chose.
- **Never** run the project's own commands (tests, entry points, install
  steps). Nothing in a review needs to execute the user's code.
- If the user actually wants a protected build, say so plainly and switch to
  the **pyobfus-protect** skill. Do not quietly start building.

## Step 1 — scan

Prefer the MCP tool if the `pyobfus-mcp` server is connected:

```
check_obfuscation_risks(path="src")
```

Otherwise use the CLI (`pip install pyobfus`):

```bash
pyobfus --check src/ --json
```

Both return the same shape: `severity_counts`, per-finding `file`/`line`/
`category`, detected `frameworks`, a `suggested_preset`, the
`effective_config` that was applied, and the files that config already
excludes.

The scan is config-aware by default: it reads the project's `pyobfus.yaml` and
reports findings that the configuration already mitigates separately from the
ones that still stand. Do not present a mitigated finding as an open risk.

**The two front ends differ on network access, so check which one you are
using before telling the user anything about it.** The CLI's `--check` runs
the dependency-hallucination advisory **by default**, which looks each declared
dependency up on PyPI; pass `--offline` to skip it. The MCP tool is the
opposite: it makes no network call unless you pass
`verify_dependencies_online=true`. If the user is on a restricted network or
cares that nothing leaves the machine, say `--offline` explicitly.

## Step 2 — preview what a build would produce

```bash
pyobfus src/ -o dist/ --dry-run --json
```

`--dry-run` writes nothing. It returns a versioned `plan`: the effective
configuration, every file selected or excluded and why, and the artifacts a
real build would emit, each tagged `ship`, `retain-internal` or `optional`.

Read the artifact roles back to the user. The one that matters: a mapping file
is tagged `retain-internal`, meaning it is the de-obfuscation key and must
never be shipped or committed publicly.

## Step 3 — report

Give the user four things, in this order:

1. **Verdict.** Ready, ready with a named preset, or blocked by specific
   high-severity findings.
2. **What would break**, grouped by cause rather than by file: dynamic
   attribute access, `eval`/`exec`, framework reflection, model loading.
   Name the file and line for each; the user has to go look.
3. **The preset you would use** and why that one. If a framework was detected,
   say which signal detected it.
4. **What the build would emit**, from the dry-run plan, with the mapping's
   `retain-internal` role stated explicitly.

Quote the numbers from the JSON. Do not estimate, and do not soften a
high-severity count into "a few issues".

## For CI

```bash
pyobfus --check src/ --sarif pyobfus.sarif
```

SARIF 2.1.0 uploads to GitHub code scanning. Exit code is `1` when
high-severity findings exist, which is the intended gate.

There is also a published GitHub Action that handles the exit-code trap
correctly (findings and tool errors are separated, so `|| true` is not
needed): `uses: zhurong2020/pyobfus-action@v1`.

## Honest limits of a review

- A clean `--check` does not promise the build will work. It means the known
  breakage patterns were not found. Verification happens in a real build, and
  that belongs to the pyobfus-protect skill.
- Obfuscation is a deterrent against casual reading, not cryptographic
  security: the shipped code must still run, so anything it needs at runtime
  is present in what you hand over. Say that plainly if the user's expectation
  sounds higher.
- Recent published work finds strong code models still reason over obfuscated
  source at close to their normal accuracy. Do not tell the user this makes
  their code unreadable to AI.

## Installing this skill

Copy it into whichever location your agent reads:

```bash
# Claude Code
mkdir -p ~/.claude/skills && cp -r skills/pyobfus-review ~/.claude/skills/

# Repository-scoped, picked up by agents that follow the .github/skills
# convention (GitHub Copilot, Cursor, Codex CLI and others)
mkdir -p .github/skills && cp -r skills/pyobfus-review .github/skills/
```
