# Contributing to TAKTKRONE-I

Thank you for your interest in contributing to TAKTKRONE-I! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Contributions](#making-contributions)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## Getting Started

### Prerequisites

- Python 3.10+ or higher
- Git
- (Optional) CUDA-capable GPU for training

### Finding Issues

- Check the [Completed.md](Completed.md) for unclaimed tasks
- Look for issues labeled `good-first-issue` or `help-wanted`
- Review open issues in the GitHub Issues tracker

## Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/olaflaitinen/taktkrone-i.git
   cd taktkrone-i
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**

   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

5. **Verify setup**

   ```bash
   make test
   make lint
   ```

## Making Contributions

### Branching Strategy

- `main` - stable release branch
- `develop` - development integration branch
- `feature/<issue>-<description>` - feature branches
- `fix/<issue>-<description>` - bug fix branches
- `docs/<description>` - documentation branches

### Workflow

1. **Create an issue** (if one doesn't exist)

2. **Create a feature branch**

   ```bash
   git checkout -b feature/123-add-mbta-adapter
   ```

3. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

4. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat(ingestion): add MBTA adapter implementation"
   ```

5. **Push and create PR**

   ```bash
   git push origin feature/123-add-mbta-adapter
   ```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Scopes:**
- `ingestion`: Data ingestion module
- `synthesis`: Synthetic data generation
- `training`: Model training
- `evaluation`: Benchmarks and evaluation
- `serving`: API and serving
- `schemas`: Data schemas
- `cli`: Command line interface
- `docs`: Documentation

**Examples:**

```
feat(ingestion): add MBTA V3 API adapter

Implements the MBTA adapter using their V3 API.
Includes support for predictions, vehicles, and alerts endpoints.

Closes #104
```

```
fix(evaluation): correct nDCG calculation for empty rankings
```

## Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [Ruff](https://github.com/astral-sh/ruff) for linting

### Type Hints

- Use type hints for all public functions
- Use `from __future__ import annotations` for forward references

```python
from __future__ import annotations

def process_event(event: RealtimeEvent) -> ProcessedEvent:
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def fetch_predictions(
    self,
    route_id: str,
    stop_id: Optional[str] = None,
) -> List[Prediction]:
    """Fetch predictions for a route.

    Args:
        route_id: The route identifier.
        stop_id: Optional stop to filter by.

    Returns:
        List of prediction objects.

    Raises:
        APIError: If the API request fails.
    """
```

### File Organization

```
occlm/
  module/
    __init__.py      # Public API exports
    core.py          # Core implementation
    utils.py         # Helper utilities
    types.py         # Type definitions
```

## Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_schemas.py -v

# With coverage
pytest tests/ --cov=occlm --cov-report=html
```

### Writing Tests

- Place tests in `tests/` mirroring the source structure
- Use pytest fixtures for reusable test data
- Name test files `test_<module>.py`
- Name test functions `test_<functionality>_<scenario>`

```python
import pytest
from occlm.schemas import RealtimeEvent

class TestRealtimeEvent:
    def test_valid_event_creation(self, sample_event_data):
        event = RealtimeEvent(**sample_event_data)
        assert event.operator == "mta_nyct"

    def test_invalid_operator_raises(self):
        with pytest.raises(ValueError):
            RealtimeEvent(operator="invalid")
```

### Test Categories

- `tests/unit/` - Unit tests (mocked dependencies)
- `tests/integration/` - Integration tests (real dependencies)
- `tests/load/` - Load/performance tests
- `tests/fixtures/` - Shared test data

## Documentation

### Documentation Types

- **Code docstrings** - In-code documentation
- **README.md** - Project overview
- **docs/** - Detailed documentation
- **examples/** - Usage examples

### Building Docs

```bash
# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

### Documentation Standards

- Keep docs up-to-date with code changes
- Include code examples
- Use clear, concise language
- Add diagrams where helpful

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if user-facing change)

### PR Template

PRs should include:

- **Description** of changes
- **Related issue** number
- **Type of change** (feature, fix, docs, etc.)
- **Testing done**
- **Screenshots** (if UI changes)

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. Address review feedback
4. Squash and merge when approved

### After Merge

- Delete your feature branch
- Close related issues
- Update Completed.md if applicable

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Publish to PyPI (maintainers only)

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email security@example.com

## Recognition

Contributors are recognized in:

- CHANGELOG.md (for significant contributions)
- GitHub contributors page
- Release notes

Thank you for contributing to TAKTKRONE-I!
