"""Entry point for the verifiable delivery reference application."""

import sys

from storefront.app import render_order

if __name__ == "__main__":
    selected_tier = sys.argv[1] if len(sys.argv) > 1 else "pro"
    print(render_order(selected_tier))
