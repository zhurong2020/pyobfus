"""Compose resource loading, business logic, and a fixed plugin."""

from importlib import resources

from .checkout import quote_order
from .plugin_loader import load_plugin


def render_order(tier: str, plugin_name: str = "standard") -> str:
    label = resources.files("storefront.data").joinpath("label.txt").read_text().strip()
    quote = quote_order([("widget", 3), ("gadget", 1)], tier)
    plugin = load_plugin(plugin_name)
    return f"{label}\n{plugin.render(quote)}"
