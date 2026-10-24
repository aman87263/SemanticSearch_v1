"""Tests for circuit breaker, single-flight, and resilience policy (§6-9, §17)."""

import asyncio
import pytest

from app.services.cache.single_flight import SingleFlight
from app.services.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    ResiliencePolicy,
)


class TestSingleFlight:
    @pytest.mark.asyncio
    async def test_deduplicates_concurrent_calls(self):
        """Concurrent calls with the same key should share one execution."""
        sf = SingleFlight()
        call_count = 0

        async def expensive_op():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return "result"

        # Launch 10 concurrent calls with the same key
        results = await asyncio.gather(
            *[sf.execute("key1", expensive_op) for _ in range(10)]
        )

        assert all(r == "result" for r in results)
        assert call_count == 1  # Only one actual execution

    @pytest.mark.asyncio
    async def test_different_keys_run_independently(self):
        """Different keys should execute independently."""
        sf = SingleFlight()
        call_count = 0

        async def expensive_op():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return "result"

        results = await asyncio.gather(
            sf.execute("key1", expensive_op),
            sf.execute("key2", expensive_op),
        )

        assert all(r == "result" for r in results)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_propagates_exceptions(self):
        """Exceptions should be propagated to all waiting callers."""
        sf = SingleFlight()

        async def failing_op():
            await asyncio.sleep(0.01)
            raise ValueError("fail")

        results = await asyncio.gather(
            sf.execute("key1", failing_op),
            sf.execute("key1", failing_op),
            return_exceptions=True,
        )

        assert all(isinstance(r, ValueError) for r in results)


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_allows_calls_when_closed(self):
        """CLOSED state should allow calls to pass through."""
        cb = CircuitBreaker("test", failure_threshold=3)

        async def success_op():
            return "ok"

        result = await cb.call(success_op)
        assert result == "ok"
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        """Circuit should OPEN after threshold consecutive failures."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout_sec=0.1)

        async def failing_op():
            raise ConnectionError("down")

        # First failure
        with pytest.raises(ConnectionError):
            await cb.call(failing_op)
        assert cb.state == "CLOSED"

        # Second failure -> should trip
        with pytest.raises(ConnectionError):
            await cb.call(failing_op)
        assert cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_opens_circuit_rejects_calls(self):
        """OPEN circuit should reject calls with CircuitBreakerOpen."""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_sec=10)

        async def failing_op():
            raise ConnectionError("down")

        with pytest.raises(ConnectionError):
            await cb.call(failing_op)

        # Circuit is now OPEN
        assert cb.state == "OPEN"

        # Next call should fail-fast
        with pytest.raises(CircuitBreakerOpen):
            await cb.call(failing_op)

    @pytest.mark.asyncio
    async def test_recovers_after_timeout(self):
        """Circuit should go HALF-OPEN after recovery timeout, then CLOSED on success."""
        cb = CircuitBreaker(
            "test", failure_threshold=1, recovery_timeout_sec=0.1,
            half_open_max_calls=1
        )

        async def failing_op():
            raise ConnectionError("down")

        async def success_op():
            return "recovered"

        # Trip the circuit
        with pytest.raises(ConnectionError):
            await cb.call(failing_op)
        assert cb.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should go HALF-OPEN and succeed
        result = await cb.call(success_op)
        assert result == "recovered"
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_half_open_reopens_on_failure(self):
        """HALF-OPEN probe failure should return to OPEN."""
        cb = CircuitBreaker(
            "test", failure_threshold=1, recovery_timeout_sec=0.1,
            half_open_max_calls=1
        )

        async def failing_op():
            raise ConnectionError("down")

        # Trip the circuit
        with pytest.raises(ConnectionError):
            await cb.call(failing_op)

        await asyncio.sleep(0.15)

        # Probe fails -> should reopen
        with pytest.raises(ConnectionError):
            await cb.call(failing_op)
        assert cb.state == "OPEN"


class TestResiliencePolicy:
    @pytest.mark.asyncio
    async def test_timeout_enforced(self):
        """Timeout should be enforced on slow operations."""
        policy = ResiliencePolicy(
            name="test", timeout_sec=0.2, retry_attempts=1
        )

        async def slow_op():
            await asyncio.sleep(1.0)
            return "done"

        with pytest.raises(asyncio.TimeoutError):
            await policy.execute(slow_op)

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """Semaphore should limit concurrent executions."""
        policy = ResiliencePolicy(
            name="test", timeout_sec=5, max_concurrent=2, retry_attempts=1
        )

        in_flight = 0
        max_concurrent_observed = 0

        async def slow_op():
            nonlocal in_flight, max_concurrent_observed
            in_flight += 1
            max_concurrent_observed = max(max_concurrent_observed, in_flight)
            await asyncio.sleep(0.1)
            in_flight -= 1
            return "ok"

        results = await asyncio.gather(
            *[policy.execute(slow_op) for _ in range(10)]
        )

        assert all(r == "ok" for r in results)
        assert max_concurrent_observed <= 2

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Retryable errors should be retried with backoff."""
        policy = ResiliencePolicy(
            name="test", timeout_sec=5, max_concurrent=10,
            retry_attempts=3, retry_base_delay=0.01,
            failure_threshold=10,
        )

        call_count = 0

        async def flaky_op():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timeout")
            return "success"

        result = await policy.execute(flaky_op)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_error_not_retried(self):
        """Non-retryable errors (e.g., 401) should not be retried."""
        policy = ResiliencePolicy(
            name="test", timeout_sec=5, max_concurrent=10,
            retry_attempts=3, retry_base_delay=0.01,
            failure_threshold=10,
        )

        call_count = 0

        async def auth_op():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("HTTP 401: Unauthorized")

        with pytest.raises(RuntimeError, match="401"):
            await policy.execute(auth_op)

        assert call_count == 1  # No retries
