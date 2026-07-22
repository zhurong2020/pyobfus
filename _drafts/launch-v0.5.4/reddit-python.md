# r/Python monthly showcase entry

The 2026 r/Python rules direct project showcases to the designated showcase
thread. Do not use the old standalone-post draft without re-checking the rules.

## Suggested comment

**pyobfus 0.5.4 — AST obfuscation with reversible production traces**

Repository: <https://github.com/zhurong2020/pyobfus>

What it does: pyobfus renames Python identifiers through the AST, preserves
reflection-sensitive APIs through FastAPI/Django/Flask/Pydantic/Click/SQLAlchemy
presets, and can save a mapping that restores original names in a production
traceback. It also has JSON CLI output and an MCP server for coding agents.

Who it is for: small teams distributing commercial Python that want to make
casual source inspection harder without giving up readable crash triage. It is
not a substitute for a hardware security boundary or protection against an
attacker controlling a running process.

What is new: 0.5.4 extends Pro device binding to every Runtime String Vault key.
Each vault receives a distinct salt; the key is derived from the bound host at
runtime instead of shipping as a baked constant.

Quick start:

```bash
pip install pyobfus
pyobfus --check src/ --json
pyobfus src/ -o dist/ --save-mapping mapping.json
```

The Apache-2.0 core is fully usable on its own; optional Pro code is separately
licensed and source-separated. I maintain the project. The most useful feedback
would be a framework compatibility case, a weakness in the stated threat model,
or which integration is missing from a real packaging pipeline.
