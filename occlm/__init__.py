"""
TAKTKRONE-I: Metro Operations Control Center Language Model

occLM (Operations Control Center Language Model) - Part of the metroLM family

This package provides tools for:
- Ingesting and normalizing transit data from multiple operators
- Generating synthetic OCC scenarios
- Training domain-adapted language models
- Evaluating operational reasoning capabilities
- Serving OCC decision support recommendations

Copyright 2026 metroLM Contributors
Licensed under Apache 2.0
"""

__version__ = "0.1.0-alpha"
__author__ = "metroLM Contributors"
__license__ = "Apache 2.0"

from types import ModuleType
from typing import Any

# Core schemas
from occlm.schemas import (
    ActionRecommendation,
    IncidentRecord,
    NetworkSnapshot,
    OCCDialogueSample,
    RealtimeEvent,
)


# Submodule imports (lazy loading for optional dependencies)
def _lazy_import(module_name: str) -> ModuleType:
    """Lazy import to avoid loading heavy dependencies at package import"""
    import importlib

    return importlib.import_module(f"occlm.{module_name}")


# Public API
__all__ = [
    # Schemas
    "RealtimeEvent",
    "NetworkSnapshot",
    "IncidentRecord",
    "OCCDialogueSample",
    "ActionRecommendation",
    # Submodules
    "training",
    "evaluation",
    "serving",
    "synthesis",
    "ingestion",
    # Version
    "__version__",
]


# Lazy submodule accessors
def __getattr__(name: str) -> Any:
    """Lazy load submodules on first access"""
    if name in ("training", "evaluation", "serving", "synthesis", "ingestion"):
        return _lazy_import(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
