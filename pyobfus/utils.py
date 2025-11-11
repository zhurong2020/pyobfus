"""
Utility functions for pyobfus.

Provides helper functions for file filtering, path matching, etc.
"""

from pathlib import Path
from typing import List, Optional
import fnmatch


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


def filter_python_files(
    directory: Path, exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Find all Python files in a directory, excluding specified patterns.

    Args:
        directory: Directory to search
        exclude_patterns: List of glob patterns to exclude

    Returns:
        List[Path]: List of Python files to process
    """
    if exclude_patterns is None:
        exclude_patterns = []

    all_py_files = list(directory.rglob("*.py"))

    # Filter out excluded files
    filtered_files = [
        f for f in all_py_files if not should_exclude_file(f, exclude_patterns, directory)
    ]

    return filtered_files


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
