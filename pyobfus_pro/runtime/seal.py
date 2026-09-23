"""Module alias for artifacts generated before pyobfus-runtime."""

import sys
from pyobfus_runtime import seal as _implementation
from pyobfus_runtime.seal import *  # noqa: F403
from pyobfus_runtime.seal import (  # noqa: F401
    _compute_seal,
    _compute_seal_bytes,
    _verify_seal,
)

sys.modules[__name__] = _implementation
