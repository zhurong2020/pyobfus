"""Build-pass AST transformer for --scrub-traceback.

Two responsibilities, deliberately split:

- :func:`load_or_generate_keypair` -- filesystem IO. Reads or creates a
  private-key sidecar file (default ``pyobfus.scrub.key.pem``) and returns
  the matching public key in PEM. The developer keeps the sidecar; it
  never ships in the obfuscated artifact.

- :func:`transform_module` -- pure AST. Takes a source string and a public
  key (bytes) and injects three statements after any leading imports:

      from pyobfus_pro.runtime import install_scrub_excepthook
      _PYOBFUS_SCRUB_PUBLIC_KEY = b"<pem>"
      install_scrub_excepthook(_PYOBFUS_SCRUB_PUBLIC_KEY, prefix="<...>")

The split lets unit tests exercise the transform without touching the
filesystem; the file helper has its own (small) test surface.

Idempotent: if the marker constant ``_PYOBFUS_SCRUB_PUBLIC_KEY`` is
already present at module level, the source is returned unchanged.

Patent-gated. See ../runtime/scrub.py for the runtime side and
docs/P2-10_DESIGN.md for the threat model.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization

from pyobfus_pro.runtime.scrub import generate_keypair

_RUNTIME_MODULE = "pyobfus_pro.runtime"
_INSTALL_FUNC = "install_scrub_excepthook"
_PUBLIC_KEY_CONSTANT = "_PYOBFUS_SCRUB_PUBLIC_KEY"
_DEFAULT_PREFIX = "PYOBFUS-ERR"
_DEFAULT_KEY_PATH = "pyobfus.scrub.key.pem"


class ScrubBuildError(RuntimeError):
    """Raised on build-time failures (key file conflict, malformed key, IO)."""


def load_or_generate_keypair(
    private_key_path: str | os.PathLike,
    *,
    regenerate: bool = False,
    key_size: int = 2048,
) -> tuple[bytes, bytes]:
    """Load an existing keypair from disk or generate a fresh one.

    Args:
        private_key_path: Filesystem path. If the file exists and
            ``regenerate=False``, the key is loaded; otherwise a new
            keypair is generated and the private half is written here.
        regenerate: When True, overwrite an existing key file. **Use with
            care**: in-flight error IDs from past builds become unrecoverable.
        key_size: RSA modulus size for new keys (ignored when loading).

    Returns:
        ``(private_pem, public_pem)`` -- bytes.

    Raises:
        ScrubBuildError: when reading or writing fails, or when an existing
            file is not a valid PEM.
    """
    path = Path(private_key_path)

    if path.exists() and not regenerate:
        try:
            private_pem = path.read_bytes()
        except OSError as exc:
            raise ScrubBuildError(f"unable to read private key {path}: {exc}") from exc
        try:
            private_key = serialization.load_pem_private_key(private_pem, password=None)
        except (ValueError, TypeError) as exc:
            raise ScrubBuildError(f"private key file {path} is not valid PEM: {exc}") from exc
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return private_pem, public_pem

    private_pem, public_pem = generate_keypair(key_size=key_size)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(private_pem)
    except OSError as exc:
        raise ScrubBuildError(f"unable to write private key to {path}: {exc}") from exc

    # Restrict permissions where the OS supports it. Non-fatal on Windows.
    try:
        os.chmod(path, 0o600)
    except (OSError, NotImplementedError):
        pass

    return private_pem, public_pem


def transform_module(
    source_code: str,
    public_key_pem: bytes,
    *,
    prefix: str = _DEFAULT_PREFIX,
    filename: str = "<scrub-pass>",
) -> str:
    """Inject ``install_scrub_excepthook`` into a module's source.

    Args:
        source_code: Python source text.
        public_key_pem: PEM-encoded RSA public key. Use
            :func:`load_or_generate_keypair` to obtain.
        prefix: Identifier prepended to error IDs at runtime
            (e.g. ``"PYOBFUS-ERR"``).
        filename: Used for compile() / parse() error messages.

    Returns:
        Transformed source. If the module already contains the marker
        constant ``_PYOBFUS_SCRUB_PUBLIC_KEY`` at top level, the source is
        returned unchanged (idempotent).

    Raises:
        SyntaxError: when ``source_code`` is not valid Python.
    """
    tree = ast.parse(source_code, filename)

    if _already_transformed(tree):
        return source_code

    # See module docstring for the three injected statements.
    import_stmt = ast.ImportFrom(
        module=_RUNTIME_MODULE,
        names=[ast.alias(name=_INSTALL_FUNC)],
        level=0,
    )
    key_assign = ast.Assign(
        targets=[ast.Name(id=_PUBLIC_KEY_CONSTANT, ctx=ast.Store())],
        value=ast.Constant(value=public_key_pem),
    )
    install_call = ast.Expr(
        value=ast.Call(
            func=ast.Name(id=_INSTALL_FUNC, ctx=ast.Load()),
            args=[ast.Name(id=_PUBLIC_KEY_CONSTANT, ctx=ast.Load())],
            keywords=[ast.keyword(arg="prefix", value=ast.Constant(value=prefix))],
        )
    )

    insert_at = 0
    for i, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            insert_at = i + 1
        else:
            break

    tree.body[insert_at:insert_at] = [import_stmt, key_assign, install_call]
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def _already_transformed(tree: ast.Module) -> bool:
    """Detect a previous transform via the marker constant at module level."""
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == _PUBLIC_KEY_CONSTANT:
                    return True
    return False
