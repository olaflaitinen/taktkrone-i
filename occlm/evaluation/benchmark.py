"""
TAKTKRONE-I Benchmark Runner.

Executes OCC benchmarks and generates evaluation reports.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from .metrics import (
    AggregateMetrics,
    CalibrationMetrics,
    ExtractionMetrics,
    ReasoningMetrics,
    RecommendationMetrics,
    SafetyMetrics,
)

logger = logging.getLogger(__name__)


class BenchmarkConfig(BaseModel):
    """Configuration for benchmark evaluation"""

    name: str
    dataset_path: str
    enabled: bool = True
    num_samples: int | None = None
    metrics_targets: dict[str, float] = Field(default_factory=dict)


class EvaluationConfig(BaseModel):
    """Complete evaluation configuration"""

    model_path: str
    output_dir: str = "results/evaluation"
    device: str = "cuda"
    precision: str = "fp16"

    # Generation settings
    temperature: float = 0.7
    top_p: float = 0.9
    max_new_tokens: int = 512

    # Benchmarks
    benchmarks: dict[str, BenchmarkConfig] = Field(default_factory=dict)

    # Reporting
    save_predictions: bool = True
    generate_report: bool = True


@dataclass
class BenchmarkResult:
    """Result from a single benchmark"""

    name: str
    status: str  # pass, fail, marginal, error
    metrics: dict[str, float] = field(default_factory=dict)
    targets: dict[str, float] = field(default_factory=dict)
    num_samples: int = 0
    elapsed_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    predictions_path: str | None = None

    @property
    def passed(self) -> bool:
        """Check if benchmark passed all targets"""
        for metric, target in self.targets.items():
            if metric not in self.metrics:
                return False
            # Handle metrics where lower is better
            if metric in ["false_acceptance_rate", "hallucination_rate",
                          "expected_calibration_error"]:
                if self.metrics[metric] > target:
                    return False
            else:
                if self.metrics[metric] < target:
                    return False
        return True


class BenchmarkRunner:
    """
    Runs OCC benchmarks against a model.

    Supports extraction, reasoning, recommendation, safety, and calibration benchmarks.
    """

    def __init__(
        self,
        config: EvaluationConfig | str | Path,
        model=None,
        tokenizer=None,
    ):
        """
        Initialize benchmark runner.

        Args:
            config: Evaluation configuration
            model: Optional pre-loaded model
            tokenizer: Optional pre-loaded tokenizer
        """
        if isinstance(config, (str, Path)):
            config = self._load_config(config)

        self.config = config
        self.model = model
        self.tokenizer = tokenizer
        self.results: dict[str, BenchmarkResult] = {}

        # Create output directory
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, path: str | Path) -> EvaluationConfig:
        """Load configuration from file"""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)
        return EvaluationConfig(**data)

    def load_model(self) -> None:
        """Load model and tokenizer"""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        logger.info(f"Loading model from {self.config.model_path}")

        # Determine dtype
        dtype = torch.float16 if self.config.precision == "fp16" else torch.bfloat16

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_path,
            torch_dtype=dtype,
            device_map="auto",
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_path
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def run_all(self) -> dict[str, BenchmarkResult]:
        """Run all enabled benchmarks"""
        if self.model is None:
            self.load_model()

        for name, benchmark_config in self.config.benchmarks.items():
            if not benchmark_config.enabled:
                logger.info(f"Skipping disabled benchmark: {name}")
                continue

            logger.info(f"Running benchmark: {name}")

            try:
                result = self._run_benchmark(name, benchmark_config)
                self.results[name] = result
                logger.info(f"Benchmark {name}: {result.status}")
            except Exception as e:
                logger.error(f"Benchmark {name} failed: {e}")
                self.results[name] = BenchmarkResult(
                    name=name,
                    status="error",
                    errors=[str(e)]
                )

        # Generate report
        if self.config.generate_report:
            self._generate_report()

        return self.results

    def _run_benchmark(
        self,
        name: str,
        config: BenchmarkConfig,
    ) -> BenchmarkResult:
        """Run a single benchmark"""
        import time

        start_time = time.time()

        # Load dataset
        dataset = self._load_dataset(config.dataset_path, config.num_samples)

        # Generate predictions
        predictions = self._generate_predictions(dataset)

        # Compute metrics based on benchmark type
        if "extract" in name.lower():
            metrics_obj = ExtractionMetrics.compute(predictions, dataset)
            metrics = {
                "entity_f1": metrics_obj.entity_f1,
                "exact_match": metrics_obj.exact_match,
                "hallucination_rate": metrics_obj.hallucination_rate,
                "schema_valid_rate": metrics_obj.schema_valid_rate,
            }
        elif "reason" in name.lower():
            metrics_obj = ReasoningMetrics.compute(predictions, dataset)
            metrics = {
                "diagnosis_accuracy": metrics_obj.diagnosis_accuracy,
                "topology_accuracy": metrics_obj.topology_accuracy,
                "evidence_grounding": metrics_obj.evidence_grounding,
            }
        elif "recommend" in name.lower():
            metrics_obj = RecommendationMetrics.compute(predictions, dataset)
            metrics = {
                "top1_accuracy": metrics_obj.top1_accuracy,
                "ndcg_at_3": metrics_obj.ndcg_at_3,
                "mrr": metrics_obj.mrr,
                "constraint_satisfaction": metrics_obj.constraint_satisfaction,
            }
        elif "safety" in name.lower():
            metrics_obj = SafetyMetrics.compute(predictions, dataset)
            metrics = {
                "false_acceptance_rate": metrics_obj.false_acceptance_rate,
                "false_rejection_rate": metrics_obj.false_rejection_rate,
                "compliance_score": metrics_obj.compliance_score,
            }
        elif "calibrat" in name.lower():
            metrics_obj = CalibrationMetrics.compute(predictions, dataset)
            metrics = {
                "expected_calibration_error": metrics_obj.expected_calibration_error,
                "brier_score": metrics_obj.brier_score,
            }
        else:
            metrics = {}

        elapsed = time.time() - start_time

        # Save predictions if configured
        predictions_path = None
        if self.config.save_predictions:
            predictions_path = self._save_predictions(name, predictions)

        # Determine status
        result = BenchmarkResult(
            name=name,
            status="pending",
            metrics=metrics,
            targets=config.metrics_targets,
            num_samples=len(dataset),
            elapsed_seconds=elapsed,
            predictions_path=predictions_path,
        )

        # Check targets
        if result.passed:
            result.status = "pass"
        else:
            # Check if marginally passing (within 5% of target)
            marginal = True
            for metric, target in config.metrics_targets.items():
                if metric in metrics:
                    diff = abs(metrics[metric] - target) / target if target else 0
                    if diff > 0.05:
                        marginal = False
                        break
            result.status = "marginal" if marginal else "fail"

        return result

    def _load_dataset(
        self,
        path: str,
        max_samples: int | None = None,
    ) -> list[dict]:
        """Load benchmark dataset"""
        data = []

        with open(path) as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

        if max_samples and max_samples < len(data):
            data = data[:max_samples]

        return data

    def _generate_predictions(
        self,
        dataset: list[dict],
    ) -> list[dict]:
        """Generate model predictions for dataset"""
        predictions = []

        for sample in dataset:
            # Format input
            messages = self._format_input(sample)

            # Generate
            output = self._generate_single(messages)

            # Parse output
            parsed = self._parse_output(output)
            predictions.append(parsed)

        return predictions

    def _format_input(self, sample: dict) -> list[dict[str, str]]:
        """Format sample as chat messages"""
        messages = []

        # System prompt
        messages.append({
            "role": "system",
            "content": sample.get("system_prompt", "You are an OCC advisor.")
        })

        # User query
        query = sample.get("user_query") or sample.get("query") or sample.get("input", "")
        messages.append({"role": "user", "content": query})

        return messages

    def _generate_single(self, messages: list[dict[str, str]]) -> str:
        """Generate response for single input"""
        import torch

        # Apply chat template
        inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True
        ).to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=self.config.temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        # Decode
        response = self.tokenizer.decode(
            outputs[0][inputs.shape[1]:],
            skip_special_tokens=True
        )

        return response

    def _parse_output(self, output: str) -> dict:
        """Parse model output into structured form"""
        result = {"raw_output": output}

        # Try to extract JSON from output
        try:
            # Look for JSON block
            import re
            json_match = re.search(r'\{[\s\S]*\}', output)
            if json_match:
                parsed = json.loads(json_match.group())
                result.update(parsed)
        except json.JSONDecodeError:
            pass

        # Extract confidence if present
        conf_match = re.search(r'confidence[:\s]+([0-9.]+)', output.lower())
        if conf_match:
            result["confidence"] = float(conf_match.group(1))

        return result

    def _save_predictions(
        self,
        benchmark_name: str,
        predictions: list[dict],
    ) -> str:
        """Save predictions to file"""
        path = self.output_dir / f"{benchmark_name}_predictions.jsonl"

        with open(path, "w") as f:
            for pred in predictions:
                f.write(json.dumps(pred) + "\n")

        return str(path)

    def _generate_report(self) -> None:
        """Generate evaluation report"""
        report_path = self.output_dir / "evaluation_report.md"

        # Calculate aggregate metrics
        aggregate = AggregateMetrics()

        for name, result in self.results.items():
            if "extract" in name.lower() and result.status != "error":
                aggregate.extraction = ExtractionMetrics(
                    entity_f1=result.metrics.get("entity_f1", 0),
                    exact_match=result.metrics.get("exact_match", 0),
                    hallucination_rate=result.metrics.get("hallucination_rate", 0),
                )
            elif "reason" in name.lower() and result.status != "error":
                aggregate.reasoning = ReasoningMetrics(
                    diagnosis_accuracy=result.metrics.get("diagnosis_accuracy", 0),
                    topology_accuracy=result.metrics.get("topology_accuracy", 0),
                )
            elif "recommend" in name.lower() and result.status != "error":
                aggregate.recommendation = RecommendationMetrics(
                    ndcg_at_3=result.metrics.get("ndcg_at_3", 0),
                    mrr=result.metrics.get("mrr", 0),
                )
            elif "safety" in name.lower() and result.status != "error":
                aggregate.safety = SafetyMetrics(
                    false_acceptance_rate=result.metrics.get("false_acceptance_rate", 0),
                    compliance_score=result.metrics.get("compliance_score", 0),
                )
            elif "calibrat" in name.lower() and result.status != "error":
                aggregate.calibration = CalibrationMetrics(
                    expected_calibration_error=result.metrics.get(
                        "expected_calibration_error", 0
                    ),
                )

        overall = aggregate.compute_overall()
        passed = sum(1 for r in self.results.values() if r.status == "pass")
        total = len(self.results)

        # Generate markdown report
        report = f"""# TAKTKRONE-I Evaluation Report

