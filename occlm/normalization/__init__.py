"""
Data normalization and validation for canonical transit schemas.

This package handles conversion of raw operator-specific data into
canonical OCCLM data contracts and validates data quality.
"""

from occlm.normalization.normalizer import SchemaNormalizer
from occlm.normalization.validator import DataValidator, ValidationResult

__all__ = [
    "SchemaNormalizer",
    "DataValidator",
    "ValidationResult",
]
