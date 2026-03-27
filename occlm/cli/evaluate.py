"""CLI for model evaluation with benchmark suite."""

import json
import logging
from pathlib import Path

import typer

logger = logging.getLogger(__name__)
app = typer.Typer(help="Evaluate TAKTKRONE-I models with benchmark suite")


@app.command()
def evaluate(
    model_path: str = typer.Option(..., help="Path to model checkpoint"),
    benchmarks: str = typer.Option(
        "all",
        help="Comma-separated list of benchmarks or 'all'",
    ),
    output_dir: str = typer.Option("results/evaluation", help="Output directory"),
    subset_size: int | None = typer.Option(None, help="Use subset of test cases"),
    format: str = typer.Option("json", help="Output format: json or html"),
    comparison_model: str | None = typer.Option(None, help="Compare with another model"),
    device: str = typer.Option("cpu", help="Device: cpu or cuda"),
    batch_size: int = typer.Option(32, help="Batch size for evaluation"),
    progress: bool = typer.Option(True, help="Show progress bar"),
):
    """Evaluate model against benchmark suite.

    Example:
        occlm evaluate --model-path model.pth --benchmarks all --output-dir results/
    """
    try:

        from occlm.evaluation.benchmark import UnifiedBenchmarkRunner

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Parse benchmarks to run
        if benchmarks == "all":
            benchmark_list = [
                "summarization",
                "disruption_diagnosis",
                "recovery_ranking",
                "topology_consistency",
                "safety_guard",
                "retrieval_qa",
            ]
        else:
            benchmark_list = [b.strip() for b in benchmarks.split(",")]

        logger.info(f"Evaluating model: {model_path}")
        logger.info(f"Benchmarks: {', '.join(benchmark_list)}")
        logger.info(f"Output: {output_dir}")

        # Initialize runner
        runner = UnifiedBenchmarkRunner(model_name=Path(model_path).name, output_dir=str(output_dir))

        # Dummy generation functions (skeleton)
        def dummy_generate(text: str) -> str:
            """Skeleton generation function."""
            return text[:50]

        def dummy_retrieve(query: str, corpus: dict) -> list[str]:
            """Skeleton retrieval function."""
            return list(corpus.keys())[:5]

        def dummy_classify(text: str) -> str:
            """Skeleton classification function."""
            return "unknown"

        # Run benchmarks with progress tracking
        results = runner.run_all_benchmarks(
            generate_fn=dummy_generate,
            retrieve_fn=dummy_retrieve,
            classify_fn=dummy_classify,
        )

        # Generate output
        if format == "json":
            output_file = output_dir / "benchmark_results.json"
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            typer.echo(f"Results saved to {output_file}")

        elif format == "html":
            output_file = output_dir / "benchmark_results.html"
            _generate_html_report(results, output_file, model_path)
            typer.echo(f"Report saved to {output_file}")

        # Print summary
        typer.echo("\n" + "=" * 60)
        typer.echo("EVALUATION SUMMARY")
        typer.echo("=" * 60)

        total_metrics = 0
        total_value = 0.0

        for benchmark_name, metrics in results.items():
            typer.echo(f"\n{benchmark_name}:")
            for metric_name, value in metrics.items():
                typer.echo(f"  {metric_name}: {value:.4f}")
                total_metrics += 1
                total_value += value

        if total_metrics > 0:
            avg_score = total_value / total_metrics
            typer.echo(f"\nAverage Score: {avg_score:.4f}")

        # Comparison if requested
        if comparison_model:
            typer.echo(f"\nComparison with {comparison_model}:")
            _compare_models(results, comparison_model, output_dir)

        typer.echo("\n" + "=" * 60)

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def run_benchmark(
    benchmark_name: str = typer.Option(..., help="Benchmark name"),
    model_path: str = typer.Option(..., help="Model path"),
    dataset_path: str | None = typer.Option(None, help="Dataset path"),
    output_file: str = typer.Option("result.json", help="Output file"),
):
    """Run single benchmark.

    Example:
        occlm evaluate run-benchmark --benchmark-name summarization --model-path model.pth
    """
    try:
        from occlm.evaluation.benchmarks import (
            DisruptionDiagnosis,
            OCCTSummarization,
            RecoveryRanking,
            RetrievalQA,
            SafetyGuard,
            TopologyConsistency,
        )

        benchmark_map = {
            "summarization": OCCTSummarization,
            "disruption_diagnosis": DisruptionDiagnosis,
            "recovery_ranking": RecoveryRanking,
            "topology_consistency": TopologyConsistency,
            "safety_guard": SafetyGuard,
            "retrieval_qa": RetrievalQA,
        }

        if benchmark_name not in benchmark_map:
            typer.echo(f"Unknown benchmark: {benchmark_name}")
            typer.echo(f"Available: {', '.join(benchmark_map.keys())}")
            raise typer.Exit(1)

        benchmark_class = benchmark_map[benchmark_name]
        benchmark = benchmark_class(
            model_name=model_path,
            dataset_path=dataset_path or f"data/{benchmark_name}.json",
        )

        typer.echo(f"Running {benchmark_name}...")
        metrics = benchmark.run()

        # Save results
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)

        typer.echo(f"Results saved to {output_file}")

        # Print metrics
        typer.echo("\nResults:")
        for name, value in metrics.items():
            typer.echo(f"  {name}: {value:.4f}")

    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def compare(
    model1_results: str = typer.Option(..., help="Path to first model's results"),
    model2_results: str = typer.Option(..., help="Path to second model's results"),
    output_file: str = typer.Option("comparison.json", help="Output file"),
):
    """Compare evaluation results between two models."""
    try:
        with open(model1_results) as f:
            results1 = json.load(f)

        with open(model2_results) as f:
            results2 = json.load(f)

        comparison = {}
        for benchmark_name in results1:
            if benchmark_name in results2:
                comparison[benchmark_name] = {}
                for metric_name in results1[benchmark_name]:
                    if metric_name in results2[benchmark_name]:
                        v1 = results1[benchmark_name][metric_name]
                        v2 = results2[benchmark_name][metric_name]
                        diff = v2 - v1
                        pct_change = (diff / v1 * 100) if v1 != 0 else 0
                        comparison[benchmark_name][metric_name] = {
                            "model1": v1,
                            "model2": v2,
                            "difference": diff,
                            "percent_change": pct_change,
                        }

        with open(output_file, "w") as f:
            json.dump(comparison, f, indent=2)

        typer.echo(f"Comparison saved to {output_file}")

        # Print summary
        for benchmark_name, metrics in comparison.items():
            typer.echo(f"\n{benchmark_name}:")
            for metric_name, values in metrics.items():
                pct = values["percent_change"]
                direction = "↑" if pct > 0 else "↓" if pct < 0 else "="
                typer.echo(
                    f"  {metric_name}: {values['model1']:.4f} → {values['model2']:.4f} "
                    f"({direction} {abs(pct):.1f}%)"
                )

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def _generate_html_report(results: dict, output_file: Path, model_path: str):
    """Generate HTML report from results."""
    from datetime import datetime

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>TAKTKRONE-I Evaluation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .metric-value {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>TAKTKRONE-I Benchmark Evaluation Report</h1>
        <p><strong>Generated:</strong> {datetime.now().isoformat()}</p>
        <p><strong>Model:</strong> {model_path}</p>

        <h2>Benchmark Results</h2>
        <table>
            <tr>
                <th>Benchmark</th>
                <th>Metric</th>
                <th class="metric-value">Value</th>
            </tr>
"""

    for benchmark_name, metrics in results.items():
        first = True
        for metric_name, value in metrics.items():
            html += f"""            <tr>
                <td>{"" if not first else benchmark_name}</td>
                <td>{metric_name}</td>
                <td class="metric-value">{value:.4f}</td>
            </tr>
"""
            first = False

    html += """        </table>
    </div>
</body>
</html>
"""

    with open(output_file, "w") as f:
        f.write(html)


def _compare_models(results: dict, comparison_model: str, output_dir: Path):
    """Stub for model comparison."""
    typer.echo(f"Comparison with {comparison_model} would go here.")


if __name__ == "__main__":
    app()
