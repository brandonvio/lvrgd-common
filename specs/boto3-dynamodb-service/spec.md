# Boto3 DynamoDB Service with Pure Pydantic DTOs - Constitutional Specification

**Generated**: 2025-11-16
**Spec Type**: Constitution-Aligned
**Version**: 1.0.0

---

## 1. Constitutional Compliance Analysis

### Constitutional Alignment Summary

This specification has been analyzed against all 7 constitutional principles. The architecture represents a **paradigm shift** from Active Record (PynamoDB) to Repository Pattern (boto3 + pure DTOs), directly addressing constitutional violations in the current implementation.

### ✅ Strongly Aligned Requirements

**Requirement: Pure Pydantic DTOs (DynamoDBBaseModel)**
- **Principle IV (Structured Data Models)**: Models are simple data definitions with only `pk` and `sk` fields
- **Principle VII (SOLID - Single Responsibility)**: Models hold data only, no persistence logic
- **Why Aligned**: Perfectly exemplifies "Models should be simple data definitions, not complex business logic"

**Requirement: Repository Pattern Service**
- **Principle VII (SOLID - Single Responsibility)**: Service handles persistence, models hold data
- **Principle VI (Dependency Injection)**: DynamoDBConfig and LoggingService injected as REQUIRED parameters
- **Why Aligned**: Clean separation of concerns, no god objects

**Requirement: boto3 Encapsulation**
- **Principle VI (Dependency Injection)**: Config injected, boto3 Table created internally (implementation detail)
- **Principle I (Radical Simplicity)**: boto3 hidden behind clean interface, not exposed externally
- **Why Aligned**: "NEVER create dependencies inside constructors" - we inject config, create table internally from that config

**Requirement: Strong Typing with boto3-stubs**
- **Principle III (Type Safety)**: Type hints everywhere, IDE autocomplete, compile-time error detection
- **Why Aligned**: Comprehensive type safety across all operations

**Requirement: Fail-Fast Error Handling**
- **Principle II (Fail Fast)**: No ping in constructor, exceptions propagate with context, no fallbacks
- **Why Aligned**: Let it fail when assumptions violated

**Requirement: Value-Add Features (Logging, Query Builders)**
- **Principle I (Radical Simplicity)**: Abstracts boto3's verbose API with clean, type-safe interfaces
- **Principle IV (Structured Data)**: SortKeyCondition as Pydantic model, not raw dicts
- **Why Aligned**: Simplifies usage while maintaining constitutional principles

### ⚠️ Constitutional Violations Identified and Resolved

**Violation 1: Current PynamoDB Active Record Pattern**
- **Original Pattern**: Models have `.save()`, `.refresh()`, `.delete()` methods
- **Principles Violated**:
  - IV (Structured Data Models): "Models should be simple data definitions, not complex business logic"
  - VII (SOLID - Single Responsibility): Models have two responsibilities (data + persistence)
- **Why This Violates**: Models are tightly coupled to database, contain business logic, hard to test
- **Constitutional Alternative**: Pure Pydantic DTOs + Repository Service
- **Recommendation**: REMOVE PynamoDB, implement boto3 Repository pattern

**Violation 2: Potential Over-Engineering Risk**
- **Original Consideration**: Could add caching, soft deletes, optimistic locking, audit trails
- **Principle Violated**: I (Radical Simplicity)
- **Why This Violates**: "We aren't building a space shuttle"
- **Constitutional Alternative**: Start minimal - CRUD, query, batch, transactions only
- **Recommendation**: Add complexity only when explicitly needed, not preemptively

**Violation 3: Risk of Defensive Programming in Error Handling**
- **Original Consideration**: Could add extensive validation, retry logic, fallback mechanisms
- **Principle Violated**: II (Fail Fast)
- **Why This Violates**: "Do not implement fallback code unless directly asked to"
- **Constitutional Alternative**: Wrap boto3 exceptions with context, then propagate (fail fast)
- **Recommendation**: No retries, no fallbacks, no extensive validation - wrap and fail

### 🎯 Simplification Opportunities

**Simplification 1: Minimal Base Model**
- Pure Pydantic with only `pk` and `sk` - nothing else
- No helper methods, no business logic
- Let domain models add their own fields via inheritance

**Simplification 2: Single Service Class**
- One `DynamoDBService` class, not multiple specialized services
- Methods organized by operation type (CRUD, query, batch, transaction)
- No service hierarchy or abstract base classes

**Simplification 3: Direct boto3 Usage**
- No custom ORM layer on top of boto3
- Use boto3's natural API, just add type safety and logging
- No query builder DSL - simple Pydantic condition models

**Simplification 4: Minimal Configuration**
- DynamoDBConfig with only essential fields: table_name, region, endpoint_url, credentials
- No connection pools, no retry config, no timeout tuning
- Trust boto3's defaults

---

## 2. Executive Summary

### Vision

Transform DynamoDB interaction from an Active Record pattern (models with database logic) to a Repository pattern (pure DTOs + persistence service), achieving full constitutional compliance and superior testability.

### Key Objectives

1. **Pure Data Models**: Pydantic DTOs with zero database logic
2. **Clean Repository**: Service handles all persistence via encapsulated boto3
3. **Strong Type Safety**: boto3-stubs for compile-time error detection
4. **Constitutional Alignment**: All 7 principles strictly followed
5. **Developer Experience**: Clean API, structured logging, type-safe query builders

### Success Definition

- DynamoDBBaseModel is a pure Pydantic model (no methods, just pk/sk fields)
- DynamoDBService provides all CRUD/query/batch/transaction operations
- boto3 encapsulated - not exposed outside service
- Zero ruff violations
- Comprehensive unit tests with mocked boto3
- All 7 constitutional principles satisfied

---

## 3. Problem Statement

### Current State: PynamoDB Active Record

```python
# Models contain persistence logic
class User(DynamoDBModel):
    class Meta:
        table_name = "users-table"

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)
    email = UnicodeAttribute()

# Usage - model knows how to persist itself
user = User(pk="USER#1", sk="PROFILE", email="test@example.com")
user.save()  # ❌ Violates SRP and Principle IV
```

**Problems:**
1. **Principle IV Violation**: Models contain complex business logic (persistence)
2. **Principle VII Violation**: Single Responsibility violated (data + persistence)
3. **Principle VI Violation**: Hard to inject dependencies, tightly coupled
4. **Testing Difficulty**: Models require database connection, hard to mock
5. **Inflexibility**: Can't swap persistence layer without changing models

### Desired State: boto3 Repository Pattern

```python
# Pure data model
class User(DynamoDBBaseModel):
    email: str
    first_name: str
    last_name: str

# Usage - clear separation of concerns
user = User(pk="USER#1", sk="PROFILE", email="test@example.com", ...)
db_service.save(user)  # ✅ Service handles persistence
```

**Benefits:**
1. **Principle IV Compliance**: Models are simple data definitions
2. **Principle VII Compliance**: Single Responsibility maintained
3. **Principle VI Compliance**: Service uses dependency injection
4. **Easy Testing**: Mock service, models are plain Python objects
5. **Flexibility**: Swap persistence without touching models

---

## 4. Requirements Summary

### Functional Requirements

