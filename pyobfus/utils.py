"""
Utility functions for pyobfus.

Provides helper functions for file filtering, path matching, etc.
"""

from pathlib import Path
from typing import List, Optional
import fnmatch
import os


def should_exclude_file(
    file_path: Path,
    exclude_patterns: Optional[List[str]] = None,
    base_path: Optional[Path] = None,
) -> bool:
    """
    Check if a file should be excluded based on glob patterns.

    Args:
        file_path: File path to check
        exclude_patterns: List of glob patterns (e.g., "test_*.py", "**/tests/**"), or None
        base_path: Base path for relative pattern matching

    Returns:
        bool: True if file should be excluded

    Examples:
        >>> should_exclude_file(Path("test_foo.py"), ["test_*.py"])
        True
        >>> should_exclude_file(Path("src/test/foo.py"), ["**/test/**"])
        True
    """
    if not exclude_patterns:
        return False

    # Get relative path if base_path provided
    if base_path:
        try:
            file_path = file_path.relative_to(base_path)
        except ValueError:
            pass  # file_path not relative to base_path

    # Convert to string for pattern matching
    file_str = str(file_path).replace("\\", "/")  # Normalize path separators

    for pattern in exclude_patterns:
        # Normalize pattern separators
        pattern = pattern.replace("\\", "/")

        # Match against filename only
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

        # Match against full path (for patterns like **/tests/**)
        if fnmatch.fnmatch(file_str, pattern):
            return True

        # Match any part of the path
        if "**" in pattern:
            # Remove ** and try matching parts
            simple_pattern = pattern.replace("**/", "").replace("/**", "")
            if simple_pattern in file_str:
                return True

    return False


ENVIRONMENT_TOOL_DIRS = frozenset(
    {
        "site-packages",
        "dist-packages",
        "node_modules",
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".nox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)


def format_skipped_directories(directories: List[str]) -> str:
    """Summarize pruned subtrees without enumerating their files."""
    sample = ", ".join(directories[:10]) or "none"
    suffix = ", ..." if len(directories) > 10 else ""
    return f"Skipped environment/tool directories: {len(directories)} ({sample}{suffix})"


def filter_python_files(
    directory: Path,
    exclude_patterns: Optional[List[str]] = None,
    *,
    skip_environment_dirs: bool = True,
    skipped_directories: Optional[List[str]] = None,
) -> List[Path]:
    """Discover sorted Python files, pruning environment/tool subtrees by default.

    The explicit input root is always traversed. Symlink directories are not
    followed, matching Path.rglob's behavior. ``skipped_directories``, when
    supplied, receives sorted relative POSIX paths of pruned subtree roots;
    files inside them are never enumerated, even for exclusion reporting.
    Set ``skip_environment_dirs=False`` to restore legacy discovery.
    """
    files: List[Path] = []
    skipped: List[str] = []
    for current, dirs, names in os.walk(directory, topdown=True, followlinks=False):
        parent = Path(current)
        if skip_environment_dirs:
            kept = []
            for name in dirs:
                child = parent / name
                if (
                    name in ENVIRONMENT_TOOL_DIRS
                    or (child / "pyvenv.cfg").is_file()
                    or (child / "conda-meta").is_dir()
                ):
                    skipped.append(child.relative_to(directory).as_posix())
                else:
                    kept.append(name)
            dirs[:] = kept
        for name in names:
            if name.endswith(".py"):
                path = parent / name
                if not should_exclude_file(path, exclude_patterns, directory):
                    files.append(path)
    if skipped_directories is not None:
        skipped_directories.extend(sorted(skipped))
    # Stable ordering controls name assignment, manifests and cache signatures.
    return sorted(files)


def count_total_lines(files: List[Path]) -> int:
    """
    Count total lines across multiple Python files.

    Args:
        files: List of Python files

    Returns:
        int: Total line count
    """
    total = 0
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                total += sum(1 for _ in f)
        except Exception:
            pass  # Skip files that can't be read

    return total
