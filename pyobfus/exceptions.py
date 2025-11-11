"""
Custom exceptions for pyobfus.

Clear, actionable error messages to guide users when obfuscation fails.
"""


class PyObfusError(Exception):
    """Base exception for all pyobfus errors."""

    pass


class ParseError(PyObfusError):
    """Raised when Python source code cannot be parsed."""

    def __init__(self, file_path: str, original_error: Exception):
        self.file_path = file_path
        self.original_error = original_error
        super().__init__(
            f"Failed to parse {file_path}: {original_error}\n"
            f"Ensure the file contains valid Python 3.8+ syntax."
        )


class AnalysisError(PyObfusError):
    """Raised when symbol analysis fails."""

    pass


class TransformError(PyObfusError):
    """Raised when code transformation fails."""

    pass


class GenerationError(PyObfusError):
    """Raised when code generation fails."""

    def __init__(self, message: str, ast_node: str = ""):
        self.ast_node = ast_node
        super().__init__(f"Code generation failed: {message}\nNode: {ast_node}")


class ConfigurationError(PyObfusError):
    """Raised when configuration is invalid."""

    pass


class LimitExceededError(PyObfusError):
    """
    Raised when Community Edition limits are exceeded.

    Provides clear upgrade path to Pro edition.
    """

    def __init__(self, limit_type: str, current: int, max_allowed: int):
        self.limit_type = limit_type
        self.current = current
        self.max_allowed = max_allowed
        super().__init__(
            f"Community Edition limit exceeded: {limit_type}\n"
            f"  Current: {current}\n"
            f"  Limit: {max_allowed}\n\n"
            f"Upgrade to pyobfus Pro for unlimited {limit_type}:\n"
            f"  https://github.com/zhurong2020/pyobfus#pricing"
        )