**FR-1: Pure Pydantic Base Model**
- Create `DynamoDBBaseModel` extending Pydantic `BaseModel`
- Contains only `pk: str` and `sk: str` fields
- Zero methods, zero business logic
- All domain models inherit from this base
- **Constitutional Principles**: IV, VII

**FR-2: boto3-Based Repository Service**
- Create `DynamoDBService` class
- Inject `DynamoDBConfig` and `LoggingService` (both REQUIRED, no Optional, no defaults)
- Create boto3 Table resource internally from config (encapsulated)
- boto3 NOT exposed outside service
- Use `boto3-stubs[dynamodb]` or `mypy-boto3-dynamodb` for type safety
- **Constitutional Principles**: I, III, VI, VII

**FR-3: CRUD Operations**
- `save(item: DynamoDBBaseModel) -> None` - Put item (create/update)
- `get_one(pk: str, sk: str, model_class: type[T]) -> T | None` - Get single item
- `delete(pk: str, sk: str) -> None` - Delete item
- `update(pk: str, sk: str, updates: dict[str, Any]) -> None` - Update specific fields
- **Constitutional Principles**: II (fail fast), III (type hints)

**FR-4: Query Operations**
- `query_by_pk(pk: str, model_class: type[T], limit: int | None = None, last_evaluated_key: dict | None = None) -> PaginationResult[T]`
- `query_by_pk_and_sk(pk: str, sk_condition: SortKeyCondition, model_class: type[T], limit: int | None = None, last_evaluated_key: dict | None = None) -> PaginationResult[T]`
- Support all 8 DynamoDB SK operators: eq, ne, lt, le, gt, ge, begins_with, between
- Support index queries (GSI/LSI) via `index_name: str | None` parameter
- **Constitutional Principles**: III (type safety), IV (structured conditions)

**FR-5: Batch Operations**
- `batch_get(keys: list[tuple[str, str]], model_class: type[T]) -> list[T]` - Batch retrieve
- `batch_write(items: list[DynamoDBBaseModel]) -> None` - Batch save
- Automatic chunking at DynamoDB's 25-item limit
- Handle partial failures with detailed error reporting
- **Constitutional Principles**: I (simplicity), II (fail on errors)

**FR-6: Transaction Operations**
- `transact_write(operations: list[TransactionWriteItem]) -> None` - Atomic write
- `transact_get(keys: list[tuple[str, str]], model_class: type[T]) -> list[T]` - Atomic read
- **Constitutional Principles**: II (fail on transaction errors), IV (structured operations)

**FR-7: Utility Operations**
- `ping() -> bool` - Health check (NOT in constructor)
- `count(pk: str, sk_condition: SortKeyCondition | None = None) -> int` - Count items
- **Constitutional Principles**: II (fail fast)

**FR-8: Value-Add Features**
- **Structured Logging**: Log all operations with pk, sk, operation type, timing
- **Error Wrapping**: Wrap boto3 ClientError with domain exceptions
- **Query Builders**: Type-safe `SortKeyCondition` Pydantic model
- **Pagination**: `PaginationResult[T]` with items, last_evaluated_key, count
- **Constitutional Principles**: I (clean abstractions), III (type safety), IV (structured data)

### Non-Functional Requirements

**NFR-1: Type Safety (Principle III)**
- Type hints on ALL methods (public and private)
- Generic TypeVar for model class handling
- Pydantic validation for all configuration and condition models
- boto3-stubs for compile-time error detection

**NFR-2: Dependency Injection (Principle VI)**
- All dependencies injected via constructor (DynamoDBConfig, LoggingService)
- ALL dependencies REQUIRED - no Optional, no default values
- boto3 Table created internally from config (NOT injected)
- Service fails fast if dependencies not provided

**NFR-3: Testing (Principle V)**
- Unit tests with mocked boto3 Table resource
- Models are pure Python objects (no mocking needed)
- Service dependencies easily mocked
- Test happy path, let edge cases fail

**NFR-4: Code Quality (Principle II)**
- Zero ruff violations
- All linting errors resolved before completion
- Clean, readable code
- Minimal cyclomatic complexity (<10)

---

## 5. System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                     │
│  (Domain logic uses DTOs and DynamoDBService)          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ├─ Uses DTOs ──────────┐
                  │                      │
                  ├─ Uses Service ───┐   │
                  │                  │   │
                  ▼                  ▼   ▼
┌──────────────────────────┐  ┌─────────────────────┐
│  DynamoDBService         │  │ DynamoDBBaseModel   │
│  (Repository)            │  │ (Pure Pydantic DTO) │
│                          │  │                     │
│ - Injected: Config, Log  │  │ - pk: str           │
│ - Internal: boto3 Table  │  │ - sk: str           │
│                          │  │                     │
│ Methods:                 │  │ Domain Models:      │
│ - save(item)             │  │ - User(Base)        │
│ - get_one(pk, sk)        │  │ - Order(Base)       │
│ - query_by_pk(pk)        │  │ - Product(Base)     │
│ - batch_write(items)     │  │                     │
│ - transact_write(ops)    │  └─────────────────────┘
│                          │
│ Encapsulated boto3:      │
│ - self._table: Table     │
│   (created internally)   │
└──────────┬───────────────┘
           │
           │ boto3 API (hidden)
           ▼
┌──────────────────────────┐
│   AWS DynamoDB Service   │
└──────────────────────────┘
```

### Component Responsibilities

**DynamoDBBaseModel (Pure DTO)**
- **Responsibility**: Define data structure for DynamoDB items
- **Principles**: IV (simple data definition), VII (single responsibility)
- **Contains**: Only `pk` and `sk` fields as Pydantic fields
- **Does NOT Contain**: Methods, business logic, database operations

**DynamoDBService (Repository)**
- **Responsibility**: Handle all DynamoDB persistence operations
- **Principles**: VI (dependency injection), VII (single responsibility), I (simplicity)
- **Injected**: DynamoDBConfig (REQUIRED), LoggingService (REQUIRED)
- **Internal**: boto3 Table resource (created from config, NOT injected)
- **Provides**: CRUD, query, batch, transaction operations
- **Hides**: boto3 API details, complexity of DynamoDB operations

**DynamoDBConfig (Configuration Model)**
- **Responsibility**: Hold configuration for DynamoDB connection
- **Principles**: IV (structured data)
- **Contains**: table_name, region, endpoint_url, aws_access_key_id, aws_secret_access_key
- **Validation**: Pydantic validation for all fields

**SortKeyCondition (Query Model)**
- **Responsibility**: Type-safe representation of DynamoDB sort key conditions
- **Principles**: III (type safety), IV (structured data)
- **Contains**: operator, value(s)
- **Operators**: eq, ne, lt, le, gt, ge, begins_with, between

**PaginationResult[T] (Result Model)**
- **Responsibility**: Hold paginated query results
- **Principles**: III (type safety via generics), IV (structured data)
- **Contains**: items, last_evaluated_key, count

### Architectural Principles Applied

**Radical Simplicity (I)**
- Single service class (no hierarchy)
- Pure Pydantic models (no complex base class)
- Direct boto3 usage (no custom ORM layer)
- Minimal configuration

**Fail Fast (II)**
- No ping in constructor
- Exceptions propagate immediately
- No fallback logic or defensive programming
- REQUIRED dependencies (fail if not provided)

**Type Safety (III)**
- Type hints on all methods
- Generic TypeVar for model classes
- boto3-stubs for boto3 operations
- Pydantic validation on all inputs

**Structured Data (IV)**
- Pydantic for models, config, conditions, results
- No dictionaries for structured data
- Models are data definitions only

**Dependency Injection (VI)**
- Config and logger injected (REQUIRED)
- boto3 Table created internally from config
- Dependencies passed in, never created in constructor
- Testable via mocking

**SOLID (VII)**
- **Single Responsibility**: Service = persistence, Models = data
- **Open/Closed**: Extensible via model inheritance
- **Liskov Substitution**: All DynamoDBBaseModel subtypes work
- **Interface Segregation**: Focused service interface
- **Dependency Inversion**: Depend on injected abstractions

---

## 6. Data Models

### DynamoDBBaseModel (Pure Pydantic DTO)

**Purpose**: Base class for all DynamoDB items, providing only pk/sk structure

**Location**: `src/lvrgd_common/models/dynamodb_base_model.py`

**Definition**:
```python
from pydantic import BaseModel, Field

