# Task Breakdown: Boto3 DynamoDB Service with Pure Pydantic DTOs

**Generated**: 2025-11-16
**Source Spec**: `specs/boto3-dynamodb-service/spec.md`

## Quick Task Checklist

**Instructions for Executor**: Work through tasks sequentially. Update each checkbox as you complete. Do NOT stop for confirmation - implement all tasks to completion.

- [ ] 1. Install boto3-stubs[dynamodb] type dependencies
- [ ] 2. Create DynamoDBBaseModel (pure Pydantic with pk/sk)
- [ ] 3. Create DynamoDBConfig configuration model
- [ ] 4. Create SortKeyCondition query condition model
- [ ] 5. Create PaginationResult generic result model
- [ ] 6. Create TransactionWriteItem transaction model
- [ ] 7. Create custom exception classes
- [ ] 8. Create DynamoDBService skeleton with dependency injection
- [ ] 9. Implement CRUD operations (save, get_one, delete, update)
- [ ] 10. Implement query operations (query_by_pk, query_by_pk_and_sk)
- [ ] 11. Implement batch operations (batch_get, batch_write)
- [ ] 12. Implement transaction operations (transact_write, transact_get)
- [ ] 13. Implement utility operations (ping, count)
- [ ] 14. Generate comprehensive unit tests for ALL service methods
- [ ] 15. Run unit tests until ALL pass (unattended)
- [ ] 16. Generate integration tests following MongoDB pattern
- [ ] 17. Add DynamoDB fixtures to conftest.py
- [ ] 18. Run integration tests until ALL pass (unattended)
- [ ] 19. Run ruff format on all files
- [ ] 20. Run ruff check --fix on all files
- [ ] 21. Manually fix ALL remaining ruff violations
- [ ] 22. Verify ZERO ruff violations
- [ ] 23. Verify all constitutional requirements met

**Note**: See detailed implementation guidance below.

---

## Specification Summary

Implement a boto3-based DynamoDB service using Repository Pattern (pure Pydantic DTOs + service layer) to replace the Active Record pattern (PynamoDB). Service provides CRUD, query, batch, and transaction operations with strong type safety via boto3-stubs, structured logging, and full constitutional compliance.

---

## Detailed Task Implementation Guidance

### Task 1: Install boto3-stubs[dynamodb] Type Dependencies
- **Constitutional Principles**: III (Type Safety)
- **Implementation Approach**:
  - Add `boto3-stubs[dynamodb]` OR `mypy-boto3-dynamodb` to dev dependencies
  - This enables compile-time type checking for boto3 operations
  - Provides IDE autocomplete for boto3 Table methods
  - No code changes, just dependency addition
- **Files to Modify**: `pyproject.toml` or `requirements-dev.txt`
- **Dependencies**: None

### Task 2: Create DynamoDBBaseModel (Pure Pydantic with pk/sk)
- **Constitutional Principles**: IV (Structured Data), VII (SOLID - SRP), I (Simplicity)
- **Implementation Approach**:
  - Pure Pydantic BaseModel with ONLY `pk: str` and `sk: str` fields
  - Zero methods, zero business logic, zero persistence logic
  - This is a PURE DTO - just data structure definition
  - All domain models will inherit from this base
  - Use Field() with descriptions for clarity
- **Files to Create**: `src/lvrgd_common/models/dynamodb_base_model.py`
- **Dependencies**: None

### Task 3: Create DynamoDBConfig Configuration Model
- **Constitutional Principles**: IV (Structured Data), III (Type Safety)
- **Implementation Approach**:
  - Pydantic BaseModel for DynamoDB connection configuration
  - Fields: table_name (required), region (required), endpoint_url (optional), aws_access_key_id (optional), aws_secret_access_key (optional)
  - Pydantic will validate fields automatically
  - Keep it simple - just configuration data
- **Files to Create**: `src/lvrgd_common/models/dynamodb_config.py`
- **Dependencies**: None

### Task 4: Create SortKeyCondition Query Condition Model
- **Constitutional Principles**: IV (Structured Data), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Pydantic BaseModel for type-safe sort key query conditions
  - Use Literal type for operator: "eq" | "ne" | "lt" | "le" | "gt" | "ge" | "begins_with" | "between"
  - Fields: operator (Literal), value (str), value2 (optional str for "between")
  - Add Pydantic validator for "between" operator requiring value2
  - Clean abstraction over boto3's verbose KeyConditionExpression syntax
- **Files to Create**: `src/lvrgd_common/models/sort_key_condition.py`
- **Dependencies**: None

