"""Test suite for Redis JSON operations.

This module tests JSON serialization and batch operations:
- get_json, set_json
- mget_json, mset_json
- hget_json, hset_json, hgetall_json
"""

import json
from unittest.mock import Mock

import pytest

from lvrgd.common.services import LoggingService
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


class TestGetJson:
    """Test get_json method."""

    def test_get_json_dict(self, redis_service: RedisService) -> None:
        """Test getting JSON dict value."""
        test_data = {"name": "John", "age": 30}
        redis_service._client.get.return_value = json.dumps(test_data)

        result = redis_service.get_json("user:123")

        assert result == test_data
        redis_service._client.get.assert_called_once_with("user:123")

    def test_get_json_list(self, redis_service: RedisService) -> None:
        """Test getting JSON list value."""
        test_data = [1, 2, 3, 4, 5]
        redis_service._client.get.return_value = json.dumps(test_data)

        result = redis_service.get_json("numbers")

        assert result == test_data

    def test_get_json_missing_key(self, redis_service: RedisService) -> None:
        """Test getting non-existent key returns None."""
        redis_service._client.get.return_value = None

        result = redis_service.get_json("missing")

        assert result is None

    def test_get_json_invalid_json(self, redis_service: RedisService) -> None:
        """Test getting invalid JSON raises JSONDecodeError."""
        redis_service._client.get.return_value = "not valid json{"

        with pytest.raises(json.JSONDecodeError):
            redis_service.get_json("bad_key")


class TestSetJson:
    """Test set_json method."""

    def test_set_json_dict(self, redis_service: RedisService) -> None:
        """Test setting JSON dict value."""
        test_data = {"name": "John", "age": 30}
        redis_service._client.set.return_value = True

        result = redis_service.set_json("user:123", test_data)

        assert result is True
        redis_service._client.set.assert_called_once_with(
            "user:123", json.dumps(test_data), ex=None, nx=False, xx=False
        )

    def test_set_json_with_expiration(self, redis_service: RedisService) -> None:
        """Test setting JSON value with expiration."""
        test_data = {"key": "value"}
        redis_service._client.set.return_value = True

        result = redis_service.set_json("test", test_data, ex=3600)

        assert result is True
        redis_service._client.set.assert_called_once_with(
            "test", json.dumps(test_data), ex=3600, nx=False, xx=False
        )

    def test_set_json_with_nx_flag(self, redis_service: RedisService) -> None:
        """Test setting JSON value with nx flag."""
        test_data = [1, 2, 3]
        redis_service._client.set.return_value = True

        result = redis_service.set_json("list", test_data, nx=True)

        assert result is True
        redis_service._client.set.assert_called_once_with(
            "list", json.dumps(test_data), ex=None, nx=True, xx=False
        )


class TestMgetJson:
    """Test mget_json method."""

    def test_mget_json_multiple_keys(self, redis_service: RedisService) -> None:
        """Test getting multiple JSON values."""
        data1 = {"name": "John"}
        data2 = {"name": "Jane"}
        redis_service._client.mget.return_value = [json.dumps(data1), json.dumps(data2), None]

        result = redis_service.mget_json("user:1", "user:2", "user:3")

        assert result == {"user:1": data1, "user:2": data2}
        redis_service._client.mget.assert_called_once_with("user:1", "user:2", "user:3")

    def test_mget_json_with_invalid_json(self, redis_service: RedisService) -> None:
        """Test mget_json skips invalid JSON entries."""
        data1 = {"name": "John"}
        redis_service._client.mget.return_value = [json.dumps(data1), "invalid json", None]

        result = redis_service.mget_json("user:1", "user:2", "user:3")

        assert result == {"user:1": data1}


class TestMsetJson:
    """Test mset_json method."""

    def test_mset_json_without_expiration(self, redis_service: RedisService) -> None:
        """Test setting multiple JSON values without expiration."""
        mapping = {"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}
        redis_service._client.mset.return_value = True

        result = redis_service.mset_json(mapping)

        assert result is True
        expected_mapping = {k: json.dumps(v) for k, v in mapping.items()}
        redis_service._client.mset.assert_called_once_with(expected_mapping)

    def test_mset_json_with_expiration(self, redis_service: RedisService) -> None:
        """Test setting multiple JSON values with expiration."""
        mapping = {"key1": {"data": "value1"}, "key2": {"data": "value2"}}
        mock_pipe = Mock()
        mock_pipe.execute.return_value = None
        redis_service._client.pipeline = Mock(return_value=mock_pipe)

        result = redis_service.mset_json(mapping, ex=3600)

        assert result is True
        mock_pipe.mset.assert_called_once()
        assert mock_pipe.expire.call_count == 2


class TestHashJsonOperations:
    """Test hash JSON operations."""

    def test_hget_json(self, redis_service: RedisService) -> None:
        """Test getting JSON value from hash field."""
        test_data = {"name": "John", "age": 30}
        redis_service._client.hget.return_value = json.dumps(test_data)

        result = redis_service.hget_json("users", "user:123")

        assert result == test_data
        redis_service._client.hget.assert_called_once_with("users", "user:123")

    def test_hget_json_missing_field(self, redis_service: RedisService) -> None:
        """Test getting missing hash field returns None."""
        redis_service._client.hget.return_value = None

        result = redis_service.hget_json("users", "missing")

        assert result is None

    def test_hset_json(self, redis_service: RedisService) -> None:
        """Test setting JSON value in hash field."""
        test_data = {"name": "John", "age": 30}
        redis_service._client.hset.return_value = 1

        result = redis_service.hset_json("users", "user:123", test_data)

        assert result == 1
        redis_service._client.hset.assert_called_once_with(
            "users", "user:123", json.dumps(test_data)
        )

    def test_hgetall_json(self, redis_service: RedisService) -> None:
        """Test getting all JSON hash fields."""
        data1 = {"name": "John"}
        data2 = {"name": "Jane"}
        redis_service._client.hgetall.return_value = {
            "user:1": json.dumps(data1),
            "user:2": json.dumps(data2),
        }

        result = redis_service.hgetall_json("users")

        assert result == {"user:1": data1, "user:2": data2}

    def test_hgetall_json_with_invalid_json(self, redis_service: RedisService) -> None:
        """Test hgetall_json skips invalid JSON entries."""
        data1 = {"name": "John"}
        redis_service._client.hgetall.return_value = {
            "user:1": json.dumps(data1),
            "user:2": "invalid json",
        }

        result = redis_service.hgetall_json("users")

        assert result == {"user:1": data1}
