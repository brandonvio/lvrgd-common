"""Enhanced MongoDB service with comprehensive error handling and monitoring.

This module provides a robust MongoDB service implementation with features including:
- Automatic retry logic for transient failures
- Connection pooling and health checks
- Transaction support
- Performance metrics collection
- Bulk operations
- Pagination and aggregation utilities
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union, Iterator, Tuple
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult, BulkWriteResult
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
    AutoReconnect,
    NetworkTimeout,
    PyMongoError,
)
from pymongo.client_session import ClientSession
from pymongo.operations import (
    InsertOne,
    UpdateOne,
    UpdateMany,
    DeleteOne,
    DeleteMany,
    ReplaceOne,
)
from bson.objectid import ObjectId
from dataclasses import dataclass

from .mongodb_models import MongoConfig


@dataclass
class OperationMetrics:
    """Metrics for database operations."""

    operation: str
    collection: str
    duration_ms: float
    documents_affected: int
    success: bool
    error: Optional[str] = None


@dataclass
class HealthCheck:
    """Database health check result."""

    is_healthy: bool
    response_time_ms: float
    server_info: Dict[str, Any]
    error: Optional[str] = None


class MongoOperationError(Exception):
    """Custom exception for MongoDB operation errors with retry context."""

    def __init__(
        self, message: str, operation: str, attempts: int, original_error: Exception
    ):
        super().__init__(message)
        self.operation = operation
        self.attempts = attempts
        self.original_error = original_error


class MongoService:
    """Enhanced MongoDB service with transactions, retries, bulk operations, and monitoring."""

    def __init__(
        self,
        logger: logging.Logger,
        config: MongoConfig,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize MongoService with enhanced features.

        Args:
            logger (logging.Logger): Standard Python logger instance
            config (MongoConfig): MongoDB configuration model
            max_retries (int): Maximum retry attempts for failed operations
            retry_delay (float): Base delay in seconds between retries
        """
        self.log = logger
        self.config = config
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._metrics: List[OperationMetrics] = []

        self.log.info(
            f"Initializing enhanced MongoDB connection to database: {config.database}"
        )

        # Build connection parameters
        connection_params = {
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
            self._client = MongoClient(**connection_params)
            self._db: Database = self._client[config.database]

            # Verify connection
            health = self.health_check()
            if not health.is_healthy:
                raise ConnectionFailure(f"Failed to connect to MongoDB: {health.error}")

            self.log.info(
                f"Successfully connected to MongoDB. Server info: {health.server_info.get('version', 'unknown')}"
            )

        except Exception as e:
            self.log.error(f"Failed to initialize MongoDB connection: {e}")
            raise

    def _record_metrics(
        self,
        operation: str,
        collection: str,
        duration_ms: float,
        documents_affected: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Record operation metrics for monitoring."""
        metrics = OperationMetrics(
            operation=operation,
            collection=collection,
            duration_ms=duration_ms,
            documents_affected=documents_affected,
            success=success,
            error=error,
        )
        self._metrics.append(metrics)

        if success:
            self.log.debug(
                f"{operation} on {collection}: {documents_affected} docs in {duration_ms:.2f}ms"
            )
        else:
            self.log.warning(
                f"{operation} on {collection} failed after {duration_ms:.2f}ms: {error}"
            )

    def _execute_with_retry(
        self, operation_name: str, operation_func, collection_name: str
    ) -> Any:
        """Execute operation with retry logic and metrics tracking."""
        last_exception = None
        start_time = time.time()

        for attempt in range(self.max_retries + 1):
            try:
                result = operation_func()
                duration_ms = (time.time() - start_time) * 1000

                # Count affected documents based on result type
                documents_affected = 0
                if hasattr(result, "inserted_id"):
                    documents_affected = 1
                elif hasattr(result, "inserted_ids"):
                    documents_affected = len(result.inserted_ids)
                elif hasattr(result, "modified_count"):
                    documents_affected = result.modified_count
                elif hasattr(result, "deleted_count"):
                    documents_affected = result.deleted_count
                elif isinstance(result, list):
                    documents_affected = len(result)

                self._record_metrics(
                    operation_name,
                    collection_name,
                    duration_ms,
                    documents_affected,
                    True,
                )
                return result

            except (AutoReconnect, NetworkTimeout, ServerSelectionTimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    self.log.warning(
                        f"{operation_name} attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    break
            except (ConnectionFailure, OperationFailure, PyMongoError) as e:
                # Don't retry these errors
                last_exception = e
                break

        # All retries failed
        duration_ms = (time.time() - start_time) * 1000
        self._record_metrics(
            operation_name, collection_name, duration_ms, 0, False, str(last_exception)
        )

        raise MongoOperationError(
            f"{operation_name} failed after {self.max_retries + 1} attempts",
            operation_name,
            self.max_retries + 1,
            last_exception,
        )

    def get_collection(self, collection_name: str) -> Collection:
        """Get a MongoDB collection.

        Args:
            collection_name (str): Name of the collection

        Returns:
            Collection: MongoDB collection instance
        """
        return self._db[collection_name]

    def health_check(self) -> HealthCheck:
        """Perform a health check on the MongoDB connection.

        Returns:
            HealthCheck: Health check result with timing and server info
        """
        start_time = time.time()
        try:
            server_info = self._client.server_info()
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                is_healthy=True,
                response_time_ms=response_time_ms,
                server_info=server_info,
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                is_healthy=False,
                response_time_ms=response_time_ms,
                server_info={},
                error=str(e),
            )

    @contextmanager
    def transaction(self) -> Iterator[ClientSession]:
        """Context manager for MongoDB transactions.

        Yields:
            ClientSession: Session for transaction operations

        Example:
            with mongo_service.transaction() as session:
                mongo_service.insert_one("users", {"name": "Alice"}, session=session)
                mongo_service.update_one("stats", {"_id": 1}, {"$inc": {"count": 1}}, session=session)
        """
        session = self._client.start_session()
        try:
            with session.start_transaction():
                self.log.debug("Started MongoDB transaction")
                yield session
                self.log.debug("Committing MongoDB transaction")
        except Exception as e:
            self.log.error(f"Transaction failed, rolling back: {e}")
            raise
        finally:
            session.end_session()

    def insert_one(
        self,
        collection_name: str,
        document: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> InsertOneResult:
        """Insert a single document into a collection.

        Args:
            collection_name (str): Name of the collection
            document (Dict[str, Any]): Document to insert
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            InsertOneResult: Result of the insert operation with proper type
        """

        def _insert():
            collection = self.get_collection(collection_name)
            return collection.insert_one(document, session=session)

        return self._execute_with_retry("insert_one", _insert, collection_name)

    def insert_many(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        session: Optional[ClientSession] = None,
        ordered: bool = True,
    ) -> List[ObjectId]:
        """Insert multiple documents into a collection.

        Args:
            collection_name (str): Name of the collection
            documents (List[Dict[str, Any]]): List of documents to insert
            session (Optional[ClientSession]): Session for transaction support
            ordered (bool): Whether to stop on first error

        Returns:
            List[ObjectId]: List of inserted document IDs
        """

        def _insert():
            collection = self.get_collection(collection_name)
            result = collection.insert_many(documents, session=session, ordered=ordered)
            return result.inserted_ids

        return self._execute_with_retry("insert_many", _insert, collection_name)

    def find_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        session: Optional[ClientSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find a single document in a collection.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            projection (Optional[Dict[str, Any]], optional): Fields to include/exclude. Defaults to None.
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            Optional[Dict[str, Any]]: Found document or None with ObjectId converted to string
        """

        def _find():
            collection = self.get_collection(collection_name)
            doc = collection.find_one(query, projection, session=session)
            if doc and "_id" in doc:
                doc["_id"] = str(doc["_id"])
            return doc

        return self._execute_with_retry("find_one", _find, collection_name)

    def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        session: Optional[ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents in a collection.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            projection (Optional[Dict[str, Any]], optional): Fields to include/exclude. Defaults to None.
            sort (Optional[List[tuple]], optional): Sort criteria. Defaults to None.
            limit (Optional[int], optional): Maximum number of documents to return. Defaults to None.
            skip (Optional[int], optional): Number of documents to skip. Defaults to None.
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            List[Dict[str, Any]]: List of found documents with ObjectIds converted to strings
        """

        def _find():
            collection = self.get_collection(collection_name)
            cursor = collection.find(query, projection, session=session)

            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)

            # Convert cursor to list and ObjectId to string for JSON serialization
            documents = list(cursor)
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            return documents

        return self._execute_with_retry("find_many", _find, collection_name)

    def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        session: Optional[ClientSession] = None,
    ) -> UpdateResult:
        """Update a single document in a collection.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            update (Dict[str, Any]): Update operations
            upsert (bool, optional): Create document if it doesn't exist. Defaults to False.
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            UpdateResult: Result of the update operation
        """

        def _update():
            collection = self.get_collection(collection_name)
            return collection.update_one(query, update, upsert=upsert, session=session)

        return self._execute_with_retry("update_one", _update, collection_name)

    def update_one_by_id(
        self,
        collection_name: str,
        id: str,
        update: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> UpdateResult:
        """Update a single document in a collection by ID.

        Args:
            collection_name (str): Name of the collection
            id (str): ID of the document
            update (Dict[str, Any]): Update operations
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            UpdateResult: Result of the update operation
        """

        def _update():
            collection = self.get_collection(collection_name)
            return collection.update_one({"_id": ObjectId(id)}, update, session=session)

        return self._execute_with_retry("update_one_by_id", _update, collection_name)

    def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        session: Optional[ClientSession] = None,
    ) -> UpdateResult:
        """Update multiple documents in a collection.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            update (Dict[str, Any]): Update operations
            upsert (bool, optional): Create documents if they don't exist. Defaults to False.
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            UpdateResult: Result of the update operation
        """

        def _update():
            collection = self.get_collection(collection_name)
            return collection.update_many(query, update, upsert=upsert, session=session)

        return self._execute_with_retry("update_many", _update, collection_name)

    def delete_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> DeleteResult:
        """Delete a single document from a collection.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            DeleteResult: Result of the delete operation
        """

        def _delete():
            collection = self.get_collection(collection_name)
            return collection.delete_one(query, session=session)

        return self._execute_with_retry("delete_one", _delete, collection_name)

    def delete_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> DeleteResult:
        """Delete multiple documents from a collection.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            DeleteResult: Result of the delete operation
        """

        def _delete():
            collection = self.get_collection(collection_name)
            return collection.delete_many(query, session=session)

        return self._execute_with_retry("delete_many", _delete, collection_name)

    def count_documents(
        self,
        collection_name: str,
        query: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> int:
        """Count documents in a collection that match a query.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            int: Number of matching documents
        """

        def _count():
            collection = self.get_collection(collection_name)
            return collection.count_documents(query, session=session)

        return self._execute_with_retry("count_documents", _count, collection_name)

    def aggregate(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]],
        session: Optional[ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Perform an aggregation pipeline on a collection.

        Args:
            collection_name (str): Name of the collection
            pipeline (List[Dict[str, Any]]): Aggregation pipeline stages
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            List[Dict[str, Any]]: Result of the aggregation with ObjectIds converted to strings
        """

        def _aggregate():
            collection = self.get_collection(collection_name)
            results = list(collection.aggregate(pipeline, session=session))

            # Convert ObjectIds to strings for JSON serialization
            for doc in results:
                if "_id" in doc and isinstance(doc["_id"], ObjectId):
                    doc["_id"] = str(doc["_id"])

            return results

        return self._execute_with_retry("aggregate", _aggregate, collection_name)

    def create_index(
        self,
        collection_name: str,
        keys: Union[str, List[tuple]],
        unique: bool = False,
    ) -> str:
        """Create an index on a collection.

        Args:
            collection_name (str): Name of the collection
            keys (Union[str, List[tuple]]): Index specification
            unique (bool, optional): Whether the index should be unique. Defaults to False.

        Returns:
            str: Name of the created index
        """

        def _create_index():
            collection = self.get_collection(collection_name)
            return collection.create_index(keys, unique=unique)

        return self._execute_with_retry("create_index", _create_index, collection_name)

    # Bulk Operations
    def bulk_write(
        self,
        collection_name: str,
        operations: List[
            Union[InsertOne, UpdateOne, UpdateMany, DeleteOne, DeleteMany, ReplaceOne]
        ],
        ordered: bool = True,
        session: Optional[ClientSession] = None,
    ) -> BulkWriteResult:
        """Execute multiple write operations in a single request.

        Args:
            collection_name (str): Name of the collection
            operations (List): List of bulk operations
            ordered (bool): Whether operations should be executed in order
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            BulkWriteResult: Result of the bulk write operation
        """

        def _bulk_write():
            collection = self.get_collection(collection_name)
            return collection.bulk_write(operations, ordered=ordered, session=session)

        return self._execute_with_retry("bulk_write", _bulk_write, collection_name)

    def bulk_insert(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        ordered: bool = True,
        session: Optional[ClientSession] = None,
    ) -> BulkWriteResult:
        """Bulk insert multiple documents.

        Args:
            collection_name (str): Name of the collection
            documents (List[Dict[str, Any]]): Documents to insert
            ordered (bool): Whether to stop on first error
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            BulkWriteResult: Result of the bulk insert operation
        """
        operations = [InsertOne(doc) for doc in documents]
        return self.bulk_write(
            collection_name, operations, ordered=ordered, session=session
        )

    # Enhanced Aggregation Utilities
    def paginate(
        self,
        collection_name: str,
        query: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
        sort: Optional[List[tuple]] = None,
        projection: Optional[Dict[str, Any]] = None,
        session: Optional[ClientSession] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Paginate query results with total count.

        Args:
            collection_name (str): Name of the collection
            query (Dict[str, Any]): Query filter
            page (int): Page number (1-based)
            page_size (int): Number of documents per page
            sort (Optional[List[tuple]]): Sort criteria
            projection (Optional[Dict[str, Any]]): Fields to include/exclude
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            Tuple[List[Dict[str, Any]], int]: (documents, total_count)
        """
        skip = (page - 1) * page_size
        documents = self.find_many(
            collection_name,
            query,
            projection=projection,
            sort=sort,
            limit=page_size,
            skip=skip,
            session=session,
        )
        total_count = self.count_documents(collection_name, query, session=session)
        return documents, total_count

    def aggregate_with_facets(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]],
        facets: Dict[str, List[Dict[str, Any]]],
        session: Optional[ClientSession] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform aggregation with multiple faceted outputs.

        Args:
            collection_name (str): Name of the collection
            pipeline (List[Dict[str, Any]]): Base aggregation pipeline
            facets (Dict[str, List[Dict[str, Any]]]): Named facet pipelines
            session (Optional[ClientSession]): Session for transaction support

        Returns:
            Dict[str, List[Dict[str, Any]]]: Faceted results
        """
        full_pipeline = pipeline + [{"$facet": facets}]
        result = self.aggregate(collection_name, full_pipeline, session=session)
        return result[0] if result else {}

    # Monitoring and Analytics
    def get_metrics(self, clear_after_read: bool = False) -> List[OperationMetrics]:
        """Get collected operation metrics.

        Args:
            clear_after_read (bool): Whether to clear metrics after reading

        Returns:
            List[OperationMetrics]: List of operation metrics
        """
        metrics = self._metrics.copy()
        if clear_after_read:
            self._metrics.clear()
        return metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics.

        Returns:
            Dict[str, Any]: Performance summary statistics
        """
        if not self._metrics:
            return {"total_operations": 0}

        successful_ops = [m for m in self._metrics if m.success]
        failed_ops = [m for m in self._metrics if not m.success]

        avg_duration = (
            sum(m.duration_ms for m in successful_ops) / len(successful_ops)
            if successful_ops
            else 0
        )
        total_docs = sum(m.documents_affected for m in successful_ops)

        operations_by_type = {}
        for metric in self._metrics:
            op_type = metric.operation
            if op_type not in operations_by_type:
                operations_by_type[op_type] = {
                    "count": 0,
                    "avg_duration_ms": 0,
                    "total_docs": 0,
                }

            ops = [m for m in successful_ops if m.operation == op_type]
            if ops:
                operations_by_type[op_type]["count"] = len(ops)
                operations_by_type[op_type]["avg_duration_ms"] = sum(
                    m.duration_ms for m in ops
                ) / len(ops)
                operations_by_type[op_type]["total_docs"] = sum(
                    m.documents_affected for m in ops
                )

        return {
            "total_operations": len(self._metrics),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "average_duration_ms": round(avg_duration, 2),
            "total_documents_affected": total_docs,
            "operations_by_type": operations_by_type,
            "error_rate": len(failed_ops) / len(self._metrics) if self._metrics else 0,
        }

    def close(self) -> None:
        """Close the MongoDB connection and cleanup resources."""
        try:
            self._client.close()
            self.log.info("MongoDB connection closed successfully")
        except Exception as e:
            self.log.error(f"Error closing MongoDB connection: {e}")
