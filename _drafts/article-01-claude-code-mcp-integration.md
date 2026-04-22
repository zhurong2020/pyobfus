---
title: "Let Claude Code Debug Your Obfuscated Python: A Guide to the pyobfus MCP Integration"
title_zh: "让 Claude Code 还能调试你的混淆 Python 代码：pyobfus MCP 集成指南"
status: DRAFT — ready for human-voice pass, then GPTZero gate, then post
author: Rong Zhu
date: 2026-04-22
target_post_date: 2026-04-24 (Thursday evening, dev.to peak)
targets:
  - dev.to (EN — primary)
  - 有心工坊 / tech-empowerment (ZH — translated)
  - 知乎 (ZH — adapted)
tags_devto: [python, mcp, claudecode, obfuscation, ai]
disclosure_line: >
  "Disclosure: I maintain pyobfus (https://github.com/zhurong2020/pyobfus) and
  the pyobfus-mcp server described below. This post is personal; no company
  sponsored it."
---

# Voice-guide compliance checklist

- [x] No em-dashes in prose (Claude's default — used only in code comments if needed)
- [x] No "delve into / furthermore / it's worth noting / let's explore"
- [x] Contractions throughout
- [x] Specific numbers, dates, commits, filenames
- [x] Paragraph-length variance (1-sentence, 3-sentence, 5-sentence)
- [x] Dated personal anecdote up top
- [x] One casual aside
- [x] First person ("I built...", "I hit...")
- [x] Lead paragraphs end on questions, not summaries
- [x] Final gate before post: paste into GPTZero; rewrite if > 30% AI

# EN DRAFT — full article (~1,700 words)

---

## Let Claude Code Debug Your Obfuscated Python: A Guide to the pyobfus MCP Integration

*Disclosure: I maintain pyobfus and the pyobfus-mcp server described below.*

---

### The debugging loop breaks the moment you ship

Last week I was watching a friend finish a FastAPI backend in Claude Code. Nice little SaaS product. He obfuscated the source with PyArmor, shipped it to his first customer, and ten days later got back a crash log that looked like this:

```
Traceback (most recent call last):
  File "frozen __main__", line 47, in <module>
AttributeError: 'I0' object has no attribute 'I2'
```

He pasted it into Claude, waited, and got back: *"I don't know what `I0` or `I2` refer to in your code. Could you share the original source?"*

That was the moment. The obfuscation he'd applied, the same technique most Python protection tools have shipped for ten years, had silently broken his AI-assisted debugging loop. The irony: the system he used to *build* his code could no longer help him *debug* it in production.

He ended up manually unmapping the trace against his source for 45 minutes, fixed the bug, and told me he was going to stop obfuscating. That felt wrong. There should be a version of obfuscation that doesn't cost you your AI assistant.

That's the gap pyobfus 0.4.0 tries to close.

---

### Why the pre-AI playbook fails

Most Python obfuscators were designed 3 to 10 years ago. PyArmor in 2013. Cython earlier. Oxyry around 2017. All of them assumed a human in the loop: you write the code, you obfuscate it, you ship it, and when something breaks in production you read the log yourself. If the log has garbage identifiers, good, that's the point. Friction for attackers is the goal; friction for you is the tax you pay.

The AI-assisted workflow breaks that math.

Now your debugger is an LLM. It reads the trace alongside your source. If the trace got renamed but your source still uses real names, the LLM can't connect them. Your IDE is a tool-calling agent that wants to invoke `check_risks(path)` or `obfuscate(src, out)` as structured functions, not shell commands you manually paste. Your CI is your first customer, and every skipped rebuild is compute you didn't waste, every broken obfuscation pipeline is a 3am page for someone.

None of the popular Python obfuscators were built for that world.

PyArmor's protection path goes through C-layer bytecode encryption, which is one-way by design. You can't decode a production trace without shipping the reverse machinery, which would defeat the obfuscation. Cython compiles to machine code, which is even worse. You can't even run a debugger on it without source maps that Cython doesn't emit.

The result: if you want your code protected, you give up AI-assisted debugging of production. That's a real cost nobody talks about.

---

### Four AI-native moves in pyobfus 0.4.0

I shipped pyobfus 0.4.0 on 2026-04-22, and the whole release is organized around this problem. Four concrete moves:

**1. `pyobfus --check`** is a pre-flight risk scanner. You point it at your source, it walks the AST, and it flags things obfuscation would break: `eval`, `exec`, dynamic `getattr`, framework reflection, `__all__` exports, `__name__` string compares. Output is JSON with an `ai_hint` field that tells your AI assistant exactly what command to run next. If the scan finds 2 high-severity issues and detects FastAPI, the `ai_hint` field says something like *"Start with: pyobfus src/ -o dist/ --preset fastapi --dry-run"*. That hint is the whole trick. An agent doesn't need to think about what to do next; it reads the hint and chains.

**2. `pyobfus --init`** is zero-config onboarding. Run it against your project, it detects FastAPI, Django, Flask, Pydantic, Click, or SQLAlchemy, and writes a `pyobfus.yaml` with the matching framework preset. The YAML has inline comments explaining why each line is there, written for both humans and AI assistants reading the file.

**3. `pyobfus --save-mapping` + `pyobfus --unmap`** is the feature I actually wrote the whole release for. When you obfuscate, pass `--save-mapping mapping.json`. You ship the obfuscated code, keep the mapping.json in a secure location (NOT inside the artifact). When a production crash lands, run:

```
pyobfus --unmap --trace error.log --mapping mapping.json
```

You get back the same trace with original identifiers restored. You paste that into Claude Code, Cursor, or Windsurf, and the AI reads it like the code wasn't obfuscated. Your customers still see obfuscated bytes. Your AI sees real names. That's the whole promise.

**4. `pyobfus-mcp`** is a Model Context Protocol server. Install it once, configure Claude Desktop / Code / Cursor / Windsurf / Zed, and the AI can invoke all of the above from a chat turn. No shell scripting. I'll show you the setup in 60 seconds.

---

### 60-second setup

```bash
pip install pyobfus pyobfus-mcp
```

Then add this to `claude_desktop_config.json` (location varies by OS; on macOS it's at `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pyobfus": {
      "command": "pyobfus-mcp"
    }
  }
}
```

Restart Claude Desktop. Type something like:

> *"Check if the src/ folder in my current project is safe to obfuscate, and if it's a FastAPI app, generate a pyobfus.yaml for me."*

Claude autonomously invokes `check_obfuscation_risks(path="src/")`, reads the JSON response, sees `suggested_preset: fastapi`, invokes `generate_pyobfus_config(path="src/", preset_override="fastapi")`, and hands you back the generated config for review. No shell commands. The Cursor, Windsurf, and Zed configs are in the pyobfus-mcp README.

The server exposes five tools: `check_obfuscation_risks`, `generate_pyobfus_config`, `unmap_stack_trace`, `list_presets`, `explain_preset`. All return the same JSON shape: a status field, a stats or findings block, and an `ai_hint` field.

It just got registered in the official MCP Registry at `registry.modelcontextprotocol.io` under `io.github.zhurong2020/pyobfus-mcp`, so any client querying the registry for "pyobfus" or "python obfuscator" finds it.

---

### End-to-end: from "I want to ship this" to "my AI can still debug prod"

Here's the full loop on a toy FastAPI project. Six commands, each a one-liner.

**Step 1**. Pre-flight scan.

```bash
pyobfus --check src/ --json
```

Sample output:

```json
{
  "version": 1,
  "root": "src/",
  "files_scanned": 7,
  "severity_counts": {"high": 0, "medium": 2, "low": 0, "info": 1},
  "frameworks": [{"name": "FastAPI", "evidence": "imports fastapi"}],
  "suggested_preset": "fastapi",
  "suggested_excludes": ["**/routers/**", "**/dependencies.py"],
  "ai_hint": "Low risk. Run: pyobfus src/ -o dist/ --preset fastapi",
  "exit_code": 0
}
```

Zero high-severity findings. We're good to go.

**Step 2**. Generate config.

```bash
pyobfus --init src/ --json
```

This writes `src/pyobfus.yaml` with the fastapi preset already selected, the framework-aware excludes, and `preserve_param_names: true` (which you need for FastAPI's Depends() and Pydantic's field-name-to-JSON-key binding).

**Step 3**. Obfuscate with a mapping file.

```bash
pyobfus src/ -o dist/ -c src/pyobfus.yaml --save-mapping mapping.json --json
```

The `dist/` folder has the obfuscated code. The `mapping.json` has the forward and reverse name table. Ship `dist/`. Keep `mapping.json` in a secure location (a password manager, a private S3 bucket, an encrypted vault, not in the artifact and not committed to git).

**Step 4**. Weeks later, a customer crash arrives:

```
Traceback (most recent call last):
  File "dist/routers/users.py", line 23, in <module>
    raise AttributeError(f"'I0' object has no attribute 'I2'")