### Task 5: Create PaginationResult Generic Result Model
- **Constitutional Principles**: IV (Structured Data), III (Type Safety via Generics)
- **Implementation Approach**:
  - Generic Pydantic BaseModel with TypeVar bound to DynamoDBBaseModel
  - Fields: items (list[T]), last_evaluated_key (dict | None), count (int)
  - Enable arbitrary_types_allowed in Config for generic support
  - Preserves type safety through query operations
- **Files to Create**: `src/lvrgd_common/models/pagination_result.py`
- **Dependencies**: Task 2 (needs DynamoDBBaseModel for TypeVar bound)

### Task 6: Create TransactionWriteItem Transaction Model
- **Constitutional Principles**: IV (Structured Data), III (Type Safety)
- **Implementation Approach**:
  - Pydantic BaseModel representing single transaction write operation
  - Use Literal for operation type: "put" | "update" | "delete"
  - Fields: operation (Literal), item (optional DynamoDBBaseModel), pk (optional str), sk (optional str), updates (optional dict)
  - Structure makes transaction operations type-safe and clear
- **Files to Create**: `src/lvrgd_common/models/transaction_write_item.py`
- **Dependencies**: Task 2 (needs DynamoDBBaseModel)

### Task 7: Create Custom Exception Classes
- **Constitutional Principles**: II (Fail Fast), III (Type Safety)
- **Implementation Approach**:
  - Base exception: DynamoDBServiceError (includes operation, pk, sk context)
  - Batch exception: DynamoDBBatchOperationError (includes failed_items, successful_count)
  - Transaction exception: DynamoDBTransactionError
  - Type hints on all __init__ methods
  - Exceptions provide rich context for debugging
- **Files to Create**: `src/lvrgd_common/exceptions/dynamodb_exceptions.py`
- **Dependencies**: None

### Task 8: Create DynamoDBService Skeleton with Dependency Injection
- **Constitutional Principles**: VI (Dependency Injection), VII (SOLID - SRP), II (Fail Fast), III (Type Safety)
- **Implementation Approach**:
  - Constructor signature: `__init__(self, logger: LoggingService, config: DynamoDBConfig) -> None`
  - ALL dependencies REQUIRED - no Optional, no default values
  - Create boto3 Table resource internally from config (NOT injected)
  - Use boto3-stubs type hints: `self._table: Table`
  - NO ping() in constructor (Principle II - fail when actually used)
  - Store logger and config as instance variables
  - Import boto3 and create resource/table internally
- **Files to Create**: `src/lvrgd_common/services/dynamodb_service.py`
- **Dependencies**: Tasks 3, 7 (needs DynamoDBConfig, exceptions)

### Task 9: Implement CRUD Operations (save, get_one, delete, update)
- **Constitutional Principles**: II (Fail Fast), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - `save(item: DynamoDBBaseModel) -> None` - use self._table.put_item()
  - `get_one(pk: str, sk: str, model_class: type[T]) -> T | None` - use self._table.get_item(), return None if not found
  - `delete(pk: str, sk: str) -> None` - use self._table.delete_item()
  - `update(pk: str, sk: str, updates: dict[str, Any]) -> None` - use self._table.update_item()
  - Add structured logging before and after each operation (operation, pk, sk, elapsed_ms)
  - Wrap boto3 ClientError in DynamoDBServiceError with context
  - Fail fast - no retries, no fallbacks, exceptions propagate
  - Type hints on ALL parameters and return values
- **Files to Modify**: `src/lvrgd_common/services/dynamodb_service.py`
- **Dependencies**: Task 8 (needs service skeleton)

### Task 10: Implement Query Operations (query_by_pk, query_by_pk_and_sk)
- **Constitutional Principles**: III (Type Safety), IV (Structured Conditions), I (Simplicity)
- **Implementation Approach**:
  - `query_by_pk()` - query by partition key only, support limit/pagination/index
  - `query_by_pk_and_sk()` - query by pk + sort key condition, support all 8 operators
  - Create helper method `_build_key_condition_expression()` to translate SortKeyCondition to boto3 Key conditions
  - Support all operators: eq, ne, lt, le, gt, ge, begins_with, between
  - Return PaginationResult[T] with items, last_evaluated_key, count
  - Support index queries via index_name parameter
  - Add structured logging with query parameters
  - Wrap errors in DynamoDBServiceError
- **Files to Modify**: `src/lvrgd_common/services/dynamodb_service.py`
- **Dependencies**: Tasks 4, 5, 9 (needs SortKeyCondition, PaginationResult, service foundation)

