# pyobfus — the Python obfuscator

<p align="center">
  <img src="https://raw.githubusercontent.com/zhurong2020/pyobfus/main/docs/assets/logo.jpeg" alt="pyobfus Logo" width="200">
</p>

**pyobfus** (pronounced as "Python obfuscator") is a modern, AST-based **python-obfuscator / code-obfuscator** with framework-aware presets, reverse stack-trace mapping for AI-assisted debugging, and a machine-readable JSON CLI designed for [Claude Code](https://claude.com/claude-code), [Cursor](https://cursor.com/), [Codex](https://openai.com/codex/), and MCP agents. A transparent, open-source alternative to PyArmor.

[![PyPI version](https://img.shields.io/pypi/v/pyobfus.svg)](https://pypi.org/project/pyobfus/)
[![PyPI downloads](https://img.shields.io/pypi/dm/pyobfus.svg)](https://pypi.org/project/pyobfus/)
[![Documentation Status](https://readthedocs.org/projects/pyobfus/badge/?version=latest)](https://pyobfus.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/License-Dual%20(Apache%202.0%20%2B%20Proprietary)-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9--3.14-blue.svg)](https://www.python.org/downloads/)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/12788/badge)](https://www.bestpractices.dev/projects/12788)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20846053.svg)](https://doi.org/10.5281/zenodo.20846053)
[![pyobfus MCP server](https://glama.ai/mcp/servers/zhurong2020/pyobfus/badges/score.svg)](https://glama.ai/mcp/servers/zhurong2020/pyobfus)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python code obfuscator built with AST-based transformations. **Supports Python 3.9 through 3.14**. Provides reliable name mangling, string encoding, control-flow flattening, AES-256 string encryption, and — unique to pyobfus — a reverse-mapping workflow that lets you (or your AI coding assistant) debug obfuscated stack traces without giving up the protection.

> **🔒 Pro Edition available** — 6 patent-targeted protection mechanisms (Selective Opacity, forensic watermarking, Runtime String Vault, and more) layered on top of the free AST obfuscator, $45 one-time, no subscription. See [Pro Edition](#-pro-edition) below.

> **🔧 What's new in v0.5.6** — Fixed a CLI bug where running any preset the normal, documented way (`--preset fastapi/django/flask/pydantic/click/sqlalchemy/ml/safe`, no extra flags) could silently override the preset's own choices: parameter names got mangled despite `preserve_param_names=True`, and docstrings got stripped despite `--preset safe`'s core promise to keep them. Both now behave as documented. Full details in the [CHANGELOG](CHANGELOG.md); see [Pro Edition](#-pro-edition) below.

## 🔌 Companion MCP server: [`pyobfus-mcp`](pyobfus_mcp/)

This repository ships **two installable packages**:

| Package | What it is | Install |
|---|---|---|
| [`pyobfus`](https://pypi.org/project/pyobfus/) | The Python obfuscator (CLI + library). | `pip install pyobfus` |
| [`pyobfus-mcp`](https://pypi.org/project/pyobfus-mcp/) | A **Model Context Protocol (MCP) server** that exposes pyobfus's tools to AI coding agents. | `uvx pyobfus-mcp` (zero-install) or `pip install pyobfus-mcp` |

The MCP server lives in [`pyobfus_mcp/`](pyobfus_mcp/) and is built on the official [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) (FastMCP). It registers eight MCP tools so **Claude Desktop, Claude Code, Cursor, Windsurf, Zed, and Codex** can call pyobfus directly from agent conversations — no shelling out:

| MCP tool | Implementation | Purpose |
|---|---|---|
| `protect_project` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | **One-call, self-verifying pipeline**: scan → preset → obfuscate → byte-compile + import-smoke-test the output → return `verified: true/false`. The agent reports a green check instead of hoping the transform didn't break anything |
| `check_obfuscation_risks` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | Pre-flight risk scan (eval/exec, dynamic attribute, framework reflection) |
| `generate_pyobfus_config` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | Auto-detect framework → write a working `pyobfus.yaml` |
| `unmap_stack_trace` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | Reverse obfuscated identifiers in a production stack trace |
| `list_presets` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | Enumerate community / framework / Pro presets |
| `explain_preset` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | Describe what a named preset changes |
| `recommend_tier` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | Analyze a project and recommend community vs Pro tier, with reasoning |
| `start_pro_trial` | [`pyobfus_mcp/tools.py`](pyobfus_mcp/pyobfus_mcp/tools.py) | Return structured guidance for starting the 5-day Pro trial |

The server is registered in the **official [MCP Registry](https://registry.modelcontextprotocol.io/)** under `io.github.zhurong2020/pyobfus-mcp`. The transport is stdio. See [`pyobfus_mcp/README.md`](pyobfus_mcp/README.md) for per-client configuration snippets.

### 🧩 Claude Code skill / plugin

This repo is also a **Claude Code plugin marketplace**. The `pyobfus-protect` skill teaches an agent the full "protect Python before shipping — obfuscate **and** verify it still runs" workflow (MCP-first, CLI fallback):

```
/plugin marketplace add zhurong2020/pyobfus
/plugin install pyobfus@pyobfus
```

See [`skills/`](skills/) for the skill and install details. (This is distinct from [`templates/ai-integration/`](templates/ai-integration/), which are copy-in rule files for *your* project.)

### 🤖 AI-native features

- **`pyobfus --check src/`** — pre-flight risk scan: detects `eval`/`exec`, dynamic attribute access, and framework reflection points before you obfuscate. JSON output with an `ai_hint` telling your AI assistant what to run next.
- **`pyobfus --init src/`** — zero-config onboarding: scans the project, detects FastAPI/Django/Pydantic/Click/SQLAlchemy, and writes a ready-to-use `pyobfus.yaml`.
- **`pyobfus --unmap --trace error.log --mapping mapping.json`** — reverse obfuscated identifiers in a production stack trace so you can debug (or hand the trace to an AI assistant) without reversing the obfuscation itself.
- **`pyobfus … --save-mapping mapping.json --trace-marker`** — stamp each obfuscated file with a `# pyobfus:obfuscated` header (id + mapping filename + the exact `--unmap` command) so an AI agent that lands in an obfuscated file from a traceback immediately knows it's pyobfus output and how to reverse the names.
- **`pyobfus … --provenance-manifest provenance.json`** — write a local JSON manifest (obfuscated files, config hash, pyobfus version, mapping digest, and a self-consistency integrity digest — not a cryptographic signature) for offline build provenance.
- **Framework-aware presets** — `--preset fastapi | django | flask | pydantic | click | sqlalchemy | ml` with built-in exclusions for dispatch methods, decorators, ORM fields, migrations, model-serving wrappers, and dependency-injection parameters.
- **Global `--json`** — every CLI mode (`obfuscate`, `--check`, `--unmap`, `--init`) emits the same structured schema with an `ai_hint` field, ready for Claude Code, Cursor, Windsurf, and MCP servers to consume.

## Features

### ✅ Free Edition

The following features are **fully implemented and available** in the current version:

- **Cross-File Obfuscation**: Consistent name obfuscation across multiple files
  - Automatic import statement rewriting
  - `__all__` list updates with obfuscated names
  - Global symbol table with collision detection
  - Two-phase obfuscation pipeline (Scan → Transform)
  - Preview mode with `--dry-run` flag

- **Name Mangling**: Rename variables, functions, classes, and class attributes to obfuscated names (I0, I1, I2...)
- **Comment Removal**: Strip comments and docstrings
- **String Encoding**: Base64 encoding for string literals with automatic decoder injection
- **Parameter Preservation**: Preserve function parameter names for keyword argument compatibility (`--preserve-param-names`)
- **Multi-file Support**: Obfuscate entire projects with preserved import relationships
- **File Filtering**: Exclude files using glob patterns (test files, config files, etc.)
- **Configuration Files**: YAML-based configuration for repeatable builds
- **Selective Obfuscation**: Preserve specific names (builtins, magic methods, custom exclusions)
- **Configuration Presets**: `--preset safe | balanced | aggressive` for quick obfuscation-strength tradeoffs, plus **framework-aware presets** — `--preset fastapi | django | flask | pydantic | click | sqlalchemy | ml` — with built-in exclusions for dispatch methods, decorators, ORM fields, migrations, and dependency-injection parameters. `--list-presets` shows them all
- **Pre-flight Risk Scanning** (`--check`): detects `eval`/`exec`, dynamic attribute access, and framework reflection points before you obfuscate
- **Reverse Stack-Trace Mapping** (`--unmap`): reverse obfuscated identifiers in a production stack trace, so you (or an AI coding assistant) can debug without un-obfuscating the shipped code
- **Build Provenance** (`--provenance-manifest`, v0.5.5): local JSON manifest of an obfuscation run — output file hashes, config hash, pyobfus version, mapping digest — for offline build provenance, no network calls

### 🔒 Pro Edition

The following advanced features are available with a Pro license:

- **String Encryption**
  - AES-256 encryption for strings
  - Runtime decryption with injected decoder
  - Automatic key generation

- **Anti-Debugging**
  - Debugger detection checks injected into functions
  - Multiple detection methods (sys.gettrace, sys.settrace)
  - Configurable behavior

- **Control Flow Flattening**
  - State machine transformation for if/else/elif
  - For/while loop flattening
  - Nested structure support
  - CLI: `--control-flow`

- **Dead Code Injection**
  - Insertion of unreachable code paths
  - Four strategies: after-return, false branches, opaque predicates, decoy functions
  - CLI: `--dead-code`

- **License Embedding**
  - Embed expiration dates: `--expire 2025-12-31`
  - Machine binding: `--bind-machine`
  - Run count limits: `--max-runs 100`
  - Offline verification - no external dependencies

- **Configuration Presets**
  - `--preset trial` - 30-day time-limited version
  - `--preset commercial` - Maximum protection with machine binding
  - `--preset library` - For pip-distributable libraries
  - `--preset maximum` - Highest security with all protections
  - `--list-presets` - View all presets

#### Patent-targeted mechanisms (CN 202610712171X, introduced v0.5.0)

Six mechanisms, available both as the `pyobfus_pro` API and — as of **v0.5.1** —
as opt-in `pyobfus` build flags (single-file / `--no-cross-file` mode):
`--selective-opacity`, `--seal-code`, `--vault`, `--scrub-traceback`,
`--fingerprint <buyer-id>`, `--expire-hard <date>`. **v0.5.3** adds
`--period <N>` (run-counter limit), `--opacity-config <opacity.toml>`
(pattern-driven L3 encryption by original qualname), and `--bind-device` /
`--bind-device-id <id>` (device-locked L3 encryption). **v0.5.4** extends
`--bind-device` to Runtime String Vault keys too — previously only the
Selective Opacity L3 layer was device-locked, so vault secrets decrypted on
any machine; now each vault key is independently re-derived at runtime from
the bound device.

- **Selective Opacity** — per-symbol protection layers (transparent / ai-readable / obfuscated / AES-256-GCM encrypted with lazy `__code__` materialization).
- **Forensic watermarking** — per-buyer deterministic key derivation for piracy traceback.
- **License binding combo** — device / expiry / run-count binding woven into the AES-GCM decryption path (no separate patchable license check).
- **`@seal_code`** — build-time bytecode integrity hash; runtime in-memory-patch detection.
- **`--scrub-traceback`** — production traceback encryption (RSA-2048 + AES-256-GCM); reverse error IDs with the new `pyobfus-unscrub` CLI.
- **Runtime String Vault** — encrypted KV namespace for runtime secrets with lazy per-entry decryption.

> Requires Python ≥ 3.9 as of v0.5.0 (3.8 dropped, EOL 2024-10).

See [ROADMAP.md](docs/ROADMAP.md) for the full feature timeline.

## Try Pro Features FREE

**Try all Pro features for 5 days - no registration or credit card required!**

```bash
# Start your free trial
pyobfus-trial start

# Check trial status
pyobfus-trial status

# Use Pro features during trial
pyobfus input.py -o output.py --level pro
```

**What's included in the trial:**
- Control flow flattening (`--control-flow`)
- AES-256 string encryption (`--string-encryption`)
- Anti-debugging protection (`--anti-debug`)
- Dead code injection (`--dead-code`)
- License embedding (`--expire`, `--bind-machine`, `--max-runs`)
- Configuration presets (`--preset trial/commercial/library/maximum`)
- Unlimited files and lines of code

After your trial, purchase a license to continue using Pro features.

> **The trial runs on the honor system.** It stores its state in an unsigned
> file in your home directory, and `pyobfus/trial.py` is readable Apache-2.0
> source — so it is a convenience control, not a security boundary, and we
> document it as such rather than claiming protection it cannot deliver. See
> [SECURITY.md](SECURITY.md#trust-boundary-the-pro-trial-is-not-a-security-boundary).
> Note that the **Community Edition has no file or line limits and needs no
> trial at all** — the trial gates only the Pro mechanisms.

## Purchase Professional Edition

**Pro Edition Features**:
- 🔀 Control Flow Flattening
- 🧩 Dead Code Injection
- 🔐 AES-256 String Encryption
- 📦 Import Obfuscation - runtime `importlib` imports with encrypted import strings
- 🛡️ Anti-Debugging Checks
- 📅 License Embedding - Expiration, machine binding, run limits
- ⚡ Configuration Presets - One-command setup
- 🔄 Lifetime Updates
- 💻 Up to 3 devices per license
- 📧 Priority Email Support

**Price**: $45.00 USD (one-time payment)

### How to Purchase

**Visit our purchase page**: **[pyobfus.github.io/purchase](https://zhurong2020.github.io/pyobfus/#purchase-professional-edition)** for detailed information and secure checkout.

**Quick purchase**: **[🚀 Buy Now](https://buy.stripe.com/00w4gr8ta9F78Fj8oI9k400)** - Direct checkout link (Instant delivery • 30-day money-back guarantee)

**3-Step Purchase Process**:

1. **Complete Secure Checkout** (Stripe)
   - Click the buy link above or visit the purchase page
   - Enter your email (for license delivery)
   - Complete payment securely via Stripe

2. **Receive License Key**
   - License key delivered to your email within minutes
   - Format: `PYOB-XXXX-XXXX-XXXX-XXXX`
   - **Check Spam/Junk folder** if not in inbox

3. **Activate License**
   ```bash
   pip install --upgrade pyobfus
   pyobfus-license register PYOB-XXXX-XXXX-XXXX-XXXX
   pyobfus-license status
   ```

4. **Start Using Pro Features**
   ```bash
   # Quick start with presets
   pyobfus src/ -o dist/ --preset commercial   # Maximum protection
   pyobfus src/ -o dist/ --preset trial        # 30-day trial version
   pyobfus src/ -o dist/ --preset library      # For pip distribution

   # Individual features
   pyobfus input.py -o output.py --string-encryption
   pyobfus input.py -o output.py --import-obfuscation
   pyobfus input.py -o output.py --anti-debug
   pyobfus input.py -o output.py --control-flow
   pyobfus input.py -o output.py --dead-code

   # License restrictions
   pyobfus src/ -o dist/ --expire 2025-12-31 --bind-machine --max-runs 100

   # All Pro features
   pyobfus input.py -o output.py --string-encryption --import-obfuscation --anti-debug --control-flow --dead-code
   ```

**Support**: If you encounter any issues, contact zhurong0525@gmail.com with your license key.

### Legal & Policies

By purchasing pyobfus Professional Edition, you agree to our:
- **[Terms of Service & EULA](docs/legal/TERMS_OF_SERVICE.md)** - License agreement and usage terms
- **[Refund Policy](docs/legal/REFUND_POLICY.md)** - 30-day money-back guarantee, no questions asked
- **[Privacy Policy](docs/legal/PRIVACY_POLICY.md)** - GDPR compliant, we protect your data

## Quick Start

### Installation

**From PyPI** (recommended):

```bash
pip install pyobfus
```

**From source** (for development):

```bash
git clone https://github.com/zhurong2020/pyobfus.git
cd pyobfus
pip install -e .
```

### Basic Usage

```bash
# Obfuscate a single file
pyobfus input.py -o output.py

# Obfuscate a directory (cross-file mode - default in v0.2.0+)
pyobfus src/ -o dist/

# Preview obfuscation without writing files (v0.2.0+)
pyobfus src/ -o dist/ --dry-run

# Legacy single-file mode (v0.2.0+)
pyobfus src/ -o dist/ --no-cross-file

# With configuration file
pyobfus src/ -o dist/ --config pyobfus.yaml

# Preserve parameter names for keyword arguments (v0.1.6+)
pyobfus src/ -o dist/ --preserve-param-names

# Verbose output with progress indicators (v0.2.0+)
pyobfus src/ -o dist/ --verbose
```

### Example

**Before obfuscation**:

```python
def calculate_risk(age, score):
    """Calculate risk factor."""
    risk_factor = 0.1
    if score > 100:
        risk_factor = 0.5
    return age * risk_factor

patient_age = 55
patient_score = 150
risk = calculate_risk(patient_age, patient_score)
print(f"Risk score: {risk}")
```

**After obfuscation**:

```python
def I0(I1, I2):
    I3 = 0.1
    if I2 > 100:
        I3 = 0.5
    return I1 * I3
I4 = 55
I5 = 150
I6 = I0(I4, I5)
print(f'Risk score: {I6}')
```

*Note: Variable names (I0, I1, etc.) may vary slightly depending on code structure, but functionality is preserved.*

## Configuration

### Quick Start with Templates

Generate a configuration template for your project type:

```bash
# For Django projects
pyobfus --init-config django

# For Flask projects
pyobfus --init-config flask

# For Python libraries
pyobfus --init-config library

# For general projects
pyobfus --init-config general
```

This creates a `pyobfus.yaml` file with sensible defaults for your project type.

### Validate Configuration

Check your configuration file for errors before use:

```bash
pyobfus --validate-config pyobfus.yaml
```

The validator checks for:
- YAML syntax errors
- Invalid configuration options
- Common typos (e.g., `exclude_pattern` -> `exclude_patterns`)
- Pro features used with community level

### Auto-Discovery

When you run `pyobfus` without `-c`, it automatically searches for:
1. `pyobfus.yaml`
2. `pyobfus.yml`
3. `.pyobfus.yaml`
4. `.pyobfus.yml`

### Manual Configuration

Create `pyobfus.yaml`:

```yaml
obfuscation:
  level: community
  exclude_patterns:
    - "test_*.py"
    - "**/tests/**"
    - "__init__.py"
  exclude_names:
    - "logger"
    - "config"
    - "main"
  remove_docstrings: true
  remove_comments: true
```

### exclude_names Behavior

The `exclude_names` option preserves specified names from being renamed during obfuscation:

```yaml
obfuscation:
  exclude_names:
    - MyPublicClass      # Name preserved, but strings inside are still encoded
    - exported_function  # Name preserved for external callers
```

**Important**: `exclude_names` only affects **name obfuscation**, not **string encoding**:

```python
# Original
SECRET_KEY = "admin-password-123"

# With exclude_names: [SECRET_KEY] and string_encoding: true
SECRET_KEY = _decode_str('YWRtaW4tcGFzc3dvcmQtMTIz')
# ✅ Name 'SECRET_KEY' is preserved
# ✅ String content is still encoded (Base64)
```

**Use cases**:
- Preserve names for public APIs that external code imports
- Keep class/function names for debugging while still protecting string content
- Maintain compatibility with external frameworks expecting specific names

### File Filtering

Exclude patterns support glob syntax:

- `test_*.py` - Exclude files starting with "test_"
- `**/tests/**` - Exclude all files in "tests" directories
- `**/__init__.py` - Exclude all `__init__.py` files
- `setup.py` - Exclude specific files

See `pyobfus.yaml.example` for more configuration examples.

## Architecture

pyobfus uses Python's `ast` module for syntax-aware transformations:

1. **Parser**: Parse Python source to AST
2. **Analyzer**: Build symbol table with scope analysis
3. **Transformers**: Apply obfuscation techniques (name mangling, string encoding, etc.)
4. **Generator**: Generate obfuscated Python code

This approach ensures:
- Syntactically correct output
- Proper handling of Python scoping rules
- Support for modern Python features (f-strings, walrus operator, etc.)

## Development

### Setup

```bash
git clone https://github.com/zhurong2020/pyobfus.git
cd pyobfus
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Testing

```bash
# Run unit tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=pyobfus --cov-report=html

# Run integration tests
pytest integration_tests/ -v
```

**Integration Testing Framework** (v0.1.6+): Test pyobfus on real-world code without uploading to PyPI. See [`INTEGRATION_TESTING.md`](docs/INTEGRATION_TESTING.md) for details.

### Code Quality

```bash
# Format code
black pyobfus/

# Type checking
mypy pyobfus/

# Linting
ruff check pyobfus/
```

## Use Cases

### Protecting Proprietary Algorithms

Obfuscate sensitive business logic before distributing Python applications.

### Educational Purposes

Demonstrate code protection concepts and obfuscation techniques.

### Intellectual Property Protection

Add an additional layer of protection for commercial Python software.

## Limitations

### Current Limitations

- **Keyword Arguments** (✅ Resolved in v0.1.6): By default, parameter names are obfuscated, which breaks keyword arguments. **Solution**: Use the `--preserve-param-names` flag to preserve parameter names while still obfuscating function bodies.

  Example:
  ```python
  # Before obfuscation
  def process(data_path, output_dir):
      temp_file = data_path + ".tmp"
      return temp_file

  result = process(data_path='./data', output_dir='./output')  # ✅ Works

  # After obfuscation (default behavior)
  def I0(I1, I2):
      I3 = I1 + ".tmp"
      return I3

  result = process(data_path='./data', output_dir='./output')  # ❌ TypeError!

  # After obfuscation (with --preserve-param-names)
  def I0(data_path, output_dir):
      I3 = data_path + ".tmp"
      return I3

  result = I0(data_path='./data', output_dir='./output')  # ✅ Works!
  ```

  **When to use `--preserve-param-names`**:
  - Public API functions/libraries where keyword arguments are used by clients
  - Functions with many parameters where keyword arguments improve readability
  - Code that relies heavily on keyword-only arguments (`def func(*, kwonly)`)

  **Trade-off**: Parameter names reveal some information about the function's interface, but function bodies and local variables are still fully obfuscated.

- **Cross-file imports**: ✅ Resolved in v0.2.0 with full cross-file obfuscation support
- **Dynamic code**: `eval()`, `exec()` with obfuscated code may require adjustments
- **Debugging**: Obfuscated code is harder to debug (by design)
- **Performance**: Some obfuscation techniques may impact runtime performance

### Recommendations

- **Test obfuscated code thoroughly** before deployment
- Keep original source in version control
- Use configuration files for reproducible builds
- For public APIs, use `--preserve-param-names` to maintain keyword argument compatibility
- Consider combining with other protection methods (compilation, etc.)

## Technical Details

- **Python Support**: 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- **Naming Scheme**: Index-based (I0, I1, I2...) - simple and effective
- **Architecture**: Modular transformer pipeline with two-phase cross-file obfuscation
- **Testing**: 1,000+ tests, 90% coverage, multi-OS CI/CD (Python 3.9-3.14 × Ubuntu / macOS / Windows)

## Frequently Asked Questions

### Is pyobfus Right for Me?

**Use pyobfus if you:**
- Need to protect proprietary algorithms before distributing Python applications
- Want a tool that "just works" without DLL conflicts or native dependencies
- Prefer transparent pricing without hidden trial limitations
- Support open-source software with optional paid features

### How do I obfuscate Python code?

```bash
# Install
pip install pyobfus

# Obfuscate a single file
pyobfus script.py -o script_obf.py

# Obfuscate an entire project
pyobfus src/ -o dist/

# Preview without writing files
pyobfus src/ -o dist/ --dry-run
```

### Will my code still work after obfuscation?

pyobfus is designed to preserve program behavior for supported Python syntax and
framework patterns, and its compatibility matrix is covered by automated tests.
Obfuscation is still a source transformation: run your own test suite and verify
the built artifact, especially when the project relies on dynamic imports,
reflection, or generated code.

### Does obfuscated code run slower?

Minimal impact:
- **Name mangling**: Zero runtime cost (just renamed identifiers)
- **String encoding** (Base64): ~0.1ms per string at startup
- **String encryption** (AES-256, Pro): ~0.5ms per string at startup

### Can I obfuscate Django/Flask projects?

Yes! Use our built-in templates:

```bash
# Django
pyobfus --init-config django

# Flask
pyobfus --init-config flask

# Then run obfuscation
pyobfus src/ -o dist/ -c pyobfus.yaml
```

### What Python versions are supported?

pyobfus supports **Python 3.9 through 3.14**. Build and test the obfuscated
artifact with the Python version used in production; cross-interpreter
portability can depend on syntax, dependencies, and enabled transformations.

### PyArmor vs pyobfus: Which should I choose?

| Feature | pyobfus | PyArmor |
|---------|---------|---------|
| **Price** | $45 (Pro) | $89 (Pro) |
| **Free tier** | Clear limits (5 files/1000 LOC) | Vague "trial" limitations |
| **Open source** | Yes (Core: Apache 2.0, Pro: Proprietary) | No |
| **Native dependencies** | None (pure Python output) | Requires runtime library |
| **Python 3.9-3.14 support** | Yes | Yes |

**Choose pyobfus if:** You want transparent pricing, open-source trust, and simpler deployment without native dependencies.

See our [detailed comparison](docs/COMPARISON.md) for more information.

### Can I use pyobfus alongside PyArmor or Nuitka?

Yes — and for many projects this is the most cost-effective approach. Use pyobfus as your always-on default layer (every module gets AST mangling + mapping for AI-debug compatibility), then stack PyArmor Pro's bytecode encryption or Nuitka's native compilation on the small set of modules that genuinely need stronger protection. See [Layered Deployment Strategy in COMPARISON.md](docs/COMPARISON.md#layered-deployment-strategy) for the full reasoning.

### What if obfuscation breaks my code?

1. **Use `--dry-run`** to preview changes before writing files
2. **Use `--preserve-param-names`** if you rely on keyword arguments
3. **Add exclusions** in `pyobfus.yaml` for names that must stay unchanged
4. **Report issues** on [GitHub](https://github.com/zhurong2020/pyobfus/issues) - we fix bugs quickly!

### Can obfuscated code be reversed?

Name mangling removes the original identifiers from the emitted source and
raises the cost of analysis, but it is not cryptographically irreversible: a
determined analyst may infer names and behavior from context. Keep the optional
mapping file private when you need reliable reverse mapping. For stronger
protection, use Pro features:
- **AES-256 encryption** for strings
- **Anti-debugging** checks to prevent analysis

### Security Note: String Encryption Limitations

**Important**: String encryption (AES-256) is designed as a **deterrent against casual reverse engineering**, not as cryptographic security.

Because obfuscated code must decrypt strings at runtime, the encryption key is necessarily embedded in the output. A determined attacker with access to the obfuscated code can:
1. Locate the embedded key
2. Extract and decrypt all strings

**This is a fundamental limitation of ALL client-side obfuscators** (including PyArmor, Nuitka, etc.) - true cryptographic security would require server-side decryption, which is impractical for most use cases.

**What string encryption DOES provide:**
- ✅ Prevents casual `strings` or `grep` searches from revealing sensitive text
- ✅ Increases effort required for reverse engineering
- ✅ Deters non-technical users from extracting information
- ✅ Adds a layer of protection combined with other techniques

**What string encryption does NOT provide:**
- ❌ Protection against determined reverse engineers
- ❌ Cryptographic security for secrets (use environment variables or secret management instead)
- ❌ DRM-level protection

**Recommendation**: For sensitive credentials (API keys, passwords), use environment variables or external secret management systems rather than embedding them in code.

### How is pyobfus different from Cython/Nuitka?

| Tool | Approach | Output |
|------|----------|--------|
| **pyobfus** | AST transformation | `.py` files (pure Python) |
| **Cython** | Compile to C | `.so`/`.pyd` (platform-specific) |
| **Nuitka** | Compile to executable | Binary (platform-specific) |

**Choose pyobfus if:** You need cross-platform `.py` files without compilation overhead.

## Documentation

### For Users
- **[Installation & Quick Start](#installation)** - Get started in minutes
- **[Configuration Guide](#configuration)** - YAML configuration and file filtering
- **[Examples](https://github.com/zhurong2020/pyobfus/tree/main/examples)** - Working code examples demonstrating features
- **[Use Cases](#use-cases)** - Real-world application scenarios

### For Developers
- **[Project Structure](https://github.com/zhurong2020/pyobfus/blob/main/docs/PROJECT_STRUCTURE.md)** - Codebase architecture and development workflow
- **[Contributing Guide](https://github.com/zhurong2020/pyobfus/blob/main/CONTRIBUTING.md)** - How to contribute code and documentation
- **[Development Roadmap](https://github.com/zhurong2020/pyobfus/blob/main/docs/ROADMAP.md)** - Planned features and timeline
- **[Changelog](https://github.com/zhurong2020/pyobfus/blob/main/CHANGELOG.md)** - Version history and release notes

### Community & Support
- **[GitHub Issues](https://github.com/zhurong2020/pyobfus/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/zhurong2020/pyobfus/discussions)** - Questions, ideas, and community help
- **[Security Policy](https://github.com/zhurong2020/pyobfus/blob/main/SECURITY.md)** - How to report security vulnerabilities

### Legal & License
- **Dual License Model** (see [`LICENSE-NOTICE.md`](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE-NOTICE.md)):
  - **pyobfus** (Core): [Apache 2.0](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE) - Free and open source
  - **pyobfus_pro** (Pro): [Proprietary](https://github.com/zhurong2020/pyobfus/blob/main/pyobfus_pro/LICENSE) - Requires paid license

## Support the Project

If you find pyobfus helpful, consider supporting its development:

[Buy Me A Coffee](https://www.buymeacoffee.com/zhurong052Q)

<a href="https://www.buymeacoffee.com/zhurong052Q" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

Your support helps maintain and improve pyobfus. Thank you!

## Citation

If you use pyobfus in academic work or want to reference it, please cite the archived release. The concept DOI below always resolves to the latest version:

**APA**

> Zhu, R. (2026). *pyobfus: An AST-based Python obfuscator with reverse stack-trace mapping for AI-assisted development*. Zenodo. https://doi.org/10.5281/zenodo.20846053

**BibTeX**

```bibtex
@software{zhu_pyobfus,
  author    = {Zhu, Rong},
  title     = {pyobfus: An AST-based Python obfuscator with reverse stack-trace mapping for AI-assisted development},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20846053},
  url       = {https://doi.org/10.5281/zenodo.20846053}
}
```

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff) (GitHub's "Cite this repository" widget reads it).

## Acknowledgments

- Inspired by [Opy](https://github.com/QQuick/Opy)'s AST-based approach
- Clean room implementation - no code copying
