"""
TAKTKRONE-I API Server - Phase 5 Production.

FastAPI-based REST API with comprehensive endpoints, middleware, exception handling.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .audit_logger import AuditLogger
from .engine import (
    AsyncOCCInferenceEngine,
    InferenceRequest,
    OCCResponse,
)
from .guardrails import GuardrailsManager

__all__ = [
    "app",
    "get_engine",
]

logger = logging.getLogger(__name__)


# Request/Response models for API

class QueryRequest(BaseModel):
    """API request for OCC query."""

    query: str = Field(min_length=5, max_length=4000, description="User query")
    operator: str = Field(default="generic", description="Operator code")
    context: dict[str, Any] | None = Field(default=None, description="Additional context")
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class QueryResponse(BaseModel):
    """API response for OCC query."""

    request_id: str
    timestamp: str
    response: OCCResponse
    latency_ms: float
    model_version: str
    guardrails_triggered: list[str] = Field(default_factory=list)


class BatchQueryRequest(BaseModel):
    """Batch query request."""

    queries: list[QueryRequest] = Field(min_length=1, max_length=32)


class BatchQueryResponse(BaseModel):
    """Batch query response."""

    results: list[QueryResponse]
    total_latency_ms: float
    batch_id: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    model_version: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness check response."""

    ready: bool
    reason: str | None = None


class ModelInfoResponse(BaseModel):
    """Model information response."""

    model_path: str
    model_version: str
    device: str
    precision: str
    guardrails_enabled: bool


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str | None = None
    request_id: str | None = None


# Global instances
engine: AsyncOCCInferenceEngine | None = None
audit_logger: AuditLogger | None = None
guardrails: GuardrailsManager | None = None


def get_engine() -> AsyncOCCInferenceEngine:
    """Get engine instance."""
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    return engine


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance."""
    if audit_logger is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit logger not initialized"
        )
    return audit_logger


def get_guardrails() -> GuardrailsManager:
    """Get guardrails manager instance."""
    if guardrails is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Guardrails not initialized"
        )
    return guardrails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global engine, audit_logger, guardrails

    # Configuration
    model_path = os.environ.get("OCCLM_MODEL_PATH", "metrolm/taktkrone-i-v0.1")
    retriever_path = os.environ.get("OCCLM_RETRIEVER_PATH")
    device = os.environ.get("OCCLM_DEVICE", "cuda")
    precision = os.environ.get("OCCLM_PRECISION", "fp16")
    log_dir = os.environ.get("OCCLM_LOG_DIR", "./logs")

    logger.info(f"Loading model: {model_path}")
    logger.info(f"Device: {device}, Precision: {precision}")

    # Initialize engine
    engine = AsyncOCCInferenceEngine(
        model_path=model_path,
        retriever_path=retriever_path,
        device=device,
        precision=precision,
        enable_guardrails=True,
    )
    engine.load()

    # Initialize audit logger
    audit_logger = AuditLogger(log_dir=log_dir)
    logger.info(f"Audit logger initialized: {log_dir}")

    # Initialize guardrails
    guardrails = GuardrailsManager()
    logger.info("Guardrails initialized")

    logger.info("Startup complete")

    yield

    # Cleanup
    logger.info("Shutting down")
    if engine:
        engine.clear_cache()
    if audit_logger:
        stats = audit_logger.get_statistics()
        logger.info(f"Audit statistics: {stats}")


# Create FastAPI app
app = FastAPI(
    title="TAKTKRONE-I API",
    description="Metro Operations Control Center Decision Support API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("OCCLM_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request/response logging

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests and responses."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id

    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds() * 1000

    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.2f}ms"
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Exception handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            request_id=request.headers.get("X-Request-ID"),
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if os.environ.get("OCCLM_DEBUG") else None,
            request_id=request.headers.get("X-Request-ID"),
        ).model_dump()
    )


# Health and readiness endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    eng = get_engine()
    return HealthResponse(
        status="healthy",
        model_loaded=eng.model is not None,
        model_version=eng.model_version,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """Readiness check for Kubernetes."""
    try:
        eng = get_engine()
        if eng.model is None:
            return ReadyResponse(ready=False, reason="Model not loaded")
        return ReadyResponse(ready=True)
    except Exception as e:
        return ReadyResponse(ready=False, reason=str(e))


# Main API endpoints

@app.post("/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process single OCC query.

    Returns structured response with recommendations,
    confidence levels, and safety considerations.
    """
    request_id = str(uuid4())
    eng = get_engine()
    audit = get_audit_logger()
    gr = get_guardrails()

    # Validate input
    validation = gr.validate_input(request.query)
    if not validation.is_valid:
        audit.log_guardrail_event(
            request_id=request_id,
            event_type="INPUT",
            code="VALIDATION_FAILED",
            message=validation.reason,
            severity=validation.severity,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.reason,
        )

    # Log request
    audit.log_request(
        request_id=request_id,
        query=request.query,
        operator=request.operator,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )

    # Process query
    result = await eng.query_async(
        query=request.query,
        operator=request.operator,
        context=request.context,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )

    # Validate output
    output_validation = gr.validate_output(result.response.summary)
    if not output_validation.is_valid:
        audit.log_guardrail_event(
            request_id=request_id,
            event_type="OUTPUT",
            code="VALIDATION_FAILED",
            message=output_validation.reason,
            severity=output_validation.severity,
        )
        result.response.error = "Output validation failed"
        result.guardrails_triggered.append("OUTPUT_VALIDATION_FAILED")

    # Log response
    audit.log_response(
        request_id=request_id,
        response=result.response.summary,
        latency_ms=result.latency_ms,
        model_version=result.model_version,
        guardrails_triggered=result.guardrails_triggered,
    )

    return QueryResponse(
        request_id=request_id,
        timestamp=result.timestamp,
        response=result.response,
        latency_ms=result.latency_ms,
        model_version=result.model_version,
        guardrails_triggered=result.guardrails_triggered,
    )


