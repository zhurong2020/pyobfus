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
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.parser import ASTParser
from pyobfus.exceptions import LimitExceededError, PyObfusError
from pyobfus.transformers.name_mangler import NameMangler
from pyobfus.utils import filter_python_files

# Check if Pro edition is available
try:
    import pyobfus_pro  # type: ignore[import]

    PRO_AVAILABLE = True
except ImportError:
    pyobfus_pro = None  # type: ignore[assignment]
    PRO_AVAILABLE = False


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(),
    required=True,
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
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
@click.version_option(version=__version__, prog_name="pyobfus")
def main(
    input_path: str,
    output_path: str,
    config_path: Optional[str],
    level: str,
    remove_docstrings: bool,
    remove_comments: bool,
    name_prefix: str,
    verbose: bool,
) -> None:
    """
    Obfuscate Python source code.

    INPUT_PATH: Python file or directory to obfuscate

    \b
    Examples:
      pyobfus script.py -o script_obf.py
      pyobfus src/ -o dist/
      pyobfus src/ -o dist/ --config pyobfus.yaml
    """
    try:
        # Load configuration
        if config_path:
            config = ObfuscationConfig.from_file(Path(config_path))
            if verbose:
                click.echo(f"Loaded configuration from: {config_path}")
        else:
            # Use default based on level
            if level == "pro":
                # Pro edition requires license verification
                if not PRO_AVAILABLE:
                    click.echo(
                        "Error: Pro edition features not installed.",
                        err=True,
                    )
                    click.echo(
                        "Install with: pip install pyobfus-pro",
                        err=True,
                    )
                    sys.exit(1)

                # Verify license (imports are guaranteed to exist when PRO_AVAILABLE is True)
                assert PRO_AVAILABLE, "Pro features should be available"
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
                            "\nPurchase a license at: https://github.com/zhurong2020/pyobfus",
                            err=True,
                        )
                        sys.exit(1)

                    # Verify the cached license (use unmasked key)
                    full_license_key = cached_status["key"]
                    license_result = pyobfus_pro.verify_license(full_license_key)

                    if verbose:
                        click.echo(
                            f"License verified: {license_result['message']}"
                        )

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
                    sys.exit(1)

                config = ObfuscationConfig.pro_edition()
            else:
                config = ObfuscationConfig.community_edition()

        # Override config with CLI options
        config.level = level
        config.remove_docstrings = remove_docstrings
        config.remove_comments = remove_comments
        config.name_prefix = name_prefix

        # Determine if input is file or directory
        input_path_obj = Path(input_path)
        output_path_obj = Path(output_path)

        if input_path_obj.is_file():
            # Single file obfuscation
            _obfuscate_file(input_path_obj, output_path_obj, config, verbose)
        elif input_path_obj.is_dir():
            # Directory obfuscation
            _obfuscate_directory(input_path_obj, output_path_obj, config, verbose)
        else:
            click.echo(f"Error: {input_path} is neither a file nor a directory", err=True)
            sys.exit(1)

        click.echo("\nObfuscation completed successfully!")

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
    input_file: Path, output_file: Path, config: ObfuscationConfig, verbose: bool
) -> None:
    """
    Obfuscate a single Python file.

    Args:
        input_file: Input Python file
        output_file: Output file path
        config: Obfuscation configuration
        verbose: Verbose output
    """
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

    if verbose:
        click.echo(f"  Name transformations: {mangler.get_transformation_count()}")

    # 2. Pro features (if enabled)
    if config.level == "pro":
        try:
            # String encryption (AES-256)
            if config.string_encryption:
                from pyobfus_pro.string_aes import StringAESEncryptor

                string_encryptor = StringAESEncryptor(config, analyzer)
                transformed_tree = string_encryptor.transform(transformed_tree)

                if verbose:
                    stats = string_encryptor.get_statistics()
                    click.echo(f"  Encrypted strings: {stats['encrypted_strings']}")

            # Anti-debugging checks
            if config.anti_debug:
                from pyobfus_pro.anti_debug import AntiDebugInjector

                anti_debug = AntiDebugInjector(config, analyzer)
                transformed_tree = anti_debug.transform(transformed_tree)

                if verbose:
                    stats = anti_debug.get_statistics()
                    click.echo(f"  Anti-debug checks: {stats['injected_functions'] + 1}")

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
    CodeGenerator.generate_to_file(transformed_tree, output_file)

    if verbose:
        click.echo(f"  Output: {output_file}")


def _obfuscate_directory(
    input_dir: Path, output_dir: Path, config: ObfuscationConfig, verbose: bool
) -> None:
    """
    Obfuscate all Python files in a directory.

    Args:
        input_dir: Input directory
        output_dir: Output directory
        config: Obfuscation configuration
        verbose: Verbose output
    """
    # Find all Python files, excluding patterns from config
    python_files = filter_python_files(input_dir, config.exclude_patterns)

    if not python_files:
        click.echo(f"No Python files found in {input_dir}")
        return

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
            _obfuscate_file(python_file, output_file, config, verbose)
        except PyObfusError as e:
            click.echo(f"  Warning: Failed to obfuscate {python_file}: {e}", err=True)
            # Continue with other files


if __name__ == "__main__":
    main()
