"""Test suite for MongoDB service Pydantic model support.

This module contains tests for the MongoDB service Pydantic methods including:
- Finding and deserializing documents to models
- Inserting and serializing models to documents
- Updating documents with models
- Validation error handling
"""

from collections.abc import Iterator
from unittest.mock import Mock, patch

import pytest
from bson.objectid import ObjectId
from pydantic import BaseModel, ValidationError
from pymongo.results import InsertOneResult, UpdateResult

from lvrgd.common.services import LoggingService
from lvrgd.common.services.mongodb.mongodb_models import MongoConfig
from lvrgd.common.services.mongodb.mongodb_service import MongoService


class UserModel(BaseModel):
    """Test model for user data."""

    name: str
    age: int
    email: str | None = None


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
def mock_mongo_client() -> Iterator[Mock]:
    """Create a mock MongoDB client."""
    with patch("lvrgd.common.services.mongodb.mongodb_service.MongoClient") as mock_client:
        yield mock_client


@pytest.fixture
def mongo_service(
    mock_logger: Mock,
    valid_config: MongoConfig,
    mock_mongo_client: Mock,
) -> MongoService:
    """Create a MongoService instance with mocked dependencies."""
    with patch.object(MongoService, "ping") as mock_ping:
        mock_ping.return_value = {"version": "5.0.0"}
        service = MongoService(mock_logger, valid_config)

        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        service._db = mock_db  # type: ignore[attr-defined]

        service._client = Mock()  # type: ignore[attr-defined]
        service._client.close = Mock()  # type: ignore[attr-defined]

        return service


@pytest.fixture
def mock_db(mongo_service: MongoService) -> Mock:
    """Get the mock database from the mongo service."""
    return mongo_service._db  # type: ignore[attr-defined]