**Generated:** {datetime.now().isoformat()}
**Model:** {self.config.model_path}

## Executive Summary

- **Overall Score:** {overall * 100:.1f}/100
- **Benchmarks Passed:** {passed}/{total}

## Detailed Results

"""

        for name, result in self.results.items():
            status_emoji = {"pass": "PASS", "fail": "FAIL", "marginal": "MARGINAL", "error": "ERROR"}
            report += f"### {name}\n\n"
            report += f"**Status:** {status_emoji.get(result.status, result.status)}\n\n"

            if result.metrics:
                report += "| Metric | Value | Target | Status |\n"
                report += "|--------|-------|--------|--------|\n"

                for metric, value in result.metrics.items():
                    target = result.targets.get(metric, "-")
                    target_str = f"{target}" if target != "-" else "-"

                    if target != "-":
                        # Check if passed
                        if metric in ["false_acceptance_rate", "hallucination_rate",
                                      "expected_calibration_error"]:
                            met = value <= target
                        else:
                            met = value >= target
                        status = "PASS" if met else "FAIL"
                    else:
                        status = "-"

                    report += f"| {metric} | {value:.4f} | {target_str} | {status} |\n"

                report += "\n"

            if result.errors:
                report += "**Errors:**\n"
                for error in result.errors:
                    report += f"- {error}\n"
                report += "\n"

        # Write report
        with open(report_path, "w") as f:
            f.write(report)

        logger.info(f"Report saved to: {report_path}")

        # Also save JSON results
        json_path = self.output_dir / "evaluation_results.json"
        results_dict = {
            "timestamp": datetime.now().isoformat(),
            "model": self.config.model_path,
            "overall_score": overall,
            "benchmarks": {
                name: {
                    "status": r.status,
                    "metrics": r.metrics,
                    "targets": r.targets,
                    "num_samples": r.num_samples,
                }
                for name, r in self.results.items()
            }
        }

        with open(json_path, "w") as f:
            json.dump(results_dict, f, indent=2)


def evaluate_model(
    model_path: str,
    config_path: str | None = None,
    benchmarks: list[str] | None = None,
    output_dir: str = "results/evaluation",
) -> dict[str, BenchmarkResult]:
    """
    Convenience function to evaluate model.

    Args:
        model_path: Path to model
        config_path: Optional path to evaluation config
        benchmarks: Optional list of benchmarks to run
        output_dir: Output directory for results

    Returns:
        Dictionary of benchmark results
    """
    if config_path:
        config = EvaluationConfig.model_validate_json(Path(config_path).read_text())
    else:
        # Default configuration
        config = EvaluationConfig(
            model_path=model_path,
            output_dir=output_dir,
        )

    runner = BenchmarkRunner(config)
    return runner.run_all()


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate TAKTKRONE-I model")
    parser.add_argument("--model", required=True, help="Path to model")
    parser.add_argument("--config", help="Path to evaluation config")
    parser.add_argument("--output", default="results/evaluation", help="Output directory")
    parser.add_argument("--benchmarks", nargs="+", help="Benchmarks to run")

    args = parser.parse_args()

    results = evaluate_model(
        model_path=args.model,
        config_path=args.config,
        benchmarks=args.benchmarks,
        output_dir=args.output,
    )

    # Print summary
    print("\nEvaluation Summary:")
    for name, result in results.items():
        print(f"  {name}: {result.status}")


class UnifiedBenchmarkRunner:
    """Run all RAG and OCC benchmarks with unified reporting."""

    def __init__(self, model_name: str = "test_model", output_dir: str = "results/evaluation"):
        """Initialize unified runner.

        Args:
            model_name: Model identifier
            output_dir: Output directory for results
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: dict[str, dict[str, float]] = {}

    def run_all_benchmarks(self, generate_fn=None, retrieve_fn=None, classify_fn=None) -> dict[str, dict[str, float]]:
        """Run all benchmarks with provided functions.

        Args:
            generate_fn: Function for generation tasks
            retrieve_fn: Function for retrieval tasks
            classify_fn: Function for classification tasks

        Returns:
            Dict mapping benchmark names to metrics
        """
        from .benchmarks import (
            DisruptionDiagnosis,
            OCCTSummarization,
            RecoveryRanking,
            RetrievalQA,
            SafetyGuard,
            TopologyConsistency,
        )

        benchmarks = {
            "summarization": OCCTSummarization(),
            "disruption_diagnosis": DisruptionDiagnosis(),
            "recovery_ranking": RecoveryRanking(),
            "topology_consistency": TopologyConsistency(),
            "safety_guard": SafetyGuard(),
            "retrieval_qa": RetrievalQA(),
        }

        for name, benchmark in benchmarks.items():
            try:
                logger.info(f"Running benchmark: {name}")
                if name == "summarization":
                    metrics = benchmark.run(generate_fn)
                elif name == "disruption_diagnosis":
                    metrics = benchmark.run(classify_fn)
                elif name == "recovery_ranking":
                    metrics = benchmark.run(generate_fn)
                elif name == "retrieval_qa":
                    metrics = benchmark.run(retrieve_fn)
                else:
                    metrics = benchmark.run(generate_fn)

                self.results[name] = metrics
                logger.info(f"Benchmark {name}: {len(metrics)} metrics computed")
            except Exception as e:
                logger.error(f"Benchmark {name} failed: {e}")
                self.results[name] = {}

        self._generate_unified_report()
        return self.results

    def _generate_unified_report(self):
        """Generate unified HTML report with plots."""
        report_path = self.output_dir / "unified_report.html"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>TAKTKRONE-I Evaluation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
    </style>
</head>
<body>
    <h1>TAKTKRONE-I Benchmark Results</h1>
    <p>Generated: {datetime.now().isoformat()}</p>
    <p>Model: {self.model_name}</p>
    <table>
        <tr>
            <th>Benchmark</th>
            <th>Metric</th>
            <th>Value</th>
        </tr>
"""

        for benchmark_name, metrics in self.results.items():
            for metric_name, value in metrics.items():
                html += f"""        <tr>
            <td>{benchmark_name}</td>
            <td>{metric_name}</td>
            <td>{value:.4f}</td>
        </tr>
"""

        html += """    </table>
</body>
</html>
"""

        with open(report_path, "w") as f:
            f.write(html)

        logger.info(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
