"""Test suite for Redis service implementation.

This module contains tests for the Redis service including:
- Connection initialization and configuration
- Common Redis operations (get, set, delete, expire, etc.)
- Hash operations
- List operations
- Set operations
- Sorted set operations
- Pub/Sub functionality
- Vector search capabilities
- Pipeline operations
- Error handling
"""

from collections.abc import Iterator
from unittest.mock import Mock, patch

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.redis.redis_models import RedisConfig
from lvrgd.common.services.redis.redis_service import RedisService


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
def mock_redis_client() -> Iterator[Mock]:
    """Create a mock Redis client."""
    with patch("lvrgd.common.services.redis.redis_service.Redis") as mock_client:
        yield mock_client


@pytest.fixture
def mock_connection_pool() -> Iterator[Mock]:
    """Create a mock connection pool."""
    with patch("lvrgd.common.services.redis.redis_service.ConnectionPool") as mock_pool:
        yield mock_pool


@pytest.fixture
def redis_service(
    mock_logger: Mock,
    valid_config: RedisConfig,
    mock_redis_client: Mock,
    mock_connection_pool: Mock,
) -> RedisService:
    """Create a RedisService instance with mocked dependencies."""
    with patch.object(RedisService, "ping") as mock_ping:
        mock_ping.return_value = True
        service = RedisService(mock_logger, valid_config)
        service._client = Mock()
        return service


class TestRedisServiceInitialization:
    """Test Redis service initialization."""

    def test_initialization_with_auth(
        self,
        mock_logger: Mock,
        valid_config: RedisConfig,
        mock_redis_client: Mock,
        mock_connection_pool: Mock,
    ) -> None:
        """Test successful Redis initialization with authentication."""
        with patch.object(RedisService, "ping") as mock_ping:
            mock_ping.return_value = True
            _ = RedisService(mock_logger, valid_config)

            mock_logger.info.assert_any_call(
                "Initializing Redis connection",
                host=valid_config.host,
                port=valid_config.port,
                db=valid_config.db,
            )
            mock_connection_pool.assert_called_once()
            mock_ping.assert_called_once()

    def test_initialization_without_auth(
        self,
        mock_logger: Mock,
        config_without_auth: RedisConfig,
        mock_redis_client: Mock,
        mock_connection_pool: Mock,
    ) -> None:
        """Test successful Redis initialization without authentication."""
        with patch.object(RedisService, "ping") as mock_ping:
            mock_ping.return_value = True
            _ = RedisService(mock_logger, config_without_auth)

            mock_logger.info.assert_any_call(
                "Initializing Redis connection",
                host=config_without_auth.host,
                port=config_without_auth.port,
                db=config_without_auth.db,
            )

    def test_initialization_connection_failure(
        self,
        mock_logger: Mock,
        valid_config: RedisConfig,
        mock_redis_client: Mock,
        mock_connection_pool: Mock,
    ) -> None:
        """Test Redis initialization failure."""
        with patch.object(RedisService, "ping") as mock_ping:
            mock_ping.side_effect = RedisConnectionError("Connection failed")

            with pytest.raises(RedisConnectionError):
                RedisService(mock_logger, valid_config)

            mock_logger.exception.assert_called()


