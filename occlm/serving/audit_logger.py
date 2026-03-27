"""
Audit Logger - Phase 5 Production.

JSONL-based audit logging with rotation, retention policies.
Tracks all requests, responses, latencies, guardrail triggers.
"""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "AuditLogger",
]

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit Logger - Production.

    JSONL-based logging with rotation and retention.
    Tracks inference requests, responses, latencies, and guardrail events.
    """

    def __init__(
        self,
        log_dir: str = "./logs",
        log_name: str = "audit",
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 10,
    ):
        """Initialize audit logger.

        Args:
            log_dir: Directory for log files
            log_name: Base name for log files
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        self.log_dir = Path(log_dir)
        self.log_name = log_name
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / f"{log_name}.jsonl"

        # Initialize logger
        self._setup_logger()

        # Statistics
        self.requests_logged = 0
        self.events_logged = 0

    def _setup_logger(self) -> None:
        """Setup JSONL logger with rotation."""
        self.logger = logging.getLogger(f"audit.{self.log_name}")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            str(self.log_path),
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
        )

        # JSON formatter
        formatter = logging.Formatter(
            fmt='{"timestamp": "%(created)s", "message": %(message)s}',
            datefmt='%Y-%m-%dT%H:%M:%S',
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def log_request(
        self,
        request_id: str,
        query: str,
        operator: str,
        max_tokens: int,
        temperature: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log inference request.

        Args:
            request_id: Unique request identifier
            query: Input query
            operator: Operator code
            max_tokens: Max tokens setting
            temperature: Temperature setting
            metadata: Additional metadata
        """
        log_entry = {
            "event_type": "REQUEST",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "query": query[:1000],  # Truncate
            "operator": operator,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if metadata:
            log_entry["metadata"] = metadata

        self._write_jsonl(log_entry)
        self.requests_logged += 1

    def log_response(
        self,
        request_id: str,
        response: str,
        latency_ms: float,
        model_version: str,
        guardrails_triggered: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log inference response.

        Args:
            request_id: Unique request identifier
            response: Response text
            latency_ms: Inference latency in ms
            model_version: Model version used
            guardrails_triggered: List of triggered guardrails
            metadata: Additional metadata
        """
        log_entry = {
            "event_type": "RESPONSE",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "response": response[:2000],  # Truncate
            "latency_ms": latency_ms,
            "model_version": model_version,
            "guardrails_triggered": guardrails_triggered or [],
        }

        if metadata:
            log_entry["metadata"] = metadata

        self._write_jsonl(log_entry)

    def log_guardrail_event(
        self,
        request_id: str,
        event_type: str,
        code: str,
        message: str,
        severity: str = "warning",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log guardrail event.

        Args:
            request_id: Unique request identifier
            event_type: Type of guardrail event (INPUT, OUTPUT, COMPLIANCE)
            code: Guardrail code
            message: Event message
            severity: Severity level (info, warning, error)
            metadata: Additional metadata
        """
        log_entry = {
            "event_type": "GUARDRAIL",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "guardrail_type": event_type,
            "guardrail_code": code,
            "message": message,
            "severity": severity,
        }

        if metadata:
            log_entry["metadata"] = metadata

        self._write_jsonl(log_entry)
        self.events_logged += 1

    def log_error(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        traceback: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log error event.

        Args:
            request_id: Unique request identifier
            error_type: Type of error
            error_message: Error message
            traceback: Optional traceback
            metadata: Additional metadata
        """
        log_entry = {
            "event_type": "ERROR",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
        }

        if traceback:
            log_entry["traceback"] = traceback

        if metadata:
            log_entry["metadata"] = metadata

        self._write_jsonl(log_entry)
        self.events_logged += 1

    def log_cache_event(
        self,
        request_id: str,
        event: str,
        cache_key: str,
        hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log cache-related event.

        Args:
            request_id: Unique request identifier
            event: Cache event (HIT, MISS, EVICT)
            cache_key: Cache key (hashed)
            hit: Whether it was a hit
            metadata: Additional metadata
        """
        log_entry = {
            "event_type": "CACHE",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "cache_event": event,
            "cache_key": cache_key[:256],  # Truncate
            "is_hit": hit,
        }

        if metadata:
            log_entry["metadata"] = metadata

        self._write_jsonl(log_entry)

    def _write_jsonl(self, entry: Dict[str, Any]) -> None:
        """Write entry as JSONL.

        Args:
            entry: Log entry dictionary
        """
        try:
            self.logger.info(json.dumps(entry, default=str))
        except Exception as e:
            logger.error(f"Failed to log entry: {e}")

    def get_recent_logs(
        self,
        last_n: int = 100,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent log entries.

        Args:
            last_n: Number of recent entries to retrieve
            event_type: Optional filter by event type

        Returns:
            List of log entries (most recent first)
        """
        entries = []

        try:
            if self.log_path.exists():
                with open(self.log_path, 'r') as f:
                    lines = f.readlines()

                # Read last N lines
                for line in lines[-last_n:]:
                    try:
                        entry = json.loads(line)
                        if event_type is None or entry.get("event_type") == event_type:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue

            # Reverse to get most recent first
            return list(reversed(entries))
        except Exception as e:
            logger.error(f"Failed to read logs: {e}")
            return []

    def get_logs_by_request_id(self, request_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific request.

        Args:
            request_id: Request identifier

        Returns:
            List of log entries for the request
        """
        entries = []

        try:
            if self.log_path.exists():
                with open(self.log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get("request_id") == request_id:
                                entries.append(entry)
                        except json.JSONDecodeError:
                            continue

            return entries
        except Exception as e:
            logger.error(f"Failed to read logs: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics.

        Returns:
            Dict with statistics
        """
        log_files = list(self.log_dir.glob(f"{self.log_name}*"))

        return {
            "requests_logged": self.requests_logged,
            "events_logged": self.events_logged,
            "log_dir": str(self.log_dir),
            "log_files_count": len(log_files),
            "current_log_size_mb": self.log_path.stat().st_size / (1024 * 1024) if self.log_path.exists() else 0,
            "max_file_size_mb": self.max_bytes / (1024 * 1024),
            "backup_count": self.backup_count,
        }

    def configure_rotation(
        self,
        max_size: int,
        backup_count: int,
    ) -> None:
        """Configure log rotation parameters.

        Args:
            max_size: Maximum file size in bytes
            backup_count: Number of backup files to keep
        """
        self.max_bytes = max_size
        self.backup_count = backup_count
        self._setup_logger()
        logger.info(f"Log rotation configured: max_size={max_size}, backup_count={backup_count}")

    def clear_logs(self) -> None:
        """Clear all log files."""
        try:
            log_files = list(self.log_dir.glob(f"{self.log_name}*"))
            for log_file in log_files:
                log_file.unlink()
            logger.info("Log files cleared")
        except Exception as e:
            logger.error(f"Failed to clear logs: {e}")
