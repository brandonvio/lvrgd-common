"""Test suite for async MongoDB service implementation.

This module contains tests for the async MongoDB service including:
- Connection initialization and configuration
- CRUD operations with logging
- Transaction handling
- Error handling
- Bulk operations
- Aggregation operations
- Pydantic model support
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.mongodb.async_mongodb_service import AsyncMongoService
from lvrgd.common.services.mongodb.mongodb_models import MongoConfig


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger for testing."""
    return Mock(spec=LoggingService)


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
def async_mongo_service(
    mock_logger: Mock,
    valid_config: MongoConfig,
) -> AsyncMongoService:
    """Create an AsyncMongoService instance with mocked dependencies."""
    with patch("lvrgd.common.services.mongodb.async_mongodb_service.AsyncIOMotorClient"):
        service = AsyncMongoService(mock_logger, valid_config)

        # Set up the database mock properly to be subscriptable
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        service._db = mock_db

        # Ensure the client's close method is mocked
        service._client = Mock()
        service._client.close = Mock()
        service._client.server_info = AsyncMock(return_value={"version": "5.0.0"})

        return service


class TestAsyncMongoServiceInitialization:
    """Test async MongoDB service initialization."""

    def test_init_with_auth(
        self,
        mock_logger: Mock,
        valid_config: MongoConfig,
    ) -> None:
        """Test initialization with authentication."""
        with patch(
            "lvrgd.common.services.mongodb.async_mongodb_service.AsyncIOMotorClient"
        ) as mock_client:
            service = AsyncMongoService(mock_logger, valid_config)

            mock_logger.info.assert_any_call(
                "Initializing async MongoDB connection",
                database=valid_config.database,
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

            mock_client.assert_called_once_with(**expected_params)
            assert service.config == valid_config
            assert service.log == mock_logger

    def test_init_without_auth(
        self,
        mock_logger: Mock,
        config_without_auth: MongoConfig,
    ) -> None:
        """Test initialization without authentication."""
        with patch(
            "lvrgd.common.services.mongodb.async_mongodb_service.AsyncIOMotorClient"
        ) as mock_client:
            service = AsyncMongoService(mock_logger, config_without_auth)

            expected_params: dict[str, Any] = {
                "host": config_without_auth.url,
                "maxPoolSize": config_without_auth.max_pool_size,
                "minPoolSize": config_without_auth.min_pool_size,
                "serverSelectionTimeoutMS": config_without_auth.server_selection_timeout_ms,
                "connectTimeoutMS": config_without_auth.connect_timeout_ms,
                "retryWrites": config_without_auth.retry_reads,
                "retryReads": config_without_auth.retry_reads,
            }

            mock_client.assert_called_once_with(**expected_params)
            assert service.config == config_without_auth


class TestPingMethod:
    """Test async ping functionality."""

    @pytest.mark.asyncio
    async def test_ping_success(self, async_mongo_service: AsyncMongoService) -> None:
        """Test successful async ping."""
        server_info: dict[str, Any] = {"version": "5.0.0", "modules": []}
        async_mongo_service._client.server_info = AsyncMock(return_value=server_info)

        result = await async_mongo_service.ping()

        assert result == server_info
        async_mongo_service._client.server_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_failure(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async ping failure."""
        async_mongo_service._client.server_info = AsyncMock(
            side_effect=ConnectionFailure("Connection failed"),
        )

        with pytest.raises(ConnectionFailure):
            await async_mongo_service.ping()

        async_mongo_service.log.exception.assert_called_once_with("Async MongoDB connection failed")


class TestGetCollection:
    """Test get_collection method."""

    def test_get_collection(self, async_mongo_service: AsyncMongoService) -> None:
        """Test getting a collection."""
        collection_name = "test_collection"

        collection = async_mongo_service.get_collection(collection_name)

        assert collection is not None
        async_mongo_service._db.__getitem__.assert_called_once_with(collection_name)


class TestInsertOperations:
    """Test async insert operations."""

    @pytest.mark.asyncio
    async def test_insert_one(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async inserting a single document."""
        collection_name = "test_collection"
        document: dict[str, Any] = {"name": "test", "value": 123}
        inserted_id = ObjectId()

        mock_result = Mock(spec=InsertOneResult)
        mock_result.inserted_id = inserted_id

        mock_collection = Mock()
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.insert_one(collection_name, document)

        assert result.inserted_id == inserted_id
        mock_collection.insert_one.assert_called_once_with(document, session=None)

    @pytest.mark.asyncio
    async def test_insert_many(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async inserting multiple documents."""
        collection_name = "test_collection"
        documents: list[dict[str, Any]] = [
            {"name": "test1", "value": 1},
            {"name": "test2", "value": 2},
        ]
        inserted_ids = [ObjectId(), ObjectId()]

        mock_result = Mock()
        mock_result.inserted_ids = inserted_ids

        mock_collection = Mock()
        mock_collection.insert_many = AsyncMock(return_value=mock_result)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.insert_many(collection_name, documents)

        assert result == inserted_ids
        mock_collection.insert_many.assert_called_once_with(documents, ordered=True, session=None)


class TestFindOperations:
    """Test async find operations."""

    @pytest.mark.asyncio
    async def test_find_one(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async finding a single document."""
        collection_name = "test_collection"
        query: dict[str, Any] = {"name": "test"}
        found_doc: dict[str, Any] = {"_id": ObjectId(), "name": "test", "value": 123}

        mock_collection = Mock()
        mock_collection.find_one = AsyncMock(return_value=found_doc)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.find_one(collection_name, query)

        assert result == found_doc
        mock_collection.find_one.assert_called_once_with(query, None, session=None)

    @pytest.mark.asyncio
    async def test_find_many(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async finding multiple documents."""
        collection_name = "test_collection"
        query: dict[str, Any] = {"status": "active"}
        found_docs: list[dict[str, Any]] = [
            {"_id": ObjectId(), "name": "test1", "status": "active"},
            {"_id": ObjectId(), "name": "test2", "status": "active"},
        ]

        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=found_docs)

        mock_collection = Mock()
        mock_collection.find = Mock(return_value=mock_cursor)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.find_many(collection_name, query)

        assert result == found_docs
        mock_collection.find.assert_called_once_with(query, None, session=None)


class TestUpdateOperations:
    """Test async update operations."""

    @pytest.mark.asyncio
    async def test_update_one(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async updating a single document."""
        collection_name = "test_collection"
        query: dict[str, Any] = {"name": "test"}
        update: dict[str, Any] = {"$set": {"value": 456}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.matched_count = 1
        mock_result.modified_count = 1
        mock_result.upserted_id = None

        mock_collection = Mock()
        mock_collection.update_one = AsyncMock(return_value=mock_result)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.update_one(collection_name, query, update)

        assert result.matched_count == 1
        assert result.modified_count == 1
        mock_collection.update_one.assert_called_once_with(
            query, update, upsert=False, session=None
        )

    @pytest.mark.asyncio
    async def test_update_many(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async updating multiple documents."""
        collection_name = "test_collection"
        query: dict[str, Any] = {"status": "active"}
        update: dict[str, Any] = {"$set": {"updated": True}}

        mock_result = Mock(spec=UpdateResult)
        mock_result.matched_count = 5
        mock_result.modified_count = 5

        mock_collection = Mock()
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.update_many(collection_name, query, update)

        assert result.matched_count == 5
        assert result.modified_count == 5
        mock_collection.update_many.assert_called_once_with(
            query, update, upsert=False, session=None
        )


class TestDeleteOperations:
    """Test async delete operations."""

    @pytest.mark.asyncio
    async def test_delete_one(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async deleting a single document."""
        collection_name = "test_collection"
        query: dict[str, Any] = {"name": "test"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 1

        mock_collection = Mock()
        mock_collection.delete_one = AsyncMock(return_value=mock_result)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.delete_one(collection_name, query)

        assert result.deleted_count == 1
        mock_collection.delete_one.assert_called_once_with(query, session=None)

    @pytest.mark.asyncio
    async def test_delete_many(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async deleting multiple documents."""
        collection_name = "test_collection"
        query: dict[str, Any] = {"status": "inactive"}

        mock_result = Mock(spec=DeleteResult)
        mock_result.deleted_count = 3

        mock_collection = Mock()
        mock_collection.delete_many = AsyncMock(return_value=mock_result)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.delete_many(collection_name, query)

        assert result.deleted_count == 3
        mock_collection.delete_many.assert_called_once_with(query, session=None)


class TestCountDocuments:
    """Test async count documents operation."""

    @pytest.mark.asyncio
    async def test_count_documents(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async counting documents."""
        collection_name = "test_collection"
        query: dict[str, Any] = {"status": "active"}
        expected_count = 42

        mock_collection = Mock()
        mock_collection.count_documents = AsyncMock(return_value=expected_count)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.count_documents(collection_name, query)

        assert result == expected_count
        mock_collection.count_documents.assert_called_once_with(query, session=None)


class TestAggregate:
    """Test async aggregation operations."""

    @pytest.mark.asyncio
    async def test_aggregate(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async aggregation pipeline."""
        collection_name = "test_collection"
        pipeline: list[dict[str, Any]] = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        ]
        expected_results: list[dict[str, Any]] = [
            {"_id": "category1", "count": 10},
            {"_id": "category2", "count": 20},
        ]

        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=expected_results)

        mock_collection = Mock()
        mock_collection.aggregate = Mock(return_value=mock_cursor)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.aggregate(collection_name, pipeline)

        assert result == expected_results
        mock_collection.aggregate.assert_called_once_with(pipeline, session=None)


class TestCreateIndex:
    """Test async index creation."""

    @pytest.mark.asyncio
    async def test_create_index(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async creating an index."""
        collection_name = "test_collection"
        keys = "name"
        expected_index_name = "name_1"

        mock_collection = Mock()
        mock_collection.create_index = AsyncMock(return_value=expected_index_name)
        async_mongo_service._db.__getitem__ = Mock(return_value=mock_collection)

        result = await async_mongo_service.create_index(collection_name, keys, unique=True)

        assert result == expected_index_name
        mock_collection.create_index.assert_called_once_with(keys, unique=True)


class TestTransaction:
    """Test async transaction support."""

    @pytest.mark.asyncio
    async def test_transaction_context_manager(
        self, async_mongo_service: AsyncMongoService
    ) -> None:
        """Test async transaction context manager."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.start_transaction = Mock(return_value=mock_session)
        mock_session.end_session = AsyncMock()

        async_mongo_service._client.start_session = AsyncMock(return_value=mock_session)

        async with async_mongo_service.transaction() as session:
            assert session == mock_session

        async_mongo_service._client.start_session.assert_called_once()
        mock_session.end_session.assert_called_once()


class TestClose:
    """Test async close method."""

    @pytest.mark.asyncio
    async def test_close(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async closing the connection."""
        await async_mongo_service.close()

        async_mongo_service._client.close.assert_called_once()
        async_mongo_service.log.info.assert_any_call("Async MongoDB connection closed successfully")
