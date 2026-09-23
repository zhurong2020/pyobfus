"""Distribution-boundary tests for the redistributable runtime."""

from __future__ import annotations

import importlib.abc
import sys


class _BlockProImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):  # noqa: ANN001
        if fullname == "pyobfus_pro" or fullname.startswith("pyobfus_pro."):
            raise AssertionError(f"runtime attempted forbidden import: {fullname}")
        return None


def test_runtime_imports_without_pro() -> None:
    blocker = _BlockProImports()
    saved = {name: module for name, module in sys.modules.items() if name.startswith("pyobfus_")}
    for name in saved:
        sys.modules.pop(name, None)
    sys.meta_path.insert(0, blocker)
    try:
        import pyobfus_runtime

        assert pyobfus_runtime.__version__
        assert pyobfus_runtime.requires_runtime(python_min="3.9") is None
        assert not any(name.startswith("pyobfus_pro") for name in sys.modules)
    finally:
        sys.meta_path.remove(blocker)
        for name in list(sys.modules):
            if name.startswith("pyobfus_"):
                sys.modules.pop(name, None)
        sys.modules.update(saved)


def test_public_runtime_surface_is_explicit() -> None:
    import pyobfus_runtime

    required = {
        "_l3_dispatch",
        "_verify_seal",
        "bind_device_key",
        "expire_check",
        "get_embedded_data",
        "install_scrub_excepthook",
        "period_check",
        "requires_runtime",
        "Vault",
    }
    assert required <= set(pyobfus_runtime.__all__)
