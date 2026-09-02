"""Shared per-file content-transform pipeline.

Both the single-file CLI path (``cli._obfuscate_file``) and the cross-file
directory path (``orchestrator._transform_single_file``) run these transforms,
so the two paths can never silently diverge on *which* content transformers
run, in what order, and under which config gates. This module is the single
source of truth for that sequence.

Historically the cross-file (default directory) path applied only the
name/import mapping transforms and silently dropped every content-level
transform — ``--string-encryption``, ``--numeric-obfuscation``,
``--strip-ai-artifacts``, ``--control-flow``, ``--anti-debug``,
``--dead-code`` and the ``commercial``/``trial``/``maximum``/``library``
presets all became no-ops on directories without any warning. Centralising the
sequence here fixes that class of bug once.

Two entry points, matching where they sit relative to name mangling:

* :func:`strip_ai_markers` runs **before** name mangling, so the AI-artifact
  stripper sees original docstrings and attribution dunder names.
* :func:`apply_content_transforms` runs **after** name mangling: string
  encoding (Community), numeric obfuscation (Community), then the Pro block
  (control-flow flattening, import obfuscation, AES string encryption,
  anti-debug, dead-code injection, license embedding).

The v0.5.1 build-fusion PRE/POST passes (opacity/seal/vault/scrub/fingerprint)
are deliberately *not* handled here: they operate on the generated source
string rather than the AST and remain single-file / ``--no-cross-file`` only.
"""

from __future__ import annotations

import ast
from typing import Any, Callable, Dict, Optional

from pyobfus.config import ObfuscationConfig

EchoFn = Optional[Callable[[str], None]]


def strip_ai_markers(
    tree: ast.Module,
    config: ObfuscationConfig,
    analyzer: Any = None,
    stats: Optional[Dict[str, Any]] = None,
    echo: EchoFn = None,
) -> ast.Module:
    """Strip AI provenance markers (Community). Runs before name mangling.

    No-op unless ``config.strip_ai_artifacts`` is set. Populates
    ``ai_docstrings_stripped`` / ``ai_attributions_stripped`` in ``stats``.
    """
    if not config.strip_ai_artifacts:
        return tree

    from pyobfus.transformers.ai_artifact_stripper import AIArtifactStripper

    stripper = AIArtifactStripper(config, analyzer)
    tree = stripper.transform(tree)
    st = stripper.get_statistics()
    if stats is not None:
        stats["ai_docstrings_stripped"] = st.get("docstrings_stripped", 0)
        stats["ai_attributions_stripped"] = st.get("attributions_stripped", 0)
    if echo:
        echo(
            f"  AI artifacts stripped: "
            f"{st.get('docstrings_stripped', 0)} docstring(s), "
            f"{st.get('attributions_stripped', 0)} attribution(s)"
        )
    return tree


def apply_content_transforms(
    tree: ast.Module,
    config: ObfuscationConfig,
    analyzer: Any = None,
    stats: Optional[Dict[str, Any]] = None,
    echo: EchoFn = None,
) -> ast.Module:
    """Apply post-mangle content transforms in the canonical order.

    Order (identical to the single-file path):

    1. String encoding — Community only (``config.level == "community"``).
    2. Numeric / constant obfuscation — Community.
    3. Pro block, only when ``config.level == "pro"``: control-flow
       flattening, import obfuscation, AES string encryption, anti-debug,
       dead-code injection, license embedding. Wrapped so a missing
       ``pyobfus_pro`` install records ``_pro_import_error`` in ``stats`` and
       falls back to Community output rather than crashing.

    Mutates and returns ``tree``; records per-transform counts in ``stats``.
    """
    if stats is None:
        stats = {}

    # 1. String encoding (Community Edition). Runs before numeric so the
    #    numeric obfuscator's emitted float.fromhex() hex strings are not
    #    themselves re-encoded.
    if config.string_encoding and config.level == "community":
        from pyobfus.transformers.string_encoder import StringEncoder

        string_encoder = StringEncoder(config, analyzer)
        tree = string_encoder.transform(tree)
        encoder_stats = string_encoder.get_statistics()
        stats["strings_encoded"] = encoder_stats.get("encoded_strings", 0)
        if echo:
            echo(f"  Encoded strings: {encoder_stats.get('encoded_strings', 0)}")
            if encoder_stats.get("skipped_fstrings", 0) > 0:
                echo(f"  Skipped f-strings: {encoder_stats['skipped_fstrings']}")

    # 2. Numeric / constant obfuscation (Community Edition).
    if config.numeric_obfuscation:
        from pyobfus.transformers.numeric_obfuscator import NumericObfuscator

        numeric_obfuscator = NumericObfuscator(config, analyzer)
        tree = numeric_obfuscator.transform(tree)
        numeric_stats = numeric_obfuscator.get_statistics()
        stats["numbers_obfuscated"] = numeric_stats.get("numbers_obfuscated", 0)
        if echo:
            echo(f"  Numbers obfuscated: {numeric_stats.get('numbers_obfuscated', 0)}")

    # 3. Pro features.
    if config.level == "pro":
        try:
            tree = _apply_pro_transforms(tree, config, analyzer, stats, echo)
        except ImportError as e:
            # Missing pyobfus_pro: record it and fall back to Community output.
            # The caller decides how to surface this (single-file warns on
            # stderr); we must not crash the build.
            stats["_pro_import_error"] = str(e)

    return tree


