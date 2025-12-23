"""
Unit tests for Control Flow Flattening.

Tests the transformation of structured control flow (if/else, for, while)
into state machine representations.
"""

import ast
import sys
import pytest

# Add pyobfus_pro to path for testing
sys.path.insert(0, str(__file__).replace("tests/test_control_flow_flattening.py", ""))

from pyobfus_pro.control_flow import ControlFlowFlattener, StateMachine, State
from pyobfus_pro.control_flow.flattener import CFFConfig


class TestStateMachine:
    """Tests for the StateMachine class."""

    def test_new_state_creates_unique_ids(self):
        """Test that new_state creates states with unique IDs."""
        sm = StateMachine()
        state1 = sm.new_state()
        state2 = sm.new_state()
        state3 = sm.new_state()

        assert state1 == 0
        assert state2 == 1
        assert state3 == 2

    def test_add_statements_to_state(self):
        """Test adding statements to a state."""
        sm = StateMachine()
        state_id = sm.new_state()

        stmt = ast.Pass()
        sm.add_statements(state_id, [stmt])

        assert len(sm.states[state_id].statements) == 1
        assert sm.states[state_id].statements[0] is stmt

    def test_add_transition(self):
        """Test adding transitions between states."""
        sm = StateMachine()
        state1 = sm.new_state()
        state2 = sm.new_state()

        sm.add_transition(state1, state2)

        assert len(sm.states[state1].transitions) == 1
        cond, target = sm.states[state1].transitions[0]
        assert cond is None
        assert target == state2

    def test_add_conditional_transition(self):
        """Test adding conditional transitions."""
        sm = StateMachine()
        state1 = sm.new_state()
        state2 = sm.new_state()

        condition = ast.Compare(
            left=ast.Name(id="x", ctx=ast.Load()),
            ops=[ast.Gt()],
            comparators=[ast.Constant(value=0)],
        )
        sm.add_transition(state1, state2, condition)

        assert len(sm.states[state1].transitions) == 1
        cond, target = sm.states[state1].transitions[0]
        assert cond is condition
        assert target == state2

    def test_to_ast_generates_valid_code(self):
        """Test that to_ast generates syntactically valid code."""
        sm = StateMachine(state_var="_state")
        state1 = sm.new_state()
        state2 = sm.new_state()

        sm.add_statements(state1, [ast.Pass()])
        sm.add_transition(state1, state2)
        sm.add_transition(state2, StateMachine.EXIT_STATE)

        result = sm.to_ast()

        # Should have init + while loop
        assert len(result) == 2
        assert isinstance(result[0], ast.Assign)
        assert isinstance(result[1], ast.While)

        # Compile to verify syntax
        module = ast.Module(body=result, type_ignores=[])
        ast.fix_missing_locations(module)
        compile(module, "<test>", "exec")

    def test_state_has_unconditional_transition(self):
        """Test detecting unconditional transitions."""
        state = State(id=0)
        assert not state.has_unconditional_transition()

        state.add_transition(1, ast.Constant(value=True))
        assert not state.has_unconditional_transition()

        state.add_transition(2)  # No condition
        assert state.has_unconditional_transition()


class TestControlFlowFlattener:
    """Tests for the ControlFlowFlattener class."""

    def test_simple_function_no_control_flow(self):
        """Test that functions without control flow are not modified."""
        code = """
def simple(x):
    return x + 1
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        # Should be unchanged (no control flow)
        func = result.body[0]
        assert len(func.body) == 1
        assert isinstance(func.body[0], ast.Return)

    def test_generator_function_skipped(self):
        """Test that generator functions are not flattened."""
        code = """
def gen():
    for i in range(10):
        yield i
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        # Should still have for loop (not flattened)
        func = result.body[0]
        assert isinstance(func.body[0], ast.For)

    def test_simple_if_else_flattening(self):
        """Test flattening a simple if/else statement."""
        code = """
def example(x):
    a = 1
    if x > 0:
        result = x * 2
    else:
        result = x / 2
    return result
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        func = result.body[0]

        # Should have state machine pattern
        # First statement should be assignment of regular code or state init
        # Last should be a while loop or state machine structure
        assert len(func.body) >= 2

        # Compile and verify it's valid Python
        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_flattened_code_executes_correctly(self):
        """Test that flattened code produces correct results."""
        code = """
def example(x):
    a = 1
    if x > 0:
        result = x * 2
    else:
        result = x / 2
    return result
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        example = namespace["example"]

        # Test positive input
        assert example(5) == 10
        # Test negative input
        assert example(-4) == -2

    def test_nested_if_flattening(self):
        """Test flattening nested if statements."""
        code = """
def classify(x):
    a = 0
    if x > 0:
        if x > 100:
            category = "large"
        else:
            category = "medium"
    else:
        category = "negative"
    return category
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        classify = namespace["classify"]

        assert classify(200) == "large"
        assert classify(50) == "medium"
        assert classify(-10) == "negative"

    def test_if_elif_else_flattening(self):
        """Test flattening if/elif/else chains."""
        code = """
