---
title: "I built a Python obfuscator that keeps production traces debuggable"
published: false
tags: python, opensource, security, claudecode
canonical_url: https://github.com/zhurong2020/pyobfus
---

Python obfuscation usually creates a second problem: the same renamed symbols
that slow down a casual reader also make production crashes useless to the
developer and their coding assistant.

That trade-off is why I built
[pyobfus](https://github.com/zhurong2020/pyobfus), an AST-based Python
obfuscator with a reversible debugging path. The Apache-2.0 core is public, the
commercial Pro source stays separately licensed, and both are developed in the
same public repository.

The basic workflow is deliberately ordinary:

```bash
pip install pyobfus
pyobfus --check src/ --json
pyobfus src/ -o dist/ --save-mapping mapping.json
```

The distributed code contains renamed symbols. The mapping file stays with the
developer. When a crash arrives:

```bash
pyobfus --unmap --trace error.log --mapping mapping.json --json
```

The result restores the original identifiers before the trace goes back to
Claude Code, Cursor, or a human debugger. Framework presets preserve reflective
APIs for FastAPI, Django, Flask, Pydantic, Click, and SQLAlchemy. A separate
`pyobfus-mcp` package exposes the risk scan, configuration, obfuscation, and
reverse-mapping workflow as machine-readable MCP tools.

## What changed in 0.5.4

The latest release closes a concrete device-binding gap in the Pro pipeline.
Before 0.5.4, `--bind-device` protected the Selective Opacity L3 key but Runtime
String Vault keys could still be emitted as baked constants. In 0.5.4, every
vault gets its own salt and derives its key from the bound machine at runtime.
The normal syntax is:

```bash
pyobfus src/ -o dist/ --level pro --vault --bind-device
```

There is no `pyobfus build` subcommand. I am calling that out because several
older release notes used the wrong shorthand and copying it produced a path
error.

The release CI recorded 1,046 passing core tests, one skip, and 90% coverage.
Core, MCP, and end-to-end suites run separately across Python 3.9 through 3.14
on Linux, macOS, and Windows.

## The threat model is intentionally limited

The community tier raises the cost of casual source inspection; it is not a
claim of irreversible protection. Pro can encrypt selected function bodies and
vaulted strings, bind decryption to a machine, seal code objects, and scrub
tracebacks. A determined attacker controlling a running process can still use
dynamic analysis or extract material from memory. The local Pro trial is also a
convenience control, not a security boundary; that limitation is documented and
pinned by tests.

If the requirement is nation-state resistance, an encrypted VM or hardware
boundary is the more honest answer. If the requirement is distributing Python
to customers while keeping routine debugging workable, this is the niche I am
trying to serve.

## What I need feedback on

The next work should come from real use rather than another speculative feature.
The candidates are:

- an ML/model-serving preset;
- a signed build-provenance manifest;
- a PyInstaller integration cookbook;
- integrity verification for MCP tool descriptions.

I am especially interested in reproducible cases where a framework breaks,
where the mapping workflow is awkward, or where the documented threat model is
wrong. Issues and code are at
[github.com/zhurong2020/pyobfus](https://github.com/zhurong2020/pyobfus).

If you use pyobfus in research, the project has a version-independent Zenodo
DOI: [10.5281/zenodo.20846053](https://doi.org/10.5281/zenodo.20846053).

*Disclosure: I maintain pyobfus and license the optional Pro edition. Nobody
sponsored this post.*