### Task 11: Implement Batch Operations (batch_get, batch_write)
- **Constitutional Principles**: I (Simplicity with auto-chunking), II (Fail Fast on partial failures)
- **Implementation Approach**:
  - `batch_get(keys: list[tuple[str, str]], model_class: type[T]) -> list[T]` - batch retrieve
  - `batch_write(items: list[DynamoDBBaseModel]) -> None` - batch save
  - Implement automatic chunking at 25-item DynamoDB limit
  - For batch_write, handle UnprocessedItems and report failures
  - Fail fast if any items fail (raise DynamoDBBatchOperationError with details)
  - Add structured logging with batch_size, successful_count, failed_count
  - Type hints on all parameters
- **Files to Modify**: `src/lvrgd_common/services/dynamodb_service.py`
- **Dependencies**: Task 9 (needs CRUD foundation)

### Task 12: Implement Transaction Operations (transact_write, transact_get)
- **Constitutional Principles**: II (Fail Fast - atomic all-or-nothing), III (Type Safety)
- **Implementation Approach**:
  - `transact_write(operations: list[TransactionWriteItem]) -> None` - atomic write
  - `transact_get(keys: list[tuple[str, str]], model_class: type[T]) -> list[T]` - atomic read
  - Use boto3 transact_write_items() and transact_get_items()
  - All-or-nothing semantics - entire transaction succeeds or fails
  - Wrap TransactionCanceledException in DynamoDBTransactionError
  - Add structured logging with operation_count, operation_types
  - Type hints on all parameters
- **Files to Modify**: `src/lvrgd_common/services/dynamodb_service.py`
- **Dependencies**: Task 6 (needs TransactionWriteItem model)

### Task 13: Implement Utility Operations (ping, count)
- **Constitutional Principles**: II (Fail Fast), I (Simplicity)
- **Implementation Approach**:
  - `ping() -> bool` - health check using table.load() or table.table_status
  - `count(pk: str, sk_condition: SortKeyCondition | None = None) -> int` - count items matching query
  - ping() NOT called in constructor - only when explicitly needed
  - Fail fast if table is inaccessible
  - Add structured logging
  - Type hints on all parameters
- **Files to Modify**: `src/lvrgd_common/services/dynamodb_service.py`
- **Dependencies**: Task 10 (count uses query infrastructure)

### Task 14: Generate Comprehensive Unit Tests for ALL Service Methods
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety)
- **Implementation Approach**:
  - Create fixtures: mock_logger, config, mock_table, db_service (with mocked boto3)
  - Mock boto3.resource to return mock table
  - Test EVERY method: save, get_one, delete, update, query_by_pk, query_by_pk_and_sk, batch_get, batch_write, transact_write, transact_get, ping, count
  - Test happy path for each method
  - Test error wrapping (mock ClientError, verify DynamoDBServiceError raised)
  - Test all 8 sort key operators in query tests
  - Test pagination (last_evaluated_key handling)
  - Test batch chunking at 25 items
  - Test transaction atomicity
  - Type hints in ALL test code
  - Use pytest fixtures for setup
- **Files to Create**: `tests/unit/test_dynamodb_service.py`
- **Dependencies**: Tasks 2-13 (needs all models and service implementation)

### Task 15: Run Unit Tests Until ALL Pass (Unattended)
- **Constitutional Principles**: II (Fail Fast), V (Testing)
- **Implementation Approach**:
  - Run `pytest tests/unit/test_dynamodb_service.py -v`
  - Fix any failures immediately
  - Re-run until ALL tests pass
  - Do NOT stop for confirmation - iterate until green
  - Verify all methods are tested
  - Verify all assertions pass
- **Files to Modify**: Any files needed to fix test failures
- **Dependencies**: Task 14 (needs unit tests)

### Task 16: Generate Integration Tests Following MongoDB Pattern
- **Constitutional Principles**: V (Testing), III (Type Safety)
- **Implementation Approach**:
  - Follow pattern from `integration-tests/test_mongodb_integration.py`
  - Create `test_dynamodb_integration.py` in integration-tests directory
  - Test against real DynamoDB (local DynamoDB or AWS)
  - Use unique table names or unique pk/sk values to avoid collisions (e.g., uuid.uuid4().hex)
  - Test CRUD operations with actual DynamoDB
  - Test query operations with real queries
  - Test batch operations with real batches
  - Test transaction operations with real transactions
  - Test pagination with real data
  - Test index queries (create GSI/LSI in test)
  - Type hints on all test code
  - Clean up test data after each test
- **Files to Create**: `integration-tests/test_dynamodb_integration.py`
- **Dependencies**: Tasks 2-13 (needs complete service implementation)

