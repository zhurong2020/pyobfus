"""
Demonstration of String Encoding (Base64) feature - Community Edition.

This example shows how string literals are encoded with Base64 to make
the code harder to read while maintaining functionality.

Usage:
    # Obfuscate with string encoding (default for community edition)
    pyobfus examples/string_encoding.py -o examples/string_encoding_obf.py

    # Test the obfuscated code
    python examples/string_encoding_obf.py

    # Compare the original and obfuscated versions
    diff examples/string_encoding.py examples/string_encoding_obf.py
"""


def greet_user(name):
    """
    Greet a user with a personalized message.

    Args:
        name: The name of the user

    Returns:
        str: Greeting message
    """
    greeting = "Hello"
    punctuation = "!"
    return f"{greeting}, {name}{punctuation}"


def calculate_discount(item_name, original_price, discount_code):
    """
    Calculate discounted price based on discount code.

    Args:
        item_name: Name of the item
        original_price: Original price
        discount_code: Discount code (SAVE10, SAVE20, SAVE50)

    Returns:
        tuple: (discounted_price, message)
    """
    # Discount codes and their rates
    discount_rates = {
        "SAVE10": 0.10,
        "SAVE20": 0.20,
        "SAVE50": 0.50,
    }

    if discount_code in discount_rates:
        rate = discount_rates[discount_code]
        discounted_price = original_price * (1 - rate)
        message = f"Discount applied: {int(rate * 100)}% off {item_name}"
        return discounted_price, message
    else:
        error_msg = "Invalid discount code"
        return original_price, error_msg


def format_product_info(product_name, description, price, currency="USD"):
    """
    Format product information into a display string.

    Args:
        product_name: Name of the product
        description: Product description
        price: Product price
        currency: Currency symbol (default: USD)

    Returns:
        str: Formatted product information
    """
    separator = "-" * 50
    title = "Product Information"

    info = f"""
{separator}
{title}
{separator}
Name: {product_name}
Description: {description}
Price: {price} {currency}
{separator}
"""
    return info


def validate_email(email):
    """
    Simple email validation.

    Args:
        email: Email address to validate

    Returns:
        tuple: (is_valid, message)
    """
    if "@" not in email:
        return False, "Email must contain @ symbol"

    if "." not in email.split("@")[1]:
        return False, "Email domain must contain a period"

    return True, "Email is valid"


def generate_status_messages():
    """
    Generate various status messages.

    Returns:
        dict: Status messages for different scenarios
    """
    messages = {
        "success": "Operation completed successfully",
        "error": "An error occurred during processing",
        "warning": "Please review the following warnings",
        "info": "Additional information available",
        "pending": "Operation is pending approval",
    }

    return messages


def demonstrate_unicode():
    """
    Demonstrate Unicode string handling.

    Returns:
        dict: Unicode strings in various languages
    """
    greetings = {
        "english": "Hello, World!",
        "chinese": "你好，世界！",
        "japanese": "こんにちは、世界！",
        "korean": "안녕하세요, 세계!",
        "arabic": "مرحبا بالعالم!",
        "russian": "Привет, мир!",
        "emoji": "Hello 👋 World 🌍",
    }

    return greetings


def main():
    """Run examples demonstrating string encoding."""

    print("=" * 70)
    print("String Encoding (Base64) Example - Community Edition")
    print("=" * 70)
    print()

    # Example 1: Basic greeting
    print("Example 1: Basic Greeting")
    print("-" * 70)
    user_name = "Alice"
    greeting = greet_user(user_name)
    print(greeting)
    print()

    # Example 2: Discount calculation
    print("Example 2: Discount Calculation")
    print("-" * 70)
    item = "Laptop"
    price = 1000.00
    code = "SAVE20"

    discounted, msg = calculate_discount(item, price, code)
    print(msg)
    print(f"Original price: ${price:.2f}")
    print(f"Discounted price: ${discounted:.2f}")
    print()

    # Example 3: Invalid discount code
    print("Example 3: Invalid Discount Code")
    print("-" * 70)
    invalid_price, invalid_msg = calculate_discount(item, price, "INVALID")
    print(invalid_msg)
    print()

    # Example 4: Product information formatting
    print("Example 4: Product Information")
    print("-" * 70)
    product_info = format_product_info(
        "Wireless Mouse",
        "Ergonomic wireless mouse with 3 buttons",
        29.99
    )
    print(product_info)

    # Example 5: Email validation
    print("Example 5: Email Validation")
    print("-" * 70)
    test_emails = [
        "user@example.com",
        "invalid-email",
        "missing-domain@",
    ]

    for email in test_emails:
        is_valid, message = validate_email(email)
        status = "✓" if is_valid else "✗"
        print(f"{status} {email}: {message}")
    print()

    # Example 6: Status messages
    print("Example 6: Status Messages")
    print("-" * 70)
    statuses = generate_status_messages()
    for status_type, message in statuses.items():
        print(f"[{status_type.upper()}] {message}")
    print()

    # Example 7: Unicode handling
    print("Example 7: Unicode String Handling")
    print("-" * 70)
    unicode_greetings = demonstrate_unicode()
    for language, greeting in unicode_greetings.items():
        print(f"{language.capitalize()}: {greeting}")
    print()

    print("=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)
    print()
    print("In the obfuscated version:")
    print("  - All string literals are encoded with Base64")
    print("  - A decoder function is automatically injected")
    print("  - F-strings preserve their runtime expressions")
    print("  - Docstrings are preserved for documentation")
    print("  - Unicode strings are handled correctly")
    print()
    print("Benefits:")
    print("  - String literals are not visible in plaintext")
    print("  - Code functionality remains unchanged")
    print("  - No runtime performance impact")
    print("  - Compatible with all Python string types")


if __name__ == "__main__":
    main()
