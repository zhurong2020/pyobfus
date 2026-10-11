"""Storefront package used by the multi-module packaging fixture."""

from .checkout import quote_order

__all__ = ["quote_order"]
