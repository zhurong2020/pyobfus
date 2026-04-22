# Stack Overflow Seeding Targets — pyobfus (2024-2026 vintage)

> **⛔ STRATEGY DECISION 2026-04-22: SO seeding paused for 6 months.**
>
> Traffic math doesn't work. The best 2024+ candidate (Q79400498) gets ~40 views/month.
> Even 3 top-tier answers would yield ~2 clicks/month to pyobfus.
> AI-content ban on SO is strictly enforced (confirmed via meta banner on every page
> and recent community policy reaffirmations in April 2026).
> Low-rep maintainer account (11 rep) posting self-promotion answers is the highest-scrutiny
> combination — mod removal risk outweighs marginal exposure.
>
> **Revised plan**: pause SO; redirect effort to dev.to articles, MCP Registry,
> HN Show HN, Reddit Showcase Saturday. Revisit SO Q4 2026 based on organic signal.
>
> **Keep this doc**: reactivation checklist + target list are still useful when we
> reassess. Do NOT post answers in the meantime.

---

**Status**: ⏸️ PAUSED — 7 verified targets preserved for future reactivation
**Research date**: 2026-04-22
**All URLs verified live via Stack Exchange API**

**Filter applied**: questions asked OR with last activity in 2024 or later only. Older-but-high-traffic questions (Q261638 from 2008, Q8076349 from 2011) were explicitly excluded per updated scope to avoid the "digging up ancient threads" pattern that looks agenda-driven.

Ground rules for each answer (applies after forum-voice guidelines are finalized in separate research):
1. Lead with honest framing ("obfuscation raises cost, not impossible"). SO hates marketing.
2. Acknowledge the incumbent (PyArmor / Cython / Nuitka) first.
3. Introduce pyobfus as modern alternative for AI-assisted workflows, not as a replacement.
4. Include working code snippets.
5. Disclose maintainer status per SO policy.

---

## 🎯 Ranked posting order

1. **#1 below** (Q79400498) — best fit, lowest risk, `--unmap` showcase
2. #3 (Q78855640) — zero answers, Poetry-specific
3. #4 (Q79014050) — Nuitka bundling angle
4. #2 (Q79305680) — multi-device, add as alternative to accepted answer
5. #5 (Q79201098) — SaaS distribution use case
6. #6 (Q78086982) — .pyd compile, frame as lighter path
7. #7 (Q77921888) — Apache-config, SKIP unless others blocked

---

## 1. Q79400498 — PyArmor + Nuitka traceback error 🔥 BEST FIT

- **URL**: https://stackoverflow.com/questions/79400498/runtimeerror-unauthorized-use-of-script-11107-after-obfuscating-python-scrip
- **Title**: `RuntimeError: unauthorized use of script (1:1107) after obfuscating Python script with PyArmor and compiling with Nuitka`
- **Views**: 599 · **Answers**: 1 (unaccepted, score 0) · **Q score**: 3
- **Asked**: 2025-01-30 · **Last activity**: 2025-08-27 · **Status**: Open, not protected, no bounty
- **Tags**: pyarmor, traceback, nuitka, pyinstaller
- **Why pyobfus fits**: `pyobfus --unmap` reverses obfuscated tracebacks; pyobfus has no PyArmor-style runtime license check that's throwing this error. Drop-in alternative avoiding the whole bug class.
- **Risk**: **LOW** — active, one weak competing answer, positive score, clearly framed.

## 2. Q79305680 — PyArmor multi-device config

- **URL**: https://stackoverflow.com/questions/79305680/how-to-configure-pyarmor-latest-version-to-make-obfuscated-scripts-runnable-on
- **Title**: `How to configure PyArmor (latest version) to make obfuscated scripts runnable on multiple devices`
- **Views**: 1,028 · **Answers**: 1 accepted (score 2) · **Q score**: 1
- **Asked**: 2024-12-24 · **Last activity**: 2025-02-21 · **Status**: Open
- **Tags**: python, pyarmor
- **Why pyobfus fits**: pyobfus Apache-2.0 has no per-device licensing friction; framework-aware presets ship the runtime with the artifact.
- **Risk**: **MEDIUM** — accepted answer exists, ours must add comparison-angle value, not replace.

## 3. Q78855640 — PyArmor + Poetry build broken

