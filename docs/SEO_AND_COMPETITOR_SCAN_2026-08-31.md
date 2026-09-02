# Competitor scan + long-tail keyword / AI-search plan — 2026-08-31

Status: Waves A/B completed 2026-09-01. Wave C shipped the same day as the
standalone SEO releases `pyobfus 0.5.20` and `pyobfus-mcp 0.3.10`; runtime and
MCP tool schemas are unchanged. PyPI and GitHub Releases are verified.
2026-09-02: MCP Registry 0.3.10 was published after the endpoint recovered and
publicly verified `active` / `isLatest=true`; docs CI run `33521916080` also
completed successfully. The SEO implementation and release closeout are complete.
Trigger: user request (competitor recheck + SEO/GEO keyword planning), post
0.5.19 release. Previous competitor scan: 2026-08-22 (`docs/CURRENT_PLAN_ZH.md`
"2026-08-22 扫描" section).

---

## 1. Competitor scan (2026-08-31)

### 1.1 Established competitors — no material change since 2026-08-22

| Tool | State | Delta vs last scan | Threat |
|---|---|---|---|
| **PyArmor** | 9.2.6 (PyPI, 2026-07-23). Still the v9 line (RFT/BCC/VMC/ECC modes, "PyArmor CI" license, readonly obfuscated module). | Incremental only; no new architecture since v9 (Oct 2024). VMC/ECC function-body virtualization already captured in `COMPARISON.md`. The earlier 9.2.7 statement was corrected on 2026-09-02 against official PyPI metadata. | Unchanged. Still the "maximum protection" incumbent; still no AI-debuggability, no MCP, no VS Code extension. |
| **Nuitka Commercial** | Traceback encryption still **symmetric-only** ("asymmetric planned"); data-hiding plugin encrypts constants. Core stays Apache-2.0. | No change — matches the P2-23 finding already in `COMPARISON.md` (pyobfus's RSA+AES hybrid `--scrub-traceback` is stronger on this one axis). | Unchanged. Different category (compile-to-C). |
| **Cython** | No obfuscation-relevant change. | — | Unchanged. |
| **Oxyry** (online) | Still online-only name mangling. | — | Unchanged. |
| **PyLocket** | Per-function bytecode encryption + device-bound keys + licensing/checkout platform. | Already in `COMPARISON.md` + "明确不做" (different product class). | Unchanged. |

### 1.2 New / newly-surfaced entrants

| Tool | What it is | Overlap with pyobfus | Threat | Action |
|---|---|---|---|---|
| **`python-obfuscator`** (PyPI, `github.com/davidteather/python-obfuscator`) | MIT, v0.1.0 (2026-04-03, single release). AST-based, 4 toggleable techniques: `variable_renamer`, `string_hex_encoder`, `dead_code_injector`, `exec_wrapper`. Self-described "I got tired of writing good code so I made good code to make bad code." | Same "AST-based, individually-togglable techniques" framing. **Squats the exact generic name** `python-obfuscator` (a keyword pyobfus already targets). | **Low.** No reverse mapping, no cross-file consistency, no framework presets, no config, no JSON CLI, no MCP. Documents its own limits (class methods not unrenamed, kwargs untouched, no scope-aware renaming, 72–207% runtime overhead). Author has a following (TikTokApi) so it may collect stars. | Add one honest row to `COMPARISON.md`. Note the name collision in the keyword plan. |
| **CodeEnigma** (`github.com/KrishnanSG/codeenigma`) | MIT, ~58★/17 forks, active (44 commits). Pipeline: compile→zlib→base64→AES-256-GCM→Cython-wrapped runtime loader. CLI (Typer), expiry enforcement, output dir, verbose. | **Closest positioning competitor**: "inspired by PyArmor but a different approach", "transparency and openness over black-box", "distrust of tools accessing production code" — nearly identical pitch to pyobfus. | **Low–moderate on positioning, low on capability.** Encrypted-bytecode-loader approach (not AST source-to-source), so a different technical class. No reverse mapping, no AI/MCP, no framework presets, no JSON CLI, no documented RE-resistance testing, runtime crypto dependency. | Add a `COMPARISON.md` row. Sharpen pyobfus's differentiators in copy: **AST source-to-source (pure `.py` out, no loader)** + **reverse stack-trace mapping** + **AI-native / MCP**. |
| **SOURCEdefender** | Encrypted `.pye` files, import-hook runtime. Referenced in pyobfus's compatibility cookbook but **not** in `COMPARISON.md`. | Encryption-at-rest + import hook (compose target, not head-to-head). | Low. | Add a brief `COMPARISON.md` row (compose-not-compete framing, like the cookbook). |
| **Online obfuscators** — `pyobfuscate.com`, `pyobfuscator.com`, "AST Obfuscator Pro" | Browser-based, free/freemium. `pyobfuscate.com` is running **content SEO** on the comparison keyword: `/compare` ("PyArmor, Nuitka, Cython 2026"), `/blog/python-marshal-explained`, `/python-obfuscator`. | Not a CLI/CI/MCP competitor, but they **own the "python obfuscator online" and "python obfuscator comparison" SERP** with dedicated pages. | Low as a tool; **real as an SEO competitor** for the comparison / "online" long-tail. | Counter with pyobfus's own honest comparison content (§2) — do not try to rank for "online" (pyobfus is deliberately local-only; make that a selling point). |
| **Slopsquatting / hallucinated-dependency detectors** (Aikido SafeChain, Snyk add-on, open-source install-boundary CLIs, "curated hallucinated-package dataset" scanners, arXiv 2606.13918 Bayesian detector) | Dedicated tools for the exact problem pyobfus's `dependency_advisory` addresses. Real Jan-2026 incident (`react-codeshift`, 237 repos). | Direct overlap with the `dependency_advisory` **graduation-criteria** question (`docs/CURRENT_PLAN_ZH.md` "下次工作建议" #8). | N/A to obfuscation positioning. | Feeds the keep-inside-pyobfus vs split decision: the standalone space is now **crowded and maturing**, which argues *against* splitting into yet another standalone scanner unless a clear differentiator emerges. Record in #8 tracking. |

### 1.3 Ecosystem / policy notes

- **VS Code Marketplace**: pyobfus is still the only legitimate Python-obfuscation-focused extension. The 2025-04 "Python Obfuscator for VSCode" XMRig-miner extension (publisher blocked) is gone; further malicious-extension news through mid-2026 keeps the *category* reputation-tainted → the extension listing's explicit trust signals (OpenSSF, PEP 740, provenance, SHA-pinned CI, CodeQL-clean) remain the right play, not a nice-to-have.
- **MCP discovery mechanics (2026)**: the MCP Registry now does **semantic search** — agents query natural-language *intents* and the registry ranks tools by relevance from their **registered descriptions**. So `server.json` `description` and each tool's description string are the actual ranking surface for agent discovery. This makes intent-phrased long-tail text in those fields a direct discoverability lever (see §2).
- **No MCP server does code obfuscation/protection** other than `pyobfus-mcp`. The SlowMist "MCP-Security-Checklist" explicitly lists *code obfuscation* as a hardening requirement for MCP tools — a latent positioning hook ("the tool that satisfies the checklist's obfuscation item").
- **`llms.txt` for AI search (2026 consensus)**: curation over completeness; factually dense; named-number facts; keep within length so decision-tree / FAQ sections are not truncated; FAQ-shaped content has (contested but repeatedly observed) higher citation rates in AI answers. Google's own May-2026 generative-search guidance says structured data is *not required* for AI Overviews — so the value is genuine Q&A **content**, not JSON-LD markup.

### 1.4 `docs/COMPARISON.md` gaps to close

Add short, honest entries for: **CodeEnigma**, **`python-obfuscator` (davidteather)**, **SOURCEdefender**, and a one-liner acknowledging the **online obfuscators** (with pyobfus's "code never leaves your machine" as the counter). Keep each to a row in the Quick Summary table plus ≤1 short paragraph. Do **not** inflate threat level or use exploit-shaped language.

---

## 2. Long-tail keyword / AI-search optimization plan

### 2.1 Principle

Every addition must be a phrase a real developer or agent would actually type,
placed in prose or a bounded keyword list — **not repeated across fields**.
PyPI and search engines penalize stuffing; over-long `llms.txt` gets truncated.
The `[cyber]` safeguard: describing pyobfus's own reverse-mapping / deobfuscation
function is fine; avoid any framing that reads as attacker how-to.

### 2.2 Real developer intents found in the wild (2026-08-31 search)

Grouped, for mapping onto surfaces below:

- **Pre-ship intent**: "obfuscate python before selling / before shipping / before publishing to PyPI", "ship code to customers without shipping readable source", "satisfy a customer requirement that source not be trivially readable", "protect an on-device Python agent / SDK".
- **Debuggability intent** (pyobfus's wedge): "debug obfuscated python stack trace", "deobfuscate a production crash", "keep production traces debuggable after obfuscation", "obfuscate but still let Claude / Cursor / Copilot read the traceback".
- **Comparison intent**: "PyArmor alternative", "open-source PyArmor alternative", "python obfuscator vs pyarmor / vs nuitka / vs cython", "pyarmor free trial limit", "transparent / auditable python obfuscator".
- **Realism intent**: "does obfuscation actually protect python", "obfuscation is a deterrent not encryption", "obfuscation hides how code works not who runs it" (→ licensing).
- **Framework intent**: "obfuscate a FastAPI / Django / Flask app without breaking it".
- **Packaging intent**: "obfuscate python for PyInstaller", "protect a python .exe build".
- **Agent-native intent**: "MCP server for code obfuscation", "obfuscate python from Claude Code / Cursor", "protect python project from an AI agent".
- **Supply-chain intent**: "check requirements.txt for hallucinated / nonexistent packages", "slopsquatting check before pip install".

### 2.3 Surfaces and proposed additions

| # | Surface | Feeds | Current gap | Proposed long-tail additions | Release-gated? |
|---|---|---|---|---|---|
| S1 | **GitHub repo description** (repo settings — maintainer sets) | GitHub search, Google, AI crawlers | "🛡️ Modern Python code obfuscator - Enterprise-grade protection at 50% lower cost than PyArmor" — "Enterprise-grade" contradicts the single-$45 / "低中端 PyArmor 替代" positioning; "50% lower cost" needs a live $89 anchor to hold | Rewrite, e.g.: *"AST-based Python obfuscator with reverse stack-trace mapping — obfuscate before shipping and still let your AI assistant debug production tracebacks. Transparent PyArmor alternative. MCP server + VS Code extension."* | No (maintainer action) |
| S2 | **GitHub `homepageUrl`** (empty) | GitHub sidebar, crawlers | not set | set to `https://pyobfus.readthedocs.io` | No |
| S3 | **GitHub topics** (13 / 20 used) | GitHub topic pages, search | no topic for the headline differentiator | add: `reverse-mapping`, `stack-trace-deobfuscation`, `debuggable-obfuscation`, `github-copilot`, `codebuddy`, `provenance`, `apache-2-0` (drop/replace any weak ones to stay ≤20) | No |
| S4 | **`docs/.well-known/ai-catalog.json` `representativeQueries`** (4 now) | ARD / AI-catalog crawlers | only 4, generic | expand to ~10, intent-phrased: "obfuscate my Python package before publishing to PyPI", "protect a FastAPI backend from reverse engineering", "make this Django app hard to read but keep it debuggable", "reverse-map an obfuscated stack trace from production", "obfuscate Python for a client who wants unreadable source", "check if requirements.txt lists any nonexistent packages", "is there an MCP server that obfuscates Python", "obfuscate before shipping a PyInstaller build" | No (docs-only) |
| S5 | **`server.json` `description`** (99-char cap; MCP Registry semantic search) | **Agent tool discovery** | current is feature-list-shaped, not intent-shaped | try an intent phrasing within the cap, e.g.: *"Obfuscate Python before shipping and still debug obfuscated production tracebacks from your AI agent. No phone-home."* (count chars) | Ships on next `pyobfus-mcp` release |
| S6 | **`pyproject.toml` keywords — core** | PyPI search | no reverse-mapping cluster; missing some clients + supply-chain terms | add: `reverse-mapping`, `unmap`, `deobfuscation`, `stack-trace`, `debuggable`, `github-copilot`, `codebuddy`, `windsurf`, `provenance`, `cyclonedx`, `sbom`, `dependency-hallucination`, `slopsquatting`, `obfuscate-before-shipping` (trim the weakest existing ones if the list gets unwieldy) | Next `pyobfus` release |
| S7 | **`pyproject.toml` keywords — mcp** | PyPI search | thin (15) | add: `code-protection`, `obfuscation`, `security`, `reverse-mapping`, `github-copilot`, `codebuddy`, `ai-native` | Next `pyobfus-mcp` release |
| S8 | **`llms.txt` / `llms-full.txt` / `docs/llms.txt`** | AI crawlers, `llms_txt2ctx`, Cursor bundling | has "When to use / NOT", but **no FAQ block** and no one-line "compared to" list | add a tight **`## FAQ`** (5–6 Q&A, ≤2 lines each, drawn from §2.2 intents) + a `## Compared to` one-liner list (PyArmor / Nuitka / CodeEnigma / online tools). Keep total file well within limits (curation). **Twins must stay byte-identical** (just reconciled 2026-08-31). | No (docs-only) — but do NOT put the release "What's new" churn here |
| S9 | **`README.md` FAQ + intro** | GitHub, PyPI long desc, Google, AI | 13 Q&A already; a few high-intent phrasings absent | add ≤3 FAQ entries: *"How do I obfuscate Python before selling it?"*, *"How do I debug an obfuscated crash with an AI assistant?"*, *"Is there an MCP server for Python obfuscation?"*; make sure the first two paragraphs contain the exact strings "obfuscate before shipping" and "debug obfuscated stack traces" | Land in a **release commit** (README → PyPI snapshot rule) |
| S10 | **`mkdocs.yml` `site_description`** | RTD `<meta description>`, Google, AI | "Modern Python Code Obfuscator" (5 words) | expand to ~150 chars with intent phrasing (mirrors the new repo description) | No (docs-only) |
| S11 | **`docs/index.md` intro paragraph** | RTD home, Google, AI | generic ("name mangling, string encoding, and code protection features") | rewrite the one intro paragraph to lead with the reverse-mapping wedge + "obfuscate before shipping" + "PyArmor alternative" | No (docs-only) |
| S12 | **`docs/COMPARISON.md`** | "python obfuscator comparison / vs X" SERP | missing CodeEnigma, `python-obfuscator`, SOURCEdefender, online tools (§1.4) | add the 3 rows + 1 online-tools one-liner; naturally carries comparison long-tail | No (docs-only) |
| S13 | **`CITATION.cff` keywords** (7 generic) | Zenodo, Scholar | generic | add: `reverse-engineering`, `stack-trace-mapping`, `model-context-protocol`, `AI-assisted-debugging` (do **not** touch `version` / `date-released` — Zenodo-archive-pinned) | No (docs-only) |
| S14 | **Pinned GitHub Discussion "FAQ"** | Google, AI, GitHub search | none | optional: one pinned Q&A discussion seeded from §2.2 — real questions, real answers | No (maintainer action) |
| S15 | **FAQPage JSON-LD on `docs/index.md`** | AEO/GEO (contested lift) | none | optional / low priority — Google says not required for AI Overviews; do only after S8/S9 content exists so the markup mirrors real content | No (docs-only) |

Surfaces deliberately **not** touched: `templates/ai-integration/*` (kept minimal
by design), `_drafts/*` (0.4.0 marketing), archived docs, `CITATION.cff`
version/date, README "What's new" banner (release-mechanics only).

### 2.4 Prioritized execution order

**Wave A — maintainer / non-package, minutes, no release (highest ROI):**
S1 repo description · S2 homepageUrl · S3 topics · S14 pinned FAQ discussion (optional).

**Completed 2026-09-01:** description rewritten around AST output, reverse
mapping, pre-shipping protection and AI-debuggable tracebacks; homepage set to
Read the Docs; topics expanded from 13 to 19 with the planned discovery terms,
while removing the misleading `python-obfuscator-online` topic. S14 remains
optional and was deliberately not created without a real discussion trigger.

**Wave B — docs-only, no release gate, one `docs:` commit each or grouped:**
S4 ai-catalog queries · S8 llms.txt FAQ + "compared to" (twins byte-identical) ·
S10 mkdocs site_description · S11 index.md intro · S12 COMPARISON.md new rows ·
S13 CITATION keywords. **Completed 2026-09-01** as one docs batch; `llms.txt`
twins remain byte-identical, the catalog parses as JSON, `CITATION.cff` parses
with its archive-pinned version/date unchanged, and `mkdocs build --strict`
completes with only the repository's pre-existing link/nav warnings. S15 remains
optional and was not added because real FAQ content is the higher-value surface.

**Wave C — bundle into the next natural release (PyPI needs a version to pick up):**
S5 server.json description (mcp release) · S6 core keywords (pyobfus release) ·
S7 mcp keywords (mcp release) · S9 README FAQ + intro (must be in the release
commit per the banner-before-tag rule).

**Completed 2026-09-01:** the maintainer explicitly approved a standalone SEO
release. Core 0.5.20 now carries 45 unique keywords and the revised README;
MCP 0.3.10 carries 23 unique keywords and the 91-character intent-oriented
Registry description. Both packages passed local suites, wheel/sdist builds,
`twine check`, fresh-wheel installation, OIDC publishing, and both PEP 740
provenance checks. The PyArmor Pro anchor was rechecked at $89 against its
official cart before the dated comparison link was added.

### 2.5 Guardrails / verification

- After any `llms.txt` edit: `cmp llms.txt docs/llms.txt` must stay silent; re-run
  `mkdocs build`; keep the file length modest (curation).
- No phrase repeated across >2 surfaces; every keyword must map to a §2.2 intent.
- `docs/COMPARISON.md` additions: honest, brief, no exploit-shaped wording, no
  threat-level inflation.
- Wave C README/keyword changes land **before** the tag in the release commit.
- Re-verify the S1 "50% lower cost" claim against PyArmor's current Pro price
  before reusing that number anywhere (COMPARISON.md still says $89).

---

## 3. Open decisions for the maintainer

1. S1 wording: **resolved — recommended wording applied 2026-09-01.**
2. Wave B: **resolved — completed as a docs batch on 2026-09-01.**
3. Wave C: **resolved — standalone SEO release explicitly approved and shipped
   as Core 0.5.20 / MCP 0.3.10 on 2026-09-01.**
4. `dependency_advisory` graduation (#8): the standalone slopsquatting-detector
   space is now crowded/maturing (§1.2) — lean toward **keeping it inside
   `--check`** unless a clear differentiator appears. Confirm.
