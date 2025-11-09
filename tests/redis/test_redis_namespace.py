"""Test suite for Redis namespace support.

This module tests namespace functionality:
- Namespace prefix application
- Operations with and without namespace
- Backward compatibility
"""

import json
from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from lvrgd.common.services import LoggingService
from lvrgd.common.services.redis.redis_models import RedisConfig
from lvrgd.common.services.redis.redis_service import RedisService


class UserModel(BaseModel):
    """Test user model."""

    name: str
    age: int


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger for testing."""
    return Mock(spec=LoggingService)


@pytest.fixture
def redis_config_with_namespace() -> RedisConfig:
    """Create a Redis configuration with namespace."""
    return RedisConfig(host="localhost", port=6379, db=0, namespace="myapp")


@pytest.fixture
def redis_config_without_namespace() -> RedisConfig:
    """Create a Redis configuration without namespace."""
    return RedisConfig(host="localhost", port=6379, db=0)


@pytest.fixture
def redis_service_with_namespace(
    mock_logger: Mock, redis_config_with_namespace: RedisConfig
) -> RedisService:
    """Create a RedisService instance with namespace."""
    service = RedisService.__new__(RedisService)
    service.log = mock_logger
    service.config = redis_config_with_namespace
    service._client = Mock()
    return service


@pytest.fixture
def redis_service_without_namespace(
    mock_logger: Mock, redis_config_without_namespace: RedisConfig
) -> RedisService:
    """Create a RedisService instance without namespace."""
    service = RedisService.__new__(RedisService)
    service.log = mock_logger
    service.config = redis_config_without_namespace
    service._client = Mock()
    return service


class TestNamespaceApplication:
    """Test namespace prefix application."""

    def test_namespace_applied_to_get(self, redis_service_with_namespace: RedisService) -> None:
        """Test namespace is applied to get operations."""
        redis_service_with_namespace._client.get.return_value = "value"

        redis_service_with_namespace.get("test_key")

        redis_service_with_namespace._client.get.assert_called_once_with("myapp:test_key")

    def test_namespace_applied_to_set(self, redis_service_with_namespace: RedisService) -> None:
        """Test namespace is applied to set operations."""
        redis_service_with_namespace._client.set.return_value = True

        redis_service_with_namespace.set("test_key", "value")

        call_args = redis_service_with_namespace._client.set.call_args
        assert call_args[0][0] == "myapp:test_key"

    def test_namespace_applied_to_delete(self, redis_service_with_namespace: RedisService) -> None:
        """Test namespace is applied to delete operations."""
        redis_service_with_namespace._client.delete.return_value = 1

        redis_service_with_namespace.delete("key1", "key2")

        redis_service_with_namespace._client.delete.assert_called_once_with(
            "myapp:key1", "myapp:key2"
        )

    def test_namespace_applied_to_exists(self, redis_service_with_namespace: RedisService) -> None:
        """Test namespace is applied to exists operations."""
        redis_service_with_namespace._client.exists.return_value = 2

        redis_service_with_namespace.exists("key1", "key2")

        redis_service_with_namespace._client.exists.assert_called_once_with(
            "myapp:key1", "myapp:key2"
        )


class TestBackwardCompatibility:
    """Test backward compatibility without namespace."""

    def test_no_namespace_uses_original_key_get(
        self, redis_service_without_namespace: RedisService
    ) -> None:
        """Test operations without namespace use original keys."""
        redis_service_without_namespace._client.get.return_value = "value"

        redis_service_without_namespace.get("test_key")

        redis_service_without_namespace._client.get.assert_called_once_with("test_key")

    def test_no_namespace_uses_original_key_set(
        self, redis_service_without_namespace: RedisService
    ) -> None:
        """Test set without namespace uses original key."""
        redis_service_without_namespace._client.set.return_value = True

        redis_service_without_namespace.set("test_key", "value")

        call_args = redis_service_without_namespace._client.set.call_args
        assert call_args[0][0] == "test_key"


class TestNamespaceWithJsonOperations:
    """Test namespace with JSON operations."""

    def test_namespace_applied_to_get_json(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to get_json."""
        redis_service_with_namespace._client.get.return_value = '{"name": "John"}'

        redis_service_with_namespace.get_json("user:123")

        redis_service_with_namespace._client.get.assert_called_once_with("myapp:user:123")

    def test_namespace_applied_to_set_json(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to set_json."""
        redis_service_with_namespace._client.set.return_value = True

        redis_service_with_namespace.set_json("user:123", {"name": "John"})

        call_args = redis_service_with_namespace._client.set.call_args
        assert call_args[0][0] == "myapp:user:123"

    def test_namespace_applied_to_mget_json(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to mget_json."""
        redis_service_with_namespace._client.mget.return_value = ['{"a": 1}', '{"b": 2}']

        redis_service_with_namespace.mget_json("key1", "key2")

        redis_service_with_namespace._client.mget.assert_called_once_with(
            "myapp:key1", "myapp:key2"
        )

    def test_namespace_applied_to_mset_json(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to mset_json."""
        redis_service_with_namespace._client.mset.return_value = True

        redis_service_with_namespace.mset_json({"key1": {"a": 1}, "key2": {"b": 2}})

        call_args = redis_service_with_namespace._client.mset.call_args
        mapping = call_args[0][0]
        assert "myapp:key1" in mapping
        assert "myapp:key2" in mapping


class TestNamespaceHelperMethod:
    """Test _apply_namespace helper method."""

    def test_apply_namespace_with_namespace_configured(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test _apply_namespace adds namespace prefix."""
        result = redis_service_with_namespace._apply_namespace("test_key")
        assert result == "myapp:test_key"

    def test_apply_namespace_without_namespace_configured(
        self, redis_service_without_namespace: RedisService
    ) -> None:
        """Test _apply_namespace returns original key when no namespace."""
        result = redis_service_without_namespace._apply_namespace("test_key")
        assert result == "test_key"

    def test_apply_namespace_with_empty_key(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test _apply_namespace handles empty key."""
        result = redis_service_with_namespace._apply_namespace("")
        assert result == "myapp:"


class TestNamespaceWithModelOperations:
    """Test namespace with Pydantic model operations."""

    def test_namespace_applied_to_get_model(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to get_model."""
        user_data = {"name": "John", "age": 30}
        redis_service_with_namespace._client.get.return_value = json.dumps(user_data)

        result = redis_service_with_namespace.get_model("user:123", UserModel)

        redis_service_with_namespace._client.get.assert_called_once_with("myapp:user:123")
        assert result is not None
        assert result.name == "John"
        assert result.age == 30

    def test_namespace_applied_to_set_model(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to set_model."""
        redis_service_with_namespace._client.set.return_value = True
        user = UserModel(name="Jane", age=25)

        redis_service_with_namespace.set_model("user:456", user)

        call_args = redis_service_with_namespace._client.set.call_args
        assert call_args[0][0] == "myapp:user:456"
        assert '"name":"Jane"' in call_args[0][1]
        assert '"age":25' in call_args[0][1]

    def test_namespace_applied_to_mget_models(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to mget_models."""
        user1_data = json.dumps({"name": "John", "age": 30})
        user2_data = json.dumps({"name": "Jane", "age": 25})
        redis_service_with_namespace._client.mget.return_value = [user1_data, user2_data]

        result = redis_service_with_namespace.mget_models(UserModel, "user:1", "user:2")

        redis_service_with_namespace._client.mget.assert_called_once_with(
            "myapp:user:1", "myapp:user:2"
        )
        assert len(result) == 2
        assert "user:1" in result
        assert "user:2" in result

    def test_namespace_applied_to_mset_models(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to mset_models."""
        redis_service_with_namespace._client.mset.return_value = True
        users = {
            "user:1": UserModel(name="John", age=30),
            "user:2": UserModel(name="Jane", age=25),
        }

        redis_service_with_namespace.mset_models(users)

        call_args = redis_service_with_namespace._client.mset.call_args
        mapping = call_args[0][0]
        assert "myapp:user:1" in mapping
        assert "myapp:user:2" in mapping

    def test_namespace_applied_to_mset_models_with_expiration(
        self, redis_service_with_namespace: RedisService
    ) -> None:
        """Test namespace is applied to mset_models with expiration."""
        mock_pipe = Mock()
        mock_pipe.execute.return_value = None
        redis_service_with_namespace._client.pipeline = Mock(return_value=mock_pipe)

        users = {
            "user:1": UserModel(name="John", age=30),
            "user:2": UserModel(name="Jane", age=25),
        }

        redis_service_with_namespace.mset_models(users, ex=3600)

        # Verify mset was called with namespaced keys
        mset_call = mock_pipe.mset.call_args
        mapping = mset_call[0][0]
        assert "myapp:user:1" in mapping
        assert "myapp:user:2" in mapping

        # Verify expire was called with namespaced keys
        expire_calls = mock_pipe.expire.call_args_list
        assert len(expire_calls) == 2
        expired_keys = {call[0][0] for call in expire_calls}
        assert "myapp:user:1" in expired_keys
        assert "myapp:user:2" in expired_keys