class DynamoDBBaseModel(BaseModel):
    """Pure Pydantic base model for DynamoDB items.

    Contains only partition key (pk) and sort key (sk).
    All domain models should inherit from this base.

    This is a PURE DTO - no methods, no business logic, no persistence.
    """
    pk: str = Field(..., description="Partition key")
    sk: str = Field(..., description="Sort key")
```

**Constitutional Alignment**:
- **Principle IV**: Simple data definition only
- **Principle VII**: Single responsibility (data structure)

**Usage Example**:
```python
class User(DynamoDBBaseModel):
    """User domain model - pure data."""
    email: str
    first_name: str
    last_name: str
    created_at: str

# Usage - just a data container
user = User(
    pk="USER#123",
    sk="PROFILE",
    email="user@example.com",
    first_name="John",
    last_name="Doe",
    created_at="2025-11-16T10:00:00Z"
)
```

### DynamoDBConfig (Configuration Model)

**Purpose**: Configuration for DynamoDB connection

**Location**: `src/lvrgd_common/models/dynamodb_config.py`

**Definition**:
```python
from pydantic import BaseModel, Field

class DynamoDBConfig(BaseModel):
    """Configuration for DynamoDB connection."""
    table_name: str = Field(..., description="DynamoDB table name")
    region: str = Field(..., description="AWS region")
    endpoint_url: str | None = Field(None, description="Custom endpoint URL (for local testing)")
    aws_access_key_id: str | None = Field(None, description="AWS access key ID")
    aws_secret_access_key: str | None = Field(None, description="AWS secret access key")
```

**Constitutional Alignment**:
- **Principle IV**: Structured configuration data
- **Principle III**: Type hints on all fields

### SortKeyCondition (Query Condition Model)

**Purpose**: Type-safe representation of DynamoDB sort key query conditions

**Location**: `src/lvrgd_common/models/sort_key_condition.py`

**Definition**:
```python
from typing import Literal
from pydantic import BaseModel, Field

OperatorType = Literal["eq", "ne", "lt", "le", "gt", "ge", "begins_with", "between"]

class SortKeyCondition(BaseModel):
    """Type-safe sort key condition for DynamoDB queries."""
    operator: OperatorType = Field(..., description="Comparison operator")
    value: str = Field(..., description="Primary comparison value")
    value2: str | None = Field(None, description="Secondary value (for 'between' operator)")

    def validate_between(self) -> "SortKeyCondition":
        """Validate that 'between' operator has both values."""
        if self.operator == "between" and self.value2 is None:
            raise ValueError("'between' operator requires value2")
        return self
```

**Constitutional Alignment**:
- **Principle III**: Type safety via Literal operator type
- **Principle IV**: Structured condition model (not raw dict)
- **Principle II**: Validation fails fast if invalid

**Usage Example**:
```python
# Equals
condition = SortKeyCondition(operator="eq", value="PROFILE")

# Range
condition = SortKeyCondition(operator="gt", value="2025-01-01")

# Begins with
condition = SortKeyCondition(operator="begins_with", value="ORDER#")

# Between
condition = SortKeyCondition(operator="between", value="2025-01-01", value2="2025-12-31")
```

### PaginationResult[T] (Generic Result Model)

**Purpose**: Hold paginated query results with type safety

**Location**: `src/lvrgd_common/models/pagination_result.py`

**Definition**:
```python
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound="DynamoDBBaseModel")

class PaginationResult(BaseModel, Generic[T]):
    """Paginated query result with type-safe items."""
    items: list[T] = Field(..., description="Query result items")
    last_evaluated_key: dict[str, str] | None = Field(None, description="Last evaluated key for pagination")
    count: int = Field(..., description="Number of items returned")

    class Config:
        arbitrary_types_allowed = True
```

**Constitutional Alignment**:
- **Principle III**: Generic type safety
- **Principle IV**: Structured result model

**Usage Example**:
```python
result: PaginationResult[User] = db_service.query_by_pk(
    pk="USER#123",
    model_class=User,
    limit=10
)

for user in result.items:  # Type-safe iteration
    print(user.email)

if result.last_evaluated_key:
    # Fetch next page
    next_result = db_service.query_by_pk(
        pk="USER#123",
        model_class=User,
        limit=10,
        last_evaluated_key=result.last_evaluated_key
    )
```

### TransactionWriteItem (Transaction Operation Model)

**Purpose**: Represent a single write operation in a transaction

**Location**: `src/lvrgd_common/models/transaction_write_item.py`

**Definition**:
```python
from typing import Literal
from pydantic import BaseModel, Field

OperationType = Literal["put", "update", "delete"]

class TransactionWriteItem(BaseModel):
    """Single write operation in a DynamoDB transaction."""
    operation: OperationType = Field(..., description="Operation type")
    item: DynamoDBBaseModel | None = Field(None, description="Item for put operation")
    pk: str | None = Field(None, description="Partition key for update/delete")
    sk: str | None = Field(None, description="Sort key for update/delete")
    updates: dict[str, Any] | None = Field(None, description="Updates for update operation")
```

**Constitutional Alignment**:
- **Principle III**: Type safety via Literal operation type
- **Principle IV**: Structured transaction operation

---

## 7. Service Design

### DynamoDBService

**Purpose**: Repository pattern service for all DynamoDB persistence operations

**Location**: `src/lvrgd_common/services/dynamodb_service.py`

**Class Signature**:
```python
from typing import TypeVar, Generic
from mypy_boto3_dynamodb.service_resource import Table
import boto3

from lvrgd_common.models.dynamodb_base_model import DynamoDBBaseModel
from lvrgd_common.models.dynamodb_config import DynamoDBConfig
from lvrgd_common.models.sort_key_condition import SortKeyCondition
from lvrgd_common.models.pagination_result import PaginationResult
from lvrgd_common.services.logging_service import LoggingService

T = TypeVar("T", bound=DynamoDBBaseModel)

