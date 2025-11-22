# DynamoDB Service with Pydynamo - Constitutional Specification

**Generated**: 2025-11-13
**Spec Type**: Constitution-Aligned
**Feature**: DynamoDB Service Implementation using Pydynamo

---

## 1. Constitutional Compliance Analysis

### ✅ Aligned Requirements

**Database Service Pattern**
- Requirements naturally fit existing service patterns (Redis, MongoDB)
- Follows established conventions for consistency
- **Principles Applied**: I (Simplicity), VII (SOLID - Single Responsibility)

**Structured Data with Pydantic**
- Base model with pk/sk uses Pydantic BaseModel
- Configuration uses Pydantic validation
- **Principles Applied**: IV (Structured Data), III (Type Safety)

**Dependency Injection**
- LoggingService injected into constructor (REQUIRED parameter)
- Config model passed as parameter (REQUIRED parameter)
- No Optional dependencies, no defaults, never created in constructors
- **Principles Applied**: VI (Dependency Injection), VII (Dependency Inversion)

**Type Safety Throughout**
- All methods have type hints
- Return types clearly defined
- Generic types for model operations
- **Principles Applied**: III (Type Safety)

### ⚠️ Constitutional Violations Identified

**No Violations Found**

The requirements are clean and constitutional:
- Simple CRUD operations align with Principle I (Radical Simplicity)
- No fallback logic requested (respects Principle II - Fail Fast)
- Structured models requested (follows Principle IV)
- Following existing patterns maintains consistency (Principle VII - SOLID)

### 🎯 Simplification Opportunities

**Keep Operations Minimal**
- Start with core operations only: create, update, get_one, query
- Avoid adding "nice-to-have" features initially
- **Rationale**: Principle I - implement simplest solution first

**Single Table Design**
- Use base model with pk/sk for all operations
- No complex table-per-entity patterns yet
- **Rationale**: Principle I - avoid over-engineering

**No Retry Logic**
- Let DynamoDB operations fail if they fail
- Trust the pydynamo library's built-in behavior
- **Rationale**: Principle II - fail fast, no fallbacks

**Direct Operations**
- No caching layer initially
- No connection pooling complexity
- **Rationale**: Principle I - keep it simple

---

## 2. Requirements Summary

### Core Functional Requirements

**FR-1: DynamoDB Service Structure**
- Description: Create DynamoDBService following existing service patterns (RedisService, MongoService)
- Constitutional Principles: I, III, VI, VII
- Implementation Approach:
  - Service class in `src/lvrgd/common/services/dynamodb/dynamodb_service.py`
  - Config model in `src/lvrgd/common/services/dynamodb/dynamodb_models.py`
  - Package init in `src/lvrgd/common/services/dynamodb/__init__.py`
  - Inject LoggingService (REQUIRED parameter, no Optional, no defaults)
  - Inject DynamoDBConfig (REQUIRED parameter, no Optional, no defaults)

**FR-2: Base Model with PK/SK**
- Description: Create Pydantic base model with partition key (pk) and sort key (sk) as strings
- Constitutional Principles: III, IV
- Implementation Approach:
  - Create `DynamoDBBaseModel` as Pydantic BaseModel
  - Fields: `pk: str` and `sk: str`
  - Use this model for all database operations
  - Enable type-safe CRUD operations

**FR-3: Create Operation**
- Description: Insert new items into DynamoDB table
- Constitutional Principles: I, II, III
- Implementation Approach:
  - Method: `create(item: DynamoDBBaseModel) -> None`
  - Use pydynamo put_item operation
  - Let it fail if item already exists (fail fast)
  - Type hints for parameters and return value

**FR-4: Update Operation**
- Description: Update existing items in DynamoDB table
- Constitutional Principles: I, II, III
- Implementation Approach:
  - Method: `update(item: DynamoDBBaseModel) -> None`
  - Use pydynamo update_item operation
  - Let it fail if item doesn't exist (fail fast)
  - Type hints for parameters and return value

