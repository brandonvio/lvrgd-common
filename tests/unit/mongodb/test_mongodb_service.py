"""Test suite for simplified MongoDB service implementation.

This module contains tests for the MongoDB service including:
- Connection initialization and configuration
- CRUD operations with logging
- Transaction handling
- Error handling
- Bulk operations
- Aggregation operations
"""

import logging
from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock, patch

import pytest
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo.results import BulkWriteResult, DeleteResult, InsertOneResult, UpdateResult

from lvrgd.common.services.mongodb.mongodb_models import MongoConfig
from lvrgd.common.services.mongodb.mongodb_service import MongoService

# ruff: noqa: S101  # assert usage in tests is acceptable
# ruff: noqa: SLF001  # accessing private members in tests is acceptable
# ruff: noqa: ARG001,ARG002  # unused arguments in fixtures/test methods are expected
# ruff: noqa: S106  # hardcoded passwords in tests are acceptable
# ruff: noqa: FBT003  # boolean literals in function calls ok in tests
# ruff: noqa: PLC0415  # imports in functions acceptable in tests


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger for testing."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def valid_config() -> MongoConfig:
    """Create a valid MongoDB configuration for testing."""
    return MongoConfig(
        url="mongodb://localhost:27017",
        database="test_db",
        username="test_user",
        password="test_pass",
        max_pool_size=50,
        min_pool_size=5,
        server_selection_timeout_ms=30000,
        connect_timeout_ms=10000,
    )


@pytest.fixture
def config_without_auth() -> MongoConfig:
    """Create a MongoDB configuration without authentication."""
    return MongoConfig(
        url="mongodb://localhost:27017",
        database="test_db",
        username=None,
        password=None,
        max_pool_size=100,
        min_pool_size=0,
        server_selection_timeout_ms=30000,
        connect_timeout_ms=10000,
    )


@pytest.fixture
def mock_mongo_client() -> Iterator[Mock]:
    """Create a mock MongoDB client."""
    with patch("services.mongodb.mongodb_service.MongoClient") as mock_client:
        yield mock_client


@pytest.fixture
def mongo_service(
    mock_logger: Mock,
    valid_config: MongoConfig,
    mock_mongo_client: Mock,
) -> MongoService:
    """Create a MongoService instance with mocked dependencies."""
    # Mock ping method to avoid actual connection during init
    with patch.object(MongoService, "ping") as mock_ping:
        mock_ping.return_value = {"version": "5.0.0"}
        service = MongoService(mock_logger, valid_config)

        # Set up the database mock properly to be subscriptable
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        service._db = mock_db  # type: ignore[attr-defined]

        return service


class TestMongoServiceInitialization:
    """Test MongoDB service initialization."""

    def test_init_with_auth(
        self,
        mock_logger: Mock,
        valid_config: MongoConfig,
        mock_mongo_client: Mock,
    ) -> None:
        """Test initialization with authentication."""
        with patch.object(MongoService, "ping") as mock_ping:
            mock_ping.return_value = {"version": "5.0.0"}
            service = MongoService(mock_logger, valid_config)

            mock_logger.info.assert_any_call(
                "Initializing MongoDB connection to database: %s",
                valid_config.database,
            )

            expected_params: dict[str, Any] = {
                "host": valid_config.url,
                "maxPoolSize": valid_config.max_pool_size,
                "minPoolSize": valid_config.min_pool_size,
                "serverSelectionTimeoutMS": valid_config.server_selection_timeout_ms,
                "connectTimeoutMS": valid_config.connect_timeout_ms,
                "retryWrites": valid_config.retry_writes,
                "retryReads": valid_config.retry_reads,
                "username": valid_config.username,
                "password": valid_config.password,
            }

            mock_mongo_client.assert_called_once_with(**expected_params)
            assert service.config == valid_config
            assert service.log == mock_logger

    def test_init_without_auth(
        self,
        mock_logger: Mock,
        config_without_auth: MongoConfig,
        mock_mongo_client: Mock,
    ) -> None:
        """Test initialization without authentication."""
        with patch.object(MongoService, "ping") as mock_ping:
            mock_ping.return_value = {"version": "5.0.0"}
            service = MongoService(mock_logger, config_without_auth)

            expected_params: dict[str, Any] = {
                "host": config_without_auth.url,
                "maxPoolSize": config_without_auth.max_pool_size,
                "minPoolSize": config_without_auth.min_pool_size,
                "serverSelectionTimeoutMS": (config_without_auth.server_selection_timeout_ms),
                "connectTimeoutMS": config_without_auth.connect_timeout_ms,
                "retryWrites": config_without_auth.retry_writes,
                "retryReads": config_without_auth.retry_reads,
            }

            mock_mongo_client.assert_called_once_with(**expected_params)
            assert service.config == config_without_auth

    def test_init_connection_failure(
        self,
        mock_logger: Mock,
        valid_config: MongoConfig,
        mock_mongo_client: Mock,
    ) -> None:
        """Test initialization when connection fails."""
        with patch.object(MongoService, "ping") as mock_ping:
            mock_ping.side_effect = ConnectionFailure("Connection failed")

            with pytest.raises(ConnectionFailure):
                MongoService(mock_logger, valid_config)


