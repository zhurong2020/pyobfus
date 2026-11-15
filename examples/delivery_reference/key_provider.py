"""Application-owned key input for the optional Pro acceptance lane."""

import os

KEY_ENV = "PYOBFUS_DELIVERY_REFERENCE_KEY"


def load_key() -> str:
    """Return the injected test key, failing closed when it is absent."""
    value = os.environ.get(KEY_ENV)
    if not value:
        raise RuntimeError(f"{KEY_ENV} is required for the Pro acceptance lane")
    return value
