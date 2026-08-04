"""
Command-line interface for pyobfus Pro license management.

Provides commands to register, check, and manage pyobfus Professional Edition licenses.
"""

import json as json_module
import sys

import click

from pyobfus_pro import __version__
from pyobfus_pro.license import (
    LicenseError,
    cache_license,
    generate_license_key,
    get_license_status,
    remove_cached_license,
    verify_license,
)


@click.group()
@click.version_option(version=__version__, prog_name="pyobfus-license")
def cli() -> None:
    """
    Manage pyobfus Professional Edition licenses.

    Use these commands to register, check, and remove your license key.
    """
    pass


@cli.command()
@click.argument("license_key")
@click.option("--verify/--no-verify", default=True, help="Verify license online (default: yes)")
def register(license_key: str, verify: bool) -> None:
    """
    Register a license key for pyobfus Professional Edition.

    LICENSE_KEY: Your license key in format PYOB-XXXX-XXXX-XXXX-XXXX

    \b
    Example:
      pyobfus-license register PYOB-A1B2-C3D4-E5F6-0123
    """
    try:
        if verify:
            # Verify license online
            click.echo("Verifying license key...")
            result = verify_license(license_key)

            if result["valid"]:
                click.echo("✓ License verified successfully!")
                click.echo(f"  Type: {result['type']}")
                click.echo(f"  Expires: {result['expires']}")
                click.echo("\nYou can now use pyobfus Pro edition with:")
                click.echo("  pyobfus input.py -o output.py --level pro")
            else:
                click.echo(f"✗ License verification failed: {result['message']}", err=True)
                sys.exit(1)
        else:
            # Register without verification (for offline use)
            from datetime import datetime

            cache_license(
                {
                    "key": license_key,
                    "type": "professional",  # Assume professional
                    "expires": "2099-12-31",  # Far future
                    "verified": datetime.now().isoformat(),
                }
            )
            click.echo("✓ License registered locally (not verified online)")
            click.echo(
                "  Note: Run 'pyobfus-license register YOUR-KEY' with internet "
                "connection to verify online"
            )

    except LicenseError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--verify/--no-verify", default=False, help="Re-verify license online")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Emit machine-readable JSON output (for editor/IDE integrations, e.g. the pyobfus "
    "VSCode extension's status bar).",
)
def status(verify: bool, json_output: bool) -> None:
    """
    Check the status of your registered license.

    \b
    Example:
      pyobfus-license status
      pyobfus-license status --verify
      pyobfus-license status --json
    """
    try:
        from pyobfus_pro.fingerprint import get_device_info

        device = get_device_info()
        license_info = get_license_status(masked=True)

        if json_output:
            payload: dict = {"version": 1, "device": device, "license_status": license_info}
            exit_code = 0
            if not license_info:
                exit_code = 1
            elif license_info["expired"]:
                exit_code = 1
            if verify and license_info:
                full_license_info = get_license_status(masked=False)
                if full_license_info:
                    result = verify_license(full_license_info["key"])
                    payload["verify_result"] = result
                    if not result["valid"]:
                        exit_code = 1
            click.echo(json_module.dumps(payload))
            sys.exit(exit_code)

        click.echo("Device Information:")
        click.echo(f"  ID: {device['fingerprint']}")
        click.echo(f"  Name: {device['name']}")
        click.echo(f"  OS: {device['system']} {device['release']}")
        click.echo()

        if not license_info:
            click.echo("No license key registered.")
            click.echo("\nTo register a license key, run:")
            click.echo("  pyobfus-license register YOUR-LICENSE-KEY")
            click.echo("\nPurchase a license at: https://github.com/zhurong2020/pyobfus")
            sys.exit(1)

        # Display license information
        click.echo("License Information:")
        click.echo(f"  Key: {license_info['key']}")
        click.echo(f"  Type: {license_info['type']}")
        click.echo(f"  Expires: {license_info['expires']}")

        if license_info["expired"]:
            click.echo("  Status: ✗ EXPIRED", err=True)
        else:
            click.echo("  Status: ✓ Active")

        click.echo(f"  Last verified: {license_info['verified_ago_days']} days ago")

        # Update cache duration display to 3 days (changed in v0.1.4)
        cache_ttl_days = 3
        if license_info["cache_valid"]:
            click.echo(
                f"  Cache: Valid (expires in {cache_ttl_days - license_info['verified_ago_days']} days)"
            )
        else:
            click.echo(
                "  Cache: Expired (verification required)",
                err=True,
            )

        # Re-verify if requested
        if verify:
            click.echo("\nRe-verifying license online...")
            full_license_info = get_license_status(masked=False)
            if full_license_info:
                result = verify_license(full_license_info["key"])
                if result["valid"]:
                    click.echo("✓ License verified successfully!")
                    click.echo(f"  {result['message']}")
                else:
                    click.echo(f"✗ Verification failed: {result['message']}", err=True)
                    sys.exit(1)

    except LicenseError as e:
        if json_output:
            click.echo(
                json_module.dumps(
                    {
                        "version": 1,
                        "status": "error",
                        "error_type": "LicenseError",
                        "message": str(e),
                    }
                )
            )
        else:
            click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        if json_output:
            click.echo(
                json_module.dumps(
                    {
                        "version": 1,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "message": str(e),
                    }
                )
            )
        else:
            click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to remove your cached license?")
def remove() -> None:
    """
    Remove the cached license key.

    This will require you to register your license again to use Pro features.

    \b
    Example:
      pyobfus-license remove
    """
    try:
        if remove_cached_license():
            click.echo("✓ License cache removed successfully.")
            click.echo("\nTo use Pro features again, re-register your license:")
            click.echo("  pyobfus-license register YOUR-LICENSE-KEY")
        else:
            click.echo("No cached license found.")

    except Exception as e:
        click.echo(f"✗ Error removing license: {e}", err=True)
        sys.exit(1)


@cli.command(hidden=True)
@click.option("--count", default=1, help="Number of keys to generate")
def generate(count: int) -> None:
    """
    Generate license keys (admin only).

    This command is for license administrators to generate new license keys.
    """
    click.echo(f"Generating {count} license key(s):\n")
    for i in range(count):
        key = generate_license_key()
        click.echo(f"{i + 1}. {key}")


if __name__ == "__main__":
    cli()
