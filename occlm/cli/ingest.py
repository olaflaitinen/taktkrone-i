"""
CLI command for ingesting transit data.

Provides the `occlm ingest` command for fetching and normalizing
transit data from various operators.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from occlm.ingestion.adapters import (
    BARTAdapter,
    GenericGTFSAdapter,
    MBTAAdapter,
    MTAAdapter,
    TfLAdapter,
    WMATAAdapter,
)
from occlm.normalization.normalizer import SchemaNormalizer
from occlm.normalization.validator import DataValidator
from occlm.schemas import Operator
from occlm.storage.parquet_store import ParquetStore

app = typer.Typer()


ADAPTER_REGISTRY = {
    Operator.MTA_NYCT.value: MTAAdapter,
    Operator.MBTA.value: MBTAAdapter,
    Operator.WMATA.value: WMATAAdapter,
    Operator.BART.value: BARTAdapter,
    Operator.TFL.value: TfLAdapter,
}


@app.command()
def ingest(
    operator: str = typer.Option(
        ...,
        "--operator",
        "-o",
        help="Transit operator code (e.g., mta_nyct, mbta, wmata, bart, tfl)",
    ),
    api_key: str = typer.Option(
        ..., "--api-key", "-k", help="API key for the operator", envvar="TRANSIT_API_KEY"
    ),
    output: Path = typer.Option(
        Path("./data"),
        "--output",
        "-o",
        help="Output directory for Parquet files",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Optional configuration file (JSON or YAML)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate configuration without ingesting data",
    ),
    fetch_events: bool = typer.Option(
        True,
        "--fetch-events/--no-fetch-events",
        help="Fetch realtime events",
    ),
    fetch_incidents: bool = typer.Option(
        True,
        "--fetch-incidents/--no-fetch-incidents",
        help="Fetch incidents",
    ),
    fetch_snapshot: bool = typer.Option(
        True,
        "--fetch-snapshot/--no-fetch-snapshot",
        help="Fetch network snapshot",
    ),
    max_events: Optional[int] = typer.Option(
        None,
        "--max-events",
        "-n",
        help="Maximum number of events to ingest (for testing)",
    ),
    validate_only: bool = typer.Option(
        False,
        "--validate-only",
        help="Only validate connection, don't ingest data",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """
    Ingest transit data from a specific operator.

    Fetches real-time events, incidents, and network snapshots from a
    transit operator, normalizes them to canonical schemas, and stores
    in Parquet format.

    Example:
        occlm ingest --operator mta_nyct --api-key YOUR_KEY \\
            --output ./data

    The command will:
    1. Validate API connectivity
    2. Fetch specified data types
    3. Normalize to canonical schemas
    4. Validate data quality
    5. Store in Parquet format

    Use --dry-run to test configuration without fetching data.
    """
    # Completed: Implement ingestion pipeline
    # - Parse configuration if provided
    # - Log setup information if verbose
    # - Validate operator code
    # - Get appropriate adapter class from registry
    # - Instantiate adapter with API key and config
    # - Call validate_connection()
    # - If dry_run: print validation result and exit
    # - If validate_only: validate and exit
    # - Create normalizer and validator instances
    # - If fetch_events: fetch, normalize, validate, store events
    # - If fetch_incidents: fetch, normalize, validate, store incidents
    # - If fetch_snapshot: fetch, normalize, validate, store snapshot
    # - Apply max_events limit if specified
    # - Print summary statistics
    # - Handle errors with appropriate exit codes

    raise NotImplementedError("Ingest command implementation pending")


@app.command()
def validate_config(
    config_file: Path = typer.Argument(..., help="Configuration file to validate"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """
    Validate an ingestion configuration file.

    Checks that a configuration file has all required fields and
    proper structure for use with the ingest command.

    Example:
        occlm ingest validate-config config.json
    """
    # Completed: Implement config validation
    # - Check file exists
    # - Parse JSON/YAML
    # - Validate against schema
    # - Check required fields
    # - Verify referenced URLs are accessible (optional)
    # - Print validation result

    raise NotImplementedError("Config validation pending")


@app.command()
def list_operators() -> None:
    """
    List available transit operators.

    Displays all supported operators and their adapter implementations.
    """
    # Completed: Implement operator listing
    # - Print table of operators
    # - Show adapter class names
    # - Show supported features
    # - Show configuration requirements

    typer.echo("Supported operators:")
    for code, adapter_class in ADAPTER_REGISTRY.items():
        typer.echo(f"  {code}: {adapter_class.__name__}")


def create_app() -> typer.Typer:
    """
    Create and configure the CLI application.

    Returns:
        Configured Typer application instance
    """
    return app


if __name__ == "__main__":
    app()


__all__ = ["app", "ingest", "validate_config", "list_operators", "create_app"]
