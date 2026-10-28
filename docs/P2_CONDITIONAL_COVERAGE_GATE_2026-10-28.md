# Conditional coverage and Python 3.15 free-threaded gate

Decision date: 2026-10-28. This is a scope decision after P0 and the bounded
P1/P2 work; it does not mark any new feature or free-threaded support as
implemented.

| Candidate | Current evidence | Trigger for a product change |
|---|---|---|
| L3 methods/nested functions | Core 0.10.0 selects top-level functions; requested methods/nested functions are counted as skipped in the build report. The P1 offline application protected a top-level function and had no coverage blocker. | A minimized application where an algorithm must remain a method or nested function, with expected behavior and traceback mapping under missing/wrong/correct key. |
| Resource/Vault application key provider | The released application provider handles L3 keys. The P1 runtime-only target validated it. The existing Y-3 contract rejects `--bind-key-env` with Vault to avoid silently embedding a key. | A concrete offline delivery that needs Vault/resource content and application-managed keys together; define the key scope, rotation and startup order before altering the runtime contract. |
| Parameter renaming | Default preservation avoids keyword-call breakage; explicit renaming has known reflection and third-party call risks. | A named interface with callers and a measurable protection need; specify which parameters may change and prove keyword calls, decorators, serialization and traceback behavior. |
| Complex import cycles | Cross-file L3 refuses unproved module accesses; P0 added explicit conservative preservation for recognized Core cases. | A minimal failing cycle from an actual delivery, with original/output behavior and import order. Fix correctness before broadening encryption. |

No candidate above has the required new blocking case from the P1 evidence.
The next implementation should follow the first real case, rather than adding
all four at once. Existing users can still supply a case through an issue or
support channel; no outbound message is required for this gate.

## Free-threaded Python 3.15

The WSL `python3.15` installed here reports `Py_GIL_DISABLED=0`; Windows
`py -0p` lists no 3.15 free-threaded interpreter. Ordinary 3.15 CI does not
establish free-threaded compatibility. An isolated attempt to obtain `uv`
for a standalone 3.15t interpreter was stopped when its 17.3 MiB wheel was
downloading at about 6.7 KiB/s. No repository dependency or CI workflow was
changed.

When a 3.15t interpreter is available, verify
`sysconfig.get_config_var("Py_GIL_DISABLED") == 1` and
`sys._is_gil_enabled() is False`, then run a bounded build/execute/traceback
smoke on Core and L3 runtime. Add a two-thread repeated import/key-provider
case and check that no extension silently re-enables the GIL. Record OS,
interpreter version, packages and exact outcomes. Only expand the matrix or
advertise support after that evidence. This distinction follows the
[Python free-threading guide](https://docs.python.org/3.15/howto/free-threading-python.html).
