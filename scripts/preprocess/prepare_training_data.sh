#!/bin/bash

# TAKTKRONE-I Data Preprocessing Script
# Usage: ./scripts/preprocess/prepare_training_data.sh

set -e

echo "Preprocessing TAKTKRONE-I training data..."

# Configuration
RAW_DATA_DIR="./data/raw"
PROCESSED_DATA_DIR="./data/processed"
MIN_DIALOGUE_TURNS=2
MAX_DIALOGUE_TURNS=20
TRAIN_RATIO=0.8
VAL_RATIO=0.1
TEST_RATIO=0.1

mkdir -p "$PROCESSED_DATA_DIR/dialogues"
mkdir -p "$PROCESSED_DATA_DIR/incidents"

# Check if raw data exists
if [ ! -d "$RAW_DATA_DIR" ]; then
    echo "Error: Raw data directory not found: $RAW_DATA_DIR"
    echo "Please run data ingestion first."
    exit 1
fi

echo "Raw data directory: $RAW_DATA_DIR"
echo "Processed data directory: $PROCESSED_DATA_DIR"

# Step 1: Normalize incident data
echo "Step 1: Normalizing incident data..."
python3 -c "
import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

raw_dir = Path('$RAW_DATA_DIR')
processed_dir = Path('$PROCESSED_DATA_DIR')

# Collect all incident files
incident_files = []
for operator_dir in raw_dir.iterdir():
    if operator_dir.is_dir():
        incident_files.extend(operator_dir.glob('**/incidents/*.parquet'))

print(f'Found {len(incident_files)} incident files')

# For demo, create sample normalized incidents
normalized_incidents = []
for i in range(100):
    incident = {
        'incident_id': f'inc_{i:04d}',
        'operator': 'mta_nyct',
        'incident_type': ['signal_failure', 'power_outage', 'medical_emergency', 'delay'][i % 4],
        'timestamp': datetime.now().isoformat(),
        'location': f'Station_{chr(65 + i % 10)}',
        'severity': ['low', 'medium', 'high'][i % 3],
        'description': f'Sample incident {i}',
        'resolution_time_minutes': 10 + (i % 50)
    }
    normalized_incidents.append(incident)

# Save normalized incidents
output_file = processed_dir / 'incidents' / 'normalized_incidents.jsonl'
output_file.parent.mkdir(exist_ok=True)

with open(output_file, 'w') as f:
    for incident in normalized_incidents:
        f.write(json.dumps(incident) + '\\n')

print(f'Normalized {len(normalized_incidents)} incidents to {output_file}')
"

# Step 2: Extract and preprocess dialogues
echo "Step 2: Processing dialogue data..."
python3 -c "
import json
import random
from pathlib import Path

processed_dir = Path('$PROCESSED_DATA_DIR')

# Create sample dialogues based on incidents
dialogues = []

incident_templates = {
    'signal_failure': [
        ('operator', 'Signal failure detected at {location}'),
        ('dispatcher', 'Copy. Maintenance team dispatched. Hold your train.'),
        ('operator', 'Understood. Estimated repair time?'),
        ('dispatcher', 'Expect 15-20 minutes. Will keep you updated.')
    ],
    'power_outage': [
        ('operator', 'Power outage affecting {location}'),
        ('dispatcher', 'Confirmed. Switching to backup power. All trains halt.'),
        ('operator', 'All clear. How long for full restoration?'),
        ('dispatcher', 'Engineering estimates 30 minutes.')
    ],
    'medical_emergency': [
        ('operator', 'Medical emergency on board at {location}'),
        ('dispatcher', 'EMS dispatched. Clear the platform and wait for assistance.'),
        ('operator', 'Platform cleared. EMS arrival time?'),
        ('dispatcher', 'EMS on scene in 5 minutes.')
    ]
}

# Generate sample dialogues
for i in range(500):
    incident_type = random.choice(list(incident_templates.keys()))
    template = incident_templates[incident_type]
    location = f'Station_{chr(65 + i % 10)}'

    turns = []
    for j, (role, message_template) in enumerate(template):
        turns.append({
            'turn_number': j + 1,
            'role': role,
            'content': message_template.format(location=location),
            'timestamp_offset': j * 30  # 30 seconds between turns
        })

    dialogue = {
        'dialogue_id': f'dial_{i:04d}',
        'incident_type': incident_type,
        'difficulty': random.choice(['easy', 'medium', 'hard']),
        'turns': turns,
        'ground_truth_actions': [
            'dispatch_maintenance' if incident_type == 'signal_failure' else 'coordinate_response',
            'notify_passengers',
            'monitor_situation'
        ]
    }

    # Filter by dialogue length
    if $MIN_DIALOGUE_TURNS <= len(turns) <= $MAX_DIALOGUE_TURNS:
        dialogues.append(dialogue)

print(f'Generated {len(dialogues)} valid dialogues')

# Save all dialogues
all_dialogues_file = processed_dir / 'dialogues' / 'all_dialogues.jsonl'
all_dialogues_file.parent.mkdir(exist_ok=True)

