"""Observability middleware for search pipeline tracing.

Implements the observability layer described in semanticAdditions.md §20:
  - Records per-request timing for each pipeline stage
  - Logs structured search metrics for debugging and monitoring
  - Provides request ID correlation across log entries

This is a lightweight foundation that can be extended with OpenTelemetry
(Phase 5) when needed.
"""

import contextvars
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("observability")

# Context variable to store search metrics for the current request
_search_metrics: contextvars.ContextVar[Optional["SearchMetrics"]] = contextvars.ContextVar(
    "search_metrics", default=None
)


@dataclass
class SearchMetrics:
    """Metrics collected during a search request."""

    request_id: str
    query: str = ""
    start_time: float = field(default_factory=time.time)
    stages: dict[str, float] = field(default_factory=dict)
    cache_hit: bool = False
    variants_count: int = 0
    bm25_count: int = 0
    dense_count: int = 0
    fused_count: int = 0
    final_count: int = 0
    reranked: bool = False
    error: Optional[str] = None


def get_search_metrics() -> Optional[SearchMetrics]:
    """Get the current request's search metrics."""
    return _search_metrics.get()


def set_search_metrics(metrics: SearchMetrics) -> None:
    """Set the current request's search metrics."""
    _search_metrics.set(metrics)


def clear_search_metrics() -> None:
    """Clear the current request's search metrics."""
    _search_metrics.set(None)


def record_stage(stage_name: str, elapsed: float) -> None:
    """Record a pipeline stage timing."""
    metrics = get_search_metrics()
    if metrics:
        metrics.stages[stage_name] = elapsed


class SearchObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware that logs search pipeline metrics for each request."""

    async def dispatch(self, request: Request, call_next):
        # Skip non-search endpoints
        if "/search" not in request.url.path:
            return await call_next(request)

        request_id = str(uuid.uuid4())[:8]
        query = request.query_params.get("q", "")
        start_time = time.time()

        # Initialize metrics for this request
        metrics = SearchMetrics(
            request_id=request_id,
            query=query[:200],  # Truncate long queries
            start_time=start_time,
        )
        set_search_metrics(metrics)

        # Log request start
        logger.info(
            f"[{request_id}] Search request started: "
            f"method={request.method}, path={request.url.path}, "
            f"query_params={dict(request.query_params)}"
        )

        try:
            response = await call_next(request)
            elapsed = time.time() - start_time

            # Log request completion with detailed metrics
            metrics.stages["total"] = elapsed
            logger.info(
                f"[{request_id}] Search request completed: "
                f"status={response.status_code}, elapsed={elapsed:.3f}s, "
                f"cache_hit={metrics.cache_hit}, "
                f"variants={metrics.variants_count}, "
                f"bm25={metrics.bm25_count}, dense={metrics.dense_count}, "
                f"fused={metrics.fused_count}, final={metrics.final_count}, "
                f"reranked={metrics.reranked}"
            )

            # Add timing headers
            response.headers["X-Search-Elapsed-Ms"] = str(int(elapsed * 1000))
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Search-Cache-Hit"] = str(metrics.cache_hit).lower()
            response.headers["X-Search-Variants"] = str(metrics.variants_count)
            response.headers["X-Search-Stages"] = ",".join(
                f"{k}={v:.3f}" for k, v in metrics.stages.items()
            )

            return response

        except Exception as exc:
            elapsed = time.time() - start_time
            metrics.error = f"{type(exc).__name__}: {exc}"
            logger.error(
                f"[{request_id}] Search request failed: "
                f"elapsed={elapsed:.3f}s, error={type(exc).__name__}: {exc}"
            )
            raise
        finally:
            clear_search_metrics()
