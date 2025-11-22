"""Unit tests for DynamoDBService.

Comprehensive test coverage for all DynamoDB service methods with mocking.
"""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from lvrgd.common.exceptions.dynamodb_exceptions import (
    DynamoDBBatchOperationError,
    DynamoDBServiceError,
    DynamoDBTransactionError,
)
from lvrgd.common.services import LoggingService
from lvrgd.common.services.dynamodb.dynamodb_base_model import DynamoDBBaseModel
from lvrgd.common.services.dynamodb.dynamodb_config import DynamoDBConfig
from lvrgd.common.services.dynamodb.dynamodb_service import DynamoDBService
from lvrgd.common.services.dynamodb.sort_key_condition import SortKeyCondition
from lvrgd.common.services.dynamodb.transaction_write_item import TransactionWriteItem


class SampleDocument(DynamoDBBaseModel):
    """Sample document model for unit tests."""

    pk: str
    sk: str
    name: str
    value: int


@pytest.fixture
def mock_logger() -> Mock:
    """Create mock LoggingService."""
    return Mock(spec=LoggingService)


@pytest.fixture
def config() -> DynamoDBConfig:
    """Create DynamoDB configuration."""
    return DynamoDBConfig(
        table_name="test-table",
        region="us-east-1",
        endpoint_url="http://localhost:8000",
    )


@pytest.fixture
def mock_table() -> Mock:
    """Create mock DynamoDB Table."""
    mock = Mock()
    mock.meta.client = Mock()
    mock.table_status = "ACTIVE"
    return mock


@pytest.fixture
def db_service(mock_logger: Mock, config: DynamoDBConfig, mock_table: Mock) -> DynamoDBService:
    """Create DynamoDBService with mocked boto3."""
    with patch("boto3.resource") as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb

        service = DynamoDBService(logger=mock_logger, config=config)
        service._table = mock_table
        return service


def test_service_initialization(mock_logger: Mock, config: DynamoDBConfig) -> None:
    """Test DynamoDBService initialization."""
    with patch("boto3.resource") as mock_resource:
        mock_table = Mock()
        mock_table.table_status = "ACTIVE"
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb

        service = DynamoDBService(logger=mock_logger, config=config)

        assert service.log == mock_logger
        assert service.config == config
        mock_resource.assert_called()


def test_save_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful save operation."""
    item = SampleDocument(pk="test-pk", sk="test-sk", name="Test", value=42)

    db_service.save(item)

    mock_table.put_item.assert_called_once_with(
        Item={"pk": "test-pk", "sk": "test-sk", "name": "Test", "value": 42}
    )


def test_save_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test save operation failure."""
    item = SampleDocument(pk="test-pk", sk="test-sk", name="Test", value=42)
    mock_table.put_item.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "PutItem"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.save(item)

    assert exc_info.value.operation == "save"
    assert exc_info.value.pk == "test-pk"
    assert exc_info.value.sk == "test-sk"


def test_get_one_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful get_one operation."""
    mock_table.get_item.return_value = {
        "Item": {"pk": "test-pk", "sk": "test-sk", "name": "Test", "value": 42}
    }

    result = db_service.get_one("test-pk", "test-sk", SampleDocument)

    assert result is not None
    assert result.pk == "test-pk"
    assert result.sk == "test-sk"
    assert result.name == "Test"
    assert result.value == 42
    mock_table.get_item.assert_called_once_with(Key={"pk": "test-pk", "sk": "test-sk"})


def test_get_one_not_found(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test get_one when item not found."""
    mock_table.get_item.return_value = {}

    result = db_service.get_one("test-pk", "test-sk", SampleDocument)

    assert result is None


def test_get_one_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test get_one operation failure."""
    mock_table.get_item.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "GetItem"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.get_one("test-pk", "test-sk", SampleDocument)

    assert exc_info.value.operation == "get_one"


def test_delete_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful delete operation."""
    db_service.delete("test-pk", "test-sk")

    mock_table.delete_item.assert_called_once_with(Key={"pk": "test-pk", "sk": "test-sk"})


