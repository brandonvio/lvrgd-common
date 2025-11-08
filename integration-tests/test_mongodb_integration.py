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