class DynamoDBService:
    """Repository service for DynamoDB operations using boto3.

    Encapsulates boto3 Table resource and provides type-safe operations
    on pure Pydantic DTOs (DynamoDBBaseModel subclasses).

    Constitutional Compliance:
    - Principle VI: Config and logger injected (REQUIRED, no Optional, no defaults)
    - Principle VI: boto3 Table created internally from config (NOT injected)
    - Principle VII: Single responsibility - persistence only
    - Principle I: Simple, clean abstraction over boto3
    - Principle II: Fail fast - no fallbacks, exceptions propagate
    """

    def __init__(self, logger: LoggingService, config: DynamoDBConfig) -> None:
        """Initialize DynamoDB service.

        Args:
            logger: Logging service (REQUIRED)
            config: DynamoDB configuration (REQUIRED)

        Constitutional Note:
        - Dependencies are REQUIRED (no Optional, no defaults)
        - boto3 Table created internally from config (implementation detail)
        - No ping() in constructor (fail fast when actually used)
        """
        self.log = logger
        self.config = config

        # Create boto3 resources internally from injected config
        # This is an IMPLEMENTATION DETAIL, not a dependency
        resource = boto3.resource(
            "dynamodb",
            region_name=config.region,
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )
        self._table: Table = resource.Table(config.table_name)
```

**Constitutional Alignment**:
- **Principle VI**: Config and logger injected (REQUIRED)
- **Principle VI**: boto3 Table created internally (not injected)
- **Principle II**: No ping in constructor
- **Principle III**: Type hints on all methods
- **Principle VII**: Single responsibility (persistence)

### Method Categories

#### CRUD Operations

```python
def save(self, item: DynamoDBBaseModel) -> None:
    """Save item to DynamoDB (create or update).

    Args:
        item: DynamoDBBaseModel instance to save

    Raises:
        DynamoDBServiceError: If put operation fails

    Constitutional: Fail fast if boto3 raises error
    """

def get_one(self, pk: str, sk: str, model_class: type[T]) -> T | None:
    """Get single item by primary key.

    Args:
        pk: Partition key
        sk: Sort key
        model_class: Model class for deserialization

    Returns:
        Model instance or None if not found

    Raises:
        DynamoDBServiceError: If get operation fails

    Constitutional: Return None if not found, fail fast on errors
    """

def delete(self, pk: str, sk: str) -> None:
    """Delete item by primary key.

    Args:
        pk: Partition key
        sk: Sort key

    Raises:
        DynamoDBServiceError: If delete operation fails

    Constitutional: Fail fast if deletion fails
    """

def update(self, pk: str, sk: str, updates: dict[str, Any]) -> None:
    """Update specific fields of an item.

    Args:
        pk: Partition key
        sk: Sort key
        updates: Field updates as dict

    Raises:
        DynamoDBServiceError: If update operation fails

    Constitutional: Fail fast, no validation beyond boto3
    """
```

#### Query Operations

```python
def query_by_pk(
    self,
    pk: str,
    model_class: type[T],
    limit: int | None = None,
    last_evaluated_key: dict[str, str] | None = None,
    index_name: str | None = None
) -> PaginationResult[T]:
    """Query items by partition key.

    Args:
        pk: Partition key
        model_class: Model class for deserialization
        limit: Maximum items to return
        last_evaluated_key: Pagination token
        index_name: GSI/LSI name (optional)

    Returns:
        PaginationResult with typed items

    Raises:
        DynamoDBServiceError: If query fails

    Constitutional: Type-safe via generics, fail fast on errors
    """

def query_by_pk_and_sk(
    self,
    pk: str,
    sk_condition: SortKeyCondition,
    model_class: type[T],
    limit: int | None = None,
    last_evaluated_key: dict[str, str] | None = None,
    index_name: str | None = None
) -> PaginationResult[T]:
    """Query items by partition key and sort key condition.

    Args:
        pk: Partition key
        sk_condition: Sort key condition (eq, lt, begins_with, etc.)
        model_class: Model class for deserialization
        limit: Maximum items to return
        last_evaluated_key: Pagination token
        index_name: GSI/LSI name (optional)

    Returns:
        PaginationResult with typed items

    Raises:
        DynamoDBServiceError: If query fails

    Constitutional: Structured condition model (Principle IV)
    """
```

#### Batch Operations

```python
def batch_get(self, keys: list[tuple[str, str]], model_class: type[T]) -> list[T]:
    """Batch retrieve items by primary keys.

    Args:
        keys: List of (pk, sk) tuples
        model_class: Model class for deserialization

    Returns:
        List of model instances (may be partial if some keys not found)

    Raises:
        DynamoDBBatchOperationError: If batch get fails

    Constitutional:
    - Automatically chunks at 25-item limit (Principle I - simplicity)
    - Fail fast on errors
    """

def batch_write(self, items: list[DynamoDBBaseModel]) -> None:
    """Batch save items to DynamoDB.

    Args:
        items: List of DynamoDBBaseModel instances

    Raises:
        DynamoDBBatchOperationError: If batch write fails or partial failure

    Constitutional:
    - Automatically chunks at 25-item limit
    - Fail fast on partial failures (report which items failed)
    """
```

#### Transaction Operations

```python
def transact_write(self, operations: list[TransactionWriteItem]) -> None:
    """Execute atomic write transaction.

    Args:
        operations: List of transaction write operations

    Raises:
        DynamoDBTransactionError: If transaction fails

    Constitutional: All-or-nothing, fail fast on transaction failure
    """

def transact_get(self, keys: list[tuple[str, str]], model_class: type[T]) -> list[T]:
    """Execute atomic read transaction.

    Args:
        keys: List of (pk, sk) tuples
        model_class: Model class for deserialization

    Returns:
        List of model instances (all or none)

    Raises:
        DynamoDBTransactionError: If transaction fails

    Constitutional: All-or-nothing atomic read
    """
```

#### Utility Operations

```python
def ping(self) -> bool:
    """Health check - verify DynamoDB table is accessible.

    Returns:
        True if table is accessible

    Raises:
        DynamoDBServiceError: If table is not accessible

    Constitutional: NOT called in constructor, fail fast if inaccessible
    """

def count(self, pk: str, sk_condition: SortKeyCondition | None = None) -> int:
    """Count items matching query.

    Args:
        pk: Partition key
        sk_condition: Optional sort key condition

    Returns:
        Count of matching items

    Raises:
        DynamoDBServiceError: If count query fails

    Constitutional: Simple count, fail fast on errors
    """
```

---

## 8. Error Handling Strategy

### Constitutional Approach: Fail Fast

**Principle II Compliance**: No fallback logic, no defensive programming, no extensive validation. Wrap boto3 errors with context and propagate immediately.

### Error Hierarchy

```python
class DynamoDBServiceError(Exception):
    """Base exception for DynamoDB service errors."""
    def __init__(self, message: str, operation: str, pk: str | None = None, sk: str | None = None) -> None:
        self.operation = operation
        self.pk = pk
        self.sk = sk
        super().__init__(message)

class DynamoDBBatchOperationError(DynamoDBServiceError):
    """Batch operation error with partial failure details."""
    def __init__(
        self,
        message: str,
        operation: str,
        failed_items: list[dict[str, Any]],
        successful_count: int
    ) -> None:
        self.failed_items = failed_items
        self.successful_count = successful_count
        super().__init__(message, operation)