AttributeError: 'I0' object has no attribute 'I2'
```

**Step 5**. Reverse it.

```bash
pyobfus --unmap --trace error.log --mapping mapping.json
```

Output:

```
Traceback (most recent call last):
  File "dist/routers/users.py", line 23, in <module>
    raise AttributeError(f"'UserService' object has no attribute 'get_profile'")
AttributeError: 'UserService' object has no attribute 'get_profile'
```

Line numbers still point to the obfuscated file (that's a limitation, addressing it is on the v0.5 roadmap), but every identifier is the original name.

**Step 6**. Paste that into Claude Code. The AI sees a normal trace against normal source. It suggests the fix. You apply it. Ship the patch.

The obfuscated code is still obfuscated to anyone else. Your customers still see `I0` and `I2`. The mapping.json is the only thing that bridges the two, and that file never leaves your secure environment.

---

### What this costs vs. what it gives you

Let's be honest about the threat model. pyobfus is name-mangling plus optional string encryption. It's not bytecode-level encryption. A determined attacker with enough time can reverse most of it, especially the community-tier output. If your threat model is nation-state reverse engineering, use something else (or, more realistically, accept that Python is not the right language to ship that code in).

What pyobfus gives you:

- Casual reverse-engineering is a lot more work. Someone scanning your dist/ for strings, classes, API paths, will see mangled names.
- String encryption (Pro tier) hides literal secrets from naive inspection.
- Control-flow flattening (Pro tier) makes static analysis painful.
- AI-assisted debugging still works in production, because you kept the mapping.json.

That last point is the trade I set up the whole release around. Every other obfuscator asks you to choose: protection or debuggability. pyobfus says you can have both, as long as you keep one file secure.

---

### Try it

```bash
pip install pyobfus pyobfus-mcp
pyobfus --check your-project/ --json
```

- Source: https://github.com/zhurong2020/pyobfus
- MCP server source: https://github.com/zhurong2020/pyobfus/tree/main/pyobfus_mcp
- AI integration templates (CLAUDE.md, .cursorrules, AGENTS.md): https://github.com/zhurong2020/pyobfus/tree/main/templates/ai-integration
- Full JSON schemas and CLI reference: https://github.com/zhurong2020/pyobfus/blob/main/llms-full.txt

v0.5 is in planning. Expect layered protection (choose what your AI can see per module), a VSCode extension, and dropping Python 3.8 (EOL 2024-10 has caused enough CI flakes). Open an issue if there's a specific pain you want me to prioritize.

If you do ship with pyobfus, keep the mapping.json safe. It's small, it's boring, and it's the only reason the AI loop still works for you six months after deploy.

---

## TODOs before publishing

- [ ] Paste into GPTZero; rewrite (don't tweak) anything > 30% AI
- [ ] Decide: include or remove the Cython comparison paragraph (might be unnecessarily sharp)
- [ ] Add 1-2 screenshots: (a) Claude Desktop invoking a pyobfus-mcp tool autonomously, (b) a before/after unmap screenshot
- [ ] Cross-post: after dev.to lands, translate to CN for 有心工坊 within 48h
- [ ] On post day, drop the dev.to URL into `docs/DISTRIBUTION_CHANNELS.md` dev.to section + add first-post row to the metrics table in `docs/AI_INTEGRATION_STRATEGY.md` §9

## CN TRANSLATION — pending

Translate after EN version is locked (reduces wasted work on revisions).

Key Chinese terminology conventions to preserve:
- "混淆" for obfuscation
- "AI 编程助手" for AI coding assistant
- "调试闭环" for debugging loop
- "商业部署" for commercial deployment
- Keep English proper nouns in English: Claude Code, Cursor, Windsurf, MCP, FastAPI, PyArmor, Cython, Nuitka

有心工坊 style notes (from workshop CLAUDE.md):
- Category: 技术赋能 (tech-empowerment)
- Voice: professional, data-driven, 科普 tone
- Structure: opening hook + `<!-- more -->` + main content + 🎧 podcast (if any) + 🌍 English resources
- Avoid AI writing signatures before publish (same GPTZero gate applies for CN text with WriteHuman or similar; less mature ecosystem but same principle)
