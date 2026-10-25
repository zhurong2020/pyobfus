"""End-to-end Pro directory L3 build, retaining Core's ordinary name transforms.

Only this Pro module resolves opacity layers and handles application key
material. Core supplies crypto-free binding metadata, staging, and debugging.
No user module is imported or executed during a build.
"""

from __future__ import annotations

import ast
import base64
import json
import os
import secrets
from dataclasses import asdict, dataclass, replace
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pyobfus.config import ObfuscationConfig
from pyobfus.core.build_report import build_report
from pyobfus.core.build_marker import insert_after_prologue
from pyobfus.core.line_map import shift_line_map
from pyobfus.core.crossfile_opacity import (
    ModulePlan,
    plan_module_targets,
    preflight,
    resolve_correspondence,
)
from pyobfus.core.crossfile_opacity_debug import (
    build_encrypted_code_table,
    build_opacity_report,
    l3_co_filename,
)
from pyobfus.core.mapping import ObfuscationMapping
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus.core.source_prologue import (
    read_python_source,
    restore_source_prologue,
    prologue_line_count,
)
from pyobfus.core.staged_release import StagedRelease, validate_destinations
from pyobfus_pro.crossfile_opacity_adapter import _assert_no_key_leak, encrypt_targets
from pyobfus_pro.opacity.config import OpacityConfig
from pyobfus_pro.opacity.layers import Layer
from pyobfus_pro.opacity.patterns import Resolver

RELEASE_MANIFEST = ".pyobfus-release.json"


@dataclass(repr=False)
class _BuildKey:
    value: bytes

    def __repr__(self) -> str:
        return "<application build key: redacted>"

    def __reduce__(self) -> Any:
        raise TypeError("Application build keys cannot be serialized")


def _require_authorization() -> None:
    from pyobfus.trial import is_trial_active
    from pyobfus_pro.license import get_license_status, verify_license

    if is_trial_active():
        return
    status = get_license_status(masked=False)
    if not status or not status.get("key"):
        raise ValueError("Crossfile opacity requires a valid Pro license or active trial")
    verify_license(status["key"])


def _read_key(env_name: str) -> _BuildKey:
    try:
        key = base64.b64decode(os.environ[env_name], validate=True)
    except (KeyError, ValueError, TypeError):
        raise ValueError("Application key must be set as base64-encoded 32 bytes") from None
    if len(key) != 32:
        raise ValueError("Application key must decode to exactly 32 bytes")
    return _BuildKey(key)


def _functions(tree: ast.AST, prefix: str = "") -> List[Tuple[str, ast.AST]]:
    result: List[Tuple[str, ast.AST]] = []
    for child in ast.iter_child_nodes(tree):
        scope = prefix
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            scope = f"{prefix}.{child.name}" if prefix else child.name
            result.append((scope, child))
        result.extend(_functions(child, scope))
    return result


def _select(module: str, source: str, opacity: OpacityConfig) -> Tuple[ModulePlan, List[str], int]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "pyobfus_pro":
            raise ValueError(
                "Pro builder imports/markers are unsupported; use TOML and runtime API"
            )
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[0] == "pyobfus_pro" for alias in node.names
        ):
            raise ValueError("Pro builder imports are unsupported in protected applications")
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
            called = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            if called in ("__import__", "import_module") and node.args:
                arg = node.args[0]
                if (
                    isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)
                    and (arg.value.split(".")[0] == "pyobfus_pro")
                ):
                    raise ValueError("Literal dynamic Pro builder imports are unsupported")
        if (
            isinstance(node, ast.Name)
            and node.id in ("__getattr__", "__lazy_modules__")
            and (isinstance(node.ctx, ast.Store))
        ):
            raise ValueError("Dynamic module exports and whole-module lazy policy are unsupported")
    if any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (node.name == "__getattr__")
        for node in tree.body
    ):
        raise ValueError("Dynamic module exports are unsupported")

    plan = plan_module_targets(module, source)
    resolver = Resolver(opacity)
    eligible = {(b.name, b.lineno): b for b in plan.selected}
    reasons = {(r.name, r.lineno): r.reason for r in plan.rejected}
    targets, qualnames = [], []
    for name, node in _functions(tree):
        qualified = f"{module}.{name}"
        qualnames.append(qualified)
        if resolver.resolve(qualified) is not Layer.ENCRYPTED:
            continue
        identity = (name, getattr(node, "lineno", 0))
        if identity not in eligible:
            raise ValueError(
                f"Requested encrypted target {qualified} is unsupported: "
                f"{reasons.get(identity, 'not an unconditional top-level function')}"
            )
        targets.append(eligible[identity])
    return replace(plan, selected=tuple(targets)), qualnames, len(plan.selected)


