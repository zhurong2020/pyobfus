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
            # Pro infrastructure (must not be renamed)
            "_ENCRYPTION_KEY",
            "_decrypt_str",
            "_check_debugger",
        }
    )
    name_prefix: str = "I"
    remove_docstrings: bool = True
    remove_comments: bool = True
    string_encoding: bool = False

    # Pro Edition features
    string_encryption: bool = False  # AES-256 encryption (Pro only)
    anti_debug: bool = False  # Anti-debugging checks (Pro only)
    control_flow_flattening: bool = False  # Control flow flattening (Pro only, Phase 2)

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
            string_encoding=True,  # Pro: simple encoding
            string_encryption=True,  # Pro: AES-256 encryption
            anti_debug=True,  # Pro: anti-debugging
        )

    @classmethod
    def preset_safe(cls) -> "ObfuscationConfig":
        """
        Safe preset: Production-ready obfuscation.

        - Preserves docstrings for documentation
        - Only obfuscates private methods and variables (starting with _)
        - Keeps all public APIs intact
        - Ideal for libraries and production code
        """
        config = cls()
        config.remove_docstrings = False  # Keep docstrings
        # Will use auto-detection to preserve public APIs
        return config

    @classmethod
    def preset_balanced(cls) -> "ObfuscationConfig":
        """
        Balanced preset: Default obfuscation (current behavior).

        - Removes docstrings
        - Obfuscates private methods and variables
        - Good balance between security and compatibility
        - Recommended for most use cases
        """
        return cls()  # Default configuration

    @classmethod
    def preset_aggressive(cls) -> "ObfuscationConfig":
        """
        Aggressive preset: Maximum obfuscation.

        - Obfuscates everything possible
        - Removes all docstrings and comments
        - May require manual exclusion lists
        - Use with caution - may break code
        """
        config = cls()
        config.exclude_names = {
            # Only preserve absolute essentials
            "__init__",
            "__str__",
            "__repr__",
            "__call__",
            "__enter__",
            "__exit__",
            "__main__",
        }
        config.remove_docstrings = True
        config.remove_comments = True
        return config

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

        # Exclude infrastructure names (Pro feature support functions/variables)
        # Pattern: _decrypt_*, _encrypt_*, _check_*, _ENCRYPTION_*, etc.
        if name.startswith("_"):
            infrastructure_patterns = [
                "_decrypt",
                "_encrypt",
                "_check",
                "_ENCRYPTION",
                "_KEY",
            ]
            if any(pattern in name for pattern in infrastructure_patterns):
                return True

        return False