def test_delete_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test delete operation failure."""
    mock_table.delete_item.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "DeleteItem"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.delete("test-pk", "test-sk")

    assert exc_info.value.operation == "delete"


def test_update_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful update operation."""
    updates = {"name": "Updated", "value": 100}

    db_service.update("test-pk", "test-sk", updates)

    mock_table.update_item.assert_called_once()
    call_args = mock_table.update_item.call_args[1]
    assert call_args["Key"] == {"pk": "test-pk", "sk": "test-sk"}
    assert "SET" in call_args["UpdateExpression"]


def test_update_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test update operation failure."""
    mock_table.update_item.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "UpdateItem"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.update("test-pk", "test-sk", {"name": "Updated"})

    assert exc_info.value.operation == "update"


def test_query_by_pk_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful query_by_pk operation."""
    mock_table.query.return_value = {
        "Items": [
            {"pk": "test-pk", "sk": "sk1", "name": "Item1", "value": 1},
            {"pk": "test-pk", "sk": "sk2", "name": "Item2", "value": 2},
        ],
        "Count": 2,
    }

    result = db_service.query_by_pk("test-pk", SampleDocument)

    assert len(result.items) == 2
    assert result.count == 2
    assert result.last_evaluated_key is None
    assert result.items[0].name == "Item1"
    assert result.items[1].name == "Item2"