class TestPingMethod:
    """Test ping functionality."""

    def test_ping_success(self, mongo_service: MongoService) -> None:
        """Test successful ping."""
        server_info: dict[str, Any] = {"version": "5.0.0", "modules": []}
        # Configure the mock to return server_info when server_info() is called
        mongo_service._client.server_info = Mock(return_value=server_info)  # type: ignore[attr-defined]

        result = mongo_service.ping()

        assert result == server_info
        mongo_service._client.server_info.assert_called_once()  # type: ignore[attr-defined]

    def test_ping_failure(self, mongo_service: MongoService) -> None:
        """Test ping failure."""
        mongo_service._client.server_info = Mock(  # type: ignore[attr-defined]
            side_effect=ConnectionFailure("Connection failed"),
        )

        with pytest.raises(ConnectionFailure):
            mongo_service.ping()

        mongo_service.log.exception.assert_called_once_with("MongoDB connection failed")  # type: ignore[attr-defined]


class TestGetCollection:
    """Test get_collection method."""

    def test_get_collection(self, mongo_service: MongoService) -> None:
        """Test getting a collection."""
        collection_name = "test_collection"

        collection = mongo_service.get_collection(collection_name)

        mongo_service._db.__getitem__.assert_called_once_with(collection_name)  # type: ignore[attr-defined]
        assert collection == mongo_service._db[collection_name]  # type: ignore[attr-defined]


class TestTransactions:
    """Test transaction functionality."""

    def test_transaction_context_manager(self, mongo_service: MongoService) -> None:
        """Test transaction context manager."""
        mock_session = Mock()
        mock_session.start_transaction.return_value.__enter__ = Mock(return_value=None)
        mock_session.start_transaction.return_value.__exit__ = Mock(return_value=None)
        mongo_service._client.start_session = Mock(return_value=mock_session)  # type: ignore[attr-defined]

        with mongo_service.transaction() as session:
            assert session == mock_session

        mock_session.start_transaction.assert_called_once()
        mock_session.end_session.assert_called_once()
        mongo_service.log.debug.assert_any_call("Starting MongoDB transaction")  # type: ignore[attr-defined]
        mongo_service.log.debug.assert_any_call(  # type: ignore[attr-defined]
            "MongoDB transaction started successfully",
        )
        mongo_service.log.info.assert_any_call(  # type: ignore[attr-defined]
            "MongoDB transaction committed successfully",
        )

    def test_transaction_rollback_on_error(self, mongo_service: MongoService) -> None:
        """Test transaction rollback on error."""
        mock_session = Mock()
        mock_transaction_context = Mock()
        mock_transaction_context.__enter__ = Mock(
            side_effect=Exception("Transaction error"),
        )
        mock_transaction_context.__exit__ = Mock()
        mock_session.start_transaction.return_value = mock_transaction_context
        mongo_service._client.start_session = Mock(return_value=mock_session)  # type: ignore[attr-defined]

        with (
            pytest.raises(Exception, match="Transaction error"),
            mongo_service.transaction(),
        ):
            pass

        mock_session.end_session.assert_called_once()
        mongo_service.log.exception.assert_called_once_with(  # type: ignore[attr-defined]
            "MongoDB transaction failed, rolling back",
        )


