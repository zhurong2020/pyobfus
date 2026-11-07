"""Local pre-commit inspection for pyobfus private material (Community)."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import NoReturn, Optional, Sequence

from pyobfus.core.delivery_check import (
    _MAX_JSON_BYTES,
    _Entry,
    _is_mapping,
    _is_private_key,
)

# PEM headers beyond this head (including leading whitespace) are not detected.
_PRIVATE_KEY_HEAD_BYTES = 64 * 1024


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        # Do not echo arbitrary argument values in error messages.
        raise ValueError("Invalid arguments; use --help for usage")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Inspect filenames; missing and nonregular files are skipped."""
    args = list(sys.argv[1:] if argv is None else argv)
    options = args[: args.index("--")] if "--" in args else args
    json_output = "--json" in options
    parser = _Parser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print a versioned JSON result")
    parser.add_argument("files", nargs="*", metavar="FILE")
    findings = []
    errors = []
    try:
        parsed = parser.parse_args(args)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        for name in parsed.files:
            path = Path(name)
            try:
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    continue
                if not stat.S_ISREG(info.st_mode):
                    continue
                # O_NOFOLLOW prevents a final-component link swap on platforms
                # that support it; fstat also rejects replaced nonregular paths.
                flags = (
                    os.O_RDONLY
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0)
                    | getattr(os, "O_BINARY", 0)
                )
                try:
                    fd = os.open(path, flags)
                except FileNotFoundError:
                    continue
                with os.fdopen(fd, "rb") as stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode):
                        continue
                    head = stream.read(_PRIVATE_KEY_HEAD_BYTES)
                    mapping = False
                    if name.endswith(".json") and info.st_size <= _MAX_JSON_BYTES:
                        stream.seek(0)
                        data = stream.read(_MAX_JSON_BYTES + 1)
                        if len(data) <= _MAX_JSON_BYTES:
                            mapping = _is_mapping(_Entry(name, data))
                entry = _Entry(name, head)
                for kind, detected, message in (
                    (
                        "mapping",
                        mapping,
                        "pyobfus mapping file (keep it private, do not commit)",
                    ),
                    ("private_key", _is_private_key(entry), "private key material"),
                ):
                    if detected:
                        findings.append({"path": name, "kind": kind, "message": message})
            except (OSError, ValueError):
                # Exceptions may contain data supplied by a parser or OS. Only
                # report the supplied filename and a fixed diagnostic.
                errors.append(f"{name}: unable to read file")
    status = "error" if errors else "findings" if findings else "clean"
    hint = (
        "Inspection incomplete. Correct arguments or file permissions and rerun."
        if errors
        else (
            "Keep the reported material private; remove it from the commit and rerun."
            if findings
            else "No known private material found; also use a general secret scanner."
        )
    )
    if json_output:
        print(json.dumps({"version": 1, "status": status, "findings": findings, "ai_hint": hint}))
    else:
        for finding in findings:
            print(f"{finding['path']}: {finding['message']}")
        for error in errors:
            print(error, file=sys.stderr)
    return 2 if errors else 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
