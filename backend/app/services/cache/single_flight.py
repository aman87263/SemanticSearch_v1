"""Single-flight execution to prevent thundering-herd on identical operations.

Implements the single-flight pattern described in semanticAdditions.md §7 and
§17. When multiple concurrent requests ask for the same embedding or search
result, only one underlying call is made; the rest wait and share the result.

Per-process (Phase 1) implementation using asyncio. A distributed variant
using Redis locks can be added later (Phase 2) when horizontal scaling is
needed.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _key_from_args(func: Callable, *args, **kwargs) -> str:
    """Build a hashable key from function arguments for deduplication."""
    import hashlib
    import json

    bound = getattr(_key_from_args, "_bound_cache", None)
    if bound:
        try:
            bound_args = bound.args
        except Exception:
            bound_args = args
    else:
        bound_args = args

    key_parts = [func.__name__]
    for arg in args:
        key_parts.append(str(arg) if not isinstance(arg, (list, dict)) else json.dumps(arg, default=str))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v if not isinstance(v, (list, dict)) else json.dumps(v, default=str)}")

    raw = "|".join(key_parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class SingleFlight:
    """Per-process single-flight coordinator.

    Usage:
        flight = SingleFlight()

        async def get_embedding(text: str):
            return await flight.execute(
                f"embed:{text}",
                lambda: _call_embedding_api(text)
            )
    """

    def __init__(self):
        self._inflight: dict[str, asyncio.Future] = {}

    async def execute(
        self,
        key: str,
        fn: Callable[[], Awaitable[T]],
    ) -> T:
        """Execute *fn* once per unique *key*.

        Concurrent callers with the same key share a single execution.
        """
        if key in self._inflight:
            future = self._inflight[key]
            return await asyncio.wrap_future(future)

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._inflight[key] = future

        try:
            result = await fn()
            future.set_result(result)
            return result
        except Exception as exc:
            future.set_exception(exc)
            raise
        finally:
            self._inflight.pop(key, None)


_single_flight = SingleFlight()


def get_single_flight() -> SingleFlight:
    return _single_flight
