"""
TAKTKRONE-I Serving Module - Phase 5 Production.

Provides model inference infrastructure including:
- AsyncOCCInferenceEngine for async model inference with caching
- GuardrailsManager for input/output validation and safety checks
- AuditLogger for JSONL-based audit logging
- FastAPI REST API server with comprehensive endpoints
- Guardrail checking and structured response generation
"""

from .audit_logger import AuditLogger
from .engine import (
    AsyncOCCInferenceEngine,
    GuardrailResult,
    InferenceRequest,
    InferenceResult,
    LRUCache,
    OCCResponse,
)
from .guardrails import (
    GuardrailsManager,
    ValidationResult,
)

__all__ = [
    # Core engine
    "AsyncOCCInferenceEngine",
    # Request/Response types
    "InferenceRequest",
    "InferenceResult",
    "OCCResponse",
    # Guardrails
    "GuardrailResult",
    "GuardrailsManager",
    "ValidationResult",
    # Audit logging
    "AuditLogger",
    # Utilities
    "LRUCache",
]
