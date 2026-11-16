# pyobfus vs PyLocket

PyLocket documents encryption of function, method, class-body and module code
blocks, together with licensing, delivery, checkout and updates. It covers the
whole job of selling and delivering a Python desktop application
([official site](https://pylocket.com/), **checked 2026-11-15**).

> **Partial refresh — checked 2026-11-15.** New version, protection scope,
> platform, packaging and pricing facts below use official pages and PyPI
> metadata from the [2026-11-15 research record](../COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md).
> They are vendor descriptions, not new hands-on protection or compatibility
> tests. Other claims and the retained assessments below keep the
> **2026-10-02** comparison baseline and were not rechecked in this refresh.

[PyPI](https://pypi.org/project/pylocket/) lists **1.1.21**, released
**2026-11-02**, requiring **Python 3.12+**; the public wheel/sdist have no PyPI
provenance (**checked 2026-11-15**).

PyLocket is a newer, developer-first platform (launched after this document's
other comparisons were written) that positions itself against SOURCEdefender
as "a full platform" rather than an encryption utility.

| Feature | pyobfus | PyLocket |
|---------|---------|----------|
| **Commercial model** | **$45** (one-time Pro) | Account subscription + **$4 per production licence**; free tier for testing ([official pricing](https://pylocket.com/pricing.html), checked 2026-11-15) |
| **Python versions** | **3.9–3.15** ([support matrix](../SUPPORT_MATRIX.md#python-versions-and-operating-systems)) | **3.12+** ([PyPI](https://pypi.org/project/pylocket/), checked 2026-11-15) |
| **Protection unit** | AST transformation on whole modules | Function/method/class-body/module code-block encryption ([official site](https://pylocket.com/), checked 2026-11-15) |
| **Key management** | Local Pro license / Runtime String Vault | Device-bound keys issued at activation, never embedded in the shipped app |
| **Anti-debug / anti-VM** | Anti-debugging (Pro) | Anti-debug + anti-VM + dynamic API resolution + memory protection |
| **Open source** | Yes (Core: Apache 2.0) | No |
| **Built-in commerce** (licensing, delivery, checkout, trials) | No — bring your own | Yes, this is the product's headline differentiator |
| **Debugging / traceback workflow** | Reverse stack-trace mapping (`--unmap`), purpose-built for AI-assisted debugging | Not mentioned anywhere in PyLocket's own docs or marketing |
| **AI-assisted development workflow** | Explicit design goal | Not mentioned |

**Delivery and runtime — checked 2026-11-15.** The
[official site](https://pylocket.com/) describes device activation followed by
key delivery, a native hardened runtime, licence revoke/reset, one-time
downloads, hosted checkout, automatic updates, webhooks and signed-artifact
replacement/distribution. It lists PyInstaller **onedir/onefile**, cx_Freeze,
Briefcase, wheel, ZIP and macOS `.app`, on **Windows x64, Linux x64/arm64,
macOS Intel/Apple Silicon**. These are vendor-listed targets, not combinations
tested here.

**Subscription dependency — rechecked 2026-11-16.** The
[pricing page](https://pylocket.com/pricing.html) says issued licences never
expire (no per-licence expiry). The official
[billing terms](https://docs.pylocket.com/part-4-topics/billing/) add that,
after the seller's paid access ends, issued licences keep working for a 30-day
grace period and stop activating unless the account is resubscribed within it.
This is part of the model to evaluate alongside the per-licence price.

pyobfus’s chosen difference is a local-first workflow with ordinary Python
Community output, private mapping/traceback restore and verifiable build
evidence; developers retain control over their source, builds and customer
relationships ([2026-11-15 assessment](../COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md)).

## Where PyLocket is genuinely stronger

The following protection assessment is retained from **2026-10-02**, without
new testing in the 2026-11-15 refresh:

Per-function bytecode encryption with device-bound keys issued only at
activation — and never embedded in the shipped binary — is a materially
stronger tamper-resistance claim than pyobfus's AST transformation plus the
Pro Runtime String Vault. There is no static file-plus-key combination an
attacker can extract from a single copy of the app; each licensed device gets
its own key at runtime. If your threat model is "prevent a static, offline
analysis of a shipped desktop binary," that architecture is a real advantage.

## Where PyLocket doesn't compete with pyobfus at all

**Retained assessment — reviewed 2026-10-02; not rechecked 2026-11-15.**
PyLocket's documentation, comparison pages, and marketing copy contain no
mention of debugging support, traceback handling, or AI-assisted development
workflows. That is not an oversight this comparison is reading into — it
reflects a different design goal: PyLocket optimizes for opaque,
tamper-resistant delivery of a finished desktop application, the same
tradeoff family as PyArmor and Nuitka above. Once code ships through
per-function runtime decryption, there is no natural mapping back to
readable stack traces for whoever has to debug a customer's crash report.
pyobfus's `--save-mapping` / `--unmap` workflow exists specifically to keep
that path open — see the [Layered Deployment Strategy](../COMPARISON.md#layered-deployment-strategy)
below for how the two tradeoffs coexist rather than compete head-on.

## When to Choose pyobfus

- You need **Python 3.9-3.11** support (PyLocket requires 3.12+)
- You want **one-time pricing** instead of a subscription + per-seat licensing
- You need to **debug production issues** without giving up protection
- You're protecting a **library or backend service**, not selling a licensed desktop app

## When to Choose PyLocket

- You're shipping a **commercial desktop application** and want licensing,
  device binding, and checkout built in rather than assembled yourself
- Your threat model is **static offline analysis of a distributed binary**,
  and per-function tamper resistance matters more than
  post-deployment debuggability
- You only need to support **Python 3.12+**

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool. Its dated scope and disclaimer apply here as well.
