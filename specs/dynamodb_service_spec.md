# DynamoDB Service Specification

## Overview
Create a simplified DynamoDB service that provides high-level operations for AWS DynamoDB using the `pydynamodb` library. The service should follow the project's constitutional principles and match the patterns established by the MongoDB and MinIO services.

## Constitutional Compliance

### Core Principles
1. **Radical Simplicity**: Keep all operations straightforward and easy to understand
2. **Fail Fast**: Let operations fail immediately if parameters are incorrect
3. **Type Safety**: Use type hints everywhere (service, models, tests)
4. **Structured Data Models**: Use Pydantic models for configuration
5. **Dependency Injection**: All dependencies passed through constructor, no Optional or defaults
6. **SOLID Principles**: Single responsibility, proper abstraction

## Requirements

### 1. Configuration Model (`dynamodb_models.py`)

Create a Pydantic configuration model with:
- `region_name`: AWS region (required)
- `aws_access_key_id`: AWS access key (optional for IAM roles)
- `aws_secret_access_key`: AWS secret key (optional for IAM roles)
- `endpoint_url`: Custom endpoint for local testing (optional)
- `default_table_name`: Default table name (optional)
- `read_capacity_units`: Default RCU for table creation (default: 5)
- `write_capacity_units`: Default WCU for table creation (default: 5)

Validation rules:
- Region must be a valid AWS region string
- If access key provided, secret key must also be provided
- Capacity units must be >= 1

### 2. Service Implementation (`dynamodb_service.py`)

Create a `DynamoDBService` class with:

#### Constructor Dependencies
- `logger: logging.Logger` (required)
- `config: DynamoDBConfig` (required)

#### Connection Management
- Initialize boto3 DynamoDB client in constructor
- Store resource and client references
- Implement `ping()` method to verify connection

#### Table Operations
- `table_exists(table_name: str) -> bool`: Check if table exists
- `list_tables() -> list[str]`: List all tables
- `create_table(table_name: str, key_schema: list[dict[str, Any]], attribute_definitions: list[dict[str, Any]]) -> None`: Create table with key schema
- `delete_table(table_name: str) -> None`: Delete a table

#### Item Operations
All item operations should support optional `table_name` parameter that defaults to configured default table.

- `put_item(item: dict[str, Any], table_name: str | None = None) -> None`: Put single item
- `get_item(key: dict[str, Any], table_name: str | None = None) -> dict[str, Any] | None`: Get single item by key
- `update_item(key: dict[str, Any], update_expression: str, expression_attribute_values: dict[str, Any], table_name: str | None = None) -> dict[str, Any]`: Update item
- `delete_item(key: dict[str, Any], table_name: str | None = None) -> None`: Delete single item

#### Query Operations
- `query(key_condition_expression: str, expression_attribute_values: dict[str, Any], table_name: str | None = None, limit: int = 0) -> list[dict[str, Any]]`: Query items with partition key
- `scan(filter_expression: str | None = None, expression_attribute_values: dict[str, Any] | None = None, table_name: str | None = None, limit: int = 0) -> list[dict[str, Any]]`: Scan table

#### Batch Operations
- `batch_write_items(items: list[dict[str, Any]], table_name: str | None = None) -> None`: Batch write up to 25 items
- `batch_get_items(keys: list[dict[str, Any]], table_name: str | None = None) -> list[dict[str, Any]]`: Batch get up to 100 items

#### Helper Methods
- `_resolve_table(table_name: str | None) -> str`: Resolve table name using default if not provided

### 3. Error Handling
- Let pydynamodb exceptions bubble up (fail fast)
- Log errors before raising
- No retry logic (keep it simple)
- Validate table name resolution fails if no default configured

### 4. Logging
Follow the established pattern:
- Log at DEBUG level for operation start
- Log at INFO level for operation completion with details
- Log at ERROR level with exception context before raising

### 5. Testing

#### Unit Tests (`tests/dynamodb/test_dynamodb_service.py`)
Mock all boto3/pydynamodb calls:
- Test constructor initialization
- Test all CRUD operations with mocked responses
- Test table operations
- Test batch operations
- Test query and scan operations
- Test table name resolution logic
- Test error handling

#### Integration Tests (`integration_tests/dynamodb/test_dynamodb_service.py`)
Test against real DynamoDB Local:
- Table creation and deletion
- Item CRUD operations
- Query operations
- Batch operations
- Connection health check

## File Structure

```
src/services/dynamodb/
├── __init__.py
├── dynamodb_service.py
├── dynamodb_models.py

tests/dynamodb/
├── __init__.py
├── test_dynamodb_service.py

integration_tests/dynamodb/
├── __init__.py
├── test_dynamodb_service.py
```

## Dependencies

Add to `pyproject.toml`:
- `pydynamodb` (or `boto3` if pydynamodb is not the correct library name)
- `moto[dynamodb]` for mocking in tests

## Example Usage

```python
import logging
from src.services.dynamodb.dynamodb_service import DynamoDBService
from src.services.dynamodb.dynamodb_models import DynamoDBConfig

# Configure service
config = DynamoDBConfig(
    region_name="us-east-1",
    aws_access_key_id="your_key",
    aws_secret_access_key="your_secret",
    default_table_name="users"
)

logger = logging.getLogger(__name__)
dynamodb_service = DynamoDBService(logger=logger, config=config)

# Put item
dynamodb_service.put_item({"id": "user123", "name": "Alice"})

# Get item
user = dynamodb_service.get_item({"id": "user123"})

# Query items
results = dynamodb_service.query(
    key_condition_expression="id = :id",
    expression_attribute_values={":id": "user123"}
)
```

## Success Criteria

1. All code follows constitutional principles
2. Comprehensive type hints on all functions
3. Pydantic configuration model with validation
4. Service uses dependency injection (no Optional dependencies)
5. Unit tests with 100% mocking of external dependencies
6. Integration tests that pass against DynamoDB Local
7. Follows the established patterns from MongoDB and MinIO services
8. Clear, simple implementation without unnecessary complexity