class TestInsertOperations:
    """Test insert operations with logging."""

    def test_insert_one_success(self, mongo_service: MongoService) -> None:
        """Test successful single document insertion."""
        collection_name = "test_collection"
        document: dict[str, Any] = {"name": "test", "value": 123}
        inserted_id = ObjectId()

        mock_collection = Mock()
        mock_result = Mock(spec=InsertOneResult)
        mock_result.inserted_id = inserted_id
        mock_collection.insert_one.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.insert_one(collection_name, document)

        mock_collection.insert_one.assert_called_once_with(document, session=None)
        assert result == mock_result

        # Verify logging
        mongo_service.log.debug.assert_called_with(  # type: ignore[attr-defined]
            "Inserting document into collection: %s",
            collection_name,
        )
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "Successfully inserted document with ID %s into collection: %s",
            inserted_id,
            collection_name,
        )

    def test_insert_many_success(self, mongo_service: MongoService) -> None:
        """Test successful multiple document insertion."""
        collection_name = "test_collection"
        documents = [{"name": "test1"}, {"name": "test2"}]
        inserted_ids = [ObjectId(), ObjectId()]

        mock_collection = Mock()
        mock_result = Mock()
        mock_result.inserted_ids = inserted_ids
        mock_collection.insert_many.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.insert_many(collection_name, documents)

        mock_collection.insert_many.assert_called_once_with(
            documents,
            ordered=True,
            session=None,
        )
        assert result == inserted_ids

        # Verify logging
        mongo_service.log.debug.assert_called_with(  # type: ignore[attr-defined]
            "Inserting %d documents into collection: %s (ordered=%s)",
            2,
            collection_name,
            True,
        )


