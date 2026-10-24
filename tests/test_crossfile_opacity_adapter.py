"""Slice C tests: the Pro crossfile-opacity adapter.

The adapter encrypts an explicit set of final (renamed) top-level functions and
rewrites the module so each becomes an L3 stub keyed by the application-provided
runtime key. No user code runs during the build; these tests do exec the
*emitted* module to prove lazy materialization works, always resetting the
process-wide key provider afterwards.
"""

from __future__ import annotations

import secrets

import pytest

import pyobfus_runtime
from pyobfus_pro.crossfile_opacity_adapter import (
    CrossfileOpacityAdapterError,
    encrypt_targets,
)

ENV = "APP_L3_KEY"


def _build(source, targets, key=None):
    key = key or secrets.token_bytes(32)
    return key, encrypt_targets(source, targets, key=key, env_name=ENV)


def _exec_with_provider(source, key):
    """Exec the emitted module with a key provider registered; return its ns."""
    pyobfus_runtime.set_key_provider(lambda: key)
    try:
        ns: dict = {}
        exec(compile(source, "<emitted>", "exec"), ns)  # noqa: S102 -- our own emitted source
        return ns
    finally:
        pyobfus_runtime.set_key_provider(None)


# --------------------------------------------------------------------------
# End-to-end: the encrypted target runs correctly with the app key
# --------------------------------------------------------------------------


def test_encrypted_target_materializes_and_runs():
    src = "def f(x):\n    return x * 3\ndef g(x):\n    return x + 1\n"
    key, res = _build(src, ["f"])
    ns = _exec_with_provider(res.source, key)
    assert ns["f"](5) == 15  # decrypted on first call
    assert ns["f"](5) == 15  # cached path on second call
    assert ns["g"](5) == 6  # untouched plain function


def test_wrong_key_fails_at_first_call_not_import():
    src = "def f(x):\n    return x * 3\n"
    key, res = _build(src, ["f"])
    # A provider that returns a valid-length but wrong key: import succeeds
    # (the key assignment just stores bytes); the first call fails to decrypt.
    pyobfus_runtime.set_key_provider(lambda: secrets.token_bytes(32))
    try:
        ns: dict = {}
        exec(compile(res.source, "<emitted>", "exec"), ns)  # noqa: S102
        with pytest.raises(Exception):
            ns["f"](5)
    finally:
        pyobfus_runtime.set_key_provider(None)


def test_defaults_kwonly_and_annotations_survive():
    src = "def f(a, b=5, *, c=10):\n" "    return a + b + c\n"
    key, res = _build(src, ["f"])
    ns = _exec_with_provider(res.source, key)
    assert ns["f"](1) == 16  # defaults b=5, c=10 applied
    assert ns["f"](1, 2, c=3) == 6


def test_multiple_targets_each_materialize():
    src = "def a(n):\n    return n - 1\ndef b(n):\n    return n * n\ndef c(n):\n    return n\n"
    key, res = _build(src, ["a", "b"])
    assert {t.final_name for t in res.targets} == {"a", "b"}
    ns = _exec_with_provider(res.source, key)
    assert ns["a"](10) == 9
    assert ns["b"](4) == 16
    assert ns["c"](7) == 7


def test_docstring_preserved_on_stub_before_first_call():
    src = 'def f(x):\n    """keep me."""\n    return x\n'
    key, res = _build(src, ["f"])
    pyobfus_runtime.set_key_provider(lambda: key)
    try:
        ns: dict = {}
        exec(compile(res.source, "<emitted>", "exec"), ns)  # noqa: S102
        assert ns["f"].__doc__ == "keep me."  # visible before first call
        assert ns["f"](3) == 3
    finally:
        pyobfus_runtime.set_key_provider(None)


# --------------------------------------------------------------------------
# Direct key expression; the raw key never appears in the source
# --------------------------------------------------------------------------


def test_source_uses_direct_provided_key_expression_not_raw_constant():
    key, res = _build("def f(x):\n    return x\n", ["f"])
    text = res.source
    assert (
        f'{res.provided_key_alias}("{ENV}")' in text or f"{res.provided_key_alias}('{ENV}')" in text
    )
    assert "_LAYER_KEY" not in text
    # No raw key in any common representation.
    import base64

    for rep in (repr(key), base64.b64encode(key).decode(), key.hex()):
        assert rep not in text


