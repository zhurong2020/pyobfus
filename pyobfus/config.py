"""
Configuration management for pyobfus.

Handles loading configuration from files, command-line arguments,
and defining default settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set
import yaml


@dataclass
class ObfuscationConfig:
    """
    Configuration for obfuscation behavior.

    Attributes:
        level: Obfuscation level ('community' or 'pro')
        exclude_patterns: File patterns to exclude (glob syntax)
        exclude_names: Names to preserve (builtins, imports, etc.)
        name_prefix: Prefix for obfuscated names (default: 'I')
        remove_docstrings: Remove docstrings (default: True)
        remove_comments: Remove comments (default: True)
        string_encoding: Enable simple string encoding (default: False)
    """

    level: str = "community"
    exclude_patterns: List[str] = field(default_factory=lambda: ["test_*.py", "**/tests/**"])
    exclude_names: Set[str] = field(
        default_factory=lambda: {
            # Python builtins
            "print",
            "len",
            "range",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "bool",
            "type",
            "object",
            "Exception",
            # Magic methods
            "__init__",
            "__str__",
            "__repr__",
            "__call__",
            "__enter__",
            "__exit__",
            "__main__",
            # Common imports
            "main",
            "logger",
            "config",
        }
    )
    name_prefix: str = "I"
    remove_docstrings: bool = True
    remove_comments: bool = True
    string_encoding: bool = False

    # Community Edition limits
    max_files: Optional[int] = None  # None = unlimited for Pro
    max_total_loc: Optional[int] = None  # None = unlimited for Pro

    @classmethod
    def from_file(cls, config_path: Path) -> "ObfuscationConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Get obfuscation config
        obf_config = data.get("obfuscation", {})

        # Convert exclude_names list to set if present
        if "exclude_names" in obf_config and isinstance(obf_config["exclude_names"], list):
            obf_config["exclude_names"] = set(obf_config["exclude_names"])

        return cls(**obf_config)

    @classmethod
    def community_edition(cls) -> "ObfuscationConfig":
        """Get default Community Edition configuration with limits."""
        return cls(
            level="community",
            max_files=5,  # Community: max 5 files
            max_total_loc=1000,  # Community: max 1000 LOC total
        )

    @classmethod
    def pro_edition(cls) -> "ObfuscationConfig":
        """Get Pro Edition configuration (unlimited)."""
        return cls(
            level="pro",
            max_files=None,  # Pro: unlimited
            max_total_loc=None,  # Pro: unlimited
            string_encoding=True,  # Pro feature
        )

    def add_exclude_pattern(self, pattern: str) -> None:
        """Add a file pattern to exclude."""
        self.exclude_patterns.append(pattern)

    def add_exclude_name(self, name: str) -> None:
        """Add a name to preserve during obfuscation."""
        self.exclude_names.add(name)

    def should_exclude_name(self, name: str) -> bool:
        """Check if a name should be excluded from obfuscation."""
        # Always exclude magic methods
        if name.startswith("__") and name.endswith("__"):
            return True

        # Check explicit exclusions
        if name in self.exclude_names:
            return True

        return False
