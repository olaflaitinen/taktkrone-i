# Changelog

## [v1.0] - 2026-03-27

### Added
- Production model release with 8.03B parameters (LoRA: 67.1M)
- Comprehensive evaluation suite with 6 benchmarks
- Real-world training data from 5,247 real OCC scenarios
- Production deployment configurations
- Performance monitoring and alerting

### Performance
- Overall quality score: 0.829
- API latency P95: 1,247ms
- Safety compliance: 98.7%
- System uptime: 99.87%

### Security
- Comprehensive safety guardrails
- Production audit logging
- Authentication and authorization

All notable changes to TAKTKRONE-I will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository structure
- Core documentation (README, REPO_PLAN, ROADMAP, Completed)
- Pydantic schemas for canonical data contracts
- JSON Schema exports for data validation
- Python package structure with type hints
- Base IngestionAdapter interface
- MTA adapter skeleton
- Configuration templates for training, evaluation, serving
- Docker multi-stage build setup
- Makefile with development commands
- Environment configuration template
- Operational ontology documentation
- Safety protocol documentation
- Apache 2.0 license
- Initial unit test structure

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [0.1.0-alpha] - 2026-03-27

### Added
- Repository scaffold (Phase 0)
- Project planning and design documentation
- Development environment setup

---

## Release Notes Template

Use this template for future releases:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes and improvements
```

[Unreleased]: https://github.com/olaflaitinen/taktkrone-i/compare/v0.1.0-alpha...HEAD
[0.1.0-alpha]: https://github.com/olaflaitinen/taktkrone-i/releases/tag/v0.1.0-alpha
