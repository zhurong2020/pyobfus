"""Isolated build authorization, including benchmark CLI subprocesses."""

import pytest

from tests.conftest import active_pro_trial, isolated_device_id  # noqa: F401


@pytest.fixture(autouse=True)
def _benchmark_build_access(request):
    """Build Pro conditions with a real trial stored under the test's home."""
    request.getfixturevalue("active_pro_trial")
