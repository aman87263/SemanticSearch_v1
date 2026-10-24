"""Circuit Breaker for external API calls.

Implements the circuit breaker pattern from semanticAdditions.md §6, §7, §8,
and §9. Protects external providers (embedding, LLM, reranker) from cascading
failures by temporarily stopping requests when a provider is unhealthy.

States:
  CLOSED   -> requests flow normally; failures are counted.
  OPEN     -> requests fail-fast for a cooldown period.
  HALF-OPEN -> a limited number of probe requests are allowed through.

Configuration:
  failure_threshold:     number of consecutive failures to trip the circuit.
  recovery_timeout_sec:  how long to stay OPEN before trying HALF-OPEN.
  half_open_max_calls:   max concurrent probes in HALF-OPEN state.
"""

import logging
import time

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when the circuit is OPEN and the call is rejected fail-fast."""


class CircuitBreaker:
    """A configurable circuit breaker with exponential failure tracking."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_max_calls: int = 2,
    ):
        self._name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_sec
        self._half_open_max = half_open_max_calls

        self._state: str = "CLOSED"
        self._failure_count: int = 0
        self._success_count: int = 0
        self._last_failure_time: float | None = None
        self._half_open_calls: int = 0

    @property
    def state(self) -> str:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def _transition_to_open(self) -> None:
        logger.warning(
            f"CircuitBreaker[{self._name}]: OPENED after "
            f"{self._failure_count} failures"
        )
        self._state = "OPEN"
        self._last_failure_time = time.time()
        self._half_open_calls = 0

    def _transition_to_half_open(self) -> None:
        logger.info(f"CircuitBreaker[{self._name}]: HALF-OPEN — probing")
        self._state = "HALF_OPEN"
        self._half_open_calls = 0

    def _transition_to_closed(self) -> None:
        logger.info(
            f"CircuitBreaker[{self._name}]: CLOSED — "
            f"{self._success_count} successes, resetting counters"
        )
        self._state = "CLOSED"
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

    def _can_attempt(self) -> bool:
        """Check if a request can proceed through the circuit."""
        if self._state == "CLOSED":
            return True

        if self._state == "OPEN":
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self._recovery_timeout:
                    self._transition_to_half_open()
                    return True
            return False

        if self._state == "HALF_OPEN":
            if self._half_open_calls < self._half_open_max:
                self._half_open_calls += 1
                return True
            return False

        return True

    def _on_success(self) -> None:
        """Called when the protected call succeeds."""
        if self._state == "HALF_OPEN":
            self._success_count += 1
            if self._success_count >= self._half_open_max:
                self._transition_to_closed()
        elif self._state == "CLOSED":
            # Reset failure count on any success in CLOSED state
            self._half_open_calls = 0

    def _on_failure(self, exc: Exception) -> None:
        """Called when the protected call fails."""
        self._failure_count += 1

        if self._state == "CLOSED":
            if self._failure_count >= self._failure_threshold:
                self._transition_to_open()
        elif self._state == "HALF_OPEN":
            # Half-open failure → go back to OPEN
            logger.warning(
                f"CircuitBreaker[{self._name}]: HALF-OPEN probe failed, "
                f"reopening"
            )
            self._transition_to_open()

    async def call(self, async_fn, *args, **kwargs):
        """Execute an async function through the circuit breaker.

        Returns the function result on success.
        Raises CircuitBreakerOpen if the circuit is open.
        Re-raises the original exception on failure (after recording it).
        """
        if not self._can_attempt():
            raise CircuitBreakerOpen(
                f"Circuit breaker '{self._name}' is OPEN. "
                f"Requests are not allowed until recovery timeout passes."
            )

        try:
            result = await async_fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            raise


class ResiliencePolicy:
    """Combines timeout, semaphore, circuit breaker, and retry into one wrapper.

    As specified in semanticAdditions.md §6-9:

        Timeout → Semaphore → Retry+jitter → Circuit Breaker → External API
    """

    def __init__(
        self,
        name: str,
        timeout_sec: float = 5.0,
        max_concurrent: int = 10,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_max_calls: int = 2,
    ):
        self._name = name
        self._timeout_sec = timeout_sec
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._circuit_breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout_sec=recovery_timeout_sec,
            half_open_max_calls=half_open_max_calls,
        )
        self._retry_attempts = retry_attempts
        self._retry_base_delay = retry_base_delay

    def _should_retry(self, exc: Exception) -> bool:
        """Decide whether an exception is retryable.

        Per semanticAdditions.md §9:
          Retry: connection failure, timeout, HTTP 429, certain 5xx
          Don't retry: invalid API key, invalid request, malformed input, auth failure
        """
        exc_type = type(exc).__name__

        # Always retry on timeouts
        if isinstance(exc, (asyncio.TimeoutError,)):
            return True

        # Retry on connection errors
        if exc_type in ("ConnectionError", "ClientError", "ServerDisconnectedError"):
            return True

        # Check for HTTP-style error codes in the exception message
        message = str(exc).lower()
        if "429" in message:
            return True
        if "500" in message or "502" in message or "503" in message or "504" in message:
            return True
        if "timeout" in message or "timed out" in message:
            return True
        if "connection" in message and "refused" in message:
            return True

        # Non-retryable: auth failures, invalid requests
        if "401" in message or "403" in message or "unauthorized" in message:
            return False
        if "400" in message or "bad request" in message:
            return False
        if "invalid api key" in message:
            return False

        # Default: don't retry unknown errors
        return False

    async def _retry_with_jitter(
        self,
        async_fn,
        *args,
        **kwargs,
    ):
        """Execute with exponential backoff + jitter retry."""
        import random

        last_exc: Exception | None = None

        for attempt in range(self._retry_attempts):
            try:
                return await async_fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc

                if not self._should_retry(exc) or attempt == self._retry_attempts - 1:
                    raise

                # Exponential backoff with jitter:
                # retry delay = exponential_backoff + random_jitter
                # jitter = random.uniform(0, base_delay * (2 ** attempt))
                base = self._retry_base_delay * (2 ** attempt)
                jitter = random.uniform(0, base * 0.5)
                delay = base + jitter

                logger.warning(
                    f"ResiliencePolicy[{self._name}]: retry "
                    f"attempt={attempt + 1}/{self._retry_attempts}, "
                    f"delay={delay:.3f}s, error={type(exc).__name__}: {exc}"
                )

                await asyncio.sleep(delay)

        if last_exc:
            raise last_exc

    async def execute(self, async_fn, *args, **kwargs):
        """Execute an async function through the full resilience stack.

        Pipeline (semanticAdditions.md §6, §8, §9):
          1. Timeout
          2. Semaphore (concurrency limit)
          3. Retry + jitter (retryable errors only)
          4. Circuit breaker
        """
        async with self._semaphore:

            async def _wrapped():
                return await self._retry_with_jitter(async_fn, *args, **kwargs)

            # The timeout wraps the retry + circuit breaker
            try:
                async with asyncio.timeout(self._timeout_sec):
                    return await self._circuit_breaker.call(_wrapped)
            except asyncio.TimeoutError:
                logger.warning(
                    f"ResiliencePolicy[{self._name}]: timeout after "
                    f"{self._timeout_sec}s on attempt"
                )
                raise


import asyncio
