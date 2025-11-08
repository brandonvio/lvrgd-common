# MongoDB Pydantic Support - Constitutional Specification

**Generated**: 2025-11-08
**Spec Type**: Constitution-Aligned

## 1. Constitutional Compliance Analysis

### Aligned Requirements
- **Mirror Redis pattern** - Existing Redis Pydantic implementation already follows constitutional principles (I, III, IV, VI, VII)
- **Use model_dump()** - Pydantic's native serialization method aligns with Principle IV (Structured Data)
- **Use model_validate()** - Type-safe deserialization aligns with Principle III (Type Safety)
- **Add to existing service** - Extending MongoService maintains single responsibility (Principle VII)
- **Backward compatible** - Keep existing dict methods without defensive programming (Principle II)

### Constitutional Violations Identified

**No Violations Found**

The user requirements are already constitutionally aligned. This is a straightforward feature addition that:
- Extends an existing service with new methods (Open/Closed Principle)
- Maintains backward compatibility without defensive code
- Uses Pydantic models for structured data (Principle IV)
- Follows the proven Redis pattern that already passes constitutional review
- Uses type hints throughout (Principle III)

### Simplification Opportunities

**Pattern Reuse**
- Redis service already implements: `get_model`, `set_model`, `mget_models`, `mset_models`, `hget_model`, `hset_model`
- MongoDB only needs: `find_one_model`, `insert_one_model`, `find_many_models`, `insert_many_models`
- Hash operations don't apply to MongoDB (collection-based, not hash-based)
- This is simpler than Redis - fewer methods needed

**No Over-Engineering**
- Don't add caching (Redis already handles that)
- Don't add retry logic (Principle II - Fail Fast)
- Don't add validation beyond Pydantic's native validation
- Don't add complex query builders - keep it simple

## 2. Requirements Summary

### Core Functional Requirements

**FR-1: Add find_one_model Method**
- Description: Find single document and deserialize to Pydantic model
- Constitutional Principles: I (Simple), III (Type Safe), IV (Structured Data)
- Implementation Approach: Use existing `find_one`, deserialize with `model_validate(**data)`

**FR-2: Add insert_one_model Method**
- Description: Serialize Pydantic model and insert as document
- Constitutional Principles: I (Simple), III (Type Safe), IV (Structured Data)
- Implementation Approach: Use `model.model_dump()`, call existing `insert_one`

**FR-3: Add find_many_models Method**
- Description: Find multiple documents and deserialize to list of Pydantic models
- Constitutional Principles: I (Simple), III (Type Safe), IV (Structured Data)
- Implementation Approach: Use existing `find_many`, map with `model_validate(**doc)` for each

**FR-4: Add insert_many_models Method**
- Description: Serialize multiple Pydantic models and bulk insert
- Constitutional Principles: I (Simple), III (Type Safe), IV (Structured Data)
- Implementation Approach: Map `model.model_dump()` over models, call existing `insert_many`

**FR-5: Add update_one_model Method**
- Description: Update document using Pydantic model data
- Constitutional Principles: I (Simple), III (Type Safe), IV (Structured Data)
- Implementation Approach: Use `model.model_dump()`, create `$set` operation, call existing `update_one`

**FR-6: Add update_many_models Method**
- Description: Bulk update documents using Pydantic model data
- Constitutional Principles: I (Simple), III (Type Safe), IV (Structured Data)
- Implementation Approach: Use `model.model_dump()`, create `$set` operation, call existing `update_many`

### Non-Functional Requirements

- **Type Safety**: All methods use generic TypeVar[T] for type inference (Principle III)
- **Data Models**: All methods accept/return Pydantic BaseModel instances (Principle IV)
- **Backward Compatibility**: Existing dict-based methods remain unchanged (Principle I - Simple)
- **Fail Fast**: Pydantic ValidationError propagates without catching (Principle II)
- **Testing**: Unit tests with mocked MongoDB client, following existing test patterns (Principle V)

## 3. System Components