@app.post("/v1/batch", response_model=BatchQueryResponse)
async def batch_query(request: BatchQueryRequest):
    """
    Process batch of OCC queries.

    More efficient than multiple single queries.
    Limited to 32 queries per batch.
    """
    import time

    batch_id = str(uuid4())
    eng = get_engine()
    audit = get_audit_logger()
    gr = get_guardrails()

    start_time = time.time()

    # Validate all inputs
    for idx, query_req in enumerate(request.queries):
        validation = gr.validate_input(query_req.query)
        if not validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query {idx} validation failed: {validation.reason}",
            )

    # Convert to internal request format
    internal_requests = [
        InferenceRequest(
            query=q.query,
            operator=q.operator,
            context=q.context,
            max_tokens=q.max_tokens,
            temperature=q.temperature,
        )
        for q in request.queries
    ]

    # Process batch
    results = await eng.batch_query_async(internal_requests)

    total_latency = (time.time() - start_time) * 1000

    # Log batch
    audit.log_request(
        request_id=batch_id,
        query=f"Batch of {len(request.queries)} queries",
        operator="batch",
        max_tokens=512,
        temperature=0.7,
        metadata={"batch_size": len(request.queries)},
    )

    return BatchQueryResponse(
        results=[
            QueryResponse(
                request_id=r.request_id,
                timestamp=r.timestamp,
                response=r.response,
                latency_ms=r.latency_ms,
                model_version=r.model_version,
                guardrails_triggered=r.guardrails_triggered,
            )
            for r in results
        ],
        total_latency_ms=total_latency,
        batch_id=batch_id,
    )


@app.get("/v1/model/info", response_model=ModelInfoResponse)
async def model_info():
    """Get model information."""
    eng = get_engine()
    return ModelInfoResponse(
        model_path=eng.model_path,
        model_version=eng.model_version,
        device=eng.device,
        precision=eng.precision,
        guardrails_enabled=eng.enable_guardrails,
    )


@app.get("/v1/operators")
async def list_operators():
    """List supported operators."""
    return {
        "operators": [
            {"code": "mta_nyct", "name": "MTA New York City Transit", "region": "New York, USA"},
            {"code": "mbta", "name": "MBTA", "region": "Boston, USA"},
            {"code": "wmata", "name": "WMATA", "region": "Washington DC, USA"},
            {"code": "bart", "name": "BART", "region": "San Francisco, USA"},
            {"code": "tfl", "name": "Transport for London", "region": "London, UK"},
            {"code": "generic", "name": "Generic Metro", "region": "Multi"},
        ]
    }


@app.get("/v1/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    eng = get_engine()
    return eng.get_cache_stats()


@app.post("/v1/cache/clear")
async def cache_clear():
    """Clear inference cache."""
    eng = get_engine()
    eng.clear_cache()
    return {"status": "cleared"}


@app.get("/v1/audit/logs")
async def get_audit_logs(last_n: int = 100):
    """Get recent audit logs."""
    audit = get_audit_logger()
    logs = audit.get_recent_logs(last_n=last_n)
    return {
        "total": len(logs),
        "logs": logs,
    }


# CLI entry point

def main():
    """Run API server."""
    import argparse

    parser = argparse.ArgumentParser(description="Run TAKTKRONE-I API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--model", help="Model path", default=None)
    parser.add_argument("--device", default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on changes")

    args = parser.parse_args()

    if args.model:
        os.environ["OCCLM_MODEL_PATH"] = args.model
    os.environ["OCCLM_DEVICE"] = args.device

    import uvicorn
    uvicorn.run(
        "occlm.serving.api:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
