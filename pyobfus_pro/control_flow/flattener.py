"""
Control Flow Flattener - transforms structured control flow into state machines.

This is the main transformer class that visits AST nodes and flattens
control flow structures (if/else, for, while) into state machine representations.
"""

import ast
import copy
from dataclasses import dataclass
from typing import List, Optional, Set

from .state_machine import StateMachine


@dataclass
class CFFConfig:
    """Configuration for Control Flow Flattening."""

    enabled: bool = True
    flatten_if: bool = True
    flatten_for: bool = True
    flatten_while: bool = True
    flatten_nested: bool = True
    max_states: int = 50
    min_statements: int = 3
    state_var_prefix: str = "_cff_state"


class ControlFlowFlattener(ast.NodeTransformer):
    """
    AST transformer that flattens control flow structures into state machines.

    This transformer converts structured control flow (if/else, for, while)
    into a state machine pattern using a while loop and state variable.

    Example:
        if x > 0:
            result = x * 2
        else:
            result = x / 2

    Becomes:
        _cff_state = 0
        while _cff_state != -1:
            if _cff_state == 0:
                _cff_state = 1 if x > 0 else 2
            elif _cff_state == 1:
                result = x * 2
                _cff_state = 3
            elif _cff_state == 2:
                result = x / 2
                _cff_state = 3
            elif _cff_state == 3:
                _cff_state = -1
    """

    def __init__(self, config: Optional[CFFConfig] = None):
        """
        Initialize the flattener.

        Args:
            config: Configuration options for flattening
        """
        self.config = config or CFFConfig()
        self._function_counter = 0
        self._skip_functions: Set[str] = set()

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Visit module and process all function definitions."""
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Transform a function definition by flattening its control flow.

        Skips:
        - Generator functions (contain yield/yield from)
        - Async functions (handled separately)
        - Functions with too few statements
        - Functions that would have too many states
        """
        if not self.config.enabled:
            return node

        # Skip generators
        if self._is_generator(node):
            return node

        # Skip if too few statements
        if len(node.body) < self.config.min_statements:
            return node

        # Skip if no control flow to flatten
        if not self._has_control_flow(node.body):
            return node

        # Flatten the function body
        new_body = self._flatten_body(node.body)

        # Create new function with flattened body
        new_node = copy.copy(node)
        new_node.body = new_body

        return ast.fix_missing_locations(new_node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Skip async functions for now (Phase 2)."""
        return node

    def _is_generator(self, node: ast.FunctionDef) -> bool:
        """Check if a function is a generator (contains yield)."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _has_control_flow(self, body: List[ast.stmt]) -> bool:
        """Check if body contains control flow statements to flatten."""
        for stmt in body:
            if isinstance(stmt, ast.If) and self.config.flatten_if:
                return True
            if isinstance(stmt, ast.For) and self.config.flatten_for:
                return True
            if isinstance(stmt, ast.While) and self.config.flatten_while:
                return True
        return False

    def _flatten_body(self, body: List[ast.stmt]) -> List[ast.stmt]:
        """
        Flatten a list of statements into a state machine.

        Args:
            body: List of AST statements to flatten

        Returns:
            New list of statements implementing the state machine
        """
        state_var = f"{self.config.state_var_prefix}_{self._function_counter}"
        self._function_counter += 1

        sm = StateMachine(state_var=state_var)

        # Track return value if needed
        has_return = self._has_return_in_body(body)
        return_var = f"_cff_return_{self._function_counter}" if has_return else None

        # Build the state machine
        entry_state = sm.new_state()
        exit_state = self._process_statements(sm, body, entry_state, return_var)

        # Add transition to exit
        sm.add_transition(exit_state, StateMachine.EXIT_STATE)

        # Generate the state machine AST
        result = sm.to_ast()

        # If we have returns, add the final return statement
        if return_var:
            result.append(ast.Return(value=ast.Name(id=return_var, ctx=ast.Load())))

        return result

    def _process_statements(
        self,
        sm: StateMachine,
        statements: List[ast.stmt],
        current_state: int,
        return_var: Optional[str],
    ) -> int:
        """
        Process a list of statements and add them to the state machine.

        Args:
            sm: The state machine being built
            statements: List of statements to process
            current_state: The current state ID
            return_var: Variable name for storing return values

        Returns:
            The final state ID after processing all statements
        """
        for stmt in statements:
            if isinstance(stmt, ast.If) and self.config.flatten_if:
                current_state = self._process_if(sm, stmt, current_state, return_var)
            elif isinstance(stmt, ast.For) and self.config.flatten_for:
                current_state = self._process_for(sm, stmt, current_state, return_var)
            elif isinstance(stmt, ast.While) and self.config.flatten_while:
                current_state = self._process_while(sm, stmt, current_state, return_var)
            elif isinstance(stmt, ast.Return):
                current_state = self._process_return(sm, stmt, current_state, return_var)
            else:
                # Regular statement - add to current state
                sm.add_statements(current_state, [stmt])

        return current_state

    def _process_if(
        self,
        sm: StateMachine,
        node: ast.If,
        current_state: int,
        return_var: Optional[str],
    ) -> int:
        """
        Process an if statement and add it to the state machine.

        Transforms:
            if cond:
                body
            else:
                orelse

        Into states:
            current_state: evaluate condition -> branch to then_state or else_state
            then_state: execute body -> goto merge_state
            else_state: execute orelse -> goto merge_state
            merge_state: continue
        """
        # Create states for then/else branches and merge point
        then_state = sm.new_state()
        merge_state = sm.new_state()

        # Create else state only if there's an else branch
        if node.orelse:
            else_state = sm.new_state()
        else:
            else_state = merge_state

        # Add conditional transition from current state
        sm.add_transition(current_state, then_state, node.test)
        sm.add_transition(current_state, else_state)  # Unconditional fallthrough

        # Process then branch
        then_end = self._process_statements(sm, node.body, then_state, return_var)
        sm.add_transition(then_end, merge_state)

        # Process else branch if present
        if node.orelse:
            # Check if it's an elif (else contains single If)
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # Recursive elif handling
                else_end = self._process_if(sm, node.orelse[0], else_state, return_var)
            else:
                else_end = self._process_statements(sm, node.orelse, else_state, return_var)
            sm.add_transition(else_end, merge_state)

        return merge_state

    def _process_for(
        self,
        sm: StateMachine,
        node: ast.For,
        current_state: int,
        return_var: Optional[str],
    ) -> int:
        """
        Process a for loop and add it to the state machine.

        Transforms:
            for item in iterable:
                body
            else:
                orelse

        Into states:
            current_state: _iter = iter(iterable) -> goto check_state
            check_state: try next(_iter) -> body_state or exit_state
            body_state: execute body -> goto check_state
            exit_state: execute orelse if any -> merge_state
        """
        iter_var = f"_cff_iter_{self._function_counter}"

        # Create states
        check_state = sm.new_state()
        body_state = sm.new_state()
        exit_state = sm.new_state()
        merge_state = sm.new_state()

        # Initialize iterator: _iter = iter(iterable)
        init_iter = ast.Assign(
            targets=[ast.Name(id=iter_var, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="iter", ctx=ast.Load()),
                args=[node.iter],
                keywords=[],
            ),
        )
        sm.add_statements(current_state, [init_iter])
        sm.add_transition(current_state, check_state)

        # Check state: try to get next item
        # We use a try/except pattern for StopIteration
        next_call = ast.Call(
            func=ast.Name(id="next", ctx=ast.Load()),
            args=[ast.Name(id=iter_var, ctx=ast.Load())],
            keywords=[],
        )

        # Assign to loop variable and continue
        assign_stmt = ast.Assign(targets=[node.target], value=next_call)

        # Wrap in try/except StopIteration
        try_stmt = ast.Try(
            body=[
                assign_stmt,
                sm._make_state_assignment(body_state),
            ],
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id="StopIteration", ctx=ast.Load()),
                    name=None,
                    body=[sm._make_state_assignment(exit_state)],
                )
            ],
            orelse=[],
            finalbody=[],
        )
        sm.add_statements(check_state, [try_stmt])

        # Process body
        body_end = self._process_statements(sm, node.body, body_state, return_var)
        sm.add_transition(body_end, check_state)  # Loop back

        # Process else clause if present
        if node.orelse:
            exit_end = self._process_statements(sm, node.orelse, exit_state, return_var)
            sm.add_transition(exit_end, merge_state)
        else:
            sm.add_transition(exit_state, merge_state)

        return merge_state

    def _process_while(
        self,
        sm: StateMachine,
        node: ast.While,
        current_state: int,
        return_var: Optional[str],
    ) -> int:
        """
        Process a while loop and add it to the state machine.

        Transforms:
            while cond:
                body
            else:
                orelse

        Into states:
            current_state -> check_state
            check_state: if cond -> body_state else exit_state
            body_state: execute body -> check_state
            exit_state: execute orelse -> merge_state
        """
        # Create states
        check_state = sm.new_state()
        body_state = sm.new_state()
        exit_state = sm.new_state()
        merge_state = sm.new_state()

        # Transition to check state
        sm.add_transition(current_state, check_state)

        # Check condition
        sm.add_transition(check_state, body_state, node.test)
        sm.add_transition(check_state, exit_state)  # Unconditional fallthrough

        # Process body
        body_end = self._process_statements(sm, node.body, body_state, return_var)
        sm.add_transition(body_end, check_state)  # Loop back

        # Process else clause if present
        if node.orelse:
            exit_end = self._process_statements(sm, node.orelse, exit_state, return_var)
            sm.add_transition(exit_end, merge_state)
        else:
            sm.add_transition(exit_state, merge_state)

        return merge_state

    def _process_return(
        self,
        sm: StateMachine,
        node: ast.Return,
        current_state: int,
        return_var: Optional[str],
    ) -> int:
        """
        Process a return statement.

        If we have a return_var, store the value and transition to exit.
        """
        if return_var and node.value:
            # Store return value
            store_stmt = ast.Assign(
                targets=[ast.Name(id=return_var, ctx=ast.Store())],
                value=node.value,
            )
            sm.add_statements(current_state, [store_stmt])
        elif return_var:
            # Return None
            store_stmt = ast.Assign(
                targets=[ast.Name(id=return_var, ctx=ast.Store())],
                value=ast.Constant(value=None),
            )
            sm.add_statements(current_state, [store_stmt])

        # Transition to exit
        sm.add_transition(current_state, StateMachine.EXIT_STATE)

        # Return a new state for any code after this (unreachable but syntactically valid)
        return sm.new_state()

    def _has_return_in_body(self, body: List[ast.stmt]) -> bool:
        """Check if body contains any return statements."""
        for stmt in body:
            if isinstance(stmt, ast.Return):
                return True
            for child in ast.walk(stmt):
                if isinstance(child, ast.Return):
                    return True
        return False


def flatten_control_flow(tree: ast.AST, config: Optional[CFFConfig] = None) -> ast.AST:
    """
    Convenience function to flatten control flow in an AST.

    Args:
        tree: The AST to transform
        config: Optional configuration

    Returns:
        The transformed AST
    """
    flattener = ControlFlowFlattener(config)
    result = flattener.visit(tree)
    return result  # type: ignore[no-any-return]