### Data Models (Principle IV - Structured Data)

**No New Models Required**
- Service works with any user-defined Pydantic BaseModel
- Uses TypeVar[T] for generic model support
- Existing MongoConfig remains unchanged

### Services (Principles VI, VII - DI + SOLID)

**MongoService** (Extended)
- Purpose: Add Pydantic model operations to existing MongoDB service
- Dependencies: Unchanged (LoggingService, MongoConfig - both REQUIRED)
- New Methods:
  - `find_one_model(collection: str, query: dict, model_class: type[T]) -> T | None`
  - `insert_one_model(collection: str, model: BaseModel) -> InsertOneResult`
  - `find_many_models(collection: str, query: dict, model_class: type[T], **kwargs) -> list[T]`
  - `insert_many_models(collection: str, models: list[BaseModel], **kwargs) -> list[ObjectId]`
  - `update_one_model(collection: str, query: dict, model: BaseModel, **kwargs) -> UpdateResult`
  - `update_many_models(collection: str, query: dict, model: BaseModel, **kwargs) -> UpdateResult`
- Location: `src/lvrgd/common/services/mongodb/mongodb_service.py`

### Integration Points

**Pydantic Integration**
- Use `model.model_dump()` for serialization (converts to dict)
- Use `model_class.model_validate(**dict)` for deserialization
- ValidationError propagates without catching (Principle II)

**Existing MongoDB Methods**
- All new methods delegate to existing dict-based methods
- No duplication of MongoDB client logic
- Maintains single responsibility

## 4. Architectural Approach

### Design Principles Applied

**Radical Simplicity (I)**
- Each new method is 3-5 lines: validate/serialize -> delegate -> return
- No complex logic - just adapters between Pydantic and existing dict methods
- Reuse all existing MongoDB operations

**Fail Fast (II)**
- Pydantic ValidationError propagates immediately
- No try-except around validation
- No existence checks on model fields
- Let MongoDB errors propagate naturally

**Type Safety (III)**
- TypeVar[T] bound to BaseModel for generic model support
- All parameters and returns fully typed
- Type hints enable IDE autocomplete for model fields

**Structured Data (IV)**
- All new methods enforce Pydantic BaseModel usage
- No loose dicts in new methods
- model_dump() and model_validate() for conversion only

**Dependency Injection (VI)**
- No new dependencies added
- Existing dependencies remain REQUIRED (no Optional, no defaults)
- Service maintains constructor injection pattern

**SOLID (VII)**
- Open/Closed: Extending service without modifying existing methods
- Single Responsibility: Each method does one thing (serialize/deserialize + delegate)
- Liskov Substitution: New methods follow same patterns as existing
- Interface Segregation: Pydantic methods separate from dict methods
- Dependency Inversion: Depends on Pydantic abstraction (BaseModel)

### File Structure
```
src/lvrgd/common/services/mongodb/
├── mongodb_models.py (unchanged)
└── mongodb_service.py (add 6 new methods, add TypeVar import)

tests/mongodb/
└── test_mongodb_service.py (add new test classes)
```

## 5. Testing Strategy

### Unit Testing Approach (Principle V)

**Mock Strategy**
- Mock pymongo client (same pattern as existing tests)
- Mock model serialization in tests (return known dicts)
- Test validation errors with invalid data
- Test None returns for missing documents

**Test Coverage Structure**
```python
class TestFindOneModel:
    - test_find_one_model_success
    - test_find_one_model_missing_returns_none
    - test_find_one_model_validation_error_propagates

class TestInsertOneModel:
    - test_insert_one_model_success
    - test_insert_one_model_with_session

class TestFindManyModels:
    - test_find_many_models_success
    - test_find_many_models_empty_list
    - test_find_many_models_with_pagination

class TestInsertManyModels:
    - test_insert_many_models_success
    - test_insert_many_models_ordered_false

class TestUpdateOneModel:
    - test_update_one_model_success
    - test_update_one_model_with_upsert

class TestUpdateManyModels:
    - test_update_many_models_success
```

