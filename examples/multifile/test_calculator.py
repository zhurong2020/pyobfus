"""
Test file for calculator (should be excluded from obfuscation).
"""

from calculator import Calculator


def test_addition():
    """Test addition operation."""
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.add(-1, 1) == 0


def test_division_by_zero():
    """Test division by zero raises error."""
    calc = Calculator()
    try:
        calc.divide(10, 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    test_addition()
    test_division_by_zero()
    print("All tests passed!")