class TestRedisBasicOperations:
    """Test basic Redis operations."""

    def test_ping_success(self, redis_service: RedisService) -> None:
        """Test successful ping."""
        redis_service._client.ping.return_value = True
        result = redis_service.ping()
        assert result is True
        redis_service._client.ping.assert_called_once()

    def test_ping_failure(self, redis_service: RedisService) -> None:
        """Test ping failure."""
        redis_service._client.ping.side_effect = RedisConnectionError("Connection lost")
        with pytest.raises(RedisConnectionError):
            redis_service.ping()

    def test_get_existing_key(self, redis_service: RedisService) -> None:
        """Test getting an existing key."""
        redis_service._client.get.return_value = "test_value"
        result = redis_service.get("test_key")
        assert result == "test_value"
        redis_service._client.get.assert_called_once_with("test_key")

    def test_get_nonexistent_key(self, redis_service: RedisService) -> None:
        """Test getting a non-existent key."""
        redis_service._client.get.return_value = None
        result = redis_service.get("nonexistent")
        assert result is None

    def test_set_simple(self, redis_service: RedisService) -> None:
        """Test setting a simple key-value pair."""
        redis_service._client.set.return_value = True
        result = redis_service.set("key", "value")
        assert result is True
        redis_service._client.set.assert_called_once_with(
            "key",
            "value",
            ex=None,
            px=None,
            nx=False,
            xx=False,
        )

    def test_set_with_expiration(self, redis_service: RedisService) -> None:
        """Test setting a key with expiration."""
        redis_service._client.set.return_value = True
        result = redis_service.set("key", "value", ex=60)
        assert result is True
        redis_service._client.set.assert_called_once_with(
            "key",
            "value",
            ex=60,
            px=None,
            nx=False,
            xx=False,
        )

    def test_delete_single_key(self, redis_service: RedisService) -> None:
        """Test deleting a single key."""
        redis_service._client.delete.return_value = 1
        result = redis_service.delete("key")
        assert result == 1
        redis_service._client.delete.assert_called_once_with("key")

    def test_delete_multiple_keys(self, redis_service: RedisService) -> None:
        """Test deleting multiple keys."""
        redis_service._client.delete.return_value = 3
        result = redis_service.delete("key1", "key2", "key3")
        assert result == 3
        redis_service._client.delete.assert_called_once_with("key1", "key2", "key3")

    def test_exists_single_key(self, redis_service: RedisService) -> None:
        """Test checking existence of a single key."""
        redis_service._client.exists.return_value = 1
        result = redis_service.exists("key")
        assert result == 1

    def test_exists_multiple_keys(self, redis_service: RedisService) -> None:
        """Test checking existence of multiple keys."""
        redis_service._client.exists.return_value = 2
        result = redis_service.exists("key1", "key2")
        assert result == 2

    def test_expire(self, redis_service: RedisService) -> None:
        """Test setting expiration on a key."""
        redis_service._client.expire.return_value = True
        result = redis_service.expire("key", 60)
        assert result is True
        redis_service._client.expire.assert_called_once_with("key", 60)

    def test_ttl(self, redis_service: RedisService) -> None:
        """Test getting TTL for a key."""
        redis_service._client.ttl.return_value = 60
        result = redis_service.ttl("key")
        assert result == 60
        redis_service._client.ttl.assert_called_once_with("key")

    def test_incr(self, redis_service: RedisService) -> None:
        """Test incrementing a key."""
        redis_service._client.incr.return_value = 5
        result = redis_service.incr("counter", 2)
        assert result == 5
        redis_service._client.incr.assert_called_once_with("counter", 2)

    def test_decr(self, redis_service: RedisService) -> None:
        """Test decrementing a key."""
        redis_service._client.decr.return_value = 3
        result = redis_service.decr("counter", 2)
        assert result == 3
        redis_service._client.decr.assert_called_once_with("counter", 2)


class TestRedisHashOperations:
    """Test Redis hash operations."""

    def test_hget(self, redis_service: RedisService) -> None:
        """Test getting a hash field."""
        redis_service._client.hget.return_value = "value"
        result = redis_service.hget("hash", "field")
        assert result == "value"
        redis_service._client.hget.assert_called_once_with("hash", "field")

    def test_hset(self, redis_service: RedisService) -> None:
        """Test setting a hash field."""
        redis_service._client.hset.return_value = 1
        result = redis_service.hset("hash", "field", "value")
        assert result == 1
        redis_service._client.hset.assert_called_once_with("hash", "field", "value")

    def test_hgetall(self, redis_service: RedisService) -> None:
        """Test getting all hash fields."""
        redis_service._client.hgetall.return_value = {"field1": "value1", "field2": "value2"}
        result = redis_service.hgetall("hash")
        assert result == {"field1": "value1", "field2": "value2"}
        redis_service._client.hgetall.assert_called_once_with("hash")

    def test_hdel(self, redis_service: RedisService) -> None:
        """Test deleting hash fields."""
        redis_service._client.hdel.return_value = 2
        result = redis_service.hdel("hash", "field1", "field2")
        assert result == 2
        redis_service._client.hdel.assert_called_once_with("hash", "field1", "field2")


