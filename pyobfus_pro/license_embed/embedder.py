"""
License Embedder - Embeds license verification code into obfuscated output.

This transformer injects license checks directly into the protected code,
enabling offline verification without external dependencies.
"""

import ast
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class LicenseEmbedConfig:
    """Configuration for License Embedding."""

    enabled: bool = True
    # Expiration date (ISO format: YYYY-MM-DD)
    expire_date: Optional[str] = None
    # Hardware binding - bind to specific machine
    bind_machine: bool = False
    # Machine fingerprint (auto-generated if bind_machine=True and not provided)
    machine_fingerprint: Optional[str] = None
    # Maximum number of runs (0 = unlimited)
    max_runs: int = 0
    # Run counter file name (hidden file in user's home directory)
    run_counter_filename: str = ".pyobfus_rc"
    # Custom error messages
    expire_message: str = "This software has expired."
    machine_message: str = "This software is not licensed for this machine."
    runs_message: str = "Maximum run limit exceeded."
    # Variable prefix for obfuscation
    var_prefix: str = "_lic_"


class LicenseEmbedder(ast.NodeTransformer):
    """
    AST transformer that embeds license verification code.

    This injects license checks at the beginning of the module that verify:
    1. Expiration date - Code stops working after a specific date
    2. Machine binding - Code only works on a specific machine
    3. Run count - Code has limited number of executions

    Example with expiration:
        # Original
        def hello():
            print("Hello")

        # After embedding --expire 2025-12-31
        import datetime as _lic_dt
        if _lic_dt.datetime.now() > _lic_dt.datetime(2025, 12, 31, 23, 59, 59):
            raise RuntimeError("This software has expired.")
        def hello():
            print("Hello")
    """

    def __init__(self, config: Optional[LicenseEmbedConfig] = None):
        """
        Initialize the embedder.

        Args:
            config: Configuration options for license embedding
        """
        self.config = config or LicenseEmbedConfig()
        self._var_counter = 0

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Visit module and inject license checks at the beginning."""
        if not self.config.enabled:
            return node

        # Collect all license check statements
        license_stmts: List[ast.stmt] = []

        # Add expiration check
        if self.config.expire_date:
            license_stmts.extend(self._generate_expiration_check())

        # Add machine binding check
        if self.config.bind_machine:
            license_stmts.extend(self._generate_machine_check())

        # Add run count check
        if self.config.max_runs > 0:
            license_stmts.extend(self._generate_run_count_check())

        # If we have any checks, inject them at the beginning
        if license_stmts:
            # Insert license checks at the beginning, after any __future__ imports
            insert_pos = 0
            for i, stmt in enumerate(node.body):
                if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
                    insert_pos = i + 1
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    # Skip module docstring
                    if i == 0 or (i == 1 and insert_pos == 1):
                        insert_pos = i + 1
                else:
                    break

            # Insert license checks
            for i, stmt in enumerate(license_stmts):
                node.body.insert(insert_pos + i, stmt)

        return ast.fix_missing_locations(node)

    def _new_var(self, suffix: str = "") -> str:
        """Generate a new variable name."""
        name = f"{self.config.var_prefix}{self._var_counter}"
        if suffix:
            name = f"{name}_{suffix}"
        self._var_counter += 1
        return name

    def _generate_expiration_check(self) -> List[ast.stmt]:
        """
        Generate expiration date check code.

        Generates:
            import datetime as _lic_dt
            if _lic_dt.datetime.now() > _lic_dt.datetime(YYYY, MM, DD, 23, 59, 59):
                raise RuntimeError("This software has expired.")
        """
        stmts: List[ast.stmt] = []

        # Parse the expiration date
        try:
            expire_dt = datetime.strptime(self.config.expire_date, "%Y-%m-%d")  # type: ignore[arg-type]
        except ValueError:
            raise ValueError(
                f"Invalid expire date format: {self.config.expire_date}. Use YYYY-MM-DD."
            )

        dt_alias = self._new_var("dt")

        # import datetime as _lic_X_dt
        import_stmt = ast.Import(names=[ast.alias(name="datetime", asname=dt_alias)])
        stmts.append(import_stmt)

        # Build the comparison: datetime.now() > datetime(YYYY, MM, DD, 23, 59, 59)
        now_call = ast.Call(
            func=ast.Attribute(
                value=ast.Attribute(
                    value=ast.Name(id=dt_alias, ctx=ast.Load()),
                    attr="datetime",
                    ctx=ast.Load(),
                ),
                attr="now",
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[],
        )

        expire_datetime = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id=dt_alias, ctx=ast.Load()),
                attr="datetime",
                ctx=ast.Load(),
            ),
            args=[
                ast.Constant(value=expire_dt.year),
                ast.Constant(value=expire_dt.month),
                ast.Constant(value=expire_dt.day),
                ast.Constant(value=23),
                ast.Constant(value=59),
                ast.Constant(value=59),
            ],
            keywords=[],
        )

        condition = ast.Compare(
            left=now_call,
            ops=[ast.Gt()],
            comparators=[expire_datetime],
        )

        # raise RuntimeError(message)
        raise_stmt = ast.Raise(
            exc=ast.Call(
                func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                args=[ast.Constant(value=self.config.expire_message)],
                keywords=[],
            ),
            cause=None,
        )

        # if condition: raise
        if_stmt = ast.If(
            test=condition,
            body=[raise_stmt],
            orelse=[],
        )
        stmts.append(if_stmt)

        return stmts

    def _generate_machine_check(self) -> List[ast.stmt]:
        """
        Generate machine binding check code.

        Generates code that creates a machine fingerprint from:
        - Platform info
        - Processor info
        - Machine name
        And compares against the embedded fingerprint.
        """
        stmts: List[ast.stmt] = []

        # Get or generate machine fingerprint
        fingerprint = self.config.machine_fingerprint
        if not fingerprint:
            fingerprint = self._get_current_machine_fingerprint()

        hashlib_alias = self._new_var("hl")
        platform_alias = self._new_var("pl")
        fp_var = self._new_var("fp")

        # import hashlib as _lic_X_hl
        stmts.append(ast.Import(names=[ast.alias(name="hashlib", asname=hashlib_alias)]))

        # import platform as _lic_X_pl
        stmts.append(ast.Import(names=[ast.alias(name="platform", asname=platform_alias)]))

        # _lic_X_fp = hashlib.sha256((platform.node() + platform.machine() + platform.processor()).encode()).hexdigest()[:16]
        fp_calculation = ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id=hashlib_alias, ctx=ast.Load()),
                        attr="sha256",
                        ctx=ast.Load(),
                    ),
                    args=[
                        ast.Call(
                            func=ast.Attribute(
                                value=ast.BinOp(
                                    left=ast.BinOp(
                                        left=ast.Call(
                                            func=ast.Attribute(
                                                value=ast.Name(id=platform_alias, ctx=ast.Load()),
                                                attr="node",
                                                ctx=ast.Load(),
                                            ),
                                            args=[],
                                            keywords=[],
                                        ),
                                        op=ast.Add(),
                                        right=ast.Call(
                                            func=ast.Attribute(
                                                value=ast.Name(id=platform_alias, ctx=ast.Load()),
                                                attr="machine",
                                                ctx=ast.Load(),
                                            ),
                                            args=[],
                                            keywords=[],
                                        ),
                                    ),
                                    op=ast.Add(),
                                    right=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id=platform_alias, ctx=ast.Load()),
                                            attr="processor",
                                            ctx=ast.Load(),
                                        ),
                                        args=[],
                                        keywords=[],
                                    ),
                                ),
                                attr="encode",
                                ctx=ast.Load(),
                            ),
                            args=[],
                            keywords=[],
                        ),
                    ],
                    keywords=[],
                ),
                attr="hexdigest",
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[],
        )

        # Slice to get first 16 characters
        fp_slice = ast.Subscript(
            value=fp_calculation,
            slice=ast.Slice(lower=None, upper=ast.Constant(value=16), step=None),
            ctx=ast.Load(),
        )

        # Assignment
        stmts.append(
            ast.Assign(
                targets=[ast.Name(id=fp_var, ctx=ast.Store())],
                value=fp_slice,
            )
        )

        # if _lic_X_fp != "expected_fingerprint": raise RuntimeError(...)
        condition = ast.Compare(
            left=ast.Name(id=fp_var, ctx=ast.Load()),
            ops=[ast.NotEq()],
            comparators=[ast.Constant(value=fingerprint)],
        )

        raise_stmt = ast.Raise(
            exc=ast.Call(
                func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                args=[ast.Constant(value=self.config.machine_message)],
                keywords=[],
            ),
            cause=None,
        )

        stmts.append(
            ast.If(
                test=condition,
                body=[raise_stmt],
                orelse=[],
            )
        )

        return stmts

    def _generate_run_count_check(self) -> List[ast.stmt]:
        """
        Generate run count check code.

        Generates code that:
        1. Reads run count from a hidden file
        2. Increments and saves the count
        3. Raises error if max runs exceeded
        """
        stmts: List[ast.stmt] = []

        os_alias = self._new_var("os")
        path_var = self._new_var("path")
        count_var = self._new_var("cnt")

        # import os as _lic_X_os
        stmts.append(ast.Import(names=[ast.alias(name="os", asname=os_alias)]))

        # _lic_X_path = os.path.join(os.path.expanduser("~"), ".pyobfus_rc")
        path_calc = ast.Call(
            func=ast.Attribute(
                value=ast.Attribute(
                    value=ast.Name(id=os_alias, ctx=ast.Load()),
                    attr="path",
                    ctx=ast.Load(),
                ),
                attr="join",
                ctx=ast.Load(),
            ),
            args=[
                ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(id=os_alias, ctx=ast.Load()),
                            attr="path",
                            ctx=ast.Load(),
                        ),
                        attr="expanduser",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Constant(value="~")],
                    keywords=[],
                ),
                ast.Constant(value=self.config.run_counter_filename),
            ],
            keywords=[],
        )

        stmts.append(
            ast.Assign(
                targets=[ast.Name(id=path_var, ctx=ast.Store())],
                value=path_calc,
            )
        )

        # _lic_X_cnt = 0
        stmts.append(
            ast.Assign(
                targets=[ast.Name(id=count_var, ctx=ast.Store())],
                value=ast.Constant(value=0),
            )
        )

        # try: _lic_X_cnt = int(open(_lic_X_path).read()) except: pass
        try_read = ast.Try(
            body=[
                ast.Assign(
                    targets=[ast.Name(id=count_var, ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Name(id="int", ctx=ast.Load()),
                        args=[
                            ast.Call(
                                func=ast.Attribute(
                                    value=ast.Call(
                                        func=ast.Name(id="open", ctx=ast.Load()),
                                        args=[ast.Name(id=path_var, ctx=ast.Load())],
                                        keywords=[],
                                    ),
                                    attr="read",
                                    ctx=ast.Load(),
                                ),
                                args=[],
                                keywords=[],
                            ),
                        ],
                        keywords=[],
                    ),
                ),
            ],
            handlers=[
                ast.ExceptHandler(
                    type=None,
                    name=None,
                    body=[ast.Pass()],
                ),
            ],
            orelse=[],
            finalbody=[],
        )
        stmts.append(try_read)

        # _lic_X_cnt += 1
        stmts.append(
            ast.AugAssign(
                target=ast.Name(id=count_var, ctx=ast.Store()),
                op=ast.Add(),
                value=ast.Constant(value=1),
            )
        )

        # open(_lic_X_path, "w").write(str(_lic_X_cnt))
        write_stmt = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Call(
                        func=ast.Name(id="open", ctx=ast.Load()),
                        args=[
                            ast.Name(id=path_var, ctx=ast.Load()),
                            ast.Constant(value="w"),
                        ],
                        keywords=[],
                    ),
                    attr="write",
                    ctx=ast.Load(),
                ),
                args=[
                    ast.Call(
                        func=ast.Name(id="str", ctx=ast.Load()),
                        args=[ast.Name(id=count_var, ctx=ast.Load())],
                        keywords=[],
                    ),
                ],
                keywords=[],
            ),
        )
        stmts.append(write_stmt)

        # if _lic_X_cnt > max_runs: raise RuntimeError(...)
        condition = ast.Compare(
            left=ast.Name(id=count_var, ctx=ast.Load()),
            ops=[ast.Gt()],
            comparators=[ast.Constant(value=self.config.max_runs)],
        )

        raise_stmt = ast.Raise(
            exc=ast.Call(
                func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                args=[ast.Constant(value=self.config.runs_message)],
                keywords=[],
            ),
            cause=None,
        )

        stmts.append(
            ast.If(
                test=condition,
                body=[raise_stmt],
                orelse=[],
            )
        )

        return stmts

    def _get_current_machine_fingerprint(self) -> str:
        """Get the fingerprint of the current machine."""
        import platform

        data = platform.node() + platform.machine() + platform.processor()
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get_current_fingerprint(self) -> str:
        """Public method to get current machine fingerprint for binding."""
        return self._get_current_machine_fingerprint()


def embed_license_checks(
    tree: ast.AST,
    config: Optional[LicenseEmbedConfig] = None,
) -> ast.AST:
    """
    Convenience function to embed license checks into an AST.

    Args:
        tree: The AST to transform
        config: Optional configuration

    Returns:
        The transformed AST with license checks embedded
    """
    embedder = LicenseEmbedder(config)
    result = embedder.visit(tree)
    return result  # type: ignore[no-any-return]


def get_machine_fingerprint() -> str:
    """
    Get the fingerprint of the current machine.

    This can be used to get the fingerprint for --bind-machine option.

    Returns:
        A 16-character hex string representing the machine fingerprint
    """
    embedder = LicenseEmbedder()
    return embedder.get_current_fingerprint()
