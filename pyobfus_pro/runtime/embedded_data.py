"""Module alias for artifacts generated before pyobfus-runtime."""

import sys
from pyobfus_runtime import embedded_data as _implementation
from pyobfus_runtime.embedded_data import *  # noqa: F403

sys.modules[__name__] = _implementation
