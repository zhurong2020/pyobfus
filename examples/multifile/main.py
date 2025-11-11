"""
Main program demonstrating the calculator usage.
"""

from calculator import Calculator
from utils import format_result, calculate_percentage


def run_demo():
    """Run calculator demonstration."""
    print("=== Calculator Demo ===\n")

    # Create calculator
    calc = Calculator(precision=2)

    # Perform calculations
    result1 = calc.add(10, 5)
    print(format_result(result1, "10 + 5"))

    result2 = calc.subtract(20, 8)
    print(format_result(result2, "20 - 8"))

    result3 = calc.multiply(6, 7)
    print(format_result(result3, "6 * 7"))

    result4 = calc.divide(100, 4)
    print(format_result(result4, "100 / 4"))

    # Show percentage
    percentage = calculate_percentage(result1, result3)
    print(f"\n{result1} is {percentage:.1f}% of {result3}")

    # Show history
    print("\n=== Calculation History ===")
    for idx, entry in enumerate(calc.get_history(), 1):
        op = entry["operation"]
        a, b = entry["operands"]
        result = entry["result"]
        print(f"{idx}. {op}({a}, {b}) = {result}")


if __name__ == "__main__":
    run_demo()
