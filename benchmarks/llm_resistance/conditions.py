"""Obfuscation conditions (the C0-C5 ladder) for the LLM-resistance benchmark.

Each condition turns a clean corpus sample's source into the artifact an LLM
attacker will see. Every condition is a real ``pyobfus`` CLI invocation so the
ladder is reproducible from a pip install; C4/C5 additionally inject the Pro L3
markers (``@opacity`` / ``vault_secrets``) the sample was tagged eligible for.

See ``docs/LLM_RESISTANCE_BENCHMARK.md`` for the design rationale.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Condition:
    """One rung of the ladder."""

    cid: str
    name: str
    # Extra CLI flags appended after ``--preset <preset>``.
    flags: tuple[str, ...]
    preset: str
    # "core" (plain command) vs the Pro L3 markers this condition requires.
    requires: str  # "" | "opacity" | "vault"
    # cid of the condition this one additively builds on, or "" if it doesn't
    # (C4/C5 use a different preset entirely, so they are not comparable to
    # C3). Used to auto-detect a no-op transform (e.g. --string-encryption on
    # a sample with no string literals) before spending an attacker call.
    builds_on: str = ""


CONDITIONS: tuple[Condition, ...] = (
    Condition("C0", "plaintext (control)", (), "", ""),
    Condition("C1", "core mangling", (), "aggressive", ""),
    Condition(
        "C2", "+ string encryption", ("--string-encryption",), "aggressive", "", builds_on="C1"
    ),
    Condition(
        "C3",
        "+ control-flow flattening",
        ("--string-encryption", "--control-flow"),
        "aggressive",
        "",
        builds_on="C2",
    ),
    Condition("C4", "Pro L3 opacity", ("--selective-opacity",), "maximum", "opacity"),
    Condition("C5", "Pro L3 vault", ("--vault",), "maximum", "vault"),
)


class ConditionError(RuntimeError):
    """Raised when a condition cannot be produced for a sample."""


def eligible(condition: Condition, meta: dict) -> bool:
    """Whether this sample can be run under this condition."""
    if condition.requires == "opacity":
        return bool(meta.get("c4_eligible"))
    if condition.requires == "vault":
        return bool(meta.get("c5_eligible"))
    return True


def obfuscate(condition: Condition, source: str, meta: dict) -> str:
    """Return the obfuscated artifact text for ``source`` under ``condition``.

    Raises ConditionError if pyobfus fails or the sample is ineligible.
    """
    if not eligible(condition, meta):
        raise ConditionError(f"{meta.get('name', '?')} is not eligible for {condition.cid}")

    if condition.cid == "C0":
        return source

    prepared = source
    if condition.requires == "opacity":
        prepared = _inject_opacity_marker(source, meta["c4_target"])
    elif condition.requires == "vault":
        prepared = _inject_vault_marker(source, meta["c5_secret_var"])

    return _run_pyobfus(prepared, condition)


def _run_pyobfus(source: str, condition: Condition) -> str:
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        src = tdp / "sample.py"
        out = tdp / "out.py"
        src.write_text(source, encoding="utf-8")
        cmd = [sys.executable, "-m", "pyobfus", str(src), "-o", str(out)]
        if condition.preset:
            cmd += ["--preset", condition.preset]
        cmd += list(condition.flags)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if proc.returncode != 0 or not out.exists():
            raise ConditionError(
                f"pyobfus failed for {condition.cid}: rc={proc.returncode}\n"
                f"cmd: {' '.join(cmd)}\nstderr: {proc.stderr[-800:]}"
            )
        return out.read_text(encoding="utf-8")


def _inject_opacity_marker(source: str, target: str) -> str:
    """Add ``@opacity(Layer.ENCRYPTED)`` to ``target`` and import the symbols."""
    tree = ast.parse(source)
    found = False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target:
            node.decorator_list.insert(
                0,
                ast.Call(
                    func=ast.Name(id="opacity", ctx=ast.Load()),
                    args=[
                        ast.Attribute(
                            value=ast.Name(id="Layer", ctx=ast.Load()),
                            attr="ENCRYPTED",
                            ctx=ast.Load(),
                        )
                    ],
                    keywords=[],
                ),
            )
            found = True
            break
    if not found:
        raise ConditionError(f"opacity target function {target!r} not found in sample")
    imp = ast.ImportFrom(
        module="pyobfus_pro",
        names=[ast.alias(name="opacity"), ast.alias(name="Layer")],
        level=0,
    )
    tree.body.insert(0, imp)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def _inject_vault_marker(source: str, secret_var: str) -> str:
    """Wrap ``<secret_var> = {..}`` into ``vault_secrets({..})`` + import it."""
    tree = ast.parse(source)
    found = False
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == secret_var
            and isinstance(node.value, ast.Dict)
        ):
            node.value = ast.Call(
                func=ast.Name(id="vault_secrets", ctx=ast.Load()),
                args=[node.value],
                keywords=[],
            )
            found = True
            break
    if not found:
        raise ConditionError(f"vault secret dict {secret_var!r} not found in sample")
    imp = ast.ImportFrom(
        module="pyobfus_pro",
        names=[ast.alias(name="vault_secrets")],
        level=0,
    )
    tree.body.insert(0, imp)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)