class TestFindOneModel:
    """Test find_one_model method."""

    def test_find_one_model_success(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test successful retrieval and deserialization of a document."""
        mock_db["users"].find_one.return_value = {
            "name": "John",
            "age": 30,
            "email": "john@example.com",
        }

        result = mongo_service.find_one_model("users", {"email": "john@example.com"}, UserModel)

        assert isinstance(result, UserModel)
        assert result.name == "John"
        assert result.age == 30
        assert result.email == "john@example.com"
        mock_db["users"].find_one.assert_called_once()

    def test_find_one_model_missing_returns_none(
        self, mongo_service: MongoService, mock_db: Mock
    ) -> None:
        """Test that None is returned when document is not found."""
        mock_db["users"].find_one.return_value = None

        result = mongo_service.find_one_model("users", {"email": "missing@example.com"}, UserModel)

        assert result is None
        mock_db["users"].find_one.assert_called_once()

    def test_find_one_model_validation_error_propagates(
        self, mongo_service: MongoService, mock_db: Mock
    ) -> None:
        """Test that ValidationError is raised for invalid data."""
        mock_db["users"].find_one.return_value = {
            "name": "John",
            "age": "not_a_number",
        }

        with pytest.raises(ValidationError):
            mongo_service.find_one_model("users", {"name": "John"}, UserModel)

    def test_find_one_model_with_projection(
        self, mongo_service: MongoService, mock_db: Mock
    ) -> None:
        """Test find_one_model with projection parameter."""
        mock_db["users"].find_one.return_value = {
            "name": "John",
            "age": 30,
        }

        projection = {"_id": 0, "name": 1, "age": 1}
        result = mongo_service.find_one_model(
            "users", {"name": "John"}, UserModel, projection=projection
        )

        assert isinstance(result, UserModel)
        assert result.name == "John"
        assert result.age == 30
        mock_db["users"].find_one.assert_called_once()


class TestInsertOneModel:
    """Test insert_one_model method."""

    def test_insert_one_model_success(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test successful serialization and insertion of a model."""
        user = UserModel(name="Alice", age=25, email="alice@example.com")
        mock_id = ObjectId()
        mock_result = Mock(spec=InsertOneResult)
        mock_result.inserted_id = mock_id
        mock_db["users"].insert_one.return_value = mock_result

        result = mongo_service.insert_one_model("users", user)

        assert result.inserted_id == mock_id
        mock_db["users"].insert_one.assert_called_once()
        call_args = mock_db["users"].insert_one.call_args[0]
        assert call_args[0]["name"] == "Alice"
        assert call_args[0]["age"] == 25
        assert call_args[0]["email"] == "alice@example.com"

    def test_insert_one_model_with_session(
        self, mongo_service: MongoService, mock_db: Mock
    ) -> None:
        """Test insert_one_model with session parameter."""
        user = UserModel(name="Bob", age=35)
        mock_session = Mock()
        mock_result = Mock(spec=InsertOneResult)
        mock_result.inserted_id = ObjectId()
        mock_db["users"].insert_one.return_value = mock_result

        result = mongo_service.insert_one_model("users", user, session=mock_session)

        assert result.inserted_id is not None
        mock_db["users"].insert_one.assert_called_once()


class TestFindManyModels:
    """Test find_many_models method."""

    def test_find_many_models_success(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test successful retrieval and deserialization of multiple documents."""
        mock_db["users"].find.return_value = [
            {"name": "Alice", "age": 25, "email": "alice@example.com"},
            {"name": "Bob", "age": 35, "email": "bob@example.com"},
            {"name": "Charlie", "age": 45},
        ]

        results = mongo_service.find_many_models("users", {"age": {"$gte": 20}}, UserModel)

        assert len(results) == 3
        assert all(isinstance(result, UserModel) for result in results)
        assert results[0].name == "Alice"
        assert results[1].name == "Bob"
        assert results[2].name == "Charlie"
        assert results[2].email is None

    def test_find_many_models_empty_list(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test that empty list is returned when no documents match."""
        mock_db["users"].find.return_value = []

        results = mongo_service.find_many_models("users", {"age": {"$gte": 100}}, UserModel)

        assert results == []

    def test_find_many_models_with_pagination(
        self, mongo_service: MongoService, mock_db: Mock
    ) -> None:
        """Test find_many_models with limit and skip parameters."""
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(
            return_value=iter(
                [
                    {"name": "User1", "age": 30},
                    {"name": "User2", "age": 31},
                ]
            )
        )
        mock_db["users"].find.return_value = mock_cursor

        results = mongo_service.find_many_models(
            "users", {}, UserModel, limit=2, skip=10, sort=[("age", 1)]
        )

        assert len(results) == 2
        mock_cursor.limit.assert_called_once_with(2)
        mock_cursor.skip.assert_called_once_with(10)
        mock_cursor.sort.assert_called_once_with([("age", 1)])


class TestInsertManyModels:
    """Test insert_many_models method."""

    def test_insert_many_models_success(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test successful serialization and insertion of multiple models."""
        users = [
            UserModel(name="Alice", age=25),
            UserModel(name="Bob", age=35),
            UserModel(name="Charlie", age=45),
        ]
        mock_ids = [ObjectId(), ObjectId(), ObjectId()]
        mock_result = Mock()
        mock_result.inserted_ids = mock_ids
        mock_db["users"].insert_many.return_value = mock_result

        result = mongo_service.insert_many_models("users", users)

        assert result == mock_ids
        mock_db["users"].insert_many.assert_called_once()
        call_args = mock_db["users"].insert_many.call_args[0]
        assert len(call_args[0]) == 3
        assert call_args[0][0]["name"] == "Alice"
        assert call_args[0][1]["name"] == "Bob"
        assert call_args[0][2]["name"] == "Charlie"

    def test_insert_many_models_ordered_false(
        self, mongo_service: MongoService, mock_db: Mock
    ) -> None:
        """Test insert_many_models with ordered parameter set to False."""
        users = [UserModel(name="Alice", age=25), UserModel(name="Bob", age=35)]
        mock_result = Mock()
        mock_result.inserted_ids = [ObjectId(), ObjectId()]
        mock_db["users"].insert_many.return_value = mock_result

        result = mongo_service.insert_many_models("users", users, ordered=False)

        assert len(result) == 2
        call_kwargs = mock_db["users"].insert_many.call_args[1]
        assert call_kwargs["ordered"] is False


class TestUpdateOneModel:
    """Test update_one_model method."""

    def test_update_one_model_success(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test successful update of a document using a model."""
        user_update = UserModel(name="Alice Updated", age=26, email="alice_new@example.com")
        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 1
        mock_result.matched_count = 1
        mock_result.upserted_id = None
        mock_db["users"].update_one.return_value = mock_result

        result = mongo_service.update_one_model("users", {"name": "Alice"}, user_update)

        assert result.modified_count == 1
        assert result.matched_count == 1
        mock_db["users"].update_one.assert_called_once()
        call_args = mock_db["users"].update_one.call_args[0]
        assert call_args[0] == {"name": "Alice"}
        assert "$set" in call_args[1]
        assert call_args[1]["$set"]["name"] == "Alice Updated"
        assert call_args[1]["$set"]["age"] == 26

    def test_update_one_model_with_upsert(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test update_one_model with upsert parameter."""
        user_update = UserModel(name="New User", age=30)
        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 0
        mock_result.matched_count = 0
        mock_result.upserted_id = ObjectId()
        mock_db["users"].update_one.return_value = mock_result

        result = mongo_service.update_one_model(
            "users", {"name": "New User"}, user_update, upsert=True
        )

        assert result.upserted_id is not None
        call_kwargs = mock_db["users"].update_one.call_args[1]
        assert call_kwargs["upsert"] is True


class TestUpdateManyModels:
    """Test update_many_models method."""

    def test_update_many_models_success(self, mongo_service: MongoService, mock_db: Mock) -> None:
        """Test successful update of multiple documents using a model."""
        status_update = UserModel(name="Updated", age=99)
        mock_result = Mock(spec=UpdateResult)
        mock_result.modified_count = 5
        mock_result.matched_count = 5
        mock_db["users"].update_many.return_value = mock_result

        result = mongo_service.update_many_models("users", {"age": {"$lt": 30}}, status_update)

        assert result.modified_count == 5
        assert result.matched_count == 5
        mock_db["users"].update_many.assert_called_once()
        call_args = mock_db["users"].update_many.call_args[0]
        assert "$set" in call_args[1]
        assert call_args[1]["$set"]["name"] == "Updated"
        assert call_args[1]["$set"]["age"] == 99
