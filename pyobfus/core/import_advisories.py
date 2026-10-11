"""Read-only compatibility checks for statically imported module objects.

Bindings are lexical candidates, not runtime identity proofs. Reassigned names
are deliberately ignored; dynamic imports and star imports are not resolved.
"""

from __future__ import annotations

import ast
from typing import List, Set


from pyobfus.core.import_resolution import ImportedAccessVisitor  # noqa: F401


def enum_members(node: ast.ClassDef) -> List[str]:
    """List statically assigned public member candidates, in source order."""
    members: List[str] = []
    ignored: Set[str] = set()
    for statement in node.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
            if any(isinstance(t, ast.Name) and t.id == "_ignore_" for t in targets):
                try:
                    value = ast.literal_eval(statement.value)
                    ignored.update(value.split() if isinstance(value, str) else value)
                except (ValueError, TypeError):
                    pass
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets = [statement.target]
        else:
            continue
        for target in targets:
            for name in ast.walk(target):
                if (
                    isinstance(name, ast.Name)
                    and isinstance(name.ctx, ast.Store)
                    and not (name.id.startswith("_") and name.id.endswith("_") and len(name.id) > 1)
                    and name.id not in members
                ):
                    members.append(name.id)
    return [name for name in members if name not in ignored]
