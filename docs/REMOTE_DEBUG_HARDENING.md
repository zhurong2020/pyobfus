# Hardening against Python 3.14 remote debugging (PEP 768)

Python 3.14 ships a built-in **remote debugging interface**
([PEP 768](https://peps.python.org/pep-0768/)). It lets an external process
attach to a running interpreter and schedule Python code inside it. This is a
great debugging feature — but for a *protected* deployment it is another way to
reach the code you obfuscated, and it is **not** something an obfuscator can
close.

`pyobfus --check` raises an informational **compatibility advisory** when both
of these are true:

- the effective build requests **anti-debug protection** (the `--anti-debug`
  Pro feature, or a protection preset such as `commercial` / `maximum` /
  `trial` that enables it), **and**
- the deployment **targets Python 3.14+** — either because your config declares
  `requires_python_min: "3.14"` (or higher), or because you run the scan on a
  3.14+ interpreter.

The advisory is severity `info`; it never changes the scan's exit code.

## Why pyobfus cannot turn this off for you

pyobfus's runtime anti-debug checks (`sys.gettrace`, TracerPid on Linux,
`IsDebuggerPresent` on Windows) detect *some* attached debuggers from inside
your process. PEP 768's interface is different: it is controlled by the
**interpreter at startup**, before your code runs, so no amount of injected
Python can disable it after the fact. Treat this as a deployment-configuration
step, not an obfuscation feature.

Attaching a remote debugger also normally requires OS-level privileges (the same
user, or a process permitted to use `PTRACE`-style attachment), so this is
defense-in-depth for a hardened deployment, not a claim that any 3.14 process is
trivially exploitable.

## How to disable it

Pick whichever fits how the protected process is launched. Any one is enough.

**Per-invocation flag:**

```bash
python -X disable_remote_debug your_app.py
```

**Environment variable** (useful for containers, systemd units, CI):

```bash
export PYTHON_DISABLE_REMOTE_DEBUG=1
python your_app.py
```

**Build-time**, if you control the interpreter you ship:

```bash
# Configure CPython without the remote debugging interface at all
./configure --without-remote-debug
```

## Verifying

On Python 3.14+, confirm the interface is off in the process you actually ship:

```python
import sys
# sys.remote_exec / the remote debugging attach path should be unavailable
# when disabled at startup. Check your interpreter's 3.14 release notes for the
# exact introspection surface on your platform.
print(sys.version_info)
```

See the CPython
[remote debugging how-to](https://docs.python.org/3.14/howto/remote_debugging.html)
for the authoritative, platform-specific details.

## What this advisory is *not*

- It does **not** mean pyobfus disabled remote debugging — it can't; you disable
  it at interpreter startup.
- It does **not** claim your app is exploitable as-is. Attachment normally needs
  OS privileges.
- It is **not** a substitute for the rest of your deployment hardening (least
  privilege, container isolation, not shipping source your threat model can't
  afford to expose).