### Test Models
```python
class UserModel(BaseModel):
    name: str
    age: int
    email: str | None = None

class ProductModel(BaseModel):
    id: str
    price: float
    in_stock: bool
```

## 6. Implementation Constraints

### Constitutional Constraints (NON-NEGOTIABLE)

- Keep each method simple (3-5 lines max)
- No try-except around Pydantic validation (fail fast)
- Type hints on all new methods (TypeVar[T] for generics)
- Use Pydantic BaseModel for all model operations
- No Optional dependencies, no defaults
- Follow SOLID principles

### Technical Constraints

- Python 3.11+ (existing project constraint)
- Pydantic v2.x (existing dependency)
- pymongo client (existing dependency)
- Must maintain backward compatibility with existing dict methods
- Must pass ruff check with zero violations
- Must maintain existing logging patterns

### Pattern Constraints

**Mirror Redis Pattern Exactly**
- Method naming: `{operation}_model` and `{operation}_models`
- Parameter order: collection/key first, then model/query, then options
- Return types: Match base operation but with models instead of dicts
- Error handling: Let Pydantic and MongoDB errors propagate

**Differences from Redis**
- MongoDB is collection-based (not key-value)
- MongoDB has queries (not just get/set)
- MongoDB has update operations (partial updates via $set)
- No hash operations needed for MongoDB

## 7. Success Criteria

### Functional Success

- [ ] `find_one_model` retrieves and deserializes single document
- [ ] `insert_one_model` serializes and inserts single model
- [ ] `find_many_models` retrieves and deserializes multiple documents
- [ ] `insert_many_models` serializes and inserts multiple models
- [ ] `update_one_model` serializes and updates single document
- [ ] `update_many_models` serializes and updates multiple documents
- [ ] All methods support optional session parameter for transactions
- [ ] ValidationError propagates on invalid data
- [ ] None returned for missing documents (find_one_model)
- [ ] Empty list returned for no matches (find_many_models)

### Constitutional Success

- [ ] All code follows radical simplicity (I) - each method under 10 lines
- [ ] Fail fast applied throughout (II) - no defensive validation catching
- [ ] Type hints on all functions (III) - full TypeVar[T] support
- [ ] Pydantic models used exclusively (IV) - no dict parameters in new methods
- [ ] Unit tests with appropriate mocking (V) - MongoDB client mocked
- [ ] Dependency injection maintained (VI) - no new dependencies created in constructor
- [ ] SOLID principles maintained (VII) - Open/Closed, Single Responsibility
- [ ] Zero ruff violations after implementation
- [ ] All tests pass with appropriate mocking

### Code Quality Success

- [ ] Methods follow exact Redis pattern naming
- [ ] Logging matches existing MongoDB service patterns
- [ ] Docstrings follow existing service style
- [ ] Test coverage mirrors Redis test structure
- [ ] Integration tests can use real MongoDB (separate file)
- [ ] Backward compatibility verified - existing tests still pass

## 8. Implementation Details

### Method Signatures

```python
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class MongoService:
    # Existing methods unchanged...

    def find_one_model(
        self,
        collection_name: str,
        query: dict[str, Any],
        model_class: type[T],
        projection: dict[str, Any] | None = None,
        session: ClientSession | None = None,
    ) -> T | None:
        """Find single document and deserialize to Pydantic model."""
        ...

    def insert_one_model(
        self,
        collection_name: str,
        model: BaseModel,
        session: ClientSession | None = None,
    ) -> InsertOneResult:
        """Serialize Pydantic model and insert as document."""
        ...

    def find_many_models(
        self,
        collection_name: str,
        query: dict[str, Any],
        model_class: type[T],
        *,
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 0,
        skip: int = 0,
        session: ClientSession | None = None,
    ) -> list[T]:
        """Find multiple documents and deserialize to Pydantic models."""
        ...

    def insert_many_models(
        self,
        collection_name: str,
        models: list[BaseModel],
        *,
        ordered: bool = True,
        session: ClientSession | None = None,
    ) -> list[ObjectId]:
        """Serialize multiple Pydantic models and bulk insert."""
        ...

    def update_one_model(
        self,
        collection_name: str,
        query: dict[str, Any],
        model: BaseModel,
        *,
        upsert: bool = False,
        session: ClientSession | None = None,
    ) -> UpdateResult:
        """Update document using Pydantic model data."""
        ...

    def update_many_models(
        self,
        collection_name: str,
        query: dict[str, Any],
        model: BaseModel,
        *,
        upsert: bool = False,
        session: ClientSession | None = None,
    ) -> UpdateResult:
        """Update documents using Pydantic model data."""
        ...
```

