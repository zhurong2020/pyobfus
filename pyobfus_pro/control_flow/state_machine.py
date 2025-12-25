"""
State machine representation for control flow flattening.

This module provides classes to build and manage state machine representations
of Python control flow structures.
"""

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass
class State:
    """
    Represents a single state in the control flow state machine.

    Attributes:
        id: Unique identifier for this state
        statements: List of AST statements to execute in this state
        transitions: List of (condition, target_state) tuples
                    If condition is None, it's an unconditional transition
    """

    id: int
    statements: List[ast.stmt] = field(default_factory=list)
    transitions: List[Tuple[Optional[ast.expr], int]] = field(default_factory=list)

    def add_transition(self, target: int, condition: Optional[ast.expr] = None) -> None:
        """Add a transition to another state."""
        self.transitions.append((condition, target))

    def has_unconditional_transition(self) -> bool:
        """Check if this state has an unconditional transition."""
        return any(cond is None for cond, _ in self.transitions)


class StateMachine:
    """
    Builds and manages a state machine representation of control flow.

    The state machine uses:
    - State 0: Entry point
    - State -1: Exit state (terminates the while loop)
    - States 1-N: Basic blocks of code
    """

    EXIT_STATE = -1

    def __init__(self, state_var: str = "_cff_state"):
        """
        Initialize the state machine.

        Args:
            state_var: Name of the state variable (default: _cff_state)
        """
        self.state_var = state_var
        self.states: Dict[int, State] = {}
        self._next_state_id = 0

    def new_state(self, statements: Optional[List[ast.stmt]] = None) -> int:
        """
        Create a new state and return its ID.

        Args:
            statements: Optional list of statements for this state

        Returns:
            The ID of the newly created state
        """
        state_id = self._next_state_id
        self._next_state_id += 1
        self.states[state_id] = State(id=state_id, statements=statements or [])
        return state_id

    def add_statements(self, state_id: int, statements: List[ast.stmt]) -> None:
        """Add statements to an existing state."""
        if state_id in self.states:
            self.states[state_id].statements.extend(statements)

    def add_transition(
        self, from_state: int, to_state: int, condition: Optional[ast.expr] = None
    ) -> None:
        """
        Add a transition between states.

        Args:
            from_state: Source state ID
            to_state: Target state ID
            condition: Optional condition for the transition
        """
        if from_state in self.states:
            self.states[from_state].add_transition(to_state, condition)

    def to_ast(self) -> List[ast.stmt]:
        """
        Generate AST for the state machine.

        Returns a list of statements that implement the state machine:
        1. Initialize state variable to 0
        2. While loop with state != -1 condition
        3. If/elif chain for state dispatch
        """
        if not self.states:
            return []

        # Create: _cff_state = 0
        init_stmt = ast.Assign(
            targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
            value=ast.Constant(value=0),
        )

        # Create the while loop body (if/elif chain)
        dispatch_body = self._build_dispatch_chain()

        # Create: while _cff_state != -1:
        while_stmt = ast.While(
            test=ast.Compare(
                left=ast.Name(id=self.state_var, ctx=ast.Load()),
                ops=[ast.NotEq()],
                comparators=[ast.Constant(value=self.EXIT_STATE)],
            ),
            body=dispatch_body,
            orelse=[],
        )

        return [init_stmt, while_stmt]

    def _build_dispatch_chain(self) -> List[ast.stmt]:
        """Build the if/elif chain for state dispatch."""
        if not self.states:
            return [ast.Pass()]

        # Sort states by ID for consistent output
        sorted_states = sorted(self.states.items())

        # Build the if/elif chain
        result: List[ast.stmt] = []
        first = True

        for state_id, state in sorted_states:
            # Build condition: _cff_state == state_id
            condition = ast.Compare(
                left=ast.Name(id=self.state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=state_id)],
            )

            # Build body: state statements + state transitions
            body = list(state.statements)  # Copy statements
            body.extend(self._build_transitions(state))

            # Ensure body is not empty
            if not body:
                body = [ast.Pass()]

            if first:
                # First state becomes 'if'
                result.append(ast.If(test=condition, body=body, orelse=[]))
                first = False
            else:
                # Subsequent states become 'elif'
                # We need to append to the orelse of the previous if
                first_if = result[0]
                assert isinstance(first_if, ast.If)
                self._append_elif(first_if, condition, body)

        return result

    def _append_elif(self, if_node: ast.If, condition: ast.expr, body: Sequence[ast.stmt]) -> None:
        """Append an elif clause to an existing if statement."""
        # Navigate to the deepest orelse
        current = if_node
        while current.orelse and isinstance(current.orelse[0], ast.If):
            current = current.orelse[0]

        # Append new elif
        new_if: ast.stmt = ast.If(test=condition, body=list(body), orelse=[])
        current.orelse = [new_if]

    def _build_transitions(self, state: State) -> List[ast.stmt]:
        """Build AST statements for state transitions."""
        if not state.transitions:
            return []

        # Single unconditional transition
        if len(state.transitions) == 1 and state.transitions[0][0] is None:
            _, target = state.transitions[0]
            return [self._make_state_assignment(target)]

        # Conditional transitions (if/else pattern)
        if len(state.transitions) == 2:
            cond1, target1 = state.transitions[0]
            cond2, target2 = state.transitions[1]

            # If first has condition and second doesn't
            if cond1 is not None and cond2 is None:
                return [
                    ast.If(
                        test=cond1,
                        body=[self._make_state_assignment(target1)],
                        orelse=[self._make_state_assignment(target2)],
                    )
                ]

            # If first doesn't have condition, use ternary
            if cond1 is None and cond2 is not None:
                # Swap for clarity
                return [
                    ast.If(
                        test=cond2,
                        body=[self._make_state_assignment(target2)],
                        orelse=[self._make_state_assignment(target1)],
                    )
                ]

            # Both have conditions - use ternary for compactness
            if cond1 is not None and cond2 is not None:
                return [
                    ast.Assign(
                        targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                        value=ast.IfExp(
                            test=cond1,
                            body=ast.Constant(value=target1),
                            orelse=ast.Constant(value=target2),
                        ),
                    )
                ]

        # Multiple transitions - use if/elif chain
        result: List[ast.stmt] = []
        for i, (cond, target) in enumerate(state.transitions):
            if cond is None:
                # Unconditional - should be last
                if i == 0:
                    result.append(self._make_state_assignment(target))
                else:
                    # Add as else clause to previous if
                    self._add_else_to_last_if(result, [self._make_state_assignment(target)])
            else:
                if not result:
                    result.append(
                        ast.If(
                            test=cond,
                            body=[self._make_state_assignment(target)],
                            orelse=[],
                        )
                    )
                else:
                    # Append as elif
                    first_if = result[0]
                    assert isinstance(first_if, ast.If)
                    self._append_elif(first_if, cond, [self._make_state_assignment(target)])

        return result

    def _make_state_assignment(self, target_state: int) -> ast.Assign:
        """Create an assignment statement: _cff_state = target_state"""
        return ast.Assign(
            targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
            value=ast.Constant(value=target_state),
        )

    def _add_else_to_last_if(self, statements: List[ast.stmt], else_body: List[ast.stmt]) -> None:
        """Add an else clause to the last if statement in the list."""
        for stmt in reversed(statements):
            if isinstance(stmt, ast.If):
                # Navigate to deepest orelse
                current = stmt
                while current.orelse and isinstance(current.orelse[0], ast.If):
                    current = current.orelse[0]
                current.orelse = else_body
                return
