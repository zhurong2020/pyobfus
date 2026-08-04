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
    numeric_obfuscation: bool = False  # Opaque arithmetic for numeric literals (Community)
    strip_ai_artifacts: bool = False  # Remove AI provenance markers (Community)
    preserve_param_names: bool = False  # Preserve parameter names for keyword arguments

    # Pro Edition features
    string_encryption: bool = False  # AES-256 encryption (Pro only)
    import_obfuscation: bool = False  # Runtime importlib imports + encrypted import strings
    anti_debug: bool = False  # Anti-debugging checks (Pro only)
    control_flow_flattening: bool = False  # Control flow flattening (Pro only)
    dead_code_injection: bool = False  # Dead code injection (Pro only)

    # License Embedding options (Pro only)
    license_expire: Optional[str] = None  # Expiration date (YYYY-MM-DD format)
    license_bind_machine: bool = False  # Bind to current machine fingerprint
    license_max_runs: int = 0  # Maximum run count (0 = unlimited)

    # v0.5.1 patent-targeted Pro mechanisms (build-fusion; Pro only)
    selective_opacity: bool = False  # P2-1: encrypt @opacity(Layer.ENCRYPTED) functions
    seal_code: bool = False  # P2-9: bytecode integrity seal for @seal_code functions
    vault: bool = False  # P2-11: encrypt vault_secrets({...}) into a runtime Vault
    scrub_traceback: bool = False  # P2-10: encrypt production tracebacks
    fingerprint: Optional[str] = None  # P2-7: per-buyer deterministic L3 key (buyer id)
    expire_hard: Optional[str] = None  # P2-8 (subset): module-top expire_check(ISO date)
    period_max_runs: Optional[int] = None  # P2-8 (subset): module-top run-counter limit (v0.5.3)
    opacity_config: Optional[str] = (
        None  # P2-1: opacity.toml path -> pattern-driven layers (v0.5.3)
    )
    bind_device: bool = False  # P2-8: runtime device-key substitution for L3 (v0.5.3)
    bind_device_id: Optional[str] = None  # P2-8: target machine-id (None = build machine)
    requires_os: Optional[str] = None  # P2-16: comma-separated OS allowlist (platform.system())
    requires_python_min: Optional[str] = None  # P2-16: minimum Python version "X.Y"
    requires_arch: Optional[str] = (
        None  # P2-16: comma-separated CPU arch allowlist (platform.machine())
    )

    # Performance options
    max_workers: Optional[int] = None  # None = auto (cpu_count), 1 = sequential

    # Community Edition limits
    max_files: Optional[int] = None  # None = unlimited for Pro
    max_total_loc: Optional[int] = None  # None = unlimited for Pro

    @classmethod
    def from_file(cls, config_path: Path) -> "ObfuscationConfig":
        """Load configuration from YAML file.

        The YAML may optionally contain a `preset:` key naming a built-in
        preset (safe/balanced/aggressive/fastapi/django/…). When present,
        the preset is applied first and the remaining keys override
        individual fields. This matches the output of `pyobfus --init`.
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        obf_config = dict(data.get("obfuscation", {}))

        # Pop `preset:` if present and use it as the base configuration
        preset_name = obf_config.pop("preset", None)
        if preset_name:
            base = cls.get_preset(str(preset_name))
        else:
            base = cls()

        # Convert exclude_names list to set if present
        if "exclude_names" in obf_config and isinstance(obf_config["exclude_names"], list):
            obf_config["exclude_names"] = set(obf_config["exclude_names"])

        # Merge exclude_patterns: YAML entries extend the preset's baseline
        if "exclude_patterns" in obf_config and isinstance(obf_config["exclude_patterns"], list):
            merged: List[str] = list(base.exclude_patterns)
            for pattern in obf_config["exclude_patterns"]:
                if pattern not in merged:
                    merged.append(pattern)
            obf_config["exclude_patterns"] = merged

        # Merge exclude_names: YAML entries extend the preset's baseline
        if "exclude_names" in obf_config:
            obf_config["exclude_names"] = set(base.exclude_names) | set(obf_config["exclude_names"])

        # Apply overrides field-by-field (dataclass doesn't let us replace with unknown keys)
        for key, value in obf_config.items():
            if hasattr(base, key):
                setattr(base, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")

        return base

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

    # ------------------------------------------------------------------
    # Framework-aware presets (community, no Pro features required)
    # ------------------------------------------------------------------
    #
    # Each framework preset extends preset_safe() with:
    #   - preserve_param_names = True  (frameworks lean heavily on kwargs /
    #     dependency injection / field names as identifiers)
    #   - framework-specific `exclude_names` for symbols reached through
    #     reflection or framework-managed dispatch
    #   - `exclude_patterns` for files/directories commonly expected to
    #     remain unmodified (migrations, generated code, entry scripts)
    #
    # See docs/ROADMAP.md P0-3 and docs/AI_INTEGRATION_STRATEGY.md for
    # why these presets exist and what "framework-aware" means here.

    @classmethod
    def preset_fastapi(cls) -> "ObfuscationConfig":
        """FastAPI preset: preserves dependency-injection param names and routers.

        - Based on preset_safe (docstrings preserved)
        - preserve_param_names=True (Depends(), Query(), Body() rely on names)
        - Excludes HTTP verb method names used by APIRouter / Starlette
        - Excludes common router and dependency modules by path pattern
        """
        config = cls.preset_safe()
        config.preserve_param_names = True
        config.exclude_names = config.exclude_names | {
            # Starlette / FastAPI dispatch methods
            "dispatch",
            "__call__",
            "app",
            "router",
            "lifespan",
            # HTTP verbs commonly overridden on class-based routes
            "get",
            "post",
            "put",
            "delete",
            "patch",
            "head",
            "options",
            "trace",
            # Pydantic model interfaces frequently used inside handlers
            "model_dump",
            "model_validate",
            "dict",
            "json",
            "parse_obj",
            "Config",
            "fields",
        }
        config.exclude_patterns = list(config.exclude_patterns) + [
            "**/routers/**",
            "**/dependencies.py",
            "**/main.py",
        ]
        return config

    @classmethod
    def preset_django(cls) -> "ObfuscationConfig":
        """Django preset: preserves ORM, CBV, signals, migrations.

        - Based on preset_safe (docstrings preserved)
        - preserve_param_names=True (form/model fields, template context)
        - Excludes Django-managed method names (Meta, save, clean, get/post…)
        - Excludes migrations, manage.py, wsgi/asgi entry points by path
        """
        config = cls.preset_safe()
        config.preserve_param_names = True
        config.exclude_names = config.exclude_names | {
            # CBV HTTP verb handlers
            "get",
            "post",
            "put",
            "delete",
            "patch",
            "head",
            "options",
            # Generic CBV hooks
            "get_queryset",
            "get_object",
            "get_context_data",
            "get_form_class",
            "form_valid",
            "form_invalid",
            "get_success_url",
            # Model / Form protocol
            "Meta",
            "save",
            "delete",
            "clean",
            "full_clean",
            "is_valid",
            "save_m2m",
            "natural_key",
            "from_db",
            "refresh_from_db",
            # Admin
            "ModelAdmin",
            "list_display",
            "list_filter",
            "search_fields",
            # Signal receivers reached via sender string
            "pre_save",
            "post_save",
            "pre_delete",
            "post_delete",
            "m2m_changed",
        }
        config.exclude_patterns = list(config.exclude_patterns) + [
            "**/migrations/**",
            "**/apps.py",
            "**/urls.py",
            "**/wsgi.py",
            "**/asgi.py",
            "**/manage.py",
            "**/settings.py",
        ]
        return config

    @classmethod
    def preset_flask(cls) -> "ObfuscationConfig":
        """Flask preset: preserves view functions and url_for() targets.

        - Based on preset_safe
        - preserve_param_names=True (URL variable names become handler kwargs)
        - Excludes Flask/Werkzeug dispatch methods
        - Excludes blueprint / views directories by path pattern
        """
        config = cls.preset_safe()
        config.preserve_param_names = True
        config.exclude_names = config.exclude_names | {
            "dispatch_request",
            "full_dispatch_request",
            "app",
            "blueprint",
            "before_request",
            "after_request",
            "teardown_request",
            "errorhandler",
            "register_blueprint",
            # HTTP verbs on MethodView
            "get",
            "post",
            "put",
            "delete",
            "patch",
            "head",
            "options",
        }
        config.exclude_patterns = list(config.exclude_patterns) + [
            "**/views/**",
            "**/blueprints/**",
            "**/wsgi.py",
        ]
        return config

    @classmethod
    def preset_pydantic(cls) -> "ObfuscationConfig":
        """Pydantic preset: preserves BaseModel field API.

        - Based on preset_safe (docstrings preserved)
        - preserve_param_names=True (field names are the serialization keys)
        - Excludes v1 and v2 public BaseModel interfaces + validator hooks
        """
        config = cls.preset_safe()
        config.preserve_param_names = True
        config.exclude_names = config.exclude_names | {
            # Pydantic v2 public API
            "model_dump",
            "model_dump_json",
            "model_validate",
            "model_validate_json",
            "model_copy",
            "model_config",
            "model_fields",
            "model_computed_fields",
            "model_json_schema",
            # Pydantic v1 public API (still widely used)
            "dict",
            "json",
            "parse_obj",
            "parse_raw",
            "parse_file",
            "from_orm",
            "copy",
            "schema",
            "schema_json",
            # Config + validator decorators
            "Config",
            "validator",
            "root_validator",
            "field_validator",
            "model_validator",
            "computed_field",
        }
        return config

    @classmethod
    def preset_click(cls) -> "ObfuscationConfig":
        """Click preset: preserves CLI command, group, and option names.

        - Based on preset_safe
        - preserve_param_names=True (Click maps --option to handler kwargs)
        - Excludes Click decorator-managed symbols
        """
        config = cls.preset_safe()
        config.preserve_param_names = True
        config.exclude_names = config.exclude_names | {
            "command",
            "group",
            "option",
            "argument",
            "pass_context",
            "pass_obj",
            "confirmation_option",
            "help_option",
            "version_option",
            "cli",
            "main",
            "ctx",
        }
        return config

    @classmethod
    def preset_sqlalchemy(cls) -> "ObfuscationConfig":
        """SQLAlchemy preset: preserves ORM columns, relationships, sessions.

        - Based on preset_safe
        - preserve_param_names=True (column names = python attribute names)
        - Excludes ORM-managed dunder-like attributes and session API
        """
        config = cls.preset_safe()
        config.preserve_param_names = True
        config.exclude_names = config.exclude_names | {
            "__tablename__",
            "__table_args__",
            "metadata",
            "registry",
            "Base",
            "DeclarativeBase",
            "MappedAsDataclass",
            "Column",
            "Mapped",
            "mapped_column",
            "relationship",
            "primary_key",
            "foreign_key",
            "ForeignKey",
            "session",
            "Session",
            "sessionmaker",
            "query",
            "add",
            "add_all",
            "commit",
            "rollback",
            "flush",
            "merge",
            "refresh",
        }
        config.exclude_patterns = list(config.exclude_patterns) + [
            "**/alembic/**",
            "**/migrations/**",
        ]
        return config

    @classmethod
    def preset_ml(cls) -> "ObfuscationConfig":
        """ML/model-serving preset: protects inference wrappers safely.

        - Based on preset_safe (docstrings preserved)
        - preserve_param_names=True, matching every other framework preset's
          convention for serving frameworks/tensor adapters that call
          wrappers by keyword
        - exclude_names covers only method names external code dispatches by
          exact string (sklearn's `predict`/`fit`/`transform`, PyTorch's
          `forward` via `nn.Module.__call__`, HuggingFace's `generate`/
          tokenizer `encode`) — generic variable-name words like `model` or
          `pipeline` are deliberately NOT blanket-excluded here, since
          exclude_names matches that exact identifier anywhere in the whole
          codebase, not just inside a wrapper's parameter list, and doing so
          would leave unrelated business logic needlessly readable too
        - Excludes model artifact directories that should not be rewritten

        Runtime String Vault routing for model paths remains an opt-in Pro
        source marker (`vault_secrets({...})`); preflight surfaces guidance for
        unsafe model deserialization and artifact literals.
        """
        config = cls.preset_safe()
        config.preserve_param_names = True
        config.exclude_names = config.exclude_names | {
            "predict",
            "predict_proba",
            "fit",
            "transform",
            "forward",
            "generate",
            "encode",
        }
        config.exclude_patterns = list(config.exclude_patterns) + [
            "**/models/**",
            "**/checkpoints/**",
            "**/weights/**",
            "**/*.pt",
            "**/*.pth",
            "**/*.onnx",
            "**/*.safetensors",
        ]
        return config

    @classmethod
    def get_preset(cls, name: str) -> "ObfuscationConfig":
        """
        Get a preset configuration by name.

        Args:
            name: Preset name. Available:
                - Community: safe, balanced, aggressive
                - Framework: fastapi, django, flask, pydantic, click, sqlalchemy, ml
                - Pro: trial, commercial, library, maximum

        Returns:
            ObfuscationConfig with preset settings

        Raises:
            ValueError: If preset name is unknown
        """
        presets: Dict[str, Callable[[], "ObfuscationConfig"]] = {
            # Community
            "safe": cls.preset_safe,
            "balanced": cls.preset_balanced,
            "aggressive": cls.preset_aggressive,
            # Framework-aware (community, no Pro required)
            "fastapi": cls.preset_fastapi,
            "django": cls.preset_django,
            "flask": cls.preset_flask,
            "pydantic": cls.preset_pydantic,
            "click": cls.preset_click,
            "sqlalchemy": cls.preset_sqlalchemy,
            "ml": cls.preset_ml,
            # Pro
            "trial": cls.preset_trial,
            "commercial": cls.preset_commercial,
            "library": cls.preset_library,
            "maximum": cls.preset_maximum,
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
        return [
            # Community
            "safe",
            "balanced",
            "aggressive",
            # Framework-aware
            "fastapi",
            "django",
            "flask",
            "pydantic",
            "click",
            "sqlalchemy",
            "ml",
            # Pro
            "trial",
            "commercial",
            "library",
            "maximum",
        ]

    # Framework presets are community-tier (no Pro license required)
    FRAMEWORK_PRESETS = frozenset(
        {"fastapi", "django", "flask", "pydantic", "click", "sqlalchemy", "ml"}
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
