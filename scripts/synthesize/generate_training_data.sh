#!/bin/bash

# TAKTKRONE-I Data Synthesis Script
# Usage: ./scripts/synthesize/generate_training_data.sh

set -e

echo "Generating synthetic training data for TAKTKRONE-I..."

OUTPUT_DIR="./data/synthetic"
NUM_SCENARIOS=1000
QUALITY_THRESHOLD=0.7

mkdir -p "$OUTPUT_DIR"

echo "Generating $NUM_SCENARIOS synthetic scenarios..."

# Generate scenarios
occlm synthesize \
    --num-scenarios "$NUM_SCENARIOS" \
    --output "$OUTPUT_DIR/scenarios.jsonl" \
    --quality-threshold "$QUALITY_THRESHOLD" \
    --seed 42 \
    --verbose

echo "Synthetic data generation complete!"

# Generate statistics
echo "Analyzing generated data..."
python3 -c "
import json
from collections import Counter

# Load scenarios
scenarios = []
with open('$OUTPUT_DIR/scenarios.jsonl') as f:
    scenarios = [json.loads(line) for line in f]

print(f'Total scenarios: {len(scenarios)}')

# Analyze incident types
incident_types = Counter(s.get('incident_type', 'unknown') for s in scenarios)
print('\\nIncident type distribution:')
for incident_type, count in incident_types.most_common():
    print(f'  {incident_type}: {count} ({count/len(scenarios)*100:.1f}%)')

# Analyze difficulty levels
difficulties = Counter(s.get('difficulty', 'unknown') for s in scenarios)
print('\\nDifficulty distribution:')
for difficulty, count in difficulties.items():
    print(f'  {difficulty}: {count} ({count/len(scenarios)*100:.1f}%)')

# Quality scores
quality_scores = [s.get('quality_score', 0) for s in scenarios if 'quality_score' in s]
if quality_scores:
    avg_quality = sum(quality_scores) / len(quality_scores)
    print(f'\\nAverage quality score: {avg_quality:.3f}')

print(f'\\nData saved to: $OUTPUT_DIR/scenarios.jsonl')
"

echo "Analysis complete!"
