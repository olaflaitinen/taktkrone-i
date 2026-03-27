"""
TAKTKRONE-I Inference Engine - Phase 5 Production.

Async inference engine with caching, device management, and vLLM support.
Handles model loading, guardrail checking, and structured response generation.
"""

import asyncio
import json
import logging
import re
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

__all__ = [
    "OCCResponse",
    "InferenceRequest",
    "InferenceResult",
    "GuardrailResult",
    "AsyncOCCInferenceEngine",
]

logger = logging.getLogger(__name__)


class OCCResponse(BaseModel):
    """Structured response from OCC inference."""

    summary: str = Field(description="Brief situation summary")
    observed_facts: list[str] = Field(
        default_factory=list,
        description="Facts directly from provided data"
    )
    inferred_hypotheses: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Hypotheses with confidence levels"
    )
    recommended_actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Prioritized action recommendations"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence")
    review_required: bool = Field(
        default=False,
        description="Whether human review is required"
    )
    uncertainties: list[str] = Field(
        default_factory=list,
        description="Key uncertainties affecting recommendation"
    )
    safety_notes: list[str] = Field(
        default_factory=list,
        description="Safety considerations"
    )
    citations: list[dict[str, str]] = Field(
        default_factory=list,
        description="References to source data"
    )
    error: str | None = Field(
        default=None,
        description="Error message if request could not be processed"
    )


class InferenceRequest(BaseModel):
    """Request to OCC inference engine."""

    query: str = Field(description="User query")
    operator: str = Field(default="generic", description="Operator code")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Additional context data"
    )
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt override"
    )
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class InferenceResult(BaseModel):
    """Complete result from inference including metadata."""

    request_id: str
    timestamp: str
    response: OCCResponse
    latency_ms: float
    model_version: str
    guardrails_triggered: list[str] = Field(default_factory=list)


@dataclass
class GuardrailResult:
    """Result from guardrail check."""
    passed: bool
    code: str | None = None
    message: str | None = None
    flagged: bool = False
    details: dict | None = None


