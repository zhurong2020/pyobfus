"""Module entry point so ``python -m pyobfus`` runs the CLI.

Equivalent to the ``pyobfus`` console script, but always resolvable via the
current interpreter without depending on the console script being on PATH.
This is what tooling (e.g. the pyobfus-mcp ``protect_project`` orchestration
tool) uses to invoke obfuscation in a subprocess reliably.
"""

from pyobfus.cli import main

if __name__ == "__main__":
    main()
