# Task Breakdown: DynamoDB Service Implementation

## Quick Task Checklist

**Instructions for Executor**: Work through these tasks sequentially. Update each checkbox as you complete the task. Do NOT stop for confirmation - implement all tasks to completion.

- [ ] 1. Create DynamoDB configuration Pydantic model with validation
- [ ] 2. Implement DynamoDB service class with dependency injection
- [ ] 3. Implement table operations (exists, list, create, delete)
- [ ] 4. Implement item operations (put, get, update, delete)
- [ ] 5. Implement query operations (query, scan)
- [ ] 6. Implement batch operations (batch_write, batch_get)
- [ ] 7. Write unit tests with moto mocking for DynamoDB service
- [ ] 8. Write integration tests for DynamoDB service
- [ ] 9. Update project dependencies in pyproject.toml
- [ ] 10. Run linting and formatting (black, flake8)

**Note**: Each task above represents a clear, sequential implementation step. See detailed implementation guidance below.

---

## Specification Summary

Implement a simplified DynamoDB service that provides high-level operations for AWS DynamoDB using boto3. The service follows the project's constitutional principles and matches the patterns established by MongoDB and MinIO services. Key features include:
- Pydantic configuration model with validation
- Constructor dependency injection (logger and config as required parameters)
- Table operations (create, delete, exists, list)
- Item operations (put, get, update, delete)
- Query and scan operations
- Batch operations (batch write/get up to 25/100 items)
- Unit tests with moto mocking
- Integration tests against DynamoDB Local

## Constitutional Compliance Analysis

### ✅ Aligned Requirements
- **Type Safety**: All functions will have comprehensive type hints including parameters and return values
- **Dependency Injection**: Service uses constructor injection with required logger and config (no Optional, no defaults)
- **Structured Data Models**: Pydantic model for configuration with validation rules
- **Fail Fast**: Let boto3 exceptions bubble up immediately, no retry logic, validate table name resolution fails if no default configured
- **Radical Simplicity**: Straightforward wrapper around boto3 operations, no unnecessary abstractions
- **SOLID Principles**: Single responsibility (database operations), dependency inversion (injected dependencies)
- **Logging**: Consistent DEBUG/INFO/ERROR logging pattern matching existing services

### ⚠️ Potential Conflicts
**None identified** - The specification naturally aligns with all constitutional principles.

### 🎯 Simplification Opportunities
- Keep boto3 error handling simple - let exceptions bubble up (fail fast)
- Use simple dict return types for items (no complex models needed)
- Table name resolution logic is straightforward - fail immediately if no default configured
- No connection pooling complexity needed (boto3 handles this internally)
- No retry logic or circuit breakers (constitutional fail fast principle)

---

## Detailed Task Implementation Guidance

### Task 1: Create DynamoDB Configuration Pydantic Model
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data)
- **Implementation Approach**: Create `src/services/dynamodb/dynamodb_models.py` with DynamoDBConfig Pydantic model
- **Key Considerations**:
  - Follow MongoDB/MinIO model patterns: use BaseModel, Field(), @field_validator
  - Required fields: `region_name` (must be valid AWS region)
  - Optional fields: `aws_access_key_id`, `aws_secret_access_key`, `endpoint_url`, `default_table_name`
  - Default values: `read_capacity_units=5`, `write_capacity_units=5` (both must be >= 1)
  - Validation: If `aws_access_key_id` provided, `aws_secret_access_key` must also be provided
  - Define constants at module level for error messages (e.g., `ERROR_SECRET_KEY_REQUIRED`)
  - Use ConfigDict with json_schema_extra for example configuration
- **Files to Create/Modify**:
  - Create: `/home/user/lvrgd-common/src/services/dynamodb/dynamodb_models.py`
  - Create: `/home/user/lvrgd-common/src/services/dynamodb/__init__.py` (empty or with exports)

