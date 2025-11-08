"""Simplified MongoDB service for database operations.

This module provides a clean MongoDB service implementation with:
- Strong typing for all operations
- Transaction support
- Direct MongoDB operations without retry logic
- Health check functionality
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure

if TYPE_CHECKING:
    from pymongo.database import Database
from pymongo.operations import (
    DeleteMany,
    DeleteOne,
    InsertOne,
    ReplaceOne,
    UpdateMany,
    UpdateOne,
)
from pymongo.results import BulkWriteResult, DeleteResult, InsertOneResult, UpdateResult

from lvrgd.common.services.logging_service import LoggingService

from .mongodb_models import MongoConfig


class MongoService:
    """Simplified MongoDB service for database operations."""

    def __init__(
        self,
        logger: LoggingService,
        config: MongoConfig,
    ) -> None:
        """Initialize MongoService.

        Args:
            logger: LoggingService instance for structured logging
            config: MongoDB configuration model
        """
        self.log = logger
        self.config = config

        self.log.info(
            "Initializing MongoDB connection",
            database=config.database,
        )

        # Build connection parameters
        connection_params: dict[str, Any] = {
            "host": config.url,
            "maxPoolSize": config.max_pool_size,
            "minPoolSize": config.min_pool_size,
            "serverSelectionTimeoutMS": config.server_selection_timeout_ms,
            "connectTimeoutMS": config.connect_timeout_ms,
            "retryWrites": config.retry_writes,
            "retryReads": config.retry_reads,
        }

        # Add authentication if provided
        if config.username:
            connection_params["username"] = config.username
        if config.password:
            connection_params["password"] = config.password

        try:
            self._client: MongoClient[dict[str, Any]] = MongoClient(**connection_params)
            self._db: Database[dict[str, Any]] = self._client[config.database]

            # Verify connection
            server_info = self.ping()
            self.log.info(
                "Successfully connected to MongoDB",
                version=server_info.get("version", "unknown"),
            )

        except Exception:
            self.log.exception("Failed to initialize MongoDB connection")
            raise

    def ping(self) -> dict[str, Any]:
        """Ping the MongoDB server to verify connection.

        Returns:
            Server information dictionary

        Raises:
            ConnectionFailure: If unable to connect to MongoDB

        """
        try:
            return self._client.server_info()
        except ConnectionFailure:
            self.log.exception("MongoDB connection failed")
            raise

    def get_collection(self, collection_name: str) -> Collection[dict[str, Any]]:
        """Get a MongoDB collection.

        Args:
            collection_name: Name of the collection

        Returns:
            MongoDB collection instance

        """
        return self._db[collection_name]

    @contextmanager
    def transaction(self) -> Iterator[ClientSession]:
        """Context manager for MongoDB transactions.

        Yields:
            Session for transaction operations

        Example:
            with mongo_service.transaction() as session:
                mongo_service.insert_one("users", {"name": "Alice"}, session=session)
                mongo_service.update_one(
                    "stats", {"_id": 1}, {"$inc": {"count": 1}}, session=session
                )

        """
        self.log.debug("Starting MongoDB transaction")
        session = self._client.start_session()
        try:
            with session.start_transaction():
                self.log.debug("MongoDB transaction started successfully")
                yield session
                self.log.info("MongoDB transaction committed successfully")
        except Exception:
            self.log.exception("MongoDB transaction failed, rolling back")
            raise
        finally:
            session.end_session()
            self.log.debug("MongoDB transaction session ended")

    def insert_one(
        self,
        collection_name: str,
        document: dict[str, Any],
        session: ClientSession | None = None,
    ) -> InsertOneResult:
        """Insert a single document into a collection.

        Args:
            collection_name: Name of the collection
            document: Document to insert
            session: Optional session for transaction support

        Returns:
            Result of the insert operation

        """
        self.log.debug("Inserting document", collection=collection_name)
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document, session=session)
        self.log.info(
            "Successfully inserted document",
            inserted_id=str(result.inserted_id),
            collection=collection_name,
        )
        return result

    def insert_many(
        self,
        collection_name: str,
        documents: list[dict[str, Any]],
        *,
        ordered: bool = True,
        session: ClientSession | None = None,
    ) -> list[ObjectId]:
        """Insert multiple documents into a collection.

        Args:
            collection_name: Name of the collection
            documents: List of documents to insert
            ordered: Whether to stop on first error
            session: Optional session for transaction support

        Returns:
            List of inserted document IDs

        """
        doc_count = len(documents)
        self.log.debug(
            "Inserting documents",
            count=doc_count,
            collection=collection_name,
            ordered=ordered,
        )
        collection = self.get_collection(collection_name)
        result = collection.insert_many(documents, ordered=ordered, session=session)
        self.log.info(
            "Successfully inserted documents",
            count=len(result.inserted_ids),
            collection=collection_name,
        )
        return result.inserted_ids

    def find_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        projection: dict[str, Any] | None = None,
        session: ClientSession | None = None,
    ) -> dict[str, Any] | None:
        """Find a single document in a collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            projection: Fields to include/exclude
            session: Optional session for transaction support

        Returns:
            Found document or None

        """
        self.log.debug(
            "Finding document",
            collection=collection_name,
            query=query,
        )
        collection = self.get_collection(collection_name)
        result = collection.find_one(query, projection, session=session)
        if result:
            self.log.debug(
                "Found document",
                doc_id=str(result.get("_id")),
                collection=collection_name,
            )
        else:
            self.log.debug("No document found", collection=collection_name)
        return result

    def find_many(
        self,
        collection_name: str,
        query: dict[str, Any],
        *,
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 0,
        skip: int = 0,
        session: ClientSession | None = None,
    ) -> list[dict[str, Any]]:
        """Find multiple documents in a collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            projection: Fields to include/exclude
            sort: Sort criteria as list of (field, direction) tuples
            limit: Maximum number of documents to return (0 = no limit)
            skip: Number of documents to skip
            session: Optional session for transaction support

        Returns:
            List of found documents

        """
        self.log.debug(
            "Finding documents",
            collection=collection_name,
            query=query,
            limit=limit,
            skip=skip,
        )
        collection = self.get_collection(collection_name)
        cursor = collection.find(query, projection, session=session)

        if sort:
            cursor = cursor.sort(sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)

        results = list(cursor)
        self.log.info(
            "Found documents",
            count=len(results),
            collection=collection_name,
        )
        return results

    def update_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
        session: ClientSession | None = None,
    ) -> UpdateResult:
        """Update a single document in a collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            update: Update operations
            upsert: Create document if it doesn't exist
            session: Optional session for transaction support

        Returns:
            Result of the update operation

        """
        self.log.debug(
            "Updating document",
            collection=collection_name,
            query=query,
            upsert=upsert,
        )
        collection = self.get_collection(collection_name)
        result = collection.update_one(query, update, upsert=upsert, session=session)
        self.log.info(
            "Updated document",
            modified=result.modified_count,
            collection=collection_name,
            matched=result.matched_count,
            upserted_id=str(result.upserted_id) if result.upserted_id else None,
        )
        return result

    def update_many(
        self,
        collection_name: str,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
        session: ClientSession | None = None,
    ) -> UpdateResult:
        """Update multiple documents in a collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            update: Update operations
            upsert: Create documents if they don't exist
            session: Optional session for transaction support

        Returns:
            Result of the update operation

        """
        self.log.debug(
            "Updating multiple documents",
            collection=collection_name,
            query=query,
            upsert=upsert,
        )
        collection = self.get_collection(collection_name)
        result = collection.update_many(query, update, upsert=upsert, session=session)
        self.log.info(
            "Updated documents",
            modified=result.modified_count,
            collection=collection_name,
            matched=result.matched_count,
        )
        return result

    def delete_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        session: ClientSession | None = None,
    ) -> DeleteResult:
        """Delete a single document from a collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            session: Optional session for transaction support

        Returns:
            Result of the delete operation

        """
        self.log.debug(
            "Deleting document",
            collection=collection_name,
            query=query,
        )
        collection = self.get_collection(collection_name)
        result = collection.delete_one(query, session=session)
        self.log.info(
            "Deleted document",
            deleted=result.deleted_count,
            collection=collection_name,
        )
        return result

    def delete_many(
        self,
        collection_name: str,
        query: dict[str, Any],
        session: ClientSession | None = None,
    ) -> DeleteResult:
        """Delete multiple documents from a collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            session: Optional session for transaction support

        Returns:
            Result of the delete operation

        """
        self.log.debug(
            "Deleting multiple documents",
            collection=collection_name,
            query=query,
        )
        collection = self.get_collection(collection_name)
        result = collection.delete_many(query, session=session)
        self.log.info(
            "Deleted documents",
            deleted=result.deleted_count,
            collection=collection_name,
        )
        return result

    def count_documents(
        self,
        collection_name: str,
        query: dict[str, Any],
        session: ClientSession | None = None,
    ) -> int:
        """Count documents in a collection that match a query.

        Args:
            collection_name: Name of the collection
            query: Query filter
            session: Optional session for transaction support

        Returns:
            Number of matching documents

        """
        self.log.debug(
            "Counting documents",
            collection=collection_name,
            query=query,
        )
        collection = self.get_collection(collection_name)
        count = collection.count_documents(query, session=session)
        self.log.debug(
            "Found matching documents",
            count=count,
            collection=collection_name,
        )
        return count

    def aggregate(
        self,
        collection_name: str,
        pipeline: list[dict[str, Any]],
        session: ClientSession | None = None,
    ) -> list[dict[str, Any]]:
        """Perform an aggregation pipeline on a collection.

        Args:
            collection_name: Name of the collection
            pipeline: Aggregation pipeline stages
            session: Optional session for transaction support

        Returns:
            Result of the aggregation

        """
        pipeline_stages = len(pipeline)
        self.log.debug(
            "Running aggregation",
            collection=collection_name,
            stages=pipeline_stages,
        )
        collection = self.get_collection(collection_name)
        results = list(collection.aggregate(pipeline, session=session))
        self.log.info(
            "Aggregation completed",
            collection=collection_name,
            results=len(results),
        )
        return results

    def create_index(
        self,
        collection_name: str,
        keys: str | list[tuple[str, int]],
        *,
        unique: bool = False,
        **kwargs: Any,
    ) -> str:
        """Create an index on a collection.

        Args:
            collection_name: Name of the collection
            keys: Index specification (field name or list of (field, direction) tuples)
            unique: Whether the index should be unique
            **kwargs: Additional index options

        Returns:
            Name of the created index

        """
        self.log.debug(
            "Creating index",
            collection=collection_name,
            keys=keys,
            unique=unique,
        )
        collection = self.get_collection(collection_name)
        index_name = collection.create_index(keys, unique=unique, **kwargs)
        self.log.info(
            "Successfully created index",
            index_name=index_name,
            collection=collection_name,
        )
        return index_name

    def bulk_write(
        self,
        collection_name: str,
        operations: list[
            InsertOne[dict[str, Any]]
            | UpdateOne
            | UpdateMany
            | DeleteOne
            | DeleteMany
            | ReplaceOne[dict[str, Any]]
        ],
        *,
        ordered: bool = True,
        session: ClientSession | None = None,
    ) -> BulkWriteResult:
        """Execute multiple write operations in a single request.

        Args:
            collection_name: Name of the collection
            operations: List of bulk operations
            ordered: Whether operations should be executed in order
            session: Optional session for transaction support

        Returns:
            Result of the bulk write operation

        """
        operation_count = len(operations)
        self.log.debug(
            "Executing bulk write",
            operations=operation_count,
            collection=collection_name,
            ordered=ordered,
        )
        collection = self.get_collection(collection_name)
        result = collection.bulk_write(operations, ordered=ordered, session=session)
        self.log.info(
            "Bulk write completed",
            collection=collection_name,
            inserted=result.inserted_count,
            matched=result.matched_count,
            modified=result.modified_count,
            deleted=result.deleted_count,
            upserted=result.upserted_count,
        )
        return result

    def close(self) -> None:
        """Close the MongoDB connection."""
        try:
            self._client.close()
            self.log.info("MongoDB connection closed successfully")
        except Exception:
            self.log.exception("Error closing MongoDB connection")
            raise
