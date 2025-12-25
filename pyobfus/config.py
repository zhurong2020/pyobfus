"""
Configuration management for pyobfus.

Handles loading configuration from files, command-line arguments,
and defining default settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
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
            # Control Flow Flattening state variables
            "_cff_state",
            "_cff_return",
            "_cff_iter",
            # Dead Code Injection variables
            "_dci_",
            # License Embedding variables
            "_lic_",
        }
    )
    name_prefix: str = "I"
    remove_docstrings: bool = True
    remove_comments: bool = True
    string_encoding: bool = False
    preserve_param_names: bool = False  # Preserve parameter names for keyword arguments

    # Pro Edition features
    string_encryption: bool = False  # AES-256 encryption (Pro only)
    anti_debug: bool = False  # Anti-debugging checks (Pro only)
    control_flow_flattening: bool = False  # Control flow flattening (Pro only)
    dead_code_injection: bool = False  # Dead code injection (Pro only)

    # License Embedding options (Pro only)
    license_expire: Optional[str] = None  # Expiration date (YYYY-MM-DD format)
    license_bind_machine: bool = False  # Bind to current machine fingerprint
    license_max_runs: int = 0  # Maximum run count (0 = unlimited)

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

    @classmethod
    def preset_trial(cls, expire_days: int = 30) -> "ObfuscationConfig":
        """
        Trial preset: Create time-limited trial versions.

        - 30-day expiration by default
        - Full obfuscation features
        - Ideal for demo/evaluation versions

        Args:
            expire_days: Number of days until expiration (default: 30)
        """
        from datetime import datetime, timedelta

        expire_date = (datetime.now() + timedelta(days=expire_days)).strftime("%Y-%m-%d")

        config = cls(
            level="pro",
            max_files=None,
            max_total_loc=None,
            string_encryption=True,
            anti_debug=True,
            control_flow_flattening=True,
            dead_code_injection=True,
            license_expire=expire_date,
        )
        return config

    @classmethod
    def preset_commercial(cls) -> "ObfuscationConfig":
        """
        Commercial preset: Maximum protection for paid software.

        - All Pro features enabled
        - Control flow flattening
        - Dead code injection
        - AES-256 string encryption
        - Anti-debugging protection
        - Machine binding
        """
        config = cls(
            level="pro",
            max_files=None,
            max_total_loc=None,
            string_encryption=True,
            anti_debug=True,
            control_flow_flattening=True,
            dead_code_injection=True,
            license_bind_machine=True,
        )
        return config

    @classmethod
    def preset_library(cls) -> "ObfuscationConfig":
        """
        Library preset: For distributing Python libraries.

        - Preserves public APIs
        - Keeps docstrings for documentation
        - Only obfuscates internal implementation
        - Safe for pip distribution
        """
        config = cls(
            level="pro",
            max_files=None,
            max_total_loc=None,
            remove_docstrings=False,
            preserve_param_names=True,
            string_encryption=True,
        )
        return config

    @classmethod
    def preset_maximum(cls) -> "ObfuscationConfig":
        """
        Maximum preset: Highest security for sensitive code.

        - All protection features enabled
        - Machine binding
        - Run count limit (1000)
        - Control flow flattening
        - Dead code injection
        - Anti-debugging
        """
        config = cls(
            level="pro",
            max_files=None,
            max_total_loc=None,
            string_encryption=True,
            anti_debug=True,
            control_flow_flattening=True,
            dead_code_injection=True,
            license_bind_machine=True,
            license_max_runs=1000,
        )
        return config

    @classmethod
    def get_preset(cls, name: str) -> "ObfuscationConfig":
        """
        Get a preset configuration by name.

        Args:
            name: Preset name (trial, commercial, library, maximum, safe, balanced, aggressive)

        Returns:
            ObfuscationConfig with preset settings

        Raises:
            ValueError: If preset name is unknown
        """
        presets: Dict[str, Callable[[], "ObfuscationConfig"]] = {
            "trial": cls.preset_trial,
            "commercial": cls.preset_commercial,
            "library": cls.preset_library,
            "maximum": cls.preset_maximum,
            "safe": cls.preset_safe,
            "balanced": cls.preset_balanced,
            "aggressive": cls.preset_aggressive,
        }

        name_lower = name.lower()
        if name_lower not in presets:
            available = ", ".join(sorted(presets.keys()))
            raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")

        return presets[name_lower]()

    @classmethod
    def list_presets(cls) -> list:
        """
        List all available preset names.

        Returns:
            List of preset names
        """
        return ["trial", "commercial", "library", "maximum", "safe", "balanced", "aggressive"]

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
        # Pattern: _decrypt_*, _encrypt_*, _check_*, _ENCRYPTION_*, _cff_*, etc.
        if name.startswith("_"):
            infrastructure_patterns = [
                "_decrypt",
                "_encrypt",
                "_check",
                "_ENCRYPTION",
                "_KEY",
                "_cff_",  # Control Flow Flattening state variables
                "_dci_",  # Dead Code Injection variables
                "_lic_",  # License Embedding variables
            ]
            if any(pattern in name for pattern in infrastructure_patterns):
                return True

        return False