### Task 2: Implement DynamoDB Service Class Core Structure
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety), VI (Dependency Injection)
- **Implementation Approach**: Create `src/services/dynamodb/dynamodb_service.py` with DynamoDBService class
- **Dependency Injection Pattern Required**: Yes - constructor must take `logger: logging.Logger` and `config: DynamoDBConfig` as REQUIRED parameters (no Optional, no defaults)
- **Key Considerations**:
  - Follow MongoDB/MinIO service patterns exactly
  - Constructor initializes boto3 DynamoDB client and resource using config parameters
  - Store `self.log` and `self.config` as instance variables
  - Initialize connection in constructor, call `ping()` to verify connectivity
  - Log initialization at INFO level with region information
  - Let any initialization exceptions bubble up (fail fast)
  - Store both `self._client` (boto3 client) and `self._resource` (boto3 resource) references
  - Implement helper method `_resolve_table(table_name: str | None) -> str` that returns table_name if provided, else config.default_table_name, else raises ValueError
- **Files to Create/Modify**:
  - Create: `/home/user/lvrgd-common/src/services/dynamodb/dynamodb_service.py`

### Task 3: Implement Table Operations
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety)
- **Implementation Approach**: Add table operation methods to DynamoDBService class
- **Key Considerations**:
  - `ping() -> dict[str, Any]`: List tables to verify connection, return boto3 response
  - `table_exists(table_name: str) -> bool`: Check if table exists using client
  - `list_tables() -> list[str]`: Return list of all table names
  - `create_table(table_name: str, key_schema: list[dict[str, Any]], attribute_definitions: list[dict[str, Any]]) -> None`: Create table with provided schema using config RCU/WCU
  - `delete_table(table_name: str) -> None`: Delete specified table
  - Follow logging pattern: DEBUG at start, INFO on completion with details
  - Let boto3 exceptions bubble up (fail fast)
- **Files to Create/Modify**:
  - Modify: `/home/user/lvrgd-common/src/services/dynamodb/dynamodb_service.py`

### Task 4: Implement Item Operations
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety)
- **Implementation Approach**: Add CRUD methods for individual items to DynamoDBService class
- **Key Considerations**:
  - All methods support optional `table_name: str | None = None` parameter that defaults to configured default table via `_resolve_table()`
  - `put_item(item: dict[str, Any], table_name: str | None = None) -> None`: Put single item
  - `get_item(key: dict[str, Any], table_name: str | None = None) -> dict[str, Any] | None`: Get item by key, return None if not found
  - `update_item(key: dict[str, Any], update_expression: str, expression_attribute_values: dict[str, Any], table_name: str | None = None) -> dict[str, Any]`: Update item and return updated attributes
  - `delete_item(key: dict[str, Any], table_name: str | None = None) -> None`: Delete item by key
  - Use table resource from `self._resource.Table(table_name)`
  - Follow logging pattern consistently
  - Return simple dict types (fail fast, no defensive checks)
- **Files to Create/Modify**:
  - Modify: `/home/user/lvrgd-common/src/services/dynamodb/dynamodb_service.py`

### Task 5: Implement Query Operations
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety)
- **Implementation Approach**: Add query and scan methods to DynamoDBService class
- **Key Considerations**:
  - `query(key_condition_expression: str, expression_attribute_values: dict[str, Any], table_name: str | None = None, limit: int = 0) -> list[dict[str, Any]]`: Query items with partition key, limit=0 means no limit
  - `scan(filter_expression: str | None = None, expression_attribute_values: dict[str, Any] | None = None, table_name: str | None = None, limit: int = 0) -> list[dict[str, Any]]`: Scan table with optional filter
  - Use boto3 Key condition builder (boto3.dynamodb.conditions.Key)
  - Apply limit only if > 0
  - Return all items from paginated responses if no limit
  - Log number of items returned at INFO level
- **Files to Create/Modify**:
  - Modify: `/home/user/lvrgd-common/src/services/dynamodb/dynamodb_service.py`

### Task 6: Implement Batch Operations
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety)
- **Implementation Approach**: Add batch write and get methods to DynamoDBService class
- **Key Considerations**:
  - `batch_write_items(items: list[dict[str, Any]], table_name: str | None = None) -> None`: Batch write up to 25 items using batch_writer context manager
  - `batch_get_items(keys: list[dict[str, Any]], table_name: str | None = None) -> list[dict[str, Any]]`: Batch get up to 100 items using batch_get_item
  - Let boto3 handle the batching internally (simple approach)
  - Log count of items processed at INFO level
  - Trust caller to respect batch size limits (fail fast if boto3 complains)