def test_query_by_pk_with_limit(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test query_by_pk with limit."""
    mock_table.query.return_value = {
        "Items": [{"pk": "test-pk", "sk": "sk1", "name": "Item1", "value": 1}],
        "Count": 1,
        "LastEvaluatedKey": {"pk": "test-pk", "sk": "sk1"},
    }

    result = db_service.query_by_pk("test-pk", SampleDocument, limit=1)

    assert len(result.items) == 1
    assert result.last_evaluated_key == {"pk": "test-pk", "sk": "sk1"}
    call_args = mock_table.query.call_args[1]
    assert call_args["Limit"] == 1


def test_query_by_pk_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test query_by_pk operation failure."""
    mock_table.query.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "Query"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.query_by_pk("test-pk", SampleDocument)

    assert exc_info.value.operation == "query_by_pk"


def test_query_by_pk_and_sk_eq(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test query_by_pk_and_sk with eq operator."""
    sk_condition = SortKeyCondition(operator="eq", value="sk1")
    mock_table.query.return_value = {
        "Items": [{"pk": "test-pk", "sk": "sk1", "name": "Item1", "value": 1}],
        "Count": 1,
    }

    result = db_service.query_by_pk_and_sk("test-pk", sk_condition, SampleDocument)

    assert len(result.items) == 1
    assert result.items[0].sk == "sk1"


def test_query_by_pk_and_sk_lt(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test query_by_pk_and_sk with lt operator."""
    sk_condition = SortKeyCondition(operator="lt", value="sk5")
    mock_table.query.return_value = {
        "Items": [
            {"pk": "test-pk", "sk": "sk1", "name": "Item1", "value": 1},
            {"pk": "test-pk", "sk": "sk2", "name": "Item2", "value": 2},
        ],
        "Count": 2,
    }

    result = db_service.query_by_pk_and_sk("test-pk", sk_condition, SampleDocument)

    assert len(result.items) == 2


def test_query_by_pk_and_sk_begins_with(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test query_by_pk_and_sk with begins_with operator."""
    sk_condition = SortKeyCondition(operator="begins_with", value="prefix")
    mock_table.query.return_value = {
        "Items": [{"pk": "test-pk", "sk": "prefix-1", "name": "Item1", "value": 1}],
        "Count": 1,
    }

    result = db_service.query_by_pk_and_sk("test-pk", sk_condition, SampleDocument)

    assert len(result.items) == 1


def test_query_by_pk_and_sk_between(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test query_by_pk_and_sk with between operator."""
    sk_condition = SortKeyCondition(operator="between", value="sk1", value2="sk5")
    mock_table.query.return_value = {
        "Items": [
            {"pk": "test-pk", "sk": "sk2", "name": "Item2", "value": 2},
            {"pk": "test-pk", "sk": "sk3", "name": "Item3", "value": 3},
        ],
        "Count": 2,
    }

    result = db_service.query_by_pk_and_sk("test-pk", sk_condition, SampleDocument)

    assert len(result.items) == 2


def test_query_by_pk_and_sk_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test query_by_pk_and_sk operation failure."""
    sk_condition = SortKeyCondition(operator="eq", value="sk1")
    mock_table.query.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "Query"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.query_by_pk_and_sk("test-pk", sk_condition, SampleDocument)

    assert exc_info.value.operation == "query_by_pk_and_sk"


def test_batch_get_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful batch_get operation."""
    mock_table.meta.client.batch_get_item.return_value = {
        "Responses": {
            "test-table": [
                {"pk": "pk1", "sk": "sk1", "name": "Item1", "value": 1},
                {"pk": "pk2", "sk": "sk2", "name": "Item2", "value": 2},
            ]
        }
    }

    keys = [("pk1", "sk1"), ("pk2", "sk2")]
    result = db_service.batch_get(keys, SampleDocument)

    assert len(result) == 2
    assert result[0].name == "Item1"
    assert result[1].name == "Item2"


def test_batch_get_chunking(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test batch_get with chunking for >100 items."""
    mock_table.meta.client.batch_get_item.return_value = {"Responses": {"test-table": []}}

    keys = [(f"pk{i}", f"sk{i}") for i in range(150)]
    db_service.batch_get(keys, SampleDocument)

    assert mock_table.meta.client.batch_get_item.call_count == 2


def test_batch_get_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test batch_get operation failure."""
    mock_table.meta.client.batch_get_item.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "BatchGetItem"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.batch_get([("pk1", "sk1")], SampleDocument)

    assert exc_info.value.operation == "batch_get"


def test_batch_write_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful batch_write operation."""
    mock_table.meta.client.batch_write_item.return_value = {"UnprocessedItems": {}}

    items = [
        SampleDocument(pk="pk1", sk="sk1", name="Item1", value=1),
        SampleDocument(pk="pk2", sk="sk2", name="Item2", value=2),
    ]

    db_service.batch_write(items)

    mock_table.meta.client.batch_write_item.assert_called_once()


def test_batch_write_chunking(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test batch_write with chunking for >25 items."""
    mock_table.meta.client.batch_write_item.return_value = {"UnprocessedItems": {}}

    items = [SampleDocument(pk=f"pk{i}", sk=f"sk{i}", name=f"Item{i}", value=i) for i in range(30)]

    db_service.batch_write(items)

    assert mock_table.meta.client.batch_write_item.call_count == 2


def test_batch_write_unprocessed_items(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test batch_write with unprocessed items."""
    mock_table.meta.client.batch_write_item.return_value = {
        "UnprocessedItems": {"test-table": [{"PutRequest": {"Item": {"pk": "pk1", "sk": "sk1"}}}]}
    }

    items = [SampleDocument(pk="pk1", sk="sk1", name="Item1", value=1)]

    with pytest.raises(DynamoDBBatchOperationError) as exc_info:
        db_service.batch_write(items)

    assert exc_info.value.operation == "batch_write"
    assert len(exc_info.value.failed_items) == 1


def test_batch_write_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test batch_write operation failure."""
    mock_table.meta.client.batch_write_item.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "BatchWriteItem"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.batch_write([SampleDocument(pk="pk1", sk="sk1", name="Item1", value=1)])

    assert exc_info.value.operation == "batch_write"


def test_transact_write_put(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test transact_write with put operation."""
    mock_table.meta.client.transact_write_items.return_value = {}

    operations = [
        TransactionWriteItem(
            operation="put", item=SampleDocument(pk="pk1", sk="sk1", name="Item1", value=1)
        )
    ]

    db_service.transact_write(operations)

    mock_table.meta.client.transact_write_items.assert_called_once()
    call_args = mock_table.meta.client.transact_write_items.call_args[1]
    assert "Put" in call_args["TransactItems"][0]


def test_transact_write_update(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test transact_write with update operation."""
    mock_table.meta.client.transact_write_items.return_value = {}

    operations = [
        TransactionWriteItem(
            operation="update", pk="pk1", sk="sk1", updates={"name": "Updated", "value": 100}
        )
    ]

    db_service.transact_write(operations)

    call_args = mock_table.meta.client.transact_write_items.call_args[1]
    assert "Update" in call_args["TransactItems"][0]


def test_transact_write_delete(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test transact_write with delete operation."""
    mock_table.meta.client.transact_write_items.return_value = {}

    operations = [TransactionWriteItem(operation="delete", pk="pk1", sk="sk1")]

    db_service.transact_write(operations)

    call_args = mock_table.meta.client.transact_write_items.call_args[1]
    assert "Delete" in call_args["TransactItems"][0]


def test_transact_write_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test transact_write operation failure."""
    mock_table.meta.client.transact_write_items.side_effect = ClientError(
        {"Error": {"Code": "TransactionCanceledException", "Message": "Transaction cancelled"}},
        "TransactWriteItems",
    )

    operations = [
        TransactionWriteItem(
            operation="put", item=SampleDocument(pk="pk1", sk="sk1", name="Item1", value=1)
        )
    ]

    with pytest.raises(DynamoDBTransactionError) as exc_info:
        db_service.transact_write(operations)

    assert exc_info.value.operation == "transact_write"


def test_transact_get_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful transact_get operation."""
    mock_table.meta.client.transact_get_items.return_value = {
        "Responses": [
            {"Item": {"pk": "pk1", "sk": "sk1", "name": "Item1", "value": 1}},
            {"Item": {"pk": "pk2", "sk": "sk2", "name": "Item2", "value": 2}},
        ]
    }

    keys = [("pk1", "sk1"), ("pk2", "sk2")]
    result = db_service.transact_get(keys, SampleDocument)

    assert len(result) == 2
    assert result[0].name == "Item1"
    assert result[1].name == "Item2"


def test_transact_get_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test transact_get operation failure."""
    mock_table.meta.client.transact_get_items.side_effect = ClientError(
        {"Error": {"Code": "TransactionCanceledException", "Message": "Transaction cancelled"}},
        "TransactGetItems",
    )

    with pytest.raises(DynamoDBTransactionError) as exc_info:
        db_service.transact_get([("pk1", "sk1")], SampleDocument)

    assert exc_info.value.operation == "transact_get"


def test_ping_success(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test successful ping operation."""
    mock_table.table_status = "ACTIVE"

    result = db_service.ping()

    assert result is True
    mock_table.load.assert_called_once()


def test_ping_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test ping operation failure."""
    mock_table.load.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "DescribeTable",
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.ping()

    assert exc_info.value.operation == "ping"


def test_count_without_sk_condition(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test count operation without SK condition."""
    mock_table.query.return_value = {"Count": 5}

    result = db_service.count("test-pk")

    assert result == 5
    call_args = mock_table.query.call_args[1]
    assert call_args["Select"] == "COUNT"


def test_count_with_sk_condition(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test count operation with SK condition."""
    sk_condition = SortKeyCondition(operator="begins_with", value="prefix")
    mock_table.query.return_value = {"Count": 3}

    result = db_service.count("test-pk", sk_condition)

    assert result == 3


def test_count_failure(db_service: DynamoDBService, mock_table: Mock) -> None:
    """Test count operation failure."""
    mock_table.query.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "Internal error"}}, "Query"
    )

    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.count("test-pk")

    assert exc_info.value.operation == "count"


def test_build_key_condition_all_operators(db_service: DynamoDBService) -> None:
    """Test _build_key_condition_expression with all operators."""
    operators = ["eq", "lt", "le", "gt", "ge", "begins_with"]

    for op in operators:
        condition = SortKeyCondition(operator=op, value="test")
        result = db_service._build_key_condition_expression(condition)
        assert result is not None

    # Test between operator
    between_condition = SortKeyCondition(operator="between", value="a", value2="z")
    result = db_service._build_key_condition_expression(between_condition)
    assert result is not None
