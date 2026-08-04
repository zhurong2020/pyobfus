"""Tests for P2-16 runtime platform-policy guard.

``requires_runtime`` is the pure predicate function; build-fusion injection
(the actual ``--requires-os``/``--requires-python-min``/``--requires-arch``
CLI flags) is exercised end-to-end in test_build_fusion.py.
"""

import pytest

from pyobfus_pro import RuntimePolicyError, requires_runtime


class TestOSConstraint:
    def test_allowed_os_passes(self):
        requires_runtime(os_allowed=("Linux", "Darwin"), current_os="Linux")

    def test_disallowed_os_raises(self):
        with pytest.raises(RuntimePolicyError, match="Windows"):
            requires_runtime(os_allowed=("Linux", "Darwin"), current_os="Windows")

    def test_case_insensitive(self):
        requires_runtime(os_allowed=("linux",), current_os="Linux")

    def test_no_constraint_is_a_noop(self):
        requires_runtime(os_allowed=None, current_os="AnyOS")


class TestPythonMinConstraint:
    def test_meets_minimum_passes(self):
        requires_runtime(python_min="3.10", current_python=(3, 10))

    def test_exceeds_minimum_passes(self):
        requires_runtime(python_min="3.10", current_python=(3, 14))

    def test_below_minimum_raises(self):
        with pytest.raises(RuntimePolicyError, match="3\\.10"):
            requires_runtime(python_min="3.10", current_python=(3, 9))

    def test_malformed_version_string_raises(self):
        with pytest.raises(RuntimePolicyError, match="python_min"):
            requires_runtime(python_min="not-a-version", current_python=(3, 12))


class TestArchConstraint:
    def test_allowed_arch_passes(self):
        requires_runtime(arch_allowed=("x86_64", "arm64"), current_arch="x86_64")

    def test_disallowed_arch_raises(self):
        with pytest.raises(RuntimePolicyError, match="i686"):
            requires_runtime(arch_allowed=("x86_64", "arm64"), current_arch="i686")


class TestCombinedConstraints:
    def test_all_satisfied_passes(self):
        requires_runtime(
            os_allowed=("Linux",),
            python_min="3.9",
            arch_allowed=("x86_64",),
            current_os="Linux",
            current_python=(3, 12),
            current_arch="x86_64",
        )

    def test_first_violated_constraint_raises(self):
        # os check runs before python/arch checks -- OS mismatch surfaces
        # even though python/arch would also fail.
        with pytest.raises(RuntimePolicyError, match="Windows"):
            requires_runtime(
                os_allowed=("Linux",),
                python_min="3.99",
                current_os="Windows",
                current_python=(3, 9),
            )

    def test_no_constraints_never_raises(self):
        requires_runtime()