- **Files to Create/Modify**:
  - Modify: `/home/user/lvrgd-common/src/services/dynamodb/dynamodb_service.py`

### Task 7: Write Unit Tests with Moto Mocking
- **Constitutional Principles**: III (Type Safety), V (Unit Testing with Mocking)
- **Implementation Approach**: Create comprehensive unit tests using moto for AWS DynamoDB mocking
- **Key Considerations**:
  - Create `tests/dynamodb/test_dynamodb_service.py`
  - Use `@mock_dynamodb` decorator from moto for all test methods
  - Test constructor initialization and connection
  - Test all table operations (exists, list, create, delete)
  - Test all item operations (put, get, update, delete)
  - Test query and scan operations
  - Test batch operations
  - Test `_resolve_table()` logic with and without default table configured
  - Test error handling (table not found, invalid keys, etc.)
  - Type hints in all test functions
  - Use pytest fixtures for logger and config
  - Mock should provide realistic DynamoDB behavior
- **Files to Create/Modify**:
  - Create: `/home/user/lvrgd-common/tests/dynamodb/__init__.py`
  - Create: `/home/user/lvrgd-common/tests/dynamodb/test_dynamodb_service.py`

### Task 8: Write Integration Tests
- **Constitutional Principles**: III (Type Safety)
- **Implementation Approach**: Create integration tests that run against real DynamoDB Local
- **Key Considerations**:
  - Create `integration_tests/dynamodb/test_dynamodb_service.py`
  - Requires DynamoDB Local running (document this requirement)
  - Test table lifecycle (create, exists, delete)
  - Test full item CRUD cycle
  - Test query operations with real data
  - Test batch operations with real data
  - Test connection health check
  - Use unique table names per test to avoid conflicts
  - Clean up tables after tests
  - Type hints in all test functions
  - Configuration should use environment variables or test defaults
- **Files to Create/Modify**:
  - Create: `/home/user/lvrgd-common/integration_tests/dynamodb/__init__.py`
  - Create: `/home/user/lvrgd-common/integration_tests/dynamodb/test_dynamodb_service.py`

### Task 9: Update Project Dependencies
- **Constitutional Principles**: I (Simplicity)
- **Implementation Approach**: Add required dependencies to pyproject.toml
- **Key Considerations**:
  - Add `boto3` to main dependencies (not pydynamodb - boto3 is the standard AWS SDK)
  - Add `moto[dynamodb]` to dev/test dependencies for mocking
  - Follow existing dependency format in pyproject.toml
  - No version pinning unless necessary (use compatible ranges)
- **Files to Create/Modify**:
  - Modify: `/home/user/lvrgd-common/pyproject.toml`

### Task 10: Run Linting and Formatting
- **Constitutional Principles**: I (Simplicity), III (Type Safety)
- **Implementation Approach**: Format and lint all new code
- **Key Considerations**:
  - Run `black` on all new Python files for consistent formatting
  - Run `flake8` or `ruff` for linting
  - Ensure all type hints are correct (use `mypy` if available)
  - Fix any linting errors
  - Ensure docstrings are clear and concise
  - Remove any verbose comments (constitution prefers minimal comments)
- **Files to Create/Modify**:
  - Modify all created/modified Python files as needed

---

## Implementation Guidance

### Radical Simplicity Checklist
- [ ] Is this the simplest possible implementation?
  - Yes - wrap boto3 operations directly without unnecessary abstractions
- [ ] Have we avoided unnecessary abstractions?
  - Yes - no custom exception classes, no complex wrappers
- [ ] Are we building only what's needed, not a "space shuttle"?
  - Yes - only essential DynamoDB operations, no fancy features
- [ ] Can any code be removed while maintaining functionality?
  - Continuously review during implementation

### Fail Fast Checklist
- [ ] No fallback logic unless explicitly requested
  - Confirmed - let boto3 exceptions bubble up
- [ ] No defensive type/instance checking
  - Confirmed - trust types, let it fail if wrong
- [ ] No existence checks for required data
  - Confirmed - `_resolve_table()` fails if no default configured and no table name provided
