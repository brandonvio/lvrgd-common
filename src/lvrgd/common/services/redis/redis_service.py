"""Simplified Redis service for caching and data operations.

This module provides a clean Redis service implementation with:
- Strong typing for all operations
- Common Redis operations (get, set, delete, expire, etc.)
- Pub/Sub support
- Vector search capabilities
- Health check functionality
"""

from __future__ import annotations

import struct
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from redis import ConnectionPool, Redis
from redis.commands.search.field import NumericField, TagField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError

from lvrgd.common.services.logging_service import LoggingService

from .redis_models import RedisConfig


class RedisService:
    """Simplified Redis service for caching and data operations."""

    def __init__(
        self,
        logger: LoggingService,
        config: RedisConfig,
    ) -> None:
        """Initialize RedisService.

        Args:
            logger: LoggingService instance for structured logging
            config: Redis configuration model
        """
        self.log = logger
        self.config = config

        self.log.info(
            "Initializing Redis connection",
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

            # Verify connection
            self.ping()
            self.log.info("Successfully connected to Redis")

        except Exception:
            self.log.exception("Failed to initialize Redis connection")
            raise

    def ping(self) -> bool:
        """Ping the Redis server to verify connection.

        Returns:
            True if connection is successful

        Raises:
            RedisConnectionError: If unable to connect to Redis
        """
        try:
            result = self._client.ping()
            self.log.debug("Redis ping successful")
            return result
        except RedisConnectionError:
            self.log.exception("Redis connection failed")
            raise

    def get(self, key: str) -> str | None:
        """Get value for a key.

        Args:
            key: Key to retrieve

        Returns:
            Value associated with key, or None if key doesn't exist
        """
        self.log.debug("Getting value", key=key)
        value = self._client.get(key)
        if value:
            self.log.debug("Found value", key=key)
        else:
            self.log.debug("Key not found", key=key)
        return value

    def set(
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
            key: Key to set
            value: Value to set
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key already exists

        Returns:
            True if operation was successful
        """
        self.log.debug(
            "Setting value",
            key=key,
            ex=ex,
            px=px,
            nx=nx,
            xx=xx,
        )
        result = self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        self.log.info("Successfully set value", key=key)
        return bool(result)

    def delete(self, *keys: str) -> int:
        """Delete one or more keys.

        Args:
            *keys: Keys to delete

        Returns:
            Number of keys that were deleted
        """
        self.log.debug("Deleting keys", count=len(keys))
        result = self._client.delete(*keys)
        self.log.info("Successfully deleted keys", deleted=result)
        return result

    def exists(self, *keys: str) -> int:
        """Check if one or more keys exist.

        Args:
            *keys: Keys to check

        Returns:
            Number of keys that exist
        """
        self.log.debug("Checking key existence", count=len(keys))
        result = self._client.exists(*keys)
        self.log.debug("Keys existence check", exists=result)
        return result

    def expire(self, key: str, seconds: int) -> bool:
        """Set a timeout on key.

        Args:
            key: Key to set timeout on
            seconds: Timeout in seconds

        Returns:
            True if timeout was set, False if key doesn't exist
        """
        self.log.debug("Setting expiration", key=key, seconds=seconds)
        result = self._client.expire(key, seconds)
        self.log.info("Successfully set expiration", key=key, result=result)
        return bool(result)

    def ttl(self, key: str) -> int:
        """Get the time to live for a key.

        Args:
            key: Key to check

        Returns:
            TTL in seconds, -1 if key exists but has no expire, -2 if key doesn't exist
        """
        self.log.debug("Getting TTL", key=key)
        result = self._client.ttl(key)
        self.log.debug("TTL retrieved", key=key, ttl=result)
        return result

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment the integer value of a key.

        Args:
            key: Key to increment
            amount: Amount to increment by (default: 1)

        Returns:
            Value of key after increment
        """
        self.log.debug("Incrementing key", key=key, amount=amount)
        result = self._client.incr(key, amount)
        self.log.info("Successfully incremented key", key=key, new_value=result)
        return result

    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement the integer value of a key.

        Args:
            key: Key to decrement
            amount: Amount to decrement by (default: 1)

        Returns:
            Value of key after decrement
        """
        self.log.debug("Decrementing key", key=key, amount=amount)
        result = self._client.decr(key, amount)
        self.log.info("Successfully decremented key", key=key, new_value=result)
        return result

    def hget(self, name: str, key: str) -> str | None:
        """Get value from hash field.

        Args:
            name: Hash name
            key: Field key

        Returns:
            Value associated with field, or None if field doesn't exist
        """
        self.log.debug("Getting hash field", hash=name, key=key)
        value = self._client.hget(name, key)
        if value:
            self.log.debug("Found hash field", hash=name, key=key)
        else:
            self.log.debug("Hash field not found", hash=name, key=key)
        return value

    def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field to value.

        Args:
            name: Hash name
            key: Field key
            value: Field value

        Returns:
            Number of fields that were added (0 if field existed and was updated)
        """
        self.log.debug("Setting hash field", hash=name, key=key)
        result = self._client.hset(name, key, value)
        self.log.info("Successfully set hash field", hash=name, key=key, added=result)
        return result

    def hgetall(self, name: str) -> dict[str, str]:
        """Get all fields and values in a hash.

        Args:
            name: Hash name

        Returns:
            Dictionary of field-value pairs
        """
        self.log.debug("Getting all hash fields", hash=name)
        result = self._client.hgetall(name)
        self.log.info("Retrieved hash fields", hash=name, count=len(result))
        return result

    def hdel(self, name: str, *keys: str) -> int:
        """Delete one or more hash fields.

        Args:
            name: Hash name
            *keys: Field keys to delete

        Returns:
            Number of fields that were deleted
        """
        self.log.debug("Deleting hash fields", hash=name, count=len(keys))
        result = self._client.hdel(name, *keys)
        self.log.info("Successfully deleted hash fields", hash=name, deleted=result)
        return result

    def lpush(self, name: str, *values: str) -> int:
        """Push values to the head of the list.

        Args:
            name: List name
            *values: Values to push

        Returns:
            Length of the list after push
        """
        self.log.debug("Pushing to list head", list=name, count=len(values))
        result = self._client.lpush(name, *values)
        self.log.info("Successfully pushed to list", list=name, length=result)
        return result

    def rpush(self, name: str, *values: str) -> int:
        """Push values to the tail of the list.

        Args:
            name: List name
            *values: Values to push

        Returns:
            Length of the list after push
        """
        self.log.debug("Pushing to list tail", list=name, count=len(values))
        result = self._client.rpush(name, *values)
        self.log.info("Successfully pushed to list", list=name, length=result)
        return result

    def lpop(self, name: str) -> str | None:
        """Remove and return the first element of the list.

        Args:
            name: List name

        Returns:
            Value of the first element, or None if list is empty
        """
        self.log.debug("Popping from list head", list=name)
        value = self._client.lpop(name)
        if value:
            self.log.info("Successfully popped from list", list=name)
        else:
            self.log.debug("List is empty", list=name)
        return value

    def rpop(self, name: str) -> str | None:
        """Remove and return the last element of the list.

        Args:
            name: List name

        Returns:
            Value of the last element, or None if list is empty
        """
        self.log.debug("Popping from list tail", list=name)
        value = self._client.rpop(name)
        if value:
            self.log.info("Successfully popped from list", list=name)
        else:
            self.log.debug("List is empty", list=name)
        return value

    def lrange(self, name: str, start: int, end: int) -> list[str]:
        """Get a range of elements from the list.

        Args:
            name: List name
            start: Start index
            end: End index

        Returns:
            List of elements in the specified range
        """
        self.log.debug("Getting list range", list=name, start=start, end=end)
        result = self._client.lrange(name, start, end)
        self.log.info("Retrieved list range", list=name, count=len(result))
        return result

    def sadd(self, name: str, *values: str) -> int:
        """Add members to a set.

        Args:
            name: Set name
            *values: Members to add

        Returns:
            Number of members that were added (excluding already existing members)
        """
        self.log.debug("Adding to set", set=name, count=len(values))
        result = self._client.sadd(name, *values)
        self.log.info("Successfully added to set", set=name, added=result)
        return result

    def smembers(self, name: str) -> set[str]:
        """Get all members of a set.

        Args:
            name: Set name

        Returns:
            Set of all members
        """
        self.log.debug("Getting set members", set=name)
        result = self._client.smembers(name)
        self.log.info("Retrieved set members", set=name, count=len(result))
        return result

    def srem(self, name: str, *values: str) -> int:
        """Remove members from a set.

        Args:
            name: Set name
            *values: Members to remove

        Returns:
            Number of members that were removed
        """
        self.log.debug("Removing from set", set=name, count=len(values))
        result = self._client.srem(name, *values)
        self.log.info("Successfully removed from set", set=name, removed=result)
        return result

    def zadd(self, name: str, mapping: dict[str, float], nx: bool = False, xx: bool = False) -> int:
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
        result = self._client.zadd(name, mapping, nx=nx, xx=xx)
        self.log.info("Successfully added to sorted set", zset=name, added=result)
        return result

    def zrange(
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
        result = self._client.zrange(name, start, end, desc=desc, withscores=withscores)
        self.log.info("Retrieved sorted set range", zset=name, count=len(result))
        return result

    def zrem(self, name: str, *values: str) -> int:
        """Remove members from a sorted set.

        Args:
            name: Sorted set name
            *values: Members to remove

        Returns:
            Number of members that were removed
        """
        self.log.debug("Removing from sorted set", zset=name, count=len(values))
        result = self._client.zrem(name, *values)
        self.log.info("Successfully removed from sorted set", zset=name, removed=result)
        return result

    @contextmanager
    def pipeline(self, transaction: bool = True) -> Iterator[Any]:
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

    def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers that received the message
        """
        self.log.debug("Publishing message", channel=channel)
        result = self._client.publish(channel, message)
        self.log.info("Successfully published message", channel=channel, subscribers=result)
        return result

    @contextmanager
    def subscribe(self, *channels: str) -> Iterator[Any]:
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
            pubsub.subscribe(*channels)
            self.log.info("Successfully subscribed to channels", channels=channels)
            yield pubsub
        finally:
            pubsub.unsubscribe()
            pubsub.close()
            self.log.debug("Unsubscribed from channels", channels=channels)

    def create_vector_index(
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
            self._client.ft(index_name).create_index(fields=schema, definition=definition)
            self.log.info(
                "Successfully created vector index",
                index_name=index_name,
                fields=len(schema),
            )
        except ResponseError:
            self.log.exception("Failed to create vector index", index_name=index_name)
            raise

    def vector_search(
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
            results = self._client.ft(index_name).search(
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

    def drop_index(self, index_name: str, delete_documents: bool = False) -> None:
        """Drop a search index.

        Args:
            index_name: Name of the index to drop
            delete_documents: Whether to delete the documents as well

        Raises:
            ResponseError: If index deletion fails
        """
        self.log.debug("Dropping index", index_name=index_name, delete_documents=delete_documents)
        try:
            self._client.ft(index_name).dropindex(delete_documents=delete_documents)
            self.log.info("Successfully dropped index", index_name=index_name)
        except ResponseError:
            self.log.exception("Failed to drop index", index_name=index_name)
            raise

    def close(self) -> None:
        """Close the Redis connection."""
        try:
            self._client.close()
            self._pool.disconnect()
            self.log.info("Redis connection closed successfully")
        except Exception:
            self.log.exception("Error closing Redis connection")
            raise
