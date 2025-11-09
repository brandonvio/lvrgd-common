"""Test suite for AsyncRedisService implementation.

This module contains tests for the async Redis service including:
- Connection initialization and configuration
- Common async Redis operations (get, set, delete, expire, etc.)
- Hash operations
- List operations
- Set operations
- Sorted set operations
- Pub/Sub functionality
- Vector search capabilities
- Pipeline operations
- JSON operations
- Pydantic model operations
- Rate limiting
- Caching with get_or_compute
- Error handling
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.redis.async_redis_service import AsyncRedisService
from lvrgd.common.services.redis.redis_models import RedisConfig


class UserModel(BaseModel):
    """Test user model for Pydantic operations."""

    name: str
    age: int


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger for testing."""
    return Mock(spec=LoggingService)


@pytest.fixture
def valid_config() -> RedisConfig:
    """Create a valid Redis configuration for testing."""
    return RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        password="test_password",
        username="test_user",
        socket_connect_timeout=5,
        socket_timeout=5,
        max_connections=50,
    )


@pytest.fixture
def config_without_auth() -> RedisConfig:
    """Create a Redis configuration without authentication."""
    return RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        password=None,
        username=None,
    )


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Create a mock async Redis client."""
    return AsyncMock()


@pytest.fixture
def mock_connection_pool() -> Mock:
    """Create a mock connection pool."""
    return Mock()


@pytest.fixture
def async_redis_service(
    mock_logger: Mock,
    valid_config: RedisConfig,
    mock_redis_client: AsyncMock,
    mock_connection_pool: Mock,
) -> AsyncRedisService:
    """Create an AsyncRedisService instance with mocked dependencies."""
    with (
        patch("lvrgd.common.services.redis.async_redis_service.Redis") as mock_redis,
        patch("lvrgd.common.services.redis.async_redis_service.ConnectionPool") as mock_pool,
    ):
        mock_pool.return_value = mock_connection_pool
        mock_redis.return_value = mock_redis_client
        mock_redis_client.ping = AsyncMock(return_value=True)

        service = AsyncRedisService(mock_logger, valid_config)
        service._client = mock_redis_client
        return service


class TestAsyncRedisServiceInitialization:
    """Test async Redis service initialization."""

    @pytest.mark.asyncio
    async def test_initialization_with_auth(
        self,
        mock_logger: Mock,
        valid_config: RedisConfig,
    ) -> None:
        """Test successful async Redis initialization with authentication."""
        with (
            patch("lvrgd.common.services.redis.async_redis_service.Redis") as mock_redis,
            patch("lvrgd.common.services.redis.async_redis_service.ConnectionPool") as mock_pool,
        ):
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping = AsyncMock(return_value=True)

            _ = AsyncRedisService(mock_logger, valid_config)

            mock_logger.info.assert_any_call(
                "Initializing async Redis connection",
                host=valid_config.host,
                port=valid_config.port,
                db=valid_config.db,
            )
            mock_pool.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_without_auth(
        self,
        mock_logger: Mock,
        config_without_auth: RedisConfig,
    ) -> None:
        """Test successful async Redis initialization without authentication."""
        with (
            patch("lvrgd.common.services.redis.async_redis_service.Redis"),
            patch("lvrgd.common.services.redis.async_redis_service.ConnectionPool"),
        ):
            _ = AsyncRedisService(mock_logger, config_without_auth)

            mock_logger.info.assert_any_call(
                "Initializing async Redis connection",
                host=config_without_auth.host,
                port=config_without_auth.port,
                db=config_without_auth.db,
            )


class TestAsyncRedisBasicOperations:
    """Test basic async Redis operations."""

    @pytest.mark.asyncio
    async def test_ping_success(self, async_redis_service: AsyncRedisService) -> None:
        """Test successful async ping."""
        async_redis_service._client.ping = AsyncMock(return_value=True)
        result = await async_redis_service.ping()
        assert result is True
        async_redis_service._client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_failure(self, async_redis_service: AsyncRedisService) -> None:
        """Test async ping failure."""
        async_redis_service._client.ping = AsyncMock(
            side_effect=RedisConnectionError("Connection lost")
        )
        with pytest.raises(RedisConnectionError):
            await async_redis_service.ping()

    @pytest.mark.asyncio
    async def test_get_existing_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting an existing key."""
        async_redis_service._client.get = AsyncMock(return_value="test_value")
        result = await async_redis_service.get("test_key")
        assert result == "test_value"
        async_redis_service._client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting a non-existent key."""
        async_redis_service._client.get = AsyncMock(return_value=None)
        result = await async_redis_service.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_simple(self, async_redis_service: AsyncRedisService) -> None:
        """Test setting a simple key-value pair."""
        async_redis_service._client.set = AsyncMock(return_value=True)
        result = await async_redis_service.set("key", "value")
        assert result is True
        async_redis_service._client.set.assert_called_once_with(
            "key",
            "value",
            ex=None,
            px=None,
            nx=False,
            xx=False,
        )

    @pytest.mark.asyncio
    async def test_set_with_expiration(self, async_redis_service: AsyncRedisService) -> None:
        """Test setting a key with expiration."""
        async_redis_service._client.set = AsyncMock(return_value=True)
        result = await async_redis_service.set("key", "value", ex=60)
        assert result is True
        async_redis_service._client.set.assert_called_once_with(
            "key",
            "value",
            ex=60,
            px=None,
            nx=False,
            xx=False,
        )

    @pytest.mark.asyncio
    async def test_delete_single_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test deleting a single key."""
        async_redis_service._client.delete = AsyncMock(return_value=1)
        result = await async_redis_service.delete("key")
        assert result == 1
        async_redis_service._client.delete.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_delete_multiple_keys(self, async_redis_service: AsyncRedisService) -> None:
        """Test deleting multiple keys."""
        async_redis_service._client.delete = AsyncMock(return_value=3)
        result = await async_redis_service.delete("key1", "key2", "key3")
        assert result == 3
        async_redis_service._client.delete.assert_called_once_with("key1", "key2", "key3")

    @pytest.mark.asyncio
    async def test_exists_single_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test checking existence of a single key."""
        async_redis_service._client.exists = AsyncMock(return_value=1)
        result = await async_redis_service.exists("key")
        assert result == 1

    @pytest.mark.asyncio
    async def test_exists_multiple_keys(self, async_redis_service: AsyncRedisService) -> None:
        """Test checking existence of multiple keys."""
        async_redis_service._client.exists = AsyncMock(return_value=2)
        result = await async_redis_service.exists("key1", "key2")
        assert result == 2

    @pytest.mark.asyncio
    async def test_expire(self, async_redis_service: AsyncRedisService) -> None:
        """Test setting expiration on a key."""
        async_redis_service._client.expire = AsyncMock(return_value=True)
        result = await async_redis_service.expire("key", 60)
        assert result is True
        async_redis_service._client.expire.assert_called_once_with("key", 60)

    @pytest.mark.asyncio
    async def test_ttl(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting TTL for a key."""
        async_redis_service._client.ttl = AsyncMock(return_value=60)
        result = await async_redis_service.ttl("key")
        assert result == 60
        async_redis_service._client.ttl.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_incr(self, async_redis_service: AsyncRedisService) -> None:
        """Test incrementing a key."""
        async_redis_service._client.incr = AsyncMock(return_value=5)
        result = await async_redis_service.incr("counter", 2)
        assert result == 5
        async_redis_service._client.incr.assert_called_once_with("counter", 2)

    @pytest.mark.asyncio
    async def test_decr(self, async_redis_service: AsyncRedisService) -> None:
        """Test decrementing a key."""
        async_redis_service._client.decr = AsyncMock(return_value=3)
        result = await async_redis_service.decr("counter", 2)
        assert result == 3
        async_redis_service._client.decr.assert_called_once_with("counter", 2)