- [ ] Let it fail immediately if assumptions are violated
  - Confirmed - all operations fail fast on errors

### Type Safety Checklist
- [ ] Type hints on all function parameters
  - Required for all service methods, tests, and models
- [ ] Type hints on all return values
  - Required including `-> None` where applicable
- [ ] Type hints in test code
  - Required in all test functions
- [ ] Using Optional[] for nullable values
  - Used in `get_item() -> dict[str, Any] | None`
  - Used in optional parameters like `table_name: str | None = None`
- [ ] No runtime type checking (trust the types)
  - Confirmed - no isinstance() or type() checks

### Dependency Injection Checklist
- [ ] All services use constructor injection
  - DynamoDBService takes logger and config in __init__
- [ ] All dependencies are REQUIRED parameters (no Optional, no defaults)
  - `logger: logging.Logger` - REQUIRED
  - `config: DynamoDBConfig` - REQUIRED
- [ ] Dependencies have proper type hints
  - All dependencies properly typed
- [ ] Dependencies are NEVER created inside constructors
  - Logger and config must be passed in from outside
- [ ] Services are loosely coupled
  - Service only depends on abstractions (logger, config model)
- [ ] Enables easy mock injection for testing
  - Tests can easily inject mock logger and test config

### SOLID Principles Checklist
- [ ] **S**: Each class has single responsibility
  - DynamoDBService: Handle DynamoDB operations only
  - DynamoDBConfig: Configuration validation only
- [ ] **O**: Open for extension, closed for modification
  - Can extend with additional methods without modifying existing ones
- [ ] **L**: Subtypes substitutable for base types
  - Not applicable (no inheritance hierarchy)
- [ ] **I**: Many specific interfaces vs one general
  - Service provides specific methods for each operation type
- [ ] **D**: Depend on abstractions, not concretions
  - Depends on logging.Logger (standard library interface)
  - Depends on DynamoDBConfig (Pydantic model)

---

## Specification Conflicts & Recommendations

### No Conflicts Identified
The specification is well-aligned with all constitutional principles. No modifications or recommendations needed.

---

## Complexity Warnings

### Areas to Watch
- **Batch Operations**: Keep batch operations simple - trust boto3 to handle complexity internally. Don't build custom chunking or retry logic.
- **Query Pagination**: If implementing pagination, keep it simple. Consider returning all results for simplicity unless pagination becomes a real performance issue.
- **Error Handling**: Resist the urge to catch and handle specific boto3 exceptions. Let them bubble up (fail fast).
- **Table Name Resolution**: Keep `_resolve_table()` simple - just check for table_name parameter, then default, then fail.

### Refactoring Opportunities
- If any method becomes too complex (>15-20 lines), consider extracting helper methods
- If similar logging patterns repeat, that's acceptable - don't create logging abstractions for this simple service
- Watch for any defensive programming patterns creeping in during implementation

---

## Testing Strategy

### Unit Test Coverage
**Test all operations with moto mocking**:
- Constructor initialization (successful and failure cases)
- Connection verification (ping method)
- Table operations (create, delete, exists, list)
- Item operations (put, get, update, delete)
- Query and scan operations
- Batch operations (batch_write, batch_get)
- Table name resolution logic (with default, without default, with parameter)
- Error scenarios (no table specified and no default, table not found, etc.)
- All tests use `@mock_dynamodb` decorator
- All test functions have type hints

### Integration Test Coverage
**Test against DynamoDB Local**:
- Full table lifecycle (create table, verify exists, delete table)
- Complete item CRUD cycle with real DynamoDB Local instance
- Query operations with multiple items
- Scan operations with filters
- Batch write and batch get with actual data
- Connection health check against real service
- Cleanup tables after each test

### Mocking Strategy
- **Unit Tests**: Use moto's `@mock_dynamodb` decorator to mock all boto3 DynamoDB calls
- **Integration Tests**: No mocking - test against real DynamoDB Local instance
- **Test Fixtures**: Create pytest fixtures for logger (use standard logging.Logger) and config (DynamoDBConfig with test values)

---

## Success Criteria