class TestRedisListOperations:
    """Test Redis list operations."""

    def test_lpush(self, redis_service: RedisService) -> None:
        """Test pushing to list head."""
        redis_service._client.lpush.return_value = 3
        result = redis_service.lpush("list", "value1", "value2")
        assert result == 3
        redis_service._client.lpush.assert_called_once_with("list", "value1", "value2")

    def test_rpush(self, redis_service: RedisService) -> None:
        """Test pushing to list tail."""
        redis_service._client.rpush.return_value = 3
        result = redis_service.rpush("list", "value1", "value2")
        assert result == 3
        redis_service._client.rpush.assert_called_once_with("list", "value1", "value2")

    def test_lpop(self, redis_service: RedisService) -> None:
        """Test popping from list head."""
        redis_service._client.lpop.return_value = "value"
        result = redis_service.lpop("list")
        assert result == "value"
        redis_service._client.lpop.assert_called_once_with("list")

    def test_rpop(self, redis_service: RedisService) -> None:
        """Test popping from list tail."""
        redis_service._client.rpop.return_value = "value"
        result = redis_service.rpop("list")
        assert result == "value"
        redis_service._client.rpop.assert_called_once_with("list")

    def test_lrange(self, redis_service: RedisService) -> None:
        """Test getting list range."""
        redis_service._client.lrange.return_value = ["value1", "value2"]
        result = redis_service.lrange("list", 0, -1)
        assert result == ["value1", "value2"]
        redis_service._client.lrange.assert_called_once_with("list", 0, -1)


class TestRedisSetOperations:
    """Test Redis set operations."""

    def test_sadd(self, redis_service: RedisService) -> None:
        """Test adding to set."""
        redis_service._client.sadd.return_value = 2
        result = redis_service.sadd("set", "member1", "member2")
        assert result == 2
        redis_service._client.sadd.assert_called_once_with("set", "member1", "member2")

    def test_smembers(self, redis_service: RedisService) -> None:
        """Test getting set members."""
        redis_service._client.smembers.return_value = {"member1", "member2"}
        result = redis_service.smembers("set")
        assert result == {"member1", "member2"}
        redis_service._client.smembers.assert_called_once_with("set")

    def test_srem(self, redis_service: RedisService) -> None:
        """Test removing from set."""
        redis_service._client.srem.return_value = 2
        result = redis_service.srem("set", "member1", "member2")
        assert result == 2
        redis_service._client.srem.assert_called_once_with("set", "member1", "member2")


class TestRedisSortedSetOperations:
    """Test Redis sorted set operations."""

    def test_zadd(self, redis_service: RedisService) -> None:
        """Test adding to sorted set."""
        redis_service._client.zadd.return_value = 2
        mapping = {"member1": 1.0, "member2": 2.0}
        result = redis_service.zadd("zset", mapping)
        assert result == 2
        redis_service._client.zadd.assert_called_once_with("zset", mapping, nx=False, xx=False)

    def test_zrange(self, redis_service: RedisService) -> None:
        """Test getting sorted set range."""
        redis_service._client.zrange.return_value = ["member1", "member2"]
        result = redis_service.zrange("zset", 0, -1)
        assert result == ["member1", "member2"]
        redis_service._client.zrange.assert_called_once_with(
            "zset",
            0,
            -1,
            desc=False,
            withscores=False,
        )

    def test_zrem(self, redis_service: RedisService) -> None:
        """Test removing from sorted set."""
        redis_service._client.zrem.return_value = 2
        result = redis_service.zrem("zset", "member1", "member2")
        assert result == 2
        redis_service._client.zrem.assert_called_once_with("zset", "member1", "member2")


class TestRedisPipeline:
    """Test Redis pipeline operations."""

    def test_pipeline_context_manager(self, redis_service: RedisService) -> None:
        """Test pipeline context manager."""
        mock_pipeline = Mock()
        redis_service._client.pipeline.return_value = mock_pipeline

        with redis_service.pipeline() as pipe:
            assert pipe == mock_pipeline

        redis_service._client.pipeline.assert_called_once_with(transaction=True)


