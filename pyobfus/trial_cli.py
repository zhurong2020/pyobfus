"""
Command-line interface for pyobfus Pro trial management.

Provides commands to start and check the status of the 5-day Pro trial.
"""

import sys

import click

from pyobfus import __version__
from pyobfus.constants import STRIPE_PAYMENT_LINK
from pyobfus.trial import (
    get_trial_status,
    start_trial,
    TRIAL_DURATION,
)


@click.group()
@click.version_option(version=__version__, prog_name="pyobfus-trial")
def cli() -> None:
    """
    Manage pyobfus Professional Edition trial.

    Try Pro features FREE for 5 days - no registration required!
    """
    pass


@cli.command()
def start() -> None:
    """
    Start a 5-day free trial of Pro features.

    No registration or credit card required.

    \b
    Trial includes:
      - AES-256 string encryption
      - Anti-debugging protection
      - Unlimited files and lines of code

    \b
    Example:
      pyobfus-trial start
    """
    click.echo("\n" + "=" * 60)
    click.echo("  pyobfus Professional Edition - Free Trial")
    click.echo("=" * 60)

    result = start_trial()

    if result["success"]:
        click.echo("")
        click.echo("  " + click.style("SUCCESS!", fg="green", bold=True))
        click.echo("")
        click.echo(f"  {result['message']}")
        click.echo("")
        click.echo("  TRIAL DETAILS")
        click.echo("  --------------")
        click.echo(f"  Duration: {TRIAL_DURATION.days} days")
        click.echo(f"  Expires:  {result['expires']}")
        click.echo(f"  Days remaining: {result['days_remaining']}")
        click.echo("")
        click.echo("  HOW TO USE")
        click.echo("  -----------")
        click.echo("  Use Pro features with the --level pro flag:")
        click.echo("")
        click.echo("    # AES-256 string encryption")
        click.echo("    pyobfus input.py -o output.py --level pro")
        click.echo("")
        click.echo("  Check trial status anytime:")
        click.echo("    pyobfus-trial status")
        click.echo("")
        click.echo("=" * 60)
    else:
        click.echo("")
        click.echo("  " + click.style("TRIAL UNAVAILABLE", fg="red", bold=True))
        click.echo("")
        click.echo(f"  {result['message']}")
        click.echo("")
        click.echo("  PURCHASE PRO LICENSE")
        click.echo("  ---------------------")
        click.echo("  $45 USD (one-time payment)")
        click.echo(f"  {STRIPE_PAYMENT_LINK}")
        click.echo("")
        click.echo("=" * 60)
        sys.exit(1)


@cli.command()
def status() -> None:
    """
    Check the status of your Pro trial.

    \b
    Example:
      pyobfus-trial status
    """
    click.echo("\n" + "=" * 60)
    click.echo("  pyobfus Professional Edition - Trial Status")
    click.echo("=" * 60)

    trial_status = get_trial_status()

    if not trial_status:
        click.echo("")
        click.echo("  " + click.style("NO TRIAL FOUND", fg="yellow", bold=True))
        click.echo("")
        click.echo("  You haven't started a trial yet.")
        click.echo("")
        click.echo("  Start your free 5-day trial:")
        click.echo("    pyobfus-trial start")
        click.echo("")
        click.echo("  Or purchase a license:")
        click.echo(f"    {STRIPE_PAYMENT_LINK}")
        click.echo("")
        click.echo("=" * 60)
        return

    click.echo("")
    if trial_status["active"]:
        click.echo("  Status: " + click.style("ACTIVE", fg="green", bold=True))
        click.echo("")
        click.echo("  TRIAL DETAILS")
        click.echo("  --------------")
        click.echo(f"  Started:  {trial_status['started'][:10]}")
        click.echo(f"  Expires:  {trial_status['expires_formatted']}")
        click.echo(f"  Days remaining: {trial_status['days_remaining']}")
        click.echo("")

        if trial_status["days_remaining"] <= 2:
            click.echo("  " + click.style("EXPIRING SOON!", fg="yellow", bold=True))
            click.echo("")
            click.echo("  Don't lose access to Pro features!")
            click.echo("  Purchase a license: $45 USD (one-time)")
            click.echo(f"  {STRIPE_PAYMENT_LINK}")
            click.echo("")
    else:
        click.echo("  Status: " + click.style("EXPIRED", fg="red", bold=True))
        click.echo("")
        click.echo("  Your trial has ended.")
        click.echo("")
        click.echo("  CONTINUE WITH PRO")
        click.echo("  ------------------")
        click.echo("  Purchase a license to keep using Pro features:")
        click.echo("")
        click.echo("  Price: $45 USD (one-time payment)")
        click.echo(f"  URL:   {STRIPE_PAYMENT_LINK}")
        click.echo("")
        click.echo("  50% cheaper than PyArmor Pro ($89)")
        click.echo("  30-day money-back guarantee")
        click.echo("")

    click.echo("=" * 60)


@cli.command()
def features() -> None:
    """
    Show Pro features available during trial.

    \b
    Example:
      pyobfus-trial features
    """
    click.echo("\n" + "=" * 60)
    click.echo("  pyobfus Professional Edition - Features")
    click.echo("=" * 60)
    click.echo("")
    click.echo("  INCLUDED IN PRO (and trial):")
    click.echo("  -----------------------------")
    click.echo("")
    click.echo("  [x] AES-256 String Encryption")
    click.echo("      Encrypt all string literals with military-grade encryption.")
    click.echo("      Much stronger than Base64 encoding in Community Edition.")
    click.echo("")
    click.echo("  [x] Anti-Debugging Protection")
    click.echo("      Detect and prevent debugger attachment.")
    click.echo("      Protects against runtime analysis.")
    click.echo("")
    click.echo("  [x] Unlimited Files & Lines of Code")
    click.echo("      No restrictions on project size.")
    click.echo("      Community Edition: 5 files / 1,000 LOC limit.")
    click.echo("")
    click.echo("  [x] Priority Email Support")
    click.echo("      Get help within 24 hours.")
    click.echo("")
    click.echo("  NEW IN v0.3.0:")
    click.echo("  ----------------------")
    click.echo("  [x] Control Flow Flattening")
    click.echo("  [x] Dead Code Injection")
    click.echo("  [x] License Embedding (expire, bind-machine, max-runs)")
    click.echo("  [x] Configuration Presets (trial, commercial, library, maximum)")
    click.echo("")
    click.echo("=" * 60)


if __name__ == "__main__":
    cli()
