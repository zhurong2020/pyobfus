"""
Dead Code Injector - injects unreachable code to increase complexity.

This transformer adds dead code that will never execute, making
reverse engineering more difficult by increasing code volume and
adding false leads for analysis.
"""

import ast
import copy
import random
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DCIConfig:
    """Configuration for Dead Code Injection."""

    enabled: bool = True
    # Injection strategies
    inject_after_return: bool = True  # Add code after return statements
    inject_false_branches: bool = True  # Add if False: blocks
    inject_opaque_predicates: bool = True  # Add always-true/false conditions
    inject_decoy_functions: bool = True  # Add never-called functions
    # Intensity settings
    injection_ratio: float = 0.3  # Probability of injection at each opportunity
    min_statements: int = 3  # Min statements in function to inject
    max_dead_statements: int = 5  # Max statements per injection
    # Naming
    var_prefix: str = "_dci_"
    func_prefix: str = "_dci_func_"


class DeadCodeInjector(ast.NodeTransformer):
    """
    AST transformer that injects dead (unreachable) code.

    Strategies:
    1. After Return: Insert statements after return that never execute
    2. False Branches: Add `if False:` blocks with realistic code
    3. Opaque Predicates: Use always-true conditions with dead else
    4. Decoy Functions: Add functions that are never called

    Example:
        def func(x):
            return x * 2

        Becomes:
            def func(x):
                return x * 2
                _dci_0 = x + 1  # Never executes
                if False:
                    _dci_1 = x * x  # Never executes
    """

    def __init__(self, config: Optional[DCIConfig] = None, seed: Optional[int] = None):
        """
        Initialize the injector.

        Args:
            config: Configuration options
            seed: Random seed for reproducible results
        """
        self.config = config or DCIConfig()
        self._random = random.Random(seed)
        self._var_counter = 0
        self._func_counter = 0
        self._injected_count = 0
        self._decoy_functions: List[ast.FunctionDef] = []

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Visit module and process all nodes, then add decoy functions."""
        # First, visit all nodes
        self.generic_visit(node)

        # Add decoy functions at module level if enabled
        if self.config.inject_decoy_functions and self.config.enabled:
            num_decoys = self._random.randint(1, 3)
            for _ in range(num_decoys):
                if self._should_inject():
                    decoy = self._generate_decoy_function()
                    self._decoy_functions.append(decoy)

            # Insert decoy functions at random positions
            for decoy in self._decoy_functions:
                if node.body:
                    pos = self._random.randint(0, len(node.body))
                    node.body.insert(pos, decoy)
                else:
                    node.body.append(decoy)

        return ast.fix_missing_locations(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Transform a function by injecting dead code."""
        if not self.config.enabled:
            return node

        # Skip small functions
        if len(node.body) < self.config.min_statements:
            return node

        # Skip generator functions
        if self._is_generator(node):
            return node

        # Process the function body
        new_body = self._process_body(node.body)

        # Create new function with modified body
        new_node = copy.copy(node)
        new_node.body = new_body

        return ast.fix_missing_locations(new_node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Handle async functions similarly."""
        if not self.config.enabled:
            return node

        if len(node.body) < self.config.min_statements:
            return node

        new_body = self._process_body(node.body)
        new_node = copy.copy(node)
        new_node.body = new_body

        return ast.fix_missing_locations(new_node)

    def _is_generator(self, node: ast.FunctionDef) -> bool:
        """Check if a function is a generator."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _should_inject(self) -> bool:
        """Decide whether to inject based on probability."""
        return self._random.random() < self.config.injection_ratio

    def _process_body(self, body: List[ast.stmt]) -> List[ast.stmt]:
        """Process a list of statements and inject dead code."""
        new_body: List[ast.stmt] = []

        for i, stmt in enumerate(body):
            new_body.append(stmt)

            # After return statements
            if isinstance(stmt, ast.Return) and self.config.inject_after_return:
                if self._should_inject():
                    dead_stmts = self._generate_dead_statements()
                    new_body.extend(dead_stmts)
                    self._injected_count += len(dead_stmts)

            # Add false branches randomly
            if self.config.inject_false_branches and not isinstance(stmt, ast.Return):
                if self._should_inject():
                    false_block = self._generate_false_branch()
                    new_body.append(false_block)
                    self._injected_count += 1

            # Add opaque predicates
            if self.config.inject_opaque_predicates and not isinstance(stmt, ast.Return):
                if self._should_inject():
                    opaque_stmts = self._generate_opaque_predicate()
                    new_body.extend(opaque_stmts)
                    self._injected_count += len(opaque_stmts)

        return new_body

    def _new_var(self) -> str:
        """Generate a new dead code variable name."""
        name = f"{self.config.var_prefix}{self._var_counter}"
        self._var_counter += 1
        return name

    def _new_func_name(self) -> str:
        """Generate a new decoy function name."""
        name = f"{self.config.func_prefix}{self._func_counter}"
        self._func_counter += 1
        return name

    def _generate_dead_statements(self) -> List[ast.stmt]:
        """Generate a list of dead statements."""
        num_stmts = self._random.randint(1, self.config.max_dead_statements)
        stmts: List[ast.stmt] = []

        for _ in range(num_stmts):
            stmt_type = self._random.choice(["assign", "expr", "augassign"])

            if stmt_type == "assign":
                stmts.append(self._generate_assignment())
            elif stmt_type == "expr":
                stmts.append(self._generate_expression())
            else:
                stmts.append(self._generate_augmented_assign())

        return stmts

    def _generate_assignment(self) -> ast.Assign:
        """Generate a dead assignment statement."""
        var = self._new_var()
        value = self._generate_value()

        return ast.Assign(
            targets=[ast.Name(id=var, ctx=ast.Store())],
            value=value,
        )

    def _generate_augmented_assign(self) -> ast.Assign:
        """Generate an assignment with arithmetic operations."""
        var = self._new_var()
        op = self._random.choice([ast.Add(), ast.Sub(), ast.Mult()])

        # Return an assignment with a binary operation
        return ast.Assign(
            targets=[ast.Name(id=var, ctx=ast.Store())],
            value=ast.BinOp(
                left=ast.Constant(value=self._random.randint(1, 100)),
                op=op,
                right=ast.Constant(value=self._random.randint(1, 10)),
            ),
        )

    def _generate_expression(self) -> ast.Expr:
        """Generate a dead expression statement."""
        # Generate a list/dict comprehension or simple expression
        expr_type = self._random.choice(["listcomp", "call", "binop"])

        if expr_type == "listcomp":
            return ast.Expr(
                value=ast.ListComp(
                    elt=ast.Name(id="_i", ctx=ast.Load()),
                    generators=[
                        ast.comprehension(
                            target=ast.Name(id="_i", ctx=ast.Store()),
                            iter=ast.Call(
                                func=ast.Name(id="range", ctx=ast.Load()),
                                args=[ast.Constant(value=self._random.randint(1, 10))],
                                keywords=[],
                            ),
                            ifs=[],
                            is_async=0,
                        )
                    ],
                )
            )
        elif expr_type == "call":
            return ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="len", ctx=ast.Load()),
                    args=[ast.List(elts=[], ctx=ast.Load())],
                    keywords=[],
                )
            )
        else:
            return ast.Expr(
                value=ast.BinOp(
                    left=ast.Constant(value=self._random.randint(1, 100)),
                    op=ast.Add(),
                    right=ast.Constant(value=self._random.randint(1, 100)),
                )
            )

    def _generate_value(self) -> ast.expr:
        """Generate a random value expression."""
        value_type = self._random.choice(["const", "binop", "list", "dict"])

        if value_type == "const":
            const_type = self._random.choice(["int", "float", "str"])
            if const_type == "int":
                return ast.Constant(value=self._random.randint(-1000, 1000))
            elif const_type == "float":
                return ast.Constant(value=self._random.random() * 100)
            else:
                return ast.Constant(value=f"_str_{self._random.randint(0, 100)}")

        elif value_type == "binop":
            op = self._random.choice([ast.Add(), ast.Sub(), ast.Mult(), ast.Div()])
            return ast.BinOp(
                left=ast.Constant(value=self._random.randint(1, 100)),
                op=op,
                right=ast.Constant(value=self._random.randint(1, 100)),
            )

        elif value_type == "list":
            num_elts = self._random.randint(0, 5)
            elts: List[ast.expr] = [
                ast.Constant(value=self._random.randint(0, 100)) for _ in range(num_elts)
            ]
            return ast.List(elts=elts, ctx=ast.Load())

        else:  # dict
            num_pairs = self._random.randint(0, 3)
            keys: List[Optional[ast.expr]] = [
                ast.Constant(value=f"key_{i}") for i in range(num_pairs)
            ]
            values: List[ast.expr] = [
                ast.Constant(value=self._random.randint(0, 100)) for _ in range(num_pairs)
            ]
            return ast.Dict(keys=keys, values=values)

    def _generate_false_branch(self) -> ast.If:
        """Generate an if False: block with dead code."""
        dead_stmts = self._generate_dead_statements()
        if not dead_stmts:
            dead_stmts = [ast.Pass()]

        return ast.If(
            test=ast.Constant(value=False),
            body=dead_stmts,
            orelse=[],
        )

    def _generate_opaque_predicate(self) -> List[ast.stmt]:
        """
        Generate an opaque predicate - a condition that always evaluates
        to True or False but is hard to determine statically.

        Returns a list of statements (init + if).
        """
        predicate_type = self._random.choice(
            [
                "square_positive",  # x*x >= 0 (always true)
                "mod_range",  # x % n < n (always true for n > 0)
                "abs_non_negative",  # abs(x) >= 0 (always true)
            ]
        )

        var = self._new_var()
        init_value = self._random.randint(1, 100)

        # Create initialization
        init_stmt = ast.Assign(
            targets=[ast.Name(id=var, ctx=ast.Store())],
            value=ast.Constant(value=init_value),
        )

        if predicate_type == "square_positive":
            # x * x >= 0 is always True
            condition = ast.Compare(
                left=ast.BinOp(
                    left=ast.Name(id=var, ctx=ast.Load()),
                    op=ast.Mult(),
                    right=ast.Name(id=var, ctx=ast.Load()),
                ),
                ops=[ast.GtE()],
                comparators=[ast.Constant(value=0)],
            )
            # Real code in if, dead code in else
            real_body = [ast.Pass()]
            dead_body = self._generate_dead_statements() or [ast.Pass()]

        elif predicate_type == "mod_range":
            # x % 10 < 10 is always True
            n = self._random.randint(2, 20)
            condition = ast.Compare(
                left=ast.BinOp(
                    left=ast.Name(id=var, ctx=ast.Load()),
                    op=ast.Mod(),
                    right=ast.Constant(value=n),
                ),
                ops=[ast.Lt()],
                comparators=[ast.Constant(value=n)],
            )
            real_body = [ast.Pass()]
            dead_body = self._generate_dead_statements() or [ast.Pass()]

        else:  # abs_non_negative
            # abs(x) >= 0 is always True
            condition = ast.Compare(
                left=ast.Call(
                    func=ast.Name(id="abs", ctx=ast.Load()),
                    args=[ast.Name(id=var, ctx=ast.Load())],
                    keywords=[],
                ),
                ops=[ast.GtE()],
                comparators=[ast.Constant(value=0)],
            )
            real_body = [ast.Pass()]
            dead_body = self._generate_dead_statements() or [ast.Pass()]

        # Create the if statement with dead else branch
        if_stmt = ast.If(
            test=condition,
            body=list(real_body),
            orelse=list(dead_body),
        )

        # Return both init and if statement
        return [init_stmt, if_stmt]

    def _generate_decoy_function(self) -> ast.FunctionDef:
        """Generate a decoy function that is never called."""
        func_name = self._new_func_name()

        # Generate parameters
        num_params = self._random.randint(0, 3)
        params = [ast.arg(arg=f"_p{i}", annotation=None) for i in range(num_params)]

        # Generate function body
        body: List[ast.stmt] = []

        # Add some assignments
        num_stmts = self._random.randint(2, 5)
        for _ in range(num_stmts):
            body.append(self._generate_assignment())

        # Add a return
        body.append(ast.Return(value=ast.Constant(value=None)))

        return ast.FunctionDef(
            name=func_name,
            args=ast.arguments(
                posonlyargs=[],
                args=params,
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=body,
            decorator_list=[],
            returns=None,
        )

    def get_statistics(self) -> dict:
        """Get injection statistics."""
        return {
            "injected_statements": self._injected_count,
            "decoy_functions": len(self._decoy_functions),
            "variables_created": self._var_counter,
        }


def inject_dead_code(
    tree: ast.AST,
    config: Optional[DCIConfig] = None,
    seed: Optional[int] = None,
) -> ast.AST:
    """
    Convenience function to inject dead code into an AST.

    Args:
        tree: The AST to transform
        config: Optional configuration
        seed: Random seed for reproducibility

    Returns:
        The transformed AST with dead code injected
    """
    injector = DeadCodeInjector(config, seed)
    result = injector.visit(tree)
    return result  # type: ignore[no-any-return]