### Task 17: Add DynamoDB Fixtures to conftest.py
- **Constitutional Principles**: VI (Dependency Injection), III (Type Safety)
- **Implementation Approach**:
  - Follow dotenv pattern from existing conftest.py
  - Load .env variables: DYNAMODB_HOST, DYNAMODB_PORT, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY
  - Create `dynamodb_config()` fixture using dotenv-loaded environment variables
  - Create `dynamodb_service()` fixture injecting logger and config
  - Use session or module scope for fixtures
  - Yield service, handle cleanup if needed
  - Type hints on all fixtures
- **Files to Modify**: `integration-tests/conftest.py`
- **Dependencies**: Tasks 3, 8 (needs DynamoDBConfig and DynamoDBService)

### Task 18: Run Integration Tests Until ALL Pass (Unattended)
- **Constitutional Principles**: II (Fail Fast), V (Testing)
- **Implementation Approach**:
  - Ensure .env has DynamoDB configuration
  - Run `pytest integration-tests/test_dynamodb_integration.py -v`
  - Fix any failures immediately
  - Re-run until ALL tests pass
  - Do NOT stop for confirmation - iterate until green
  - Verify all operations work against real DynamoDB
  - Verify cleanup is working (no leftover test data)
- **Files to Modify**: Any files needed to fix test failures
- **Dependencies**: Tasks 16, 17 (needs integration tests and fixtures)

### Task 19: Run ruff format on All Files
- **Constitutional Principles**: II (Fail Fast - linting required), Quality Gates
- **Implementation Approach**:
  - Run `ruff format src/lvrgd_common/models/dynamodb*.py`
  - Run `ruff format src/lvrgd_common/services/dynamodb_service.py`
  - Run `ruff format src/lvrgd_common/exceptions/dynamodb_exceptions.py`
  - Run `ruff format tests/unit/test_dynamodb_service.py`
  - Run `ruff format integration-tests/test_dynamodb_integration.py`
  - Run `ruff format integration-tests/conftest.py` (if modified)
  - Auto-formats all files to consistent style
- **Files to Modify**: All DynamoDB-related files
- **Dependencies**: Tasks 2-17 (needs all files created)

### Task 20: Run ruff check --fix on All Files
- **Constitutional Principles**: II (Fail Fast - zero violations required)
- **Implementation Approach**:
  - Run `ruff check --fix src/lvrgd_common/models/dynamodb*.py`
  - Run `ruff check --fix src/lvrgd_common/services/dynamodb_service.py`
  - Run `ruff check --fix src/lvrgd_common/exceptions/dynamodb_exceptions.py`
  - Run `ruff check --fix tests/unit/test_dynamodb_service.py`
  - Run `ruff check --fix integration-tests/test_dynamodb_integration.py`
  - Auto-fixes all automatically fixable violations
  - Identifies remaining violations for manual fixing
- **Files to Modify**: All DynamoDB-related files
- **Dependencies**: Task 19 (after formatting)

### Task 21: Manually Fix ALL Remaining ruff Violations
- **Constitutional Principles**: II (Fail Fast - zero tolerance), I (Simplicity)
- **Implementation Approach**:
  - Run `ruff check src/lvrgd_common/models/dynamodb*.py`
  - Run `ruff check src/lvrgd_common/services/dynamodb_service.py`
  - Run `ruff check tests/unit/test_dynamodb_service.py`
  - Run `ruff check integration-tests/test_dynamodb_integration.py`
  - For EACH violation type:
    - **C901 (complexity >10)**: Refactor into smaller functions (Principle I violation)
    - **PLR0915 (>50 statements)**: Break down into helper methods (Principle I violation)
    - **BLE001 (blind except)**: Catch specific exception types (Principle II violation)
    - **A002 (builtin shadowing)**: Rename variables (e.g., `id` -> `item_id`)
    - **PERF* (performance)**: Apply optimizations
    - **SIM* (simplify)**: Simplify code patterns
    - **FBT* (boolean trap)**: Fix boolean parameter patterns
  - Re-run `ruff check` after each fix
  - Iterate until ZERO violations
- **Files to Modify**: Any files with violations
- **Dependencies**: Task 20 (after auto-fix)

### Task 22: Verify ZERO ruff Violations
- **Constitutional Principles**: II (Fail Fast - code NOT complete until clean)
- **Implementation Approach**:
  - Run `ruff check src/lvrgd_common/models/dynamodb*.py`
  - Run `ruff check src/lvrgd_common/services/dynamodb_service.py`
  - Run `ruff check src/lvrgd_common/exceptions/dynamodb_exceptions.py`
  - Run `ruff check tests/unit/test_dynamodb_service.py`
  - Run `ruff check integration-tests/test_dynamodb_integration.py`
  - Verify output shows ZERO violations for all files
  - If ANY violations remain, return to Task 21
  - Code is NOT complete until this passes
