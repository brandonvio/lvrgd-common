"""Async Redis service for caching and data operations.

This module provides a clean Redis service implementation with:
- Strong typing for all operations
- Common Redis operations (get, set, delete, expire, etc.)
- Pub/Sub support
- Vector search capabilities
- Health check functionality
"""

from __future__ import annotations

import functools
import json
import struct
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from redis.asyncio import ConnectionPool, Redis
from redis.commands.search.field import NumericField, TagField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError

from lvrgd.common.services.logging_service import LoggingService

from .redis_models import RedisConfig

T = TypeVar("T", bound=BaseModel)


class AsyncRedisService:
    """Async Redis service for caching and data operations."""

    def __init__(
        self,
        logger: LoggingService,
        config: RedisConfig,
    ) -> None:
        """Initialize AsyncRedisService.

        Args:
            logger: LoggingService instance for structured logging
            config: Redis configuration model
        """
        self.log = logger
        self.config = config

        self.log.info(
            "Initializing async Redis connection",
            host=config.host,
            port=config.port,
            db=config.db,
        )

        # Create connection pool
        connection_params: dict[str, Any] = {
            "host": config.host,
            "port": config.port,
            "db": config.db,
            "socket_connect_timeout": config.socket_connect_timeout,
            "socket_timeout": config.socket_timeout,
            "max_connections": config.max_connections,
            "decode_responses": config.decode_responses,
            "retry_on_timeout": config.retry_on_timeout,
            "health_check_interval": config.health_check_interval,
        }

        # Add authentication if provided
        if config.password:
            connection_params["password"] = config.password
        if config.username:
            connection_params["username"] = config.username

        try:
            self._pool: ConnectionPool = ConnectionPool(**connection_params)
            self._client: Redis[str] = Redis(connection_pool=self._pool)
            self.log.info("Async Redis client initialized")

        except Exception:
            self.log.exception("Failed to initialize async Redis connection")
            raise

    def _apply_namespace(self, key: str) -> str:
        """Apply namespace prefix to key if configured.

        Args:
            key: Original key

        Returns:
            Key with namespace prefix if configured, otherwise original key
        """
        if self.config.namespace:
            return f"{self.config.namespace}:{key}"
        return key

    async def ping(self) -> bool:
        """Ping the Redis server to verify connection.

        Returns:
            True if connection is successful

        Raises:
            RedisConnectionError: If unable to connect to Redis
        """
        try:
            result = await self._client.ping()
            self.log.debug("Async Redis ping successful")
            return result
        except RedisConnectionError:
            self.log.exception("Async Redis connection failed")
            raise

    async def get(self, key: str) -> str | None:
        """Get value for a key.

        Args:
            key: Key to retrieve (namespace will be applied if configured)

        Returns:
            Value associated with key, or None if key doesn't exist
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug("Getting value", key=namespaced_key)
        value = await self._client.get(namespaced_key)
        if value:
            self.log.debug("Found value", key=namespaced_key)
        else:
            self.log.debug("Key not found", key=namespaced_key)
        return value

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set key to hold the string value.

        Args:
            key: Key to set (namespace will be applied if configured)
            value: Value to set
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key already exists

        Returns:
            True if operation was successful
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug(
            "Setting value",
            key=namespaced_key,
            ex=ex,
            px=px,
            nx=nx,
            xx=xx,
        )
        result = await self._client.set(namespaced_key, value, ex=ex, px=px, nx=nx, xx=xx)
        self.log.info("Successfully set value", key=namespaced_key)
        return bool(result)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys.

        Args:
            *keys: Keys to delete (namespace will be applied if configured)

        Returns:
            Number of keys that were deleted
        """
        namespaced_keys = [self._apply_namespace(k) for k in keys]
        self.log.debug("Deleting keys", count=len(namespaced_keys))
        result = await self._client.delete(*namespaced_keys)
        self.log.info("Successfully deleted keys", deleted=result)
        return result

    async def exists(self, *keys: str) -> int:
        """Check if one or more keys exist.

        Args:
            *keys: Keys to check (namespace will be applied if configured)

        Returns:
            Number of keys that exist
        """
        namespaced_keys = [self._apply_namespace(k) for k in keys]
        self.log.debug("Checking key existence", count=len(namespaced_keys))
        result = await self._client.exists(*namespaced_keys)
        self.log.debug("Keys existence check", exists=result)
        return result

    async def expire(self, key: str, seconds: int) -> bool:
        """Set a timeout on key.

        Args:
            key: Key to set timeout on (namespace will be applied if configured)
            seconds: Timeout in seconds

        Returns:
            True if timeout was set, False if key doesn't exist
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug("Setting expiration", key=namespaced_key, seconds=seconds)
        result = await self._client.expire(namespaced_key, seconds)
        self.log.info("Successfully set expiration", key=namespaced_key, result=result)
        return bool(result)

    async def ttl(self, key: str) -> int:
        """Get the time to live for a key.

        Args:
            key: Key to check (namespace will be applied if configured)

        Returns:
            TTL in seconds, -1 if key exists but has no expire, -2 if key doesn't exist
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug("Getting TTL", key=namespaced_key)
        result = await self._client.ttl(namespaced_key)
        self.log.debug("TTL retrieved", key=namespaced_key, ttl=result)
        return result

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment the integer value of a key.

        Args:
            key: Key to increment (namespace will be applied if configured)
            amount: Amount to increment by (default: 1)

        Returns:
            Value of key after increment
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug("Incrementing key", key=namespaced_key, amount=amount)
        result = await self._client.incr(namespaced_key, amount)
        self.log.info("Successfully incremented key", key=namespaced_key, new_value=result)
        return result

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement the integer value of a key.

        Args:
            key: Key to decrement (namespace will be applied if configured)
            amount: Amount to decrement by (default: 1)

        Returns:
            Value of key after decrement
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug("Decrementing key", key=namespaced_key, amount=amount)
        result = await self._client.decr(namespaced_key, amount)
        self.log.info("Successfully decremented key", key=namespaced_key, new_value=result)
        return result

    async def hget(self, name: str, key: str) -> str | None:
        """Get value from hash field.

        Args:
            name: Hash name
            key: Field key

        Returns:
            Value associated with field, or None if field doesn't exist
        """
        self.log.debug("Getting hash field", hash=name, key=key)
        value = await self._client.hget(name, key)
        if value:
            self.log.debug("Found hash field", hash=name, key=key)
        else:
            self.log.debug("Hash field not found", hash=name, key=key)
        return value

    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field to value.

        Args:
            name: Hash name
            key: Field key
            value: Field value

        Returns:
            Number of fields that were added (0 if field existed and was updated)
        """
        self.log.debug("Setting hash field", hash=name, key=key)
        result = await self._client.hset(name, key, value)
        self.log.info("Successfully set hash field", hash=name, key=key, added=result)
        return result

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all fields and values in a hash.

        Args:
            name: Hash name

        Returns:
            Dictionary of field-value pairs
        """
        self.log.debug("Getting all hash fields", hash=name)
        result = await self._client.hgetall(name)
        self.log.info("Retrieved hash fields", hash=name, count=len(result))
        return result

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete one or more hash fields.

        Args:
            name: Hash name
            *keys: Field keys to delete

        Returns:
            Number of fields that were deleted
        """
        self.log.debug("Deleting hash fields", hash=name, count=len(keys))
        result = await self._client.hdel(name, *keys)
        self.log.info("Successfully deleted hash fields", hash=name, deleted=result)
        return result

    async def lpush(self, name: str, *values: str) -> int:
        """Push values to the head of the list.

        Args:
            name: List name
            *values: Values to push

        Returns:
            Length of the list after push
        """
        self.log.debug("Pushing to list head", list=name, count=len(values))
        result = await self._client.lpush(name, *values)
        self.log.info("Successfully pushed to list", list=name, length=result)
        return result

    async def rpush(self, name: str, *values: str) -> int:
        """Push values to the tail of the list.

        Args:
            name: List name
            *values: Values to push

        Returns:
            Length of the list after push
        """
        self.log.debug("Pushing to list tail", list=name, count=len(values))
        result = await self._client.rpush(name, *values)
        self.log.info("Successfully pushed to list", list=name, length=result)
        return result

    async def lpop(self, name: str) -> str | None:
        """Remove and return the first element of the list.

        Args:
            name: List name

        Returns:
            Value of the first element, or None if list is empty
        """
        self.log.debug("Popping from list head", list=name)
        value = await self._client.lpop(name)
        if value:
            self.log.info("Successfully popped from list", list=name)
        else:
            self.log.debug("List is empty", list=name)
        return value

    async def rpop(self, name: str) -> str | None:
        """Remove and return the last element of the list.

        Args:
            name: List name

        Returns:
            Value of the last element, or None if list is empty
        """
        self.log.debug("Popping from list tail", list=name)
        value = await self._client.rpop(name)
        if value:
            self.log.info("Successfully popped from list", list=name)
        else:
            self.log.debug("List is empty", list=name)
        return value

    async def lrange(self, name: str, start: int, end: int) -> list[str]:
        """Get a range of elements from the list.

        Args:
            name: List name
            start: Start index
            end: End index

        Returns:
            List of elements in the specified range
        """
        self.log.debug("Getting list range", list=name, start=start, end=end)
        result = await self._client.lrange(name, start, end)
        self.log.info("Retrieved list range", list=name, count=len(result))
        return result

    async def sadd(self, name: str, *values: str) -> int:
        """Add members to a set.

        Args:
            name: Set name
            *values: Members to add

        Returns:
            Number of members that were added (excluding already existing members)
        """
        self.log.debug("Adding to set", set=name, count=len(values))
        result = await self._client.sadd(name, *values)
        self.log.info("Successfully added to set", set=name, added=result)
        return result

    async def smembers(self, name: str) -> set[str]:
        """Get all members of a set.

        Args:
            name: Set name

        Returns:
            Set of all members
        """
        self.log.debug("Getting set members", set=name)
        result = await self._client.smembers(name)
        self.log.info("Retrieved set members", set=name, count=len(result))
        return result

    async def srem(self, name: str, *values: str) -> int:
        """Remove members from a set.

        Args:
            name: Set name
            *values: Members to remove

        Returns:
            Number of members that were removed
        """
        self.log.debug("Removing from set", set=name, count=len(values))
        result = await self._client.srem(name, *values)
        self.log.info("Successfully removed from set", set=name, removed=result)
        return result

    async def zadd(
        self, name: str, mapping: dict[str, float], nx: bool = False, xx: bool = False
    ) -> int:
        """Add members to a sorted set.

        Args:
            name: Sorted set name
            mapping: Dictionary of member-score pairs
            nx: Only add new members (don't update scores for existing members)
            xx: Only update scores for existing members (don't add new members)

        Returns:
            Number of members added (or updated if xx=True)
        """
        self.log.debug("Adding to sorted set", zset=name, count=len(mapping), nx=nx, xx=xx)
        result = await self._client.zadd(name, mapping, nx=nx, xx=xx)
        self.log.info("Successfully added to sorted set", zset=name, added=result)
        return result

    async def zrange(
        self,
        name: str,
        start: int,
        end: int,
        desc: bool = False,
        withscores: bool = False,
    ) -> list[str] | list[tuple[str, float]]:
        """Get a range of members from a sorted set.

        Args:
            name: Sorted set name
            start: Start index
            end: End index
            desc: Sort in descending order
            withscores: Return scores along with members

        Returns:
            List of members, or list of (member, score) tuples if withscores=True
        """
        self.log.debug(
            "Getting sorted set range",
            zset=name,
            start=start,
            end=end,
            desc=desc,
            withscores=withscores,
        )
        result = await self._client.zrange(name, start, end, desc=desc, withscores=withscores)
        self.log.info("Retrieved sorted set range", zset=name, count=len(result))
        return result

    async def zrem(self, name: str, *values: str) -> int:
        """Remove members from a sorted set.

        Args:
            name: Sorted set name
            *values: Members to remove

        Returns:
            Number of members that were removed
        """
        self.log.debug("Removing from sorted set", zset=name, count=len(values))
        result = await self._client.zrem(name, *values)
        self.log.info("Successfully removed from sorted set", zset=name, removed=result)
        return result

    @asynccontextmanager
    async def pipeline(self, transaction: bool = True) -> AsyncIterator[Any]:
        """Context manager for Redis pipeline.

        Args:
            transaction: Whether to use transaction (MULTI/EXEC)

        Yields:
            Pipeline object for batching commands

        Example:
            with redis_service.pipeline() as pipe:
                pipe.set("key1", "value1")
                pipe.set("key2", "value2")
                results = pipe.execute()
        """
        self.log.debug("Starting Redis pipeline", transaction=transaction)
        pipe = self._client.pipeline(transaction=transaction)
        try:
            yield pipe
            self.log.debug("Redis pipeline executed successfully")
        except Exception:
            self.log.exception("Redis pipeline failed")
            raise

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers that received the message
        """
        self.log.debug("Publishing message", channel=channel)
        result = await self._client.publish(channel, message)
        self.log.info("Successfully published message", channel=channel, subscribers=result)
        return result

    @asynccontextmanager
    async def subscribe(self, *channels: str) -> AsyncIterator[Any]:
        """Context manager for subscribing to channels.

        Args:
            *channels: Channel names to subscribe to

        Yields:
            PubSub object for receiving messages

        Example:
            with redis_service.subscribe("channel1", "channel2") as pubsub:
                for message in pubsub.listen():
                    if message["type"] == "message":
                        print(message["data"])
        """
        self.log.debug("Subscribing to channels", channels=channels)
        pubsub = self._client.pubsub()
        try:
            await pubsub.subscribe(*channels)
            self.log.info("Successfully subscribed to channels", channels=channels)
            yield pubsub
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()
            self.log.debug("Unsubscribed from channels", channels=channels)

    async def create_vector_index(
        self,
        index_name: str,
        prefix: str,
        vector_field: str,
        vector_dims: int,
        distance_metric: str = "COSINE",
        text_fields: list[str] | None = None,
        numeric_fields: list[str] | None = None,
        tag_fields: list[str] | None = None,
    ) -> None:
        """Create a vector search index.

        Args:
            index_name: Name of the index
            prefix: Key prefix for documents in this index
            vector_field: Name of the field containing vector embeddings
            vector_dims: Dimensionality of the vectors
            distance_metric: Distance metric (COSINE, L2, IP)
            text_fields: List of text fields to index
            numeric_fields: List of numeric fields to index
            tag_fields: List of tag fields to index

        Raises:
            ResponseError: If index creation fails
        """
        self.log.debug(
            "Creating vector index",
            index_name=index_name,
            prefix=prefix,
            vector_dims=vector_dims,
            distance_metric=distance_metric,
        )

        schema = []

        # Add vector field
        schema.append(
            VectorField(
                vector_field,
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": vector_dims,
                    "DISTANCE_METRIC": distance_metric,
                },
            ),
        )

        # Add text fields
        if text_fields:
            schema.extend(TextField(field) for field in text_fields)

        # Add numeric fields
        if numeric_fields:
            schema.extend(NumericField(field) for field in numeric_fields)

        # Add tag fields
        if tag_fields:
            schema.extend(TagField(field) for field in tag_fields)

        definition = IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)

        try:
            await self._client.ft(index_name).create_index(fields=schema, definition=definition)
            self.log.info(
                "Successfully created vector index",
                index_name=index_name,
                fields=len(schema),
            )
        except ResponseError:
            self.log.exception("Failed to create vector index", index_name=index_name)
            raise

    async def vector_search(
        self,
        index_name: str,
        vector_field: str,
        query_vector: list[float],
        k: int = 10,
        filter_query: str = "*",
    ) -> list[dict[str, Any]]:
        """Perform vector similarity search.

        Args:
            index_name: Name of the index to search
            vector_field: Name of the vector field
            query_vector: Query vector for similarity search
            k: Number of results to return
            filter_query: Optional filter query (e.g., "@category:{electronics}")

        Returns:
            List of search results with scores

        Example:
            results = redis_service.vector_search(
                "products_idx",
                "embedding",
                [0.1, 0.2, ...],
                k=5,
                filter_query="@category:{electronics}"
            )
        """
        self.log.debug(
            "Performing vector search",
            index_name=index_name,
            k=k,
            filter_query=filter_query,
        )

        # Convert vector to bytes
        vector_bytes = b"".join(struct.pack("<f", float(v)) for v in query_vector)

        # Build the query
        query = (
            Query(f"({filter_query})=>[KNN {k} @{vector_field} $vector AS score]")
            .return_fields("score")
            .sort_by("score")
            .dialect(2)
        )

        try:
            results = await self._client.ft(index_name).search(
                query, query_params={"vector": vector_bytes}
            )
            self.log.info(
                "Vector search completed",
                index_name=index_name,
                results=results.total,
            )

            # Convert results to list of dicts
            return [{"id": doc.id, "score": doc.score, **doc.__dict__} for doc in results.docs]

        except ResponseError:
            self.log.exception("Vector search failed", index_name=index_name)
            raise

    async def drop_index(self, index_name: str, delete_documents: bool = False) -> None:
        """Drop a search index.

        Args:
            index_name: Name of the index to drop
            delete_documents: Whether to delete the documents as well

        Raises:
            ResponseError: If index deletion fails
        """
        self.log.debug("Dropping index", index_name=index_name, delete_documents=delete_documents)
        try:
            await self._client.ft(index_name).dropindex(delete_documents=delete_documents)
            self.log.info("Successfully dropped index", index_name=index_name)
        except ResponseError:
            self.log.exception("Failed to drop index", index_name=index_name)
            raise

    async def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
        """Get and deserialize JSON value for a key.

        Args:
            key: Key to retrieve (namespace will be applied if configured)

        Returns:
            Deserialized JSON value (dict, list, or primitive), or None if key doesn't exist

        Raises:
            json.JSONDecodeError: If stored value is not valid JSON

        Example:
            data = redis_service.get_json("user:123")
            # Returns: {"name": "John", "age": 30}
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug("Getting JSON value", key=namespaced_key)
        value = await self._client.get(namespaced_key)

        if value is None:
            self.log.debug("Key not found", key=namespaced_key)
            return None

        try:
            result = json.loads(value)
            self.log.debug("Successfully deserialized JSON", key=namespaced_key)
            return result
        except json.JSONDecodeError:
            self.log.warning("Invalid JSON for key", key=namespaced_key)
            raise

    async def set_json(
        self,
        key: str,
        value: dict[str, Any] | list[Any] | str | float | bool | None,
        ex: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Serialize and set JSON value for a key.

        Args:
            key: Key to set (namespace will be applied if configured)
            value: JSON-serializable value (dict, list, or primitive)
            ex: Expire time in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key already exists

        Returns:
            True if operation was successful

        Example:
            redis_service.set_json("user:123", {"name": "John", "age": 30}, ex=3600)
        """
        namespaced_key = self._apply_namespace(key)
        self.log.debug("Setting JSON value", key=namespaced_key, ex=ex, nx=nx, xx=xx)
        json_str = json.dumps(value)
        result = await self._client.set(namespaced_key, json_str, ex=ex, nx=nx, xx=xx)
        self.log.info("Successfully set JSON value", key=namespaced_key)
        return bool(result)

    async def mget_json(self, *keys: str) -> dict[str, Any]:
        """Get multiple JSON values in a single operation.

        Args:
            *keys: Keys to retrieve (namespace will be applied if configured)

        Returns:
            Dictionary mapping original keys to their deserialized JSON values (omits missing keys and invalid JSON)

        Example:
            results = redis_service.mget_json("user:1", "user:2", "user:3")
            # Returns: {"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}
        """
        namespaced_keys = [self._apply_namespace(k) for k in keys]
        self.log.debug("Getting multiple JSON values", count=len(namespaced_keys))
        values = await self._client.mget(*namespaced_keys)
        result: dict[str, Any] = {}

        for key, value in zip(keys, values, strict=False):
            if value is None:
                continue

            try:
                result[key] = json.loads(value)
            except json.JSONDecodeError:
                self.log.warning("Invalid JSON for key, skipping", key=key)
                continue

        self.log.info("Retrieved JSON values", requested=len(keys), returned=len(result))
        return result

    async def mset_json(
        self,
        mapping: dict[str, dict[str, Any] | list[Any] | str | int | float | bool | None],
        ex: int | None = None,
    ) -> bool:
        """Set multiple JSON values in a single operation.

        Args:
            mapping: Dictionary of key-value pairs to set (namespace will be applied if configured)
            ex: Optional expiration time in seconds (applied to all keys)

        Returns:
            True if operation was successful

        Example:
            redis_service.mset_json({
                "user:1": {"name": "John"},
                "user:2": {"name": "Jane"}
            }, ex=3600)
        """
        self.log.debug("Setting multiple JSON values", count=len(mapping), ex=ex)

        # Apply namespace and serialize all values to JSON
        json_mapping = {
            self._apply_namespace(key): json.dumps(value) for key, value in mapping.items()
        }

        if ex is None:
            # Simple MSET without expiration
            result = await self._client.mset(json_mapping)
            self.log.info("Successfully set JSON values", count=len(mapping))
            return bool(result)

        # Use pipeline for MSET + EXPIRE
        async with self.pipeline() as pipe:
            pipe.mset(json_mapping)
            for key in json_mapping:
                pipe.expire(key, ex)
            await pipe.execute()

        self.log.info("Successfully set JSON values with expiration", count=len(mapping), ex=ex)
        return True

    async def hget_json(self, name: str, key: str) -> dict[str, Any] | list[Any] | None:
        """Get and deserialize JSON value from hash field.

        Args:
            name: Hash name
            key: Field key

        Returns:
            Deserialized JSON value, or None if field doesn't exist

        Raises:
            json.JSONDecodeError: If stored value is not valid JSON

        Example:
            data = redis_service.hget_json("users", "user:123")
            # Returns: {"name": "John", "age": 30}
        """
        self.log.debug("Getting JSON hash field", hash=name, key=key)
        value = await self._client.hget(name, key)

        if value is None:
            self.log.debug("Hash field not found", hash=name, key=key)
            return None

        try:
            result = json.loads(value)
            self.log.debug("Successfully deserialized JSON hash field", hash=name, key=key)
            return result
        except json.JSONDecodeError:
            self.log.warning("Invalid JSON in hash field", hash=name, key=key)
            raise

    async def hset_json(
        self,
        name: str,
        key: str,
        value: dict[str, Any] | list[Any] | str | float | bool | None,
    ) -> int:
        """Serialize and set JSON value in hash field.

        Args:
            name: Hash name
            key: Field key
            value: JSON-serializable value

        Returns:
            Number of fields that were added (0 if field existed and was updated)

        Example:
            redis_service.hset_json("users", "user:123", {"name": "John", "age": 30})
        """
        self.log.debug("Setting JSON hash field", hash=name, key=key)
        json_str = json.dumps(value)
        result = await self._client.hset(name, key, json_str)
        self.log.info("Successfully set JSON hash field", hash=name, key=key, added=result)
        return result

    async def hgetall_json(self, name: str) -> dict[str, Any]:
        """Get all fields and deserialize JSON values from hash.

        Args:
            name: Hash name

        Returns:
            Dictionary of field-value pairs with deserialized JSON values (skips invalid JSON)

        Example:
            data = redis_service.hgetall_json("users")
            # Returns: {"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}
        """
        self.log.debug("Getting all JSON hash fields", hash=name)
        raw_data = await self._client.hgetall(name)
        result: dict[str, Any] = {}

        for key, value in raw_data.items():
            try:
                result[key] = json.loads(value)
            except json.JSONDecodeError:  # noqa: PERF203
                # Try-except in loop is intentional - each field may have invalid JSON
                self.log.warning("Invalid JSON in hash field, skipping", hash=name, key=key)
                continue

        self.log.info("Retrieved JSON hash fields", hash=name, count=len(result))
        return result

    async def get_model(self, key: str, model_class: type[T]) -> T | None:
        """Get and deserialize Pydantic model for a key.

        Args:
            key: Key to retrieve
            model_class: Pydantic model class to deserialize into

        Returns:
            Validated Pydantic model instance, or None if key doesn't exist

        Raises:
            ValidationError: If stored data doesn't match model schema

        Example:
            user = redis_service.get_model("user:123", UserModel)
            # Returns: UserModel(name="John", age=30)
        """
        self.log.debug("Getting Pydantic model", key=key, model=model_class.__name__)
        namespaced_key = self._apply_namespace(key)
        value = await self._client.get(namespaced_key)

        if value is None:
            self.log.debug("Key not found", key=key)
            return None

        try:
            data = json.loads(value)
            result = model_class(**data)
            self.log.debug("Successfully validated model", key=key, model=model_class.__name__)
            return result
        except ValidationError:
            self.log.warning("Validation failed for model", key=key, model=model_class.__name__)
            raise

    async def set_model(
        self,
        key: str,
        model: BaseModel,
        ex: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Serialize and set Pydantic model for a key.

        Args:
            key: Key to set
            model: Pydantic model instance to store
            ex: Expire time in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key already exists

        Returns:
            True if operation was successful

        Example:
            user = UserModel(name="John", age=30)
            redis_service.set_model("user:123", user, ex=3600)
        """
        self.log.debug(
            "Setting Pydantic model", key=key, model=type(model).__name__, ex=ex, nx=nx, xx=xx
        )
        json_str = model.model_dump_json()
        namespaced_key = self._apply_namespace(key)
        result = await self._client.set(namespaced_key, json_str, ex=ex, nx=nx, xx=xx)
        self.log.info("Successfully set model", key=key, model=type(model).__name__)
        return bool(result)

    async def mget_models(self, model_class: type[T], *keys: str) -> dict[str, T]:
        """Get multiple Pydantic models in a single operation.

        Args:
            model_class: Pydantic model class to deserialize into
            *keys: Keys to retrieve

        Returns:
            Dictionary mapping keys to validated model instances (omits missing keys and invalid models)

        Example:
            users = redis_service.mget_models(UserModel, "user:1", "user:2", "user:3")
            # Returns: {"user:1": UserModel(...), "user:2": UserModel(...)}
        """
        self.log.debug(
            "Getting multiple Pydantic models", model=model_class.__name__, count=len(keys)
        )
        namespaced_keys = [self._apply_namespace(k) for k in keys]
        values = await self._client.mget(*namespaced_keys)
        result: dict[str, T] = {}

        for key, value in zip(keys, values, strict=False):
            if value is None:
                continue

            try:
                data = json.loads(value)
                result[key] = model_class(**data)
            except (json.JSONDecodeError, ValidationError):
                self.log.warning(
                    "Invalid model data for key, skipping", key=key, model=model_class.__name__
                )
                continue

        self.log.info(
            "Retrieved models",
            model=model_class.__name__,
            requested=len(keys),
            returned=len(result),
        )
        return result

    async def mset_models(self, mapping: dict[str, BaseModel], ex: int | None = None) -> bool:
        """Set multiple Pydantic models in a single operation.

        Args:
            mapping: Dictionary of key-model pairs to set
            ex: Optional expiration time in seconds (applied to all keys)

        Returns:
            True if operation was successful

        Example:
            redis_service.mset_models({
                "user:1": UserModel(name="John"),
                "user:2": UserModel(name="Jane")
            }, ex=3600)
        """
        self.log.debug("Setting multiple Pydantic models", count=len(mapping), ex=ex)

        # Serialize all models to JSON and apply namespace
        json_mapping = {
            self._apply_namespace(key): model.model_dump_json() for key, model in mapping.items()
        }

        if ex is None:
            # Simple MSET without expiration
            result = await self._client.mset(json_mapping)
            self.log.info("Successfully set models", count=len(mapping))
            return bool(result)

        # Use pipeline for MSET + EXPIRE
        async with self.pipeline() as pipe:
            pipe.mset(json_mapping)
            for key in mapping:
                pipe.expire(self._apply_namespace(key), ex)
            await pipe.execute()

        self.log.info("Successfully set models with expiration", count=len(mapping), ex=ex)
        return True

    async def hget_model(self, hash_name: str, field: str, model_class: type[T]) -> T | None:
        """Get and deserialize Pydantic model from hash field.

        Args:
            hash_name: Hash name
            field: Field key
            model_class: Pydantic model class to deserialize into

        Returns:
            Validated Pydantic model instance, or None if field doesn't exist

        Raises:
            ValidationError: If stored data doesn't match model schema

        Example:
            user = redis_service.hget_model("users", "user:123", UserModel)
            # Returns: UserModel(name="John", age=30)
        """
        self.log.debug(
            "Getting Pydantic model from hash",
            hash=hash_name,
            field=field,
            model=model_class.__name__,
        )
        value = await self._client.hget(hash_name, field)

        if value is None:
            self.log.debug("Hash field not found", hash=hash_name, field=field)
            return None

        try:
            data = json.loads(value)
            result = model_class(**data)
            self.log.debug(
                "Successfully validated model from hash",
                hash=hash_name,
                field=field,
                model=model_class.__name__,
            )
            return result
        except ValidationError:
            self.log.warning(
                "Validation failed for hash field",
                hash=hash_name,
                field=field,
                model=model_class.__name__,
            )
            raise

    async def hset_model(self, hash_name: str, field: str, model: BaseModel) -> int:
        """Serialize and set Pydantic model in hash field.

        Args:
            hash_name: Hash name
            field: Field key
            model: Pydantic model instance to store

        Returns:
            Number of fields that were added (0 if field existed and was updated)

        Example:
            user = UserModel(name="John", age=30)
            redis_service.hset_model("users", "user:123", user)
        """
        self.log.debug(
            "Setting Pydantic model in hash",
            hash=hash_name,
            field=field,
            model=type(model).__name__,
        )
        json_str = model.model_dump_json()
        result = await self._client.hset(hash_name, field, json_str)
        self.log.info(
            "Successfully set model in hash",
            hash=hash_name,
            field=field,
            model=type(model).__name__,
            added=result,
        )
        return result

    async def cache(  # noqa: C901, PLR0915
        self,
        ttl: int,
        key_prefix: str | None = None,
        namespace: str | None = None,
        skip_cache_if: Callable[[Any], bool] | None = None,
        prevent_thundering_herd: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to cache function results in Redis.

        Args:
            ttl: Time to live in seconds
            key_prefix: Optional prefix for cache key
            namespace: Optional namespace for cache key
            skip_cache_if: Optional callable to skip caching based on result
            prevent_thundering_herd: Use lock to prevent multiple simultaneous cache fills

        Returns:
            Decorator function

        Example:
            @redis_service.cache(ttl=3600, key_prefix="user", namespace="app")
            def get_user(user_id: str) -> dict[str, Any]:
                return fetch_user_from_db(user_id)
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:  # noqa: C901
            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                cache_key = self._generate_cache_key(func, key_prefix, namespace, args, kwargs)

                # Try to get cached value
                try:
                    cached = await self.get_json(cache_key)
                    if cached is not None:
                        self.log.debug("Cache hit", cache_key=cache_key)
                        return cached
                except Exception:  # noqa: BLE001
                    # Broad exception catch is intentional - cache failures should not break function
                    self.log.warning(
                        "Failed to get cached value, calling function", cache_key=cache_key
                    )

                # Cache miss - need to call function
                if prevent_thundering_herd:
                    lock_key = f"{cache_key}:lock"
                    lock_acquired = await self.set(lock_key, "1", ex=ttl, nx=True)

                    if not lock_acquired:
                        # Another process is computing, wait briefly and retry cache
                        self.log.debug(
                            "Lock held by another process, retrying cache", cache_key=cache_key
                        )
                        try:
                            cached = await self.get_json(cache_key)
                            if cached is not None:
                                return cached
                        except Exception:  # noqa: BLE001
                            # Broad exception catch is intentional - if cache read fails during lock wait,
                            # we'll compute the value ourselves
                            self.log.debug(
                                "Failed to retry cache read, will compute value",
                                cache_key=cache_key,
                            )

                # Call the actual function
                try:
                    result = await func(*args, **kwargs)

                    # Check if we should skip caching this result
                    if skip_cache_if and skip_cache_if(result):
                        self.log.debug(
                            "Skipping cache due to skip_cache_if condition", cache_key=cache_key
                        )
                        return result

                    # Store result in cache
                    try:
                        await self.set_json(cache_key, result, ex=ttl)
                        self.log.debug("Cached function result", cache_key=cache_key, ttl=ttl)
                    except Exception:  # noqa: BLE001
                        # Broad exception catch is intentional - cache write failures should not break function
                        self.log.warning("Failed to cache result", cache_key=cache_key)

                    return result

                except Exception:
                    self.log.exception("Function call failed", cache_key=cache_key)
                    raise

            async def invalidate(*args: Any, **kwargs: Any) -> int:
                """Invalidate cached result for specific arguments.

                Args:
                    *args: Positional arguments for cache key generation
                    **kwargs: Keyword arguments for cache key generation

                Returns:
                    Number of keys deleted (0 or 1)
                """
                cache_key = self._generate_cache_key(func, key_prefix, namespace, args, kwargs)
                deleted = await self.delete(cache_key)
                self.log.info("Invalidated cache", cache_key=cache_key, deleted=deleted)
                return deleted

            async def invalidate_all() -> int:
                """Invalidate all cached results for this function.

                Returns:
                    Number of keys deleted
                """
                pattern_parts = []
                if namespace:
                    pattern_parts.append(namespace)
                if key_prefix:
                    pattern_parts.append(key_prefix)
                pattern_parts.append(func.__name__)
                pattern = ":".join(pattern_parts) + "*"

                keys = [k async for k in self._client.scan_iter(match=pattern)]
                if keys:
                    deleted = await self.delete(*keys)
                    self.log.info("Invalidated all cache entries", pattern=pattern, deleted=deleted)
                    return deleted
                return 0

            # Attach invalidation methods to wrapper
            wrapper.invalidate = invalidate  # type: ignore[attr-defined]
            wrapper.invalidate_all = invalidate_all  # type: ignore[attr-defined]

            return wrapper

        return decorator

    def _generate_cache_key(
        self,
        func: Callable[..., Any],
        key_prefix: str | None,
        namespace: str | None,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> str:
        """Generate cache key from function and arguments.

        Args:
            func: Function being cached
            key_prefix: Prefix for cache key
            namespace: Namespace for cache key
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Generated cache key
        """
        parts = []

        # Add namespace
        if namespace is not None:
            parts.append(namespace)

        # Add key prefix
        if key_prefix is not None:
            parts.append(key_prefix)

        # Add function name
        parts.append(func.__name__)

        # Add arguments
        parts.extend(self._serialize_cache_arg(arg) for arg in args)

        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            parts.append(f"{key}={self._serialize_cache_arg(value)}")

        return ":".join(parts)

    def _serialize_cache_arg(self, arg: Any) -> str:
        """Serialize argument for cache key.

        Args:
            arg: Argument to serialize

        Returns:
            Serialized string representation
        """
        if isinstance(arg, str):
            return arg
        if isinstance(arg, (int, float)):
            return str(arg)
        if isinstance(arg, (list, dict)):
            return json.dumps(arg, sort_keys=True)
        return str(arg)

    async def get_or_compute(
        self,
        key: str,
        compute: Callable[[], Any],
        ex: int | None = None,
        serialize_json: bool = True,
    ) -> Any:
        """Get value from cache or compute and store it atomically.

        Args:
            key: Cache key
            compute: Callable to compute value if not cached
            ex: Optional expiration time in seconds
            serialize_json: Whether to serialize/deserialize as JSON

        Returns:
            Cached or computed value

        Example:
            result = redis_service.get_or_compute(
                "user:123",
                lambda: fetch_user_from_db("123"),
                ex=3600
            )
        """
        self.log.debug("Get or compute", key=key, serialize_json=serialize_json)

        # Try to get cached value
        cached = await self.get_json(key) if serialize_json else await self.get(key)

        if cached is not None:
            self.log.debug("Cache hit in get_or_compute", key=key)
            return cached

        # Use SET NX to acquire lock and prevent race condition
        lock_key = f"{key}:lock"
        lock_acquired = await self.set(lock_key, "1", ex=ex or 60, nx=True)

        if not lock_acquired:
            # Another process is computing, wait and retry
            self.log.debug("Lock held by another process in get_or_compute", key=key)
            cached = await self.get_json(key) if serialize_json else await self.get(key)
            if cached is not None:
                return cached

        # Compute the value
        self.log.debug("Computing value", key=key)
        result = compute()

        # Store the computed value
        if serialize_json:
            await self.set_json(key, result, ex=ex)
        else:
            await self.set(key, str(result), ex=ex)

        # Clean up lock
        await self.delete(lock_key)

        self.log.info("Computed and cached value", key=key)
        return result

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        sliding: bool = True,
    ) -> tuple[bool, int]:
        """Check if rate limit is exceeded for a key.

        Args:
            key: Rate limit key (e.g., "user:123:api_calls")
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds
            sliding: Use sliding window (True) or fixed window (False)

        Returns:
            Tuple of (is_allowed, remaining_requests)

        Example:
            # Sliding window (default)
            is_allowed, remaining = redis_service.check_rate_limit(
                "user:123:api",
                max_requests=100,
                window_seconds=3600,
                sliding=True
            )

            # Fixed window
            is_allowed, remaining = redis_service.check_rate_limit(
                "user:123:api",
                max_requests=100,
                window_seconds=3600,
                sliding=False
            )
        """
        self.log.debug(
            "Checking rate limit",
            key=key,
            max_requests=max_requests,
            window_seconds=window_seconds,
            sliding=sliding,
        )

        if sliding:
            return await self._check_rate_limit_sliding(key, max_requests, window_seconds)
        return await self._check_rate_limit_fixed(key, max_requests, window_seconds)

    async def _check_rate_limit_sliding(
        self, key: str, max_requests: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Check rate limit using sliding window with sorted set.

        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            window_seconds: Window size in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - window_seconds

        async with self.pipeline() as pipe:
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current requests in window
            pipe.zcard(key)
            # Add current request timestamp
            pipe.zadd(key, {str(now): now})
            # Set expiration on the sorted set
            pipe.expire(key, window_seconds)
            results = await pipe.execute()

        current_count = results[1]
        remaining = max(0, max_requests - current_count - 1)
        is_allowed = current_count < max_requests

        self.log.info(
            "Sliding window rate limit check",
            key=key,
            current=current_count,
            max=max_requests,
            allowed=is_allowed,
            remaining=remaining,
        )

        return is_allowed, remaining

    async def _check_rate_limit_fixed(
        self, key: str, max_requests: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Check rate limit using fixed window with counter.

        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            window_seconds: Window size in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_count = await self.incr(key, 1)

        # Set expiration only on first request
        if current_count == 1:
            await self.expire(key, window_seconds)

        remaining = max(0, max_requests - current_count)
        is_allowed = current_count <= max_requests

        self.log.info(
            "Fixed window rate limit check",
            key=key,
            current=current_count,
            max=max_requests,
            allowed=is_allowed,
            remaining=remaining,
        )

        return is_allowed, remaining

    async def close(self) -> None:
        """Close the async Redis connection."""
        try:
            await self._client.aclose()
            await self._pool.aclose()
            self.log.info("Async Redis connection closed successfully")
        except Exception:
            self.log.exception("Error closing async Redis connection")
            raise
