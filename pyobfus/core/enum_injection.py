"""Static preservation plan for enum.global_enum; never import target code."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import List, Optional, Set

from pyobfus.core.import_advisories import enum_members
from pyobfus.core.import_resolution import ImportedAccessVisitor
from pyobfus.exceptions import AnalysisError

_ENUM_BASES = {f"enum.{name}" for name in ("Enum", "IntEnum", "StrEnum", "Flag", "IntFlag")}


@dataclass
class EnumInjection:
    node: ast.ClassDef
    members: List[str]
    reason: Optional[str] = None


@dataclass
class EnumInjectionPlan:
    classes: List[EnumInjection] = field(default_factory=list)
    preserved: Set[str] = field(default_factory=set)
    errors: List[str] = field(default_factory=list)
    preserve_module: bool = False

    def require_static(self) -> None:
        if self.errors:
            raise AnalysisError(
                "Cannot safely obfuscate enum.global_enum injection: "
                + "; ".join(self.errors)
                + ". Use a statically decorated enum with simple member assignments."
            )


def enum_injection_plan(tree: ast.Module) -> EnumInjectionPlan:
    plan = EnumInjectionPlan()

    class Scan(ImportedAccessVisitor):
        def __init__(self):
            super().__init__(
                lambda n: n.module if not n.level else None, lambda n, m: None, self.inspect
            )

        def inspect(self, cls):
            if not any(self.resolve(d) == "enum.global_enum" for d in cls.decorator_list):
                return
            reason = None
            simple = [
                d
                for d in cls.decorator_list
                if isinstance(d, ast.Call) and self.resolve(d.func) == "enum._simple_enum"
            ]
            regular = len(cls.bases) == 1 and self.resolve(cls.bases[0]) in _ENUM_BASES
            converted = (
                not cls.bases
                and len(simple) == 1
                and len(simple[0].args) == 1
                and self.resolve(simple[0].args[0]) in _ENUM_BASES
                and not simple[0].keywords
            )
            if cls.keywords or not (regular or converted):
                reason = "custom bases or metaclass"
            for decorator in cls.decorator_list:
                if decorator in simple:
                    continue
                if self.resolve(decorator) not in {"enum.global_enum", "enum.unique"}:
                    reason = "additional decorator"
            for statement in cls.body:
                if isinstance(statement, (ast.Pass, ast.Expr)):
                    if isinstance(statement, ast.Expr) and not isinstance(
                        statement.value, ast.Constant
                    ):
                        reason = "executable class body"
                    continue
                if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if statement.name != "_missing_":
                        reason = "custom enum method"
                    if any(
                        not (isinstance(d, ast.Name) and d.id == "classmethod")
                        and self.resolve(d) != "builtins.classmethod"
                        for d in statement.decorator_list
                    ):
                        reason = "additional method decorator"
                    plan.preserved.add(statement.name)
                    continue
                if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                    if not all(isinstance(t, ast.Name) for t in targets):
                        reason = "non-simple member target"
                    for target in targets:
                        if isinstance(target, ast.Name):
                            plan.preserved.add(target.id)
                            if target.id == "__module__":
                                reason = "custom enum owner"
                    value = statement.value
                    if value is None:
                        continue
                    try:
                        ast.literal_eval(value)
                    except (ValueError, TypeError):
                        if not (
                            isinstance(value, ast.Call)
                            and self.resolve(value.func) == "enum.auto"
                            and not value.args
                            and not value.keywords
                        ):
                            reason = "computed member value"
                    continue
                reason = "dynamic class body"
            members = enum_members(cls)
            plan.preserved.update(members)
            plan.classes.append(EnumInjection(cls, members, reason))
            if reason:
                plan.errors.append(f"{cls.name} at line {cls.lineno}: {reason}")

        def visit_Call(self, node):
            if self.resolve(node.func) == "enum.global_enum":
                plan.errors.append(f"computed enum owner at line {node.lineno}")
            self.generic_visit(node)

    Scan().visit(tree)
    if plan.classes and any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "__getattr__"
        for n in tree.body
    ):
        plan.preserve_module = True
        # H cannot prove module identity with a runtime attribute fallback.
        # Keep every possible binding spelling, including calendar's ordinary
        # exports, so callers and __all__ remain synchronized without H edits.
        for node in ast.walk(tree):
            for attr in ("id", "arg", "name", "asname", "rest"):
                name = getattr(node, attr, None)
                if isinstance(name, str):
                    plan.preserved.add(name)
    return plan
