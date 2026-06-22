---
title: 'pyobfus: An AST-based Python obfuscator with reverse stack-trace mapping for AI-assisted development'
tags:
  - Python
  - software protection
  - obfuscation
  - intellectual property
  - AI-assisted development
  - developer tools
authors:
  - name: Rong Zhu
    orcid: 0009-0008-6087-0581
    affiliation: 1
affiliations:
  - name: Independent Researcher, Shanghai, China
    index: 1
date: 22 June 2026
bibliography: paper.bib
---

# Summary

`pyobfus` is an open-source, source-to-source obfuscator for Python built on the
standard-library abstract syntax tree (`ast`). It renames identifiers, encodes
string and numeric literals, and rewrites imports consistently across a
multi-file project, emitting ordinary `.py` files that run on any CPython 3.9
through 3.14 interpreter without a native runtime, bytecode virtual machine, or
platform-specific binary. Its distinguishing feature is a reverse mapping
workflow: each build can record an identifier map that later translates an
obfuscated production stack trace back to the original names, so a developer, or
an AI coding assistant working on their behalf, can debug shipped code without
weakening the protection or distributing the map. The same operations are exposed
through a machine-readable JSON command-line interface and a Model Context
Protocol [@mcp] server, letting agents such as Claude Code and Cursor invoke
`pyobfus` directly inside a conversation. `pyobfus` follows an open-core model:
the Community Edition described here is licensed under Apache-2.0, and a separate
Professional Edition adds commercial protection features.

# Statement of need

Python is distributed as source, so shipping proprietary or research software
written in Python exposes its logic to anyone who receives it. The established
options for protecting that code each impose a cost. Compilers such as Nuitka and
Cython produce platform-specific binaries; commercial tools such as PyArmor rely
on a bundled native runtime. These approaches complicate deployment and, more
fundamentally, make the program hard to debug: the artifact that fails in
production no longer resembles the author's source.

That debugging gap has widened as developers increasingly diagnose failures with
AI assistants that reason over identifiers, file paths, and stack traces. An
obfuscated traceback full of names like `I0` and `I7` is opaque to both the
developer and the assistant, which forces a choice between protection and
maintainability. `pyobfus` is designed to remove that choice. Because it emits
plain Python and records a reversible identifier map, an obfuscated traceback can
be mapped back to meaningful names on demand (`--save-mapping` then `--unmap`),
keeping the AI-assisted debugging loop intact while the shipped artifact stays
protected; a worked example of this reverse-mapping loop ships in the repository
(`examples/ai_debugging`). Framework-aware presets for FastAPI, Django, Flask, Pydantic, Click,
and SQLAlchemy preserve the names that those frameworks resolve by reflection, a
common cause of breakage in naive obfuscators. The JSON CLI and the MCP server
expose these capabilities to agentic development workflows directly, rather than
as a manual post-processing step.

`pyobfus` originated in a concrete research-software need. A production
cardiovascular-imaging analysis pipeline had to be shared with a clinical
research group's graduate students and collaborators, and later with reviewers,
without disclosing methods that were unpublished and under patent review, while
its maintainers continued to debug the distributed build with AI assistance. This situation recurs across
computational research: a group must circulate runnable code so that others can
reproduce or extend a result, yet cannot release the source outright because of
embargo, competition, or intellectual-property constraints — as when a
clinical-AI pipeline must be validated by a hospital or a third party without
disclosing the model code. `pyobfus` is built as reusable infrastructure for
that need rather than a single-purpose script. It
increases the effort required to recover unpublished methods from distributed
Python while preserving the reproducibility and AI-assisted debuggability that
the collaboration still depends on.

# Functionality and implementation

`pyobfus` operates entirely on the `ast` representation of a program. Multi-file
projects are processed in two phases: a scan phase builds a global symbol table
that records every renamable definition and its cross-module references, and a
transform phase applies the rename map consistently while rewriting `import`
statements and `__all__` exports so that the obfuscated package still imports
correctly. The Community Edition provides name mangling, base-encoded string
literals, value-preserving numeric obfuscation, optional removal of
AI-provenance markers, the framework presets, and the reverse-mapping tooling. A
preflight risk scanner reports constructs that obfuscation can break, such as
`eval`, dynamic attribute access, and framework reflection, and every command
emits a stable JSON schema with a next-step hint for automated callers. The
transform is fast: obfuscating Click (about 11,000 lines) and Rich (about 38,000
lines) completes in two to three seconds, and the pure-Python output byte-compiles
cleanly and is 17 to 19 percent smaller than the source, since docstrings and long
identifiers are removed.

The project adopts an open-core model. The Community Edition (Apache-2.0, and the
subject of this paper) provides the core obfuscation features; a separately
licensed Professional Edition adds further protection mechanisms such as AES-256
string encryption, control-flow flattening, per-buyer forensic watermarking
[@clasp], a runtime secret vault, and production-traceback encryption. A subset
of these Professional mechanisms is the subject of a pending Chinese invention
patent (application number 202610712171X). The Community Edition described here
is fully open source and self-contained: it builds, runs, and passes its test
suite without any Professional-Edition or patented component. Cryptographic
operations throughout build on the `cryptography` library [@cryptography] rather
than bespoke primitives.

`pyobfus` is actively maintained and continuously tested: it ships with more than
1,000 automated tests at roughly 90% line coverage, runs continuous integration
across CPython 3.9 to 3.14 on Linux, macOS, and Windows, and holds an OpenSSF
Best Practices passing badge [@openssf]. It is published on the Python Package
Index as `pyobfus`, with the companion MCP server published as `pyobfus-mcp`.

# Comparison with existing tools

Compilers (Nuitka, Cython) and the runtime-based protector PyArmor trade
pure-source output and source-level debuggability for binary or runtime
protection. `pyobfus` keeps plain, debuggable Python and adds agent-facing
interfaces.

| Capability | pyobfus | PyArmor | Nuitka | Cython |
| :------------------------------------------------ | :-----: | :-----: | :-----: | :-----: |
| Pure-Python output (no native runtime or binary) | Yes | No | No | No |
| Reverse traceback mapping for debugging | Yes | No | No | No |
| Agent interface (JSON CLI + MCP server) | Yes | No | No | No |
| Cross-platform source distribution | Yes | Partial | No | No |

# Ethics statement

Code obfuscation is dual-use: the same transformations that protect legitimate
intellectual property can also conceal malicious code. `pyobfus` is built for
authors who own the code they protect. It keeps a transparent, open-source core
so that its behavior can be audited, preserves debuggability rather than
defeating it, and deliberately omits anti-analysis features such as
anti-debugging and sandbox evasion that primarily serve evasion rather than
protection. Users remain responsible for applying it only to code they are
authorized to distribute.

# Acknowledgements

`pyobfus` builds on the Python standard library and the `cryptography` package.
We thank the open-source maintainers of those projects and the early users whose
production deployments shaped the reverse-mapping workflow.

# References