def build_directory(
    input_dir: Path,
    output: Path,
    config: ObfuscationConfig,
    *,
    mapping_path: Path,
    report_path: Path | None,
    plan: Dict[str, Any],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Build and publish a fresh directory, or validate without writing in dry-run."""
    preflight(config, cross_file=True, input_is_dir=input_dir.is_dir())
    _require_authorization()  # also protects YAML/preset/API callers
    metadata = {"mapping.json": mapping_path}
    if report_path is not None:
        metadata["report.json"] = report_path
    validate_destinations(input_dir, output, metadata.values())
    key = _read_key(config.bind_key_env or "")
    opacity = OpacityConfig.from_toml(Path(config.opacity_config or ""))
    orchestrator = CrossFileOrchestrator(config)
    orchestrator.phase1_scan(input_dir)
    preflight(
        config,
        cross_file=True,
        input_is_dir=True,
        module_names=(f.module_name for f in orchestrator.files),
    )
    if orchestrator.module_attribute_accesses_unproved:
        raise ValueError(
            "Crossfile opacity refuses unproved project module attribute accesses; "
            "run --check and use exclude_names for the referenced exports"
        )
    selected = {}
    qualified_names: List[str] = []
    eligible_count = 0
    for file in orchestrator.files:
        selected[file.module_name], names, eligible = _select(
            file.module_name, read_python_source(file.path), opacity
        )
        qualified_names.extend(names)
        eligible_count += eligible
    count = sum(len(p.selected) for p in selected.values())
    if not count:
        raise ValueError("Opacity selection contains no eligible encrypted targets")
    warnings = list(orchestrator.planning_warnings)
    for rule in opacity.rules:
        if not any(fnmatchcase(name, rule.pattern) for name in qualified_names):
            warnings.append(
                "An opacity rule matched no functions; inspect private selection config"
            )
    warnings.append(
        "Register the application key provider outside the protected package before import; "
        "package __init__ and spawn initializers can import protected modules early. "
        "Encrypted frames restore names only; ordinary frames in L3 modules may remain unchanged."
    )
    stats: Dict[str, Any] = {
        "files_processed": 0 if dry_run else len(orchestrator.files),
        "encrypted_targets": count,
        "warnings": warnings,
    }
    if dry_run:
        return {"stats": stats, "build_id": None}
    build_id = secrets.token_hex(16)
    mapping = ObfuscationMapping.from_global_table(orchestrator.global_table, root=str(input_dir))
    table_entries = []
    private_targets = []
    with StagedRelease(output, metadata, build_id) as stage:
        errors = orchestrator.phase2_transform(input_dir, stage.app)
        if errors:
            # Transformer errors can contain source text. Keep failure diagnostics bounded.
            raise ValueError("Core transformation failed; no protected application was published")
        mapping.files = orchestrator.file_line_maps
        encrypted_files = []
        for file in orchestrator.files:
            file_key = file.relative_path.as_posix()
            destination = stage.app / file.relative_path
            source = read_python_source(destination)
            module_plan = selected[file.module_name]
            if module_plan.selected:
                code_filename = l3_co_filename(build_id, file_key)
                correspondence = resolve_correspondence(module_plan, mapping)
                result = encrypt_targets(
                    source,
                    (b.final_name for b in correspondence.resolved),
                    key=key.value,
                    env_name=config.bind_key_env or "",
                    filename=file_key,
                    code_filename=code_filename,
                    interpreter_guard=True,
                )
                source = restore_source_prologue(source, result.source)
                for item in correspondence.resolved:
                    table_entries.append((code_filename, item.final_name, item.binding.name))
                    private_targets.append({"file": file_key, **asdict(item)})
                record = mapping.files.get(file_key)
                if record is not None:
                    record["lines"] = None
                    record["reason"] = "crossfile_l3_no_line_table"
                encrypted_files.append(file_key)
            insertion = prologue_line_count(source)
            source = insert_after_prologue(source, f"# pyobfus:l3-build {build_id}\n")
            record = mapping.files.get(file_key)
            if record is not None:
                shift_line_map(record, insertion, 1)
                record["line_count"] = len(source.splitlines())
            compile(source, file_key, "exec", dont_inherit=True)
            _assert_no_key_leak(source, key.value)
            destination.write_text(source, encoding="utf-8")
        mapping.encrypted_code = build_encrypted_code_table(table_entries)
        mapping.opacity_plan = {"build_id": build_id, "targets": private_targets}
        opacity_report = build_opacity_report(
            artifact_id=build_id,
            env_name=config.bind_key_env or "",
            eligible=eligible_count,
            encrypted=count,
            rejected_reasons=(r.reason for p in selected.values() for r in p.rejected),
        )
        report = build_report(
            plan=plan,
            output_path=stage.app,
            stats={k: v for k, v in stats.items() if isinstance(v, int)},
            verification={"syntax_valid": True, "execution_performed": False},
            provenance_manifest_path=None,
            cwd=Path.cwd(),
        )
        report["opacity"] = opacity_report
        report["build_id"] = build_id
        manifest = {
            "format": "pyobfus-l3-release",
            "version": 1,
            "state": "completed",
            "build_id": build_id,
            "files": report["outputs"]["files"],
            "encrypted_files": encrypted_files,
        }
        (stage.app / RELEASE_MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
        (stage.root / "mapping.json").write_text(mapping.to_json(), encoding="utf-8")
        if report_path is not None:
            (stage.root / "report.json").write_text(json.dumps(report), encoding="utf-8")
        for path in stage.root.rglob("*"):
            if path.is_file():
                _assert_no_key_leak(path.read_text(encoding="utf-8"), key.value)
        # Completion is checked independently by the Community delivery checker.
        from pyobfus.core.delivery_check import check_delivery

        checked = check_delivery(stage.app)
        if checked["status"] == "fail":
            raise ValueError("Staged delivery validation failed")
        stage.commit()
    return {"stats": stats, "build_id": build_id}