def test_future_and_docstring_prologue_stay_ahead_of_injected_code():
    src = (
        '"""module doc."""\n'
        "from __future__ import annotations\n"
        "def f(x: int) -> int:\n    return x + 1\n"
    )
    key, res = _build(src, ["f"])
    lines = [ln for ln in res.source.splitlines() if ln.strip()]
    assert lines[0].strip() == '"""module doc."""'
    assert lines[1].strip() == "from __future__ import annotations"
    # The emitted module still compiles and runs.
    ns = _exec_with_provider(res.source, key)
    assert ns["f"](4) == 5


# --------------------------------------------------------------------------
# Name-collision safety
# --------------------------------------------------------------------------


def test_names_do_not_collide_with_user_identifiers():
    src = (
        "_l3_dispatch = 1\n"
        "provided_key = 2\n"
        "_pyobfus_l3_key = 3\n"
        "def f(x):\n    return x + _l3_dispatch + provided_key + _pyobfus_l3_key\n"
    )
    key, res = _build(src, ["f"])
    assert res.key_name != "_pyobfus_l3_key"
    assert res.dispatch_alias not in {"_l3_dispatch", "provided_key"}
    ns = _exec_with_provider(res.source, key)
    assert ns["f"](0) == 1 + 2 + 3  # user globals intact


# --------------------------------------------------------------------------
# Explicit-target discipline and errors
# --------------------------------------------------------------------------


def test_unknown_target_rejected():
    with pytest.raises(CrossfileOpacityAdapterError):
        _build("def f(x):\n    return x\n", ["nonexistent"])


def test_ambiguous_target_also_bound_at_module_level_rejected():
    # f is both a def and reassigned at module level -> ambiguous.
    with pytest.raises(CrossfileOpacityAdapterError):
        _build("def f(x):\n    return x\nf = None\n", ["f"])


def test_target_also_imported_rejected():
    with pytest.raises(CrossfileOpacityAdapterError):
        _build("from os import f\ndef f(x):\n    return x\n", ["f"])


def test_bad_key_length_rejected():
    with pytest.raises(ValueError):
        encrypt_targets("def f(x):\n    return x\n", ["f"], key=b"short", env_name=ENV)


def test_empty_targets_rejected():
    with pytest.raises(CrossfileOpacityAdapterError):
        _build("def f(x):\n    return x\n", [])


def test_empty_env_name_rejected():
    with pytest.raises(CrossfileOpacityAdapterError):
        encrypt_targets(
            "def f(x):\n    return x\n", ["f"], key=secrets.token_bytes(32), env_name=""
        )


def test_does_not_run_user_module_at_build_time():
    # A top-level reference to an undefined name raises NameError only if the
    # module is executed; compiling it is fine. Building must compile, not exec.
    src = "undefined_name_at_runtime\ndef f(x):\n    return x\n"
    key, res = _build(src, ["f"])
    assert res.targets[0].final_name == "f"


# --------------------------------------------------------------------------
# Regressions for the slice-C review findings
# --------------------------------------------------------------------------


def test_target_rebound_in_module_control_flow_rejected():
    # f is rebound inside module-level control flow -> unstable -> must reject.
    src = "def f():\n    return 1\nif True:\n    f = lambda: 2\n"
    with pytest.raises(CrossfileOpacityAdapterError):
        _build(src, ["f"])


def test_generator_target_rejected():
    with pytest.raises(CrossfileOpacityAdapterError):
        _build("def f():\n    yield 1\n", ["f"])


def test_decorated_target_rejected():
    src = "import functools\n@functools.cache\ndef f():\n    return 1\n"
    with pytest.raises(CrossfileOpacityAdapterError):
        _build(src, ["f"])


def test_trivial_function_bodies_are_accepted():
    # A stub can compile to the same bytecode as a trivial original; that must
    # not be mistaken for "plaintext still shipped".
    for src in ("def f():\n    return None\n", 'def f():\n    """d"""\n    return 123\n'):
        key, res = _build(src, ["f"])
        ns = _exec_with_provider(res.source, key)
        # Runs correctly after decryption.
        assert ns["f"]() in (None, 123)


def test_fresh_names_avoid_except_handler_binding():
    # An except handler binds (then deletes) its name at module scope; a helper
    # reusing it would be deleted out from under the module and NameError.
    src = (
        "try:\n    raise ValueError()\nexcept ValueError as _pyobfus_l3_key:\n    pass\n"
        "def f(x):\n    return x + 1\n"
    )
    key, res = _build(src, ["f"])
    assert res.key_name != "_pyobfus_l3_key"
    ns = _exec_with_provider(res.source, key)  # imports without NameError
    assert ns["f"](1) == 2