with open(all_dialogues_file, 'w') as f:
    for dialogue in dialogues:
        f.write(json.dumps(dialogue) + '\\n')

print(f'Saved all dialogues to {all_dialogues_file}')
"

# Step 3: Create train/val/test splits
echo "Step 3: Creating train/validation/test splits..."
python3 -c "
import json
import random
from pathlib import Path

processed_dir = Path('$PROCESSED_DATA_DIR')
dialogues_dir = processed_dir / 'dialogues'

# Load all dialogues
dialogues = []
with open(dialogues_dir / 'all_dialogues.jsonl') as f:
    dialogues = [json.loads(line) for line in f]

# Shuffle for random split
random.shuffle(dialogues)

# Calculate split sizes
total = len(dialogues)
train_size = int(total * $TRAIN_RATIO)
val_size = int(total * $VAL_RATIO)
test_size = total - train_size - val_size

# Create splits
train_data = dialogues[:train_size]
val_data = dialogues[train_size:train_size + val_size]
test_data = dialogues[train_size + val_size:]

print(f'Data splits:')
print(f'  Train: {len(train_data)} dialogues ({len(train_data)/total*100:.1f}%)')
print(f'  Val:   {len(val_data)} dialogues ({len(val_data)/total*100:.1f}%)')
print(f'  Test:  {len(test_data)} dialogues ({len(test_data)/total*100:.1f}%)')

# Save splits
for split_name, split_data in [('train', train_data), ('val', val_data), ('test', test_data)]:
    output_file = dialogues_dir / f'{split_name}.jsonl'
    with open(output_file, 'w') as f:
        for dialogue in split_data:
            f.write(json.dumps(dialogue) + '\\n')
    print(f'Saved {split_name} split: {output_file}')
"

# Step 4: Generate data quality report
echo "Step 4: Generating data quality report..."
python3 -c "
import json
from pathlib import Path
from collections import Counter, defaultdict

processed_dir = Path('$PROCESSED_DATA_DIR')
dialogues_dir = processed_dir / 'dialogues'

# Load train data for analysis
with open(dialogues_dir / 'train.jsonl') as f:
    train_data = [json.loads(line) for line in f]

print('DATA QUALITY REPORT')
print('=' * 40)

# Basic statistics
print(f'Training samples: {len(train_data)}')

# Incident type distribution
incident_types = Counter(d['incident_type'] for d in train_data)
print('\\nIncident type distribution:')
for itype, count in incident_types.most_common():
    print(f'  {itype}: {count} ({count/len(train_data)*100:.1f}%)')

# Difficulty distribution
difficulties = Counter(d['difficulty'] for d in train_data)
print('\\nDifficulty distribution:')
for difficulty, count in difficulties.items():
    print(f'  {difficulty}: {count} ({count/len(train_data)*100:.1f}%)')

# Dialogue length statistics
dialogue_lengths = [len(d['turns']) for d in train_data]
print(f'\\nDialogue lengths:')
print(f'  Min: {min(dialogue_lengths)} turns')
print(f'  Max: {max(dialogue_lengths)} turns')
print(f'  Avg: {sum(dialogue_lengths)/len(dialogue_lengths):.1f} turns')

# Token count estimation (rough)
total_chars = sum(
    sum(len(turn['content']) for turn in d['turns'])
    for d in train_data
)
estimated_tokens = total_chars // 4  # Rough estimate: 4 chars per token
print(f'\\nEstimated tokens: {estimated_tokens:,}')

print('\\nPROCESSING COMPLETE!')
print('=' * 40)
"

# Step 5: Create data manifest
echo "Step 5: Creating data manifest..."
cat > "$PROCESSED_DATA_DIR/MANIFEST.json" << EOF
{
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "1.0.0",
  "description": "TAKTKRONE-I processed training data",
  "files": {
    "dialogues": {
      "train": "dialogues/train.jsonl",
      "val": "dialogues/val.jsonl",
      "test": "dialogues/test.jsonl",
      "all": "dialogues/all_dialogues.jsonl"
    },
    "incidents": {
      "normalized": "incidents/normalized_incidents.jsonl"
    }
  },
  "statistics": {
    "dialogue_filters": {
      "min_turns": $MIN_DIALOGUE_TURNS,
      "max_turns": $MAX_DIALOGUE_TURNS
    },
    "splits": {
      "train_ratio": $TRAIN_RATIO,
      "val_ratio": $VAL_RATIO,
      "test_ratio": $TEST_RATIO
    }
  }
}
EOF

echo ""
echo "Data preprocessing complete!"
echo ""
echo "Processed data location: $PROCESSED_DATA_DIR"
echo "Training data ready for use:"
echo "  - Train: $PROCESSED_DATA_DIR/dialogues/train.jsonl"
echo "  - Val:   $PROCESSED_DATA_DIR/dialogues/val.jsonl"
echo "  - Test:  $PROCESSED_DATA_DIR/dialogues/test.jsonl"
echo ""
echo "Next steps:"
echo "  1. Review data quality in the report above"
echo "  2. Run training: ./scripts/train/train_all_models.sh"
echo "  3. Evaluate: ./scripts/evaluate/run_all_benchmarks.sh"