class DynamoDBTransactionError(DynamoDBServiceError):
    """Transaction error (all-or-nothing failure)."""
    pass
```

### Error Wrapping Pattern

```python
# Example: save() method
def save(self, item: DynamoDBBaseModel) -> None:
    try:
        self._table.put_item(Item=item.model_dump())
        self.log.info(
            "Item saved",
            extra={"pk": item.pk, "sk": item.sk, "operation": "save"}
        )
    except ClientError as e:
        self.log.error(
            "Failed to save item",
            extra={"pk": item.pk, "sk": item.sk, "error": str(e)}
        )
        raise DynamoDBServiceError(
            message=f"Failed to save item: {e}",
            operation="save",
            pk=item.pk,
            sk=item.sk
        ) from e
```

### Error Handling Principles

1. **Wrap, Don't Swallow**: Catch boto3 ClientError, wrap with domain exception, propagate
2. **Add Context**: Include operation, pk, sk in exception
3. **Log Before Raising**: Structured log with error details
4. **No Retries**: Let caller decide retry strategy
5. **No Fallbacks**: Fail immediately, no "try X then Y" logic

### Constitutional Compliance

- **Principle II (Fail Fast)**: Errors propagate immediately
- **No defensive programming**: Trust boto3, trust inputs
- **No existence checks**: Let DynamoDB return empty results
- **No type validation**: Type hints are documentation, trust them

---

## 9. Type Safety Implementation

### boto3-stubs Integration

**Purpose**: Provide compile-time type checking for boto3 operations

**Installation**:
```bash
pip install boto3-stubs[dynamodb]
# OR
pip install mypy-boto3-dynamodb
```

**Usage in Service**:
```python
from mypy_boto3_dynamodb.service_resource import Table, DynamoDBServiceResource
import boto3

class DynamoDBService:
    def __init__(self, logger: LoggingService, config: DynamoDBConfig) -> None:
        self.log = logger
        self.config = config

        # Type-safe boto3 resource
        resource: DynamoDBServiceResource = boto3.resource(
            "dynamodb",
            region_name=config.region,
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )

        # Type-safe Table
        self._table: Table = resource.Table(config.table_name)

        # Now IDE autocomplete and type checking work!
        # self._table.put_item(...)  <- IDE knows this method
        # self._table.query(...)     <- IDE knows parameters
```

### Generic TypeVar Pattern

**Purpose**: Preserve type information through service methods

```python
from typing import TypeVar

T = TypeVar("T", bound=DynamoDBBaseModel)

class DynamoDBService:
    def get_one(self, pk: str, sk: str, model_class: type[T]) -> T | None:
        """Return type is the same as model_class parameter."""
        response = self._table.get_item(Key={"pk": pk, "sk": sk})
        if "Item" not in response:
            return None
        return model_class(**response["Item"])  # Type-safe instantiation

# Usage - IDE knows result is User, not just DynamoDBBaseModel
user: User | None = db_service.get_one("USER#1", "PROFILE", User)
if user:
    print(user.email)  # IDE autocomplete works!
```

### Type Hints on All Methods

**Constitutional Requirement (Principle III)**: Type hints on EVERY method

```python
# ✅ Good - complete type hints
def query_by_pk(
    self,
    pk: str,
    model_class: type[T],
    limit: int | None = None,
    last_evaluated_key: dict[str, str] | None = None,
    index_name: str | None = None
) -> PaginationResult[T]:
    ...

# ❌ Bad - missing type hints
def query_by_pk(self, pk, model_class, limit=None):
    ...
```

### Pydantic Validation

**Purpose**: Validate all structured inputs (config, conditions, operations)

```python
# Configuration validated on instantiation
config = DynamoDBConfig(
    table_name="users-table",
    region="us-east-1",
    endpoint_url="http://localhost:8000"  # ✅ Validated by Pydantic
)

# Conditions validated
condition = SortKeyCondition(
    operator="between",  # ✅ Literal type - only valid operators
    value="2025-01-01",
    value2="2025-12-31"
)

# Will raise ValidationError if invalid
invalid_condition = SortKeyCondition(
    operator="invalid_op",  # ❌ Not in Literal - fails validation
    value="x"
)
```

---

## 10. Testing Strategy

### Unit Testing Approach (Principle V)

**Constitutional Guidance**: Use appropriate mocking strategies, test happy path, let edge cases fail.

### Mocking boto3 Table

**Pattern**: Mock boto3 Table resource in unit tests

```python
from unittest.mock import Mock, MagicMock
import pytest

from lvrgd_common.services.dynamodb_service import DynamoDBService
from lvrgd_common.models.dynamodb_config import DynamoDBConfig
from lvrgd_common.services.logging_service import LoggingService

@pytest.fixture
def mock_logger() -> Mock:
    """Mock LoggingService."""
    return Mock(spec=LoggingService)

@pytest.fixture
def config() -> DynamoDBConfig:
    """DynamoDB configuration for testing."""
    return DynamoDBConfig(
        table_name="test-table",
        region="us-east-1",
        endpoint_url="http://localhost:8000"
    )

@pytest.fixture
def mock_table() -> MagicMock:
    """Mock boto3 Table resource."""
    return MagicMock()

@pytest.fixture
def db_service(mock_logger: Mock, config: DynamoDBConfig, mock_table: MagicMock, monkeypatch) -> DynamoDBService:
    """DynamoDBService with mocked boto3 Table."""
    # Mock boto3.resource to return mock table
    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table

    def mock_boto3_resource(*args, **kwargs):
        return mock_resource

    monkeypatch.setattr("boto3.resource", mock_boto3_resource)

    service = DynamoDBService(logger=mock_logger, config=config)
    service._table = mock_table  # Directly inject mock
    return service
```

### Test Examples

**Test CRUD Operations**:
```python
def test_save_item(db_service: DynamoDBService, mock_table: MagicMock) -> None:
    """Test saving an item."""
    user = User(pk="USER#1", sk="PROFILE", email="test@example.com")

    db_service.save(user)

    mock_table.put_item.assert_called_once_with(
        Item=user.model_dump()
    )

def test_get_one_found(db_service: DynamoDBService, mock_table: MagicMock) -> None:
    """Test getting an existing item."""
    mock_table.get_item.return_value = {
        "Item": {
            "pk": "USER#1",
            "sk": "PROFILE",
            "email": "test@example.com"
        }
    }

    result = db_service.get_one("USER#1", "PROFILE", User)

    assert result is not None
    assert result.pk == "USER#1"
    assert result.email == "test@example.com"

def test_get_one_not_found(db_service: DynamoDBService, mock_table: MagicMock) -> None:
    """Test getting a non-existent item."""
    mock_table.get_item.return_value = {}  # No "Item" key

    result = db_service.get_one("USER#999", "PROFILE", User)

    assert result is None  # Constitutional: return None, don't raise
```

**Test Query Operations**:
```python
def test_query_by_pk(db_service: DynamoDBService, mock_table: MagicMock) -> None:
    """Test querying by partition key."""
    mock_table.query.return_value = {
        "Items": [
            {"pk": "USER#1", "sk": "PROFILE", "email": "test@example.com"}
        ],
        "Count": 1,
        "LastEvaluatedKey": None
    }

    result = db_service.query_by_pk("USER#1", User)

    assert result.count == 1
    assert len(result.items) == 1
    assert result.items[0].email == "test@example.com"
    assert result.last_evaluated_key is None