- **URL**: https://stackoverflow.com/questions/78855640/obfuscating-package-using-pyarmor-poetry-build-does-not-seem-to-work
- **Title**: `Obfuscating package using Pyarmor + Poetry Build does not seem to work`
- **Views**: 285 · **Answers**: 0 · **Q score**: 2
- **Asked**: 2024-08-10 · **Last activity**: 2024-08-10 · **Status**: Open
- **Tags**: python-poetry, pyarmor, deployment, package
- **Why pyobfus fits**: pyobfus JSON CLI integrates with Poetry/`pyproject.toml` build hooks without PyArmor's opaque runtime injection that breaks Poetry's wheel structure.
- **Risk**: **LOW** — zero answers, positive score, specific packaging question.

## 4. Q79014050 — Nuitka + obfuscation multi-file executable

- **URL**: https://stackoverflow.com/questions/79014050/compiling-multiple-python-files-and-json-files-into-a-single-executable-using-nu
- **Title**: `Compiling multiple python files and json files into a single executable Using Nuitka`
- **Views**: 429 · **Answers**: 0 · **Q score**: 0
- **Asked**: 2024-09-23 · **Last activity**: 2024-09-23 · **Status**: Open
- **Tags**: python, pyinstaller, exe, obfuscation, nuitka
- **Why pyobfus fits**: pyobfus pre-processes source before Nuitka/PyInstaller bundling; JSON CLI makes it CI/CD-friendly for multi-file builds.
- **Risk**: **MEDIUM** — no activity since ask date but `obfuscation` tag keeps it discoverable.

## 5. Q79201098 — Distributing Python script to client machines

- **URL**: https://stackoverflow.com/questions/79201098/what-are-the-different-ways-of-distributing-a-script-to-run-on-different-company
- **Title**: `What are the different ways of distributing a script to run on different company client machines?`
- **Views**: 78 · **Answers**: 1 (unaccepted, score 0) · **Q score**: 0
- **Asked**: 2024-11-18 · **Last activity**: 2024-11-22 · **Status**: Open
- **Tags**: python, architecture, supabase, saas, software-distribution
- **Why pyobfus fits**: SaaS-to-client distribution = protect IP on untrusted machines. Apache-2.0 + $45 Pro undercuts PyArmor.
- **Risk**: **MEDIUM** — broad/opinion-leaning; must narrow to the obfuscation slice.

## 6. Q78086982 — Compiling Python to .pyd

- **URL**: https://stackoverflow.com/questions/78086982/how-can-i-compile-python-projects-into-pyd-files
- **Title**: `How can I compile Python projects into .pyd files?`
- **Views**: 799 · **Answers**: 1 (unaccepted, score 0) · **Q score**: 0
- **Asked**: 2024-03-01 · **Last activity**: 2024-03-02 · **Status**: Open
- **Tags**: python, compilation, pyqt, pyqt5, cython
- **Why pyobfus fits**: User wants source protection via compilation; pyobfus offers faster iteration than Cython and `--unmap` traceback recovery Cython can't match.
- **Risk**: **MEDIUM** — answer must address .pyd specifically; frame as "if your goal is source protection, here's a lighter path".

## 7. Q77921888 — Python executable via Apache but unreadable

- **URL**: https://stackoverflow.com/questions/77921888/allow-python-script-to-be-executed-by-apache-but-not-read-in-a-browser
- **Views**: 79 · **Answers**: 1 accepted (score 2)
- **Asked**: 2024-02-01 · **Last activity**: 2024-08-11
- **Risk**: **HIGH** — accepted answer solved the real problem (Apache config). Our answer risks off-topic. Skip unless others blocked.

---

## Previously listed (now demoted — archived for reference)

The earlier list targeted high-view classics: Q261638 (509K views, 2008) and Q8076349 (2011). These are excluded from the current plan per scope update — "digging up ancient threads" tends to look agenda-driven and SO's late-answer policy requires genuinely new info. If we reconsider later, Q261638 (still canonical, 2025-03 activity) is the only one worth revisiting.

---

## Next step

**Blocked on**: AI-policy + voice research (agent running in background). Once that returns, we'll:

1. Apply human-voice rewrite rules to the first answer draft (Q79400498)
2. The user reviews, edits in his own voice, submits manually
3. Observe reception; if positive, move on to Q78855640