def grade(score):
    result = 0
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    else:
        grade = "F"
    return grade
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        grade = namespace["grade"]

        assert grade(95) == "A"
        assert grade(85) == "B"
        assert grade(75) == "C"
        assert grade(60) == "F"


class TestForLoopFlattening:
    """Tests for for loop flattening."""

    def test_simple_for_loop(self):
        """Test flattening a simple for loop."""
        code = """
def sum_list(items):
    total = 0
    for item in items:
        total += item
    return total
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        sum_list = namespace["sum_list"]

        assert sum_list([1, 2, 3, 4, 5]) == 15
        assert sum_list([]) == 0

    def test_for_loop_with_conditional(self):
        """Test for loop containing if statement."""
        code = """
def sum_positive(items):
    total = 0
    for item in items:
        if item > 0:
            total += item
    return total
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        sum_positive = namespace["sum_positive"]

        assert sum_positive([1, -2, 3, -4, 5]) == 9
        assert sum_positive([-1, -2, -3]) == 0


class TestWhileLoopFlattening:
    """Tests for while loop flattening."""

    def test_simple_while_loop(self):
        """Test flattening a simple while loop."""
        code = """
def countdown(n):
    result = []
    i = n
    while i > 0:
        result.append(i)
        i -= 1
    return result
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        countdown = namespace["countdown"]

        assert countdown(5) == [5, 4, 3, 2, 1]
        assert countdown(0) == []


class TestCFFConfig:
    """Tests for CFFConfig options."""

    def test_disabled_config(self):
        """Test that disabled config skips flattening."""
        code = """
def example(x):
    a = 1
    if x > 0:
        return x * 2
    return x / 2
"""
        tree = ast.parse(code)
        config = CFFConfig(enabled=False)
        flattener = ControlFlowFlattener(config)
        result = flattener.visit(tree)

        func = result.body[0]
        # Should still have if statement (not flattened)
        assert any(isinstance(s, ast.If) for s in func.body)

    def test_min_statements_threshold(self):
        """Test that functions with too few statements are skipped."""
        code = """
def tiny(x):
    if x: return 1
    return 0
"""
        tree = ast.parse(code)
        config = CFFConfig(min_statements=5)
        flattener = ControlFlowFlattener(config)
        result = flattener.visit(tree)

        func = result.body[0]
        # Should still have if statement (not flattened due to min_statements)
        assert any(isinstance(s, ast.If) for s in func.body)


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_if_body(self):
        """Test handling of empty if body (pass statement)."""
        code = """
def example(x):
    a = 0
    if x > 0:
        pass
    else:
        a = 1
    return a
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        example = namespace["example"]

        assert example(5) == 0
        assert example(-5) == 1

    def test_if_without_else(self):
        """Test handling of if without else."""
        code = """
def example(x):
    result = 0
    if x > 0:
        result = x * 2
    return result
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        example = namespace["example"]

        assert example(5) == 10
        assert example(-5) == 0

    def test_multiple_if_statements(self):
        """Test handling multiple sequential if statements."""
        code = """
def example(x):
    result = 0
    if x > 0:
        result += 1
    if x > 10:
        result += 10
    if x > 100:
        result += 100
    return result
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        example = namespace["example"]

        assert example(5) == 1
        assert example(50) == 11
        assert example(150) == 111


class TestCorrectness:
    """Tests to verify correctness of flattened code."""

    def test_factorial(self):
        """Test factorial computation after flattening."""
        code = """
def factorial(n):
    result = 1
    i = n
    while i > 1:
        result *= i
        i -= 1
    return result
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        factorial = namespace["factorial"]

        assert factorial(5) == 120
        assert factorial(0) == 1
        assert factorial(1) == 1

    def test_fibonacci(self):
        """Test fibonacci computation after flattening."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    a = 0
    b = 1
    i = 2
    while i <= n:
        a, b = b, a + b
        i += 1
    return b
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        fibonacci = namespace["fibonacci"]

        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
        assert fibonacci(10) == 55

    def test_bubble_sort(self):
        """Test bubble sort after flattening."""
        code = """
def bubble_sort(arr):
    n = len(arr)
    result = list(arr)
    i = 0
    while i < n:
        j = 0
        while j < n - i - 1:
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
            j += 1
        i += 1
    return result
"""
        tree = ast.parse(code)
        flattener = ControlFlowFlattener()
        result = flattener.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        bubble_sort = namespace["bubble_sort"]

        assert bubble_sort([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]
        assert bubble_sort([]) == []
        assert bubble_sort([1]) == [1]


# Run pytest if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
