"""Slice D of the multi-module L3 + application-key design: debugging and the
shareable report.

Two Community-side capabilities (local debugging is never paywalled):

1. A **dedicated encrypted-code frame identity**. Each build has an opaque,
   key-free ``artifact_id``; every encrypted function's code object is stamped
   with ``co_filename = "<pyobfus-l3:<artifact_id>:<relative_file>>"``. The angle
   brackets keep it from matching a real ``.py`` path, so ``linecache`` never
   shows a stub's source. A traceback from an encrypted function therefore
   carries a frame the restorer can match *exactly* -- no deployment-root voting
   and no short-path fallback.

2. A **name-only restorer** for those frames (:func:`restore_l3_names`) plus a
   **counts-only shareable report** (:func:`build_opacity_report`). The restorer
   recovers the original function *name* from a private ``encrypted_code`` table;
   it never invents an original line number, because the encrypted code object's
   line table is the renamed build text, not the original source. Unrecognized
   ``<pyobfus-l3:...>`` frames (wrong build id, unknown file, unknown name) are
   left untouched -- the table is matched exactly, nothing is guessed.

The private ``encrypted_code`` table and ``opacity_plan`` live in the build's
private mapping, not in the shareable report. A reader needs at least
:data:`L3_UNMAP_MIN_CORE_VERSION` to resolve these frames.
"""

from __future__ import annotations

import re
import sys
import sysconfig
from collections import Counter
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

# A reader older than this does not understand the encrypted-code frame table.
L3_UNMAP_MIN_CORE_VERSION = "0.10.0"

_L3_PREFIX = "<pyobfus-l3:"
# "<pyobfus-l3:<artifact_id>:<relative_file>>" -- artifact_id has no colon; the
# relative file may contain colons (Windows drive) so it is matched greedily up
# to the closing ">".
_L3_CO_FILENAME = re.compile(r"^<pyobfus-l3:(?P<artifact>[^:>]+):(?P<file>.+)>$")

_FRAME = re.compile(
    r'^(?P<indent>[ \t]*)File "(?P<path>[^"\r\n]+)", line (?P<line>[0-9]+), in (?P<name>[^\r\n]+)$'
)

# ``encrypted_code`` table: co_filename -> {final_name: original_name}.
EncryptedCodeTable = Dict[str, Dict[str, str]]


def l3_co_filename(artifact_id: str, relative_file: str) -> str:
    """Build the dedicated co_filename for an encrypted module's code objects."""
    if ":" in artifact_id or ">" in artifact_id:
        raise ValueError("artifact_id must not contain ':' or '>'")
    return f"{_L3_PREFIX}{artifact_id}:{relative_file}>"


def parse_l3_co_filename(path: str) -> Optional[Tuple[str, str]]:
    """Return ``(artifact_id, relative_file)`` for a dedicated frame path, else None."""
    match = _L3_CO_FILENAME.match(path)
    if match is None:
        return None
    return match["artifact"], match["file"]


def build_encrypted_code_table(
    entries: Iterable[Tuple[str, str, str]],
) -> EncryptedCodeTable:
    """Assemble the ``encrypted_code`` table from ``(co_filename, final, original)``.

    Raises on a conflicting original name for the same ``(co_filename, final)``,
    which would make restoration ambiguous.
    """
    table: EncryptedCodeTable = {}
    for co_filename, final_name, original_name in entries:
        bucket = table.setdefault(co_filename, {})
        if final_name in bucket and bucket[final_name] != original_name:
            raise ValueError(f"conflicting original name for {final_name!r} in {co_filename!r}")
        bucket[final_name] = original_name
    return table


def restore_l3_names(trace: str, table: EncryptedCodeTable) -> Dict[str, object]:
    """Restore original function names in encrypted-code frames of a traceback.

    Only ``<pyobfus-l3:...>`` frames are touched, and only when the build id,
    file and final name all match ``table`` exactly. The reported line is the
    encrypted code's line, never a reconstructed original line, so each restored
    frame is marked ``original_line: None`` with ``status: "name_only"``. Every
    other line (plain frames, messages, excerpts) is returned verbatim; compose
    this with the ordinary name/line restorer for mixed traces.
    """
    out_lines: List[str] = []
    frames: List[Dict[str, object]] = []
    for text in trace.splitlines(keepends=True):
        body = text.rstrip("\r\n")
        ending = text[len(body) :]
        match = _FRAME.fullmatch(body)
        if match is None or not match["path"].startswith(_L3_PREFIX):
            out_lines.append(text)
            continue

        path = match["path"]
        final_name = match["name"]
        original = table.get(path, {}).get(final_name)
        if original is None:
            # A dedicated frame we cannot match exactly: leave it untouched.
            frames.append(
                {
                    "file": path,
                    "name": final_name,
                    "status": "unmatched_l3",
                    "original_line": None,
                }
            )
            out_lines.append(text)
            continue

        out_lines.append(
            f'{match["indent"]}File "{path}", line {match["line"]}, in {original}{ending}'
        )
        frames.append(
            {
                "file": path,
                "name": original,
                "obfuscated_name": final_name,
                "status": "name_only",
                "original_line": None,
            }
        )

    note = (
        "Encrypted-function frames restore the original name only; their line "
        "numbers refer to the encrypted build text, not the original source, so "
        "no original line is reported. Unmatched <pyobfus-l3:...> frames (a "
        "different build id, file, or name) are left unchanged."
    )
    return {"restored_trace": "".join(out_lines), "frames": frames, "note": note}


def interpreter_tuple() -> Dict[str, object]:
    """The CPython identity an L3 artifact is bound to (implementation/minor/GIL).

    Recorded in the shareable report; the emitted runtime guard (elsewhere)
    enforces the match. ``gil_disabled`` reflects the free-threaded build flag.
    """
    gil_disabled = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    return {
        "implementation": sys.implementation.name,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "gil_disabled": gil_disabled,
    }


def build_opacity_report(
    *,
    artifact_id: str,
    env_name: str,
    eligible: int,
    encrypted: int,
    rejected_reasons: Iterable[str],
    runtime_requirement: str = "pyobfus-runtime>=0.1,<1",
) -> Dict[str, object]:
    """Build the shareable, counts-only crossfile-opacity report.

    Deliberately carries no original qualified names and no per-function
    selection -- only the mode, counts, a reason histogram, the runtime and
    interpreter requirements, the key-source *type* and env name, and the
    non-secret build id. The detailed per-binding plan belongs in the private
    mapping's ``opacity_plan`` segment, never here.
    """
    histogram: Mapping[str, int] = dict(Counter(rejected_reasons))
    return {
        "mode": "crossfile_opacity",
        "build_id": artifact_id,
        "eligible_targets": int(eligible),
        "encrypted_targets": int(encrypted),
        "rejected_targets": sum(histogram.values()),
        "rejection_histogram": dict(sorted(histogram.items())),
        "runtime_requirement": runtime_requirement,
        "interpreter": interpreter_tuple(),
        "key_source": {"type": "application_provided_env", "env_name": env_name},
        "unmap_min_core_version": L3_UNMAP_MIN_CORE_VERSION,
    }
