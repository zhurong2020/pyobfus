"""
Demonstration of keyword argument preservation with --preserve-param-names flag.

This example shows how to use the --preserve-param-names option to maintain
keyword argument compatibility after obfuscation.

Usage:
    # Obfuscate with parameter name preservation
    pyobfus examples/keyword_arguments.py -o examples/keyword_arguments_obf.py --preserve-param-names

    # Test the obfuscated code
    python examples/keyword_arguments_obf.py
"""


def calculate_shipping_cost(
    weight_kg,
    distance_km,
    express_shipping=False,
    insurance=False,
):
    """
    Calculate shipping cost based on weight, distance, and options.

    Args:
        weight_kg: Package weight in kilograms
        distance_km: Shipping distance in kilometers
        express_shipping: Whether to use express shipping (default: False)
        insurance: Whether to add insurance (default: False)

    Returns:
        float: Total shipping cost in USD
    """
    # Base cost calculation
    base_cost = weight_kg * 2.5 + distance_km * 0.15

    # Apply express shipping multiplier
    if express_shipping:
        base_cost *= 1.5

    # Add insurance
    if insurance:
        insurance_cost = base_cost * 0.02
        base_cost += insurance_cost

    return round(base_cost, 2)


def process_order(customer_name, *items, payment_method="credit_card", **shipping_options):
    """
    Process an order with variable items and shipping options.

    Demonstrates use of *args and **kwargs with keyword arguments.

    Args:
        customer_name: Name of the customer
        *items: Variable number of items to order
        payment_method: Payment method (default: "credit_card")
        **shipping_options: Additional shipping options (express, insurance, etc.)

    Returns:
        dict: Order summary
    """
    order_summary = {
        "customer": customer_name,
        "items": items,
        "payment_method": payment_method,
        "item_count": len(items),
        "shipping_options": shipping_options,
    }

    return order_summary


def configure_api_client(
    *,
    api_key,
    endpoint,
    timeout=30,
    retry_count=3,
):
    """
    Configure API client with keyword-only arguments.

    Demonstrates keyword-only parameters (after *).

    Args:
        api_key: API authentication key (keyword-only)
        endpoint: API endpoint URL (keyword-only)
        timeout: Request timeout in seconds (default: 30)
        retry_count: Number of retry attempts (default: 3)

    Returns:
        dict: Client configuration
    """
    config = {
        "api_key": api_key,
        "endpoint": endpoint,
        "timeout": timeout,
        "retry_count": retry_count,
    }

    return config


def main():
    """Run examples demonstrating keyword argument usage."""

    print("=" * 70)
    print("Keyword Arguments Example - Obfuscated with --preserve-param-names")
    print("=" * 70)
    print()

    # Example 1: Regular function with keyword arguments
    print("Example 1: Shipping Cost Calculation")
    print("-" * 70)

    cost1 = calculate_shipping_cost(
        weight_kg=5.0,
        distance_km=100,
        express_shipping=False,
        insurance=False,
    )
    print(f"Standard shipping (5kg, 100km): ${cost1}")

    cost2 = calculate_shipping_cost(
        weight_kg=5.0,
        distance_km=100,
        express_shipping=True,
        insurance=True,
    )
    print(f"Express + Insurance (5kg, 100km): ${cost2}")

    # Can also use positional arguments
    cost3 = calculate_shipping_cost(10.0, 500, True, False)
    print(f"Express only (10kg, 500km): ${cost3}")

    print()

    # Example 2: Function with *args and **kwargs
    print("Example 2: Order Processing with Variable Arguments")
    print("-" * 70)

    order1 = process_order(
        "John Doe",
        "Laptop",
        "Mouse",
        "Keyboard",
        payment_method="paypal",
        express=True,
        gift_wrap=True,
    )
    print(f"Order for {order1['customer']}:")
    print(f"  Items: {', '.join(order1['items'])}")
    print(f"  Payment: {order1['payment_method']}")
    print(f"  Shipping options: {order1['shipping_options']}")

    print()

    # Example 3: Keyword-only arguments
    print("Example 3: API Client Configuration (Keyword-only)")
    print("-" * 70)

    config = configure_api_client(
        api_key="sk_test_123456789",
        endpoint="https://api.example.com/v1",
        timeout=60,
        retry_count=5,
    )
    print(f"API Configuration:")
    print(f"  Endpoint: {config['endpoint']}")
    print(f"  Timeout: {config['timeout']}s")
    print(f"  Retries: {config['retry_count']}")

    print()
    print("=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)
    print()
    print("Note: Parameter names are preserved (weight_kg, distance_km, etc.)")
    print("      but function names and local variables are obfuscated.")
    print()
    print("Benefits:")
    print("  - Keyword arguments work correctly after obfuscation")
    print("  - Function bodies and local variables still protected")
    print("  - Public API compatibility maintained")


if __name__ == "__main__":
    main()
