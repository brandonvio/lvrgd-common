"""Async MongoDB service for database operations.

This module provides a clean async MongoDB service implementation with:
- Strong typing for all operations
- Transaction support
- Direct MongoDB operations without retry logic
- Health check functionality
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from bson.objectid import ObjectId
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pydantic import BaseModel
from pymongo.errors import ConnectionFailure
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

T = TypeVar("T", bound=BaseModel)


class AsyncMongoService:
    """Async MongoDB service for database operations."""

    def __init__(
        self,
        logger: LoggingService,
        config: MongoConfig,
    ) -> None:
        """Initialize AsyncMongoService.

        Args:
            logger: LoggingService instance for structured logging
            config: MongoDB configuration model
        """
        self.log = logger
        self.config = config

        self.log.info(
            "Initializing async MongoDB connection",
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
            self._client: AsyncIOMotorClient[dict[str, Any]] = AsyncIOMotorClient(
                **connection_params
            )
            self._db: AsyncIOMotorDatabase[dict[str, Any]] = self._client[config.database]

            self.log.info(
                "Async MongoDB client initialized",
                database=config.database,
            )

        except Exception:
            self.log.exception("Failed to initialize async MongoDB connection")
            raise

    async def ping(self) -> dict[str, Any]:
        """Ping the MongoDB server to verify connection.

        Returns:
            Server information dictionary

        Raises:
            ConnectionFailure: If unable to connect to MongoDB

        """
        try:
            return await self._client.server_info()
        except ConnectionFailure:
            self.log.exception("Async MongoDB connection failed")
            raise

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection[dict[str, Any]]:
        """Get an async MongoDB collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Async MongoDB collection instance

        """
        return self._db[collection_name]

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncIOMotorClientSession]:
        """Context manager for async MongoDB transactions.

        Yields:
            Session for transaction operations

        Example:
            async with mongo_service.transaction() as session:
                await mongo_service.insert_one("users", {"name": "Alice"}, session=session)
                await mongo_service.update_one(
                    "stats", {"_id": 1}, {"$inc": {"count": 1}}, session=session
                )

        """
        self.log.debug("Starting async MongoDB transaction")
        session = await self._client.start_session()
        try:
            async with session.start_transaction():
                self.log.debug("Async MongoDB transaction started successfully")
                yield session
                self.log.info("Async MongoDB transaction committed successfully")
        except Exception:
            self.log.exception("Async MongoDB transaction failed, rolling back")
            raise
        finally:
            await session.end_session()
            self.log.debug("Async MongoDB transaction session ended")

    async def insert_one(
        self,
        collection_name: str,
        document: dict[str, Any],
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.insert_one(document, session=session)
        self.log.info(
            "Successfully inserted document",
            inserted_id=str(result.inserted_id),
            collection=collection_name,
        )
        return result

    async def insert_many(
        self,
        collection_name: str,
        documents: list[dict[str, Any]],
        *,
        ordered: bool = True,
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.insert_many(documents, ordered=ordered, session=session)
        self.log.info(
            "Successfully inserted documents",
            count=len(result.inserted_ids),
            collection=collection_name,
        )
        return result.inserted_ids

    async def find_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        projection: dict[str, Any] | None = None,
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.find_one(query, projection, session=session)
        if result:
            self.log.debug(
                "Found document",
                doc_id=str(result.get("_id")),
                collection=collection_name,
            )
        else:
            self.log.debug("No document found", collection=collection_name)
        return result

    async def find_many(
        self,
        collection_name: str,
        query: dict[str, Any],
        *,
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 0,
        skip: int = 0,
        session: AsyncIOMotorClientSession | None = None,
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

        results = await cursor.to_list(length=None)
        self.log.info(
            "Found documents",
            count=len(results),
            collection=collection_name,
        )
        return results

    async def update_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.update_one(query, update, upsert=upsert, session=session)
        self.log.info(
            "Updated document",
            modified=result.modified_count,
            collection=collection_name,
            matched=result.matched_count,
            upserted_id=str(result.upserted_id) if result.upserted_id else None,
        )
        return result

    async def update_many(
        self,
        collection_name: str,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.update_many(query, update, upsert=upsert, session=session)
        self.log.info(
            "Updated documents",
            modified=result.modified_count,
            collection=collection_name,
            matched=result.matched_count,
        )
        return result

    async def delete_one(
        self,
        collection_name: str,
        query: dict[str, Any],
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.delete_one(query, session=session)
        self.log.info(
            "Deleted document",
            deleted=result.deleted_count,
            collection=collection_name,
        )
        return result

    async def delete_many(
        self,
        collection_name: str,
        query: dict[str, Any],
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.delete_many(query, session=session)
        self.log.info(
            "Deleted documents",
            deleted=result.deleted_count,
            collection=collection_name,
        )
        return result

    async def count_documents(
        self,
        collection_name: str,
        query: dict[str, Any],
        session: AsyncIOMotorClientSession | None = None,
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
        count = await collection.count_documents(query, session=session)
        self.log.debug(
            "Found matching documents",
            count=count,
            collection=collection_name,
        )
        return count

    async def aggregate(
        self,
        collection_name: str,
        pipeline: list[dict[str, Any]],
        session: AsyncIOMotorClientSession | None = None,
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
        cursor = collection.aggregate(pipeline, session=session)
        results = await cursor.to_list(length=None)
        self.log.info(
            "Aggregation completed",
            collection=collection_name,
            results=len(results),
        )
        return results

    async def create_index(
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
        index_name = await collection.create_index(keys, unique=unique, **kwargs)
        self.log.info(
            "Successfully created index",
            index_name=index_name,
            collection=collection_name,
        )
        return index_name

    async def bulk_write(
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
        session: AsyncIOMotorClientSession | None = None,
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
        result = await collection.bulk_write(operations, ordered=ordered, session=session)
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

    async def find_one_model(
        self,
        collection_name: str,
        query: dict[str, Any],
        model_class: type[T],
        projection: dict[str, Any] | None = None,
        session: AsyncIOMotorClientSession | None = None,
    ) -> T | None:
        """Find single document and deserialize to Pydantic model.

        Args:
            collection_name: Name of the collection
            query: Query filter
            model_class: Pydantic model class to deserialize into
            projection: Fields to include/exclude
            session: Optional session for transaction support

        Returns:
            Validated Pydantic model instance, or None if not found

        Raises:
            ValidationError: If document doesn't match model schema
        """
        self.log.debug(
            "Finding document as model", collection=collection_name, model=model_class.__name__
        )
        doc = await self.find_one(collection_name, query, projection, session)

        if doc is None:
            return None

        result = model_class.model_validate(doc)
        self.log.debug(
            "Successfully validated model", collection=collection_name, model=model_class.__name__
        )
        return result

    async def insert_one_model(
        self,
        collection_name: str,
        model: BaseModel,
        session: AsyncIOMotorClientSession | None = None,
    ) -> InsertOneResult:
        """Insert a Pydantic model as a document.

        Args:
            collection_name: Name of the collection
            model: Pydantic model instance to insert
            session: Optional session for transaction support

        Returns:
            Result of the insert operation
        """
        self.log.debug("Inserting model", collection=collection_name, model=type(model).__name__)
        document = model.model_dump()
        result = await self.insert_one(collection_name, document, session)
        self.log.debug(
            "Successfully inserted model", collection=collection_name, model=type(model).__name__
        )
        return result

    async def find_many_models(
        self,
        collection_name: str,
        query: dict[str, Any],
        model_class: type[T],
        *,
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 0,
        skip: int = 0,
        session: AsyncIOMotorClientSession | None = None,
    ) -> list[T]:
        """Find multiple documents and deserialize to Pydantic models.

        Args:
            collection_name: Name of the collection
            query: Query filter
            model_class: Pydantic model class to deserialize into
            projection: Fields to include/exclude
            sort: Sort criteria as list of (field, direction) tuples
            limit: Maximum number of documents to return (0 = no limit)
            skip: Number of documents to skip
            session: Optional session for transaction support

        Returns:
            List of validated Pydantic model instances

        Raises:
            ValidationError: If any document doesn't match model schema
        """
        self.log.debug(
            "Finding documents as models", collection=collection_name, model=model_class.__name__
        )
        docs = await self.find_many(
            collection_name,
            query,
            projection=projection,
            sort=sort,
            limit=limit,
            skip=skip,
            session=session,
        )
        results = [model_class.model_validate(doc) for doc in docs]
        self.log.debug(
            "Successfully validated models",
            collection=collection_name,
            model=model_class.__name__,
            count=len(results),
        )
        return results

    async def insert_many_models(
        self,
        collection_name: str,
        models: list[BaseModel],
        *,
        ordered: bool = True,
        session: AsyncIOMotorClientSession | None = None,
    ) -> list[ObjectId]:
        """Insert multiple Pydantic models as documents.

        Args:
            collection_name: Name of the collection
            models: List of Pydantic model instances to insert
            ordered: Whether to stop on first error
            session: Optional session for transaction support

        Returns:
            List of inserted document IDs
        """
        self.log.debug("Inserting models", collection=collection_name, count=len(models))
        documents = [model.model_dump() for model in models]
        result = await self.insert_many(
            collection_name, documents, ordered=ordered, session=session
        )
        self.log.debug(
            "Successfully inserted models", collection=collection_name, count=len(result)
        )
        return result

    async def update_one_model(
        self,
        collection_name: str,
        query: dict[str, Any],
        model: BaseModel,
        *,
        upsert: bool = False,
        session: AsyncIOMotorClientSession | None = None,
    ) -> UpdateResult:
        """Update a single document using a Pydantic model.

        Args:
            collection_name: Name of the collection
            query: Query filter
            model: Pydantic model instance with update data
            upsert: Create document if it doesn't exist
            session: Optional session for transaction support

        Returns:
            Result of the update operation
        """
        self.log.debug(
            "Updating document with model", collection=collection_name, model=type(model).__name__
        )
        update = {"$set": model.model_dump()}
        result = await self.update_one(
            collection_name, query, update, upsert=upsert, session=session
        )
        self.log.debug(
            "Successfully updated with model",
            collection=collection_name,
            model=type(model).__name__,
        )
        return result

    async def update_many_models(
        self,
        collection_name: str,
        query: dict[str, Any],
        model: BaseModel,
        *,
        upsert: bool = False,
        session: AsyncIOMotorClientSession | None = None,
    ) -> UpdateResult:
        """Update multiple documents using a Pydantic model.

        Args:
            collection_name: Name of the collection
            query: Query filter
            model: Pydantic model instance with update data
            upsert: Create documents if they don't exist
            session: Optional session for transaction support

        Returns:
            Result of the update operation
        """
        self.log.debug(
            "Updating documents with model", collection=collection_name, model=type(model).__name__
        )
        update = {"$set": model.model_dump()}
        result = await self.update_many(
            collection_name, query, update, upsert=upsert, session=session
        )
        self.log.debug(
            "Successfully updated documents with model",
            collection=collection_name,
            model=type(model).__name__,
        )
        return result

    async def close(self) -> None:
        """Close the async MongoDB connection."""
        try:
            self._client.close()
            self.log.info("Async MongoDB connection closed successfully")
        except Exception:
            self.log.exception("Error closing async MongoDB connection")
            raise
