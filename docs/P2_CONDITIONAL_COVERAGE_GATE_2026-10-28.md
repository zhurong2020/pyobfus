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

The original WSL `python3.15` reports `Py_GIL_DISABLED=0`, and Windows
`py -0p` lists no 3.15 free-threaded interpreter. A matching Linux 3.15.2
no-GIL build was subsequently obtained into `/tmp` and verified with the
GIL disabled. The bounded Core, runtime, traceback and two-thread provider
results are recorded in [the 3.15t validation](PYTHON315_FREETHREADING_VALIDATION_2026-10-28.md).
Cross-file L3 still rejects free-threaded builds by design; do not advertise
it as supported. A clean public-wheel target and another OS remain unverified.
Ordinary 3.15 CI cannot substitute for these distinct checks. This follows the
[Python free-threading guide](https://docs.python.org/3.15/howto/free-threading-python.html).
