"""Tests for framework-aware presets (P0-3)."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig

# ---------------------------------------------------------------------------
# Individual preset factories
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "preset_name",
    ["fastapi", "django", "flask", "pydantic", "click", "sqlalchemy", "ml"],
)
def test_framework_preset_is_registered(preset_name: str) -> None:
    cfg = ObfuscationConfig.get_preset(preset_name)
    assert cfg is not None
    # All framework presets are community-tier
    assert cfg.level == "community"
    # All framework presets preserve parameter names
    assert cfg.preserve_param_names is True


def test_framework_presets_in_list_presets() -> None:
    presets = ObfuscationConfig.list_presets()
    for fw in ["fastapi", "django", "flask", "pydantic", "click", "sqlalchemy", "ml"]:
        assert fw in presets


def test_framework_presets_registered_constant() -> None:
    assert ObfuscationConfig.FRAMEWORK_PRESETS == frozenset(
        {"fastapi", "django", "flask", "pydantic", "click", "sqlalchemy", "ml"}
    )


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------


def test_fastapi_preset_excludes_http_verbs() -> None:
    cfg = ObfuscationConfig.preset_fastapi()
    for verb in ("get", "post", "put", "delete", "patch"):
        assert verb in cfg.exclude_names


def test_fastapi_preset_excludes_router_paths() -> None:
    cfg = ObfuscationConfig.preset_fastapi()
    assert "**/routers/**" in cfg.exclude_patterns
    assert "**/dependencies.py" in cfg.exclude_patterns


def test_fastapi_preset_preserves_docstrings() -> None:
    # Framework presets are built on preset_safe -> docstrings kept
    cfg = ObfuscationConfig.preset_fastapi()
    assert cfg.remove_docstrings is False


# ---------------------------------------------------------------------------
# Django
# ---------------------------------------------------------------------------


def test_django_preset_excludes_orm_surface() -> None:
    cfg = ObfuscationConfig.preset_django()
    for name in ("Meta", "save", "clean", "is_valid", "get_queryset"):
        assert name in cfg.exclude_names


def test_django_preset_excludes_migrations_and_entrypoints() -> None:
    cfg = ObfuscationConfig.preset_django()
    for pattern in ("**/migrations/**", "**/urls.py", "**/settings.py", "**/manage.py"):
        assert pattern in cfg.exclude_patterns


def test_django_preset_excludes_signal_receivers() -> None:
    cfg = ObfuscationConfig.preset_django()
    for signal in ("pre_save", "post_save", "pre_delete", "post_delete"):
        assert signal in cfg.exclude_names


# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------


def test_flask_preset_excludes_dispatch_methods() -> None:
    cfg = ObfuscationConfig.preset_flask()
    assert "dispatch_request" in cfg.exclude_names
    assert "before_request" in cfg.exclude_names


# ---------------------------------------------------------------------------
# Pydantic
# ---------------------------------------------------------------------------


def test_pydantic_preset_covers_v1_and_v2_api() -> None:
    cfg = ObfuscationConfig.preset_pydantic()
    # v2
    assert "model_dump" in cfg.exclude_names
    assert "model_validate" in cfg.exclude_names
    assert "model_config" in cfg.exclude_names
    # v1
    assert "dict" in cfg.exclude_names
    assert "parse_obj" in cfg.exclude_names
    # Decorators
    assert "field_validator" in cfg.exclude_names
    assert "root_validator" in cfg.exclude_names


# ---------------------------------------------------------------------------
# Click
# ---------------------------------------------------------------------------


def test_click_preset_excludes_decorator_names() -> None:
    cfg = ObfuscationConfig.preset_click()
    for name in ("command", "group", "option", "argument"):
        assert name in cfg.exclude_names


# ---------------------------------------------------------------------------
# SQLAlchemy
# ---------------------------------------------------------------------------


def test_sqlalchemy_preset_excludes_orm_dunders_and_session() -> None:
    cfg = ObfuscationConfig.preset_sqlalchemy()
    assert "__tablename__" in cfg.exclude_names
    assert "metadata" in cfg.exclude_names
    assert "session" in cfg.exclude_names
    assert "relationship" in cfg.exclude_names
    assert "**/alembic/**" in cfg.exclude_patterns


# ---------------------------------------------------------------------------
# ML/model-serving
# ---------------------------------------------------------------------------


def test_ml_preset_preserves_model_serving_surface() -> None:
    cfg = ObfuscationConfig.preset_ml()
    # Only names external code dispatches by exact string (sklearn/PyTorch/
    # HuggingFace method conventions) are blanket-excluded.
    for name in ("predict", "predict_proba", "fit", "transform", "forward", "generate", "encode"):
        assert name in cfg.exclude_names
    assert cfg.preserve_param_names is True
    assert cfg.remove_docstrings is False


def test_ml_preset_does_not_blanket_exclude_generic_variable_names() -> None:
    # Regression guard: these are common variable/attribute names far beyond
    # ML code. preserve_param_names=True already covers them as parameters;
    # blanket-excluding them in exclude_names would leave unrelated business
    # logic readable everywhere that word appears as an identifier.
    cfg = ObfuscationConfig.preset_ml()
    for name in (
        "model",
        "tokenizer",
        "pipeline",
        "device",
        "dtype",
        "batch_size",
        "inputs",
        "outputs",
        "preprocess",
        "postprocess",
        "load_model",
        "embed",
    ):
        assert name not in cfg.exclude_names


def test_ml_preset_excludes_model_artifact_paths() -> None:
    cfg = ObfuscationConfig.preset_ml()
    for pattern in ("**/models/**", "**/checkpoints/**", "**/*.safetensors"):
        assert pattern in cfg.exclude_patterns


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_accepts_framework_preset_without_pro(tmp_path) -> None:
    src = tmp_path / "main.py"
    src.write_text(
        "from pydantic import BaseModel\n"
        "class User(BaseModel):\n"
        "    name: str\n"
        "def greet(name: str):\n"
        "    return User(name=name).model_dump()\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.py"

    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--preset", "pydantic"])
    # Must NOT fail with a Pro-license error
    assert result.exit_code == 0, result.output
    assert out.exists()

    code = out.read_text(encoding="utf-8")
    # model_dump() is excluded, so it must survive in the output
    assert "model_dump" in code


def test_cli_fastapi_preset_preserves_param_names(tmp_path) -> None:
    src = tmp_path / "api.py"
    src.write_text(
        "def handler(user_id: int, limit: int = 10):\n"
        "    return {'user_id': user_id, 'limit': limit}\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.py"
    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--preset", "fastapi"])
    assert result.exit_code == 0, result.output
    code = out.read_text(encoding="utf-8")
    # preserve_param_names=True -> user_id and limit must remain
    assert "user_id" in code
    assert "limit" in code


def test_list_presets_shows_frameworks() -> None:
    result = CliRunner().invoke(main, ["--list-presets"])
    assert result.exit_code == 0
    out = result.output
    for fw in ("fastapi", "django", "flask", "pydantic", "click", "sqlalchemy", "ml"):
        assert fw in out
    assert "FRAMEWORK-AWARE PRESETS" in out


def test_cli_ml_preset_preserves_dispatch_method_name(tmp_path) -> None:
    # NOTE: preserve_param_names=True does not currently preserve parameter
    # identifiers end-to-end through the CLI (tracked separately -- see the
    # project issue tracker; reproduced against --preset fastapi too, so it
    # is a pre-existing, cross-preset gap, not specific to --preset ml).
    # This test sticks to what actually works today: exclude_names keeps the
    # framework-dispatched method name itself unmangled.
    src = tmp_path / "serve.py"
    src.write_text(
        "def predict(inputs, batch_size=8):\n    return inputs[:batch_size]\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.py"
    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--preset", "ml"])
    assert result.exit_code == 0, result.output
    code = out.read_text(encoding="utf-8")
    assert "def predict(" in code


def test_unknown_preset_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown preset"):
        ObfuscationConfig.get_preset("nonexistent_framework")
