"""
Cross-file Obfuscation Orchestrator.

This module provides the CrossFileOrchestrator class which coordinates
the two-phase obfuscation process for multi-file projects.
"""

import ast
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from pyobfus.config import ObfuscationConfig
from pyobfus.core.class_bindings import mark_class_bindings
from pyobfus.core.function_locals import LocalPlan, plan_locals, apply_local_plan
from pyobfus.core import content_transforms
from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.core.export_detector import ExportDetector, ReExportSource
from pyobfus import __version__
from pyobfus.core.build_marker import apply_marker, marker_enabled
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.source_prologue import (
    read_python_source,
    restore_source_prologue,
    copy_executable_bits,
)
from pyobfus.core.parser import ASTParser
from pyobfus.core.line_map import build_line_map, mark_source_statements
from pyobfus.transformers.import_rewriter import ImportRewriter
from pyobfus.transformers.all_list_updater import AllListUpdater
from pyobfus.transformers.exported_name_transformer import ExportedNameTransformer
from pyobfus.transformers.imported_name_transformer import (
    ImportedNameTransformer,
    ImportCollector,
)
from pyobfus.transformers.local_name_transformer import LocalNameTransformer
from pyobfus.utils import filter_python_files


def _transform_single_file(
    file_path: Path,
    relative_path: Path,
    module_name: str,
    input_dir: Path,
    output_dir: Path,
    global_table: "GlobalSymbolTable",
    config: Optional[ObfuscationConfig] = None,
    local_plan: Optional[LocalPlan] = None,
) -> Tuple[str, Optional[str], Dict[str, int], Optional[Dict[str, Any]]]:
    """
    Transform a single file using the global symbol table.

    This is a module-level function so it can be used with ProcessPoolExecutor.

    Applies the cross-file name/import mapping AND — when ``config`` is given —
    the shared per-file content transforms (AI-marker stripping, string
    encoding, numeric obfuscation, and the Pro block) via
    :mod:`pyobfus.core.content_transforms`, so directory mode matches
    single-file mode instead of silently dropping those transforms.

    Returns:
        Tuple of (module_name, error_message_or_None, per_file_stats, line_map_record)
    """
    file_stats: Dict[str, int] = {}
    try:
        source = read_python_source(file_path)

        original_tree = ast.parse(source)
        tree = ast.parse(source)
        mark_source_statements(tree)
        mark_class_bindings(tree)
        if local_plan is not None:
            tree = apply_local_plan(tree, local_plan)
            file_stats["local_names_obfuscated"] = len(local_plan.mappings)
            file_stats["local_functions_skipped"] = local_plan.skipped
            file_stats["local_files_skipped"] = local_plan.files_skipped

        # Strip AI provenance markers BEFORE name mangling, so the stripper
        # sees the original docstrings and attribution dunder names (matches
        # the single-file transform order).
        if config is not None:
            tree = content_transforms.strip_ai_markers(tree, config, None, file_stats)
            tree = content_transforms.remove_docstrings(tree, config)

        # Collect imported names from original tree
        import_collector = ImportCollector(global_table, module_name)
        import_collector.visit(original_tree)
        imported_names = set(import_collector.import_mappings.keys())

        # Apply transformers in order
        exported_name_transformer = ExportedNameTransformer(
            global_table,
            module_name,
            file_path,
        )
        tree = exported_name_transformer.visit(tree)

        import_rewriter = ImportRewriter(
            global_table,
            module_name,
            file_path,
        )
        tree = import_rewriter.visit(tree)

        imported_name_transformer = ImportedNameTransformer(
            original_tree,
            global_table,
            module_name,
            file_path,
        )
        tree = imported_name_transformer.visit(tree)

        local_name_transformer = LocalNameTransformer(
            global_table,
            module_name,
            imported_names,
            file_path,
        )
        tree = local_name_transformer.visit(tree)

        all_updater = AllListUpdater(
            global_table,
            module_name,
            file_path,
        )
        tree = all_updater.visit(tree)

        # Post-mangle content transforms (string encoding, numeric, Pro block).
        # Shared with the single-file path so the two modes cannot diverge.
        if config is not None:
            tree = content_transforms.apply_content_transforms(tree, config, None, file_stats)

        ast.fix_missing_locations(tree)
        new_source = restore_source_prologue(source, CodeGenerator.generate(tree))

        # Transparent build marker. `relative_path` is already project-relative,
        # so no absolute build path can reach the shipped file.
        if config is None or marker_enabled(getattr(config, "community_marker", "auto")):
            new_source = apply_marker(
                new_source,
                tool_version=__version__,
                edition=getattr(config, "level", "community") if config else "community",
                source_label=Path(relative_path).as_posix(),
            )

        output_file = output_dir / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_source)
        copy_executable_bits(file_path, output_file)

        record = build_line_map(tree, new_source, relative_path.as_posix(), module_name)
        return (module_name, None, file_stats, record)
    except Exception as e:
        return (module_name, str(e), file_stats, None)


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

        # Aggregated per-file content-transform stats from phase2 (string
        # encoding, numeric, control-flow, string encryption, anti-debug,
        # dead-code, AI-marker stripping). Populated by phase2_transform.
        self.content_stats: Dict[str, int] = {}
        self.file_line_maps: Dict[str, Dict[str, Any]] = {}
        self.local_plans: Dict[str, LocalPlan] = {}
        self._reserved_names: Set[str] = set()
        self._planning_warnings: List[str] = []

    @property
    def planning_warnings(self) -> List[str]:
        """Warnings from the most recent scan, including skipped local plans."""
        return list(self._planning_warnings)

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
            warnings.extend(self._planning_warnings)

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
            transform_errors = self.phase2_transform(input_dir, output_dir)
            errors.extend(transform_errors)

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
        # A repeated build on the same orchestrator starts a fresh plan.
        self.global_table = GlobalSymbolTable()
        self._name_counter = 0
        self.local_plans = {}
        self._planning_warnings = []
        self._reserved_names = set()

        # 1. Discover files
        self.files = self._discover_files(input_dir)

        if self.config.crossfile_local_names:
            self._reserved_names.update(self.config.exclude_names)
        for fi in self.files:
            tree = ASTParser.parse_file(fi.path)
            for node in ast.walk(tree):
                # Explicit aliases survive even when local renaming is off;
                # newly allocated definitions must not collide with them.
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    self._reserved_names.update(a.asname for a in node.names if a.asname)
                if self.config.crossfile_local_names:
                    # A preserved parameter I42 must never capture a new I42.
                    for attr in ("id", "arg", "name", "asname", "rest"):
                        value = getattr(node, attr, None)
                        if isinstance(value, str):
                            self._reserved_names.add(value)

        # 2. Detect exports once per file, then register in two passes.
        #
        # A name a module re-exports (`from .core import run` plus `run` in
        # __all__) must keep the obfuscated name of the module that defines
        # it. Minting a fresh one made the package advertise an identifier
        # that existed nowhere, so `from pkg import *` and any consumer
        # reading __all__ broke. Definitions therefore get their names first,
        # and re-exports are resolved against them afterwards.
        pending_reexports: List[Tuple[FileInfo, str, ReExportSource]] = []

        for file_info in self.files:
            tree = ASTParser.parse_file(file_info.path)

            detector = ExportDetector()
            detector.visit(tree)
            exports = detector.get_exports()

            # Update file_info
            file_info.exports = exports

            # A package's exports are registered under its __init__ module
            # name, but consumers import them from the package itself.
            if file_info.module_name.endswith(".__init__"):
                self.global_table.register_module_alias(
                    alias=file_info.module_name[: -len(".__init__")],
                    target=file_info.module_name,
                )
            elif file_info.module_name == "__init__":
                self.global_table.register_module_alias(alias="", target=file_info.module_name)

            # Pass 1 registers definitions. Sorted, not raw set order:
            # `exports` is a set, so iterating it directly assigns I0/I1/... in
            # an order that changes with the interpreter's string hash seed.
            # That made the generated bytes differ between two runs of the same
            # input, which in turn made the output digests in --build-report
            # and --provenance-manifest impossible for anyone else to
            # reproduce.
            for export_name in sorted(exports):
                # Skip names that should be preserved
                if self._should_preserve_name(export_name):
                    continue

                source = detector.imported_from.get(export_name)
                if source is not None and source.has_explicit_alias:
                    # `from M import X as A` exports the local binding A, not
                    # M's renamed X. Consumers and __all__ must retain A too.
                    continue
                if source is not None and source.is_module_binding:
                    # A module bound by `import x`: the import statement keeps
                    # the real module name, so this name must keep it too.
                    continue
                if source is not None:
                    # Defined elsewhere; resolved in pass 2.
                    pending_reexports.append((file_info, export_name, source))
                    continue

                # Generate obfuscated name
                obfuscated_name = self._generate_obfuscated_name()

                # Register in global table
                self.global_table.register_export(
                    module=file_info.module_name,
                    original_name=export_name,
                    obfuscated_name=obfuscated_name,
                )

        self._register_reexports(pending_reexports)

        if self.config.crossfile_local_names:
            for fi in sorted(self.files, key=lambda f: f.relative_path.as_posix()):
                local_source = read_python_source(fi.path)
                counter = self._name_counter
                reserved = set(self._reserved_names)
                try:
                    plan = plan_locals(
                        local_source,
                        self.config,
                        self._generate_obfuscated_name,
                        self.global_table.get_module_exports(fi.module_name),
                        fi.relative_path.as_posix(),
                    )
                except (ValueError, SyntaxError, RecursionError) as exc:
                    # Discard partial local allocations. The existing module
                    # transformation can still run without a local-name plan.
                    # SyntaxError covers compile-time checks (for example a late
                    # `global`) that ast.parse accepts but symtable rejects.
                    self._name_counter = counter
                    self._reserved_names = reserved
                    plan = LocalPlan(
                        skipped=sum(
                            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                            for n in ast.walk(ast.parse(local_source))
                        ),
                        files_skipped=1,
                    )
                    self._planning_warnings.append(
                        f"Skipped function-local renaming for {fi.relative_path.as_posix()}: {exc}"
                    )
                self.local_plans[fi.module_name] = plan
                self.global_table.local_mappings[fi.module_name] = plan.mappings

        return self.global_table

    def _register_reexports(self, pending: List[Tuple[FileInfo, str, ReExportSource]]) -> None:
        """Give each re-exported name the obfuscated name of its definition.

        Re-exports can chain (``pkg`` re-exports from ``pkg.api``, which
        re-exports from ``pkg.core``), and a chain can be registered in any
        order, so this repeats until nothing new resolves.

        A name whose source is not part of this project — ``from requests
        import Session`` — is left unregistered on purpose. It belongs to a
        package pyobfus does not rewrite, so renaming it here would break the
        import it came from.
        """
        remaining = list(pending)

        while remaining:
            unresolved: List[Tuple[FileInfo, str, ReExportSource]] = []
            for file_info, export_name, source in remaining:
                source_module = self._resolve_source_module(file_info, source)
                obfuscated_name = (
                    self.global_table.get_obfuscated_import(source_module, source.original_name)
                    if source_module
                    else None
                )

                if obfuscated_name is None:
                    unresolved.append((file_info, export_name, source))
                    continue

                self.global_table.register_reexport(
                    module=file_info.module_name,
                    original_name=export_name,
                    obfuscated_name=obfuscated_name,
                )

            if len(unresolved) == len(remaining):
                # Nothing resolved this round: the rest point outside the
                # project (or at names that are preserved), so leave them.
                break
            remaining = unresolved

    def _resolve_source_module(self, file_info: FileInfo, source: ReExportSource) -> Optional[str]:
        """Turn the module in an import statement into an absolute module name."""
        if source.level == 0:
            return source.module

        parts = file_info.module_name.split(".")
        # Inside pkg/__init__.py the module name already ends in `__init__`,
        # so one dot correctly drops that component and lands on the package.
        if source.level > len(parts):
            return None

        parent_parts = parts[: -source.level]
        if source.module:
            parent_parts.append(source.module)

        return ".".join(parent_parts) if parent_parts else None

    def phase2_transform(
        self,
        input_dir: Path,
        output_dir: Path,
        progress_callback: Any = None,
    ) -> List[str]:
        """
        Phase 2: Transform all files (supports parallel processing).

        Uses global symbol table to:
        1. Rename exported definitions (class Calculator -> class I0)
        2. Rewrite import statements using global mappings
        3. Update references to imported names (Calculator() -> I0())
        4. Update __all__ lists with obfuscated names
        5. Generate obfuscated output files

        Args:
            input_dir: Source directory
            output_dir: Output directory
            progress_callback: Optional callable(module_name, error_or_none) for progress

        Returns:
            List of error messages (empty if all successful)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        errors: List[str] = []
        self.content_stats = {}
        self.file_line_maps = {}

        max_workers = self.config.max_workers
        use_parallel = max_workers != 1 and len(self.files) > 1

        if use_parallel:
            workers = max_workers or min(os.cpu_count() or 1, len(self.files))
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(
                        _transform_single_file,
                        fi.path,
                        fi.relative_path,
                        fi.module_name,
                        input_dir,
                        output_dir,
                        self.global_table,
                        self.config,
                        self.local_plans.get(fi.module_name),
                    ): fi
                    for fi in self.files
                }
                for future in as_completed(futures):
                    module_name, error, file_stats, record = future.result()
                    if record is not None:
                        self.file_line_maps[futures[future].relative_path.as_posix()] = record
                    self._accumulate_content_stats(file_stats)
                    if error:
                        errors.append(f"{module_name}: {error}")
                    if progress_callback:
                        progress_callback(module_name, error)
        else:
            for file_info in self.files:
                module_name, error, file_stats, record = _transform_single_file(
                    file_info.path,
                    file_info.relative_path,
                    file_info.module_name,
                    input_dir,
                    output_dir,
                    self.global_table,
                    self.config,
                    self.local_plans.get(file_info.module_name),
                )
                if record is not None:
                    self.file_line_maps[file_info.relative_path.as_posix()] = record
                self._accumulate_content_stats(file_stats)
                if error:
                    errors.append(f"{module_name}: {error}")
                if progress_callback:
                    progress_callback(module_name, error)

        return errors

    def _accumulate_content_stats(self, file_stats: Dict[str, int]) -> None:
        """Sum per-file content-transform counts into ``self.content_stats``.

        Skips private bookkeeping keys (leading underscore, e.g.
        ``_pro_import_error``) and any non-numeric values.
        """
        for key, value in file_stats.items():
            if key.startswith("_") or not isinstance(value, int):
                continue
            self.content_stats[key] = self.content_stats.get(key, 0) + value

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
            if not self.global_table.is_name_used(name) and name not in self._reserved_names:
                self._reserved_names.add(name)
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
            "total_local_names": sum(len(p.mappings) for p in self.local_plans.values()),
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
