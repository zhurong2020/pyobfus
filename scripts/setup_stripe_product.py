#!/usr/bin/env python3
"""
Setup Stripe product and price for pyobfus Professional Edition.
Creates product and price in live mode if they don't exist.
"""

import os
import stripe

def load_env_file():
    """Load .env.stripe file."""
    env_vars = {}
    with open('.env.stripe', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip()
    return env_vars

def create_product_and_price(mode='live'):
    """Create product and price in specified mode."""
    env_vars = load_env_file()

    if mode == 'live':
        stripe.api_key = env_vars['STRIPE_LIVE_SECRET_KEY']
        print("[INFO] Using LIVE mode")
    else:
        stripe.api_key = env_vars['STRIPE_TEST_SECRET_KEY']
        print("[INFO] Using TEST mode")

    print("\n" + "=" * 60)
    print("Creating Stripe Product and Price")
    print("=" * 60)

    # Product details
    product_name = "pyobfus Professional Edition"
    product_description = "Professional license for pyobfus - Advanced Python code obfuscation with AES-256 encryption and anti-debugging features"

    # Price details
    unit_amount = 4500  # $45.00 in cents
    currency = "usd"

    try:
        # Create product
        print("\n[INFO] Creating product...")
        product = stripe.Product.create(
            name=product_name,
            description=product_description,
            metadata={
                'features': 'AES-256 String Encryption, Anti-Debugging Checks, Lifetime Updates',
                'license_type': 'Professional',
                'max_devices': '3'
            }
        )
        print(f"[SUCCESS] Product created!")
        print(f"   Product ID: {product.id}")
        print(f"   Name: {product.name}")

        # Create price
        print("\n[INFO] Creating price...")
        price = stripe.Price.create(
            product=product.id,
            unit_amount=unit_amount,
            currency=currency,
            metadata={
                'price_description': 'One-time payment for lifetime license'
            }
        )
        print(f"[SUCCESS] Price created!")
        print(f"   Price ID: {price.id}")
        print(f"   Amount: ${price.unit_amount/100:.2f} {price.currency.upper()}")

        # Display configuration
        print("\n" + "=" * 60)
        print("Configuration Complete!")
        print("=" * 60)
        print("\n📋 Update .env.stripe with:")
        print(f"   STRIPE_PRODUCT_ID={product.id}")
        print(f"   STRIPE_PRICE_ID={price.id}")

        print("\n🔗 Stripe Dashboard:")
        if mode == 'live':
            print(f"   Product: https://dashboard.stripe.com/products/{product.id}")
            print(f"   Prices: https://dashboard.stripe.com/prices")
        else:
            print(f"   Product: https://dashboard.stripe.com/test/products/{product.id}")
            print(f"   Prices: https://dashboard.stripe.com/test/prices")

        return product, price

    except Exception as e:
        print(f"[ERROR] Failed to create product/price: {e}")
        return None, None

if __name__ == "__main__":
    import sys

    mode = 'live'
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        mode = 'test'

    product, price = create_product_and_price(mode)

    if product and price:
        print("\n✅ Setup complete!")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
