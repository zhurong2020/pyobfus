"""Entry script: prints a quote, or raises for an unknown tier."""

import sys

from storefront.checkout import quote_order

if __name__ == "__main__":
    tier = sys.argv[1] if len(sys.argv) > 1 else "pro"
    print(quote_order([("widget", 3), ("gadget", 1)], tier))
