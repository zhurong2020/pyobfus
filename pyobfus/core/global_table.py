"""
Global Symbol Table for Cross-file Name Mapping.

This module provides the GlobalSymbolTable class which maintains a centralized
registry of all exported names across files in a multi-file project.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass


@dataclass
class ImportInfo:
    """
    Information about an import statement.

    Attributes:
        from_module: Module name being imported from (e.g., "calculator")
        import_name: Original name being imported (e.g., "Calculator")
        alias: Optional alias (e.g., "Calc" in "import Calculator as Calc")
        is_relative: Whether this is a relative import (from . import ...)
        level: Relative import level (0=absolute, 1=., 2=.., etc.)
    """

    from_module: str
    import_name: str
    alias: Optional[str] = None
    is_relative: bool = False
    level: int = 0


class GlobalSymbolTable:
    """
    Centralized mapping of all exported names across files.

    The global symbol table is built during Phase 1 (scan) and used during
    Phase 2 (transform) to ensure consistent name obfuscation across files.

    Example:
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>> table.register_export("calculator", "add", "I1")
        >>> table.get_obfuscated_import("calculator", "Calculator")
        'I0'
    """

    def __init__(self):
        """Initialize empty global symbol table."""
        # Module exports: module_name -> {original_name -> obfuscated_name}
        # Example: {"calculator": {"Calculator": "I0", "add": "I1"}}
        self.module_exports: Dict[str, Dict[str, str]] = {}

        # Import statements: file_path -> [ImportInfo, ...]
        # Track what each file imports for validation
        self.import_statements: Dict[Path, List[ImportInfo]] = {}

        # All used obfuscated names (for collision detection)
        self.used_names: Set[str] = set()

        # Reverse mapping: obfuscated_name -> (module, original_name)
        # Used for debugging and validation
        self._reverse_mapping: Dict[str, Tuple[str, str]] = {}

    def register_export(self, module: str, original_name: str, obfuscated_name: str) -> None:
        """
        Register a name exported by a module.

        Args:
            module: Module name (e.g., "calculator")
            original_name: Original name (e.g., "Calculator")
            obfuscated_name: Obfuscated name (e.g., "I0")

        Raises:
            ValueError: If obfuscated_name is already used for a different symbol
        """
        # Check for name collision
        if obfuscated_name in self.used_names:
            existing = self._reverse_mapping.get(obfuscated_name)
            if existing is not None and existing != (module, original_name):
                raise ValueError(
                    f"Name collision: {obfuscated_name} already used for "
                    f"{existing[0]}.{existing[1]}, cannot use for "
                    f"{module}.{original_name}"
                )

        # Register export
        if module not in self.module_exports:
            self.module_exports[module] = {}

        self.module_exports[module][original_name] = obfuscated_name
        self.used_names.add(obfuscated_name)
        self._reverse_mapping[obfuscated_name] = (module, original_name)

    def get_obfuscated_import(self, module: str, original_name: str) -> Optional[str]:
        """
        Get the obfuscated name for an import.

        Args:
            module: Module name (e.g., "calculator")
            original_name: Original name (e.g., "Calculator")

        Returns:
            Obfuscated name (e.g., "I0"), or None if not found
        """
        return self.module_exports.get(module, {}).get(original_name)

    def resolve_import(self, from_module: str, import_name: str) -> Optional[str]:
        """
        Resolve import to obfuscated name.

        This is an alias for get_obfuscated_import() for backward compatibility.

        Args:
            from_module: Module name
            import_name: Name being imported

        Returns:
            Obfuscated name, or None if not found
        """
        return self.get_obfuscated_import(from_module, import_name)

    def register_import(self, file_path: Path, import_info: ImportInfo) -> None:
        """
        Register an import statement for a file.

        This is used for validation and debugging.

        Args:
            file_path: File containing the import
            import_info: Import information
        """
        if file_path not in self.import_statements:
            self.import_statements[file_path] = []

        self.import_statements[file_path].append(import_info)

    def get_module_exports(self, module: str) -> Dict[str, str]:
        """
        Get all exports from a module.

        Args:
            module: Module name

        Returns:
            Dictionary mapping original names to obfuscated names
        """
        return self.module_exports.get(module, {}).copy()

    def get_all_modules(self) -> List[str]:
        """
        Get list of all registered modules.

        Returns:
            List of module names
        """
        return list(self.module_exports.keys())

    def is_name_used(self, obfuscated_name: str) -> bool:
        """
        Check if an obfuscated name is already used.

        Args:
            obfuscated_name: Name to check

        Returns:
            True if name is used, False otherwise
        """
        return obfuscated_name in self.used_names

    def get_reverse_mapping(self, obfuscated_name: str) -> Optional[Tuple[str, str]]:
        """
        Get original (module, name) for an obfuscated name.

        Args:
            obfuscated_name: Obfuscated name

        Returns:
            Tuple of (module, original_name), or None if not found
        """
        return self._reverse_mapping.get(obfuscated_name)

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the global symbol table.

        Returns:
            Dictionary with statistics:
            - total_modules: Number of modules
            - total_exports: Total number of exported names
            - total_imports: Total number of import statements
        """
        total_exports = sum(len(exports) for exports in self.module_exports.values())
        total_imports = sum(len(imports) for imports in self.import_statements.values())

        return {
            "total_modules": len(self.module_exports),
            "total_exports": total_exports,
            "total_imports": total_imports,
        }

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the global symbol table for consistency.

        Returns:
            Tuple of (is_valid, errors)
            - is_valid: True if no errors found
            - errors: List of error messages
        """
        errors = []

        # Check for unresolved imports
        for file_path, imports in self.import_statements.items():
            for import_info in imports:
                # Skip standard library imports (not in our table)
                if import_info.from_module not in self.module_exports:
                    continue

                # Check if imported name exists
                if import_info.import_name != "*":
                    obfuscated = self.get_obfuscated_import(
                        import_info.from_module, import_info.import_name
                    )
                    if obfuscated is None:
                        errors.append(
                            f"{file_path}: Cannot resolve import "
                            f"'{import_info.import_name}' from '{import_info.from_module}'"
                        )

        is_valid = len(errors) == 0
        return (is_valid, errors)

    def __repr__(self) -> str:
        """String representation for debugging."""
        stats = self.get_statistics()
        return (
            f"GlobalSymbolTable("
            f"modules={stats['total_modules']}, "
            f"exports={stats['total_exports']}, "
            f"imports={stats['total_imports']})"
        )