- **Files to Verify**: All DynamoDB-related files
- **Dependencies**: Task 21 (after manual fixes)

### Task 23: Verify All Constitutional Requirements Met
- **Constitutional Principles**: All (I-VII)
- **Implementation Approach**:
  - Review all code for Principle I (Simplicity): No complex hierarchies, functions <10 complexity, <50 statements
  - Review all code for Principle II (Fail Fast): No fallbacks, exceptions propagate, zero ruff violations
  - Review all code for Principle III (Type Safety): Type hints on ALL methods including tests
  - Review all code for Principle IV (Structured Data): All models are Pydantic, no dict passing for structured data
  - Review all code for Principle V (Testing): Unit tests mock boto3, integration tests use real DynamoDB
  - Review all code for Principle VI (Dependency Injection): Logger and config REQUIRED (no Optional), boto3 created internally
  - Review all code for Principle VII (SOLID): Service = persistence only, Models = data only, SRP maintained
  - Verify all acceptance criteria from spec are met
  - Verify all quality gates passed
- **Dependencies**: All previous tasks

---

## Constitutional Principle Reference

For each task, the following principles are referenced:
- **I** - Radical Simplicity
- **II** - Fail Fast Philosophy
- **III** - Comprehensive Type Safety
- **IV** - Structured Data Models
- **V** - Unit Testing with Mocking
- **VI** - Dependency Injection (all REQUIRED)
- **VII** - SOLID Principles

**Detailed implementation guidance** is in the specification document and constitution.

---

## Success Criteria

### Functional Requirements (from spec)
- [ ] DynamoDBBaseModel is pure Pydantic (pk/sk only, no methods)
- [ ] DynamoDBService uses dependency injection (logger, config REQUIRED)
- [ ] boto3 Table created internally (NOT injected)
- [ ] All CRUD operations work (save, get_one, delete, update)
- [ ] All query operations work (query_by_pk, query_by_pk_and_sk, all 8 operators)
- [ ] Index queries work (GSI/LSI support)
- [ ] Batch operations work (batch_get, batch_write with auto-chunking)
- [ ] Transaction operations work (transact_write, transact_get)
- [ ] Utility operations work (ping, count)
- [ ] Structured logging on all operations
- [ ] Error wrapping with domain exceptions
- [ ] Query builder (SortKeyCondition) works
- [ ] Pagination works (PaginationResult)

### Constitutional Compliance (from spec)
- [ ] All code follows radical simplicity (I) - functions <10 complexity, <50 statements
- [ ] Fail fast applied throughout (II) - no fallbacks, exceptions propagate
- [ ] Type hints on all functions (III) - including tests
- [ ] Pydantic models used (IV) - no dicts for structured data
- [ ] Unit tests mock boto3 (V) - integration tests use real DynamoDB
- [ ] Dependency injection implemented (VI) - logger/config REQUIRED, boto3 internal
- [ ] SOLID principles maintained (VII) - SRP, service=persistence, models=data

### Code Quality Gates
- [ ] All functions have type hints (parameters and return values)
- [ ] All services use constructor injection (REQUIRED dependencies)
- [ ] No defensive programming (unless requested)
- [ ] Models are simple data definitions (no business logic)
- [ ] Unit tests use appropriate mocking (boto3 mocked)
- [ ] Integration tests use real DynamoDB
- [ ] Code formatted with ruff format
- [ ] ZERO ruff violations (ruff check passes clean)
- [ ] All unit tests pass
- [ ] All integration tests pass

### Testing Coverage
- [ ] Unit tests for ALL service methods (CRUD, query, batch, transaction, utility)
- [ ] Unit tests for all 8 sort key operators
- [ ] Unit tests for pagination
- [ ] Unit tests for error handling
- [ ] Integration tests for CRUD operations
- [ ] Integration tests for query operations
- [ ] Integration tests for batch operations
- [ ] Integration tests for transaction operations
- [ ] Integration tests for index queries
- [ ] Integration tests use dotenv for configuration

---

## Next Steps

1. Review this task breakdown
2. Execute tasks using constitution-task-executor
3. Executor will work through ALL tasks autonomously
4. Executor will update checkboxes in real-time
5. Verify zero ruff violations before completion
6. Verify all tests pass before completion
