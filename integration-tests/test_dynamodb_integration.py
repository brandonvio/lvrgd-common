"""Integration tests for DynamoDB service.

Tests DynamoDB service operations against a real DynamoDB instance.
Configuration loaded from environment variables via conftest.py fixtures.
"""

import uuid

from pydantic import Field

from lvrgd.common.services.dynamodb.dynamodb_base_model import DynamoDBBaseModel
from lvrgd.common.services.dynamodb.dynamodb_service import DynamoDBService
from lvrgd.common.services.dynamodb.sort_key_condition import SortKeyCondition
from lvrgd.common.services.dynamodb.transaction_write_item import TransactionWriteItem


class DynamoDocument(DynamoDBBaseModel):
    """Document model for DynamoDB integration tests."""

    pk: str = Field(..., description="Partition key")
    sk: str = Field(..., description="Sort key")
    name: str = Field(..., description="Document name")
    value: int = Field(..., description="Document value")
    active: bool = Field(default=True, description="Document active status")


class TestDynamoDBIntegration:
    """Integration tests for DynamoDBService."""

    def test_dynamodb_connection_and_ping(self, dynamodb_service: DynamoDBService) -> None:
        """Test DynamoDB connection and ping functionality."""
        result = dynamodb_service.ping()
        assert result is True

    def test_save_and_get_one(self, dynamodb_service: DynamoDBService) -> None:
        """Test save and get_one operations."""
        test_id = uuid.uuid4().hex[:8]
        doc = DynamoDocument(
            pk=f"test-{test_id}", sk="doc1", name="Test Document", value=42, active=True
        )

        try:
            # Save document
            dynamodb_service.save(doc)

            # Get document
            retrieved = dynamodb_service.get_one(doc.pk, doc.sk, DynamoDocument)
            assert retrieved is not None
            assert retrieved.pk == doc.pk
            assert retrieved.sk == doc.sk
            assert retrieved.name == "Test Document"
            assert retrieved.value == 42
            assert retrieved.active is True

        finally:
            # Cleanup
            dynamodb_service.delete(doc.pk, doc.sk)

    def test_get_one_not_found(self, dynamodb_service: DynamoDBService) -> None:
        """Test get_one returns None for non-existent item."""
        test_id = uuid.uuid4().hex[:8]
        result = dynamodb_service.get_one(f"nonexistent-{test_id}", "sk1", DynamoDocument)
        assert result is None

    def test_update_operation(self, dynamodb_service: DynamoDBService) -> None:
        """Test update operation."""
        test_id = uuid.uuid4().hex[:8]
        doc = DynamoDocument(
            pk=f"test-{test_id}", sk="doc1", name="Original", value=10, active=True
        )

        try:
            # Save initial document
            dynamodb_service.save(doc)

            # Update document
            dynamodb_service.update(doc.pk, doc.sk, {"name": "Updated", "value": 100})

            # Verify update
            updated = dynamodb_service.get_one(doc.pk, doc.sk, DynamoDocument)
            assert updated is not None
            assert updated.name == "Updated"
            assert updated.value == 100

        finally:
            # Cleanup
            dynamodb_service.delete(doc.pk, doc.sk)

    def test_delete_operation(self, dynamodb_service: DynamoDBService) -> None:
        """Test delete operation."""
        test_id = uuid.uuid4().hex[:8]
        doc = DynamoDocument(
            pk=f"test-{test_id}", sk="doc1", name="To Delete", value=1, active=True
        )

        # Save and delete
        dynamodb_service.save(doc)
        dynamodb_service.delete(doc.pk, doc.sk)

        # Verify deletion
        result = dynamodb_service.get_one(doc.pk, doc.sk, DynamoDocument)
        assert result is None

    def test_query_by_pk(self, dynamodb_service: DynamoDBService) -> None:
        """Test query_by_pk operation."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk="sk1", name="Doc1", value=10, active=True),
            DynamoDocument(pk=pk, sk="sk2", name="Doc2", value=20, active=False),
            DynamoDocument(pk=pk, sk="sk3", name="Doc3", value=30, active=True),
        ]

        try:
            # Save documents
            for doc in docs:
                dynamodb_service.save(doc)

            # Query by partition key
            result = dynamodb_service.query_by_pk(pk, DynamoDocument)
            assert result.count == 3
            assert len(result.items) == 3

        finally:
            # Cleanup
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_query_by_pk_and_sk_eq(self, dynamodb_service: DynamoDBService) -> None:
        """Test query_by_pk_and_sk with eq operator."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk="sk1", name="Doc1", value=10, active=True),
            DynamoDocument(pk=pk, sk="sk2", name="Doc2", value=20, active=True),
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            # Query with eq operator
            condition = SortKeyCondition(operator="eq", value="sk1")
            result = dynamodb_service.query_by_pk_and_sk(pk, condition, DynamoDocument)
            assert result.count == 1
            assert result.items[0].sk == "sk1"

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_query_by_pk_and_sk_lt(self, dynamodb_service: DynamoDBService) -> None:
        """Test query_by_pk_and_sk with lt operator."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk="sk1", name="Doc1", value=10, active=True),
            DynamoDocument(pk=pk, sk="sk2", name="Doc2", value=20, active=True),
            DynamoDocument(pk=pk, sk="sk3", name="Doc3", value=30, active=True),
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            # Query with lt operator
            condition = SortKeyCondition(operator="lt", value="sk3")
            result = dynamodb_service.query_by_pk_and_sk(pk, condition, DynamoDocument)
            assert result.count == 2

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_query_by_pk_and_sk_begins_with(self, dynamodb_service: DynamoDBService) -> None:
        """Test query_by_pk_and_sk with begins_with operator."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk="prefix-1", name="Doc1", value=10, active=True),
            DynamoDocument(pk=pk, sk="prefix-2", name="Doc2", value=20, active=True),
            DynamoDocument(pk=pk, sk="other-1", name="Doc3", value=30, active=True),
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            # Query with begins_with operator
            condition = SortKeyCondition(operator="begins_with", value="prefix")
            result = dynamodb_service.query_by_pk_and_sk(pk, condition, DynamoDocument)
            assert result.count == 2

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_query_by_pk_and_sk_between(self, dynamodb_service: DynamoDBService) -> None:
        """Test query_by_pk_and_sk with between operator."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk="sk1", name="Doc1", value=10, active=True),
            DynamoDocument(pk=pk, sk="sk2", name="Doc2", value=20, active=True),
            DynamoDocument(pk=pk, sk="sk3", name="Doc3", value=30, active=True),
            DynamoDocument(pk=pk, sk="sk4", name="Doc4", value=40, active=True),
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            # Query with between operator
            condition = SortKeyCondition(operator="between", value="sk2", value2="sk3")
            result = dynamodb_service.query_by_pk_and_sk(pk, condition, DynamoDocument)
            assert result.count == 2

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_query_with_pagination(self, dynamodb_service: DynamoDBService) -> None:
        """Test query with pagination."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk=f"sk{i:03d}", name=f"Doc{i}", value=i, active=True)
            for i in range(10)
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            # First page
            result1 = dynamodb_service.query_by_pk(pk, DynamoDocument, limit=5)
            assert len(result1.items) == 5
            assert result1.last_evaluated_key is not None

            # Second page
            result2 = dynamodb_service.query_by_pk(
                pk, DynamoDocument, limit=5, last_evaluated_key=result1.last_evaluated_key
            )
            assert len(result2.items) == 5

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_batch_get(self, dynamodb_service: DynamoDBService) -> None:
        """Test batch_get operation."""
        test_id = uuid.uuid4().hex[:8]
        docs = [
            DynamoDocument(pk=f"test-{test_id}", sk=f"sk{i}", name=f"Doc{i}", value=i, active=True)
            for i in range(5)
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            # Batch get
            keys = [(doc.pk, doc.sk) for doc in docs]
            results = dynamodb_service.batch_get(keys, DynamoDocument)
            assert len(results) == 5

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_batch_write(self, dynamodb_service: DynamoDBService) -> None:
        """Test batch_write operation."""
        test_id = uuid.uuid4().hex[:8]
        docs = [
            DynamoDocument(pk=f"test-{test_id}", sk=f"sk{i}", name=f"Doc{i}", value=i, active=True)
            for i in range(10)
        ]

        try:
            # Batch write
            dynamodb_service.batch_write(docs)

            # Verify all written
            for doc in docs:
                result = dynamodb_service.get_one(doc.pk, doc.sk, DynamoDocument)
                assert result is not None
                assert result.name == doc.name

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_transact_write_put(self, dynamodb_service: DynamoDBService) -> None:
        """Test transact_write with put operation."""
        test_id = uuid.uuid4().hex[:8]
        docs = [
            DynamoDocument(pk=f"test-{test_id}", sk="sk1", name="Doc1", value=1, active=True),
            DynamoDocument(pk=f"test-{test_id}", sk="sk2", name="Doc2", value=2, active=True),
        ]

        try:
            # Transaction write
            operations = [TransactionWriteItem(operation="put", item=doc) for doc in docs]
            dynamodb_service.transact_write(operations)

            # Verify both written
            for doc in docs:
                result = dynamodb_service.get_one(doc.pk, doc.sk, DynamoDocument)
                assert result is not None

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_transact_write_update_delete(self, dynamodb_service: DynamoDBService) -> None:
        """Test transact_write with update and delete operations."""
        test_id = uuid.uuid4().hex[:8]
        doc1 = DynamoDocument(pk=f"test-{test_id}", sk="sk1", name="Doc1", value=1, active=True)
        doc2 = DynamoDocument(pk=f"test-{test_id}", sk="sk2", name="Doc2", value=2, active=True)

        try:
            # Save initial documents
            dynamodb_service.save(doc1)
            dynamodb_service.save(doc2)

            # Transaction: update doc1, delete doc2
            operations = [
                TransactionWriteItem(
                    operation="update", pk=doc1.pk, sk=doc1.sk, updates={"value": 100}
                ),
                TransactionWriteItem(operation="delete", pk=doc2.pk, sk=doc2.sk),
            ]
            dynamodb_service.transact_write(operations)

            # Verify update
            updated = dynamodb_service.get_one(doc1.pk, doc1.sk, DynamoDocument)
            assert updated is not None
            assert updated.value == 100

            # Verify deletion
            deleted = dynamodb_service.get_one(doc2.pk, doc2.sk, DynamoDocument)
            assert deleted is None

        finally:
            dynamodb_service.delete(doc1.pk, doc1.sk)

    def test_transact_get(self, dynamodb_service: DynamoDBService) -> None:
        """Test transact_get operation."""
        test_id = uuid.uuid4().hex[:8]
        docs = [
            DynamoDocument(pk=f"test-{test_id}", sk="sk1", name="Doc1", value=1, active=True),
            DynamoDocument(pk=f"test-{test_id}", sk="sk2", name="Doc2", value=2, active=True),
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            # Transaction get
            keys = [(doc.pk, doc.sk) for doc in docs]
            results = dynamodb_service.transact_get(keys, DynamoDocument)
            assert len(results) == 2

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_count_without_condition(self, dynamodb_service: DynamoDBService) -> None:
        """Test count operation without SK condition."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk=f"sk{i}", name=f"Doc{i}", value=i, active=True)
            for i in range(5)
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            count = dynamodb_service.count(pk)
            assert count == 5

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)

    def test_count_with_condition(self, dynamodb_service: DynamoDBService) -> None:
        """Test count operation with SK condition."""
        test_id = uuid.uuid4().hex[:8]
        pk = f"test-{test_id}"
        docs = [
            DynamoDocument(pk=pk, sk=f"sk{i:03d}", name=f"Doc{i}", value=i, active=True)
            for i in range(10)
        ]

        try:
            for doc in docs:
                dynamodb_service.save(doc)

            condition = SortKeyCondition(operator="lt", value="sk005")
            count = dynamodb_service.count(pk, condition)
            assert count == 5

        finally:
            for doc in docs:
                dynamodb_service.delete(doc.pk, doc.sk)
