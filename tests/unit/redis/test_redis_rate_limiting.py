"""Test suite for Redis rate limiting primitives.

This module tests rate limiting functionality:
- Sliding window rate limiting
- Fixed window rate limiting
- Rate limit checking
- Remaining request calculations
"""

from unittest.mock import Mock

import pytest

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.redis.redis_models import RedisConfig
from lvrgd.common.services.redis.redis_service import RedisService


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger for testing."""
    return Mock(spec=LoggingService)


@pytest.fixture
def redis_config() -> RedisConfig:
    """Create a Redis configuration for testing."""
    return RedisConfig(host="localhost", port=6379, db=0)


@pytest.fixture
def redis_service(mock_logger: Mock, redis_config: RedisConfig) -> RedisService:
    """Create a RedisService instance with mocked client."""
    service = RedisService.__new__(RedisService)
    service.log = mock_logger
    service.config = redis_config
    service._client = Mock()
    return service


class TestSlidingWindowRateLimit:
    """Test sliding window rate limiting."""

    def test_sliding_window_allows_under_limit(self, redis_service: RedisService) -> None:
        """Test sliding window allows requests under limit."""
        mock_pipe = Mock()
        mock_pipe.execute.return_value = [0, 5, 1, True]  # removed, count, zadd, expire
        redis_service._client.pipeline = Mock(return_value=mock_pipe)

        is_allowed, remaining = redis_service.check_rate_limit(
            "user:123", max_requests=10, window_seconds=60, sliding=True
        )

        assert is_allowed is True
        assert remaining == 4

    def test_sliding_window_blocks_over_limit(self, redis_service: RedisService) -> None:
        """Test sliding window blocks requests over limit."""
        mock_pipe = Mock()
        mock_pipe.execute.return_value = [0, 10, 1, True]  # removed, count, zadd, expire
        redis_service._client.pipeline = Mock(return_value=mock_pipe)

        is_allowed, remaining = redis_service.check_rate_limit(
            "user:123", max_requests=10, window_seconds=60, sliding=True
        )

        assert is_allowed is False
        assert remaining == 0

    def test_sliding_window_uses_sorted_set(self, redis_service: RedisService) -> None:
        """Test sliding window uses sorted set operations."""
        mock_pipe = Mock()
        mock_pipe.execute.return_value = [0, 3, 1, True]
        redis_service._client.pipeline = Mock(return_value=mock_pipe)

        redis_service.check_rate_limit("user:123", max_requests=10, window_seconds=60, sliding=True)

        # Verify sorted set operations were called
        mock_pipe.zremrangebyscore.assert_called_once()
        mock_pipe.zcard.assert_called_once()
        mock_pipe.zadd.assert_called_once()
        mock_pipe.expire.assert_called_once()


class TestFixedWindowRateLimit:
    """Test fixed window rate limiting."""

    def test_fixed_window_allows_under_limit(self, redis_service: RedisService) -> None:
        """Test fixed window allows requests under limit."""
        redis_service._client.incr.return_value = 5

        is_allowed, remaining = redis_service.check_rate_limit(
            "user:456", max_requests=10, window_seconds=60, sliding=False
        )

        assert is_allowed is True
        assert remaining == 5

    def test_fixed_window_blocks_over_limit(self, redis_service: RedisService) -> None:
        """Test fixed window blocks requests over limit."""
        redis_service._client.incr.return_value = 11

        is_allowed, remaining = redis_service.check_rate_limit(
            "user:456", max_requests=10, window_seconds=60, sliding=False
        )

        assert is_allowed is False
        assert remaining == 0

    def test_fixed_window_sets_expiration_on_first_request(
        self, redis_service: RedisService
    ) -> None:
        """Test fixed window sets expiration on first request."""
        redis_service._client.incr.return_value = 1
        redis_service._client.expire.return_value = True

        redis_service.check_rate_limit(
            "user:789", max_requests=10, window_seconds=60, sliding=False
        )

        redis_service._client.expire.assert_called_once_with("user:789", 60)

    def test_fixed_window_no_expiration_on_subsequent_requests(
        self, redis_service: RedisService
    ) -> None:
        """Test fixed window doesn't set expiration on subsequent requests."""
        redis_service._client.incr.return_value = 5

        redis_service.check_rate_limit(
            "user:789", max_requests=10, window_seconds=60, sliding=False
        )

        redis_service._client.expire.assert_not_called()


class TestRateLimitRemainingCalculation:
    """Test remaining request calculations."""

    def test_remaining_never_negative_sliding(self, redis_service: RedisService) -> None:
        """Test remaining count never goes negative in sliding window."""
        mock_pipe = Mock()
        mock_pipe.execute.return_value = [0, 15, 1, True]  # Over limit
        redis_service._client.pipeline = Mock(return_value=mock_pipe)

        _, remaining = redis_service.check_rate_limit(
            "user:123", max_requests=10, window_seconds=60, sliding=True
        )

        assert remaining >= 0

    def test_remaining_never_negative_fixed(self, redis_service: RedisService) -> None:
        """Test remaining count never goes negative in fixed window."""
        redis_service._client.incr.return_value = 15  # Over limit

        _, remaining = redis_service.check_rate_limit(
            "user:456", max_requests=10, window_seconds=60, sliding=False
        )

        assert remaining >= 0


class TestRateLimitKeyNamespacing:
    """Test rate limit key namespacing."""

    def test_rate_limit_uses_provided_key(self, redis_service: RedisService) -> None:
        """Test rate limiting uses provided key for namespacing."""
        redis_service._client.incr.return_value = 1
        redis_service._client.expire.return_value = True

        redis_service.check_rate_limit(
            "api:user:123:requests", max_requests=100, window_seconds=3600, sliding=False
        )

        redis_service._client.incr.assert_called_once_with("api:user:123:requests", 1)
