"""Module alias for artifacts generated before pyobfus-runtime."""

import sys
from pyobfus_runtime import binding as _implementation
from pyobfus_runtime.binding import *  # noqa: F403

sys.modules[__name__] = _implementation
