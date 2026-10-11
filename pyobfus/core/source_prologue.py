"""Preserve executable source metadata while emitting UTF-8 Python (Community)."""

import codecs
import os
import re
import stat
import tokenize
from pathlib import Path
from typing import Optional, Tuple

# PEP 263: a cookie must be in a comment; line two is eligible only if
# line one is blank or a comment (including a shebang).
_CODING_COOKIE_RE = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)")
_COMMENT_OR_BLANK_RE = re.compile(r"^[ \t\f]*(?:#|\r?$)")


def read_python_source(path: Path) -> str:
    """Decode as Python does, including PEP 263 cookies and UTF-8 BOMs."""
    with tokenize.open(path) as stream:
        return stream.read()


def source_prologue(source: str) -> Tuple[str, Optional[str]]:
    """Return the preserved prefix and any dropped non-UTF-8 encoding name.

    Preserve a UTF-8 cookie at its original line, retaining a preceding
    blank/comment line when necessary. Other leading comments are omitted.
    Line endings are normalized to LF, as for the generated body.
    """
    lines = source.splitlines()[:2]
    prefix = [lines[0]] if lines and lines[0].startswith("#!") else []
    for idx, line in enumerate(lines):
        if idx == 1 and not _COMMENT_OR_BLANK_RE.match(lines[0]):
            break
        match = _CODING_COOKIE_RE.match(line)
        if match:
            encoding = match.group(1)
            if codecs.lookup(encoding).name != "utf-8":
                return "".join(part + "\n" for part in prefix), encoding
            return "".join(part + "\n" for part in lines[: idx + 1]), None
    return "".join(part + "\n" for part in prefix), None


def restore_source_prologue(source: str, generated: str) -> str:
    """Restore metadata after all text passes, before stamping build markers."""
    prefix, _ = source_prologue(source)
    return prefix + generated


def prologue_line_count(text: str) -> int:
    """Count the prefix marker blocks must follow to keep a cookie effective."""
    lines = text.splitlines()[:2]
    for idx, line in enumerate(lines):
        if idx == 1 and not _COMMENT_OR_BLANK_RE.match(lines[0]):
            break
        if _CODING_COOKIE_RE.match(line):
            return idx + 1
    return int(bool(lines and lines[0].startswith("#!")))


def copy_executable_bits(source: Path, output: Path) -> None:
    """Copy only POSIX execute bits, preserving output's other permissions."""
    if os.name == "nt":
        return
    mask = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    bits = source.stat().st_mode & mask
    if bits:
        output.chmod((stat.S_IMODE(output.stat().st_mode) & ~mask) | bits)
