# Dogfood canary fixture

A small, deterministic project that the self-dogfooding lanes obfuscate and
execute (see `docs/SELF_DOGFOODING_BEST_PRACTICES.md`, Lane B/C/D). It exercises
cross-file imports, `__all__` re-export, a package entry point, and a plain
computation whose result is stable, so the lanes can compare *semantic outcomes*
(the obfuscated app still prints the same number) rather than byte-diffing
naturally varying output.

Running `python app.py` prints `25`. Keep it deterministic: no clock, no random,
no I/O, no environment reads.
