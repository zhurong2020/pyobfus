"""Tests for pyobfus exceptions module."""

import pytest

from pyobfus.exceptions import (
    PyObfusError,
    ParseError,
    AnalysisError,
    TransformError,
    GenerationError,
    ConfigurationError,
    LimitExceededError,
)


class TestPyObfusError:
    def test_base_error(self):
        e = PyObfusError("test error")
        assert str(e) == "test error"
        assert isinstance(e, Exception)


class TestParseError:
    def test_parse_error_message(self):
        original = SyntaxError("unexpected EOF")
        e = ParseError("test.py", original)
        assert "test.py" in str(e)
        assert "unexpected EOF" in str(e)
        assert e.file_path == "test.py"
        assert e.original_error is original

    def test_parse_error_is_pyobfus_error(self):
        e = ParseError("test.py", ValueError("bad"))
        assert isinstance(e, PyObfusError)


class TestGenerationError:
    def test_generation_error_with_node(self):
        e = GenerationError("failed to unparse", "FunctionDef")
        assert "failed to unparse" in str(e)
        assert "FunctionDef" in str(e)
        assert e.ast_node == "FunctionDef"

    def test_generation_error_without_node(self):
        e = GenerationError("generic failure")
        assert "generic failure" in str(e)


class TestLimitExceededError:
    def test_limit_exceeded_fields(self):
        e = LimitExceededError("file_count", 10, 5)
        assert e.limit_type == "file_count"
        assert e.current == 10
        assert e.max_allowed == 5

    def test_limit_exceeded_message(self):
        e = LimitExceededError("lines_of_code", 2000, 1000)
        msg = str(e)
        assert "lines_of_code" in msg
        assert "2000" in msg
        assert "1000" in msg
        assert "Pro" in msg


class TestOtherErrors:
    def test_analysis_error(self):
        e = AnalysisError("symbol conflict")
        assert isinstance(e, PyObfusError)

    def test_transform_error(self):
        e = TransformError("transform failed")
        assert isinstance(e, PyObfusError)

    def test_configuration_error(self):
        e = ConfigurationError("bad config")
        assert isinstance(e, PyObfusError)
