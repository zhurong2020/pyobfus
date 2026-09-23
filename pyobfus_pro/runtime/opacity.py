"""Module alias for artifacts generated before pyobfus-runtime."""

import sys
from pyobfus_runtime import opacity as _implementation
from pyobfus_runtime.opacity import *  # noqa: F403
from pyobfus_runtime.opacity import _decrypt_code, _encrypt_code, _l3_dispatch  # noqa: F401

sys.modules[__name__] = _implementation
