"""Test suite for Redis caching decorator.

This module tests caching decorator functionality:
- Cache hits and misses
- TTL and expiration
- Key generation with various argument types
- Cache invalidation
- Thundering herd prevention
- Graceful degradation
"""

from typing import Any
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


class TestCacheDecorator:
    """Test cache decorator basic functionality."""

    def test_cache_miss_calls_function(self, redis_service: RedisService) -> None:
        """Test cache miss calls the decorated function."""
        redis_service._client.get.return_value = None
        redis_service._client.set.return_value = True
        call_count = 0

        @redis_service.cache(ttl=3600)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result = expensive_function(5)

        assert result == 10
        assert call_count == 1

    def test_cache_hit_skips_function(self, redis_service: RedisService) -> None:
        """Test cache hit returns cached value without calling function."""
        redis_service._client.get.return_value = '{"result": 10}'
        call_count = 0

        @redis_service.cache(ttl=3600)
        def expensive_function(x: int) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"result": x * 2}

        result = expensive_function(5)

        assert result == {"result": 10}
        assert call_count == 0

    def test_cache_stores_result_with_ttl(self, redis_service: RedisService) -> None:
        """Test cache stores result with correct TTL."""
        redis_service._client.get.return_value = None
        redis_service._client.set.return_value = True

        @redis_service.cache(ttl=7200)
        def get_data() -> dict[str, str]:
            return {"status": "ok"}

        get_data()

        redis_service._client.set.assert_called_once()
        call_args = redis_service._client.set.call_args
        assert call_args[1]["ex"] == 7200


class TestKeyGeneration:
    """Test cache key generation with various argument types."""

    def test_key_generation_with_string_args(self, redis_service: RedisService) -> None:
        """Test key generation with string arguments."""
        redis_service._client.get.return_value = None
        redis_service._client.set.return_value = True

        @redis_service.cache(ttl=3600, key_prefix="user")
        def get_user(user_id: str) -> str:
            return f"User {user_id}"

        get_user("123")

        cache_key = redis_service._client.get.call_args[0][0]
        assert "user" in cache_key
        assert "get_user" in cache_key
        assert "123" in cache_key

    def test_key_generation_with_numeric_args(self, redis_service: RedisService) -> None:
        """Test key generation with numeric arguments."""
        redis_service._client.get.return_value = None
        redis_service._client.set.return_value = True

        @redis_service.cache(ttl=3600)
        def calculate(x: int, y: float) -> float:
            return x * y

        calculate(5, 2.5)

        cache_key = redis_service._client.get.call_args[0][0]
        assert "calculate" in cache_key
        assert "5" in cache_key
        assert "2.5" in cache_key

    def test_key_generation_with_namespace(self, redis_service: RedisService) -> None:
        """Test key generation with namespace."""
        redis_service._client.get.return_value = None
        redis_service._client.set.return_value = True

        @redis_service.cache(ttl=3600, namespace="myapp", key_prefix="data")
        def get_data(data_id: str) -> str:
            return f"Data {data_id}"

        get_data("abc")

        cache_key = redis_service._client.get.call_args[0][0]
        assert cache_key.startswith("myapp:")


class TestCacheInvalidation:
    """Test cache invalidation methods."""

    def test_invalidate_specific_args(self, redis_service: RedisService) -> None:
        """Test invalidating cache for specific arguments."""
        redis_service._client.get.return_value = None
        redis_service._client.set.return_value = True
        redis_service._client.delete.return_value = 1

        @redis_service.cache(ttl=3600)
        def get_user(user_id: str) -> str:
            return f"User {user_id}"

        get_user("123")
        deleted = get_user.invalidate("123")  # type: ignore[attr-defined]

        assert deleted == 1
        redis_service._client.delete.assert_called_once()

    def test_invalidate_all(self, redis_service: RedisService) -> None:
        """Test invalidating all cached values for a function."""
        redis_service._client.get.return_value = None
        redis_service._client.set.return_value = True
        redis_service._client.scan_iter.return_value = ["cache:get_user:1", "cache:get_user:2"]
        redis_service._client.delete.return_value = 2

        @redis_service.cache(ttl=3600, key_prefix="cache")
        def get_user(user_id: str) -> str:
            return f"User {user_id}"

        get_user("1")
        get_user("2")
        deleted = get_user.invalidate_all()  # type: ignore[attr-defined]

        assert deleted == 2


class TestThunderingHerd:
    """Test thundering herd prevention."""

    def test_thundering_herd_prevention(self, redis_service: RedisService) -> None:
        """Test lock prevents multiple simultaneous cache fills."""
        redis_service._client.get.return_value = None
        redis_service._client.set.side_effect = [True, True]  # First for lock, second for cache
        call_count = 0

        @redis_service.cache(ttl=3600, prevent_thundering_herd=True)
        def expensive_operation() -> str:
            nonlocal call_count
            call_count += 1
            return "result"

        result = expensive_operation()

        assert result == "result"
        assert call_count == 1
        assert redis_service._client.set.call_count == 2  # Lock + cache


class TestSkipCacheIf:
    """Test skip_cache_if condition."""

    def test_skip_cache_if_condition(self, redis_service: RedisService) -> None:
        """Test skipping cache based on result condition."""
        redis_service._client.get.return_value = None

        @redis_service.cache(ttl=3600, skip_cache_if=lambda x: x is None)
        def maybe_get_data(exists: bool) -> str | None:  # noqa: FBT001
            return "data" if exists else None

        result = maybe_get_data(False)  # noqa: FBT003

        assert result is None
        redis_service._client.set.assert_not_called()


class TestGracefulDegradation:
    """Test graceful degradation when Redis unavailable."""

    def test_graceful_degradation_on_get_error(self, redis_service: RedisService) -> None:
        """Test function still executes when cache get fails."""
        redis_service._client.get.side_effect = Exception("Redis unavailable")
        call_count = 0

        @redis_service.cache(ttl=3600)
        def get_data() -> str:
            nonlocal call_count
            call_count += 1
            return "data"

        result = get_data()

        assert result == "data"
        assert call_count == 1