```

**Test Error Handling**:
```python
def test_save_error(db_service: DynamoDBService, mock_table: MagicMock) -> None:
    """Test that errors are wrapped and propagated."""
    from botocore.exceptions import ClientError

    mock_table.put_item.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Invalid item"}},
        "PutItem"
    )

    user = User(pk="USER#1", sk="PROFILE", email="test@example.com")

    # Constitutional: fail fast, exception propagates
    with pytest.raises(DynamoDBServiceError) as exc_info:
        db_service.save(user)

    assert exc_info.value.operation == "save"
    assert exc_info.value.pk == "USER#1"
```

### Testing Pure DTOs

**Benefit**: Models are pure Python objects - no mocking needed!

```python
def test_user_model() -> None:
    """Test User model instantiation."""
    user = User(
        pk="USER#1",
        sk="PROFILE",
        email="test@example.com",
        first_name="John",
        last_name="Doe"
    )

    assert user.pk == "USER#1"
    assert user.email == "test@example.com"
    # No database, no mocking, just pure data!
```

### Constitutional Testing Principles

1. **Mock External Dependencies**: Mock boto3 Table, not models
2. **Test Happy Path**: Focus on successful operations
3. **Let Edge Cases Fail**: Trust fail-fast philosophy
4. **Type Hints in Tests**: All test code uses type hints
5. **No Over-Engineering**: Simple, focused tests

---

## 11. Logging and Observability

### Structured Logging Strategy

**Purpose**: Provide detailed, queryable logs for all DynamoDB operations

**Pattern**: Log before and after each operation with structured context

```python
def save(self, item: DynamoDBBaseModel) -> None:
    """Save item with structured logging."""
    start_time = time.time()

    self.log.info(
        "Saving item to DynamoDB",
        extra={
            "operation": "save",
            "pk": item.pk,
            "sk": item.sk,
            "table": self.config.table_name
        }
    )

    try:
        self._table.put_item(Item=item.model_dump())

        elapsed = time.time() - start_time
        self.log.info(
            "Item saved successfully",
            extra={
                "operation": "save",
                "pk": item.pk,
                "sk": item.sk,
                "elapsed_ms": round(elapsed * 1000, 2)
            }
        )
    except ClientError as e:
        elapsed = time.time() - start_time
        self.log.error(
            "Failed to save item",
            extra={
                "operation": "save",
                "pk": item.pk,
                "sk": item.sk,
                "error_code": e.response["Error"]["Code"],
                "error_message": e.response["Error"]["Message"],
                "elapsed_ms": round(elapsed * 1000, 2)
            }
        )
        raise DynamoDBServiceError(...) from e
```

### Log Context Fields

**All Operations**:
- `operation`: Operation type (save, get_one, query_by_pk, etc.)
- `table`: Table name
- `elapsed_ms`: Operation duration in milliseconds

**Item Operations (save, get_one, delete, update)**:
- `pk`: Partition key
- `sk`: Sort key

**Query Operations**:
- `pk`: Partition key
- `sk_condition`: Sort key condition (if applicable)
- `index_name`: Index name (if querying index)
- `limit`: Query limit
- `result_count`: Number of items returned

**Batch Operations**:
- `batch_size`: Number of items in batch
- `successful_count`: Number of successful operations
- `failed_count`: Number of failed operations

**Transaction Operations**:
- `operation_count`: Number of operations in transaction
- `operation_types`: Types of operations (put, update, delete)

### Observability Goals

1. **Performance Tracking**: Log operation duration for all calls
2. **Error Analysis**: Structured error context for debugging
3. **Usage Patterns**: Track which operations are most common
4. **Query Optimization**: Identify slow queries via duration logs
5. **Failure Investigation**: Detailed context on all failures

### Constitutional Alignment

- **Principle I (Simplicity)**: Structured logging adds value without complexity
- **Principle III (Type Safety)**: Log fields are well-defined
- **Principle VII (Single Responsibility)**: Logging service handles logging, DynamoDB service uses it

---

## 12. Query Builder Design

### SortKeyCondition Model

**Purpose**: Type-safe, clean abstraction over DynamoDB's verbose KeyConditionExpression syntax

**Benefits**:
1. Type safety via Literal operator types
2. Pydantic validation
3. Clean, readable code
4. IDE autocomplete

### Operator Support

**All 8 DynamoDB Sort Key Operators**:

```python
# Equality
condition = SortKeyCondition(operator="eq", value="PROFILE")

# Comparison
condition = SortKeyCondition(operator="lt", value="2025-12-31")
condition = SortKeyCondition(operator="le", value="2025-12-31")
condition = SortKeyCondition(operator="gt", value="2025-01-01")
condition = SortKeyCondition(operator="ge", value="2025-01-01")

# Pattern matching
condition = SortKeyCondition(operator="begins_with", value="ORDER#")

# Range
condition = SortKeyCondition(operator="between", value="2025-01-01", value2="2025-12-31")

# Inequality (scan, not query - but supported for completeness)
condition = SortKeyCondition(operator="ne", value="INACTIVE")
```

### Internal Translation to boto3

**Pattern**: Translate SortKeyCondition to boto3 KeyConditionExpression

```python
def _build_key_condition_expression(
    self,
    pk: str,
    sk_condition: SortKeyCondition | None
) -> tuple[str, dict[str, Any]]:
    """Build boto3 KeyConditionExpression from SortKeyCondition.

    Returns:
        Tuple of (expression_string, expression_attribute_values)
    """
    from boto3.dynamodb.conditions import Key

    # Partition key condition (always present)
    key_condition = Key("pk").eq(pk)

    # Sort key condition (optional)
    if sk_condition:
        sk_key = Key("sk")

        if sk_condition.operator == "eq":
            key_condition = key_condition & sk_key.eq(sk_condition.value)
        elif sk_condition.operator == "lt":
            key_condition = key_condition & sk_key.lt(sk_condition.value)
        elif sk_condition.operator == "le":
            key_condition = key_condition & sk_key.lte(sk_condition.value)
        elif sk_condition.operator == "gt":
            key_condition = key_condition & sk_key.gt(sk_condition.value)
        elif sk_condition.operator == "ge":
            key_condition = key_condition & sk_key.gte(sk_condition.value)
        elif sk_condition.operator == "begins_with":
            key_condition = key_condition & sk_key.begins_with(sk_condition.value)
        elif sk_condition.operator == "between":
            key_condition = key_condition & sk_key.between(
                sk_condition.value,
                sk_condition.value2
            )

    return key_condition
