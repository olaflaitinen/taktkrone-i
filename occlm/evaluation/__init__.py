"""
TAKTKRONE-I Evaluation Module.

Provides benchmark evaluation infrastructure including:
- OCC benchmark suite (Extract, Reason, Recommend, Safety, Calibrate)
- Metrics computation
- Report generation
"""

from .benchmark import (
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkRunner,
    EvaluationConfig,
    evaluate_model,
)
from .benchmarks import (
    DisruptionDiagnosis,
    OCCTSummarization,
    RecoveryRanking,
    RetrievalQA,
    SafetyGuard,
    TopologyConsistency,
)
from .metrics import (
    AggregateMetrics,
    CalibrationMetrics,
    ExtractionMetrics,
    ReasoningMetrics,
    RecommendationMetrics,
    SafetyMetrics,
    compute_calibration_error,
    compute_mrr,
    compute_ndcg,
)

__all__ = [
    # Config
    "EvaluationConfig",
    "BenchmarkConfig",
    # Runner
    "BenchmarkRunner",
    "BenchmarkResult",
    "evaluate_model",
    # Metrics
    "ExtractionMetrics",
    "ReasoningMetrics",
    "RecommendationMetrics",
    "SafetyMetrics",
    "CalibrationMetrics",
    "AggregateMetrics",
    # Utility functions
    "compute_ndcg",
    "compute_mrr",
    "compute_calibration_error",
    # RAG Benchmarks
    "OCCTSummarization",
    "DisruptionDiagnosis",
    "RecoveryRanking",
    "TopologyConsistency",
    "SafetyGuard",
    "RetrievalQA",
]