class TestAsyncRedisHashOperations:
    """Test async Redis hash operations."""

    @pytest.mark.asyncio
    async def test_hget(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting a hash field."""
        async_redis_service._client.hget = AsyncMock(return_value="value")
        result = await async_redis_service.hget("hash", "field")
        assert result == "value"
        async_redis_service._client.hget.assert_called_once_with("hash", "field")

    @pytest.mark.asyncio
    async def test_hset(self, async_redis_service: AsyncRedisService) -> None:
        """Test setting a hash field."""
        async_redis_service._client.hset = AsyncMock(return_value=1)
        result = await async_redis_service.hset("hash", "field", "value")
        assert result == 1
        async_redis_service._client.hset.assert_called_once_with("hash", "field", "value")

    @pytest.mark.asyncio
    async def test_hgetall(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting all hash fields."""
        async_redis_service._client.hgetall = AsyncMock(
            return_value={"field1": "value1", "field2": "value2"}
        )
        result = await async_redis_service.hgetall("hash")
        assert result == {"field1": "value1", "field2": "value2"}
        async_redis_service._client.hgetall.assert_called_once_with("hash")

    @pytest.mark.asyncio
    async def test_hdel(self, async_redis_service: AsyncRedisService) -> None:
        """Test deleting hash fields."""
        async_redis_service._client.hdel = AsyncMock(return_value=2)
        result = await async_redis_service.hdel("hash", "field1", "field2")
        assert result == 2
        async_redis_service._client.hdel.assert_called_once_with("hash", "field1", "field2")


class TestAsyncRedisListOperations:
    """Test async Redis list operations."""

    @pytest.mark.asyncio
    async def test_lpush(self, async_redis_service: AsyncRedisService) -> None:
        """Test pushing to list head."""
        async_redis_service._client.lpush = AsyncMock(return_value=3)
        result = await async_redis_service.lpush("list", "value1", "value2")
        assert result == 3
        async_redis_service._client.lpush.assert_called_once_with("list", "value1", "value2")

    @pytest.mark.asyncio
    async def test_rpush(self, async_redis_service: AsyncRedisService) -> None:
        """Test pushing to list tail."""
        async_redis_service._client.rpush = AsyncMock(return_value=3)
        result = await async_redis_service.rpush("list", "value1", "value2")
        assert result == 3
        async_redis_service._client.rpush.assert_called_once_with("list", "value1", "value2")

    @pytest.mark.asyncio
    async def test_lpop(self, async_redis_service: AsyncRedisService) -> None:
        """Test popping from list head."""
        async_redis_service._client.lpop = AsyncMock(return_value="value")
        result = await async_redis_service.lpop("list")
        assert result == "value"
        async_redis_service._client.lpop.assert_called_once_with("list")

    @pytest.mark.asyncio
    async def test_rpop(self, async_redis_service: AsyncRedisService) -> None:
        """Test popping from list tail."""
        async_redis_service._client.rpop = AsyncMock(return_value="value")
        result = await async_redis_service.rpop("list")
        assert result == "value"
        async_redis_service._client.rpop.assert_called_once_with("list")

    @pytest.mark.asyncio
    async def test_lrange(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting list range."""
        async_redis_service._client.lrange = AsyncMock(return_value=["value1", "value2"])
        result = await async_redis_service.lrange("list", 0, -1)
        assert result == ["value1", "value2"]
        async_redis_service._client.lrange.assert_called_once_with("list", 0, -1)


class TestAsyncRedisSetOperations:
    """Test async Redis set operations."""

    @pytest.mark.asyncio
    async def test_sadd(self, async_redis_service: AsyncRedisService) -> None:
        """Test adding to set."""
        async_redis_service._client.sadd = AsyncMock(return_value=2)
        result = await async_redis_service.sadd("set", "member1", "member2")
        assert result == 2
        async_redis_service._client.sadd.assert_called_once_with("set", "member1", "member2")

    @pytest.mark.asyncio
    async def test_smembers(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting set members."""
        async_redis_service._client.smembers = AsyncMock(return_value={"member1", "member2"})
        result = await async_redis_service.smembers("set")
        assert result == {"member1", "member2"}
        async_redis_service._client.smembers.assert_called_once_with("set")

    @pytest.mark.asyncio
    async def test_srem(self, async_redis_service: AsyncRedisService) -> None:
        """Test removing from set."""
        async_redis_service._client.srem = AsyncMock(return_value=2)
        result = await async_redis_service.srem("set", "member1", "member2")
        assert result == 2
        async_redis_service._client.srem.assert_called_once_with("set", "member1", "member2")


class TestAsyncRedisSortedSetOperations:
    """Test async Redis sorted set operations."""

    @pytest.mark.asyncio
    async def test_zadd(self, async_redis_service: AsyncRedisService) -> None:
        """Test adding to sorted set."""
        async_redis_service._client.zadd = AsyncMock(return_value=2)
        mapping = {"member1": 1.0, "member2": 2.0}
        result = await async_redis_service.zadd("zset", mapping)
        assert result == 2
        async_redis_service._client.zadd.assert_called_once_with(
            "zset", mapping, nx=False, xx=False
        )

    @pytest.mark.asyncio
    async def test_zrange(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting sorted set range."""
        async_redis_service._client.zrange = AsyncMock(return_value=["member1", "member2"])
        result = await async_redis_service.zrange("zset", 0, -1)
        assert result == ["member1", "member2"]
        async_redis_service._client.zrange.assert_called_once_with(
            "zset",
            0,
            -1,
            desc=False,
            withscores=False,
        )

    @pytest.mark.asyncio
    async def test_zrem(self, async_redis_service: AsyncRedisService) -> None:
        """Test removing from sorted set."""
        async_redis_service._client.zrem = AsyncMock(return_value=2)
        result = await async_redis_service.zrem("zset", "member1", "member2")
        assert result == 2
        async_redis_service._client.zrem.assert_called_once_with("zset", "member1", "member2")


class TestAsyncRedisPipeline:
    """Test async Redis pipeline operations."""

    @pytest.mark.asyncio
    async def test_pipeline_context_manager(self, async_redis_service: AsyncRedisService) -> None:
        """Test async pipeline context manager."""
        mock_pipeline = AsyncMock()
        async_redis_service._client.pipeline = Mock(return_value=mock_pipeline)

        async with async_redis_service.pipeline() as pipe:
            assert pipe == mock_pipeline

        async_redis_service._client.pipeline.assert_called_once_with(transaction=True)


class TestAsyncRedisPubSub:
    """Test async Redis pub/sub operations."""

    @pytest.mark.asyncio
    async def test_publish(self, async_redis_service: AsyncRedisService) -> None:
        """Test publishing a message."""
        async_redis_service._client.publish = AsyncMock(return_value=5)
        result = await async_redis_service.publish("channel", "message")
        assert result == 5
        async_redis_service._client.publish.assert_called_once_with("channel", "message")

    @pytest.mark.asyncio
    async def test_subscribe_context_manager(self, async_redis_service: AsyncRedisService) -> None:
        """Test async subscribe context manager."""
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        async_redis_service._client.pubsub = Mock(return_value=mock_pubsub)

        async with async_redis_service.subscribe("channel1", "channel2") as pubsub:
            assert pubsub == mock_pubsub
            mock_pubsub.subscribe.assert_called_once_with("channel1", "channel2")

        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()


class TestAsyncRedisVectorOperations:
    """Test async Redis vector search operations."""

    @pytest.mark.asyncio
    async def test_create_vector_index(self, async_redis_service: AsyncRedisService) -> None:
        """Test creating a vector index."""
        mock_ft = AsyncMock()
        mock_ft.create_index = AsyncMock()
        async_redis_service._client.ft = Mock(return_value=mock_ft)

        await async_redis_service.create_vector_index(
            index_name="idx",
            prefix="doc:",
            vector_field="embedding",
            vector_dims=128,
            text_fields=["title", "content"],
            numeric_fields=["price"],
            tag_fields=["category"],
        )

        async_redis_service._client.ft.assert_called_once_with("idx")
        mock_ft.create_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_vector_index_failure(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test vector index creation failure."""
        mock_ft = AsyncMock()
        mock_ft.create_index = AsyncMock(side_effect=ResponseError("Index already exists"))
        async_redis_service._client.ft = Mock(return_value=mock_ft)

        with pytest.raises(ResponseError):
            await async_redis_service.create_vector_index(
                index_name="idx",
                prefix="doc:",
                vector_field="embedding",
                vector_dims=128,
            )

    @pytest.mark.asyncio
    async def test_vector_search(self, async_redis_service: AsyncRedisService) -> None:
        """Test vector similarity search."""
        mock_ft = AsyncMock()
        mock_results = Mock()
        mock_doc = Mock()
        mock_doc.id = "doc:1"
        mock_doc.score = 0.95
        mock_doc.__dict__ = {"id": "doc:1", "score": 0.95, "title": "Test"}
        mock_results.docs = [mock_doc]
        mock_results.total = 1

        mock_ft.search = AsyncMock(return_value=mock_results)
        async_redis_service._client.ft = Mock(return_value=mock_ft)

        query_vector = [0.1] * 128
        results = await async_redis_service.vector_search("idx", "embedding", query_vector, k=10)

        assert len(results) == 1
        assert results[0]["id"] == "doc:1"
        assert results[0]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_vector_search_failure(self, async_redis_service: AsyncRedisService) -> None:
        """Test vector search failure."""
        mock_ft = AsyncMock()
        mock_ft.search = AsyncMock(side_effect=ResponseError("Index not found"))
        async_redis_service._client.ft = Mock(return_value=mock_ft)

        with pytest.raises(ResponseError):
            await async_redis_service.vector_search("idx", "embedding", [0.1] * 128)

    @pytest.mark.asyncio
    async def test_drop_index(self, async_redis_service: AsyncRedisService) -> None:
        """Test dropping an index."""
        mock_ft = AsyncMock()
        mock_ft.dropindex = AsyncMock()
        async_redis_service._client.ft = Mock(return_value=mock_ft)

        await async_redis_service.drop_index("idx", delete_documents=True)

        async_redis_service._client.ft.assert_called_once_with("idx")
        mock_ft.dropindex.assert_called_once_with(delete_documents=True)

    @pytest.mark.asyncio
    async def test_drop_index_failure(self, async_redis_service: AsyncRedisService) -> None:
        """Test drop index failure."""
        mock_ft = AsyncMock()
        mock_ft.dropindex = AsyncMock(side_effect=ResponseError("Index not found"))
        async_redis_service._client.ft = Mock(return_value=mock_ft)

        with pytest.raises(ResponseError):
            await async_redis_service.drop_index("idx")


class TestAsyncRedisJSONOperations:
    """Test async Redis JSON operations."""

    @pytest.mark.asyncio
    async def test_get_json_existing_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting JSON value for existing key."""
        async_redis_service._client.get = AsyncMock(return_value='{"name": "John", "age": 30}')
        result = await async_redis_service.get_json("user:123")
        assert result == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_get_json_nonexistent_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting JSON value for non-existent key."""
        async_redis_service._client.get = AsyncMock(return_value=None)
        result = await async_redis_service.get_json("user:999")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_json(self, async_redis_service: AsyncRedisService) -> None:
        """Test setting JSON value."""
        async_redis_service._client.set = AsyncMock(return_value=True)
        data = {"name": "John", "age": 30}
        result = await async_redis_service.set_json("user:123", data, ex=3600)
        assert result is True
        async_redis_service._client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_mget_json(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting multiple JSON values."""
        async_redis_service._client.mget = AsyncMock(
            return_value=['{"name": "John"}', '{"name": "Jane"}', None]
        )
        result = await async_redis_service.mget_json("user:1", "user:2", "user:3")
        assert len(result) == 2
        assert result["user:1"] == {"name": "John"}
        assert result["user:2"] == {"name": "Jane"}

    @pytest.mark.asyncio
    async def test_mset_json_without_expiration(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test setting multiple JSON values without expiration."""
        async_redis_service._client.mset = AsyncMock(return_value=True)
        mapping = {"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}
        result = await async_redis_service.mset_json(mapping)
        assert result is True
        async_redis_service._client.mset.assert_called_once()

    @pytest.mark.asyncio
    async def test_mset_json_with_expiration(self, async_redis_service: AsyncRedisService) -> None:
        """Test setting multiple JSON values with expiration."""
        mock_pipeline = AsyncMock()
        mock_pipeline.mset = Mock()
        mock_pipeline.expire = Mock()
        mock_pipeline.execute = AsyncMock()
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)

        async_redis_service.pipeline = Mock(return_value=mock_pipeline)

        mapping = {"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}
        result = await async_redis_service.mset_json(mapping, ex=3600)
        assert result is True


class TestAsyncRedisPydanticOperations:
    """Test async Redis Pydantic model operations."""

    @pytest.mark.asyncio
    async def test_get_model_existing_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting Pydantic model for existing key."""
        async_redis_service._client.get = AsyncMock(return_value='{"name": "John", "age": 30}')
        result = await async_redis_service.get_model("user:123", UserModel)
        assert result is not None
        assert result.name == "John"
        assert result.age == 30

    @pytest.mark.asyncio
    async def test_get_model_nonexistent_key(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting Pydantic model for non-existent key."""
        async_redis_service._client.get = AsyncMock(return_value=None)
        result = await async_redis_service.get_model("user:999", UserModel)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_model(self, async_redis_service: AsyncRedisService) -> None:
        """Test setting Pydantic model."""
        async_redis_service._client.set = AsyncMock(return_value=True)
        user = UserModel(name="John", age=30)
        result = await async_redis_service.set_model("user:123", user, ex=3600)
        assert result is True
        async_redis_service._client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_mget_models(self, async_redis_service: AsyncRedisService) -> None:
        """Test getting multiple Pydantic models."""
        async_redis_service._client.mget = AsyncMock(
            return_value=['{"name": "John", "age": 30}', '{"name": "Jane", "age": 25}', None]
        )
        result = await async_redis_service.mget_models(UserModel, "user:1", "user:2", "user:3")
        assert len(result) == 2
        assert result["user:1"].name == "John"
        assert result["user:2"].name == "Jane"

    @pytest.mark.asyncio
    async def test_mset_models_without_expiration(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test setting multiple Pydantic models without expiration."""
        async_redis_service._client.mset = AsyncMock(return_value=True)
        mapping = {
            "user:1": UserModel(name="John", age=30),
            "user:2": UserModel(name="Jane", age=25),
        }
        result = await async_redis_service.mset_models(mapping)
        assert result is True
        async_redis_service._client.mset.assert_called_once()

    @pytest.mark.asyncio
    async def test_mset_models_with_expiration(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test setting multiple Pydantic models with expiration."""
        mock_pipeline = AsyncMock()
        mock_pipeline.mset = Mock()
        mock_pipeline.expire = Mock()
        mock_pipeline.execute = AsyncMock()
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)

        async_redis_service.pipeline = Mock(return_value=mock_pipeline)

        mapping = {
            "user:1": UserModel(name="John", age=30),
            "user:2": UserModel(name="Jane", age=25),
        }
        result = await async_redis_service.mset_models(mapping, ex=3600)
        assert result is True


class TestAsyncRedisRateLimiting:
    """Test async Redis rate limiting operations."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_sliding_window_allowed(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test sliding window rate limit when allowed."""
        mock_pipeline = AsyncMock()
        mock_pipeline.zremrangebyscore = Mock()
        mock_pipeline.zcard = Mock()
        mock_pipeline.zadd = Mock()
        mock_pipeline.expire = Mock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 5, None, None])
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)

        async_redis_service.pipeline = Mock(return_value=mock_pipeline)

        is_allowed, remaining = await async_redis_service.check_rate_limit(
            "user:123:api", max_requests=10, window_seconds=60, sliding=True
        )
        assert is_allowed is True
        assert remaining == 4

    @pytest.mark.asyncio
    async def test_check_rate_limit_sliding_window_exceeded(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test sliding window rate limit when exceeded."""
        mock_pipeline = AsyncMock()
        mock_pipeline.zremrangebyscore = Mock()
        mock_pipeline.zcard = Mock()
        mock_pipeline.zadd = Mock()
        mock_pipeline.expire = Mock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 10, None, None])
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)

        async_redis_service.pipeline = Mock(return_value=mock_pipeline)

        is_allowed, remaining = await async_redis_service.check_rate_limit(
            "user:123:api", max_requests=10, window_seconds=60, sliding=True
        )
        assert is_allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_fixed_window_allowed(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test fixed window rate limit when allowed."""
        async_redis_service._client.incr = AsyncMock(return_value=5)
        async_redis_service._client.expire = AsyncMock()

        is_allowed, remaining = await async_redis_service.check_rate_limit(
            "user:123:api", max_requests=10, window_seconds=60, sliding=False
        )
        assert is_allowed is True
        assert remaining == 5

    @pytest.mark.asyncio
    async def test_check_rate_limit_fixed_window_exceeded(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test fixed window rate limit when exceeded."""
        async_redis_service._client.incr = AsyncMock(return_value=11)
        async_redis_service._client.expire = AsyncMock()

        is_allowed, remaining = await async_redis_service.check_rate_limit(
            "user:123:api", max_requests=10, window_seconds=60, sliding=False
        )
        assert is_allowed is False
        assert remaining == 0


class TestAsyncRedisGetOrCompute:
    """Test async Redis get_or_compute operations."""

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_hit(self, async_redis_service: AsyncRedisService) -> None:
        """Test get_or_compute with cache hit."""
        async_redis_service.get_json = AsyncMock(return_value={"result": "cached"})

        result = await async_redis_service.get_or_compute(
            "key", lambda: {"result": "computed"}, ex=3600
        )
        assert result == {"result": "cached"}

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_miss(self, async_redis_service: AsyncRedisService) -> None:
        """Test get_or_compute with cache miss."""
        async_redis_service.get_json = AsyncMock(return_value=None)
        async_redis_service.set = AsyncMock(return_value=True)
        async_redis_service.set_json = AsyncMock()
        async_redis_service.delete = AsyncMock()

        result = await async_redis_service.get_or_compute(
            "key", lambda: {"result": "computed"}, ex=3600
        )
        assert result == {"result": "computed"}
        async_redis_service.set_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_compute_without_json_serialization(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test get_or_compute without JSON serialization."""
        async_redis_service.get = AsyncMock(return_value=None)
        async_redis_service.set = AsyncMock(return_value=True)
        async_redis_service.delete = AsyncMock()

        result = await async_redis_service.get_or_compute(
            "key", lambda: "computed_value", ex=3600, serialize_json=False
        )
        assert result == "computed_value"


class TestAsyncRedisServiceClose:
    """Test async Redis service close operation."""

    @pytest.mark.asyncio
    async def test_close_success(self, async_redis_service: AsyncRedisService) -> None:
        """Test successful async close."""
        mock_pool = AsyncMock()
        async_redis_service._pool = mock_pool
        async_redis_service._client.aclose = AsyncMock()
        mock_pool.aclose = AsyncMock()

        await async_redis_service.close()

        async_redis_service._client.aclose.assert_called_once()
        mock_pool.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_failure(self, async_redis_service: AsyncRedisService) -> None:
        """Test async close failure."""
        async_redis_service._client.aclose = AsyncMock(side_effect=RuntimeError("Close failed"))

        with pytest.raises(RuntimeError, match="Close failed"):
            await async_redis_service.close()

        async_redis_service.log.exception.assert_called()
