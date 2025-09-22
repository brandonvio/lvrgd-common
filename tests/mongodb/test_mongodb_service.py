import logging
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from bson.objectid import ObjectId
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    AutoReconnect,
    NetworkTimeout,
)
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult, BulkWriteResult
from pymongo.operations import InsertOne, UpdateOne, DeleteOne

from mongodb.mongodb_service import (
    MongoService,
    MongoOperationError,
    OperationMetrics,
    HealthCheck,
)
from mongodb.mongodb_models import MongoConfig


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def valid_config():
    """Create a valid MongoDB configuration for testing."""
    return MongoConfig(
        url="mongodb://localhost:27017",
        database="test_db",
        username="test_user",
        password="test_pass",
        max_pool_size=50,
        min_pool_size=5,
    )


@pytest.fixture
def config_without_auth():
    """Create a MongoDB configuration without authentication."""
    return MongoConfig(url="mongodb://localhost:27017", database="test_db")


@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoDB client."""
    with patch("mongodb.mongodb_service.MongoClient") as mock_client:
        yield mock_client


@pytest.fixture
def mongo_service(mock_logger, valid_config, mock_mongo_client):
    """Create a MongoService instance with mocked dependencies."""
    # Mock health check to avoid actual connection during init
    with patch.object(MongoService, "health_check") as mock_health:
        mock_health.return_value = HealthCheck(
            is_healthy=True, response_time_ms=10.0, server_info={"version": "5.0.0"}
        )
        return MongoService(mock_logger, valid_config, max_retries=1, retry_delay=0.1)


class TestMongoServiceInitialization:
    """Test MongoDB service initialization."""

    def test_init_with_auth(self, mock_logger, valid_config, mock_mongo_client):
        """Test initialization with authentication."""
        with patch.object(MongoService, "health_check") as mock_health:
            mock_health.return_value = HealthCheck(
                is_healthy=True, response_time_ms=10.0, server_info={"version": "5.0.0"}
            )
            service = MongoService(mock_logger, valid_config)

            mock_logger.info.assert_any_call(
                f"Initializing enhanced MongoDB connection to database: {valid_config.database}"
            )

            expected_params = {
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
            assert service.max_retries == 3  # default value

    def test_init_without_auth(
        self, mock_logger, config_without_auth, mock_mongo_client
    ):
        """Test initialization without authentication."""
        with patch.object(MongoService, "health_check") as mock_health:
            mock_health.return_value = HealthCheck(
                is_healthy=True, response_time_ms=10.0, server_info={"version": "5.0.0"}
            )
            service = MongoService(mock_logger, config_without_auth)

            expected_params = {
                "host": config_without_auth.url,
                "maxPoolSize": config_without_auth.max_pool_size,
                "minPoolSize": config_without_auth.min_pool_size,
                "serverSelectionTimeoutMS": config_without_auth.server_selection_timeout_ms,
                "connectTimeoutMS": config_without_auth.connect_timeout_ms,
                "retryWrites": config_without_auth.retry_writes,
                "retryReads": config_without_auth.retry_reads,
            }

            mock_mongo_client.assert_called_once_with(**expected_params)

    def test_init_health_check_failure(
        self, mock_logger, valid_config, mock_mongo_client
    ):
        """Test initialization when health check fails."""
        with patch.object(MongoService, "health_check") as mock_health:
            mock_health.return_value = HealthCheck(
                is_healthy=False,
                response_time_ms=5000.0,
                server_info={},
                error="Connection timeout",
            )
            with pytest.raises(ConnectionFailure, match="Failed to connect to MongoDB"):
                MongoService(mock_logger, valid_config)


class TestHealthCheck:
    """Test health check functionality."""

    def test_health_check_success(self, mongo_service):
        """Test successful health check."""
        server_info = {"version": "5.0.0", "modules": []}
        mongo_service._client.server_info.return_value = server_info

        result = mongo_service.health_check()

        assert result.is_healthy is True
        assert result.response_time_ms > 0
        assert result.server_info == server_info
        assert result.error is None

    def test_health_check_failure(self, mongo_service):
        """Test health check failure."""
        mongo_service._client.server_info.side_effect = ConnectionFailure(
            "Connection failed"
        )

        result = mongo_service.health_check()

        assert result.is_healthy is False
        assert result.response_time_ms > 0
        assert result.server_info == {}
        assert "Connection failed" in result.error


class TestGetCollection:
    """Test get_collection method."""

    def test_get_collection(self, mongo_service):
        """Test getting a collection."""
        collection_name = "test_collection"

        collection = mongo_service.get_collection(collection_name)

        mongo_service._db.__getitem__.assert_called_once_with(collection_name)
        assert collection == mongo_service._db[collection_name]


class TestTransactions:
    """Test transaction functionality."""

    def test_transaction_context_manager(self, mongo_service):
        """Test transaction context manager."""
        mock_session = Mock()
        mock_session.start_transaction.return_value.__enter__ = Mock(return_value=None)
        mock_session.start_transaction.return_value.__exit__ = Mock(return_value=None)
        mongo_service._client.start_session.return_value = mock_session

        with mongo_service.transaction() as session:
            assert session == mock_session

        mock_session.start_transaction.assert_called_once()
        mock_session.end_session.assert_called_once()

    def test_transaction_rollback_on_error(self, mongo_service):
        """Test transaction rollback on error."""
        mock_session = Mock()
        mock_transaction_context = Mock()
        mock_transaction_context.__enter__ = Mock(side_effect=Exception("Transaction error"))
        mock_transaction_context.__exit__ = Mock()
        mock_session.start_transaction.return_value = mock_transaction_context
        mongo_service._client.start_session.return_value = mock_session

        with pytest.raises(Exception, match="Transaction error"):
            with mongo_service.transaction() as session:
                pass

        mock_session.end_session.assert_called_once()


class TestInsertOperations:
    """Test insert operations."""

    def test_insert_one_success(self, mongo_service):
        """Test successful single document insertion."""
        collection_name = "test_collection"
        document = {"name": "test", "value": 123}
        inserted_id = ObjectId()

        mock_collection = Mock()
        mock_result = Mock(spec=InsertOneResult)
        mock_result.inserted_id = inserted_id
        mock_collection.insert_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.insert_one(collection_name, document)

        mock_collection.insert_one.assert_called_once_with(document, session=None)
        assert result == mock_result  # Now returns InsertOneResult, not string

    def test_insert_many_success(self, mongo_service):
        """Test successful multiple document insertion."""
        collection_name = "test_collection"
        documents = [{"name": "test1"}, {"name": "test2"}]
        inserted_ids = [ObjectId(), ObjectId()]

        mock_collection = Mock()
        mock_result = Mock()
        mock_result.inserted_ids = inserted_ids
        mock_collection.insert_many.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.insert_many(collection_name, documents)

        mock_collection.insert_many.assert_called_once_with(
            documents, session=None, ordered=True
        )
        assert result == inserted_ids


class TestFindOperations:
    """Test find operations."""

    def test_find_one_success(self, mongo_service):
        """Test successful single document find."""
        collection_name = "test_collection"
        query = {"name": "test"}
        projection = {"_id": 0}
        expected_doc = {"name": "test", "value": 123}

        mock_collection = Mock()
        mock_collection.find_one.return_value = expected_doc
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.find_one(collection_name, query, projection)

        mock_collection.find_one.assert_called_once_with(query, projection, session=None)
        assert result == expected_doc

    def test_find_one_not_found(self, mongo_service):
        """Test find_one when document is not found."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}

        mock_collection = Mock()
        mock_collection.find_one.return_value = None
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.find_one(collection_name, query)

        assert result is None

    def test_find_many_success(self, mongo_service):
        """Test successful multiple document find."""
        collection_name = "test_collection"
        query = {"status": "active"}
        projection = {"_id": 1, "name": 1}
        sort = [("name", 1)]
        limit = 10
        skip = 5

        doc1_id = ObjectId()
        doc2_id = ObjectId()
        mock_docs = [
            {"_id": doc1_id, "name": "test1"},
            {"_id": doc2_id, "name": "test2"},
        ]

        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter(mock_docs))

        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.find_many(
            collection_name, query, projection, sort, limit, skip
        )

        mock_collection.find.assert_called_once_with(query, projection, session=None)
        mock_cursor.sort.assert_called_once_with(sort)
        mock_cursor.skip.assert_called_once_with(skip)
        mock_cursor.limit.assert_called_once_with(limit)

        expected_result = [
            {"_id": str(doc1_id), "name": "test1"},
            {"_id": str(doc2_id), "name": "test2"},
        ]
        assert result == expected_result

    def test_find_many_no_options(self, mongo_service):
        """Test find_many without sort, limit, or skip."""
        collection_name = "test_collection"
        query = {"status": "active"}

        mock_docs = [{"name": "test1"}, {"name": "test2"}]
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(mock_docs))

        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.find_many(collection_name, query)

        mock_cursor.sort.assert_not_called()
        mock_cursor.skip.assert_not_called()
        mock_cursor.limit.assert_not_called()
        assert result == mock_docs


