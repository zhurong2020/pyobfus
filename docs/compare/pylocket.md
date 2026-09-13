# pyobfus vs PyLocket

PyLocket encrypts individual functions' bytecode and bundles a licensing and
commerce platform around it. It answers a different question from pyobfus: how
to sell a desktop application, rather than how to protect a codebase you
already ship.

PyLocket is a newer, developer-first platform (launched after this document's
other comparisons were written) that positions itself against SOURCEdefender
as "a full platform" rather than an encryption utility.

| Feature | pyobfus | PyLocket |
|---------|---------|----------|
| **Price (Pro)** | **$45** (one-time) | Flat subscription + $4/activated license |
| **Python versions** | **3.9 - 3.14** | 3.12 - 3.14 only |
| **Protection unit** | AST transformation on whole modules | Per-function bytecode encryption |
| **Key management** | Local Pro license / Runtime String Vault | Device-bound keys issued at activation, never embedded in the shipped app |
| **Anti-debug / anti-VM** | Anti-debugging (Pro) | Anti-debug + anti-VM + dynamic API resolution + memory protection |
| **Open source** | Yes (Core: Apache 2.0) | No |
| **Built-in commerce** (licensing, delivery, checkout, trials) | No — bring your own | Yes, this is the product's headline differentiator |
| **Debugging / traceback workflow** | Reverse stack-trace mapping (`--unmap`), purpose-built for AI-assisted debugging | Not mentioned anywhere in PyLocket's own docs or marketing |
| **AI-assisted development workflow** | Explicit design goal | Not mentioned |

## Where PyLocket is genuinely stronger

Per-function bytecode encryption with device-bound keys issued only at
activation — and never embedded in the shipped binary — is a materially
stronger tamper-resistance claim than pyobfus's AST transformation plus the
Pro Runtime String Vault. There is no static file-plus-key combination an
attacker can extract from a single copy of the app; each licensed device gets
its own key at runtime. If your threat model is "prevent a static, offline
analysis of a shipped desktop binary," that architecture is a real advantage.

## Where PyLocket doesn't compete with pyobfus at all

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
  and maximum per-function tamper resistance matters more than
  post-deployment debuggability
- You only need to support **Python 3.12+**

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool.