class TestRedisPubSub:
    """Test Redis pub/sub operations."""

    def test_publish(self, redis_service: RedisService) -> None:
        """Test publishing a message."""
        redis_service._client.publish.return_value = 5
        result = redis_service.publish("channel", "message")
        assert result == 5
        redis_service._client.publish.assert_called_once_with("channel", "message")

    def test_subscribe_context_manager(self, redis_service: RedisService) -> None:
        """Test subscribe context manager."""
        mock_pubsub = Mock()
        redis_service._client.pubsub.return_value = mock_pubsub

        with redis_service.subscribe("channel1", "channel2") as pubsub:
            assert pubsub == mock_pubsub
            mock_pubsub.subscribe.assert_called_once_with("channel1", "channel2")

        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()


class TestRedisVectorOperations:
    """Test Redis vector search operations."""

    def test_create_vector_index(self, redis_service: RedisService) -> None:
        """Test creating a vector index."""
        mock_ft = Mock()
        redis_service._client.ft.return_value = mock_ft

        redis_service.create_vector_index(
            index_name="idx",
            prefix="doc:",
            vector_field="embedding",
            vector_dims=128,
            text_fields=["title", "content"],
            numeric_fields=["price"],
            tag_fields=["category"],
        )

        redis_service._client.ft.assert_called_once_with("idx")
        mock_ft.create_index.assert_called_once()

    def test_create_vector_index_failure(self, redis_service: RedisService) -> None:
        """Test vector index creation failure."""
        mock_ft = Mock()
        redis_service._client.ft.return_value = mock_ft
        mock_ft.create_index.side_effect = ResponseError("Index already exists")

        with pytest.raises(ResponseError):
            redis_service.create_vector_index(
                index_name="idx",
                prefix="doc:",
                vector_field="embedding",
                vector_dims=128,
            )

    def test_vector_search(self, redis_service: RedisService) -> None:
        """Test vector similarity search."""
        mock_ft = Mock()
        mock_results = Mock()
        mock_doc = Mock()
        mock_doc.id = "doc:1"
        mock_doc.score = 0.95
        mock_doc.__dict__ = {"id": "doc:1", "score": 0.95, "title": "Test"}
        mock_results.docs = [mock_doc]
        mock_results.total = 1

        redis_service._client.ft.return_value = mock_ft
        mock_ft.search.return_value = mock_results

        query_vector = [0.1] * 128
        results = redis_service.vector_search("idx", "embedding", query_vector, k=10)

        assert len(results) == 1
        assert results[0]["id"] == "doc:1"
        assert results[0]["score"] == 0.95

    def test_vector_search_failure(self, redis_service: RedisService) -> None:
        """Test vector search failure."""
        mock_ft = Mock()
        redis_service._client.ft.return_value = mock_ft
        mock_ft.search.side_effect = ResponseError("Index not found")

        with pytest.raises(ResponseError):
            redis_service.vector_search("idx", "embedding", [0.1] * 128)

    def test_drop_index(self, redis_service: RedisService) -> None:
        """Test dropping an index."""
        mock_ft = Mock()
        redis_service._client.ft.return_value = mock_ft

        redis_service.drop_index("idx", delete_documents=True)

        redis_service._client.ft.assert_called_once_with("idx")
        mock_ft.dropindex.assert_called_once_with(delete_documents=True)

    def test_drop_index_failure(self, redis_service: RedisService) -> None:
        """Test drop index failure."""
        mock_ft = Mock()
        redis_service._client.ft.return_value = mock_ft
        mock_ft.dropindex.side_effect = ResponseError("Index not found")

        with pytest.raises(ResponseError):
            redis_service.drop_index("idx")


class TestRedisServiceClose:
    """Test Redis service close operation."""

    def test_close_success(self, redis_service: RedisService) -> None:
        """Test successful close."""
        mock_pool = Mock()
        redis_service._pool = mock_pool

        redis_service.close()

        redis_service._client.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()

    def test_close_failure(self, redis_service: RedisService) -> None:
        """Test close failure."""
        redis_service._client.close.side_effect = RuntimeError("Close failed")

        with pytest.raises(RuntimeError, match="Close failed"):
            redis_service.close()

        redis_service.log.exception.assert_called()