class TestUpdateOperations:
    """Test update operations."""

    def test_update_one_success(self, mongo_service):
        """Test successful single document update."""
        collection_name = "test_collection"
        query = {"name": "test"}
        update = {"$set": {"value": 456}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 1
        mock_collection = Mock()
        mock_collection.update_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.update_one(collection_name, query, update)

        mock_collection.update_one.assert_called_once_with(query, update, upsert=False, session=None)
        assert result == mock_result

    def test_update_one_with_upsert(self, mongo_service):
        """Test update_one with upsert enabled."""
        collection_name = "test_collection"
        query = {"name": "test"}
        update = {"$set": {"value": 456}}

        mock_result = Mock(spec=UpdateResult)
        mock_collection = Mock()
        mock_collection.update_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.update_one(collection_name, query, update, upsert=True)

        mock_collection.update_one.assert_called_once_with(query, update, upsert=True, session=None)

    def test_update_one_by_id_success(self, mongo_service):
        """Test successful update by ID."""
        collection_name = "test_collection"
        doc_id = str(ObjectId())
        update = {"$set": {"value": 789}}

        mock_result = Mock(spec=UpdateResult)
        mock_collection = Mock()
        mock_collection.update_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.update_one_by_id(collection_name, doc_id, update)

        expected_query = {"_id": ObjectId(doc_id)}
        mock_collection.update_one.assert_called_once_with(expected_query, update, session=None)
        assert result == mock_result

    def test_update_many_success(self, mongo_service):
        """Test successful multiple document update."""
        collection_name = "test_collection"
        query = {"status": "inactive"}
        update = {"$set": {"status": "active"}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 5
        mock_collection = Mock()
        mock_collection.update_many.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.update_many(collection_name, query, update)

        mock_collection.update_many.assert_called_once_with(query, update, upsert=False, session=None)
        assert result == mock_result


class TestDeleteOperations:
    """Test delete operations."""

    def test_delete_one_success(self, mongo_service):
        """Test successful single document deletion."""
        collection_name = "test_collection"
        query = {"name": "test"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 1
        mock_collection = Mock()
        mock_collection.delete_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.delete_one(collection_name, query)

        mock_collection.delete_one.assert_called_once_with(query, session=None)
        assert result == mock_result

    def test_delete_many_success(self, mongo_service):
        """Test successful multiple document deletion."""
        collection_name = "test_collection"
        query = {"status": "expired"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 3
        mock_collection = Mock()
        mock_collection.delete_many.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.delete_many(collection_name, query)

        mock_collection.delete_many.assert_called_once_with(query, session=None)
        assert result == mock_result


class TestAggregationOperations:
    """Test aggregation operations."""

    def test_count_documents_success(self, mongo_service):
        """Test successful document count."""
        collection_name = "test_collection"
        query = {"status": "active"}
        expected_count = 42

        mock_collection = Mock()
        mock_collection.count_documents.return_value = expected_count
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.count_documents(collection_name, query)

        mock_collection.count_documents.assert_called_once_with(query, session=None)
        assert result == expected_count

    def test_aggregate_success(self, mongo_service):
        """Test successful aggregation pipeline."""
        collection_name = "test_collection"
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        ]
        expected_result = [
            {"_id": "electronics", "count": 10},
            {"_id": "books", "count": 5},
        ]

        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(expected_result))
        mock_collection = Mock()
        mock_collection.aggregate.return_value = mock_cursor
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.aggregate(collection_name, pipeline)

        mock_collection.aggregate.assert_called_once_with(pipeline, session=None)
        assert result == expected_result


class TestIndexOperations:
    """Test index operations."""

    def test_create_index_simple(self, mongo_service):
        """Test creating a simple index."""
        collection_name = "test_collection"
        keys = "name"
        expected_index_name = "name_1"

        mock_collection = Mock()
        mock_collection.create_index.return_value = expected_index_name
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.create_index(collection_name, keys)

        mock_collection.create_index.assert_called_once_with(keys, unique=False)
        assert result == expected_index_name

    def test_create_index_compound_unique(self, mongo_service):
        """Test creating a compound unique index."""
        collection_name = "test_collection"
        keys = [("name", 1), ("email", 1)]
        expected_index_name = "name_1_email_1"

        mock_collection = Mock()
        mock_collection.create_index.return_value = expected_index_name
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.create_index(collection_name, keys, unique=True)

        mock_collection.create_index.assert_called_once_with(keys, unique=True)
        assert result == expected_index_name


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_connection_failure(self, mock_logger, valid_config):
        """Test handling of connection failures."""
        with patch("mongodb.mongodb_service.MongoClient") as mock_client:
            mock_client.side_effect = ConnectionFailure("Connection failed")

            with pytest.raises(ConnectionFailure):
                MongoService(mock_logger, valid_config)

    def test_operation_failure_on_insert(self, mongo_service):
        """Test handling of operation failures during insert."""
        collection_name = "test_collection"
        document = {"name": "test"}

        mock_collection = Mock()
        mock_collection.insert_one.side_effect = OperationFailure("Insert failed")
        mongo_service._db.__getitem__.return_value = mock_collection

        with pytest.raises(MongoOperationError):
            mongo_service.insert_one(collection_name, document)

    def test_invalid_object_id_on_update_by_id(self, mongo_service):
        """Test handling of invalid ObjectId in update_one_by_id."""
        collection_name = "test_collection"
        invalid_id = "invalid_id"
        update = {"$set": {"value": 123}}

        mock_collection = Mock()
        mongo_service._db.__getitem__.return_value = mock_collection

        with pytest.raises(
            Exception
        ):  # ObjectId will raise an exception for invalid format
            mongo_service.update_one_by_id(collection_name, invalid_id, update)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_find_many_empty_result(self, mongo_service):
        """Test find_many with empty result set."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}

        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([]))
        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.find_many(collection_name, query)

        assert result == []

    def test_find_many_documents_without_id(self, mongo_service):
        """Test find_many with documents that don't have _id field."""
        collection_name = "test_collection"
        query = {"name": "test"}

        mock_docs = [{"name": "test1"}, {"name": "test2"}]
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(mock_docs))
        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.find_many(collection_name, query)

        assert result == mock_docs

    def test_update_operations_no_matches(self, mongo_service):
        """Test update operations when no documents match."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}
        update = {"$set": {"value": 123}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 0
        mock_result.matched_count = 0
        mock_collection = Mock()
        mock_collection.update_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.update_one(collection_name, query, update)

        assert result.modified_count == 0
        assert result.matched_count == 0

    def test_delete_operations_no_matches(self, mongo_service):
        """Test delete operations when no documents match."""
        collection_name = "test_collection"
        query = {"name": "nonexistent"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 0
        mock_collection = Mock()
        mock_collection.delete_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.delete_one(collection_name, query)

        assert result.deleted_count == 0


class TestRetryLogic:
    """Test retry logic and error handling."""

    def test_retry_on_auto_reconnect(self, mongo_service):
        """Test retry logic for AutoReconnect errors."""
        collection_name = "test_collection"
        document = {"name": "test"}

        mock_collection = Mock()
        # First call fails, second succeeds
        mock_collection.insert_one.side_effect = [
            AutoReconnect("Connection lost"),
            Mock(spec=InsertOneResult, inserted_id=ObjectId()),
        ]
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.insert_one(collection_name, document)

        assert mock_collection.insert_one.call_count == 2
        assert result is not None

    def test_retry_exhausted_raises_mongo_operation_error(self, mongo_service):
        """Test that exhausted retries raise MongoOperationError."""
        collection_name = "test_collection"
        document = {"name": "test"}

        mock_collection = Mock()
        mock_collection.insert_one.side_effect = AutoReconnect("Connection lost")
        mongo_service._db.__getitem__.return_value = mock_collection

        with pytest.raises(MongoOperationError) as exc_info:
            mongo_service.insert_one(collection_name, document)

        assert exc_info.value.operation == "insert_one"
        assert exc_info.value.attempts == 2  # max_retries + 1
        assert isinstance(exc_info.value.original_error, AutoReconnect)

    def test_no_retry_on_operation_failure(self, mongo_service):
        """Test that OperationFailure doesn't trigger retries."""
        collection_name = "test_collection"
        document = {"name": "test"}

        mock_collection = Mock()
        mock_collection.insert_one.side_effect = OperationFailure("Validation error")
        mongo_service._db.__getitem__.return_value = mock_collection

        with pytest.raises(MongoOperationError):
            mongo_service.insert_one(collection_name, document)

        # Should only be called once (no retries)
        assert mock_collection.insert_one.call_count == 1


class TestBulkOperations:
    """Test bulk operations."""

    def test_bulk_write_success(self, mongo_service):
        """Test successful bulk write operation."""
        collection_name = "test_collection"
        operations = [
            InsertOne({"name": "doc1"}),
            UpdateOne({"_id": 1}, {"$set": {"updated": True}}),
            DeleteOne({"_id": 2}),
        ]

        mock_collection = Mock()
        mock_result = Mock(spec=BulkWriteResult)
        mock_result.inserted_count = 1
        mock_result.modified_count = 1
        mock_result.deleted_count = 1
        mock_collection.bulk_write.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.bulk_write(collection_name, operations)

        mock_collection.bulk_write.assert_called_once_with(
            operations, ordered=True, session=None
        )
        assert result == mock_result

    def test_bulk_insert_success(self, mongo_service):
        """Test successful bulk insert operation."""
        collection_name = "test_collection"
        documents = [{"name": "doc1"}, {"name": "doc2"}]

        mock_collection = Mock()
        mock_result = Mock(spec=BulkWriteResult)
        mock_result.inserted_count = 2
        mock_collection.bulk_write.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        result = mongo_service.bulk_insert(collection_name, documents)

        assert mock_collection.bulk_write.called
        assert result == mock_result


class TestEnhancedAggregation:
    """Test enhanced aggregation utilities."""

    def test_paginate_success(self, mongo_service):
        """Test pagination functionality."""
        collection_name = "test_collection"
        query = {"status": "active"}

        # Mock find_many and count_documents calls
        with (
            patch.object(mongo_service, "find_many") as mock_find,
            patch.object(mongo_service, "count_documents") as mock_count,
        ):
            mock_find.return_value = [{"_id": "1", "name": "doc1"}]
            mock_count.return_value = 25

            documents, total_count = mongo_service.paginate(
                collection_name, query, page=2, page_size=10
            )

            mock_find.assert_called_once_with(
                collection_name,
                query,
                projection=None,
                sort=None,
                limit=10,
                skip=10,
                session=None,
            )
            mock_count.assert_called_once_with(collection_name, query, session=None)
            assert documents == [{"_id": "1", "name": "doc1"}]
            assert total_count == 25

    def test_aggregate_with_facets(self, mongo_service):
        """Test faceted aggregation."""
        collection_name = "test_collection"
        pipeline = [{"$match": {"status": "active"}}]
        facets = {
            "by_category": [{"$group": {"_id": "$category", "count": {"$sum": 1}}}],
            "by_date": [{"$group": {"_id": "$date", "count": {"$sum": 1}}}],
        }

        with patch.object(mongo_service, "aggregate") as mock_agg:
            mock_agg.return_value = [
                {
                    "by_category": [{"_id": "electronics", "count": 10}],
                    "by_date": [{"_id": "2023-01-01", "count": 5}],
                }
            ]

            result = mongo_service.aggregate_with_facets(
                collection_name, pipeline, facets
            )

            expected_pipeline = pipeline + [{"$facet": facets}]
            mock_agg.assert_called_once_with(
                collection_name, expected_pipeline, session=None
            )
            assert "by_category" in result
            assert "by_date" in result


class TestMetricsAndMonitoring:
    """Test metrics and monitoring functionality."""

    def test_metrics_collection(self, mongo_service):
        """Test that metrics are collected during operations."""
        collection_name = "test_collection"
        document = {"name": "test"}

        mock_collection = Mock()
        mock_result = Mock(spec=InsertOneResult, inserted_id=ObjectId())
        mock_collection.insert_one.return_value = mock_result
        mongo_service._db.__getitem__.return_value = mock_collection

        # Perform operation to generate metrics
        mongo_service.insert_one(collection_name, document)

        metrics = mongo_service.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].operation == "insert_one"
        assert metrics[0].collection == collection_name
        assert metrics[0].success is True
        assert metrics[0].documents_affected == 1

    def test_performance_summary(self, mongo_service):
        """Test performance summary generation."""
        # Add some mock metrics
        from mongodb.mongodb_service import OperationMetrics

        mongo_service._metrics = [
            OperationMetrics("insert_one", "users", 10.5, 1, True),
            OperationMetrics("insert_one", "users", 15.2, 1, True),
            OperationMetrics("find_many", "users", 25.1, 5, True),
            OperationMetrics("update_one", "users", 8.7, 1, False, "Connection error"),
        ]

        summary = mongo_service.get_performance_summary()

        assert summary["total_operations"] == 4
        assert summary["successful_operations"] == 3
        assert summary["failed_operations"] == 1
        assert summary["error_rate"] == 0.25
        assert "insert_one" in summary["operations_by_type"]
        assert summary["operations_by_type"]["insert_one"]["count"] == 2

    def test_clear_metrics_after_read(self, mongo_service):
        """Test clearing metrics after reading."""
        from mongodb.mongodb_service import OperationMetrics

        mongo_service._metrics = [
            OperationMetrics("insert_one", "users", 10.5, 1, True)
        ]

        metrics = mongo_service.get_metrics(clear_after_read=True)
        assert len(metrics) == 1
        assert len(mongo_service._metrics) == 0

    def test_close_connection(self, mongo_service):
        """Test closing MongoDB connection."""
        mongo_service.close()
        mongo_service._client.close.assert_called_once()
        mongo_service.log.info.assert_any_call("MongoDB connection closed successfully")
