.PHONY: help install install-dev setup-dev clean format lint typecheck test test-cov test-unit test-integration docker-build docker-run ingest-mta synthesize train evaluate serve demo

# Default target
help:
	@echo "TAKTKRONE-I Development Commands"
	@echo "================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install core dependencies"
	@echo "  make install-dev      Install dev dependencies"
	@echo "  make setup-dev        Full dev setup with pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Lint code with ruff"
	@echo "  make typecheck        Type check with mypy"
	@echo "  make test             Run all tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  make ingest-mta       Ingest MTA data (requires API key)"
	@echo "  make synthesize       Generate synthetic scenarios"
	@echo "  make validate-data    Validate data against schemas"
	@echo ""
	@echo "Training & Evaluation:"
	@echo "  make train            Run training pipeline"
	@echo "  make evaluate         Run evaluation benchmarks"
	@echo "  make tensorboard      Launch TensorBoard"
	@echo ""
	@echo "Serving:"
	@echo "  make serve            Start API server"
	@echo "  make demo             Launch Gradio demo"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run in Docker container"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and caches"

# Setup and Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-all:
	pip install -e ".[all]"

setup-dev: install-dev
	pre-commit install
	@echo "Development environment ready!"

# Code Quality
format:
	black occlm/ tests/ scripts/
	isort occlm/ tests/ scripts/
	@echo "Code formatted successfully!"

lint:
	ruff check occlm/ tests/ scripts/
	@echo "Linting complete!"

typecheck:
	mypy occlm/
	@echo "Type checking complete!"

# Testing
test:
	pytest tests/

test-cov:
	pytest tests/ --cov=occlm --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-watch:
	pytest-watch tests/

# Data Pipeline
ingest-mta:
	occlm ingest mta --lines 1,2,3,4,5,6,7 --days 7
	@echo "MTA data ingestion complete!"

ingest-mbta:
	occlm ingest mbta --routes Red,Orange,Blue --days 7
	@echo "MBTA data ingestion complete!"

ingest-all:
	occlm ingest --operators mta,mbta,bart --days 7
	@echo "Multi-operator ingestion complete!"

synthesize:
	occlm synthesize \
		--scenario-types delay,disruption,recovery,turnback \
		--num-scenarios 1000 \
		--output-dir data/synthetic/scenarios/
	@echo "Synthetic scenarios generated!"

validate-data:
	occlm validate \
		--schema-dir data_contracts/ \
		--data-dir data/normalized/ \
		--recursive
	@echo "Data validation complete!"

# Training
train:
	occlm train \
		--config configs/training/sft_baseline.yaml \
		--output-dir models/taktkrone-v0.1
	@echo "Training complete!"

train-lora:
	occlm train \
		--config configs/training/lora_efficient.yaml \
		--output-dir models/taktkrone-lora-v0.1
	@echo "LoRA training complete!"

tensorboard:
	tensorboard --logdir runs/ --port 6006

# Evaluation
evaluate:
	occlm evaluate \
		--model-path models/taktkrone-v0.1 \
		--benchmark all \
		--output-dir results/eval_v0.1/
	@echo "Evaluation complete!"

evaluate-safety:
	occlm evaluate \
		--model-path models/taktkrone-v0.1 \
		--benchmark safety_guard \
		--output-dir results/safety_eval/
	@echo "Safety evaluation complete!"

# Serving
serve:
	occlm serve \
		--model-path models/taktkrone-v0.1 \
		--host 0.0.0.0 \
		--port 8000 \
		--enable-rag

demo:
	occlm demo \
		--model-path models/taktkrone-v0.1 \
		--share

# Docker
docker-build:
	docker build -t taktkrone:latest -f docker/Dockerfile .
	@echo "Docker image built: taktkrone:latest"

docker-run:
	docker run -it --rm \
		-p 8000:8000 \
		-v $(PWD)/models:/models \
		-v $(PWD)/data:/data \
		taktkrone:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "Cleanup complete!"

# Documentation
docs-serve:
	mkdocs serve

docs-build:
	mkdocs build

# Notebooks
notebook:
	jupyter lab --notebook-dir=notebooks/

# Dataset management
export-schemas:
	python scripts/export_schemas.py \
		--output-dir data_contracts/
	@echo "Schemas exported to data_contracts/"

# Quick checks before commit
precommit: format lint typecheck test-unit
	@echo "Pre-commit checks passed!"
