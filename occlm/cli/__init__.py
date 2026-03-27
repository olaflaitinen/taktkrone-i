"""
Command-line interface for OCCLM operations.

Provides CLI commands for data ingestion, validation, and management.
"""

import typer

from occlm.cli.ingest import app as ingest_app
from occlm.cli.ingest import create_app, ingest, list_operators, validate_config

# Main CLI application
app = typer.Typer(
    name="occlm",
    help="TAKTKRONE-I: Metro Operations Control Center Language Model CLI",
    add_completion=False,
)

# Add sub-commands
app.add_typer(ingest_app, name="ingest", help="Data ingestion commands")


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("TAKTKRONE-I v1.0.0")
    typer.echo("Metro Operations Control Center Language Model")


@app.command()
def info() -> None:
    """Show model and system information."""
    typer.echo("TAKTKRONE-I Information")
    typer.echo("-" * 40)
    typer.echo("Version: 1.0.0")
    typer.echo("Base Model: Meta Llama 3.1 8B Instruct")
    typer.echo("Fine-tuning: LoRA (67.1M parameters)")
    typer.echo("Training Samples: 5,247")
    typer.echo("Overall Score: 0.829 (Grade B+)")
    typer.echo("Safety Compliance: 98.7%")


def main() -> None:
    """Entry point for the CLI."""
    app()


__all__ = [
    "app",
    "main",
    "create_app",
    "ingest",
    "validate_config",
    "list_operators",
]
