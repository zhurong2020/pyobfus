"""``pyobfus unscrub`` -- developer-side decrypt of P2-10 error IDs.

Customers report opaque error IDs of the form ``PYOBFUS-ERR:eyJhbGc...``
(produced by :func:`pyobfus_pro.runtime.install_scrub_excepthook`).
This CLI takes such an ID + the developer-retained private key and prints
the original traceback to stdout.

Usage::

    pyobfus-unscrub --key pyobfus.scrub.key.pem 'PYOBFUS-ERR:eyJhbGc...'
    pyobfus-unscrub --key pyobfus.scrub.key.pem --prefix PYOBFUS-ERR \\
                    'PYOBFUS-ERR:eyJhbGc...'
    pyobfus-unscrub --key key.pem --error-id-file id.txt
    cat id.txt | pyobfus-unscrub --key key.pem -

Exit codes:
    0 -- decryption succeeded; traceback printed to stdout
    1 -- decryption failed (wrong key, malformed ID, missing prefix)
    2 -- argument-parsing error or filesystem failure

The CLI is a thin wrapper around :func:`pyobfus_pro.runtime.unscrub_error_id`;
the cryptographic logic lives in the runtime module so build / runtime / dev
all share a single implementation (family-rule discipline, see
PATENT_NOTES.md P2-1 W3-B finding #6).

Patent-gated. See PATENT_NOTES.md and docs/P2-10_DESIGN.md.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from pyobfus_pro.runtime.scrub import ScrubError, unscrub_error_id

_PROG_NAME = "pyobfus-unscrub"
_EXIT_OK = 0
_EXIT_DECRYPT_FAILED = 1
_EXIT_USAGE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROG_NAME,
        description=(
            "Decrypt a pyobfus --scrub-traceback error ID back to the "
            "original Python traceback. Requires the private key sidecar "
            "from build time."
        ),
        epilog=(
            "Pass '-' as the error_id positional to read the ID from stdin. "
            "Pass --error-id-file to read from a file."
        ),
    )
    parser.add_argument(
        "error_id",
        nargs="?",
        help=(
            "The opaque error ID to decrypt (e.g. 'PYOBFUS-ERR:...'). Pass "
            "'-' to read from stdin. Mutually exclusive with --error-id-file."
        ),
    )
    parser.add_argument(
        "--key",
        "-k",
        required=True,
        type=Path,
        help=(
            "Path to the developer-retained private key PEM file (e.g. "
            "pyobfus.scrub.key.pem from build time)."
        ),
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help=(
            "If specified, only IDs with this exact prefix are accepted. "
            "Default: any prefix is accepted (or none)."
        ),
    )
    parser.add_argument(
        "--error-id-file",
        type=Path,
        default=None,
        help=(
            "Read the error ID from this file. Mutually exclusive with "
            "the positional error_id argument."
        ),
    )
    return parser


def _resolve_error_id(args: argparse.Namespace) -> str:
    """Return the error ID string from positional / --error-id-file / stdin.

    Raises:
        SystemExit: with _EXIT_USAGE on conflicting / missing inputs.
    """
    if args.error_id and args.error_id_file:
        print(
            f"{_PROG_NAME}: error: positional error_id and --error-id-file "
            f"are mutually exclusive",
            file=sys.stderr,
        )
        raise SystemExit(_EXIT_USAGE)

    if args.error_id_file is not None:
        try:
            error_id_file = cast(Path, args.error_id_file)
            return error_id_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            print(f"{_PROG_NAME}: error: cannot read --error-id-file: {exc}", file=sys.stderr)
            raise SystemExit(_EXIT_USAGE) from exc

    if args.error_id == "-":
        return sys.stdin.read().strip()

    if args.error_id is None:
        print(
            f"{_PROG_NAME}: error: error_id is required (or use " f"--error-id-file)",
            file=sys.stderr,
        )
        raise SystemExit(_EXIT_USAGE)

    return cast(str, args.error_id).strip()


def _read_private_key(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        print(f"{_PROG_NAME}: error: cannot read --key: {exc}", file=sys.stderr)
        raise SystemExit(_EXIT_USAGE) from exc


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code.

    Accepts ``argv`` for testability; defaults to ``sys.argv[1:]`` when None.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    error_id = _resolve_error_id(args)
    private_key_pem = _read_private_key(args.key)

    if not error_id:
        print(f"{_PROG_NAME}: error: empty error ID", file=sys.stderr)
        return _EXIT_USAGE

    try:
        traceback_text = unscrub_error_id(error_id, private_key_pem, prefix=args.prefix)
    except ScrubError as exc:
        print(f"{_PROG_NAME}: decrypt failed: {exc}", file=sys.stderr)
        return _EXIT_DECRYPT_FAILED

    sys.stdout.write(traceback_text)
    if not traceback_text.endswith("\n"):
        sys.stdout.write("\n")
    return _EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