def _apply_pro_transforms(
    tree: ast.Module,
    config: ObfuscationConfig,
    analyzer: Any,
    stats: Dict[str, Any],
    echo: EchoFn,
) -> ast.Module:
    """Pro AST transforms, in the single-file order. Raises ImportError if the
    ``pyobfus_pro`` package is unavailable (caller handles fallback)."""
    # Control Flow Flattening
    if config.control_flow_flattening:
        from pyobfus_pro.control_flow import ControlFlowFlattener

        cff = ControlFlowFlattener()
        tree = cff.visit(tree)
        stats["control_flow_applied"] = 1
        if echo:
            echo("  Control flow flattening: Applied")

    # Import obfuscation (runtime importlib + encrypted import strings)
    if config.import_obfuscation:
        from pyobfus_pro.import_obfuscation import ImportObfuscator

        import_obfuscator = ImportObfuscator()
        tree = import_obfuscator.transform(tree)
        import_stats = import_obfuscator.get_statistics()
        stats["imports_obfuscated"] = import_stats.get("imports_obfuscated", 0)
        if echo:
            echo(f"  Imports obfuscated: {import_stats.get('imports_obfuscated', 0)}")

    # String encryption (AES-256)
    if config.string_encryption:
        from pyobfus_pro.string_aes import StringAESEncryptor

        string_encryptor = StringAESEncryptor(config, analyzer)
        tree = string_encryptor.transform(tree)
        encryptor_stats = string_encryptor.get_statistics()
        stats["strings_encrypted"] = encryptor_stats.get("encrypted_strings", 0)
        if echo:
            echo(f"  Encrypted strings: {encryptor_stats.get('encrypted_strings', 0)}")

    # Anti-debugging checks
    if config.anti_debug:
        from pyobfus_pro.anti_debug import AntiDebugInjector

        anti_debug = AntiDebugInjector(config, analyzer)
        tree = anti_debug.transform(tree)
        anti_debug_stats = anti_debug.get_statistics()
        stats["anti_debug_checks"] = anti_debug_stats.get("injected_functions", 0) + 1
        if echo:
            echo(f"  Anti-debug checks: {anti_debug_stats.get('injected_functions', 0) + 1}")

    # Dead Code Injection
    if config.dead_code_injection:
        from pyobfus_pro.dead_code import DeadCodeInjector

        dead_code_injector = DeadCodeInjector()
        tree = dead_code_injector.visit(tree)
        dci_stats = dead_code_injector.get_statistics()
        stats["dead_code_injected"] = dci_stats.get("injected_statements", 0)
        if echo:
            echo(f"  Dead code injection: {dci_stats.get('injected_statements', 0)} statements")

    # License Embedding (applied last to inject at module start)
    license_embed_enabled = (
        config.license_expire or config.license_bind_machine or config.license_max_runs > 0
    )
    if license_embed_enabled:
        from pyobfus_pro.license_embed import LicenseEmbedder, LicenseEmbedConfig

        embed_config = LicenseEmbedConfig(
            expire_date=config.license_expire,
            bind_machine=config.license_bind_machine,
            max_runs=config.license_max_runs,
        )
        license_embedder = LicenseEmbedder(embed_config)
        tree = license_embedder.visit(tree)
        if echo:
            embed_info = []
            if config.license_expire:
                embed_info.append(f"expires {config.license_expire}")
            if config.license_bind_machine:
                fp = license_embedder.get_current_fingerprint()
                embed_info.append(f"bound to {fp[:8]}...")
            if config.license_max_runs > 0:
                embed_info.append(f"max {config.license_max_runs} runs")
            echo(f"  License embedding: {', '.join(embed_info)}")

    return tree
