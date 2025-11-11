"""
Utility functions for the calculator.
"""


def format_result(value, prefix="Result"):
    """
    Format a calculation result for display.

    Args:
        value: Numeric result
        prefix: Optional prefix string

    Returns:
        str: Formatted result string
    """
    return f"{prefix}: {value}"


def validate_number(value):
    """
    Validate that a value is a number.

    Args:
        value: Value to validate

    Returns:
        bool: True if valid number

    Raises:
        TypeError: If value is not a number
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected number, got {type(value).__name__}")
    return True


def calculate_percentage(value, total):
    """
    Calculate percentage of value relative to total.

    Args:
        value: Part value
        total: Total value

    Returns:
        float: Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return (value / total) * 100
