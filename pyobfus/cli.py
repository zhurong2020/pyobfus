"""
Command-line interface for pyobfus.

Provides a user-friendly CLI for obfuscating Python files and projects.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from pyobfus import __version__
from pyobfus.config import ObfuscationConfig
from pyobfus.constants import STRIPE_PAYMENT_LINK, PRO_PRICE_USD
from pyobfus.config_templates import get_template, list_templates
from pyobfus.config_validator import validate_config_file, find_config_file
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.parser import ASTParser
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus.exceptions import LimitExceededError, PyObfusError
from pyobfus.transformers.name_mangler import NameMangler
from pyobfus.utils import filter_python_files
from pyobfus.trial import is_trial_active, get_trial_expiry_message

# Check if Pro edition is available
try:
    import pyobfus_pro  # type: ignore[import]

    PRO_AVAILABLE = True
except ImportError:
    pyobfus_pro = None  # type: ignore[assignment]
    PRO_AVAILABLE = False


@click.command()
@click.argument("input_path", type=click.Path(exists=True), required=False)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(),
    help="Output file or directory path",
)
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=True),
    help="Configuration file (YAML)",
)
@click.option(
    "--init-config",
    "init_config_template",
    type=click.Choice(["django", "flask", "library", "general"], case_sensitive=False),
    help="Generate configuration template (django, flask, library, general)",
)
@click.option(
    "--validate-config",
    "validate_config_path",
    type=click.Path(exists=True),
    help="Validate a configuration file",
)
@click.option(
    "--level",
    type=click.Choice(["community", "pro"], case_sensitive=False),
    default="community",
    help="Obfuscation level (default: community)",
)
@click.option(
    "--remove-docstrings/--keep-docstrings",
    default=True,
    help="Remove docstrings (default: remove)",
)
@click.option(
    "--remove-comments/--keep-comments",
    default=True,
    help="Remove comments (default: remove)",
)
@click.option(
    "--name-prefix",
    default="I",
    help="Prefix for obfuscated names (default: I)",
)
@click.option(
    "--preserve-param-names",
    is_flag=True,
    help="Preserve parameter names to allow keyword arguments after obfuscation",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview obfuscation without writing output",
)
@click.option(
    "--cross-file/--no-cross-file",
    default=True,
    help="Enable cross-file import mapping (default: enabled)",
)
@click.option(
    "--upgrade",
    is_flag=True,
    help="Show Pro edition features and purchase information",
)
@click.option(
    "--control-flow",
    is_flag=True,
    help="Enable control flow flattening (Pro feature)",
)
@click.option(
    "--string-encryption",
    is_flag=True,
    help="Enable AES-256 string encryption (Pro feature)",
)
@click.option(
    "--anti-debug",
    is_flag=True,
    help="Enable anti-debugging protection (Pro feature)",
)
@click.option(
    "--dead-code",
    is_flag=True,
    help="Enable dead code injection (Pro feature)",
)
@click.option(
    "--expire",
    type=str,
    help="Set expiration date for obfuscated code (YYYY-MM-DD format, Pro feature)",
)
@click.option(
    "--bind-machine",
    is_flag=True,
    help="Bind obfuscated code to current machine (Pro feature)",
)
@click.option(
    "--max-runs",
    type=int,
    default=0,
    help="Set maximum run count for obfuscated code (0=unlimited, Pro feature)",
)
@click.option(
    "--preset",
    type=click.Choice(
        ["trial", "commercial", "library", "maximum", "safe", "balanced", "aggressive"],
        case_sensitive=False,
    ),
    help="Use a preset configuration (Pro feature for trial/commercial/library/maximum)",
)
@click.option(
    "--list-presets",
    is_flag=True,
    help="List all available presets with descriptions",
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show obfuscation statistics summary",
)
@click.version_option(version=__version__, prog_name="pyobfus")
def main(
    input_path: Optional[str],
    output_path: Optional[str],
    config_path: Optional[str],
    init_config_template: Optional[str],
    validate_config_path: Optional[str],
    level: str,
    remove_docstrings: bool,
    remove_comments: bool,
    name_prefix: str,
    preserve_param_names: bool,
    verbose: bool,
    dry_run: bool,
    cross_file: bool,
    upgrade: bool,
    control_flow: bool,
    string_encryption: bool,
    anti_debug: bool,
    dead_code: bool,
    expire: Optional[str],
    bind_machine: bool,
    max_runs: int,
    preset: Optional[str],
    list_presets: bool,
    stats: bool,
) -> None:
    """
    Obfuscate Python source code.

    INPUT_PATH: Python file or directory to obfuscate

    \b
    Examples:
      pyobfus script.py -o script_obf.py
      pyobfus src/ -o dist/
      pyobfus src/ -o dist/ --config pyobfus.yaml
      pyobfus --init-config django
      pyobfus --validate-config pyobfus.yaml
    """
    # Handle --upgrade: Show Pro edition information
    if upgrade:
        _handle_upgrade()
        return

    # Handle --list-presets: Show available presets
    if list_presets:
        _handle_list_presets()
        return

    # Handle --init-config: Generate configuration template
    if init_config_template:
        _handle_init_config(init_config_template)
        return

    # Handle --validate-config: Validate configuration file
    if validate_config_path:
        _handle_validate_config(validate_config_path)
        return

    # For obfuscation, input_path and output_path are required
    if not input_path:
        click.echo("Error: Missing argument 'INPUT_PATH'.", err=True)
        click.echo("\nUsage: pyobfus INPUT_PATH -o OUTPUT_PATH", err=True)
        click.echo("\nOr use utility commands:", err=True)
        click.echo("  pyobfus --init-config django     Generate Django config template", err=True)
        click.echo("  pyobfus --validate-config FILE   Validate config file", err=True)
        sys.exit(1)

    if not output_path:
        click.echo("Error: Missing required option '-o' / '--output'.", err=True)
        sys.exit(1)

    try:
        # Load configuration
        effective_config_path = config_path

        # Auto-discover config if not specified
        if not config_path:
            auto_config = _try_auto_discover_config(verbose)
            if auto_config:
                effective_config_path = str(auto_config)

        if effective_config_path:
            config = ObfuscationConfig.from_file(Path(effective_config_path))
            if verbose:
                click.echo(f"Loaded configuration from: {effective_config_path}")
        elif preset:
            # Use preset configuration
            pro_presets = ["trial", "commercial", "library", "maximum"]
            if preset.lower() in pro_presets:
                # Check Pro access for Pro presets
                trial_active = is_trial_active()
                has_pro_access = trial_active or PRO_AVAILABLE

                if not has_pro_access:
                    click.echo(
                        f"Error: The '{preset}' preset requires Pro edition or active trial.",
                        err=True,
                    )
                    click.echo("\nStart a free 5-day trial:", err=True)
                    click.echo("  pyobfus-trial start", err=True)
                    click.echo(
                        f"\nOr purchase a license (${PRO_PRICE_USD} one-time):",
                        err=True,
                    )
                    click.echo(f"  {STRIPE_PAYMENT_LINK}", err=True)
                    sys.exit(1)

            config = ObfuscationConfig.get_preset(preset.lower())
            if verbose:
                click.echo(f"Using preset: {preset}")
        else:
            # Use default based on level
            if level == "pro":
                # Check trial status first (refreshed at runtime)
                trial_active = is_trial_active()

                if trial_active:
                    # Trial is active - allow Pro features without license
                    trial_msg = get_trial_expiry_message()
                    if verbose:
                        click.echo(f"Trial mode: {trial_msg}")
                    config = ObfuscationConfig.pro_edition()
                elif PRO_AVAILABLE:
                    # Pro edition installed - verify license
                    assert pyobfus_pro is not None, "pyobfus_pro module should be loaded"

                    try:
                        # Get cached license status (unmasked to get full key)
                        cached_status = pyobfus_pro.get_license_status(masked=False)
                        if not cached_status:
                            click.echo(
                                "Error: No license key found. Please register your license first.",
                                err=True,
                            )
                            click.echo(
                                "\nTo register your license key, run:",
                                err=True,
                            )
                            click.echo(
                                "  pyobfus-license register YOUR-LICENSE-KEY",
                                err=True,
                            )
                            click.echo(
                                "\nOr start a free 5-day trial:",
                                err=True,
                            )
                            click.echo(
                                "  pyobfus-trial start",
                                err=True,
                            )
                            click.echo(
                                "\nPurchase a license at: https://github.com/zhurong2020/pyobfus",
                                err=True,
                            )
                            sys.exit(1)

                        # Verify the cached license (use unmasked key)
                        full_license_key = cached_status["key"]
                        license_result = pyobfus_pro.verify_license(full_license_key)

                        if verbose:
                            click.echo(f"License verified: {license_result['message']}")

                    except pyobfus_pro.LicenseError as e:
                        click.echo(
                            f"Error: License verification failed - {e}",
                            err=True,
                        )
                        click.echo(
                            "\nPlease check your license status with: pyobfus-license status",
                            err=True,
                        )
                        click.echo(
                            "Or register a new license: pyobfus-license register YOUR-LICENSE-KEY",
                            err=True,
                        )
                        click.echo(
                            "\nOr start a free 5-day trial: pyobfus-trial start",
                            err=True,
                        )
                        sys.exit(1)

                    config = ObfuscationConfig.pro_edition()
                else:
                    # No Pro installed and no trial - show options
                    click.echo(
                        "Error: Pro edition features require a license or active trial.",
                        err=True,
                    )
                    click.echo(
                        "\nStart a free 5-day trial (no registration required):",
                        err=True,
                    )
                    click.echo(
                        "  pyobfus-trial start",
                        err=True,
                    )
                    click.echo(
                        "\nOr purchase a license ($45 one-time):",
                        err=True,
                    )
                    click.echo(
                        f"  {STRIPE_PAYMENT_LINK}",
                        err=True,
                    )
                    sys.exit(1)
            else:
                config = ObfuscationConfig.community_edition()

        # Override config with CLI options
        config.level = level
        config.remove_docstrings = remove_docstrings
        config.remove_comments = remove_comments
        config.name_prefix = name_prefix
        config.preserve_param_names = preserve_param_names

        # Handle Pro feature flags
        license_embedding_requested = expire or bind_machine or max_runs > 0
        pro_features_requested = (
            control_flow
            or string_encryption
            or anti_debug
            or dead_code
            or license_embedding_requested
        )
        if pro_features_requested:
            # Check if user has Pro access (license or trial)
            trial_active = is_trial_active()
            has_pro_access = trial_active or PRO_AVAILABLE

            if not has_pro_access:
                click.echo(
                    "Error: Pro features require a license or active trial.",
                    err=True,
                )
                click.echo(
                    "\nStart a free 5-day trial (no registration required):",
                    err=True,
                )
                click.echo("  pyobfus-trial start", err=True)
                click.echo(
                    f"\nOr purchase a license (${PRO_PRICE_USD} one-time):",
                    err=True,
                )
                click.echo(f"  {STRIPE_PAYMENT_LINK}", err=True)
                sys.exit(1)

            # User has Pro access - enable requested features
            config.level = "pro"
            if control_flow:
                config.control_flow_flattening = True
                if verbose:
                    click.echo("Enabled: Control Flow Flattening")
            if string_encryption:
                config.string_encryption = True
                if verbose:
                    click.echo("Enabled: AES-256 String Encryption")
            if anti_debug:
                config.anti_debug = True
                if verbose:
                    click.echo("Enabled: Anti-Debugging Protection")
            if dead_code:
                config.dead_code_injection = True
                if verbose:
                    click.echo("Enabled: Dead Code Injection")

            # License embedding options
            if expire:
                config.license_expire = expire
                if verbose:
                    click.echo(f"Enabled: License Expiration ({expire})")
            if bind_machine:
                config.license_bind_machine = True
                if verbose:
                    click.echo("Enabled: Machine Binding")
            if max_runs > 0:
                config.license_max_runs = max_runs
                if verbose:
                    click.echo(f"Enabled: Run Limit ({max_runs} runs)")

        # Determine if input is file or directory
        input_path_obj = Path(input_path)
        output_path_obj = Path(output_path)

        if dry_run:
            click.echo("\n[DRY RUN MODE] - No files will be written")

        # Initialize statistics
        obfuscation_stats: dict = {
            "files_processed": 0,
            "total_names_obfuscated": 0,
            "strings_encoded": 0,
            "strings_encrypted": 0,
            "control_flow_applied": 0,
            "dead_code_injected": 0,
            "anti_debug_checks": 0,
        }

        if input_path_obj.is_file():
            # Single file obfuscation
            file_stats = _obfuscate_file(input_path_obj, output_path_obj, config, verbose, dry_run)
            if file_stats:
                obfuscation_stats["files_processed"] = 1
                for key, value in file_stats.items():
                    if key in obfuscation_stats:
                        obfuscation_stats[key] += value
        elif input_path_obj.is_dir():
            # Directory obfuscation - use CrossFileOrchestrator if enabled
            if cross_file:
                dir_stats = _obfuscate_directory_crossfile(
                    input_path_obj, output_path_obj, config, verbose, dry_run
                )
                if dir_stats:
                    obfuscation_stats.update(dir_stats)
            else:
                # Legacy single-file mode
                dir_stats = _obfuscate_directory(
                    input_path_obj, output_path_obj, config, verbose, dry_run
                )
                if dir_stats:
                    obfuscation_stats.update(dir_stats)
        else:
            click.echo(f"Error: {input_path} is neither a file nor a directory", err=True)
            sys.exit(1)

        if not dry_run:
            click.echo("\nObfuscation completed successfully!")
        else:
            click.echo("\n[DRY RUN] Preview completed. Use without --dry-run to write files.")

        # Display statistics if requested
        if stats and not dry_run:
            _display_stats(obfuscation_stats, config)

        # Subtle Pro feature hint (only for Community users without trial)
        if level == "community" and not PRO_AVAILABLE and not is_trial_active():
            click.echo("\nTip: Try Pro FREE for 5 days - AES-256 encryption & anti-debugging")
            click.echo("     Start trial: pyobfus-trial start")

    except LimitExceededError as e:
        click.echo(f"\nError: {e}", err=True)
        click.echo("\nConsider upgrading to pyobfus Pro for unlimited obfuscation.")
        sys.exit(1)
    except PyObfusError as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nUnexpected error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def _obfuscate_file(
    input_file: Path,
    output_file: Path,
    config: ObfuscationConfig,
    verbose: bool,
    dry_run: bool = False,
) -> dict:
    """
    Obfuscate a single Python file.

    Args:
        input_file: Input Python file
        output_file: Output file path
        config: Obfuscation configuration
        verbose: Verbose output
        dry_run: Preview mode without writing files

    Returns:
        Dictionary with obfuscation statistics
    """
    file_stats: dict = {
        "total_names_obfuscated": 0,
        "strings_encoded": 0,
        "strings_encrypted": 0,
        "control_flow_applied": 0,
        "dead_code_injected": 0,
        "anti_debug_checks": 0,
    }
    if verbose:
        click.echo(f"\nObfuscating: {input_file}")

    # Parse file
    tree = ASTParser.parse_file(input_file)

    # Count lines for Community Edition limits
    line_count = ASTParser.count_lines(tree)
    if config.max_total_loc and line_count > config.max_total_loc:
        raise LimitExceededError("lines_of_code", line_count, config.max_total_loc)

    # Analyze symbols
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    if verbose:
        stats = analyzer.get_statistics()
        click.echo(f"  Total names: {stats['total_names']}")
        click.echo(f"  Obfuscatable names: {stats['obfuscatable_names']}")
        click.echo(f"  Excluded names: {stats['excluded_names']}")

    # Transform - Apply transformations in sequence
    transformed_tree = tree

    # 1. Name mangling (always applied)
    mangler = NameMangler(config, analyzer)
    transformed_tree = mangler.transform(transformed_tree)
    file_stats["total_names_obfuscated"] = mangler.get_transformation_count()

    if verbose:
        click.echo(f"  Name transformations: {mangler.get_transformation_count()}")

    # 2. String encoding (Community Edition - if enabled)
    if config.string_encoding and config.level == "community":
        from pyobfus.transformers.string_encoder import StringEncoder

        string_encoder = StringEncoder(config, analyzer)
        transformed_tree = string_encoder.transform(transformed_tree)
        encoder_stats = string_encoder.get_statistics()
        file_stats["strings_encoded"] = encoder_stats.get("encoded_strings", 0)

        if verbose:
            click.echo(f"  Encoded strings: {encoder_stats['encoded_strings']}")
            if encoder_stats["skipped_fstrings"] > 0:
                click.echo(f"  Skipped f-strings: {encoder_stats['skipped_fstrings']}")

    # 3. Pro features (if enabled)
    if config.level == "pro":
        try:
            # Control Flow Flattening
            if config.control_flow_flattening:
                from pyobfus_pro.control_flow import ControlFlowFlattener

                cff = ControlFlowFlattener()
                transformed_tree = cff.visit(transformed_tree)
                file_stats["control_flow_applied"] = 1

                if verbose:
                    click.echo("  Control flow flattening: Applied")

            # String encryption (AES-256)
            if config.string_encryption:
                from pyobfus_pro.string_aes import StringAESEncryptor

                string_encryptor = StringAESEncryptor(config, analyzer)
                transformed_tree = string_encryptor.transform(transformed_tree)
                encryptor_stats = string_encryptor.get_statistics()
                file_stats["strings_encrypted"] = encryptor_stats.get("encrypted_strings", 0)

                if verbose:
                    click.echo(f"  Encrypted strings: {encryptor_stats['encrypted_strings']}")

            # Anti-debugging checks
            if config.anti_debug:
                from pyobfus_pro.anti_debug import AntiDebugInjector

                anti_debug = AntiDebugInjector(config, analyzer)
                transformed_tree = anti_debug.transform(transformed_tree)
                anti_debug_stats = anti_debug.get_statistics()
                file_stats["anti_debug_checks"] = anti_debug_stats.get("injected_functions", 0) + 1

                if verbose:
                    click.echo(f"  Anti-debug checks: {anti_debug_stats['injected_functions'] + 1}")

            # Dead Code Injection
            if config.dead_code_injection:
                from pyobfus_pro.dead_code import DeadCodeInjector

                dead_code_injector = DeadCodeInjector()
                transformed_tree = dead_code_injector.visit(transformed_tree)
                dci_stats = dead_code_injector.get_statistics()
                file_stats["dead_code_injected"] = dci_stats.get("injected_statements", 0)

                if verbose:
                    click.echo(
                        f"  Dead code injection: {dci_stats['injected_statements']} statements"
                    )

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
                transformed_tree = license_embedder.visit(transformed_tree)

                if verbose:
                    embed_info = []
                    if config.license_expire:
                        embed_info.append(f"expires {config.license_expire}")
                    if config.license_bind_machine:
                        fp = license_embedder.get_current_fingerprint()
                        embed_info.append(f"bound to {fp[:8]}...")
                    if config.license_max_runs > 0:
                        embed_info.append(f"max {config.license_max_runs} runs")
                    click.echo(f"  License embedding: {', '.join(embed_info)}")

        except ImportError as e:
            click.echo(f"\n⚠️  Pro features not available: {e}", err=True)
            click.echo("Please ensure pyobfus Pro is properly installed.", err=True)
            if verbose:
                click.echo("Pro features require additional modules in pyobfus_pro/", err=True)
            # Continue with Community Edition features only

    # Generate code
    obfuscated_code = CodeGenerator.generate(transformed_tree)

    # Add header comment
    obfuscated_code = CodeGenerator.add_header_comment(obfuscated_code, str(input_file))

    # Write output
    if not dry_run:
        CodeGenerator.generate_to_file(transformed_tree, output_file)
        if verbose:
            click.echo(f"  Output: {output_file}")
    else:
        if verbose:
            click.echo(f"  Would write to: {output_file}")
            click.echo("  Preview (first 10 lines):")
            lines = obfuscated_code.split("\n")[:10]
            for line in lines:
                click.echo(f"    {line}")

    return file_stats


def _obfuscate_directory(
    input_dir: Path,
    output_dir: Path,
    config: ObfuscationConfig,
    verbose: bool,
    dry_run: bool = False,
) -> dict:
    """
    Obfuscate all Python files in a directory (legacy single-file mode).

    Args:
        input_dir: Input directory
        output_dir: Output directory
        config: Obfuscation configuration
        verbose: Verbose output
        dry_run: Preview mode without writing files

    Returns:
        Dictionary with aggregated obfuscation statistics
    """
    dir_stats: dict = {
        "files_processed": 0,
        "total_names_obfuscated": 0,
        "strings_encoded": 0,
        "strings_encrypted": 0,
        "control_flow_applied": 0,
        "dead_code_injected": 0,
        "anti_debug_checks": 0,
    }

    # Find all Python files, excluding patterns from config
    python_files = filter_python_files(input_dir, config.exclude_patterns)

    if not python_files:
        click.echo(f"No Python files found in {input_dir}")
        return dir_stats

    if verbose and config.exclude_patterns:
        click.echo(f"Excluding patterns: {', '.join(config.exclude_patterns)}")

    # Check Community Edition file limit
    if config.max_files and len(python_files) > config.max_files:
        raise LimitExceededError("file_count", len(python_files), config.max_files)

    click.echo(f"\nFound {len(python_files)} Python file(s) to obfuscate")

    # Check total LOC limit
    if config.max_total_loc:
        total_loc = 0
        for file in python_files:
            try:
                tree = ASTParser.parse_file(file)
                total_loc += ASTParser.count_lines(tree)
            except Exception:
                pass  # Count what we can

        if total_loc > config.max_total_loc:
            raise LimitExceededError("total_lines_of_code", total_loc, config.max_total_loc)

    # Obfuscate each file
    for python_file in python_files:
        # Calculate relative path
        rel_path = python_file.relative_to(input_dir)
        output_file = output_dir / rel_path

        try:
            file_stats = _obfuscate_file(python_file, output_file, config, verbose, dry_run)
            dir_stats["files_processed"] += 1
            for key, value in file_stats.items():
                if key in dir_stats:
                    dir_stats[key] += value
        except PyObfusError as e:
            click.echo(f"  Warning: Failed to obfuscate {python_file}: {e}", err=True)
            # Continue with other files

    return dir_stats


def _obfuscate_directory_crossfile(
    input_dir: Path,
    output_dir: Path,
    config: ObfuscationConfig,
    verbose: bool,
    dry_run: bool = False,
) -> dict:
    """
    Obfuscate directory with cross-file import mapping using CrossFileOrchestrator.

    Args:
        input_dir: Input directory
        output_dir: Output directory
        config: Obfuscation configuration
        verbose: Verbose output
        dry_run: Preview mode without writing files

    Returns:
        Dictionary with obfuscation statistics
    """
    dir_stats: dict = {
        "files_processed": 0,
        "total_names_obfuscated": 0,
        "strings_encoded": 0,
        "strings_encrypted": 0,
        "control_flow_applied": 0,
        "dead_code_injected": 0,
        "anti_debug_checks": 0,
    }

    if verbose:
        click.echo("\nUsing cross-file obfuscation mode")
        click.echo(f"Input:  {input_dir}")
        click.echo(f"Output: {output_dir}")

    # Create orchestrator
    orchestrator = CrossFileOrchestrator(config)

    try:
        # Phase 1: Scan
        if verbose:
            click.echo("\n[Phase 1] Scanning project...")

        global_table = orchestrator.phase1_scan(input_dir)

        stats = orchestrator.get_statistics()
        dir_stats["files_processed"] = stats.get("files_discovered", 0)
        dir_stats["total_names_obfuscated"] = stats.get("total_exports", 0)

        click.echo(f"\nDiscovered {stats['files_discovered']} Python file(s)")
        click.echo(f"  Modules: {stats['total_modules']}")
        click.echo(f"  Exports: {stats['total_exports']}")

        # Validate
        is_valid, errors = global_table.validate()
        if not is_valid:
            click.echo("\nWarning: Some imports cannot be resolved:", err=True)
            for error in errors[:5]:  # Show first 5 errors
                click.echo(f"  - {error}", err=True)
            if len(errors) > 5:
                click.echo(f"  ... and {len(errors) - 5} more", err=True)
            click.echo("\nThese may be standard library or external imports (OK to continue)")

        if dry_run:
            click.echo("\n[DRY RUN] Would transform files with these mappings:")
            for module in sorted(global_table.get_all_modules())[:5]:
                exports = global_table.get_module_exports(module)
                if exports:
                    click.echo(f"\n  Module: {module}")
                    for orig, obf in list(exports.items())[:3]:
                        click.echo(f"    {orig} -> {obf}")
            if stats["total_modules"] > 5:
                click.echo(f"\n  ... and {stats['total_modules'] - 5} more modules")
            return dir_stats

        # Phase 2: Transform
        if verbose:
            click.echo("\n[Phase 2] Transforming files...")

        orchestrator.phase2_transform(input_dir, output_dir)

        click.echo(f"\nSuccessfully obfuscated {stats['files_discovered']} file(s)")

        if verbose:
            click.echo(f"\nOutput written to: {output_dir}")

        return dir_stats

    except Exception as e:
        click.echo(f"\nError during cross-file obfuscation: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def _handle_upgrade() -> None:
    """
    Display Pro edition features and purchase information.
    """
    # Check current status
    trial_active = is_trial_active()
    trial_msg = get_trial_expiry_message()

    if PRO_AVAILABLE:
        click.echo("\n" + "=" * 60)
        click.echo("  pyobfus Professional Edition - ACTIVE")
        click.echo("=" * 60)
        click.echo("\nYour Pro license is active. You have access to all features:")
        click.echo("  - AES-256 string encryption (--string-encryption)")
        click.echo("  - Anti-debugging protection (--anti-debug)")
        click.echo("  - Unlimited files and lines of code")
        click.echo("  - Priority email support")
        click.echo("\nRun 'pyobfus-license status' to view license details.")
        return

    if trial_active:
        click.echo("\n" + "=" * 60)
        click.echo("  pyobfus Professional Edition - TRIAL ACTIVE")
        click.echo("=" * 60)
        click.echo(f"\n  {trial_msg}")
        click.echo("\n  You have access to all Pro features:")
        click.echo("  - AES-256 string encryption (--level pro)")
        click.echo("  - Anti-debugging protection (--level pro)")
        click.echo("  - Unlimited files and lines of code")
        click.echo("")
        click.echo("  To keep using Pro after trial:")
        click.echo(f"  ${PRO_PRICE_USD}.00 USD (one-time payment)")
        click.echo(f"  {STRIPE_PAYMENT_LINK}")
        click.echo("")
        click.echo("  Check trial status: pyobfus-trial status")
        click.echo("=" * 60)
        return

    # Show Pro edition information for Community users
    click.echo("\n" + "=" * 60)
    click.echo("  pyobfus Professional Edition")
    click.echo("=" * 60)
    click.echo("")
    click.echo("  TRY FREE FOR 5 DAYS")
    click.echo("  --------------------")
    click.echo("  No registration or credit card required!")
    click.echo("  Start now: pyobfus-trial start")
    click.echo("")
    click.echo("  FEATURES")
    click.echo("  ---------")
    click.echo("  [x] AES-256 string encryption")
    click.echo("      Encrypt all strings with military-grade encryption")
    click.echo("")
    click.echo("  [x] Anti-debugging protection")
    click.echo("      Detect and prevent debugger attachment")
    click.echo("")
    click.echo("  [x] Unlimited files & lines of code")
    click.echo("      No restrictions on project size")
    click.echo("")
    click.echo("  [x] Priority email support")
    click.echo("      Get help within 24 hours")
    click.echo("")
    click.echo("  PRICING")
    click.echo("  --------")
    click.echo("  $45.00 USD (one-time payment)")
    click.echo("  - 50% cheaper than PyArmor Pro ($89)")
    click.echo("  - Lifetime license, no subscription")
    click.echo("  - 30-day money-back guarantee")
    click.echo("")
    click.echo("  PURCHASE")
    click.echo("  ---------")
    click.echo(f"  {STRIPE_PAYMENT_LINK}")
    click.echo("")
    click.echo("  After purchase, activate with:")
    click.echo("    pip install --upgrade pyobfus")
    click.echo("    pyobfus-license register YOUR-LICENSE-KEY")
    click.echo("")
    click.echo("=" * 60)


def _handle_list_presets() -> None:
    """
    Display all available presets with descriptions.
    """
    click.echo("\n" + "=" * 60)
    click.echo("  pyobfus Configuration Presets")
    click.echo("=" * 60)

    click.echo("\n  COMMUNITY PRESETS (Free)")
    click.echo("  " + "-" * 30)

    click.echo("\n  safe")
    click.echo("    Preserves docstrings and public APIs")
    click.echo("    Ideal for libraries and production code")
    click.echo("    Usage: pyobfus src/ -o dist/ --preset safe")

    click.echo("\n  balanced (default)")
    click.echo("    Removes docstrings, obfuscates private names")
    click.echo("    Good balance between security and compatibility")
    click.echo("    Usage: pyobfus src/ -o dist/ --preset balanced")

    click.echo("\n  aggressive")
    click.echo("    Obfuscates everything possible")
    click.echo("    Use with caution - may break code")
    click.echo("    Usage: pyobfus src/ -o dist/ --preset aggressive")

    click.echo("\n  PRO PRESETS (Requires Pro license or trial)")
    click.echo("  " + "-" * 30)

    click.echo("\n  trial")
    click.echo("    30-day time-limited version")
    click.echo("    All Pro features + expiration date")
    click.echo("    Usage: pyobfus src/ -o dist/ --preset trial")

    click.echo("\n  commercial")
    click.echo("    Maximum protection for paid software")
    click.echo("    CFF + DCI + AES + Anti-debug + Machine binding")
    click.echo("    Usage: pyobfus src/ -o dist/ --preset commercial")

    click.echo("\n  library")
    click.echo("    For distributing Python libraries")
    click.echo("    Preserves APIs, encrypts internal code")
    click.echo("    Usage: pyobfus src/ -o dist/ --preset library")

    click.echo("\n  maximum")
    click.echo("    Highest security for sensitive code")
    click.echo("    All features + machine binding + run limits")
    click.echo("    Usage: pyobfus src/ -o dist/ --preset maximum")

    click.echo("\n" + "=" * 60)
    click.echo("\n  Start a free 5-day trial: pyobfus-trial start")
    click.echo("")


def _handle_init_config(template_name: str) -> None:
    """
    Generate configuration template file.

    Args:
        template_name: Template type (django, flask, library, general)
    """
    output_file = Path("pyobfus.yaml")

    # Check if file already exists
    if output_file.exists():
        if not click.confirm(f"'{output_file}' already exists. Overwrite?"):
            click.echo("Aborted.")
            return

    try:
        template_content = get_template(template_name)
        output_file.write_text(template_content, encoding="utf-8")
        click.echo(f"Generated '{output_file}' with {template_name} template")
        click.echo("\nNext steps:")
        click.echo("  1. Review and customize the configuration")
        click.echo(f"  2. Run: pyobfus src/ -o dist/ -c {output_file}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(f"\nAvailable templates: {', '.join(list_templates())}", err=True)
        sys.exit(1)


def _handle_validate_config(config_path: str) -> None:
    """
    Validate a configuration file and report errors/warnings.

    Args:
        config_path: Path to configuration file
    """
    click.echo(f"Validating: {config_path}\n")

    result = validate_config_file(Path(config_path))

    # Print errors
    for error in result.errors:
        click.echo(error, err=True)

    # Print warnings
    for warning in result.warnings:
        click.echo(warning)

    # Print suggestions
    for suggestion in result.suggestions:
        click.echo(suggestion)

    # Print summary
    click.echo(f"\n{result.get_summary()}")

    if not result.is_valid:
        sys.exit(1)


def _try_auto_discover_config(verbose: bool) -> Optional[Path]:
    """
    Try to auto-discover configuration file.

    Args:
        verbose: Whether to print discovery messages

    Returns:
        Path to config file if found, None otherwise
    """
    config_path, _ = find_config_file()

    if config_path:
        if verbose:
            click.echo(f"Auto-discovered config: {config_path}")
        return config_path

    return None


def _display_stats(stats: dict, config: ObfuscationConfig) -> None:
    """
    Display obfuscation statistics summary.

    Args:
        stats: Dictionary with obfuscation statistics
        config: Obfuscation configuration
    """
    click.echo("\n" + "=" * 50)
    click.echo("  Obfuscation Statistics")
    click.echo("=" * 50)

    click.echo(f"\n  Files processed:      {stats.get('files_processed', 0)}")
    click.echo(f"  Names obfuscated:     {stats.get('total_names_obfuscated', 0)}")

    if stats.get("strings_encoded", 0) > 0:
        click.echo(f"  Strings encoded:      {stats['strings_encoded']}")

    if config.level == "pro":
        if stats.get("strings_encrypted", 0) > 0:
            click.echo(f"  Strings encrypted:    {stats['strings_encrypted']}")
        if stats.get("control_flow_applied", 0) > 0:
            click.echo(f"  Control flow files:   {stats['control_flow_applied']}")
        if stats.get("dead_code_injected", 0) > 0:
            click.echo(f"  Dead code statements: {stats['dead_code_injected']}")
        if stats.get("anti_debug_checks", 0) > 0:
            click.echo(f"  Anti-debug checks:    {stats['anti_debug_checks']}")

    click.echo("\n" + "=" * 50)


if __name__ == "__main__":
    main()