```

### Usage in Service Methods

```python
def query_by_pk_and_sk(
    self,
    pk: str,
    sk_condition: SortKeyCondition,
    model_class: type[T],
    limit: int | None = None,
    last_evaluated_key: dict[str, str] | None = None,
    index_name: str | None = None
) -> PaginationResult[T]:
    """Query with sort key condition."""
    # Build boto3 key condition
    key_condition = self._build_key_condition_expression(pk, sk_condition)

    # Build query parameters
    query_params: dict[str, Any] = {
        "KeyConditionExpression": key_condition
    }

    if limit:
        query_params["Limit"] = limit
    if last_evaluated_key:
        query_params["ExclusiveStartKey"] = last_evaluated_key
    if index_name:
        query_params["IndexName"] = index_name

    # Execute query
    response = self._table.query(**query_params)

    # Deserialize results
    items = [model_class(**item) for item in response.get("Items", [])]

    return PaginationResult(
        items=items,
        last_evaluated_key=response.get("LastEvaluatedKey"),
        count=response["Count"]
    )
```

### Constitutional Alignment

- **Principle I (Simplicity)**: Clean abstraction over boto3's verbose API
- **Principle III (Type Safety)**: Literal operator types, Pydantic validation
- **Principle IV (Structured Data)**: Condition is a Pydantic model, not a dict

---

## 13. Pagination Implementation

### PaginationResult Model

**Design**: Generic model holding query results with pagination metadata

```python
class PaginationResult(BaseModel, Generic[T]):
    """Paginated query result."""
    items: list[T]
    last_evaluated_key: dict[str, str] | None
    count: int
```

### Pagination Pattern

**Client-Driven Pagination**: Client controls when to fetch next page

```python
# Initial query
result = db_service.query_by_pk("USER#123", User, limit=10)

print(f"Found {result.count} users")
for user in result.items:
    print(user.email)

# Check if more pages exist
if result.last_evaluated_key:
    # Fetch next page
    next_result = db_service.query_by_pk(
        "USER#123",
        User,
        limit=10,
        last_evaluated_key=result.last_evaluated_key
    )

    for user in next_result.items:
        print(user.email)
```

### Pagination Loop Pattern

**Fetch All Pages**:
```python
all_items: list[User] = []
last_key = None

while True:
    result = db_service.query_by_pk(
        "USER#123",
        User,
        limit=100,
        last_evaluated_key=last_key
    )

    all_items.extend(result.items)

    if not result.last_evaluated_key:
        break  # No more pages

    last_key = result.last_evaluated_key

print(f"Total items: {len(all_items)}")
```

### Index Pagination

**Same pattern works for index queries**:
```python
result = db_service.query_by_pk(
    pk="ACTIVE",  # GSI partition key
    model_class=User,
    limit=50,
    index_name="status-index"  # Query GSI
)

# Pagination works identically
if result.last_evaluated_key:
    next_result = db_service.query_by_pk(
        pk="ACTIVE",
        model_class=User,
        limit=50,
        last_evaluated_key=result.last_evaluated_key,
        index_name="status-index"
    )
```

### Constitutional Alignment

- **Principle I (Simplicity)**: Simple, consistent pagination pattern
- **Principle III (Type Safety)**: Generic PaginationResult preserves type
- **Principle IV (Structured Data)**: Pagination metadata in structured model

---

## 14. Implementation Roadmap

### Phase 1: Core Models and Configuration

**Tasks**:
1. Create `DynamoDBBaseModel` (pure Pydantic with pk/sk)
2. Create `DynamoDBConfig` (connection configuration)
3. Create `SortKeyCondition` (query condition model)
4. Create `PaginationResult[T]` (generic result model)
5. Create `TransactionWriteItem` (transaction operation model)

**Success Criteria**:
- All models are pure Pydantic (no logic)
- Type hints on all fields
- Pydantic validation works
- Zero ruff violations

**Estimated Effort**: 2-3 hours

### Phase 2: Service Foundation

**Tasks**:
1. Create `DynamoDBService` class skeleton
2. Implement constructor with dependency injection
3. Create boto3 Table resource from config
4. Add custom exception classes
5. Implement `ping()` utility method

**Success Criteria**:
- Config and logger injected (REQUIRED, no Optional)
- boto3 Table created internally
- No ping in constructor
- Type hints on constructor
- Zero ruff violations

**Estimated Effort**: 2-3 hours

### Phase 3: CRUD Operations

**Tasks**:
1. Implement `save(item)`
2. Implement `get_one(pk, sk, model_class)`
3. Implement `delete(pk, sk)`
4. Implement `update(pk, sk, updates)`
5. Add structured logging to all operations
6. Add error wrapping to all operations

**Success Criteria**:
- All CRUD operations work
- Type hints on all methods
- Structured logging on all operations
- Errors wrapped and propagated
- Unit tests with mocked boto3
- Zero ruff violations

**Estimated Effort**: 4-6 hours

### Phase 4: Query Operations

**Tasks**:
1. Implement `query_by_pk()`
2. Implement `query_by_pk_and_sk()`
3. Implement sort key condition translation
4. Add pagination support
5. Add index support (GSI/LSI)
6. Add `count()` method

**Success Criteria**:
- All query operations work
- All 8 SK operators supported
- Pagination works correctly
- Index queries work
- Type-safe PaginationResult
- Unit tests for all query types
- Zero ruff violations

**Estimated Effort**: 6-8 hours

### Phase 5: Batch and Transaction Operations

**Tasks**:
1. Implement `batch_get()`
2. Implement `batch_write()` with chunking
3. Implement `transact_write()`
4. Implement `transact_get()`
5. Add partial failure handling for batches
6. Add transaction error handling

**Success Criteria**:
- Batch operations auto-chunk at 25 items
- Partial failures reported clearly
- Transactions are atomic (all-or-nothing)
- Unit tests for batch and transaction
- Zero ruff violations

**Estimated Effort**: 6-8 hours

### Phase 6: Testing and Documentation

**Tasks**:
1. Comprehensive unit tests for all operations
2. Integration tests with local DynamoDB
3. Type checking with mypy
4. Linting with ruff
5. Code documentation (docstrings)
6. Usage examples

**Success Criteria**:
- 100% method coverage
- Integration tests pass against local DynamoDB
- mypy passes with no errors
- Zero ruff violations
- All methods have docstrings

**Estimated Effort**: 8-10 hours

### Phase 7: Migration and Deprecation

**Tasks**:
1. Keep existing PynamoDB service temporarily
2. Migrate existing code to use new service
3. Update all tests
4. Deprecate PynamoDB service
5. Remove PynamoDB dependency

**Success Criteria**:
- All code uses new boto3 service
- All tests pass
- PynamoDB removed from dependencies
- No regression in functionality

**Estimated Effort**: Variable (depends on existing codebase)

### Total Estimated Effort

**30-40 hours** for complete implementation, testing, and migration.

---

## 15. Success Criteria and Validation

### Functional Success Criteria

- [ ] **FR-1**: DynamoDBBaseModel is a pure Pydantic model (only pk/sk fields, no methods)
- [ ] **FR-2**: DynamoDBService accepts DynamoDBConfig and LoggingService via DI (REQUIRED)
- [ ] **FR-2**: DynamoDBService creates boto3 Table internally from config
- [ ] **FR-2**: boto3 is NOT exposed outside the service
- [ ] **FR-3**: All CRUD operations work (save, get_one, delete, update)
- [ ] **FR-4**: All query operations work (query_by_pk, query_by_pk_and_sk)
- [ ] **FR-4**: All 8 sort key operators supported
- [ ] **FR-4**: Index queries work (GSI/LSI)
- [ ] **FR-5**: Batch operations work (batch_get, batch_write)
- [ ] **FR-5**: Batch auto-chunking at 25 items
- [ ] **FR-6**: Transaction operations work (transact_write, transact_get)
- [ ] **FR-7**: Utility operations work (ping, count)
- [ ] **FR-8**: Structured logging on all operations
- [ ] **FR-8**: Error wrapping with domain exceptions
- [ ] **FR-8**: Query builder (SortKeyCondition) works
- [ ] **FR-8**: Pagination works (PaginationResult)

### Constitutional Success Criteria

**Principle I - Radical Simplicity**
- [ ] Single service class (no hierarchy)
- [ ] Pure Pydantic models (no complexity)
- [ ] Direct boto3 usage (no custom ORM)
- [ ] Minimal configuration
- [ ] Functions with cyclomatic complexity <10
- [ ] No over-engineered features

**Principle II - Fail Fast**
- [ ] No ping in constructor
- [ ] Exceptions propagate immediately
- [ ] No fallback logic
- [ ] No defensive programming
- [ ] Zero ruff violations
- [ ] Specific exception types (not blind catching)

**Principle III - Type Safety**
- [ ] Type hints on ALL methods (public and private)
- [ ] Generic TypeVar for model classes
- [ ] boto3-stubs for boto3 operations
- [ ] Pydantic validation on all inputs
- [ ] mypy passes with no errors

**Principle IV - Structured Data Models**
- [ ] All models are Pydantic
- [ ] No dictionaries for structured data
- [ ] Models are simple data definitions only
- [ ] No business logic in models

**Principle V - Unit Testing with Mocking**
- [ ] Unit tests mock boto3 Table
- [ ] Models tested as pure objects (no mocking)
- [ ] Service dependencies mocked
- [ ] Appropriate mocking strategies
- [ ] Test happy path, let edge cases fail

**Principle VI - Dependency Injection**
- [ ] Config and logger injected (REQUIRED, no Optional, no defaults)
- [ ] boto3 Table created internally (NOT injected)
- [ ] Constructor fails fast if dependencies missing
- [ ] No dependencies created in constructor
- [ ] Testable via mock injection

**Principle VII - SOLID Principles**
- [ ] Single Responsibility: Service = persistence, Models = data
- [ ] Open/Closed: Extensible via model inheritance
- [ ] Liskov Substitution: All DynamoDBBaseModel subtypes work
- [ ] Interface Segregation: Focused service interface
- [ ] Dependency Inversion: Depend on injected abstractions

### Quality Gates

**Code Quality**:
- [ ] `ruff format` applied to all files
- [ ] `ruff check` passes with ZERO violations
- [ ] `mypy` passes with no errors
- [ ] All functions have docstrings
- [ ] Inline comments removed (docstrings preferred)

**Testing**:
- [ ] 100% method coverage in unit tests
- [ ] Integration tests pass against local DynamoDB
- [ ] All tests have type hints
- [ ] No flaky tests
- [ ] Test suite runs in <5 seconds

**Documentation**:
- [ ] All public methods have docstrings
- [ ] Docstrings include Args, Returns, Raises
- [ ] Usage examples provided
- [ ] Constitutional alignment documented

### Acceptance Checklist

- [ ] Pure Pydantic DTOs with no database logic
- [ ] Repository service with encapsulated boto3
- [ ] Strong typing using boto3-stubs
- [ ] All CRUD, query, batch, transaction operations
- [ ] Type hints on all methods
- [ ] Comprehensive unit tests
- [ ] Zero ruff violations
- [ ] Zero mypy errors
- [ ] All 7 constitutional principles followed
- [ ] Service adds clear value (logging, error handling, type safety, query builders)
- [ ] Ready for production use

---

## Appendix A: File Structure

```
src/lvrgd_common/
├── models/
│   ├── __init__.py
│   ├── dynamodb_base_model.py          # Pure Pydantic base (pk/sk only)
│   ├── dynamodb_config.py              # Configuration model
│   ├── sort_key_condition.py           # Query condition model
│   ├── pagination_result.py            # Pagination result model
│   └── transaction_write_item.py       # Transaction operation model
│
├── services/
│   ├── __init__.py
│   └── dynamodb_service.py             # Repository service with boto3
│
└── exceptions/
    ├── __init__.py
    └── dynamodb_exceptions.py          # Custom exceptions

