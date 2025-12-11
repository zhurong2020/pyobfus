"""
Cross-file Obfuscation Orchestrator.

This module provides the CrossFileOrchestrator class which coordinates
the two-phase obfuscation process for multi-file projects.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from pyobfus.config import ObfuscationConfig
from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.core.export_detector import ExportDetector
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.parser import ASTParser
from pyobfus.transformers.import_rewriter import ImportRewriter
from pyobfus.transformers.all_list_updater import AllListUpdater
from pyobfus.transformers.exported_name_transformer import ExportedNameTransformer
from pyobfus.transformers.imported_name_transformer import (
    ImportedNameTransformer,
    ImportCollector,
)
from pyobfus.transformers.local_name_transformer import LocalNameTransformer
from pyobfus.utils import filter_python_files


@dataclass
class ObfuscationResult:
    """
    Result of obfuscation operation.

    Attributes:
        files_processed: Number of files processed
        global_mappings: Number of global name mappings
        warnings: List of warning messages
        errors: List of error messages
    """

    files_processed: int
    global_mappings: int
    warnings: List[str]
    errors: List[str]

    @property
    def success(self) -> bool:
        """Check if obfuscation was successful (no errors)."""
        return len(self.errors) == 0


@dataclass
class FileInfo:
    """
    Information about a file in the project.

    Attributes:
        path: Path to the file
        relative_path: Path relative to project root
        module_name: Python module name (e.g., "calculator", "utils.helpers")
        exports: Set of exported names
    """

    path: Path
    relative_path: Path
    module_name: str
    exports: Set[str]


class CrossFileOrchestrator:
    """
    Orchestrate cross-file obfuscation with two-phase processing.

    Phase 1 (Scan): Build global symbol table
    - Discover all Python files
    - Detect exports from each file
    - Generate obfuscated names
    - Populate global symbol table

    Phase 2 (Transform): Transform all files
    - Analyze each file with global context
    - Transform names (local + imported)
    - Rewrite import statements
    - Generate obfuscated output

    Example:
        >>> config = ObfuscationConfig.community_edition()
        >>> orchestrator = CrossFileOrchestrator(config)
        >>> result = orchestrator.obfuscate(Path("src"), Path("dist"))
        >>> print(f"Processed {result.files_processed} files")
    """

    def __init__(self, config: ObfuscationConfig):
        """
        Initialize orchestrator.

        Args:
            config: Obfuscation configuration
        """
        self.config = config
        self.global_table = GlobalSymbolTable()

        # Track discovered files
        self.files: List[FileInfo] = []

        # Name generator state
        self._name_counter: int = 0
        self._name_prefix: str = config.name_prefix

    def obfuscate(self, input_dir: Path, output_dir: Path) -> ObfuscationResult:
        """
        Obfuscate entire project with cross-file coordination.

        Args:
            input_dir: Source directory
            output_dir: Output directory

        Returns:
            ObfuscationResult with statistics and messages
        """
        warnings: List[str] = []
        errors: List[str] = []

        try:
            # Phase 1: Scan
            self.phase1_scan(input_dir)

            # Validate global table
            is_valid, validation_errors = self.global_table.validate()
            if not is_valid:
                errors.extend(validation_errors)
                # Don't proceed to Phase 2 if validation failed
                return ObfuscationResult(
                    files_processed=len(self.files),
                    global_mappings=self.global_table.get_statistics()["total_exports"],
                    warnings=warnings,
                    errors=errors,
                )

            # Phase 2: Transform
            self.phase2_transform(input_dir, output_dir)

        except Exception as e:
            errors.append(f"Obfuscation failed: {e}")

        return ObfuscationResult(
            files_processed=len(self.files),
            global_mappings=self.global_table.get_statistics()["total_exports"],
            warnings=warnings,
            errors=errors,
        )

    def phase1_scan(self, input_dir: Path) -> GlobalSymbolTable:
        """
        Phase 1: Build global symbol table.

        Scans all files to:
        1. Discover Python files
        2. Detect exports
        3. Generate obfuscated names
        4. Populate global symbol table

        Args:
            input_dir: Source directory

        Returns:
            Populated GlobalSymbolTable
        """
        # 1. Discover files
        self.files = self._discover_files(input_dir)

        # 2. For each file, detect exports and register in global table
        for file_info in self.files:
            # Parse file
            tree = ASTParser.parse_file(file_info.path)

            # Detect exports
            detector = ExportDetector()
            detector.visit(tree)
            exports = detector.get_exports()

            # Update file_info
            file_info.exports = exports

            # Register each export in global table
            for export_name in exports:
                # Skip names that should be preserved
                if self._should_preserve_name(export_name):
                    continue

                # Generate obfuscated name
                obfuscated_name = self._generate_obfuscated_name()

                # Register in global table
                self.global_table.register_export(
                    module=file_info.module_name,
                    original_name=export_name,
                    obfuscated_name=obfuscated_name,
                )

        return self.global_table

    def phase2_transform(self, input_dir: Path, output_dir: Path) -> None:
        """
        Phase 2: Transform all files.

        Uses global symbol table to:
        1. Rename exported definitions (class Calculator -> class I0)
        2. Rewrite import statements using global mappings
        3. Update references to imported names (Calculator() -> I0())
        4. Update __all__ lists with obfuscated names
        5. Generate obfuscated output files

        Args:
            input_dir: Source directory
            output_dir: Output directory
        """
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Transform each file
        for file_info in self.files:
            # Read source file
            with open(file_info.path, "r", encoding="utf-8") as f:
                source = f.read()

            # Parse to AST and save original for reference analysis
            original_tree = ast.parse(source)
            tree = ast.parse(source)

            # Collect imported names from original tree (before any transformation)
            import_collector = ImportCollector(self.global_table, file_info.module_name)
            import_collector.visit(original_tree)
            imported_names = set(import_collector.import_mappings.keys())

            # Apply transformers in order:
            # 1. Rename exported definitions (class Calculator -> class I0)
            exported_name_transformer = ExportedNameTransformer(
                self.global_table,
                file_info.module_name,
                file_info.path,
            )
            tree = exported_name_transformer.visit(tree)

            # 2. Rewrite import statements (from X import Y -> from X import I0)
            import_rewriter = ImportRewriter(
                self.global_table,
                file_info.module_name,
                file_info.path,
            )
            tree = import_rewriter.visit(tree)

            # 3. Update references to imported names (Y() -> I0())
            imported_name_transformer = ImportedNameTransformer(
                original_tree,  # Use original to analyze imports
                self.global_table,
                file_info.module_name,
                file_info.path,
            )
            tree = imported_name_transformer.visit(tree)

            # 4. Update references to local exported names (run_demo() -> I2())
            local_name_transformer = LocalNameTransformer(
                self.global_table,
                file_info.module_name,
                imported_names,  # Don't rename imported names
                file_info.path,
            )
            tree = local_name_transformer.visit(tree)

            # 5. Update __all__ lists
            all_updater = AllListUpdater(
                self.global_table,
                file_info.module_name,
                file_info.path,
            )
            tree = all_updater.visit(tree)

            # Fix missing locations
            ast.fix_missing_locations(tree)

            # Convert back to source (use CodeGenerator for Python 3.8 compatibility)
            new_source = CodeGenerator.generate(tree)

            # Write to output directory, preserving directory structure
            output_file = output_dir / file_info.relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(new_source)

    def _discover_files(self, input_dir: Path) -> List[FileInfo]:
        """
        Discover all Python files in directory.

        Args:
            input_dir: Source directory

        Returns:
            List of FileInfo objects
        """
        # Use existing utility to find Python files
        python_files = filter_python_files(input_dir, self.config.exclude_patterns)

        file_infos = []
        for file_path in python_files:
            # Calculate relative path
            relative_path = file_path.relative_to(input_dir)

            # Calculate module name (e.g., "utils/helpers.py" -> "utils.helpers")
            module_name = self._path_to_module_name(relative_path)

            file_info = FileInfo(
                path=file_path,
                relative_path=relative_path,
                module_name=module_name,
                exports=set(),  # Will be filled during scan
            )
            file_infos.append(file_info)

        return file_infos

    def _path_to_module_name(self, relative_path: Path) -> str:
        """
        Convert file path to Python module name.

        Args:
            relative_path: Relative path (e.g., "utils/helpers.py")

        Returns:
            Module name (e.g., "utils.helpers")

        Examples:
            >>> self._path_to_module_name(Path("calculator.py"))
            'calculator'
            >>> self._path_to_module_name(Path("utils/helpers.py"))
            'utils.helpers'
            >>> self._path_to_module_name(Path("pkg/subpkg/module.py"))
            'pkg.subpkg.module'
        """
        # Remove .py extension
        parts = list(relative_path.parts)
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        # Join with dots
        return ".".join(parts)

    def _generate_obfuscated_name(self) -> str:
        """
        Generate unique obfuscated name.

        Returns:
            Obfuscated name (e.g., "I0", "I1", "I2"...)

        Note:
            Ensures uniqueness by checking GlobalSymbolTable.
        """
        while True:
            name = f"{self._name_prefix}{self._name_counter}"
            self._name_counter += 1

            # Check if name is already used
            if not self.global_table.is_name_used(name):
                return name

    def _should_preserve_name(self, name: str) -> bool:
        """
        Check if name should be preserved (not obfuscated).

        Args:
            name: Name to check

        Returns:
            True if name should be preserved, False otherwise
        """
        # Check against exclude_names in config
        if name in self.config.exclude_names:
            return True

        # Check against preserve_patterns (if implemented)
        # For now, just check exact matches
        return False

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about orchestration.

        Returns:
            Dictionary with statistics:
            - files_discovered: Number of Python files found
            - total_exports: Number of exported names
            - total_modules: Number of modules
        """
        return {
            "files_discovered": len(self.files),
            "total_exports": self.global_table.get_statistics()["total_exports"],
            "total_modules": self.global_table.get_statistics()["total_modules"],
        }

    def get_file_info(self, module_name: str) -> Optional[FileInfo]:
        """
        Get FileInfo for a module.

        Args:
            module_name: Module name (e.g., "calculator")

        Returns:
            FileInfo if found, None otherwise
        """
        for file_info in self.files:
            if file_info.module_name == module_name:
                return file_info
        return None