**FR-5: Get One Operation**
- Description: Retrieve single item by pk and sk
- Constitutional Principles: I, II, III, IV
- Implementation Approach:
  - Method: `get_one(pk: str, sk: str, model_class: type[T]) -> T | None`
  - Use pydynamo get_item operation
  - Return None if not found (simple, predictable)
  - Generic type support for model deserialization
  - Type hints for parameters and return value

**FR-6: Query Operations**
- Description: Query items by partition key with sort key conditions
- Constitutional Principles: I, III, IV
- Implementation Approach:
  - Method: `query_by_pk(pk: str, model_class: type[T], **sk_conditions) -> list[T]`
  - Support common SK operations: begins_with, between, equals
  - Use pydynamo query operations
  - Return empty list if no matches (simple, predictable)
  - Type hints for parameters and return value

**FR-7: Configuration Model**
- Description: Pydantic model for DynamoDB connection configuration
- Constitutional Principles: III, IV
- Implementation Approach:
  - Create `DynamoDBConfig` as Pydantic BaseModel
  - Fields: table_name, region, endpoint_url (optional for local), credentials
  - Field validation with Pydantic validators
  - Type hints on all fields

### Non-Functional Requirements

**NFR-1: Type Safety (Principle III)**
- All functions require comprehensive type hints
- Parameters: explicit types (no Any unless necessary)
- Return values: explicit types including None where applicable
- Generic types: TypeVar for model operations

**NFR-2: Structured Data Models (Principle IV)**
- Pydantic BaseModel for DynamoDBBaseModel
- Pydantic BaseModel for DynamoDBConfig
- No passing dictionaries for structured data
- All database items are typed models

**NFR-3: Dependency Injection (Principle VI)**
- LoggingService injected via constructor (REQUIRED, no Optional, no defaults)
- DynamoDBConfig injected via constructor (REQUIRED, no Optional, no defaults)
- No service creates its own dependencies
- Constructor fails if dependencies not provided (fail fast)