### Implementation Pattern (Example: find_one_model)

```python
def find_one_model(
    self,
    collection_name: str,
    query: dict[str, Any],
    model_class: type[T],
    projection: dict[str, Any] | None = None,
    session: ClientSession | None = None,
) -> T | None:
    """Find single document and deserialize to Pydantic model.

    Args:
        collection_name: Name of the collection
        query: Query filter
        model_class: Pydantic model class to deserialize into
        projection: Fields to include/exclude
        session: Optional session for transaction support

    Returns:
        Validated Pydantic model instance, or None if not found

    Raises:
        ValidationError: If document doesn't match model schema

    Example:
        user = mongo_service.find_one_model(
            "users",
            {"email": "john@example.com"},
            UserModel
        )
    """
    self.log.debug("Finding document as model", collection=collection_name, model=model_class.__name__)
    doc = self.find_one(collection_name, query, projection, session)

    if doc is None:
        self.log.debug("No document found", collection=collection_name)
        return None

    result = model_class.model_validate(doc)
    self.log.debug("Successfully validated model", collection=collection_name, model=model_class.__name__)
    return result
```

## 9. Error Handling Strategy

### Pydantic ValidationError (Principle II - Fail Fast)

**What**: Pydantic raises ValidationError when data doesn't match model schema
**Strategy**: Let it propagate - do NOT catch
**Reason**: Principle II (Fail Fast) - invalid data should fail immediately

```python
# CORRECT (Constitutional)
doc = self.find_one(collection, query)
return model_class.model_validate(doc)  # Let ValidationError propagate

# WRONG (Anti-Constitutional)
try:
    return model_class.model_validate(doc)
except ValidationError:
    return None  # NO! This violates Fail Fast
```

### MongoDB Errors

**What**: ConnectionFailure, OperationFailure, etc.
**Strategy**: Let them propagate (already handled in base methods)
**Reason**: New methods delegate to existing methods that handle MongoDB errors

### None Handling

**What**: find_one returns None when document not found
**Strategy**: Return None from find_one_model (expected behavior)
**Reason**: This is not an error - it's valid MongoDB behavior

## 10. Logging Strategy

### Follow Existing Pattern

```python
# On method entry
self.log.debug("Finding document as model", collection=collection_name, model=model_class.__name__)

# On successful deserialiation
self.log.debug("Successfully validated model", collection=collection_name, model=model_class.__name__)

# On serialization
self.log.debug("Serializing model for insert", collection=collection_name, model=type(model).__name__)

# Delegate to base methods for actual operation logging
```

### Don't Duplicate Logging

- Base methods already log insert/update/delete operations
- New methods only log serialization/deserialization steps
- Keep logging simple and informative

## 11. Migration Path

### No Migration Needed

**Backward Compatible**
- Existing dict-based methods remain unchanged
- New model-based methods are additions only
- Users can adopt gradually
- No breaking changes

**Adoption Pattern**
```python
# Old way (still works)
user_dict = mongo_service.find_one("users", {"email": "john@example.com"})
user = UserModel(**user_dict)

# New way (simpler)
user = mongo_service.find_one_model("users", {"email": "john@example.com"}, UserModel)
```

## 12. Performance Considerations

### No Performance Impact