### Functional Requirements
- [ ] DynamoDBConfig model created with all required fields and validation
- [ ] DynamoDBService class created with dependency injection pattern
- [ ] All table operations implemented and working (exists, list, create, delete)
- [ ] All item operations implemented and working (put, get, update, delete)
- [ ] Query and scan operations implemented and working
- [ ] Batch operations implemented and working (batch_write, batch_get)
- [ ] Table name resolution works correctly with defaults
- [ ] Connection verification (ping) works correctly

### Constitutional Compliance
- [ ] All code follows radical simplicity (no unnecessary complexity)
- [ ] Type hints used everywhere (service, models, tests)
- [ ] Structured data models (Pydantic config, no loose dicts for config)
- [ ] Dependency injection implemented (logger and config as REQUIRED parameters, no Optional, no defaults)
- [ ] SOLID principles maintained (single responsibility, dependency inversion)
- [ ] Fail fast philosophy applied (exceptions bubble up, no defensive coding)
- [ ] Unit tests use moto for AWS service mocking

### Code Quality Gates
- [ ] All functions have type hints for parameters and return values
- [ ] DynamoDBService uses constructor injection for all dependencies
- [ ] No Optional dependencies or default parameter values in constructor
- [ ] No defensive programming (no unnecessary type checks or existence checks)
- [ ] Pydantic model is simple data definition with validators
- [ ] Clean docstrings on all public methods
- [ ] Minimal comments (code should be self-explanatory)
- [ ] Formatted with black
- [ ] Passes flake8 linting
- [ ] Unit tests achieve high coverage (>90%)
- [ ] Integration tests pass against DynamoDB Local
- [ ] Follows established patterns from MongoDB and MinIO services

### Pattern Consistency
- [ ] File structure matches MongoDB/MinIO services (dynamodb_service.py, dynamodb_models.py)
- [ ] Pydantic model structure matches existing services (Field(), @field_validator, ConfigDict)
- [ ] Service class structure matches existing services (__init__, logging pattern, helper methods)
- [ ] Logging pattern matches existing services (DEBUG/INFO/ERROR levels, consistent message format)
- [ ] Test structure matches existing test patterns

---

## Reference Examples

### Expected File Structure
```
src/services/dynamodb/
├── __init__.py                 # Empty or exports
├── dynamodb_service.py         # Main service class
├── dynamodb_models.py          # Pydantic configuration model

tests/dynamodb/
├── __init__.py                 # Empty
├── test_dynamodb_service.py    # Unit tests with moto

integration_tests/dynamodb/
├── __init__.py                 # Empty
├── test_dynamodb_service.py    # Integration tests
```

### Constructor Pattern (matches MongoDB/MinIO)
```python
def __init__(
    self,
    logger: logging.Logger,
    config: DynamoDBConfig,
) -> None:
    """Initialize DynamoDBService.

    Args:
        logger: Standard Python logger instance
        config: DynamoDB configuration model
    """
    self.log = logger
    self.config = config

    self.log.info("Initializing DynamoDB connection to region: %s", config.region_name)

    # Initialize boto3 client and resource
    # ... connection logic ...

    # Verify connection
    self.ping()
```

### Logging Pattern
```python
# Operation start (DEBUG)
self.log.debug("Operation description with context: %s", param)

# Operation success (INFO)
self.log.info("Operation completed successfully: %s", details)

# Operation failure (ERROR with exception)
try:
    # operation
except Exception:
    self.log.exception("Operation failed with context")
    raise
```

---

## Notes for Executor

1. **Start with Task 1** and proceed sequentially through all tasks
2. **Follow existing patterns** from MongoDB and MinIO services exactly
3. **Keep it simple** - resist any urge to add complexity
4. **Type hints everywhere** - parameters, return values, even in tests
5. **No Optional dependencies** in constructor - logger and config must be REQUIRED
6. **Let it fail fast** - no defensive coding, no fallbacks, let exceptions bubble up
7. **Use moto for unit tests** - mock all boto3 operations with `@mock_dynamodb`
8. **Test against DynamoDB Local** for integration tests
9. **Update checkboxes** as you complete each task
10. **Do NOT stop for confirmation** - implement all tasks to completion

Good luck! Remember: We're not building a space shuttle, we're building a simple, clean DynamoDB service wrapper.