**NFR-4: Testing with Mocking (Principle V)**
- Unit tests mock pydynamo operations
- Unit tests mock LoggingService
- Test happy paths primarily
- Let edge cases fail (don't over-test)

**NFR-5: SOLID Principles (Principle VII)**
- Single Responsibility: DynamoDBService handles only DynamoDB operations
- Open/Closed: Extensible through inheritance if needed
- Liskov Substitution: Generic model operations are substitutable
- Interface Segregation: Clean, focused public API
- Dependency Inversion: Depends on abstractions (LoggingService interface)

---

## 3. System Components

### Data Models (Principle IV - Structured Data)

**DynamoDBBaseModel** (Pydantic BaseModel)
- Purpose: Base model for all DynamoDB items with pk and sk
- Fields:
  - `pk: str` - Partition key
  - `sk: str` - Sort key
- Location: `src/lvrgd/common/services/dynamodb/dynamodb_models.py`
- Note: Users can extend this model for domain-specific items

**DynamoDBConfig** (Pydantic BaseModel)
- Purpose: Configuration for DynamoDB connection
- Fields:
  - `table_name: str` - DynamoDB table name (required)
  - `region: str` - AWS region (default: "us-east-1")
  - `endpoint_url: str | None` - For local DynamoDB (optional)
  - `aws_access_key_id: str | None` - AWS credentials (optional)
  - `aws_secret_access_key: str | None` - AWS credentials (optional)
- Validation:
  - table_name cannot be empty
  - region must be valid AWS region format
- Location: `src/lvrgd/common/services/dynamodb/dynamodb_models.py`

### Services (Principles VI, VII - DI + SOLID)

**DynamoDBService**
- Purpose: Provide simple DynamoDB operations using pydynamo (Single Responsibility)
- Dependencies (ALL REQUIRED):
  - `logger: LoggingService` - Structured logging (NO Optional, NO defaults)
  - `config: DynamoDBConfig` - Connection configuration (NO Optional, NO defaults)
- Key Methods:
  - `__init__(self, logger: LoggingService, config: DynamoDBConfig) -> None`
  - `ping(self) -> bool` - Health check
  - `create(self, item: DynamoDBBaseModel) -> None` - Create item
  - `update(self, item: DynamoDBBaseModel) -> None` - Update item
  - `get_one(self, pk: str, sk: str, model_class: type[T]) -> T | None` - Get single item
  - `query_by_pk(self, pk: str, model_class: type[T], **sk_conditions) -> list[T]` - Query by PK
  - `close(self) -> None` - Cleanup
- Location: `src/lvrgd/common/services/dynamodb/dynamodb_service.py`

### Integration Points

**Pydynamo Library**
- External dependency for DynamoDB operations
- Mocking strategy: Mock pydynamo client and operations in unit tests
- Let pydynamo handle AWS SDK integration (don't wrap excessively)

**AWS DynamoDB**
- External service accessed via pydynamo
- Mocking strategy: Mock at pydynamo level, not AWS SDK level
- Integration tests can use local DynamoDB (docker)

---

## 4. Architectural Approach

### Design Principles Applied

**Radical Simplicity (I)**
- Single service class with focused responsibilities
- No complex query builders or DSLs
- Direct pydynamo operations without abstraction layers
- Base model has only two fields: pk and sk

**Fail Fast (II)**
- No retry logic for failed operations
- No existence checks before operations
- No fallback mechanisms
- Let DynamoDB errors propagate (trust pydynamo exceptions)

**Type Safety (III)**
- All method signatures have complete type hints
- Generic TypeVar[T] for model operations
- Return types clearly indicate None possibilities
- Pydantic models enforce runtime validation

**Structured Data (IV)**
- DynamoDBBaseModel uses Pydantic
- DynamoDBConfig uses Pydantic
- No dictionaries for item data
- All operations accept/return typed models

**Dependency Injection (VI)**
- Constructor receives LoggingService and DynamoDBConfig (both REQUIRED)
- No Optional parameters - all dependencies are REQUIRED
- No default parameter values - explicit injection
- Services never create dependencies internally
- Enables testing through mock injection
- Maintains loose coupling

**SOLID (VII)**
- Single Responsibility: Only DynamoDB operations
- Open/Closed: Can extend for specific use cases
- Liskov Substitution: Generic operations work with any model
- Interface Segregation: Focused API (create, read, update, query)
- Dependency Inversion: Depends on LoggingService abstraction

### File Structure

```
src/lvrgd/common/services/
├── dynamodb/
│   ├── __init__.py (exports DynamoDBService, DynamoDBConfig, DynamoDBBaseModel)
│   ├── dynamodb_service.py (service implementation)
│   └── dynamodb_models.py (DynamoDBConfig, DynamoDBBaseModel)
└── __init__.py (add DynamoDB exports)

tests/
└── dynamodb/
    ├── test_dynamodb_service.py (unit tests with mocking)
    └── __init__.py
```

### Dependencies

**Production Dependencies**
- `pydynamo` - DynamoDB operations library (add to pyproject.toml)
- `boto3` - AWS SDK (likely dependency of pydynamo)
- `pydantic` - Already in project (validation/models)
- `loguru` - Already in project (via LoggingService)

**Development Dependencies**
- `pytest` - Already in project (testing)
- `pytest-mock` - Already in project (mocking)
- `moto` - Optional (for local DynamoDB mocking in integration tests)

---

## 5. Testing Strategy

### Unit Testing Approach (Principle V)

**Mock pydynamo Operations**
- Mock pydynamo client initialization
- Mock put_item, get_item, update_item, query operations
- Verify correct pydynamo API usage
- Don't test pydynamo itself (trust the library)

**Mock LoggingService**
- Use Mock(spec=LoggingService) in tests
- Verify logging calls for important operations
- Don't over-verify logging details

**Test Happy Paths Primarily**
- Focus on successful operations
- Basic error cases (item not found)
- Let edge cases fail naturally (Principle II)

**Type Hints in Test Code**
- All test fixtures have type hints (Principle III)
- Test functions have return type hints
- Maintain type safety in tests

### Test Coverage

**DynamoDBService Tests**
- Initialization with valid config
- Initialization validates dependencies are provided
- create() with valid item
- update() with valid item
- get_one() returns model when found
- get_one() returns None when not found
- query_by_pk() returns list of models
- query_by_pk() returns empty list when no matches
- ping() health check
- close() cleanup

**DynamoDBConfig Tests**
- Valid configuration creation
- Table name validation (not empty)
- Region validation (valid format)
- Pydantic validation errors on invalid input

**DynamoDBBaseModel Tests**
- Model creation with pk and sk
- Model serialization/deserialization
- Pydantic validation

### Test Structure Example

```python
"""Test suite for DynamoDB service implementation."""
from unittest.mock import Mock
import pytest
from lvrgd.common.services import LoggingService
from lvrgd.common.services.dynamodb import (
    DynamoDBService,
    DynamoDBConfig,
    DynamoDBBaseModel
)

@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger for testing."""
    return Mock(spec=LoggingService)

@pytest.fixture
def valid_config() -> DynamoDBConfig:
    """Create a valid DynamoDB configuration."""
    return DynamoDBConfig(
        table_name="test-table",
        region="us-east-1"
    )

@pytest.fixture
def dynamodb_service(mock_logger: Mock, valid_config: DynamoDBConfig) -> DynamoDBService:
    """Create a DynamoDBService instance with mocked dependencies."""
    with patch('pydynamo.client.DynamoDBClient'):
        return DynamoDBService(mock_logger, valid_config)

class TestDynamoDBServiceInitialization:
    def test_initialization_with_valid_config(
        self, mock_logger: Mock, valid_config: DynamoDBConfig
    ) -> None:
        """Test successful initialization."""
        # Test implementation
```

---

## 6. Implementation Constraints

### Constitutional Constraints (NON-NEGOTIABLE)

**Radical Simplicity**
- ✅ No complex abstraction layers over pydynamo
- ✅ No query builder DSLs
- ✅ Keep method signatures simple and clear
- ✅ Single base model with pk/sk only

**Fail Fast**
- ✅ No retry mechanisms
- ✅ No fallback logic
- ✅ No existence checks before operations
- ✅ Let pydynamo exceptions propagate

**Type Safety**
- ✅ Type hints on ALL methods and functions
- ✅ Type hints in test code
- ✅ Generic types for model operations
- ✅ Explicit None returns (not implicit)

**Structured Data**
- ✅ Pydantic models for all structured data
- ✅ No dictionary passing for items
- ✅ No JSON strings for configuration
- ✅ BaseModel-based inheritance

**Dependency Injection**
- ✅ Constructor receives ALL dependencies as REQUIRED parameters
- ✅ NO Optional parameters for dependencies
- ✅ NO default parameter values for dependencies
- ✅ Never create dependencies inside constructor
- ✅ Constructor must fail if dependencies not provided (fail fast)

**SOLID Principles**
- ✅ Single responsibility: only DynamoDB operations
- ✅ Clean separation of concerns
- ✅ Depend on abstractions (LoggingService)
- ✅ Follow existing service patterns

### Technical Constraints

**Python Version**
- Python >= 3.10 (already required by project)

**Pydynamo Integration**
- Add `pydynamo` to pyproject.toml dependencies
- Use pydynamo's type hints where provided
- Follow pydynamo's conventions

**AWS Integration**
- Support both AWS and local DynamoDB (via endpoint_url)
- Use standard AWS credential chain (via boto3)
- Region configuration through config model

**Existing Codebase**
- Follow established service patterns (Redis, MongoDB)
- Match logging patterns and conventions
- Integrate with existing __init__.py exports
- Use existing LoggingService

---

## 7. Success Criteria

### Functional Success

- [ ] DynamoDBService can be instantiated with logger and config (both REQUIRED)
- [ ] create() successfully inserts items into DynamoDB
- [ ] update() successfully updates existing items
- [ ] get_one() retrieves items by pk/sk and returns typed models
- [ ] query_by_pk() queries items and returns typed model lists
- [ ] ping() verifies DynamoDB connectivity
- [ ] close() properly cleans up resources

### Constitutional Success

- [ ] Radical Simplicity (I): Service is straightforward with no unnecessary complexity
- [ ] Fail Fast (II): No fallback logic, operations fail immediately on error
- [ ] Type Safety (III): All methods have complete type hints
- [ ] Structured Data (IV): Pydantic models used for all structured data
- [ ] Unit Testing (V): Tests use appropriate mocking of pydynamo operations
- [ ] Dependency Injection (VI): All dependencies REQUIRED (no Optional, no defaults), injected via constructor, never created internally
- [ ] SOLID Principles (VII): Single responsibility, clean interfaces, dependency inversion

### Code Quality Success

- [ ] Passes `ruff format` (auto-formatting)
- [ ] Passes `ruff check` with ZERO violations
- [ ] All tests pass with pytest
- [ ] Service follows patterns from RedisService and MongoService
- [ ] Documentation is clear and concise
- [ ] Exports properly configured in __init__.py files

---

## 8. Next Steps

### Implementation Phase

1. **Add pydynamo Dependency**
   - Update `pyproject.toml` to include `pydynamo`
   - Verify compatible version with Python 3.10+

2. **Create DynamoDB Models**
   - Implement `DynamoDBBaseModel` with pk/sk
   - Implement `DynamoDBConfig` with Pydantic validation
   - Add field validators following existing patterns

3. **Implement DynamoDBService**
   - Create service class with injected dependencies (all REQUIRED)
   - Implement core methods: create, update, get_one, query_by_pk
   - Add ping() and close() methods
   - Follow existing service patterns exactly

4. **Create Package Structure**
   - Create `__init__.py` with exports
   - Update main services `__init__.py` to include DynamoDB exports
   - Follow redis/mongodb package structure

5. **Write Unit Tests**
   - Create test file with pytest fixtures
   - Mock pydynamo operations appropriately
   - Test happy paths and basic error cases
   - Achieve good coverage without over-testing

6. **Verify Constitutional Compliance**
   - Run `ruff format` on all files
   - Run `ruff check` and fix ALL violations
   - Verify type hints are complete
   - Verify dependency injection follows constitution (all REQUIRED)
   - Verify no fallback logic exists

7. **Integration Testing (Optional)**
   - Create integration tests using local DynamoDB
   - Test against real DynamoDB operations
   - Verify pydynamo integration works correctly

8. **Documentation**
   - Add docstrings following Google style (existing pattern)
   - Update README if needed
   - Document usage examples

### Review Phase

1. Review constitutional compliance against all 7 principles
2. Verify pattern consistency with Redis and MongoDB services
3. Check dependency injection correctness (all REQUIRED, no Optional, no defaults)
4. Ensure ruff check passes with zero violations
5. Confirm all tests pass
6. Validate simplicity (no over-engineering)

### Deployment Phase

1. Merge to main branch following project conventions
2. Version bump following semantic versioning
3. Update changelog
4. Deploy to package repository if applicable

---

## Appendix: Pydynamo Usage Notes

### Expected Pydynamo API Patterns

Based on typical DynamoDB client patterns, pydynamo likely provides:

```python
# Initialization
client = DynamoDBClient(table_name=..., region=..., endpoint_url=...)

# Put item
client.put_item(item_dict)

# Get item
item = client.get_item(key={'pk': '...', 'sk': '...'})

# Update item
client.update_item(key={...}, update_expression=..., expression_attribute_values=...)

# Query
items = client.query(key_condition_expression=...)
```

**Note**: Actual pydynamo API should be verified during implementation. This spec assumes standard DynamoDB SDK patterns.

### Model Serialization

DynamoDBBaseModel will need serialization to/from DynamoDB format:
- `model.model_dump()` for dict representation (Pydantic v2)
- `ModelClass.model_validate(data)` for deserialization (Pydantic v2)
- Handle DynamoDB type conversions if needed (via pydynamo)

---

**Constitutional Compliance Verified**: This specification aligns with all 7 constitutional principles and follows established codebase patterns. Implementation should be straightforward and maintainable.

**Specification Version**: 1.0
**Review Date**: 2025-11-13
**Approved By**: Constitutional Analysis Agent
