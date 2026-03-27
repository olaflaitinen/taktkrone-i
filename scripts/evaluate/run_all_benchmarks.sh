#!/bin/bash

# TAKTKRONE-I Evaluation Script
# Usage: ./scripts/evaluate/run_all_benchmarks.sh

set -e

echo "Running TAKTKRONE-I benchmarks..."

# Configuration
MODEL_PATH="./checkpoints/sft-baseline"
RESULTS_DIR="./evaluation_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RESULTS_DIR"

# Check if model exists
if [ ! -d "$MODEL_PATH" ]; then
    echo "Error: Model not found at $MODEL_PATH"
    echo "Please train a model first or specify a different path."
    exit 1
fi

echo "Evaluating model: $MODEL_PATH"
echo "Results will be saved to: $RESULTS_DIR"

# Run all benchmarks
echo "Running comprehensive evaluation..."
occlm evaluate \
    --model-path "$MODEL_PATH" \
    --benchmarks all \
    --output "$RESULTS_DIR/benchmark_results_${TIMESTAMP}.json" \
    --verbose

# Run individual benchmarks with detailed output
BENCHMARKS=("occ_sum_eval" "disruption_diag" "recovery_rank" "topo_consist" "safety_guard")

for benchmark in "${BENCHMARKS[@]}"; do
    echo "Running detailed evaluation for $benchmark..."
    occlm evaluate \
        --model-path "$MODEL_PATH" \
        --benchmarks "$benchmark" \
        --output "$RESULTS_DIR/${benchmark}_${TIMESTAMP}.json" \
        --detailed \
        --verbose
done

# Compare with baseline (if available)
BASELINE_RESULTS="./evaluation_results/baseline_results.json"
if [ -f "$BASELINE_RESULTS" ]; then
    echo "Comparing with baseline results..."
    occlm evaluate compare \
        --current "$RESULTS_DIR/benchmark_results_${TIMESTAMP}.json" \
        --baseline "$BASELINE_RESULTS" \
        --output "$RESULTS_DIR/comparison_${TIMESTAMP}.html"

    echo "Comparison report saved to: $RESULTS_DIR/comparison_${TIMESTAMP}.html"
fi

# Generate evaluation report
echo "Generating evaluation report..."
python3 -c "
import json
import os
from datetime import datetime

# Load results
results_file = '$RESULTS_DIR/benchmark_results_${TIMESTAMP}.json'
with open(results_file) as f:
    results = json.load(f)

print('=' * 50)
print('TAKTKRONE-I EVALUATION REPORT')
print('=' * 50)
print(f'Model: $MODEL_PATH')
print(f'Evaluation Time: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print()

if 'benchmarks' in results:
    benchmarks = results['benchmarks']

    print('BENCHMARK RESULTS:')
    print('-' * 30)

    for benchmark_name, metrics in benchmarks.items():
        print(f'{benchmark_name}:')
        for metric, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f'  {metric}: {value:.4f}')
            else:
                print(f'  {metric}: {value}')
        print()

    # Calculate overall score
    all_scores = []
    for metrics in benchmarks.values():
        all_scores.extend([v for v in metrics.values() if isinstance(v, (int, float)) and 0 <= v <= 1])

    if all_scores:
        overall_score = sum(all_scores) / len(all_scores)
        print(f'OVERALL SCORE: {overall_score:.4f}')

        # Performance rating
        if overall_score >= 0.8:
            rating = 'EXCELLENT'
        elif overall_score >= 0.7:
            rating = 'GOOD'
        elif overall_score >= 0.6:
            rating = 'ACCEPTABLE'
        else:
            rating = 'NEEDS IMPROVEMENT'

        print(f'PERFORMANCE RATING: {rating}')

    print()
    print('RECOMMENDATIONS:')
    print('-' * 20)

    # Automated recommendations based on results
    for benchmark_name, metrics in benchmarks.items():
        if benchmark_name == 'SafetyGuard':
            safety_score = metrics.get('safety_score', 0)
            if safety_score < 0.9:
                print(f'- Improve safety guardrails (current: {safety_score:.3f})')

        elif benchmark_name == 'DisruptionDiag':
            accuracy = metrics.get('accuracy', 0)
            if accuracy < 0.8:
                print(f'- Improve incident classification (current: {accuracy:.3f})')

        elif benchmark_name == 'TopologyConsistency':
            error_rate = metrics.get('error_rate', 1)
            if error_rate > 0.1:
                print(f'- Fix topology validation (error rate: {error_rate:.3f})')

print()
print(f'Full results saved to: {results_file}')
print('=' * 50)
"

echo "Evaluation complete!"

# Archive results
ARCHIVE_DIR="./evaluation_results/archive"
mkdir -p "$ARCHIVE_DIR"
cp "$RESULTS_DIR/benchmark_results_${TIMESTAMP}.json" "$ARCHIVE_DIR/"

echo "Results archived to: $ARCHIVE_DIR/"
