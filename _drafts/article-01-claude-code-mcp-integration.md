---
title: "Let Claude Code Obfuscate Your Python Project Automatically: A Guide to the pyobfus MCP Integration"
title_zh: "让 Claude Code 自动混淆你的 Python 项目：pyobfus MCP 集成指南"
status: DRAFT
author: Rong Zhu
date: 2026-04-22
targets:
  - dev.to (EN)
  - 有心工坊 / tech-empowerment (ZH)
  - 知乎 (ZH, adapted)
  - Medium (EN, secondary)
tags: [python, mcp, claude-code, cursor, obfuscation, ai-agents, pyobfus, pyarmor]
---

# Outline

## 0. Hook (150 words)
Open with a concrete scene: developer finishes a FastAPI SaaS backend in Claude Code, ships it, two weeks later gets a customer crash report full of `'I0' object has no attribute 'I2'`. PyArmor's C-layer path is one-way — you can't decode the trace with your AI assistant without reversing the obfuscation itself. Hook: *what if the obfuscator was designed for an AI-assisted workflow from the start?*

## 1. The problem: obfuscation tools were built before AI agents (200 words)
- PyArmor and friends predate Claude Code / Cursor / Windsurf.
- They assume a human-in-the-loop Debug cycle: you are the one reading the trace.
- In the AI-agent era, the trace goes to an LLM. Obfuscated names break that path.
- Other pain points: framework awareness (FastAPI / Pydantic reflection), zero-config onboarding, CI pipelines that repeat work.

## 2. pyobfus v0.4.0: four AI-native moves (250 words)
- `--check` — pre-flight risk scan, JSON output, `ai_hint` field telling the AI what to do next
- `--init` — scans project, detects framework (FastAPI/Django/Pydantic/Click/SQLAlchemy), writes `pyobfus.yaml`
- `--save-mapping` + `--unmap` — the killer feature: reverse obfuscated tracebacks without reversing the obfuscation
- `pyobfus-mcp` — MCP server so Claude Desktop / Code / Cursor / Windsurf / Zed can invoke these tools autonomously from a chat turn

Small diagrams / code blocks for each.

## 3. The MCP integration in 60 seconds (200 words)
- `pip install pyobfus-mcp`
- Add 3 lines to `claude_desktop_config.json` / `~/.cursor/mcp.json`
- Restart, talk to Claude: *"Scan this FastAPI project for obfuscation risks"*
- Show a real transcript (or mock) of the agent autonomously calling `check_obfuscation_risks` → `generate_pyobfus_config` → obfuscate with `--save-mapping`

## 4. Walkthrough: from "I want to ship this" to "my AI can still debug prod" (400 words)
Concrete end-to-end story with a sample FastAPI-style app. Six steps, each a single command:
1. `pyobfus --check src/ --json` — risk report
2. `pyobfus --init src/ --json` — generates `pyobfus.yaml` with `fastapi` preset
3. `pyobfus src/ -o dist/ -c pyobfus.yaml --save-mapping mapping.json` — obfuscate
4. Ship `dist/`; keep `mapping.json` in a secure location
5. Production crash comes in → `pyobfus --unmap --trace error.log --mapping mapping.json`
6. Paste the unmapped trace into Claude Code → AI helps debug as if the code wasn't obfuscated

Emphasize: mapping.json never leaves your secure environment. The obfuscated binary is still obfuscated to anyone else.

## 5. Why this matters for the AI-assisted programming era (200 words)
- Obfuscation's historical job: raise reverse-engineering cost for humans.
- New job: same *plus* stay compatible with AI-assisted development.
- The two goals aren't in conflict — if the tool is designed right.
- pyobfus's design principle: "selective opacity" — choose what the AI sees, not all-or-nothing.
- Contrast with PyArmor's bytecode-encryption path: fundamentally incompatible with symbol-level debugging.

