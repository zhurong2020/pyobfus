# Python Obfuscation Tools Comparison

A comprehensive comparison of Python code obfuscation tools to help you choose the right solution.

## Quick Summary

| Tool | Price | Approach | Best For |
|------|-------|----------|----------|
| **pyobfus** | Free / $45 Pro | AST transformation | Cross-platform Python distribution |
| **PyArmor** | Free trial / $89 Pro | Native runtime + encryption | Maximum protection (with complexity) |
| **Oxyry** | Online service | Name mangling | Quick one-off obfuscation |
| **Cython** | Free / $270/yr Commercial | Compile to C | Performance + obfuscation |
| **Nuitka** | Free / $270/yr Commercial | Compile to binary | Standalone executables |
| **PyLocket** | Subscription + $4/license | Per-function bytecode encryption + commerce platform | Selling a desktop app with built-in licensing |

## Detailed Comparison

### pyobfus vs PyArmor

PyArmor is the most established Python obfuscator. Here's how pyobfus compares:

| Feature | pyobfus | PyArmor |
|---------|---------|---------|
| **Price (Pro)** | **$45** (one-time) | $89 (one-time) |
| **Price savings** | **50% cheaper** | - |
| **Free tier** | Unlimited (Community features) | ~935-940 lines/file before `ERROR out of license` (PyArmor 9.2.4, verified 2026-05-09) |
| **Pro trial** | **5 days free** (full features) | Same opaque trial limits as free; no documented threshold |
| **Open source** | Yes (Core: Apache 2.0, Pro: Proprietary) | No |
| **Auditable code** | Yes | No |
| **Native dependencies** | None | Requires `pytransform` runtime |
| **Output format** | Pure `.py` files | `.py` + native libraries |
| **Cross-platform output** | Yes (single output works everywhere) | Requires per-platform build |
| **Python 3.9-3.14** | Yes | Yes |
| **String encryption** | AES-256 (Pro) | AES (Pro) |
| **Anti-debugging** | Yes (Pro) | Yes (Pro) |
| **Control flow flattening** | Yes (Pro v0.3.0+) | Yes (Pro) |
| **Import obfuscation** | Yes (Pro, runtime importlib + encrypted import strings) | Yes (Pro) |
| **Function-body virtualization** | No (AST-level only) | Yes — VMC/ECC modes (PyArmor 9.2.x, 2026) |
| **License binding** | Per-device (3 devices) | Per-device |
| **Future Python support** | Community-driven | "Can't guarantee" (per docs) |

#### PyArmor Pain Points (from user feedback)

Based on GitHub issues and community feedback, common PyArmor frustrations include:

1. **Opaque trial limit (~935-940 lines/file)**: Errors out at this threshold with the message `ERROR out of license` — no threshold number, no upgrade hint, no documentation. Verified empirically on PyArmor 9.2.4 in clean venv on 2026-05-09 (935 lines passes, 940 fails; line count not byte count — 900 lines at 67 KB still passes). Full reproducible methodology: [`PYARMOR_TRIAL_LIMIT_EXPERIMENT.md`](PYARMOR_TRIAL_LIMIT_EXPERIMENT.md).
2. **PyInstaller conflicts**: DLL version mismatches, slow startup times
3. **Environment issues**: Doesn't work in MSYS, no warning given
4. **Future compatibility**: License may not work with future PyArmor versions
5. **Complex deployment**: Requires distributing native `pytransform` libraries

#### Bytecode Protection Is Not Magic

PyArmor's native runtime and bytecode-oriented protection are stronger than
plain AST rewriting against casual inspection. That does not make protected
bytecode irreversible. Public research tooling now exists that targets PyArmor
8.0-9.2.x output and can statically convert protected scripts back to bytecode
disassembly and experimental source without executing the protected program:
[Pyarmor-Static-Unpack-1shot](https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot).
The tool's own README is careful about limits: disassembly can be accurate while
decompiled source may be incomplete or incorrect.

**A stronger PyArmor tier exists above plain RFT/bytecode encryption.** As of
PyArmor 9.2.x (2026), `pyarmor build --vmc`/`--ecc` replace an entire function
body — not just names — with either PyArmor's own VM bytecode (VMC mode: no C
compiler needed at build time; PyArmor's own docs describe the result as
reversible) or compiled C machine code (ECC mode: requires a C compiler at
build time; irreversible). We haven't verified whether the unpacking tooling
above also handles VMC/ECC output specifically — its documented scope is
standard `pytransform`-encrypted bytecode. Either way, this function-level
virtualization is a real capability pyobfus doesn't have: pyobfus stays at
the AST source-transformation layer and doesn't compile function bodies to a
private VM instruction set or native code. If VMC/ECC-grade function
virtualization is the requirement, PyArmor's Pro/Group tiers are the right
tool for that job, not pyobfus.

