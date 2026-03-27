#!/bin/bash

# TAKTKRONE-I Training Script
# Usage: ./scripts/train/train_all_models.sh

set -e

echo "Training TAKTKRONE-I models..."

# Configuration
TRAIN_DATA="./data/processed/dialogues/train.jsonl"
VAL_DATA="./data/processed/dialogues/val.jsonl"
OUTPUT_DIR="./checkpoints"
WANDB_PROJECT="taktkrone-i-training"

mkdir -p "$OUTPUT_DIR"

# Check if training data exists
if [ ! -f "$TRAIN_DATA" ]; then
    echo "Error: Training data not found at $TRAIN_DATA"
    echo "Please run data ingestion and preprocessing first."
    exit 1
fi

echo "Training data found: $TRAIN_DATA"
echo "Validation data: $VAL_DATA"

# Train SFT baseline model
echo "Training SFT baseline model..."
occlm train \
    --config configs/training/sft_baseline.yaml \
    --train-data "$TRAIN_DATA" \
    --val-data "$VAL_DATA" \
    --output-dir "$OUTPUT_DIR/sft-baseline" \
    --wandb-project "$WANDB_PROJECT" \
    --verbose

echo "SFT baseline training complete!"

# Train LoRA model
echo "Training LoRA model..."
occlm train \
    --config configs/training/lora_baseline.yaml \
    --train-data "$TRAIN_DATA" \
    --val-data "$VAL_DATA" \
    --output-dir "$OUTPUT_DIR/lora" \
    --wandb-project "$WANDB_PROJECT" \
    --verbose

echo "LoRA training complete!"

# Run hyperparameter sweep (optional)
read -p "Run hyperparameter sweep? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running hyperparameter sweep..."

    for lr in 1e-5 2e-5 5e-5; do
        for batch_size in 16 32; do
            run_name="lr-${lr}_bs-${batch_size}"
            echo "Training with LR=$lr, Batch Size=$batch_size"

            # Create temporary config
            temp_config="/tmp/train_config_${run_name}.yaml"
            sed -e "s/learning_rate: .*/learning_rate: $lr/" \
                -e "s/per_device_train_batch_size: .*/per_device_train_batch_size: $batch_size/" \
                configs/training/sft_baseline.yaml > "$temp_config"

            occlm train \
                --config "$temp_config" \
                --train-data "$TRAIN_DATA" \
                --val-data "$VAL_DATA" \
                --output-dir "$OUTPUT_DIR/sweep/$run_name" \
                --wandb-project "$WANDB_PROJECT-sweep" \
                --verbose

            rm "$temp_config"
        done
    done

    echo "Hyperparameter sweep complete!"
fi

# Generate training summary
echo "Generating training summary..."
python3 -c "
import json
import os
from pathlib import Path

checkpoint_dir = Path('$OUTPUT_DIR')
models = []

for model_dir in checkpoint_dir.iterdir():
    if model_dir.is_dir():
        config_file = model_dir / 'config.json'
        metrics_file = model_dir / 'trainer_state.json'

        model_info = {'name': model_dir.name}

        # Load config if exists
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                model_info['model_type'] = config.get('model_type', 'unknown')

        # Load metrics if exists
        if metrics_file.exists():
            with open(metrics_file) as f:
                state = json.load(f)
                if state.get('log_history'):
                    last_metrics = state['log_history'][-1]
                    model_info['final_loss'] = last_metrics.get('train_loss', 'N/A')
                    model_info['eval_loss'] = last_metrics.get('eval_loss', 'N/A')

        models.append(model_info)

print('Training Summary:')
for model in models:
    name = model['name']
    loss = model.get('final_loss', 'N/A')
    eval_loss = model.get('eval_loss', 'N/A')
    print(f'  {name}: Train Loss={loss}, Eval Loss={eval_loss}')

with open('training_summary.json', 'w') as f:
    json.dump(models, f, indent=2)
"

echo "Training complete! Summary saved to training_summary.json"
echo "Models saved in: $OUTPUT_DIR"
