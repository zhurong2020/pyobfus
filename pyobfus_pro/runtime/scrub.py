"""Module alias for artifacts generated before pyobfus-runtime."""

import sys
from pyobfus_runtime import scrub as _implementation
from pyobfus_runtime.scrub import *  # noqa: F403

sys.modules[__name__] = _implementation
