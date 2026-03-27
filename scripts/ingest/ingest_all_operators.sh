#!/bin/bash

# TAKTKRONE-I Data Ingestion Script
# Usage: ./scripts/ingest/ingest_all_operators.sh

set -e

echo "Starting TAKTKRONE-I data ingestion for all operators..."

DATA_DIR="./data/raw"
API_KEYS_FILE=".env"

# Load API keys
if [ -f "$API_KEYS_FILE" ]; then
    source "$API_KEYS_FILE"
fi

# List of operators to ingest
OPERATORS=("mta_nyct" "mbta" "wmata" "bart" "tfl")

mkdir -p "$DATA_DIR"

for operator in "${OPERATORS[@]}"; do
    echo "Ingesting data for $operator..."

    # Skip if no API key
    api_key_var="${operator^^}_API_KEY"
    api_key="${!api_key_var}"

    if [ -z "$api_key" ]; then
        echo "Warning: No API key found for $operator (${api_key_var}). Skipping..."
        continue
    fi

    # Run ingestion
    occlm ingest \
        --operator "$operator" \
        --api-key "$api_key" \
        --output "$DATA_DIR/$operator" \
        --max-events 1000 \
        --verbose

    echo "Completed ingestion for $operator"
    echo "---"
done

echo "All operator ingestion complete!"
echo "Data stored in: $DATA_DIR"

# Generate summary report
echo "Generating ingestion summary..."
python3 -c "
import json
import os
from pathlib import Path

data_dir = Path('$DATA_DIR')
summary = {}

for operator_dir in data_dir.glob('*/'):
    operator = operator_dir.name
    files = list(operator_dir.glob('**/*.parquet'))
    summary[operator] = {
        'files': len(files),
        'size_mb': sum(f.stat().st_size for f in files) / 1024 / 1024
    }

print('Ingestion Summary:')
for op, stats in summary.items():
    print(f'  {op}: {stats[\"files\"]} files, {stats[\"size_mb\"]:.1f} MB')

with open('ingestion_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
"

echo "Summary saved to ingestion_summary.json"
