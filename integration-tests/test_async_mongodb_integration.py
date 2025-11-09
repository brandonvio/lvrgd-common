"""Integration tests for async MongoDB service.

Tests async MongoDB service operations against a real MongoDB instance.
Configuration loaded from environment variables via conftest.py fixtures.
"""

import uuid
from typing import Any

import pytest
from pydantic import BaseModel, Field
from pymongo.operations import InsertOne, UpdateOne

from lvrgd.common.services.mongodb.async_mongodb_service import AsyncMongoService


class AsyncMongoDocument(BaseModel):
    """Document model for async MongoDB integration tests."""

    name: str = Field(..., description="Document name")
    value: int = Field(..., description="Document value")
    active: bool = Field(default=True, description="Document active status")


class TestAsyncMongoDBIntegration:
    """Integration tests for AsyncMongoService."""

    @pytest.mark.asyncio
    async def test_mongodb_connection_and_ping(
        self, async_mongo_service: AsyncMongoService
    ) -> None:
        """Test async MongoDB connection and ping functionality."""
        # Ping server
        server_info = await async_mongo_service.ping()
        assert isinstance(server_info, dict)
        assert "version" in server_info

    @pytest.mark.asyncio
    async def test_insert_and_find_one(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async insert and find single document."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert document
            doc: dict[str, Any] = {"name": "test-doc", "value": 42, "active": True}
            result = await async_mongo_service.insert_one(collection, doc)
            assert result.inserted_id is not None

            # Find document
            found = await async_mongo_service.find_one(collection, {"name": "test-doc"})
            assert found is not None
            assert found["name"] == "test-doc"
            assert found["value"] == 42
            assert found["active"] is True

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_insert_many_and_find_many(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async batch insert and query multiple documents."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert multiple documents
            docs: list[dict[str, Any]] = [
                {"name": "doc1", "value": 10, "active": True},
                {"name": "doc2", "value": 20, "active": False},
                {"name": "doc3", "value": 30, "active": True},
            ]
            inserted_ids = await async_mongo_service.insert_many(collection, docs)
            assert len(inserted_ids) == 3

            # Find all documents
            found = await async_mongo_service.find_many(collection, {})
            assert len(found) == 3

            # Find with query filter
            active_docs = await async_mongo_service.find_many(collection, {"active": True})
            assert len(active_docs) == 2

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_update_operations(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async update_one and update_many operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs: list[dict[str, Any]] = [
                {"name": "doc1", "value": 10},
                {"name": "doc2", "value": 20},
                {"name": "doc3", "value": 30},
            ]
            await async_mongo_service.insert_many(collection, docs)

            # Update one document
            result = await async_mongo_service.update_one(
                collection,
                {"name": "doc1"},
                {"$set": {"value": 100}},
            )
            assert result.modified_count == 1

            # Verify update
            updated = await async_mongo_service.find_one(collection, {"name": "doc1"})
            assert updated is not None
            assert updated["value"] == 100

            # Update many documents
            result = await async_mongo_service.update_many(
                collection,
                {"value": {"$gte": 20}},
                {"$inc": {"value": 5}},
            )
            assert result.modified_count == 3

            # Verify updates
            doc2 = await async_mongo_service.find_one(collection, {"name": "doc2"})
            doc3 = await async_mongo_service.find_one(collection, {"name": "doc3"})
            assert doc2 is not None
            assert doc2["value"] == 25
            assert doc3 is not None
            assert doc3["value"] == 35

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_delete_operations(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async delete_one and delete_many operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs: list[dict[str, Any]] = [
                {"name": "doc1", "status": "active"},
                {"name": "doc2", "status": "inactive"},
                {"name": "doc3", "status": "inactive"},
            ]
            await async_mongo_service.insert_many(collection, docs)

            # Delete one document
            result = await async_mongo_service.delete_one(collection, {"name": "doc1"})
            assert result.deleted_count == 1

            # Verify deletion
            remaining = await async_mongo_service.find_many(collection, {})
            assert len(remaining) == 2

            # Delete many documents
            result = await async_mongo_service.delete_many(collection, {"status": "inactive"})
            assert result.deleted_count == 2

            # Verify all deleted
            final_count = await async_mongo_service.count_documents(collection, {})
            assert final_count == 0

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_count_documents(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async count_documents operation."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs: list[dict[str, Any]] = [
                {"status": "active"},
                {"status": "active"},
                {"status": "inactive"},
            ]
            await async_mongo_service.insert_many(collection, docs)

            # Count all documents
            total_count = await async_mongo_service.count_documents(collection, {})
            assert total_count == 3

            # Count active documents
            active_count = await async_mongo_service.count_documents(
                collection, {"status": "active"}
            )
            assert active_count == 2

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_aggregation(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async aggregation pipeline."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert test documents
            docs: list[dict[str, Any]] = [
                {"category": "A", "value": 10},
                {"category": "A", "value": 20},
                {"category": "B", "value": 30},
            ]
            await async_mongo_service.insert_many(collection, docs)

            # Run aggregation
            pipeline: list[dict[str, Any]] = [
                {"$group": {"_id": "$category", "total": {"$sum": "$value"}}}
            ]
            results = await async_mongo_service.aggregate(collection, pipeline)

            assert len(results) == 2
            category_totals = {r["_id"]: r["total"] for r in results}
            assert category_totals["A"] == 30
            assert category_totals["B"] == 30

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_index_creation(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async index creation."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Create unique index
            index_name = await async_mongo_service.create_index(collection, "name", unique=True)
            assert index_name is not None
            assert "name" in index_name

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_bulk_write(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async bulk write operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Perform bulk write
            operations = [
                InsertOne({"name": "doc1", "value": 10}),
                InsertOne({"name": "doc2", "value": 20}),
                UpdateOne({"name": "doc1"}, {"$set": {"value": 15}}),
            ]
            result = await async_mongo_service.bulk_write(collection, operations)

            assert result.inserted_count == 2
            assert result.modified_count == 1

            # Verify results
            doc1 = await async_mongo_service.find_one(collection, {"name": "doc1"})
            assert doc1 is not None
            assert doc1["value"] == 15

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()

    @pytest.mark.asyncio
    async def test_pydantic_model_support(self, async_mongo_service: AsyncMongoService) -> None:
        """Test async Pydantic model insert and find operations."""
        collection = f"test_collection_{uuid.uuid4().hex[:8]}"

        try:
            # Insert Pydantic model
            model = AsyncMongoDocument(name="pydantic-doc", value=123, active=True)
            result = await async_mongo_service.insert_one_model(collection, model)
            assert result.inserted_id is not None

            # Find as Pydantic model
            found = await async_mongo_service.find_one_model(
                collection, {"name": "pydantic-doc"}, AsyncMongoDocument
            )
            assert found is not None
            assert found.name == "pydantic-doc"
            assert found.value == 123
            assert found.active is True

            # Insert multiple models
            models = [
                AsyncMongoDocument(name="model1", value=10),
                AsyncMongoDocument(name="model2", value=20),
            ]
            inserted_ids = await async_mongo_service.insert_many_models(collection, models)
            assert len(inserted_ids) == 2

            # Find multiple as models
            found_models = await async_mongo_service.find_many_models(
                collection, {}, AsyncMongoDocument
            )
            assert len(found_models) == 3

            # Update with model
            update_model = AsyncMongoDocument(name="pydantic-doc", value=999, active=False)
            update_result = await async_mongo_service.update_one_model(
                collection, {"name": "pydantic-doc"}, update_model
            )
            assert update_result.modified_count == 1

            # Verify update
            updated_doc = await async_mongo_service.find_one_model(
                collection, {"name": "pydantic-doc"}, AsyncMongoDocument
            )
            assert updated_doc is not None
            assert updated_doc.value == 999
            assert updated_doc.active is False

        finally:
            # Cleanup
            await async_mongo_service.get_collection(collection).drop()