tests/
├── unit/
│   ├── test_dynamodb_base_model.py     # Model tests (pure objects)
│   ├── test_dynamodb_config.py         # Config tests
│   ├── test_sort_key_condition.py      # Condition tests
│   └── test_dynamodb_service.py        # Service tests (mocked boto3)
│
└── integration/
    └── test_dynamodb_integration.py    # Integration tests (local DynamoDB)
```

## Appendix B: boto3-stubs Type Examples

**Type-Safe Table Operations**:
```python
from mypy_boto3_dynamodb.service_resource import Table

# IDE knows all Table methods and parameters
table: Table = ...

# put_item - IDE autocomplete works
table.put_item(
    Item={"pk": "USER#1", "sk": "PROFILE", "email": "test@example.com"}
)

# query - IDE knows parameters
response = table.query(
    KeyConditionExpression=Key("pk").eq("USER#1"),
    Limit=10,
    IndexName="email-index"  # Type-checked!
)

# get_item - return type known
response = table.get_item(
    Key={"pk": "USER#1", "sk": "PROFILE"}
)
# response["Item"] is typed as dict[str, Any]
```

**Type-Safe Batch Operations**:
```python
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

resource: DynamoDBServiceResource = boto3.resource("dynamodb")

# batch_writer - context manager type-checked
with table.batch_writer() as batch:
    batch.put_item(Item={"pk": "USER#1", "sk": "PROFILE"})
    batch.delete_item(Key={"pk": "USER#2", "sk": "PROFILE"})
```

## Appendix C: Migration Examples

**Before (PynamoDB Active Record)**:
```python
# Model with persistence logic
class User(DynamoDBModel):
    class Meta:
        table_name = "users-table"

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)
    email = UnicodeAttribute()
    first_name = UnicodeAttribute()
    last_name = UnicodeAttribute()

# Usage - model knows how to persist
user = User(pk="USER#1", sk="PROFILE", email="test@example.com", ...)
user.save()  # ❌ Violates SRP

# Query - model-level operation
users = User.query("USER#1", User.sk.begins_with("PROFILE"))
```

**After (boto3 Repository Pattern)**:
```python
# Pure data model
class User(DynamoDBBaseModel):
    email: str
    first_name: str
    last_name: str
    created_at: str

# Usage - clear separation
user = User(pk="USER#1", sk="PROFILE", email="test@example.com", ...)
db_service.save(user)  # ✅ Service handles persistence

# Query - service-level operation
condition = SortKeyCondition(operator="begins_with", value="PROFILE")
result = db_service.query_by_pk_and_sk("USER#1", condition, User)
```

---

**End of Constitutional Specification**

This specification has been generated in strict compliance with all 7 constitutional principles. All requirements have been analyzed for constitutional alignment, violations have been flagged with alternatives, and simplification opportunities have been identified. The architecture enforces clean separation between data (pure DTOs) and persistence (repository service), enabling superior testability and constitutional compliance.