- Pydantic serialization/deserialization is fast
- Same MongoDB queries as dict methods
- No additional network calls
- No caching layer (Redis handles that separately)

### When to Use Dict vs Model

**Use Models When**
- You have defined Pydantic models for your data
- You want type safety and validation
- You want IDE autocomplete

**Use Dicts When**
- Quick scripts or prototypes
- Dynamic data structures
- No validation needed

## 13. Security Considerations

### No New Security Concerns

- Pydantic validation provides additional safety (validates data types)
- Same MongoDB authentication as existing service
- No new attack vectors introduced
- model_dump() excludes private fields by default (Pydantic behavior)

### Potential Security Benefits

- Type validation prevents some injection attacks
- Schema validation catches malformed data
- Structured models enforce data contracts

## 14. Documentation Requirements

### Code Documentation

- Docstrings for all 6 new methods
- Follow existing MongoService docstring format
- Include Args, Returns, Raises, Example sections
- Reference Pydantic ValidationError in raises

### Usage Examples

```python
from pydantic import BaseModel
from lvrgd.common.services.mongodb import MongoService

class UserModel(BaseModel):
    name: str
    age: int
    email: str

# Find one
user = mongo_service.find_one_model("users", {"email": "john@example.com"}, UserModel)

# Insert one
new_user = UserModel(name="Jane", age=25, email="jane@example.com")
result = mongo_service.insert_one_model("users", new_user)

# Find many
active_users = mongo_service.find_many_models(
    "users",
    {"status": "active"},
    UserModel,
    limit=10
)

# Insert many
users = [UserModel(...), UserModel(...)]
result = mongo_service.insert_many_models("users", users)

# Update one
updated_data = UserModel(name="John Updated", age=31, email="john@example.com")
result = mongo_service.update_one_model(
    "users",
    {"email": "john@example.com"},
    updated_data
)

# With transactions
with mongo_service.transaction() as session:
    mongo_service.insert_one_model("users", user, session=session)
    mongo_service.update_one_model("stats", {"_id": 1}, stats, session=session)
```

## 15. Next Steps

### Implementation Sequence

1. **Add TypeVar import** to mongodb_service.py
2. **Implement find_one_model** (simplest - good starting point)
3. **Add tests for find_one_model** (verify pattern works)
4. **Implement insert_one_model** (serialization)
5. **Add tests for insert_one_model**
6. **Implement find_many_models** (list handling)
7. **Add tests for find_many_models**
8. **Implement insert_many_models** (bulk serialization)
9. **Add tests for insert_many_models**
10. **Implement update_one_model** ($set operation)
11. **Add tests for update_one_model**
12. **Implement update_many_models** (bulk updates)
13. **Add tests for update_many_models**
14. **Run ruff check** - ensure zero violations
15. **Run ruff format** - ensure consistent formatting
16. **Run all tests** - verify backward compatibility
17. **Update integration tests** (if needed)

### Task Generation

Use constitution-task-generator to create detailed tasks:
```bash
# Generate implementation tasks from this spec
constitution-task-generator specs/work-20251108-130130/work-spec.md
```

### Execution

Use constitution-task-executor to implement:
```bash
# Execute tasks with constitutional enforcement
constitution-task-executor specs/work-20251108-130130/tasks/
```

---

**Constitutional Compliance Summary**

This specification enforces all 7 constitutional principles:

I. **Radical Simplicity** - Each method is 3-5 lines, delegates to existing methods
II. **Fail Fast** - ValidationError and MongoDB errors propagate without catching
III. **Type Safety** - TypeVar[T] for generic model support, full type hints
IV. **Structured Data** - Pydantic BaseModel required for all new methods
V. **Unit Testing** - Mock MongoDB client, test validation, follow existing patterns
VI. **Dependency Injection** - No new dependencies, existing DI pattern maintained
VII. **SOLID Principles** - Open/Closed extension, Single Responsibility per method

**No constitutional violations identified. Implementation can proceed.**
