# pyobfus vs PyArmor

PyArmor is the most established commercial Python obfuscator, and the tool most
people weigh pyobfus against. Both protect source before it ships; they differ
in what they do to your build, your runtime, and your ability to debug what
comes back from production.

| Feature | pyobfus | PyArmor |
|---------|---------|---------|
| **Price (Pro)** | **$45** (one-time) | $89 (one-time; [official cart](https://jondy.github.io/paypal/index.html), verified 2026-09-01) |
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

## PyArmor Pain Points (from user feedback)

Based on GitHub issues and community feedback, common PyArmor frustrations include:

1. **Opaque trial limit (~935-940 lines/file)**: Errors out at this threshold with the message `ERROR out of license` — no threshold number, no upgrade hint, no documentation. Verified empirically on PyArmor 9.2.4 in clean venv on 2026-05-09 (935 lines passes, 940 fails; line count not byte count — 900 lines at 67 KB still passes). Full reproducible methodology: [`PYARMOR_TRIAL_LIMIT_EXPERIMENT.md`](../PYARMOR_TRIAL_LIMIT_EXPERIMENT.md).
2. **PyInstaller conflicts**: DLL version mismatches, slow startup times
3. **Environment issues**: Doesn't work in MSYS, no warning given
4. **Future compatibility**: License may not work with future PyArmor versions
5. **Complex deployment**: Requires distributing native `pytransform` libraries

## Bytecode Protection Is Not Magic

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

## When to Choose pyobfus

- You want **transparent, predictable** pricing and limits
- You need **pure Python output** without native dependencies
- You value **open-source** and code auditability
- You're building **cross-platform** applications
- You want **50% cost savings** over PyArmor Pro

## When to Choose PyArmor

- You require **Themida protection** (Windows only)
- You're already invested in PyArmor's ecosystem
- You need bytecode-level encryption

## Migrating from PyArmor

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

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool.
