"""Integration tests for MongoDB service.

Tests MongoDB service operations against a real MongoDB instance.
Configuration loaded from environment variables via conftest.py fixtures.
"""

import uuid
from typing import Any

from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from pymongo.operations import InsertOne, UpdateOne

from lvrgd.common.services.mongodb.mongodb_service import MongoService


class MongoDocument(BaseModel):
    """Document model for MongoDB integration tests."""

    name: str = Field(..., description="Document name")
    value: int = Field(..., description="Document value")
    active: bool = Field(default=True, description="Document active status")


class TestMongoDBIntegration:
    """Integration tests for MongoService."""

    def test_mongodb_connection_and_ping(self, mongo_service: MongoService) -> None:
        """Test MongoDB connection and ping functionality."""
        # Ping server
        server_info = mongo_service.ping()
        assert isinstance(server_info, dict)
        assert "version" in server_info

    def test_insert_and_find_one(self, mongo_service: MongoService) -> None:
        """Test insert and find single document."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert document
            doc = {"name": "test-doc", "value": 42, "active": True}
            result = mongo_service.insert_one(collection, doc)
            assert result.inserted_id is not None

            # Find document
            found = mongo_service.find_one(collection, {"name": "test-doc"})
            assert found is not None
            assert found["name"] == "test-doc"
            assert found["value"] == 42
            assert found["active"] is True

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_insert_many_and_find_many(self, mongo_service: MongoService) -> None:
        """Test batch insert and query multiple documents."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert multiple documents
            docs = [
                {"name": "doc1", "value": 10, "active": True},
                {"name": "doc2", "value": 20, "active": False},
                {"name": "doc3", "value": 30, "active": True},
            ]
            inserted_ids = mongo_service.insert_many(collection, docs)
            assert len(inserted_ids) == 3

            # Find all documents
            found = mongo_service.find_many(collection, {})
            assert len(found) == 3

            # Find with query filter
            active_docs = mongo_service.find_many(collection, {"active": True})
            assert len(active_docs) == 2

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_update_operations(self, mongo_service: MongoService) -> None:
        """Test update_one and update_many operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs = [
                {"name": "doc1", "value": 10},
                {"name": "doc2", "value": 20},
                {"name": "doc3", "value": 30},
            ]
            mongo_service.insert_many(collection, docs)

            # Update one document
            result = mongo_service.update_one(
                collection,
                {"name": "doc1"},
                {"$set": {"value": 100}},
            )
            assert result.modified_count == 1

            # Verify update
            updated = mongo_service.find_one(collection, {"name": "doc1"})
            assert updated is not None
            assert updated["value"] == 100

            # Update many documents (value >= 20 matches doc1(100), doc2(20), doc3(30) = 3 docs)
            result = mongo_service.update_many(
                collection,
                {"value": {"$gte": 20}},
                {"$inc": {"value": 5}},
            )
            assert result.modified_count == 3

            # Verify updates
            doc2 = mongo_service.find_one(collection, {"name": "doc2"})
            doc3 = mongo_service.find_one(collection, {"name": "doc3"})
            assert doc2 is not None
            assert doc2["value"] == 25
            assert doc3 is not None
            assert doc3["value"] == 35

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_delete_operations(self, mongo_service: MongoService) -> None:
        """Test delete_one and delete_many operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs = [
                {"name": "doc1", "status": "active"},
                {"name": "doc2", "status": "inactive"},
                {"name": "doc3", "status": "inactive"},
            ]
            mongo_service.insert_many(collection, docs)

            # Delete one document
            result = mongo_service.delete_one(collection, {"name": "doc1"})
            assert result.deleted_count == 1

            # Verify deletion
            remaining = mongo_service.find_many(collection, {})
            assert len(remaining) == 2

            # Delete many documents
            result = mongo_service.delete_many(collection, {"status": "inactive"})
            assert result.deleted_count == 2

            # Verify all deleted
            remaining = mongo_service.find_many(collection, {})
            assert len(remaining) == 0

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_aggregation_pipeline(self, mongo_service: MongoService) -> None:
        """Test aggregation pipeline operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test data
            docs = [
                {"category": "A", "value": 10},
                {"category": "A", "value": 20},
                {"category": "B", "value": 30},
                {"category": "B", "value": 40},
            ]
            mongo_service.insert_many(collection, docs)

            # Run aggregation pipeline
            pipeline = [
                {"$group": {"_id": "$category", "total": {"$sum": "$value"}}},
                {"$sort": {"_id": 1}},
            ]
            results = mongo_service.aggregate(collection, pipeline)

            # Verify results
            assert len(results) == 2
            assert results[0]["_id"] == "A"
            assert results[0]["total"] == 30
            assert results[1]["_id"] == "B"
            assert results[1]["total"] == 70

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_index_creation(self, mongo_service: MongoService) -> None:
        """Test index creation and unique constraint."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Create unique index
            index_name = mongo_service.create_index(
                collection,
                "email",
                unique=True,
            )
            assert index_name is not None

            # Insert document
            mongo_service.insert_one(collection, {"email": "test@example.com"})

            # Try to insert duplicate - should fail
            try:
                mongo_service.insert_one(collection, {"email": "test@example.com"})
                assert False, "Should have raised DuplicateKeyError"
            except DuplicateKeyError:
                pass

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_bulk_operations(self, mongo_service: MongoService) -> None:
        """Test bulk write operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Prepare bulk operations
            operations: list[Any] = [
                InsertOne({"name": "doc1", "value": 10}),
                InsertOne({"name": "doc2", "value": 20}),
                UpdateOne({"name": "doc1"}, {"$set": {"value": 100}}),
            ]

            # Execute bulk write
            result = mongo_service.bulk_write(collection, operations)
            assert result.inserted_count == 2
            assert result.modified_count == 1

            # Verify results
            doc1 = mongo_service.find_one(collection, {"name": "doc1"})
            assert doc1 is not None
            assert doc1["value"] == 100

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_count_documents(self, mongo_service: MongoService) -> None:
        """Test document counting with query."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test data
            docs = [
                {"status": "active", "value": 10},
                {"status": "active", "value": 20},
                {"status": "inactive", "value": 30},
            ]
            mongo_service.insert_many(collection, docs)

            # Count all documents
            total = mongo_service.count_documents(collection, {})
            assert total == 3

            # Count with query
            active_count = mongo_service.count_documents(collection, {"status": "active"})
            assert active_count == 2

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_find_one_model(self, mongo_service: MongoService) -> None:
        """Test finding and deserializing single document to Pydantic model."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test document
            doc = {"name": "Alice", "value": 25, "active": True}
            mongo_service.insert_one(collection, doc)

            # Find and deserialize to model
            result = mongo_service.find_one_model(collection, {"name": "Alice"}, MongoDocument)

            # Verify model instance
            assert result is not None
            assert isinstance(result, MongoDocument)
            assert result.name == "Alice"
            assert result.value == 25
            assert result.active is True

            # Test not found returns None
            not_found = mongo_service.find_one_model(
                collection, {"name": "NonExistent"}, MongoDocument
            )
            assert not_found is None

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_insert_one_model(self, mongo_service: MongoService) -> None:
        """Test inserting Pydantic model as document."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Create and insert model
            model = MongoDocument(name="Bob", value=35, active=False)
            result = mongo_service.insert_one_model(collection, model)

            # Verify insertion
            assert result.inserted_id is not None

            # Verify document in database
            found = mongo_service.find_one(collection, {"name": "Bob"})
            assert found is not None
            assert found["name"] == "Bob"
            assert found["value"] == 35
            assert found["active"] is False

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_find_many_models(self, mongo_service: MongoService) -> None:
        """Test finding and deserializing multiple documents to Pydantic models."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs = [
                {"name": "Alice", "value": 25, "active": True},
                {"name": "Bob", "value": 35, "active": False},
                {"name": "Charlie", "value": 45, "active": True},
            ]
            mongo_service.insert_many(collection, docs)

            # Find all and deserialize to models
            results = mongo_service.find_many_models(collection, {}, MongoDocument)

            # Verify models
            assert len(results) == 3
            assert all(isinstance(r, MongoDocument) for r in results)
            assert results[0].name == "Alice"
            assert results[1].name == "Bob"
            assert results[2].name == "Charlie"

            # Test with query filter
            active_results = mongo_service.find_many_models(
                collection, {"active": True}, MongoDocument
            )
            assert len(active_results) == 2
            assert all(r.active for r in active_results)

            # Test with pagination
            paginated = mongo_service.find_many_models(
                collection,
                {},
                MongoDocument,
                sort=[("value", 1)],
                limit=2,
                skip=1,
            )
            assert len(paginated) == 2
            assert paginated[0].name == "Bob"
            assert paginated[1].name == "Charlie"

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_insert_many_models(self, mongo_service: MongoService) -> None:
        """Test inserting multiple Pydantic models as documents."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Create models
            models = [
                MongoDocument(name="Alice", value=25),
                MongoDocument(name="Bob", value=35, active=False),
                MongoDocument(name="Charlie", value=45),
            ]

            # Insert models
            inserted_ids = mongo_service.insert_many_models(collection, models)

            # Verify insertions
            assert len(inserted_ids) == 3

            # Verify documents in database
            found = mongo_service.find_many(collection, {})
            assert len(found) == 3
            assert found[0]["name"] == "Alice"
            assert found[1]["name"] == "Bob"
            assert found[2]["name"] == "Charlie"

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_update_one_model(self, mongo_service: MongoService) -> None:
        """Test updating single document using Pydantic model."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert initial document
            doc = {"name": "Alice", "value": 25, "active": True}
            mongo_service.insert_one(collection, doc)

            # Update using model
            update_model = MongoDocument(name="Alice Updated", value=30, active=False)
            result = mongo_service.update_one_model(collection, {"name": "Alice"}, update_model)

            # Verify update
            assert result.modified_count == 1
            assert result.matched_count == 1

            # Verify updated document
            updated = mongo_service.find_one(collection, {"name": "Alice Updated"})
            assert updated is not None
            assert updated["value"] == 30
            assert updated["active"] is False

            # Test upsert
            new_model = MongoDocument(name="NewDoc", value=100)
            upsert_result = mongo_service.update_one_model(
                collection, {"name": "NewDoc"}, new_model, upsert=True
            )
            assert upsert_result.upserted_id is not None

            # Verify upserted document
            upserted = mongo_service.find_one(collection, {"name": "NewDoc"})
            assert upserted is not None
            assert upserted["value"] == 100

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()

    def test_update_many_models(self, mongo_service: MongoService) -> None:
        """Test updating multiple documents using Pydantic model."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs = [
                {"name": "doc1", "value": 10, "active": True},
                {"name": "doc2", "value": 20, "active": True},
                {"name": "doc3", "value": 30, "active": False},
            ]
            mongo_service.insert_many(collection, docs)

            # Update multiple using model
            update_model = MongoDocument(name="Updated", value=999, active=False)
            result = mongo_service.update_many_models(collection, {"active": True}, update_model)

            # Verify updates
            assert result.modified_count == 2
            assert result.matched_count == 2

            # Verify updated documents
            updated_docs = mongo_service.find_many(collection, {"name": "Updated"})
            assert len(updated_docs) == 2
            assert all(d["value"] == 999 for d in updated_docs)
            assert all(d["active"] is False for d in updated_docs)

        finally:
            # Cleanup
            mongo_service.get_collection(collection).drop()
