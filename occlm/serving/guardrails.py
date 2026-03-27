"""
Guardrails Manager - Phase 5 Production.

Input/output validation, safety compliance checking, language detection.
"""

import logging
import re
from dataclasses import dataclass

__all__ = [
    "GuardrailsManager",
    "ValidationResult",
]

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    reason: str
    severity: str = "info"  # info, warning, error
    flagged_content: list[str] | None = None


class GuardrailsManager:
    """
    Guardrails Manager - Production.

    Validates input/output, checks safety compliance, detects
    language, enforces length constraints.
    """

    def __init__(
        self,
        max_input_length: int = 4000,
        min_input_length: int = 5,
        max_output_length: int = 8000,
        enable_language_detection: bool = True,
        enable_pii_detection: bool = True,
    ):
        """Initialize guardrails manager.

        Args:
            max_input_length: Maximum input length
            min_input_length: Minimum input length
            max_output_length: Maximum output length
            enable_language_detection: Enable language detection
            enable_pii_detection: Enable PII detection
        """
        self.max_input_length = max_input_length
        self.min_input_length = min_input_length
        self.max_output_length = max_output_length
        self.enable_language_detection = enable_language_detection
        self.enable_pii_detection = enable_pii_detection

        self._init_patterns()

    def _init_patterns(self) -> None:
        """Initialize pattern matching for guardrails."""
        # Injection patterns
        self.injection_patterns = [
            (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)", re.I), "OVERRIDE_ATTEMPT"),
            (re.compile(r"(you are|act as|pretend to be)\s+", re.I), "ROLE_HIJACK"),
            (re.compile(r"system\s*:\s*", re.I), "FAKE_SYSTEM"),
            (re.compile(r"<\|[^>]+\|>"), "TOKEN_MANIPULATION"),
            (re.compile(r"\[\s*INST\s*\]", re.I), "INSTRUCTION_INJECTION"),
        ]

        # Safety patterns
        self.safety_patterns = [
            (re.compile(r"(bypass|disable|override)\s+(safety|interlock|protection)", re.I), "SAFETY_OVERRIDE"),
            (re.compile(r"(set|change|control)\s+(signal|switch)", re.I), "CONTROL_COMMAND"),
            (re.compile(r"I (have|will|am)\s+(dispatch|move|control)", re.I), "AUTONOMOUS_CLAIM"),
            (re.compile(r"(emergency|critical|urgent)\s+(stop|halt|shutdown)", re.I), "EMERGENCY_COMMAND"),
        ]

        # PII patterns
        self.pii_patterns = [
            (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN"),
            (re.compile(r"\b\d{3}\s*-\s*\d{2}\s*-\s*\d{4}\b"), "SSN_SPACED"),
            (re.compile(r"\b\d{16}\b"), "CREDIT_CARD"),
            (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "EMAIL"),
            (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "PHONE"),
        ]

        # Profanity patterns (minimal example)
        self.profanity_patterns = [
            re.compile(r"\b(badword1|badword2)\b", re.I),
        ]

    def validate_input(self, query: str) -> ValidationResult:
        """Validate input query.

        Args:
            query: Input query to validate

        Returns:
            ValidationResult with is_valid and reason
        """
        # Length check
        if len(query) < self.min_input_length:
            return ValidationResult(
                is_valid=False,
                reason=f"Input too short (min {self.min_input_length} chars)",
                severity="warning",
            )

        if len(query) > self.max_input_length:
            return ValidationResult(
                is_valid=False,
                reason=f"Input too long (max {self.max_input_length} chars)",
                severity="error",
            )

        # Injection detection
        for pattern, code in self.injection_patterns:
            matches = pattern.findall(query)
            if matches:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Input validation failed: {code}",
                    severity="error",
                    flagged_content=[str(m) for m in matches],
                )

        # PII detection
        if self.enable_pii_detection:
            pii_result = self._check_pii(query)
            if not pii_result["is_clean"]:
                return ValidationResult(
                    is_valid=False,
                    reason=f"PII detected: {', '.join(pii_result['types'])}",
                    severity="warning",
                    flagged_content=pii_result.get("samples", []),
                )

        return ValidationResult(
            is_valid=True,
            reason="Input validation passed",
            severity="info",
        )

    def validate_output(self, response: str) -> ValidationResult:
        """Validate output response.

        Args:
            response: Output response to validate

        Returns:
            ValidationResult with is_valid and reason
        """
        # Length check
        if len(response) > self.max_output_length:
            return ValidationResult(
                is_valid=False,
                reason=f"Output too long (max {self.max_output_length} chars)",
                severity="warning",
            )

        # Safety pattern check
        for pattern, code in self.safety_patterns:
            matches = pattern.findall(response)
            if matches:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Output validation failed: {code}",
                    severity="error",
                    flagged_content=[str(m) for m in matches],
                )

        # Profanity check
        profanity_found = []
        for pattern in self.profanity_patterns:
            matches = pattern.findall(response)
            if matches:
                profanity_found.extend(matches)

        if profanity_found:
            return ValidationResult(
                is_valid=False,
                reason="Output contains inappropriate content",
                severity="warning",
                flagged_content=profanity_found,
            )

        return ValidationResult(
            is_valid=True,
            reason="Output validation passed",
            severity="info",
        )

    def check_safety_compliance(self, response: str) -> dict[str, any]:
        """Check response for safety compliance.

        Args:
            response: Response to check

        Returns:
            Dict with compliance results
        """
        compliance = {
            "is_compliant": True,
            "violations": [],
            "warnings": [],
            "confidence": 1.0,
        }

        # Check safety patterns
        for pattern, code in self.safety_patterns:
            if pattern.search(response):
                compliance["is_compliant"] = False
                compliance["violations"].append(code)

        # Check length
        if len(response) > self.max_output_length:
            compliance["warnings"].append("OUTPUT_LENGTH_WARNING")

        # Check for confidence statements
        if re.search(r"confidence.*0\.\d", response.lower()):
            compliance["warnings"].append("LOW_CONFIDENCE")

        # Overall confidence
        if compliance["violations"]:
            compliance["confidence"] = 0.0
        elif compliance["warnings"]:
            compliance["confidence"] = 0.7
        else:
            compliance["confidence"] = 0.95

        return compliance

    def detect_language(self, text: str) -> dict[str, any]:
        """Detect language of text (basic implementation).

        Args:
            text: Text to detect language for

        Returns:
            Dict with detected language info
        """
        if not self.enable_language_detection:
            return {"language": "unknown", "confidence": 0.0}

        # Placeholder implementation
        # Would use langdetect or similar in production
        try:
            import langdetect
            try:
                lang = langdetect.detect(text)
                prob = langdetect.detect_langs(text)[0].prob
                return {
                    "language": lang,
                    "confidence": prob,
                    "is_english": lang == "en",
                }
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")
                return {"language": "unknown", "confidence": 0.0}
        except ImportError:
            logger.debug("langdetect not available, skipping language detection")
            return {"language": "unknown", "confidence": 0.0}

    def _check_pii(self, text: str) -> dict[str, any]:
        """Check for PII in text.

        Args:
            text: Text to check

        Returns:
            Dict with PII detection results
        """
        pii_types = set()
        samples = []

        for pattern, pii_type in self.pii_patterns:
            matches = pattern.findall(text)
            if matches:
                pii_types.add(pii_type)
                samples.extend(matches[:2])  # Keep first 2 samples

        return {
            "is_clean": len(pii_types) == 0,
            "types": list(pii_types),
            "samples": samples,
        }

    def get_validation_stats(self) -> dict[str, any]:
        """Get validation configuration stats.

        Returns:
            Dict with configuration information
        """
        return {
            "max_input_length": self.max_input_length,
            "min_input_length": self.min_input_length,
            "max_output_length": self.max_output_length,
            "language_detection_enabled": self.enable_language_detection,
            "pii_detection_enabled": self.enable_pii_detection,
            "injection_patterns_count": len(self.injection_patterns),
            "safety_patterns_count": len(self.safety_patterns),
            "pii_patterns_count": len(self.pii_patterns),
        }
