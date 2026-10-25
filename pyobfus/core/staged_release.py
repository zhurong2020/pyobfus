"""Private staging and no-clobber publication for new artifact directories.

Metadata is linked first and the completed application directory is renamed
last. This is not a crash-durable multi-path transaction. A private ownership
journal permits recovery of metadata left by an interrupted build; recovery
never deletes an application directory or a file no longer owned by staging.
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable


def validate_destinations(input_dir: Path, output: Path, metadata: Iterable[Path]) -> None:
    """Require distinct new paths, existing parents, one filesystem, no source overlap."""
    source = input_dir.resolve()
    destinations = [output.absolute(), *(p.absolute() for p in metadata)]
    resolved = [p.resolve() for p in destinations]
    if len(set(resolved)) != len(resolved):
        raise ValueError("Output and metadata destinations must be distinct")
    for path, real in zip(destinations, resolved):
        if os.path.lexists(path):
            raise ValueError("Crossfile opacity requires entirely new output and metadata paths")
        if not path.parent.is_dir():
            raise ValueError("Create output and metadata parent directories before building")
        if real == source or source in real.parents or real in source.parents:
            raise ValueError("Crossfile opacity destinations must be outside the source tree")
        for other in resolved:
            if real != other and real in other.parents:
                raise ValueError("Metadata must be outside the delivered application directory")
    if len({p.parent.stat().st_dev for p in destinations}) != 1:
        raise ValueError("Crossfile opacity output and metadata must use the same filesystem")
    if not (sys.platform.startswith("linux") or sys.platform == "darwin" or os.name == "nt"):
        raise ValueError("No-clobber directory publication is unsupported on this platform")


def _private_directory(path: Path) -> None:
    if os.name != "nt":
        path.chmod(0o700)
        return
    # tempfile's default DACL may inherit permissions from a shared parent.
    # Restrict to the current token's SID; fail before any sensitive data exists.
    identity = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        check=True,
        capture_output=True,
        text=True,
    )
    import csv

    sid = next(csv.reader([identity.stdout.strip()]))[1]
    subprocess.run(
        ["icacls", str(path), "/inheritance:r", "/grant:r", f"*{sid}:(OI)(CI)F"],
        check=True,
        capture_output=True,
    )


def _rename_new(source: Path, destination: Path) -> None:
    """Atomic directory rename that refuses even an existing empty directory."""
    if os.name == "nt":
        os.rename(source, destination)  # Windows refuses existing destinations.
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux"):
        result = libc.renameat2(
            -100, os.fsencode(source), -100, os.fsencode(destination), 1  # RENAME_NOREPLACE
        )
    elif sys.platform == "darwin":
        result = libc.renamex_np(os.fsencode(source), os.fsencode(destination), 4)  # RENAME_EXCL
    else:
        raise OSError("No no-clobber rename available")
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


class StagedRelease:
    """Own one staging tree; commit metadata first and the new directory last."""

    def __init__(self, output: Path, metadata: Dict[str, Path], build_id: str):
        self.output = output.absolute()
        self.metadata = {key: path.absolute() for key, path in metadata.items()}
        self.root = Path(tempfile.mkdtemp(prefix=".pyobfus-release-", dir=output.parent))
        try:
            _private_directory(self.root)
        except BaseException:
            self.root.rmdir()
            raise
        self.app = self.root / "app"
        self.app.mkdir()
        self.journal = {
            "format": "pyobfus-staging-ownership",
            "build_id": build_id,
            "output": str(self.output),
            "metadata": {key: str(path) for key, path in self.metadata.items()},
        }
        (self.root / "ownership.json").write_text(json.dumps(self.journal), encoding="utf-8")

    def __enter__(self) -> StagedRelease:
        return self

    def commit(self) -> None:
        for key, destination in self.metadata.items():
            staged = self.root / key
            staged.chmod(0o600)
            os.link(staged, destination)  # exclusive; no overwrite on a raced path
        _rename_new(self.app, self.output)

    def __exit__(self, *exc: object) -> None:
        recover_staging(self.root)


def recover_staging(root: Path) -> None:
    """Recover a known private stage using inode ownership, never names alone.

    An already published directory means its metadata must remain. Otherwise
    remove only metadata still hard-linked to its private staged inode. A crash
    before link creation, or a destination replaced since then, is safe too.
    The caller must supply its own trusted staging directory, not untrusted JSON.
    """
    journal = json.loads((root / "ownership.json").read_text(encoding="utf-8"))
    if journal.get("format") != "pyobfus-staging-ownership":
        raise ValueError("Not a pyobfus ownership journal")
    output = Path(journal["output"])
    # A competing directory is not proof that our application was committed.
    committed = not (root / "app").exists()
    if committed:
        manifest = output / ".pyobfus-release.json"
        try:
            committed = (
                json.loads(manifest.read_text(encoding="utf-8"))["build_id"] == journal["build_id"]
            )
        except (OSError, ValueError, KeyError, TypeError):
            # Ambiguous post-commit state: retain private evidence for manual recovery.
            raise ValueError("Published application identity unavailable; keep staging") from None
    if not committed:
        for key, path in journal["metadata"].items():
            if Path(key).name != key:
                raise ValueError("Invalid staging metadata key")
            staged, destination = root / key, Path(path)
            if staged.is_file() and destination.is_file() and not destination.is_symlink():
                if os.path.samefile(staged, destination):
                    destination.unlink()
    shutil.rmtree(root)
