# Boto3 DynamoDB Service with Pydantic DTOs - Requirements

**Created**: 2025-11-16
**Objective**: Refactor DynamoDB service to use boto3 with pure Pydantic DTOs following Repository pattern

## Core Requirement

Replace the current PynamoDB-based Active Record implementation with a clean Repository pattern:

- **Models = Pure Pydantic DTOs** (simple data structures with pk/sk)
- **Service = Repository** (handles all persistence operations via boto3)

## Architectural Philosophy

### Current Problem (PynamoDB Active Record)

```python
# Models have database logic - violates SRP
user = User(pk="USER#1", sk="PROFILE", email="test@example.com")
user.save()  # ❌ Model knows how to persist itself
```

**Issues:**
- Models are not pure DTOs - they contain persistence logic
- Tight coupling to DynamoDB
- Hard to test - models depend on database connection
- Violates Constitutional Principle IV: "Models should be simple data definitions, not complex business logic"
- Violates Constitutional Principle VII (SOLID): Single Responsibility

### Desired Solution (boto3 + Repository Pattern)

```python
# Models are pure data structures
class User(DynamoDBBaseModel):
    email: str
    first_name: str
    last_name: str

user = User(pk="USER#1", sk="PROFILE", email="test@example.com", ...)

# Service handles persistence
db_service.save(user)  # ✅ Clear separation of concerns
```

**Benefits:**
- ✅ Pure separation of concerns - models are just data
- ✅ Easy to test - can mock the service, models are just Python objects
- ✅ Swappable persistence - change DB without touching models
- ✅ Constitutional Principle IV compliance - simple data definitions
- ✅ Constitutional Principle VII compliance - Single Responsibility
- ✅ Constitutional Principle VI compliance - Dependency Injection (boto3 table injected)

## Functional Requirements

### FR-1: Pure Pydantic Base Model

Create `DynamoDBBaseModel` as pure Pydantic BaseModel:
- Contains only `pk: str` and `sk: str` fields
- No database logic or methods
- All domain models inherit from this base

### FR-2: boto3-Based Repository Service

Create `DynamoDBService` that:
- Accepts boto3 Table resource via dependency injection (not created in constructor)
- Accepts LoggingService via dependency injection
- Provides CRUD operations on Pydantic models
- Handles serialization/deserialization between Pydantic and DynamoDB

### FR-3: Core Operations

Support all essential DynamoDB operations:

**CRUD:**
- `save(item: DynamoDBBaseModel)` - Put item (create/update)
- `get_one(pk: str, sk: str, model_class: type[T]) -> T | None` - Get single item
- `delete(pk: str, sk: str)` - Delete item
- `update(pk: str, sk: str, updates: dict[str, Any])` - Update specific fields

**Query:**
- `query_by_pk(pk: str, model_class: type[T])` - Query by partition key
- `query_by_pk_and_sk(pk: str, sk_condition: SortKeyCondition, model_class: type[T])` - Query with sort key filter
- Support all 8 DynamoDB SK operators: eq, ne, lt, le, gt, ge, begins_with, between

**Batch:**
- `batch_get(keys: list[tuple[str, str]], model_class: type[T])` - Batch retrieve
- `batch_write(items: list[DynamoDBBaseModel])` - Batch save

**Transactions:**
- `transact_write(operations: list[TransactionWriteItem])` - Atomic write transaction
- `transact_get(keys: list[tuple[str, str]], model_class: type[T])` - Atomic read transaction

**Utility:**
- `ping() -> bool` - Health check
- `count(pk: str, sk_condition: SortKeyCondition | None = None) -> int` - Count items

### FR-4: Type Safety

- Type hints on ALL methods
- Generic TypeVar for model class handling
- Pydantic validation for all configuration and condition models

### FR-5: Pagination Support

- Return `PaginationResult[T]` for query operations
- Include `items`, `last_evaluated_key`, `count`
- Support `limit` and `last_evaluated_key` parameters

### FR-6: Index Support

- Support querying Global Secondary Indexes (GSI)
- Support querying Local Secondary Indexes (LSI)
- Add `index_name: str | None` parameter to query methods

### FR-7: Value-Add Features

Beyond basic boto3 wrapping, add:

**Observability:**
- Structured logging for all operations (pk, sk, operation type, timing)
- Operation timing metrics
- Success/failure tracking

**Error Handling:**
- Wrap boto3 ClientError with domain-specific exceptions
- Custom exceptions: DynamoDBBatchOperationError, DynamoDBTransactionError
- Fail-fast principle - let errors propagate

**Batch Optimization:**
- Automatic chunking at DynamoDB's 25-item limit
- Handle partial failures with detailed error reporting

**Query Builders:**
- Type-safe `SortKeyCondition` model for query conditions
- Clean abstraction over boto3's verbose expression syntax

## Constitutional Alignment

### Principle I - Radical Simplicity
- Pure Pydantic models are simpler than PynamoDB models
- Service provides clean abstraction over boto3's verbose API
- No unnecessary complexity

### Principle II - Fail Fast
- No ping() in constructor
- Exceptions propagate (wrapped with context)
- No fallback logic or defensive programming

### Principle III - Type Safety
- Type hints everywhere
- Pydantic validation for all inputs
- Generic TypeVar pattern for type preservation

### Principle IV - Structured Data Models
- Pydantic for all models (DTOs, config, conditions)
- Models are simple data definitions ONLY
- No business logic in models

### Principle V - Unit Testing with Mocking
- Mock boto3 Table resource in tests
- Models are pure Python objects (easy to test)
- Service dependencies injected (mockable)

### Principle VI - Dependency Injection
- boto3 Table resource injected (REQUIRED, no Optional, no defaults)
- LoggingService injected (REQUIRED)
- NEVER create boto3 clients/resources in constructor
- Constructor only assigns dependencies

### Principle VII - SOLID
- **Single Responsibility**: Service handles persistence, models hold data
- **Open/Closed**: Extensible via model inheritance
- **Liskov Substitution**: All DynamoDBBaseModel subtypes work with service
- **Interface Segregation**: Focused service interface
- **Dependency Inversion**: Depends on injected boto3 Table abstraction

## Success Criteria

- [ ] DynamoDBBaseModel is pure Pydantic (no database logic)
- [ ] All domain models can inherit from DynamoDBBaseModel
- [ ] DynamoDBService uses boto3 for all operations
- [ ] boto3 Table resource is dependency-injected (not created in constructor)
- [ ] All CRUD, query, batch, and transaction operations work
- [ ] Type hints on all methods
- [ ] Comprehensive unit tests with mocked boto3 Table
- [ ] Zero ruff violations
- [ ] All 7 constitutional principles followed
- [ ] Service adds clear value: logging, error handling, type safety, query builders

## Non-Goals

- Do NOT use PynamoDB
- Do NOT put database logic in models
- Do NOT create boto3 clients in service constructor
- Do NOT add caching (can be added later)
- Do NOT add soft deletes (can be added later)

## Migration Path

1. Keep existing PynamoDB service temporarily
2. Build new boto3 service alongside
3. Migrate tests to new service
4. Deprecate PynamoDB service
5. Remove PynamoDB dependency

## References

- Constitutional Principle IV: "Models should be simple data definitions, not complex business logic"
- Constitutional Principle VI: "NEVER create dependencies inside constructors"
- Constitutional Principle VII: SOLID principles (especially Single Responsibility)
