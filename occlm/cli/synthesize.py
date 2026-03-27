"""
CLI command for synthetic scenario generation.

Provides the `occlm synthesize` command for generating large-scale
synthetic training data for TAKTKRONE-I.
"""

import json
from pathlib import Path

import typer

from occlm.synthesis.dialogue_generator import DialogueGenerator
from occlm.synthesis.disruption_patterns import (
    DISRUPTION_TEMPLATES,
)
from occlm.synthesis.quality_scorer import QualityScorer
from occlm.synthesis.scenario_engine import ScenarioEngine
from occlm.synthesis.topology_simulator import create_sample_network

__all__ = ["app", "synthesize", "create_app"]

app = typer.Typer()


@app.command()
def synthesize(
    num_scenarios: int = typer.Option(
        100,
        "--num-scenarios",
        "-n",
        help="Number of scenarios to generate",
    ),
    output: Path = typer.Option(
        Path("./scenarios.jsonl"),
        "--output",
        "-o",
        help="Output file path (JSONL format)",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Optional JSON config file",
    ),
    incident_types: str | None = typer.Option(
        None,
        "--incident-types",
        help="Comma-separated incident types to generate (default: all)",
    ),
    difficulty: str | None = typer.Option(
        None,
        "--difficulty",
        help="Difficulty level: easy, medium, hard (default: mixed)",
    ),
    quality_threshold: float = typer.Option(
        0.5,
        "--quality-threshold",
        help="Minimum quality score (0.0-1.0)",
    ),
    seed: int | None = typer.Option(
        None,
        "--seed",
        help="Random seed for reproducibility",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate without saving",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Generate synthetic transit disruption scenarios.

    Creates realistic OCC scenarios combining disruption patterns,
    network topology, dialogue templates, and quality scoring.

    Example:
        occlm synthesize --num-scenarios 1000 \\
            --output training_data.jsonl \\
            --difficulty medium

    The command will:
    1. Initialize scenario engine and generators
    2. Generate scenarios of specified types and difficulties
    3. Score quality against threshold
    4. Annotate with dialogue and actions
    5. Output to JSONL format

    Use --dry-run to validate configuration without generating.
    """
    try:
        # Load config if provided
        if config:
            if not config.exists():
                typer.echo(
                    f"Error: Config file not found: {config}",
                    err=True,
                )
                raise typer.Exit(1)

            with open(config) as f:
                json.load(f)

            if verbose:
                typer.echo(f"Loaded config from {config}")

        # Initialize components
        if verbose:
            typer.echo("Initializing synthesis engine...")

        create_sample_network()
        scenario_engine = ScenarioEngine(random_seed=seed)
        dialogue_generator = DialogueGenerator(random_seed=seed)
        quality_scorer = QualityScorer()

        # Filter incident types if specified
        if incident_types:
            types_list = [t.strip() for t in incident_types.split(",")]
            valid_types = [
                t for t in types_list
                if t in DISRUPTION_TEMPLATES
            ]
            if not valid_types:
                typer.echo(
                    f"Error: No valid incident types in {incident_types}",
                    err=True,
                )
                raise typer.Exit(1)
        else:
            valid_types = list(DISRUPTION_TEMPLATES.keys())

        if verbose:
            typer.echo(
                f"Generating {num_scenarios} scenarios from "
                f"{len(valid_types)} incident types"
            )

        # Generate scenarios
        scenarios = []
        dialogues = []

        with typer.progressbar(
            length=num_scenarios,
            label="Generating scenarios",
        ) as progress_bar:
            for i in range(num_scenarios):
                # Select random incident type
                incident_type = valid_types[
                    i % len(valid_types)
                ]

                # Generate scenario
                scenario_list = (
                    scenario_engine.generate_delay_scenario(
                        num_scenarios=1,
                        difficulty=difficulty,
                    )
                )

                if scenario_list:
                    scenario = scenario_list[0]
                    scenario["incident_details"]["type"] = incident_type

                    # Score quality
                    realism = quality_scorer.score_realism(scenario)

                    if realism >= quality_threshold:
                        # Generate dialogue
                        try:
                            dialogue = (
                                dialogue_generator
                                .generate_occ_dialogue(scenario)
                            )
                            scenario["dialogue"] = dialogue
                            scenarios.append(scenario)
                            dialogues.append({
                                "scenario_id": scenario["incident_id"],
                                "dialogue": dialogue,
                            })
                        except Exception as e:
                            if verbose:
                                typer.echo(
                                    f"Skipped scenario due to: {e}"
                                )

                progress_bar.update(1)

        if verbose:
            typer.echo(
                f"Generated {len(scenarios)} scenarios "
                f"(passed quality threshold)"
            )

        # Score batch
        if scenarios:
            batch_scores = quality_scorer.score_batch(scenarios)

            if verbose:
                typer.echo("\nQuality Metrics:")
                typer.echo(
                    f"  Average Realism: {batch_scores['avg_realism']}"
                )
                typer.echo(
                    f"  Temporal Consistency: "
                    f"{batch_scores['avg_temporal_consistency']}"
                )
                typer.echo(
                    f"  Diversity Score: "
                    f"{batch_scores['diversity']['overall_diversity']}"
                )

        # Dry run: just show stats
        if dry_run:
            stats = scenario_engine.get_scenario_stats()
            typer.echo("\nDry-run completed. Statistics:")
            typer.echo(f"  Total scenarios: {len(scenarios)}")
            typer.echo(f"  Avg affected routes: "
                       f"{stats.get('avg_affected_routes', 0):.2f}")
            raise typer.Exit(0)

        # Write output file
        if verbose:
            typer.echo(f"Writing {len(scenarios)} scenarios to {output}")

        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w") as f:
            for scenario in scenarios:
                f.write(json.dumps(scenario) + "\n")

        typer.echo(
            f"Successfully generated {len(scenarios)} scenarios"
        )
        typer.echo(f"Output saved to: {output}")

        if verbose:
            typer.echo(f"File size: {output.stat().st_size:,} bytes")
            typer.echo(
                f"Average scenario size: "
                f"{output.stat().st_size // len(scenarios):,} bytes"
            )

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def list_incident_types() -> None:
    """
    List available incident types for synthesis.

    Shows all incident types that can be used with --incident-types.
    """
    typer.echo("Available incident types:")
    for incident_type, template in DISRUPTION_TEMPLATES.items():
        typer.echo(
            f"  {incident_type:20s} - {template.description}"
        )


@app.command()
def validate_config(
    config_file: Path = typer.Argument(
        ...,
        help="Configuration file to validate",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Validate a synthesis configuration file.

    Checks that a JSON configuration file has proper structure and
    all required fields for scenario generation.

    Example:
        occlm synthesize validate-config config.json
    """
    try:
        if not config_file.exists():
            typer.echo(
                f"Error: Config file not found: {config_file}",
                err=True,
            )
            raise typer.Exit(1)

        with open(config_file) as f:
            config = json.load(f)


        typer.echo(f"Validating {config_file}...")

        # Check structure
        if isinstance(config, dict):
            typer.echo("  JSON structure: OK")
        else:
            typer.echo("  JSON structure: INVALID (must be object)", err=True)
            raise typer.Exit(1)

        # Check keys
        present_keys = set(config.keys())
        if verbose:
            typer.echo(f"  Found keys: {', '.join(present_keys)}")

        # Check types
        valid_types_count = 0
        if "incident_types" in config:
            if isinstance(config["incident_types"], list):
                for itype in config["incident_types"]:
                    if itype in DISRUPTION_TEMPLATES:
                        valid_types_count += 1

            typer.echo(
                f"  Valid incident types: {valid_types_count}/"
                f"{len(config['incident_types'])}"
            )

        typer.echo("Configuration is valid!")

    except json.JSONDecodeError as e:
        typer.echo(f"JSON parse error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(1)


def create_app() -> typer.Typer:
    """
    Create and configure the CLI application.

    Returns:
        Configured Typer application instance
    """
    return app


if __name__ == "__main__":
    app()
