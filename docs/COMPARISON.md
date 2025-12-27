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

## Detailed Comparison

### pyobfus vs PyArmor

PyArmor is the most established Python obfuscator. Here's how pyobfus compares:

| Feature | pyobfus | PyArmor |
|---------|---------|---------|
| **Price (Pro)** | **$45** (one-time) | $89 (one-time) |
| **Price savings** | **50% cheaper** | - |
| **Free tier** | Unlimited (Community features) | Vague "trial" limits |
| **Pro trial** | **5 days free** (full features) | Vague limits |
| **Open source** | Yes (Core: Apache 2.0, Pro: Proprietary) | No |
| **Auditable code** | Yes | No |
| **Native dependencies** | None | Requires `pytransform` runtime |
| **Output format** | Pure `.py` files | `.py` + native libraries |
| **Cross-platform output** | Yes (single output works everywhere) | Requires per-platform build |
| **Python 3.8-3.14** | Yes | Yes |
| **String encryption** | AES-256 (Pro) | AES (Pro) |
| **Anti-debugging** | Yes (Pro) | Yes (Pro) |
| **Control flow flattening** | Yes (Pro v0.3.0+) | Yes (Pro) |
| **License binding** | Per-device (3 devices) | Per-device |
| **Future Python support** | Community-driven | "Can't guarantee" (per docs) |

#### PyArmor Pain Points (from user feedback)

Based on GitHub issues and community feedback, common PyArmor frustrations include:

1. **Unpredictable trial limits**: "My big script fails to obfuscate" with no clear explanation
2. **PyInstaller conflicts**: DLL version mismatches, slow startup times
3. **Environment issues**: Doesn't work in MSYS, no warning given
4. **Future compatibility**: License may not work with future PyArmor versions
5. **Complex deployment**: Requires distributing native `pytransform` libraries

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
| **Python versions** | 3.8 - 3.14 | 3.3 - 3.7 (outdated) |
| **Multi-file support** | Yes (cross-file) | Limited |
| **Configuration** | YAML files | Web interface |
| **CI/CD integration** | Yes | No |
| **Offline usage** | Yes | No |

#### When to Choose pyobfus

- You need **modern Python** (3.8+) support
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

#### When to Choose pyobfus

- You're distributing **Python libraries** (not executables)
- You want **one-time payment** vs subscription
- You need **fast builds** (no compilation)
- **File size** matters

#### When to Choose Nuitka

- You need **standalone executables**
- Users shouldn't need Python installed
- You want **maximum binary protection**

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
   - Modern Python 3.8-3.14 support
   - Batch processing for directories

---

## Conclusion

**Choose pyobfus if you want:**
- Transparent, affordable pricing (50% cheaper than PyArmor)
- Open-source trust and auditability
- Pure Python output without native dependencies
- Cross-platform compatibility from a single build
- Modern Python 3.8-3.14 support

**Get started:**
```bash
pip install pyobfus
pyobfus --help
```

**Questions?** Open an issue on [GitHub](https://github.com/zhurong2020/pyobfus/issues) or join our [Discussions](https://github.com/zhurong2020/pyobfus/discussions).
