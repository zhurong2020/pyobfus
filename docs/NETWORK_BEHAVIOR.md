# Network behavior: what pyobfus sends, and when

pyobfus does not upload your source code and has no telemetry. Obfuscating,
previewing (`--dry-run`), verifying syntax, saving and reading mappings, and
reversing tracebacks (`--unmap`) all run without a network connection.

There are exactly three places where the code makes a network request. Each
one is listed below with what it sends and how to avoid it. This page was
checked against the source of pyobfus 0.6.1 on 2026-10-11; you can repeat the
check yourself (see [How to verify this](#how-to-verify-this)).

| When | Edition | Sends to | What is sent | How to avoid it |
|---|---|---|---|---|
| `pyobfus --check` finds dependency files | Community | `pypi.org` | Dependency **names** read from `requirements*.txt` / `pyproject.toml` | `--check --offline` |
| `pyobfus-trial start --email <address>` | Pro trial | pyobfus licence server | The email address and a device ID | Run `pyobfus-trial start` without `--email` |
| Pro licence verification and device release | Pro | pyobfus licence server | The licence key and a device ID | `pyobfus-license register <KEY> --no-verify` |

## 1. Dependency check in `--check` (Community)

When `pyobfus --check` finds `requirements*.txt` or `pyproject.toml`, it asks
PyPI whether each listed dependency name exists, to warn about names that
cannot be installed. One `GET https://pypi.org/pypi/<name>/json` request is
made per dependency name. No source code, file paths or project names are sent.

- CLI: the lookup is **on by default**. Pass `--offline` to skip it.
- MCP server (`pyobfus-mcp`): the lookup is **off by default**. An agent has to
  pass `verify_dependencies_online=True` to turn it on.
- If PyPI cannot be reached, `--check` adds an informational finding saying
  how many dependencies could not be verified, and nothing else changes.

## 2. Trial registration with `--email` (Pro trial)

`pyobfus-trial start --email you@example.com` registers the five-day Pro
trial with the licence server, which de-duplicates trials per email address.
It sends the email address and a device ID. Without `--email`, the trial is
recorded locally only and nothing is sent. If the server cannot be reached,
the `--email` path falls back to a local trial.

## 3. Pro licence verification (Pro)

A Pro build checks the licence key with the licence server. The request
contains the licence key and a device ID: a random value generated once and
stored in `~/.pyobfus/device_id`, not a hardware fingerprint. A successful
check is cached for three days, so most builds make no request. Releasing a
device slot (`pyobfus-license deactivate`) sends the same two fields.

For machines that must stay offline, register the key without contacting the
server:

```bash
pyobfus-license register <KEY> --no-verify
```

See the [licence activation guide](LICENSE_ACTIVATION_GUIDE.md) for details.

## What never goes over the network

- Your source code, obfuscated output, file names or directory layout.
- Mapping files. The mapping stays with you and is only read locally by `--unmap`.
- Usage statistics, crash reports or analytics. There is no telemetry.

Generated code does not contact anything either. Community output is ordinary
Python. Runtime-backed Pro artifacts depend on `pyobfus-runtime`, which makes
no network requests; expiry and device policies are checked locally.

The VS Code extension runs the `pyobfus` CLI on your machine and does not send
code anywhere. The Marketplace and Open VSX handle extension installs and
updates as for any other extension.

## How to verify this

All outgoing requests use Python's `urllib.request`. To list every call site
in an installed copy:

```bash
python - <<'EOF'
import pathlib, pyobfus
root = pathlib.Path(pyobfus.__file__).parent.parent
for pkg in ("pyobfus", "pyobfus_pro", "pyobfus_runtime"):
    for path in sorted((root / pkg).rglob("*.py")):
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "urlopen(" in line:
                print(f"{path.relative_to(root)}:{no}: {line.strip()}")
EOF
```

On 0.6.1 this prints the three modules above: `pyobfus/core/dependency_advisory.py`,
`pyobfus/trial.py` and `pyobfus_pro/license.py`. `pyobfus_runtime` is a separate
package; if it is installed in the same environment, the script checks it too.
For a runtime check, run a build with outbound traffic blocked (for example in
a container started with `--network none`) and with `--check --offline`.
