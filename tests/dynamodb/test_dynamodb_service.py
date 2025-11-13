"""Test suite for DynamoDB service implementation.

This module contains tests for the DynamoDB service including:
- Configuration validation
- Base model validation
- Service initialization
- CRUD operations
- Query operations
"""

from collections.abc import Iterator
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from pydantic import ValidationError

from lvrgd.common.services import LoggingService
from lvrgd.common.services.dynamodb import DynamoDBBaseModel, DynamoDBConfig, DynamoDBService


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger for testing."""
    return Mock(spec=LoggingService)


@pytest.fixture
def valid_config() -> DynamoDBConfig:
    """Create a valid DynamoDB configuration for testing."""
    return DynamoDBConfig(
        table_name="test-table",
        region="us-east-1",
        endpoint_url="http://localhost:8000",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@pytest.fixture
def minimal_config() -> DynamoDBConfig:
    """Create a minimal DynamoDB configuration for testing."""
    return DynamoDBConfig(
        table_name="test-table",
    )


@pytest.fixture
def mock_boto3_client() -> Iterator[Mock]:
    """Create a mock boto3 client."""
    with patch("lvrgd.common.services.dynamodb.dynamodb_service.boto3.client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_boto3_resource() -> Iterator[Mock]:
    """Create a mock boto3 resource."""
    with patch("lvrgd.common.services.dynamodb.dynamodb_service.boto3.resource") as mock_resource:
        yield mock_resource


@pytest.fixture
def dynamodb_service(
    mock_logger: Mock,
    valid_config: DynamoDBConfig,
    mock_boto3_client: Mock,
    mock_boto3_resource: Mock,
) -> DynamoDBService:
    """Create a DynamoDBService instance with mocked dependencies."""
    mock_table = Mock()
    mock_resource_instance = Mock()
    mock_resource_instance.Table.return_value = mock_table
    mock_boto3_resource.return_value = mock_resource_instance

    mock_client_instance = Mock()
    mock_client_instance.describe_table.return_value = {"Table": {"TableName": "test-table"}}
    mock_boto3_client.return_value = mock_client_instance

    service = DynamoDBService(mock_logger, valid_config)
    service._client = mock_client_instance
    service._table = mock_table
    return service


class TestDynamoDBConfig:
    """Test DynamoDB configuration validation."""

    def test_valid_configuration(self, valid_config: DynamoDBConfig) -> None:
        """Test valid configuration creation."""
        assert valid_config.table_name == "test-table"
        assert valid_config.region == "us-east-1"
        assert valid_config.endpoint_url == "http://localhost:8000"
        assert valid_config.aws_access_key_id == "test"
        assert valid_config.aws_secret_access_key == "test"

    def test_minimal_configuration(self, minimal_config: DynamoDBConfig) -> None:
        """Test minimal configuration with defaults."""
        assert minimal_config.table_name == "test-table"
        assert minimal_config.region == "us-east-1"
        assert minimal_config.endpoint_url is None
        assert minimal_config.aws_access_key_id is None
        assert minimal_config.aws_secret_access_key is None

    def test_empty_table_name_validation(self) -> None:
        """Test validation fails for empty table name."""
        with pytest.raises(ValidationError):
            DynamoDBConfig(table_name="")

    def test_whitespace_table_name_validation(self) -> None:
        """Test validation fails for whitespace-only table name."""
        with pytest.raises(ValidationError):
            DynamoDBConfig(table_name="   ")

    def test_empty_region_validation(self) -> None:
        """Test validation fails for empty region."""
        with pytest.raises(ValidationError):
            DynamoDBConfig(table_name="test-table", region="")

    def test_whitespace_region_validation(self) -> None:
        """Test validation fails for whitespace-only region."""
        with pytest.raises(ValidationError):
            DynamoDBConfig(table_name="test-table", region="   ")

    def test_optional_fields(self) -> None:
        """Test optional fields can be None."""
        config = DynamoDBConfig(
            table_name="test-table",
            endpoint_url=None,
            aws_access_key_id=None,
            aws_secret_access_key=None,
        )
        assert config.endpoint_url is None
        assert config.aws_access_key_id is None
        assert config.aws_secret_access_key is None


class TestDynamoDBBaseModel:
    """Test DynamoDB base model validation."""

    def test_model_creation(self) -> None:
        """Test base model creation with pk and sk."""
        model = DynamoDBBaseModel(pk="USER#123", sk="PROFILE#main")
        assert model.pk == "USER#123"
        assert model.sk == "PROFILE#main"

    def test_model_dump(self) -> None:
        """Test model serialization to dict."""
        model = DynamoDBBaseModel(pk="USER#123", sk="PROFILE#main")
        data = model.model_dump()
        assert data == {"pk": "USER#123", "sk": "PROFILE#main"}

    def test_model_validate(self) -> None:
        """Test model deserialization from dict."""
        data = {"pk": "USER#123", "sk": "PROFILE#main"}
        model = DynamoDBBaseModel.model_validate(data)
        assert model.pk == "USER#123"
        assert model.sk == "PROFILE#main"

    def test_model_validation_fails_missing_pk(self) -> None:
        """Test validation fails when pk is missing."""
        with pytest.raises(ValidationError):
            DynamoDBBaseModel(sk="PROFILE#main")

    def test_model_validation_fails_missing_sk(self) -> None:
        """Test validation fails when sk is missing."""
        with pytest.raises(ValidationError):
            DynamoDBBaseModel(pk="USER#123")


class TestDynamoDBServiceInitialization:
    """Test DynamoDB service initialization."""

    def test_initialization_with_full_config(
        self,
        mock_logger: Mock,
        valid_config: DynamoDBConfig,
        mock_boto3_client: Mock,
        mock_boto3_resource: Mock,
    ) -> None:
        """Test successful DynamoDB initialization with full configuration."""
        mock_client_instance = Mock()
        mock_client_instance.describe_table.return_value = {"Table": {"TableName": "test-table"}}
        mock_boto3_client.return_value = mock_client_instance

        mock_table = Mock()
        mock_resource_instance = Mock()
        mock_resource_instance.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource_instance

        service = DynamoDBService(mock_logger, valid_config)

        mock_logger.info.assert_any_call(
            "Initializing DynamoDB connection",
            table_name=valid_config.table_name,
            region=valid_config.region,
        )
        mock_boto3_client.assert_called_once()
        assert service.config == valid_config
        assert service.log == mock_logger

    def test_initialization_with_minimal_config(
        self,
        mock_logger: Mock,
        minimal_config: DynamoDBConfig,
        mock_boto3_client: Mock,
        mock_boto3_resource: Mock,
    ) -> None:
        """Test successful DynamoDB initialization with minimal configuration."""
        mock_client_instance = Mock()
        mock_client_instance.describe_table.return_value = {"Table": {"TableName": "test-table"}}
        mock_boto3_client.return_value = mock_client_instance

        mock_table = Mock()
        mock_resource_instance = Mock()
        mock_resource_instance.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource_instance

        service = DynamoDBService(mock_logger, minimal_config)

        assert service.config == minimal_config
        assert service.log == mock_logger

    def test_required_dependencies_no_defaults(self) -> None:
        """Test that all dependencies are required (no Optional, no defaults)."""
        # This test verifies the signature requires both parameters
        with pytest.raises(TypeError):
            DynamoDBService()


class TestDynamoDBServiceCRUD:
    """Test DynamoDB service CRUD operations."""

    def test_ping_success(self, dynamodb_service: DynamoDBService) -> None:
        """Test successful ping operation."""
        dynamodb_service._client.describe_table.return_value = {"Table": {"TableName": "test"}}
        result = dynamodb_service.ping()
        assert result is True

    def test_ping_failure(self, dynamodb_service: DynamoDBService, mock_logger: Mock) -> None:
        """Test ping operation failure."""
        dynamodb_service._client.describe_table.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}},
            "DescribeTable",
        )
        result = dynamodb_service.ping()
        assert result is False
        mock_logger.exception.assert_called_once()

    def test_create_item(self, dynamodb_service: DynamoDBService, mock_logger: Mock) -> None:
        """Test creating an item in DynamoDB."""
        item = DynamoDBBaseModel(pk="USER#123", sk="PROFILE#main")
        dynamodb_service.create(item)

        dynamodb_service._table.put_item.assert_called_once_with(
            Item={"pk": "USER#123", "sk": "PROFILE#main"}
        )
        mock_logger.info.assert_any_call(
            "Creating item in DynamoDB",
            pk="USER#123",
            sk="PROFILE#main",
        )

    def test_update_item(self, dynamodb_service: DynamoDBService, mock_logger: Mock) -> None:
        """Test updating an item in DynamoDB."""
        item = DynamoDBBaseModel(pk="USER#123", sk="PROFILE#main")
        dynamodb_service.update(item)

        dynamodb_service._table.put_item.assert_called_once_with(
            Item={"pk": "USER#123", "sk": "PROFILE#main"}
        )
        mock_logger.info.assert_any_call(
            "Updating item in DynamoDB",
            pk="USER#123",
            sk="PROFILE#main",
        )

    def test_get_one_item_found(
        self,
        dynamodb_service: DynamoDBService,
        mock_logger: Mock,
    ) -> None:
        """Test retrieving an item that exists."""
        dynamodb_service._table.get_item.return_value = {
            "Item": {"pk": "USER#123", "sk": "PROFILE#main"}
        }

        result = dynamodb_service.get_one("USER#123", "PROFILE#main", DynamoDBBaseModel)

        assert result is not None
        assert result.pk == "USER#123"
        assert result.sk == "PROFILE#main"
        dynamodb_service._table.get_item.assert_called_once_with(
            Key={"pk": "USER#123", "sk": "PROFILE#main"}
        )
        mock_logger.info.assert_any_call(
            "Getting item from DynamoDB",
            pk="USER#123",
            sk="PROFILE#main",
        )

    def test_get_one_item_not_found(self, dynamodb_service: DynamoDBService) -> None:
        """Test retrieving an item that doesn't exist."""
        dynamodb_service._table.get_item.return_value = {}

        result = dynamodb_service.get_one("USER#123", "PROFILE#main", DynamoDBBaseModel)

        assert result is None

    def test_close(self, dynamodb_service: DynamoDBService, mock_logger: Mock) -> None:
        """Test closing DynamoDB connection."""
        dynamodb_service.close()
        mock_logger.info.assert_any_call("Closing DynamoDB connection")


class TestDynamoDBServiceQuery:
    """Test DynamoDB service query operations."""

    def test_query_by_pk_with_results(
        self,
        dynamodb_service: DynamoDBService,
        mock_logger: Mock,
    ) -> None:
        """Test querying by partition key with results."""
        dynamodb_service._table.query.return_value = {
            "Items": [
                {"pk": "USER#123", "sk": "PROFILE#main"},
                {"pk": "USER#123", "sk": "PROFILE#secondary"},
            ]
        }

        results = dynamodb_service.query_by_pk("USER#123", DynamoDBBaseModel)

        assert len(results) == 2
        assert results[0].pk == "USER#123"
        assert results[0].sk == "PROFILE#main"
        assert results[1].pk == "USER#123"
        assert results[1].sk == "PROFILE#secondary"
        mock_logger.info.assert_any_call(
            "Querying items from DynamoDB",
            pk="USER#123",
        )

    def test_query_by_pk_no_results(self, dynamodb_service: DynamoDBService) -> None:
        """Test querying by partition key with no results."""
        dynamodb_service._table.query.return_value = {"Items": []}

        results = dynamodb_service.query_by_pk("USER#123", DynamoDBBaseModel)

        assert len(results) == 0
        assert results == []
