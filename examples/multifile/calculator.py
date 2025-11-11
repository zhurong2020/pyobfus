"""
Calculator module demonstrating class obfuscation.
"""


class Calculator:
    """A simple calculator class."""

    def __init__(self, precision=2):
        """Initialize calculator with precision."""
        self.precision = precision
        self.history = []

    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self._record_operation("add", a, b, result)
        return round(result, self.precision)

    def subtract(self, a, b):
        """Subtract b from a."""
        result = a - b
        self._record_operation("subtract", a, b, result)
        return round(result, self.precision)

    def multiply(self, a, b):
        """Multiply two numbers."""
        result = a * b
        self._record_operation("multiply", a, b, result)
        return round(result, self.precision)

    def divide(self, a, b):
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self._record_operation("divide", a, b, result)
        return round(result, self.precision)

    def _record_operation(self, operation, a, b, result):
        """Record operation in history."""
        self.history.append({
            "operation": operation,
            "operands": (a, b),
            "result": result
        })

    def get_history(self):
        """Get calculation history."""
        return self.history.copy()

    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()