That matters for how to choose a tool. If your threat model is "stop a curious
customer from reading ordinary source," PyArmor's bytecode layer is useful. If
your threat model includes a determined reverser with public unpacking tooling,
neither PyArmor nor pyobfus should be described as cryptographic protection for
client-side Python. The more reliable question is operational: which failure
mode do you want?

- **PyArmor's tradeoff**: harder first look, native runtime dependency, and a
  less transparent debugging/deployment story.
- **pyobfus's tradeoff**: intentionally pure-Python AST output, easier to
  inspect by a determined attacker, but predictable builds, readable failure
  modes, and reverse stack-trace mapping for AI-assisted debugging.

This is also why pyobfus stays in the "defender-lane" rather than hiding
malware behind opaque bytecode. PyArmor is recurrently seen in malicious Python
samples, including the SANS ISC write-up
[Obfuscated Malicious Python Scripts with PyArmor](https://isc.sans.edu/diary/31840).
pyobfus is designed for legitimate code owners who still need to debug what
they ship.

#### When to Choose pyobfus

- You want **transparent, predictable** pricing and limits
- You need **pure Python output** without native dependencies
- You value **open-source** and code auditability
- You're building **cross-platform** applications
- You want **50% cost savings** over PyArmor Pro

#### When to Choose PyArmor

- You require **Themida protection** (Windows only)
- You're already invested in PyArmor's ecosystem
- You need bytecode-level encryption

---

### pyobfus vs Oxyry

Oxyry is an online Python obfuscation service.

| Feature | pyobfus | Oxyry |
|---------|---------|-------|
| **Deployment** | CLI tool (local) | Web service only |
| **Privacy** | Code never leaves your machine | Code uploaded to server |
| **Python versions** | 3.9 - 3.14 | 3.3 - 3.7 (outdated) |
| **Multi-file support** | Yes (cross-file) | Limited |
| **Configuration** | YAML files | Web interface |
| **CI/CD integration** | Yes | No |
| **Offline usage** | Yes | No |

#### When to Choose pyobfus

- You need **modern Python** (3.9+) support
- You want code to **stay local** (privacy/compliance)
- You need **CI/CD integration**
- You're obfuscating **multi-file projects**

#### When to Choose Oxyry

- Quick, one-off obfuscation of small scripts
- You're comfortable with Python 3.7 or older

---

### pyobfus vs Cython

Cython compiles Python to C code, providing both performance benefits and obfuscation.

| Feature | pyobfus | Cython |
|---------|---------|--------|
| **Approach** | AST transformation | Compile to C |
| **Output** | `.py` files | `.so`/`.pyd` (platform-specific) |
| **Cross-platform** | Yes (single output) | No (compile per platform) |
| **Build complexity** | None | Requires C compiler |
| **Development workflow** | Unchanged | Compilation step required |
| **Performance** | Python speed | Near-C speed |
| **Reversibility** | Names irreversible | Binary harder to reverse |

#### When to Choose pyobfus

- You need **cross-platform** distribution
- You want to **avoid compilation** complexity
- You need **fast iteration** during development
- Your users don't have C compilers

#### When to Choose Cython

- **Performance** is critical (CPU-bound code)
- You can handle **per-platform builds**
- You want **binary-level** protection

---

### pyobfus vs Nuitka

Nuitka compiles Python to standalone executables.

| Feature | pyobfus | Nuitka |
|---------|---------|--------|
| **Output** | `.py` files | Standalone binary |
| **Distribution** | Requires Python installed | Self-contained |
| **Build time** | Instant | Minutes to hours |
| **File size** | Original size | Large (includes Python) |
| **Commercial price** | $45 | ~$270/year |
| **License model** | One-time | Annual subscription |
| **Traceback protection** | RSA-2048-OAEP + AES-256-GCM hybrid, reversible via `pyobfus-unscrub` | Symmetric encryption only ([per Nuitka's own docs](https://nuitka.net/doc/commercial/traceback-encryption.html), asymmetric "planned" as of 2026-08) |

#### Traceback Protection: Hybrid vs Symmetric-Only

Both tools ship a feature for the same real problem — a production traceback
can leak internal file/function/variable names to whoever sees it. Nuitka
Commercial's "Traceback Encryption" (part of its ~$270/year tier) encrypts
tracebacks so only the vendor can decode them, but as of this writing its own
documentation states the encryption is symmetric only, with asymmetric
support still on the roadmap. pyobfus's `--scrub-traceback` (Pro) already
uses a hybrid RSA-2048-OAEP + AES-256-GCM scheme — the production side never
holds a key capable of decrypting what it just encrypted, only the
private-key holder can, via the separate `pyobfus-unscrub` CLI. Symmetric
encryption is not insecure by itself, but it does mean whichever process
performs the encryption necessarily holds a key capable of reversing it too
— a meaningfully different key-management story than asymmetric encryption's
one-way trapdoor.

#### When to Choose pyobfus

- You're distributing **Python libraries** (not executables)
- You want **one-time payment** vs subscription
- You need **fast builds** (no compilation)
- **File size** matters

#### When to Choose Nuitka

- You need **standalone executables**
- Users shouldn't need Python installed
- You want **maximum binary protection**

> **Want a standalone executable without Nuitka's price or compile times?**
> pyobfus pairs with the free, MIT-licensed [PyInstaller](https://pyinstaller.org/)
> to ship a single-file binary with mangled identifiers — obfuscate first,
> then bundle. See the [PyInstaller Cookbook](PYINSTALLER_COOKBOOK.md) for a
> full worked example, including verification that the original names never
> reach the compiled binary.

---

### pyobfus vs PyLocket

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

#### Where PyLocket is genuinely stronger

Per-function bytecode encryption with device-bound keys issued only at
activation — and never embedded in the shipped binary — is a materially
stronger tamper-resistance claim than pyobfus's AST transformation plus the
Pro Runtime String Vault. There is no static file-plus-key combination an
attacker can extract from a single copy of the app; each licensed device gets
its own key at runtime. If your threat model is "prevent a static, offline
analysis of a shipped desktop binary," that architecture is a real advantage.

#### Where PyLocket doesn't compete with pyobfus at all

PyLocket's documentation, comparison pages, and marketing copy contain no
mention of debugging support, traceback handling, or AI-assisted development
workflows. That is not an oversight this comparison is reading into — it
reflects a different design goal: PyLocket optimizes for opaque,
tamper-resistant delivery of a finished desktop application, the same
tradeoff family as PyArmor and Nuitka above. Once code ships through
per-function runtime decryption, there is no natural mapping back to
readable stack traces for whoever has to debug a customer's crash report.
pyobfus's `--save-mapping` / `--unmap` workflow exists specifically to keep
that path open — see the [Layered Deployment Strategy](#layered-deployment-strategy)
below for how the two tradeoffs coexist rather than compete head-on.

#### When to Choose pyobfus

- You need **Python 3.9-3.11** support (PyLocket requires 3.12+)
- You want **one-time pricing** instead of a subscription + per-seat licensing
- You need to **debug production issues** without giving up protection
- You're protecting a **library or backend service**, not selling a licensed desktop app

#### When to Choose PyLocket

- You're shipping a **commercial desktop application** and want licensing,
  device binding, and checkout built in rather than assembled yourself
- Your threat model is **static offline analysis of a distributed binary**,
  and maximum per-function tamper resistance matters more than
  post-deployment debuggability
- You only need to support **Python 3.12+**

---

## Feature Matrix

### Obfuscation Techniques

| Technique | pyobfus Free | pyobfus Pro | PyArmor | Cython |
|-----------|-------------|-------------|---------|--------|
| Name mangling | Yes | Yes | Yes | Yes (binary) |
| String encoding (Base64) | Yes | Yes | No | No |
| String encryption (AES) | No | **Yes** | Yes | No |
| Docstring removal | Yes | Yes | Yes | No |
| Comment removal | Yes | Yes | Yes | Yes |
| Anti-debugging | No | **Yes** | Yes | No |
| Control flow flattening | No | **Yes** | Yes | No |
| Dead code injection | No | **Yes** | No | No |
| Import obfuscation | No | **Yes** | Yes | No |
| License embedding | No | **Yes** | Yes | No |
| Configuration presets | No | **Yes** | No | No |

### Developer Experience

| Feature | pyobfus | PyArmor | Oxyry | Cython |
|---------|---------|---------|-------|--------|
| CLI tool | Yes | Yes | No | Yes |
| YAML configuration | Yes | Yes | No | setup.py |
| Dry-run preview | Yes | No | No | No |
| Cross-file support | Yes | Yes | Limited | Yes |
| CI/CD friendly | Yes | Yes | No | Yes |
| Error messages | Clear | Often vague | N/A | Technical |

---

## Pricing Comparison

### One-Time Purchase

| Tool | Free Tier | Pro/Commercial |
|------|-----------|----------------|
| **pyobfus** | Unlimited (5-day Pro trial) | **$45** |
| **PyArmor Basic** | Trial (vague limits) | $52 |
| **PyArmor Pro** | Trial (vague limits) | $89 |
| **PyArmor Group** | Trial (vague limits) | $158 |

### Annual Subscription

| Tool | Price/Year |
|------|------------|
| **pyobfus** | $0 (one-time Pro) |
| **PyArmor CI** | $90/year |
| **Nuitka Commercial** | ~$270/year |

### Total Cost of Ownership (3 Years)

| Tool | Year 1 | Year 2 | Year 3 | **Total** |
|------|--------|--------|--------|-----------|
| **pyobfus Pro** | $45 | $0 | $0 | **$45** |
| **PyArmor Pro** | $89 | $0 | $0 | **$89** |
| **Nuitka** | $270 | $270 | $270 | **$810** |

---

## Migration Guide

### From PyArmor to pyobfus

1. **Install pyobfus**:
   ```bash
   pip install pyobfus
   ```

2. **Create configuration** (if you had PyArmor config):
   ```bash
   pyobfus --init-config general
   # Edit pyobfus.yaml to match your needs
   ```

3. **Run obfuscation**:
   ```bash
   # PyArmor: pyarmor gen src/
   # pyobfus equivalent:
   pyobfus src/ -o dist/
   ```

4. **Key differences**:
   - No native `pytransform` library needed
   - Output is pure Python
   - Cross-file imports automatically handled

### From Oxyry to pyobfus

1. **Install locally**:
   ```bash
   pip install pyobfus
   ```

2. **Run from command line**:
   ```bash
   pyobfus your_script.py -o obfuscated.py
   ```

3. **Benefits**:
   - Code stays on your machine
   - Modern Python 3.9-3.14 support
   - Batch processing for directories

---

## Layered Deployment Strategy

Most production Python projects don't need a single obfuscation tool — they need the right tool for each layer of the codebase.

A layered approach that fits the 2026 ecosystem:

| Stage | Recommended | Why |
|---|---|---|
| **Development / testing** | No obfuscation | Faster iteration; full debug visibility |
| **Pre-release / staging** | pyobfus (Community or Pro) | AST mangling + mapping preserved → AI assistants can still debug; cross-platform `.py` output; no native deps |
| **Production / customer delivery** | pyobfus + optional PyArmor Pro or Nuitka Commercial on highest-value modules | pyobfus protects the entire codebase consistently; PyArmor adds bytecode-level protection on the few modules that genuinely need it; Nuitka adds compile-to-native for performance-critical sections |

**Why pyobfus is the always-on default layer**: it's the only tool in this space that doesn't break AI-assisted debugging in production. PyArmor's bytecode encryption and Nuitka's compilation are both one-way — once a stack trace comes back from production, neither tool can map it back to readable identifiers without losing the protection. pyobfus's `--save-mapping` + `--unmap` workflow is purpose-built for this: the obfuscated artifact ships to customers, the mapping stays in your secure storage, and you can hand a reversed trace to Claude Code or Cursor without giving up the obfuscation.

**Why pyobfus alone may not be enough for the crown jewels**: pyobfus's protection is AST-level, which means a determined attacker with time can reverse most of the structure. If a single algorithm module is the company's crown jewel, stacking PyArmor Pro's bytecode encryption or Nuitka's native compilation on top of that one module is rational. We don't pretend otherwise.

**Why bytecode encryption alone may not be enough either**: public static-unpack
tools for PyArmor 8.0-9.2.x show that "encrypted bytecode" should be treated as
a speed bump, not a guarantee that client-side Python cannot be inspected.
Stacking tools can make sense, but it does not remove the need for server-side
boundaries around truly secret algorithms, credentials, or licensing decisions.

This honest framing is part of why pyobfus is priced at $45 single-tier instead of competing with PyArmor's enterprise track — pyobfus is the tool you reach for first, not necessarily the only tool in the toolbox.

---

## Conclusion

**Choose pyobfus if you want:**
- Transparent, affordable pricing (50% cheaper than PyArmor)
- Open-source trust and auditability
- Pure Python output without native dependencies
- Cross-platform compatibility from a single build
- Modern Python 3.9-3.14 support

**Get started:**
```bash
pip install pyobfus
pyobfus --help
```

**Questions?** Open an issue on [GitHub](https://github.com/zhurong2020/pyobfus/issues) or join our [Discussions](https://github.com/zhurong2020/pyobfus/discussions).
