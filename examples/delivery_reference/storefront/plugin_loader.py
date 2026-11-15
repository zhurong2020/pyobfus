"""Load one of the application's explicitly allowed local plugins."""

from importlib import import_module

PLUGINS = {"standard": "storefront.plugins.standard"}


def load_plugin(name):
    try:
        module_name = PLUGINS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown delivery plugin: {name}") from exc
    return import_module(module_name)
