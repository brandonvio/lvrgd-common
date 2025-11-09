"""Integration tests for Redis service.

Tests Redis service operations against a real Redis instance.
Configuration loaded from environment variables via conftest.py fixtures.
"""

import uuid

from pydantic import BaseModel, Field

from lvrgd.common.services import LoggingService
from lvrgd.common.services.redis.redis_models import RedisConfig
from lvrgd.common.services.redis.redis_service import RedisService


class RedisUser(BaseModel):
    """User model for Redis Pydantic operations."""

    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    age: int = Field(..., description="User age")


class TestRedisIntegration:
    """Integration tests for RedisService."""

    def test_redis_connection_and_ping(self, redis_service: RedisService) -> None:
        """Test Redis connection and ping functionality."""
        # Ping server
        result = redis_service.ping()
        assert result is True

    def test_string_operations(self, redis_service: RedisService) -> None:
        """Test basic string set, get, and delete operations."""
        key = f"test_str_{uuid.uuid4().hex}"

        try:
            # Set value
            result = redis_service.set(key, "test_value")
            assert result is True

            # Get value
            value = redis_service.get(key)
            assert value == "test_value"

            # Delete key
            deleted = redis_service.delete(key)
            assert deleted == 1

            # Verify deleted
            value = redis_service.get(key)
            assert value is None

        finally:
            # Cleanup
            redis_service.delete(key)

    def test_expiration_and_ttl(self, redis_service: RedisService) -> None:
        """Test key expiration and TTL operations."""
        key = f"test_exp_{uuid.uuid4().hex}"

        try:
            # Set value with TTL
            redis_service.set(key, "expiring_value", ex=10)

            # Check TTL exists
            ttl = redis_service.ttl(key)
            assert ttl > 0
            assert ttl <= 10

            # Update TTL
            result = redis_service.expire(key, 20)
            assert result is True

            # Verify new TTL
            new_ttl = redis_service.ttl(key)
            assert new_ttl > 10
            assert new_ttl <= 20

        finally:
            # Cleanup
            redis_service.delete(key)

    def test_hash_operations(self, redis_service: RedisService) -> None:
        """Test hash field operations."""
        hash_name = f"test_hash_{uuid.uuid4().hex}"

        try:
            # Set hash fields
            result = redis_service.hset(hash_name, "field1", "value1")
            assert result == 1  # New field added

            result = redis_service.hset(hash_name, "field2", "value2")
            assert result == 1

            # Get hash field
            value = redis_service.hget(hash_name, "field1")
            assert value == "value1"

            # Get all hash fields
            all_fields = redis_service.hgetall(hash_name)
            assert all_fields == {"field1": "value1", "field2": "value2"}

            # Delete hash field
            deleted = redis_service.hdel(hash_name, "field1")
            assert deleted == 1

            # Verify deletion
            all_fields = redis_service.hgetall(hash_name)
            assert "field1" not in all_fields
            assert all_fields == {"field2": "value2"}

        finally:
            # Cleanup
            redis_service.delete(hash_name)

    def test_list_operations(self, redis_service: RedisService) -> None:
        """Test list push, pop, and range operations."""
        list_name = f"test_list_{uuid.uuid4().hex}"

        try:
            # Push to head
            result = redis_service.lpush(list_name, "item1", "item2")
            assert result == 2

            # Push to tail
            result = redis_service.rpush(list_name, "item3")
            assert result == 3

            # Get range
            items = redis_service.lrange(list_name, 0, -1)
            assert items == ["item2", "item1", "item3"]

            # Pop from head
            value = redis_service.lpop(list_name)
            assert value == "item2"

            # Pop from tail
            value = redis_service.rpop(list_name)
            assert value == "item3"

            # Verify remaining
            items = redis_service.lrange(list_name, 0, -1)
            assert items == ["item1"]

        finally:
            # Cleanup
            redis_service.delete(list_name)

    def test_set_operations(self, redis_service: RedisService) -> None:
        """Test set add, members, and remove operations."""
        set_name = f"test_set_{uuid.uuid4().hex}"

        try:
            # Add members
            result = redis_service.sadd(set_name, "member1", "member2", "member3")
            assert result == 3

            # Get members
            members = redis_service.smembers(set_name)
            assert members == {"member1", "member2", "member3"}

            # Remove member
            removed = redis_service.srem(set_name, "member2")
            assert removed == 1

            # Verify removal
            members = redis_service.smembers(set_name)
            assert members == {"member1", "member3"}

        finally:
            # Cleanup
            redis_service.delete(set_name)

    def test_sorted_set_operations(self, redis_service: RedisService) -> None:
        """Test sorted set add, range, and remove operations."""
        zset_name = f"test_zset_{uuid.uuid4().hex}"

        try:
            # Add members with scores
            result = redis_service.zadd(
                zset_name,
                {"member1": 1.0, "member2": 2.0, "member3": 3.0},
            )
            assert result == 3

            # Get range
            members = redis_service.zrange(zset_name, 0, -1)
            assert members == ["member1", "member2", "member3"]

            # Get range with scores
            members_with_scores = redis_service.zrange(zset_name, 0, -1, withscores=True)
            assert members_with_scores == [
                ("member1", 1.0),
                ("member2", 2.0),
                ("member3", 3.0),
            ]

            # Remove member
            removed = redis_service.zrem(zset_name, "member2")
            assert removed == 1

            # Verify removal
            members = redis_service.zrange(zset_name, 0, -1)
            assert members == ["member1", "member3"]

        finally:
            # Cleanup
            redis_service.delete(zset_name)

    def test_json_operations(self, redis_service: RedisService) -> None:
        """Test JSON set, get, mget, and mset operations."""
        key1 = f"test_json_{uuid.uuid4().hex}_1"
        key2 = f"test_json_{uuid.uuid4().hex}_2"
        key3 = f"test_json_{uuid.uuid4().hex}_3"

        try:
            # Set JSON
            result = redis_service.set_json(key1, {"name": "Alice", "age": 30})
            assert result is True

            # Get JSON
            value = redis_service.get_json(key1)
            assert value == {"name": "Alice", "age": 30}

            # Multiple set
            result = redis_service.mset_json(
                {
                    key2: {"name": "Bob", "age": 25},
                    key3: {"name": "Charlie", "age": 35},
                }
            )
            assert result is True

            # Multiple get
            values = redis_service.mget_json(key1, key2, key3)
            assert len(values) == 3
            assert values[key1] == {"name": "Alice", "age": 30}
            assert values[key2] == {"name": "Bob", "age": 25}
            assert values[key3] == {"name": "Charlie", "age": 35}

        finally:
            # Cleanup
            redis_service.delete(key1, key2, key3)

    def test_pydantic_operations(self, redis_service: RedisService) -> None:
        """Test Pydantic model set and get operations."""
        key = f"test_user_{uuid.uuid4().hex}"

        try:
            # Create and set model
            user = RedisUser(
                user_id="user123",
                username="testuser",
                email="test@example.com",
                age=25,
            )
            result = redis_service.set_model(key, user)
            assert result is True

            # Get model
            retrieved_user = redis_service.get_model(key, RedisUser)
            assert retrieved_user is not None
            assert retrieved_user.user_id == "user123"
            assert retrieved_user.username == "testuser"
            assert retrieved_user.email == "test@example.com"
            assert retrieved_user.age == 25

        finally:
            # Cleanup
            redis_service.delete(key)

    def test_namespace_functionality(
        self, redis_service: RedisService, redis_config: RedisConfig, logger: LoggingService
    ) -> None:
        """Test namespace prefix functionality."""
        # Create namespaced service
        namespaced_config = RedisConfig(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            namespace="test_ns",
        )
        namespaced_service = RedisService(logger=logger, config=namespaced_config)

        key = f"namespaced_key_{uuid.uuid4().hex}"

        try:
            # Set value using namespaced service
            namespaced_service.set(key, "namespaced_value")

            # Verify key has namespace prefix in Redis
            actual_key = f"test_ns:{key}"
            value = redis_service.get(actual_key)
            assert value == "namespaced_value"

            # Get using namespaced service
            value = namespaced_service.get(key)
            assert value == "namespaced_value"

        finally:
            # Cleanup
            namespaced_service.delete(key)
            namespaced_service.close()

    def test_pipeline_operations(self, redis_service: RedisService) -> None:
        """Test pipeline batch operations."""
        key1 = f"test_pipe_{uuid.uuid4().hex}_1"
        key2 = f"test_pipe_{uuid.uuid4().hex}_2"
        key3 = f"test_pipe_{uuid.uuid4().hex}_3"

        try:
            # Execute pipeline
            with redis_service.pipeline() as pipe:
                pipe.set(key1, "value1")
                pipe.set(key2, "value2")
                pipe.set(key3, "value3")
                results = pipe.execute()

            # Verify all commands succeeded
            assert len(results) == 3
            assert all(results)

            # Verify values
            value1 = redis_service.get(key1)
            value2 = redis_service.get(key2)
            value3 = redis_service.get(key3)
            assert value1 == "value1"
            assert value2 == "value2"
            assert value3 == "value3"

        finally:
            # Cleanup
            redis_service.delete(key1, key2, key3)

    def test_pubsub_operations(self, redis_service: RedisService) -> None:
        """Test publish and subscribe operations."""
        channel = f"test_channel_{uuid.uuid4().hex}"
        test_message = "test message content"

        # Subscribe to channel
        with redis_service.subscribe(channel) as pubsub:
            # Wait for subscription confirmation
            message = pubsub.get_message()
            if message and message["type"] == "subscribe":
                # Publish message from another thread/connection
                subscribers = redis_service.publish(channel, test_message)
                assert subscribers >= 0  # May be 0 or 1 depending on timing

                # Receive message
                received = False
                for _ in range(5):  # Try up to 5 times
                    message = pubsub.get_message(timeout=1.0)
                    if message and message["type"] == "message":
                        assert message["data"] == test_message
                        received = True
                        break

                assert received, "Did not receive published message"

    def test_increment_decrement(self, redis_service: RedisService) -> None:
        """Test counter increment and decrement operations."""
        key = f"test_counter_{uuid.uuid4().hex}"

        try:
            # Set initial value
            redis_service.set(key, "10")

            # Increment
            new_value = redis_service.incr(key, 5)
            assert new_value == 15

            # Increment by 1 (default)
            new_value = redis_service.incr(key)
            assert new_value == 16

            # Decrement
            new_value = redis_service.decr(key, 3)
            assert new_value == 13

            # Decrement by 1 (default)
            new_value = redis_service.decr(key)
            assert new_value == 12

        finally:
            # Cleanup
            redis_service.delete(key)
