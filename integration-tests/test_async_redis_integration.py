"""Integration tests for async Redis service.

Tests async Redis service operations against a real Redis instance.
Configuration loaded from environment variables via conftest.py fixtures.
"""

import uuid

import pytest
from pydantic import BaseModel, Field

from lvrgd.common.services.redis.async_redis_service import AsyncRedisService


class AsyncRedisTestModel(BaseModel):
    """Model for async Redis integration tests."""

    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    score: int = Field(..., description="User score")


class TestAsyncRedisIntegration:
    """Integration tests for AsyncRedisService."""

    @pytest.mark.asyncio
    async def test_redis_connection_and_ping(self, async_redis_service: AsyncRedisService) -> None:
        """Test async Redis connection and ping functionality."""
        result = await async_redis_service.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_basic_get_set_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async basic get and set operations."""
        test_key = f"test:basic:{uuid.uuid4().hex[:8]}"

        try:
            # Set value
            result = await async_redis_service.set(test_key, "test_value", ex=60)
            assert result is True

            # Get value
            value = await async_redis_service.get(test_key)
            assert value == "test_value"

            # Verify TTL
            ttl = await async_redis_service.ttl(test_key)
            assert ttl > 0
            assert ttl <= 60

        finally:
            # Cleanup
            await async_redis_service.delete(test_key)

    @pytest.mark.asyncio
    async def test_json_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async JSON serialization operations."""
        test_key = f"test:json:{uuid.uuid4().hex[:8]}"

        try:
            # Set JSON value
            data = {"name": "John Doe", "age": 30, "active": True}
            result = await async_redis_service.set_json(test_key, data, ex=60)
            assert result is True

            # Get JSON value
            retrieved = await async_redis_service.get_json(test_key)
            assert retrieved == data
            assert retrieved["name"] == "John Doe"
            assert retrieved["age"] == 30

        finally:
            # Cleanup
            await async_redis_service.delete(test_key)

    @pytest.mark.asyncio
    async def test_pydantic_model_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async Pydantic model storage and retrieval."""
        test_key = f"test:model:{uuid.uuid4().hex[:8]}"

        try:
            # Create and store model
            user = AsyncRedisTestModel(user_id="user123", name="Alice", score=100)
            result = await async_redis_service.set_model(test_key, user, ex=60)
            assert result is True

            # Retrieve model
            retrieved = await async_redis_service.get_model(test_key, AsyncRedisTestModel)
            assert retrieved is not None
            assert retrieved.user_id == "user123"
            assert retrieved.name == "Alice"
            assert retrieved.score == 100

        finally:
            # Cleanup
            await async_redis_service.delete(test_key)

    @pytest.mark.asyncio
    async def test_batch_json_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async batch JSON operations."""
        test_keys = [f"test:batch:json:{uuid.uuid4().hex[:8]}" for _ in range(3)]

        try:
            # Batch set JSON
            mapping = {
                test_keys[0]: {"name": "User1", "value": 10},
                test_keys[1]: {"name": "User2", "value": 20},
                test_keys[2]: {"name": "User3", "value": 30},
            }
            result = await async_redis_service.mset_json(mapping, ex=60)
            assert result is True

            # Batch get JSON
            retrieved = await async_redis_service.mget_json(*test_keys)
            assert len(retrieved) == 3
            assert retrieved[test_keys[0]]["name"] == "User1"
            assert retrieved[test_keys[1]]["value"] == 20

        finally:
            # Cleanup
            await async_redis_service.delete(*test_keys)

    @pytest.mark.asyncio
    async def test_batch_model_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async batch Pydantic model operations."""
        test_keys = [f"test:batch:model:{uuid.uuid4().hex[:8]}" for _ in range(3)]

        try:
            # Batch set models
            mapping = {
                test_keys[0]: AsyncRedisTestModel(user_id="u1", name="User1", score=10),
                test_keys[1]: AsyncRedisTestModel(user_id="u2", name="User2", score=20),
                test_keys[2]: AsyncRedisTestModel(user_id="u3", name="User3", score=30),
            }
            result = await async_redis_service.mset_models(mapping, ex=60)
            assert result is True

            # Batch get models
            retrieved = await async_redis_service.mget_models(AsyncRedisTestModel, *test_keys)
            assert len(retrieved) == 3
            assert retrieved[test_keys[0]].user_id == "u1"
            assert retrieved[test_keys[1]].name == "User2"
            assert retrieved[test_keys[2]].score == 30

        finally:
            # Cleanup
            await async_redis_service.delete(*test_keys)

    @pytest.mark.asyncio
    async def test_pipeline_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async pipeline batch operations."""
        test_keys = [f"test:pipeline:{uuid.uuid4().hex[:8]}" for _ in range(3)]

        try:
            # Use pipeline for batch operations
            async with async_redis_service.pipeline() as pipe:
                pipe.set(test_keys[0], "value1")
                pipe.set(test_keys[1], "value2")
                pipe.set(test_keys[2], "value3")
                pipe.expire(test_keys[0], 60)
                pipe.expire(test_keys[1], 60)
                pipe.expire(test_keys[2], 60)
                results = await pipe.execute()

            assert len(results) == 6
            assert all(results[:3])  # All set operations succeeded

            # Verify values
            value1 = await async_redis_service.get(test_keys[0])
            value2 = await async_redis_service.get(test_keys[1])
            assert value1 == "value1"
            assert value2 == "value2"

        finally:
            # Cleanup
            await async_redis_service.delete(*test_keys)

    @pytest.mark.asyncio
    async def test_pub_sub_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async pub/sub messaging."""
        channel_name = f"test:channel:{uuid.uuid4().hex[:8]}"

        # Publish message
        subscribers = await async_redis_service.publish(channel_name, "test message")
        # No subscribers yet, so should return 0
        assert subscribers >= 0

    @pytest.mark.asyncio
    async def test_rate_limiting_sliding_window(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test async sliding window rate limiting."""
        rate_limit_key = f"test:ratelimit:sliding:{uuid.uuid4().hex[:8]}"

        try:
            # Test rate limiting with sliding window
            max_requests = 5
            window_seconds = 2

            # Make requests within limit
            for _ in range(max_requests):
                is_allowed, remaining = await async_redis_service.check_rate_limit(
                    rate_limit_key, max_requests, window_seconds, sliding=True
                )
                assert is_allowed is True
                assert remaining >= 0

            # Next request should be rate limited
            is_allowed, remaining = await async_redis_service.check_rate_limit(
                rate_limit_key, max_requests, window_seconds, sliding=True
            )
            assert is_allowed is False
            assert remaining == 0

        finally:
            # Cleanup
            await async_redis_service.delete(rate_limit_key)

    @pytest.mark.asyncio
    async def test_rate_limiting_fixed_window(self, async_redis_service: AsyncRedisService) -> None:
        """Test async fixed window rate limiting."""
        rate_limit_key = f"test:ratelimit:fixed:{uuid.uuid4().hex[:8]}"

        try:
            # Test rate limiting with fixed window
            max_requests = 3
            window_seconds = 2

            # Make requests within limit
            for _ in range(max_requests):
                is_allowed, remaining = await async_redis_service.check_rate_limit(
                    rate_limit_key, max_requests, window_seconds, sliding=False
                )
                assert is_allowed is True

            # Next request should be rate limited
            is_allowed, remaining = await async_redis_service.check_rate_limit(
                rate_limit_key, max_requests, window_seconds, sliding=False
            )
            assert is_allowed is False
            assert remaining == 0

        finally:
            # Cleanup
            await async_redis_service.delete(rate_limit_key)

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_hit(self, async_redis_service: AsyncRedisService) -> None:
        """Test async get_or_compute with cache hit."""
        test_key = f"test:compute:hit:{uuid.uuid4().hex[:8]}"

        try:
            # Prime the cache
            await async_redis_service.set_json(test_key, {"result": "cached_value"}, ex=60)

            # Call get_or_compute - should return cached value
            compute_called = False

            def compute_fn() -> dict[str, str]:
                nonlocal compute_called
                compute_called = True
                return {"result": "computed_value"}

            result = await async_redis_service.get_or_compute(
                test_key, compute_fn, ex=60, serialize_json=True
            )

            assert result == {"result": "cached_value"}
            assert compute_called is False  # Compute function should not be called

        finally:
            # Cleanup
            await async_redis_service.delete(test_key)

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_miss(self, async_redis_service: AsyncRedisService) -> None:
        """Test async get_or_compute with cache miss."""
        test_key = f"test:compute:miss:{uuid.uuid4().hex[:8]}"

        try:
            compute_called = False

            def compute_fn() -> dict[str, str]:
                nonlocal compute_called
                compute_called = True
                return {"result": "computed_value"}

            # Call get_or_compute - should compute and cache
            result = await async_redis_service.get_or_compute(
                test_key, compute_fn, ex=60, serialize_json=True
            )

            assert result == {"result": "computed_value"}
            assert compute_called is True

            # Verify value was cached
            cached = await async_redis_service.get_json(test_key)
            assert cached == {"result": "computed_value"}

        finally:
            # Cleanup
            await async_redis_service.delete(test_key)

    @pytest.mark.asyncio
    async def test_hash_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async hash operations."""
        hash_name = f"test:hash:{uuid.uuid4().hex[:8]}"

        try:
            # Set hash fields
            await async_redis_service.hset(hash_name, "field1", "value1")
            await async_redis_service.hset(hash_name, "field2", "value2")

            # Get hash field
            value = await async_redis_service.hget(hash_name, "field1")
            assert value == "value1"

            # Get all hash fields
            all_fields = await async_redis_service.hgetall(hash_name)
            assert len(all_fields) == 2
            assert all_fields["field1"] == "value1"
            assert all_fields["field2"] == "value2"

            # Delete hash field
            deleted = await async_redis_service.hdel(hash_name, "field1")
            assert deleted == 1

            # Verify deletion
            remaining = await async_redis_service.hgetall(hash_name)
            assert len(remaining) == 1

        finally:
            # Cleanup
            await async_redis_service.delete(hash_name)

    @pytest.mark.asyncio
    async def test_list_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async list operations."""
        list_name = f"test:list:{uuid.uuid4().hex[:8]}"

        try:
            # Push to list
            length = await async_redis_service.rpush(list_name, "item1", "item2", "item3")
            assert length == 3

            # Get list range
            items = await async_redis_service.lrange(list_name, 0, -1)
            assert len(items) == 3
            assert items == ["item1", "item2", "item3"]

            # Pop from list
            popped = await async_redis_service.lpop(list_name)
            assert popped == "item1"

            # Verify remaining items
            remaining = await async_redis_service.lrange(list_name, 0, -1)
            assert len(remaining) == 2

        finally:
            # Cleanup
            await async_redis_service.delete(list_name)

    @pytest.mark.asyncio
    async def test_set_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async set operations."""
        set_name = f"test:set:{uuid.uuid4().hex[:8]}"

        try:
            # Add to set
            added = await async_redis_service.sadd(set_name, "member1", "member2", "member3")
            assert added == 3

            # Get set members
            members = await async_redis_service.smembers(set_name)
            assert len(members) == 3
            assert "member1" in members

            # Remove from set
            removed = await async_redis_service.srem(set_name, "member1")
            assert removed == 1

            # Verify remaining members
            remaining = await async_redis_service.smembers(set_name)
            assert len(remaining) == 2

        finally:
            # Cleanup
            await async_redis_service.delete(set_name)

    @pytest.mark.asyncio
    async def test_sorted_set_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async sorted set operations."""
        zset_name = f"test:zset:{uuid.uuid4().hex[:8]}"

        try:
            # Add to sorted set
            mapping = {"member1": 1.0, "member2": 2.0, "member3": 3.0}
            added = await async_redis_service.zadd(zset_name, mapping)
            assert added == 3

            # Get sorted set range
            members = await async_redis_service.zrange(zset_name, 0, -1)
            assert len(members) == 3
            assert members == ["member1", "member2", "member3"]

            # Remove from sorted set
            removed = await async_redis_service.zrem(zset_name, "member2")
            assert removed == 1

            # Verify remaining members
            remaining = await async_redis_service.zrange(zset_name, 0, -1)
            assert len(remaining) == 2

        finally:
            # Cleanup
            await async_redis_service.delete(zset_name)

    @pytest.mark.asyncio
    async def test_increment_decrement_operations(
        self, async_redis_service: AsyncRedisService
    ) -> None:
        """Test async increment and decrement operations."""
        counter_key = f"test:counter:{uuid.uuid4().hex[:8]}"

        try:
            # Increment
            value = await async_redis_service.incr(counter_key, 5)
            assert value == 5

            # Increment again
            value = await async_redis_service.incr(counter_key, 3)
            assert value == 8

            # Decrement
            value = await async_redis_service.decr(counter_key, 2)
            assert value == 6

        finally:
            # Cleanup
            await async_redis_service.delete(counter_key)

    @pytest.mark.asyncio
    async def test_expiration_operations(self, async_redis_service: AsyncRedisService) -> None:
        """Test async expiration operations."""
        test_key = f"test:expire:{uuid.uuid4().hex[:8]}"

        try:
            # Set value
            await async_redis_service.set(test_key, "test_value")

            # Set expiration
            result = await async_redis_service.expire(test_key, 10)
            assert result is True

            # Check TTL
            ttl = await async_redis_service.ttl(test_key)
            assert ttl > 0
            assert ttl <= 10

            # Check existence
            exists = await async_redis_service.exists(test_key)
            assert exists == 1

        finally:
            # Cleanup
            await async_redis_service.delete(test_key)
