"""
Cross-file Obfuscation Orchestrator.

This module provides the CrossFileOrchestrator class which coordinates
the two-phase obfuscation process for multi-file projects.
"""

import ast
import os
import stat
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from pyobfus.config import ObfuscationConfig
from pyobfus.core.class_bindings import mark_class_bindings
from pyobfus.core.enum_injection import enum_injection_plan
from pyobfus.core.function_locals import LocalPlan, plan_locals, apply_local_plan
from pyobfus.core import content_transforms
from pyobfus.core.module_attributes import (
    AttributePlan,
    inspect_unproved_accesses,
    ModuleInventory,
    plan_attributes,
    apply_attribute_plan,
)
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
from pyobfus.core.star_imports import plan_stars, expand_stars
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
from pyobfus.transformers.scoped_imports import ScopeResolutionError
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
    attribute_plan: Optional[AttributePlan] = None,
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
        if config is not None and config.crossfile_module_attributes:
            if attribute_plan is None:
                raise ValueError("Missing module attribute plan")
            apply_attribute_plan(tree, source, relative_path.as_posix(), attribute_plan)
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

        expand_stars(original_tree, global_table.star_import_plans.get(module_name, {}))
        expand_stars(tree, global_table.star_import_plans.get(module_name, {}))

        # Collect imported names from original tree
        import_collector = ImportCollector(global_table, module_name)
        import_collector.visit(original_tree)
        # ImportedNameTransformer marks references to their actual imported
        # binding. A flat union is unsafe: a class-only import can suppress
        # rewriting a same-spelled module export after class-body `del`.
        imported_names: Set[str] = set()

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
            preserved_imports=import_collector.preserved_imports,
        )
        tree = import_rewriter.visit(tree)

        imported_name_transformer = ImportedNameTransformer(
            original_tree,
            global_table,
            module_name,
            file_path,
            collector=import_collector,
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

        from pyobfus.core.fstring_compat import ensure_fstring_compatibility

        ensure_fstring_compatibility(source, new_source, str(file_path))
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
        self.attribute_plans: Dict[str, AttributePlan] = {}
        self.attribute_inventory: Optional[ModuleInventory] = None
        self.module_attribute_accesses_unproved = 0
        self.local_plans: Dict[str, LocalPlan] = {}
        self._reserved_names: Set[str] = set()
        self._planning_warnings: List[str] = []
        self._preserved_unproved_names: Set[str] = set()

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
            self._preserved_unproved_names = set()
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

    def phase1_scan(self, input_dir: Path, _preservation_pass: bool = False) -> GlobalSymbolTable:
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
        self.attribute_plans = {}
        self.attribute_inventory = None
        self._planning_warnings = []
        self._reserved_names = set()
        self._reserved_names.update(self._preserved_unproved_names)

        # 1. Discover files
        self.files = self._discover_files(input_dir)

        if self.config.crossfile_local_names:
            self._reserved_names.update(self.config.exclude_names)
        enum_package_fallbacks: Set[Path] = set()
        for fi in self.files:
            tree = ASTParser.parse_file(fi.path)
            injection = enum_injection_plan(tree)
            self._reserved_names.update(injection.preserved)
            if injection.errors and fi.relative_path.name == "__init__.py":
                enum_package_fallbacks.add(fi.relative_path.parent)
            if injection.preserve_module:
                self.global_table.conservative_import_modules.add(fi.module_name)
                self._planning_warnings.append(
                    f"Preserved module names and import bindings for {fi.relative_path.as_posix()}: "
                    f"{injection.warning}"
                )
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

        if not self.config.crossfile_local_names and self.global_table.conservative_import_modules:
            # An unknown injected spelling may occur only in a consumer import.
            # Reserving owner names alone lets a generated I0 definition capture
            # `from owner import I0`. Keep allocation clear of consumer bindings
            # and references even when function-local renaming is disabled.
            for fi in self.files:
                for node in ast.walk(ASTParser.parse_file(fi.path)):
                    for attr in ("id", "arg", "name", "asname", "rest"):
                        value = getattr(node, attr, None)
                        if isinstance(value, str):
                            self._reserved_names.add(value)

        # A non-static injection in a package initializer can observe its
        # sibling modules through module attributes and star-import chains.
        # Preserve that package's names together: otherwise the initializer's
        # fallback alone leaves dependencies (notably re._constants) renamed.
        # This is scoped to enum packages, not general star-import resolution.
        for fi in self.files:
            if any(parent in fi.relative_path.parents for parent in enum_package_fallbacks):
                self.global_table.conservative_import_modules.add(fi.module_name)
                self._planning_warnings.append(
                    f"Preserved all module names and import bindings for {fi.relative_path.as_posix()}: "
                    "non-static enum injection in package initializer"
                )
                for node in ast.walk(ASTParser.parse_file(fi.path)):
                    for attr in ("id", "arg", "name", "asname", "rest"):
                        value = getattr(node, attr, None)
                        if isinstance(value, str):
                            self._reserved_names.add(value)
        # Plan stars after enum fallbacks, before registering any exports.
        # Unknown star namespaces preserve globals; known expansions still need
        # the enum identity mappings when re-export chains resolve below.
        sources = {fi.module_name: read_python_source(fi.path) for fi in self.files}
        star_plans, unknown_stars = plan_stars(sources)
        self.global_table.star_import_plans = star_plans
        self._preserve_star_globals = unknown_stars
        if unknown_stars:
            self._planning_warnings.append(
                "Preserved project global names: an internal wildcard import has "
                "a dynamic, conditional, external-derived, or cyclic export namespace."
            )

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

            expand_stars(tree, star_plans[file_info.module_name])
            star_bindings = {
                name for names in star_plans[file_info.module_name].values() for name in names
            }
            detector = ExportDetector(overridden_imports=star_bindings)
            detector.visit(tree)
            injection = enum_injection_plan(tree)
            exports = detector.get_exports() | set(
                name for cls in injection.classes for name in cls.members
            )
            # __all__ controls wildcard visibility, not explicit importability.
            # Every binding introduced by an expanded star needs a table entry,
            # including private names and names omitted from the shim's __all__.
            exports.update(star_bindings)

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
                if (
                    export_name in injection.preserved
                    or file_info.module_name in self.global_table.conservative_import_modules
                ):
                    self.global_table.register_preserved_export(file_info.module_name, export_name)
                    continue
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

        # Prove import scopes before local and attribute plans are allocated.
        # A compiler shape we do not understand must reduce protection rather
        # than fail an otherwise valid project or guess reference ownership.
        for fi in self.files:
            try:
                ImportCollector(self.global_table, fi.module_name).visit(
                    expand_stars(ast.parse(read_python_source(fi.path)), star_plans[fi.module_name])
                )
            except ScopeResolutionError as exc:
                self.global_table.conservative_import_modules.add(fi.module_name)
                for name in self.global_table.get_module_exports(fi.module_name):
                    self.global_table.register_reexport(fi.module_name, name, name)
                self._planning_warnings.append(
                    f"Preserved module names and import bindings for {fi.relative_path.as_posix()}: {exc}"
                )
        if self.global_table.conservative_import_modules:
            # Consumers and re-export chains must see the preserved public names.
            for _ in range(len(pending_reexports) + 1):
                self._register_reexports(
                    [
                        entry
                        for entry in pending_reexports
                        if entry[0].module_name not in self.global_table.conservative_import_modules
                    ]
                )

        if self.config.crossfile_local_names:
            for fi in sorted(self.files, key=lambda f: f.relative_path.as_posix()):
                if fi.module_name in self.global_table.conservative_import_modules:
                    self.local_plans[fi.module_name] = LocalPlan(files_skipped=1)
                    continue
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

        # Observation runs for opt-out builds too; it never supplies edits.
        sources = {fi.module_name: read_python_source(fi.path) for fi in self.files}
        file_index = {fi.module_name: fi for fi in self.files}
        inventory = ModuleInventory(
            sources,
            lambda module, node: self._resolve_source_module(
                file_index[module], ReExportSource(node.module, node.level, "")
            ),
            self.global_table,
        )
        if self.config.crossfile_module_attributes:
            self.attribute_inventory = inventory
        self.attribute_plans = (
            {
                fi.module_name: plan_attributes(
                    sources[fi.module_name],
                    fi.relative_path.as_posix(),
                    fi.module_name,
                    inventory,
                    self.global_table,
                )
                for fi in self.files
            }
            if self.config.crossfile_module_attributes
            else {}
        )
        self.module_attribute_accesses_unproved, unproved_names = inspect_unproved_accesses(
            sources, inventory, self.global_table, self.attribute_plans
        )
        if self.config.preserve_unproved_module_attributes and unproved_names:
            if _preservation_pass:
                raise ValueError("Unproved module attribute preservation did not stabilize")
            self._preserved_unproved_names.update(unproved_names)
            return self.phase1_scan(input_dir, _preservation_pass=True)
        if self._preserved_unproved_names:
            self._planning_warnings.append(
                "Preserved unproved module attribute names: "
                + ", ".join(sorted(self._preserved_unproved_names))
            )

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
        self, input_dir: Path, output_dir: Path, progress_callback=None
    ) -> List[str]:
        """Attribute-rewriting builds stage output until every plan succeeds."""
        if not self.config.crossfile_module_attributes:
            return self._phase2_transform(input_dir, output_dir, progress_callback)
        output_dir = Path(output_dir)
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".pyobfus-attributes-", dir=output_dir.parent
        ) as temporary:
            staging = Path(temporary)
            errors = self._phase2_transform(input_dir, staging, progress_callback)
            if errors:
                self.file_line_maps = {}
                return errors
            for fi in self.files:
                destination = output_dir / fi.relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                staged = staging / fi.relative_path
                if os.name != "nt" and destination.exists():
                    # Replacing a staged inode must preserve the existing
                    # output's read/write bits, just like the legacy writer.
                    staged.chmod(stat.S_IMODE(destination.stat().st_mode))
                    copy_executable_bits(fi.path, staged)
                os.replace(staged, destination)
        return []

    def _phase2_transform(
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
                        self.attribute_plans.get(fi.module_name),
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
                    self.attribute_plans.get(file_info.module_name),
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
        python_files = filter_python_files(
            input_dir,
            self.config.exclude_patterns,
            skip_environment_dirs=self.config.skip_environment_dirs,
        )

        file_infos = []
        # A package supplied as the input directory may be imported by its
        # package name or used as a flat script root. An __init__.py alone is
        # insufficient: examples/multifile has one, but its main script uses
        # flat sibling imports. Prefix only the unambiguous package form.
        package_root = None
        if (input_dir / "__init__.py").is_file():
            siblings = {
                path.stem
                for path in python_files
                if path.parent == input_dir and path.stem != "__init__"
            }
            package_import = False
            flat_import = False
            for path in python_files:
                for node in ast.walk(ASTParser.parse_file(path)):
                    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        package_import |= node.module.split(".")[0] == input_dir.name
                        flat_import |= node.module.split(".")[0] in siblings
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            package_import |= alias.name.split(".")[0] == input_dir.name
                            flat_import |= alias.name.split(".")[0] in siblings
            if package_import and not flat_import:
                package_root = input_dir.name
        for file_path in python_files:
            # Calculate relative path
            relative_path = file_path.relative_to(input_dir)

            # Calculate module name (e.g., "utils/helpers.py" -> "utils.helpers")
            module_name = self._path_to_module_name(relative_path)
            if package_root:
                module_name = f"{package_root}.{module_name}"

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
        if (
            getattr(self, "_preserve_star_globals", False)
            or name in self.config.exclude_names
            or name in self._preserved_unproved_names
        ):
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
            "module_attribute_accesses_unproved": self.module_attribute_accesses_unproved,
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