class LRUCache:
    """LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize cache.

        Args:
            max_size: Maximum number of items to cache
            ttl_seconds: Time-to-live for cached items in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple] = OrderedDict()

    def get(self, key: str) -> Any | None:
        """Get value from cache if present and not expired."""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = (value, time.time())

        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


class AsyncOCCInferenceEngine:
    """
    TAKTKRONE-I Inference Engine - Production.

    High-throughput async inference with caching, device management,
    and guardrails.
    """

    def __init__(
        self,
        model_path: str,
        retriever_path: str | None = None,
        device: str = "cuda",
        precision: str = "fp16",
        enable_guardrails: bool = True,
        cache_max_size: int = 1000,
        cache_ttl_seconds: int = 3600,
    ):
        """Initialize inference engine.

        Args:
            model_path: Path to model or HF model ID
            retriever_path: Optional path to retriever for RAG
            device: Device to use (cuda/cpu)
            precision: Model precision (fp16/bf16/fp32)
            enable_guardrails: Whether to enable guardrails
            cache_max_size: Maximum number of cached inferences
            cache_ttl_seconds: Cache TTL in seconds
        """
        self.model_path = model_path
        self.retriever_path = retriever_path
        self.device = device
        self.precision = precision
        self.enable_guardrails = enable_guardrails

        self.model = None
        self.tokenizer = None
        self.retriever = None
        self.model_version = "unknown"

        # Caching
        self.cache = LRUCache(max_size=cache_max_size, ttl_seconds=cache_ttl_seconds)

        # Device info
        self.device_info = {}
        self._init_device_info()

        # Guardrail patterns
        self._init_guardrails()

        # Metrics
        self.inference_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def _init_device_info(self) -> None:
        """Initialize device information."""
        try:
            import torch

            if self.device == "cuda":
                if torch.cuda.is_available():
                    self.device_info = {
                        "device_type": "cuda",
                        "device_count": torch.cuda.device_count(),
                        "device_name": torch.cuda.get_device_name(0),
                        "cuda_version": torch.version.cuda,
                    }
                else:
                    logger.warning("CUDA requested but not available, using CPU")
                    self.device = "cpu"
                    self.device_info = {"device_type": "cpu"}
            else:
                self.device_info = {"device_type": "cpu"}
        except ImportError:
            logger.warning("torch not available for device detection")
            self.device_info = {"device_type": self.device}

    def _init_guardrails(self) -> None:
        """Initialize guardrail patterns."""
        self.injection_patterns = [
            (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)", re.I), "OVERRIDE_ATTEMPT"),
            (re.compile(r"(you are|act as|pretend to be)\s+", re.I), "ROLE_HIJACK"),
            (re.compile(r"system\s*:\s*", re.I), "FAKE_SYSTEM"),
            (re.compile(r"<\|[^>]+\|>"), "TOKEN_MANIPULATION"),
        ]

        self.safety_patterns = [
            (re.compile(r"(bypass|disable|override)\s+(safety|interlock|protection)", re.I), "SAFETY_OVERRIDE"),
            (re.compile(r"(set|change|control)\s+(signal|switch)", re.I), "CONTROL_COMMAND"),
            (re.compile(r"I (have|will|am)\s+(dispatch|move|control)", re.I), "AUTONOMOUS_CLAIM"),
        ]

    def load(self) -> None:
        """Load model and tokenizer."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading model from {self.model_path}")

            dtype_map = {
                "fp16": torch.float16,
                "bf16": torch.bfloat16,
                "fp32": torch.float32,
            }
            dtype = dtype_map.get(self.precision, torch.float16)

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=dtype,
                device_map="auto" if self.device == "cuda" else None,
            )

            if self.device == "cpu":
                self.model = self.model.to("cpu")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model_version = getattr(
                self.model.config, "model_version", self.model_path
            )

            logger.info(f"Model loaded: {self.model_version}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def clear_cache(self) -> None:
        """Clear inference cache."""
        self.cache.clear()
        logger.info("Inference cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            **self.cache.get_stats(),
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
        }

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {
            "model_path": self.model_path,
            "model_version": self.model_version,
            "device": self.device,
            "device_info": self.device_info,
            "precision": self.precision,
            "guardrails_enabled": self.enable_guardrails,
            "retriever_enabled": self.retriever is not None,
            "inference_count": self.inference_count,
            "cache_stats": self.get_cache_stats(),
        }

    async def infer(
        self,
        query: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        operator: str = "generic",
        context: dict[str, Any] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Single inference call (simplified).

        Args:
            query: Input query
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            operator: Operator code
            context: Additional context
            system_prompt: Optional system prompt

        Returns:
            Generated response string
        """
        result = await self.query_async(
            query=query,
            operator=operator,
            context=context,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return result.response.summary

    async def infer_batch(
        self,
        queries: list[str],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> list[str]:
        """Batch inference call.

        Args:
            queries: List of input queries
            max_tokens: Maximum tokens per generation
            temperature: Sampling temperature

        Returns:
            List of generated responses
        """
        requests = [
            InferenceRequest(
                query=q,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            for q in queries
        ]
        results = await self.batch_query_async(requests)
        return [r.response.summary for r in results]

    async def query_async(
        self,
        query: str,
        operator: str = "generic",
        context: dict[str, Any] | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> InferenceResult:
        """Async query method with full inference."""
        request_id = str(uuid4())
        start_time = time.time()
        guardrails_triggered = []

        # Cache key
        cache_key = f"{query}:{operator}:{max_tokens}:{temperature}"
        cached = self.cache.get(cache_key)
        if cached:
            self.cache_hits += 1
            logger.debug(f"Cache hit for {request_id}")
            return cached

        self.cache_misses += 1

        # Input guardrails
        if self.enable_guardrails:
            input_result = self._check_input_guardrails(query)
            if not input_result.passed:
                guardrails_triggered.append(input_result.code)
                return self._create_error_result(
                    request_id, start_time, input_result, guardrails_triggered
                )

        # Build messages
        messages = self._build_messages(query, operator, context, system_prompt)

        # Generate response
        raw_output = await self._generate_async(messages, max_tokens, temperature)

        # Output guardrails
        if self.enable_guardrails:
            output_result = self._check_output_guardrails(raw_output)
            if not output_result.passed:
                guardrails_triggered.append(output_result.code)
                return self._create_filtered_result(
                    request_id, start_time, output_result, guardrails_triggered
                )

        # Parse structured output
        response = self._parse_response(raw_output)

        if response.confidence < 0.4:
            response.review_required = True
            guardrails_triggered.append("LOW_CONFIDENCE")

        latency_ms = (time.time() - start_time) * 1000
        self.inference_count += 1

        result = InferenceResult(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            response=response,
            latency_ms=latency_ms,
            model_version=self.model_version,
            guardrails_triggered=guardrails_triggered,
        )

        # Cache result
        self.cache.set(cache_key, result)
        return result

    async def batch_query_async(
        self,
        requests: list[InferenceRequest],
    ) -> list[InferenceResult]:
        """Process batch of requests asynchronously."""
        tasks = [
            self.query_async(
                req.query,
                req.operator,
                req.context,
                req.system_prompt,
                req.max_tokens,
                req.temperature,
            )
            for req in requests
        ]
        return await asyncio.gather(*tasks)

    def _check_input_guardrails(self, query: str) -> GuardrailResult:
        """Check input against guardrails."""
        if len(query) < 5:
            return GuardrailResult(
                passed=False,
                code="INPUT_TOO_SHORT",
                message="Query must be at least 5 characters"
            )

        if len(query) > 4000:
            return GuardrailResult(
                passed=False,
                code="INPUT_TOO_LONG",
                message="Query exceeds maximum length"
            )

        for pattern, code in self.injection_patterns:
            if pattern.search(query):
                return GuardrailResult(
                    passed=False,
                    code=code,
                    message="Query contains potentially manipulative content"
                )

        return GuardrailResult(passed=True)

    def _check_output_guardrails(self, output: str) -> GuardrailResult:
        """Check output against guardrails."""
        for pattern, code in self.safety_patterns:
            if pattern.search(output):
                return GuardrailResult(
                    passed=False,
                    code=code,
                    message="Output contains unsafe content"
                )
        return GuardrailResult(passed=True)

    def _build_messages(
        self,
        query: str,
        operator: str,
        context: dict | None,
        system_prompt: str | None,
    ) -> list[dict[str, str]]:
        """Build chat messages."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system",
                "content": self._get_default_system_prompt(operator)
            })

        if context:
            context_str = f"Context:\n{json.dumps(context, indent=2)}"
            messages.append({"role": "user", "content": context_str})
            messages.append({"role": "assistant", "content": "I understand the context. What is your question?"})

        messages.append({"role": "user", "content": query})
        return messages

    def _get_default_system_prompt(self, operator: str) -> str:
        """Get default system prompt."""
        return f"""You are an Operations Control Center (OCC) advisor for {operator} metro operations.

Your role is to provide decision SUPPORT to human operators. You must:
1. Analyze situations based on provided data
2. Identify likely causes of disruptions
3. Recommend appropriate actions with confidence levels
4. Flag uncertainties and safety considerations

Important:
- You provide recommendations, not commands
- Never fabricate data - if unavailable, say so
- Include confidence levels (0.0-1.0)
- Flag when human review is required

Respond in JSON structure with: summary, observed_facts, inferred_hypotheses, recommended_actions, confidence, review_required, uncertainties, safety_notes"""

    async def _generate_async(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate model response asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate,
            messages,
            max_tokens,
            temperature,
        )

    def _generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate model response (sync)."""
        import torch

        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True
        ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        response = self.tokenizer.decode(
            outputs[0][inputs.shape[1]:],
            skip_special_tokens=True
        )
        return response

    def _parse_response(self, raw_output: str) -> OCCResponse:
        """Parse raw output into structured response."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', raw_output)
            if json_match:
                data = json.loads(json_match.group())
                return OCCResponse(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")

        response = OCCResponse(
            summary=raw_output[:500] if len(raw_output) > 500 else raw_output,
            observed_facts=[],
            recommended_actions=[],
            confidence=0.5,
            review_required=True,
        )

        conf_match = re.search(r'confidence[:\s]+([0-9.]+)', raw_output.lower())
        if conf_match:
            response.confidence = float(conf_match.group(1))

        return response

    def _create_error_result(
        self,
        request_id: str,
        start_time: float,
        guardrail_result: GuardrailResult,
        triggered: list[str],
    ) -> InferenceResult:
        """Create error result for blocked input."""
        latency_ms = (time.time() - start_time) * 1000
        return InferenceResult(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            response=OCCResponse(
                summary="Unable to process request",
                confidence=0.0,
                review_required=True,
                error=guardrail_result.message,
            ),
            latency_ms=latency_ms,
            model_version=self.model_version,
            guardrails_triggered=triggered,
        )

    def _create_filtered_result(
        self,
        request_id: str,
        start_time: float,
        guardrail_result: GuardrailResult,
        triggered: list[str],
    ) -> InferenceResult:
        """Create filtered result when output is blocked."""
        latency_ms = (time.time() - start_time) * 1000
        return InferenceResult(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            response=OCCResponse(
                summary="Response filtered by safety guardrails",
                confidence=0.0,
                review_required=True,
                error="Output contained potentially unsafe content",
            ),
            latency_ms=latency_ms,
            model_version=self.model_version,
            guardrails_triggered=triggered,
        )