class TestFindOperations:
    """Test find operations with logging."""

    def test_find_one_success(self, mongo_service: MongoService) -> None:
        """Test successful single document find."""
        collection_name = "test_collection"
        query = {"name": "test"}
        projection = {"_id": 0}
        expected_doc: dict[str, Any] = {"_id": ObjectId(), "name": "test", "value": 123}

        mock_collection = Mock()
        mock_collection.find_one.return_value = expected_doc
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.find_one(collection_name, query, projection)

        mock_collection.find_one.assert_called_once_with(
            query,
            projection,
            session=None,
        )
        assert result == expected_doc

        # Verify logging
        mongo_service.log.debug.assert_any_call(  # type: ignore[attr-defined]
            "Finding document in collection: %s with query: %s",
            collection_name,
            query,
        )

    def test_find_one_not_found(self, mongo_service: MongoService) -> None:
        """Test find_one when document is not found."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}

        mock_collection = Mock()
        mock_collection.find_one.return_value = None
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.find_one(collection_name, query)

        assert result is None
        mongo_service.log.debug.assert_any_call(  # type: ignore[attr-defined]
            "No document found in collection: %s",
            collection_name,
        )

    def test_find_many_success(self, mongo_service: MongoService) -> None:
        """Test successful multiple document find."""
        collection_name = "test_collection"
        query = {"status": "active"}
        projection = {"_id": 1, "name": 1}
        sort = [("name", 1)]
        limit = 10
        skip = 5

        mock_docs = [{"name": "test1"}, {"name": "test2"}]
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter(mock_docs))

        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.find_many(
            collection_name,
            query,
            projection=projection,
            sort=sort,
            limit=limit,
            skip=skip,
        )

        mock_collection.find.assert_called_once_with(query, projection, session=None)
        mock_cursor.sort.assert_called_once_with(sort)
        mock_cursor.skip.assert_called_once_with(skip)
        mock_cursor.limit.assert_called_once_with(limit)
        assert result == mock_docs

        # Verify logging
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "Found %d documents in collection: %s",
            2,
            collection_name,
        )


class TestUpdateOperations:
    """Test update operations with logging."""

    def test_update_one_success(self, mongo_service: MongoService) -> None:
        """Test successful single document update."""
        collection_name = "test_collection"
        query = {"name": "test"}
        update = {"$set": {"value": 456}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 1
        mock_result.matched_count = 1
        mock_result.upserted_id = None
        mock_collection = Mock()
        mock_collection.update_one.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.update_one(collection_name, query, update)

        mock_collection.update_one.assert_called_once_with(
            query,
            update,
            upsert=False,
            session=None,
        )
        assert result == mock_result

        # Verify logging
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "Updated %d document(s) in collection: %s (matched=%d, upserted_id=%s)",
            1,
            collection_name,
            1,
            None,
        )

    def test_update_many_success(self, mongo_service: MongoService) -> None:
        """Test successful multiple document update."""
        collection_name = "test_collection"
        query = {"status": "inactive"}
        update = {"$set": {"status": "active"}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 5
        mock_result.matched_count = 5
        mock_collection = Mock()
        mock_collection.update_many.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.update_many(collection_name, query, update)

        mock_collection.update_many.assert_called_once_with(
            query,
            update,
            upsert=False,
            session=None,
        )
        assert result == mock_result


class TestDeleteOperations:
    """Test delete operations with logging."""

    def test_delete_one_success(self, mongo_service: MongoService) -> None:
        """Test successful single document deletion."""
        collection_name = "test_collection"
        query = {"name": "test"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 1
        mock_collection = Mock()
        mock_collection.delete_one.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.delete_one(collection_name, query)

        mock_collection.delete_one.assert_called_once_with(query, session=None)
        assert result == mock_result

        # Verify logging
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "Deleted %d document(s) from collection: %s",
            1,
            collection_name,
        )

    def test_delete_many_success(self, mongo_service: MongoService) -> None:
        """Test successful multiple document deletion."""
        collection_name = "test_collection"
        query = {"status": "expired"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 3
        mock_collection = Mock()
        mock_collection.delete_many.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.delete_many(collection_name, query)

        mock_collection.delete_many.assert_called_once_with(query, session=None)
        assert result == mock_result


class TestAggregationOperations:
    """Test aggregation operations with logging."""

    def test_count_documents_success(self, mongo_service: MongoService) -> None:
        """Test successful document count."""
        collection_name = "test_collection"
        query = {"status": "active"}
        expected_count = 42

        mock_collection = Mock()
        mock_collection.count_documents.return_value = expected_count
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.count_documents(collection_name, query)

        mock_collection.count_documents.assert_called_once_with(query, session=None)
        assert result == expected_count

        # Verify logging
        mongo_service.log.debug.assert_any_call(  # type: ignore[attr-defined]
            "Found %d documents matching query in collection: %s",
            expected_count,
            collection_name,
        )

    def test_aggregate_success(self, mongo_service: MongoService) -> None:
        """Test successful aggregation pipeline."""
        collection_name = "test_collection"
        pipeline: list[dict[str, Any]] = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        ]
        expected_result: list[dict[str, Any]] = [
            {"_id": "electronics", "count": 10},
            {"_id": "books", "count": 5},
        ]

        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(expected_result))
        mock_collection = Mock()
        mock_collection.aggregate.return_value = mock_cursor
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.aggregate(collection_name, pipeline)

        mock_collection.aggregate.assert_called_once_with(pipeline, session=None)
        assert result == expected_result

        # Verify logging
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "Aggregation completed on collection: %s, returned %d results",
            collection_name,
            2,
        )


class TestIndexOperations:
    """Test index operations with logging."""

    def test_create_index_simple(self, mongo_service: MongoService) -> None:
        """Test creating a simple index."""
        collection_name = "test_collection"
        keys = "name"
        expected_index_name = "name_1"

        mock_collection = Mock()
        mock_collection.create_index.return_value = expected_index_name
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.create_index(collection_name, keys)

        mock_collection.create_index.assert_called_once_with(keys, unique=False)
        assert result == expected_index_name

        # Verify logging
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "Successfully created index '%s' on collection: %s",
            expected_index_name,
            collection_name,
        )

    def test_create_index_compound_unique(self, mongo_service: MongoService) -> None:
        """Test creating a compound unique index."""
        collection_name = "test_collection"
        keys = [("name", 1), ("email", 1)]
        expected_index_name = "name_1_email_1"

        mock_collection = Mock()
        mock_collection.create_index.return_value = expected_index_name
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.create_index(collection_name, keys, unique=True)

        mock_collection.create_index.assert_called_once_with(keys, unique=True)
        assert result == expected_index_name


class TestBulkOperations:
    """Test bulk operations with logging."""

    def test_bulk_write_success(self, mongo_service: MongoService) -> None:
        """Test successful bulk write operation."""
        from pymongo.operations import DeleteOne, InsertOne, UpdateOne

        collection_name = "test_collection"
        operations = [  # type: ignore[var-annotated]
            InsertOne({"name": "doc1"}),
            UpdateOne({"_id": 1}, {"$set": {"updated": True}}),
            DeleteOne({"_id": 2}),
        ]

        mock_collection = Mock()
        mock_result = Mock(spec=BulkWriteResult)
        mock_result.inserted_count = 1
        mock_result.matched_count = 1
        mock_result.modified_count = 1
        mock_result.deleted_count = 1
        mock_result.upserted_count = 0
        mock_collection.bulk_write.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.bulk_write(collection_name, operations)  # type: ignore[arg-type]

        mock_collection.bulk_write.assert_called_once_with(
            operations,
            ordered=True,
            session=None,
        )
        assert result == mock_result

        # Verify logging
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "Bulk write completed on collection: %s - "
            "inserted: %d, matched: %d, modified: %d, deleted: %d, upserted: %d",
            collection_name,
            1,
            1,
            1,
            1,
            0,
        )


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_connection_failure_during_operation(
        self,
        mongo_service: MongoService,
    ) -> None:
        """Test handling of connection failures during operations."""
        collection_name = "test_collection"
        document = {"name": "test"}

        mock_collection = Mock()
        mock_collection.insert_one.side_effect = ConnectionFailure("Connection lost")
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        with pytest.raises(ConnectionFailure):
            mongo_service.insert_one(collection_name, document)

    def test_operation_failure_on_insert(self, mongo_service: MongoService) -> None:
        """Test handling of operation failures during insert."""
        collection_name = "test_collection"
        document = {"name": "test"}

        mock_collection = Mock()
        mock_collection.insert_one.side_effect = OperationFailure("Insert failed")
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        with pytest.raises(OperationFailure):
            mongo_service.insert_one(collection_name, document)

    def test_close_connection(self, mongo_service: MongoService) -> None:
        """Test closing MongoDB connection."""
        mongo_service.close()
        mongo_service._client.close.assert_called_once()  # type: ignore[attr-defined,misc]
        mongo_service.log.info.assert_called_with(  # type: ignore[attr-defined]
            "MongoDB connection closed successfully",
        )

    def test_close_connection_with_error(self, mongo_service: MongoService) -> None:
        """Test error handling when closing connection fails."""
        mongo_service._client.close.side_effect = Exception("Close failed")  # type: ignore[attr-defined,misc]

        with pytest.raises(Exception, match="Close failed"):
            mongo_service.close()

        mongo_service.log.exception.assert_called_with(  # type: ignore[attr-defined]
            "Error closing MongoDB connection",
        )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_find_many_empty_result(self, mongo_service: MongoService) -> None:
        """Test find_many with empty result set."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}

        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([]))
        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.find_many(collection_name, query)

        assert result == []

    def test_update_operations_no_matches(self, mongo_service: MongoService) -> None:
        """Test update operations when no documents match."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}
        update = {"$set": {"value": 123}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 0
        mock_result.matched_count = 0
        mock_result.upserted_id = None
        mock_collection = Mock()
        mock_collection.update_one.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.update_one(collection_name, query, update)

        assert result.modified_count == 0
        assert result.matched_count == 0

    def test_delete_operations_no_matches(self, mongo_service: MongoService) -> None:
        """Test delete operations when no documents match."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 0
        mock_collection = Mock()
        mock_collection.delete_one.return_value = mock_result
        mongo_service._db.__getitem__ = Mock(return_value=mock_collection)  # type: ignore[attr-defined]

        result = mongo_service.delete_one(collection_name, query)

        assert result.deleted_count == 0
