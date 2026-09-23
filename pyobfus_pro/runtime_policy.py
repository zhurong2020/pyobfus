"""Module alias for artifacts generated before pyobfus-runtime."""

import sys
from pyobfus_runtime import policy as _implementation
from pyobfus_runtime.policy import *  # noqa: F403

sys.modules[__name__] = _implementation
