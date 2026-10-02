# pyobfus vs PyArmor

PyArmor is a long-running commercial Python obfuscator and a common alternative
considered alongside pyobfus. Both protect source before it ships; they differ
in what they do to your build, your runtime, and your ability to debug what
comes back from production.

> **Baseline — reviewed 2026-10-02.** PyArmor facts use the official 9.2.7
> documentation, PyPI metadata and public purchase page. The free-tier line
> threshold is a separate reproducible test of PyArmor 9.2.4 performed on
> 2026-05-09; it has **not** been re-measured on 9.2.7 and is labelled
> accordingly. Features and restrictions vary by licence, platform and build
> mode. Prices and terms can change, so verify the linked official sources and
> test your own project. PyArmor is a trademark of its owner; this independent
> comparison is not endorsed by PyArmor and is not a warranty, security
> guarantee or legal advice.

| Feature | pyobfus | PyArmor |
|---------|---------|---------|
| **Price (Pro)** | **$45** (one-time) | $89 (one-time; [official purchase page](https://jondy.github.io/paypal/index.html), checked 2026-10-02) |
| **Price difference at snapshot** | **$44 lower** | Baseline |
| **Free tier** | No file/line cap on Community features | Official docs say it cannot obfuscate “big scripts”; our 9.2.4 test passed 935 lines and failed 940 lines |
| **Pro feature trial** | **5 days free** | Free trial does not unlock licensed features; official docs do not state a numeric big-script threshold |
| **Source availability** | Core: Apache-2.0; Pro builder: proprietary | Proprietary product |
| **Inspectable implementation** | Community implementation is public | Public documentation and packaged interface; implementation is not published as open source |
| **Runtime dependency** | Community output is pure Python; some Pro modes use the separately redistributable pure-Python runtime | Generated output uses a platform-specific PyArmor runtime package |
| **Output format** | Pure `.py` files | `.py` + native libraries |
| **Cross-platform output** | Community output is portable; Pro runtime policies may intentionally restrict it | Runtime packages and advanced modes depend on target platforms; verify the selected mode |
| **Python 3.9-3.14** | Yes | Yes |
| **String encryption** | AES-256 (Pro) | AES (Pro) |
| **Anti-debugging** | Yes (Pro) | Yes (Pro) |
| **Control flow flattening** | Yes (Pro v0.3.0+) | Yes (Pro) |
| **Import obfuscation** | Yes (Pro, runtime importlib + encrypted import strings) | Yes (Pro) |
| **Function-body virtualization** | No (AST-level only) | Yes — VMC/ECC modes (PyArmor 9.2.7 docs, checked 2026-10-02) |
| **License binding** | Per-device (3 devices) | Per-device |
| **Future Python support** | Community-driven | "Can't guarantee" (per docs) |

## Constraints and trade-offs

These items have different evidence strengths; each should be read only within
the stated source or tested version:

1. **Free-version big-script restriction**: official 9.2.7 docs disclose that
   the free version cannot obfuscate “big scripts” but do not give a numeric
   threshold. In our clean-venv **9.2.4** experiment on 2026-05-09, 935 lines
   passed and 940 failed with `ERROR out of license`; this may differ in later
   releases. See the full reproducible
   [methodology](../PYARMOR_TRIAL_LIMIT_EXPERIMENT.md).
2. **Platform/runtime planning**: PyArmor's native runtime and some advanced
   modes require target-specific build decisions. This can provide stronger
   protection, but should be tested across every shipping platform.
3. **Future-version licence compatibility**: PyArmor's official licence page
   says non-CI licences keep working with the purchased version but may not
   work with future PyArmor versions.

## Bytecode Protection Is Not Magic

PyArmor's native runtime and bytecode-oriented protection are stronger than
plain AST rewriting against casual inspection. That does not make protected
bytecode irreversible. Public research tooling now exists that targets PyArmor
8.0-9.2.x output and can statically convert protected scripts back to bytecode
disassembly and experimental source without executing the protected program:
[Pyarmor-Static-Unpack-1shot](https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot).
The tool's own README is careful about limits: disassembly can be accurate while
decompiled source may be incomplete or incorrect.

**A stronger PyArmor tier exists above plain RFT/bytecode encryption.** In the
PyArmor 9.2.7 documentation checked on 2026-10-02, `pyarmor build --vmc`/`--ecc` replace an entire function
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
- The documented pyobfus workflow better matches your portability and
  reverse-mapping needs, and the current $45 price fits your budget

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
tool. Its dated scope and disclaimer apply here as well.