## 6. Try it / links (100 words)
- `pip install pyobfus pyobfus-mcp`
- GitHub: https://github.com/zhurong2020/pyobfus
- Docs: https://pyobfus.readthedocs.io/
- MCP integration guide: https://github.com/zhurong2020/pyobfus/tree/main/pyobfus_mcp
- AI integration templates (CLAUDE.md, .cursorrules, AGENTS.md): https://github.com/zhurong2020/pyobfus/tree/main/templates/ai-integration

---

# English opening — full draft (~500 words, ready to copy into dev.to / Medium)

**Title**: *Let Claude Code Obfuscate Your Python Project Automatically: A Guide to the pyobfus MCP Integration*

**Subtitle**: *The Python obfuscator built for the AI-assisted development era.*

---

Last Wednesday, I watched a developer ship a FastAPI SaaS backend to production from Claude Code. Ten days later, his customer sent a crash log full of identifiers like `'I0' object has no attribute 'I2'`. He pasted it into Claude, waited, and got back: "I don't know what `I0` or `I2` refer to in your codebase. Could you share the original source?"

That was the moment. The obfuscation he'd applied — the same technique PyArmor and half a dozen other tools have shipped for a decade — had silently broken his AI-assisted debugging loop. The irony: the very system he'd used to *build* the code could no longer help him *debug* it.

This post is about a different approach. [**pyobfus 0.4.0**](https://pypi.org/project/pyobfus/) and its companion [**pyobfus-mcp**](https://pypi.org/project/pyobfus-mcp/) server are designed from the ground up for the AI-assisted development era — where your obfuscator doesn't just raise reverse-engineering cost for attackers, but also stays compatible with the way you (and your AI coding assistant) actually work.

## What's broken in the pre-AI playbook

Most Python obfuscators were designed 3–10 years ago for a human-in-the-loop workflow. You obfuscate, you ship, and when a crash arrives you read the log yourself. If the log has garbage identifiers — that's the *point*. Protection cost is friction for attackers; friction for you is the unavoidable tax.

That logic doesn't survive contact with Claude Code, Cursor, Windsurf, or any other AI coding agent. Now:

- **Your debugger is an LLM.** It reads the trace alongside your source. If the trace has been renamed but the source still uses original names, the LLM can't connect them.
- **Your IDE is a tool-calling agent.** It wants to call `check_risks`, `generate_config`, `obfuscate` as structured functions — not shell commands you script into it.
- **Your CI is your first customer.** Every skipped rebuild is compute saved; every broken obfuscation pipeline is a 3am page.

None of the established Python obfuscators were built for that world.

## Enter pyobfus 0.4.0 — four AI-native moves

1. **`pyobfus --check`** — pre-flight risk scan. Walks your AST looking for `eval` / `exec` / dynamic `getattr` / framework reflection. Output is JSON with an `ai_hint` field telling your AI assistant exactly what to run next.
2. **`pyobfus --init`** — zero-config onboarding. Detects FastAPI / Django / Pydantic / Click / SQLAlchemy and writes a ready-to-use `pyobfus.yaml` with the matching preset.
3. **`pyobfus --unmap`** — the killer feature. Takes a production stack trace plus a `mapping.json` file, returns the original identifier names. Your AI assistant reads the trace as if the code weren't obfuscated — *while the deployed code stays obfuscated to everyone else.*
4. **`pyobfus-mcp`** — a Model Context Protocol server. Five tools, zero shell scripting. Install once, use across Claude Desktop, Claude Code, Cursor, Windsurf, and Zed.

Let me show you the 60-second setup, then walk through a real end-to-end debugging session…

---

# TODO before publish

- [ ] Add a screen recording / animated GIF of Claude Desktop calling the `check_obfuscation_risks` tool autonomously
- [ ] Produce Chinese translation with 有心工坊 voice (less "I" narrative, more "我们 / 笔者")
- [ ] Add a "PyArmor comparison table" sidebar
- [ ] Request review from @zhurong2020 before publishing
- [ ] Cross-post URLs once published to docs/AI_INTEGRATION_STRATEGY.md success-metrics section
