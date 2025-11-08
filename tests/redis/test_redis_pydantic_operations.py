"""Test suite for Redis Pydantic model operations.

This module tests Pydantic model integration:
- get_model, set_model
- mget_models, mset_models
- hget_model, hset_model
"""

import json
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, ValidationError

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.redis.redis_models import RedisConfig
from lvrgd.common.services.redis.redis_service import RedisService


class UserModel(BaseModel):
    """Test user model."""

    name: str
    age: int
    email: str | None = None


class ProductModel(BaseModel):
    """Test product model."""

    id: str
    price: float
    in_stock: bool


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


class TestGetModel:
    """Test get_model method."""

    def test_get_model_success(self, redis_service: RedisService) -> None:
        """Test getting and validating a Pydantic model."""
        user_data = {"name": "John", "age": 30, "email": "john@example.com"}
        redis_service._client.get.return_value = json.dumps(user_data)

        result = redis_service.get_model("user:123", UserModel)

        assert isinstance(result, UserModel)
        assert result.name == "John"
        assert result.age == 30
        assert result.email == "john@example.com"
        redis_service._client.get.assert_called_once_with("user:123")

    def test_get_model_missing_key(self, redis_service: RedisService) -> None:
        """Test getting missing key returns None."""
        redis_service._client.get.return_value = None

        result = redis_service.get_model("missing", UserModel)

        assert result is None

    def test_get_model_validation_error(self, redis_service: RedisService) -> None:
        """Test validation error fails fast."""
        invalid_data = {"name": "John", "age": "not_an_int"}
        redis_service._client.get.return_value = json.dumps(invalid_data)

        with pytest.raises(ValidationError):
            redis_service.get_model("user:123", UserModel)


class TestSetModel:
    """Test set_model method."""

    def test_set_model_success(self, redis_service: RedisService) -> None:
        """Test setting a Pydantic model."""
        user = UserModel(name="John", age=30, email="john@example.com")
        redis_service._client.set.return_value = True

        result = redis_service.set_model("user:123", user)

        assert result is True
        redis_service._client.set.assert_called_once()
        call_args = redis_service._client.set.call_args
        assert call_args[0][0] == "user:123"
        assert json.loads(call_args[0][1]) == {
            "name": "John",
            "age": 30,
            "email": "john@example.com",
        }

    def test_set_model_with_expiration(self, redis_service: RedisService) -> None:
        """Test setting model with expiration."""
        user = UserModel(name="Jane", age=25)
        redis_service._client.set.return_value = True

        result = redis_service.set_model("user:456", user, ex=3600)

        assert result is True
        call_args = redis_service._client.set.call_args
        assert call_args[1]["ex"] == 3600


class TestMgetModels:
    """Test mget_models method."""

    def test_mget_models_success(self, redis_service: RedisService) -> None:
        """Test getting multiple models."""
        user1_data = {"name": "John", "age": 30}
        user2_data = {"name": "Jane", "age": 25}
        redis_service._client.mget.return_value = [
            json.dumps(user1_data),
            json.dumps(user2_data),
            None,
        ]

        result = redis_service.mget_models(UserModel, "user:1", "user:2", "user:3")

        assert len(result) == 2
        assert isinstance(result["user:1"], UserModel)
        assert result["user:1"].name == "John"
        assert isinstance(result["user:2"], UserModel)
        assert result["user:2"].name == "Jane"

    def test_mget_models_with_invalid_data(self, redis_service: RedisService) -> None:
        """Test mget_models skips invalid model data."""
        user1_data = {"name": "John", "age": 30}
        invalid_data = {"name": "Bad", "age": "not_int"}
        redis_service._client.mget.return_value = [
            json.dumps(user1_data),
            json.dumps(invalid_data),
        ]

        result = redis_service.mget_models(UserModel, "user:1", "user:2")

        assert len(result) == 1
        assert "user:1" in result
        assert "user:2" not in result


class TestMsetModels:
    """Test mset_models method."""

    def test_mset_models_without_expiration(self, redis_service: RedisService) -> None:
        """Test setting multiple models without expiration."""
        user1 = UserModel(name="John", age=30)
        user2 = UserModel(name="Jane", age=25)
        mapping = {"user:1": user1, "user:2": user2}
        redis_service._client.mset.return_value = True

        result = redis_service.mset_models(mapping)

        assert result is True
        redis_service._client.mset.assert_called_once()

    def test_mset_models_with_expiration(self, redis_service: RedisService) -> None:
        """Test setting multiple models with expiration."""
        user1 = UserModel(name="John", age=30)
        user2 = UserModel(name="Jane", age=25)
        mapping = {"user:1": user1, "user:2": user2}
        mock_pipe = Mock()
        mock_pipe.execute.return_value = None
        redis_service._client.pipeline = Mock(return_value=mock_pipe)

        result = redis_service.mset_models(mapping, ex=3600)

        assert result is True
        mock_pipe.mset.assert_called_once()
        assert mock_pipe.expire.call_count == 2


class TestHashModelOperations:
    """Test hash Pydantic model operations."""

    def test_hget_model_success(self, redis_service: RedisService) -> None:
        """Test getting model from hash field."""
        user_data = {"name": "John", "age": 30}
        redis_service._client.hget.return_value = json.dumps(user_data)

        result = redis_service.hget_model("users", "user:123", UserModel)

        assert isinstance(result, UserModel)
        assert result.name == "John"
        assert result.age == 30

    def test_hget_model_missing_field(self, redis_service: RedisService) -> None:
        """Test getting missing hash field returns None."""
        redis_service._client.hget.return_value = None

        result = redis_service.hget_model("users", "missing", UserModel)

        assert result is None

    def test_hget_model_validation_error(self, redis_service: RedisService) -> None:
        """Test validation error fails fast."""
        invalid_data = {"name": "John", "age": "not_int"}
        redis_service._client.hget.return_value = json.dumps(invalid_data)

        with pytest.raises(ValidationError):
            redis_service.hget_model("users", "user:123", UserModel)

    def test_hset_model_success(self, redis_service: RedisService) -> None:
        """Test setting model in hash field."""
        user = UserModel(name="John", age=30)
        redis_service._client.hset.return_value = 1

        result = redis_service.hset_model("users", "user:123", user)

        assert result == 1
        redis_service._client.hset.assert_called_once()
        call_args = redis_service._client.hset.call_args
        assert call_args[0][0] == "users"
        assert call_args[0][1] == "user:123"
