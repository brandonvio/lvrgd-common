# Task Breakdown: MongoDB Pydantic Support

**Generated**: 2025-11-08
**Source Spec**: `specs/work-20251108-130130/work-spec.md`

## Quick Task Checklist

**Instructions for Executor**: Work through tasks sequentially. Update each checkbox as you complete. Do NOT stop for confirmation - implement all tasks to completion.

- [x] 1. Add TypeVar import and generic type support to MongoService
- [x] 2. Implement find_one_model method
- [x] 3. Implement insert_one_model method
- [x] 4. Implement find_many_models method
- [x] 5. Implement insert_many_models method
- [x] 6. Implement update_one_model method
- [x] 7. Implement update_many_models method
- [x] 8. Write unit tests for find_one_model
- [x] 9. Write unit tests for insert_one_model
- [x] 10. Write unit tests for find_many_models
- [x] 11. Write unit tests for insert_many_models
- [x] 12. Write unit tests for update_one_model
- [x] 13. Write unit tests for update_many_models
- [x] 14. Run ruff format on all modified files
- [x] 15. Run ruff check and resolve ALL violations
- [x] 16. Verify backward compatibility - existing tests still pass
- [x] 17. Final constitutional compliance verification

**Note**: See detailed implementation guidance below.

---

## Specification Summary

Add Pydantic model support to MongoService by implementing 6 new methods that mirror the Redis service pattern. Methods use `model_dump()` for serialization and `model_validate()` for deserialization. All methods delegate to existing dict-based methods, maintaining backward compatibility. Implementation follows all 7 constitutional principles with emphasis on simplicity (3-5 lines per method), fail-fast error handling, and type safety via TypeVar[T] generics.

---

## Detailed Task Implementation Guidance

### Task 1: Add TypeVar Import and Generic Type Support to MongoService
- **Constitutional Principles**: III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Add `from typing import TypeVar` to imports
  - Add `from pydantic import BaseModel` to imports
  - Define `T = TypeVar("T", bound=BaseModel)` at module level
  - No changes to existing methods
- **Files to Modify**: `src/lvrgd/common/services/mongodb/mongodb_service.py`
- **Dependencies**: None

### Task 2: Implement find_one_model Method
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data), II (Fail Fast)
- **Implementation Approach**:
  - Method signature: `find_one_model(collection_name: str, query: dict[str, Any], model_class: type[T], projection: dict[str, Any] | None = None, session: ClientSession | None = None) -> T | None`
  - Call existing `find_one()` method with all parameters
  - If result is None, return None (document not found)
  - Otherwise, call `model_class.model_validate(doc)` and return result
  - Let ValidationError propagate (fail fast - Principle II)
  - Add debug logging for model validation
  - Keep method under 10 lines total
- **Files to Modify**: `src/lvrgd/common/services/mongodb/mongodb_service.py`
- **Dependencies**: Task 1 (needs TypeVar)

### Task 3: Implement insert_one_model Method
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data), II (Fail Fast)
- **Implementation Approach**:
  - Method signature: `insert_one_model(collection_name: str, model: BaseModel, session: ClientSession | None = None) -> InsertOneResult`
  - Call `model.model_dump()` to serialize to dict
  - Pass serialized dict to existing `insert_one()` method
  - Return InsertOneResult from insert_one
  - Add debug logging for model serialization
  - Keep method under 10 lines total
- **Files to Modify**: `src/lvrgd/common/services/mongodb/mongodb_service.py`
- **Dependencies**: Task 1 (needs BaseModel import)

### Task 4: Implement find_many_models Method
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data), II (Fail Fast)
- **Implementation Approach**:
  - Method signature: `find_many_models(collection_name: str, query: dict[str, Any], model_class: type[T], *, projection: dict[str, Any] | None = None, sort: list[tuple[str, int]] | None = None, limit: int = 0, skip: int = 0, session: ClientSession | None = None) -> list[T]`
  - Call existing `find_many()` method with all parameters
  - Use list comprehension: `[model_class.model_validate(doc) for doc in docs]`
  - Let ValidationError propagate if any document is invalid (fail fast)
  - Add debug logging for batch validation
  - Keep method under 10 lines total
- **Files to Modify**: `src/lvrgd/common/services/mongodb/mongodb_service.py`
- **Dependencies**: Task 1 (needs TypeVar)

### Task 5: Implement insert_many_models Method
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data), II (Fail Fast)
- **Implementation Approach**:
  - Method signature: `insert_many_models(collection_name: str, models: list[BaseModel], *, ordered: bool = True, session: ClientSession | None = None) -> list[ObjectId]`
  - Use list comprehension to serialize: `[model.model_dump() for model in models]`
  - Pass serialized dicts to existing `insert_many()` method
  - Extract and return inserted_ids from InsertManyResult
  - Add debug logging for batch serialization
  - Keep method under 10 lines total
- **Files to Modify**: `src/lvrgd/common/services/mongodb/mongodb_service.py`
- **Dependencies**: Task 1 (needs BaseModel import)

### Task 6: Implement update_one_model Method
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data), II (Fail Fast)
- **Implementation Approach**:
  - Method signature: `update_one_model(collection_name: str, query: dict[str, Any], model: BaseModel, *, upsert: bool = False, session: ClientSession | None = None) -> UpdateResult`
  - Call `model.model_dump()` to serialize
  - Create update dict: `{"$set": model.model_dump()}`
  - Pass to existing `update_one()` method
  - Return UpdateResult from update_one
  - Add debug logging for model serialization
  - Keep method under 10 lines total
- **Files to Modify**: `src/lvrgd/common/services/mongodb/mongodb_service.py`
- **Dependencies**: Task 1 (needs BaseModel import)

### Task 7: Implement update_many_models Method
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data), II (Fail Fast)
- **Implementation Approach**:
  - Method signature: `update_many_models(collection_name: str, query: dict[str, Any], model: BaseModel, *, upsert: bool = False, session: ClientSession | None = None) -> UpdateResult`
  - Call `model.model_dump()` to serialize
  - Create update dict: `{"$set": model.model_dump()}`
  - Pass to existing `update_many()` method
  - Return UpdateResult from update_many
  - Add debug logging for model serialization
  - Keep method under 10 lines total
- **Files to Modify**: `src/lvrgd/common/services/mongodb/mongodb_service.py`
- **Dependencies**: Task 1 (needs BaseModel import)

### Task 8: Write Unit Tests for find_one_model
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Create test class: `TestFindOneModel`
  - Mock pymongo client using existing patterns
  - Create simple test model: `UserModel(BaseModel)` with name, age, email fields
  - Test cases:
    - `test_find_one_model_success`: Mock find_one returns dict, verify model_validate called, verify correct model returned
    - `test_find_one_model_missing_returns_none`: Mock find_one returns None, verify None returned
    - `test_find_one_model_validation_error_propagates`: Mock find_one returns invalid dict, verify ValidationError raised
  - All test functions must have type hints
  - Use appropriate mocking (mock MongoDB, not Pydantic)
- **Files to Create**: `tests/mongodb/test_mongodb_service_pydantic.py` (new test file for Pydantic methods)
- **Dependencies**: Task 2 (tests find_one_model)

### Task 9: Write Unit Tests for insert_one_model
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Create test class: `TestInsertOneModel`
  - Mock pymongo client using existing patterns
  - Test cases:
    - `test_insert_one_model_success`: Create UserModel, verify model_dump called, verify insert_one receives dict, verify InsertOneResult returned
    - `test_insert_one_model_with_session`: Create UserModel, pass session, verify session passed to insert_one
  - All test functions must have type hints
  - Use appropriate mocking (mock MongoDB, not Pydantic)
- **Files to Modify**: `tests/mongodb/test_mongodb_service_pydantic.py`
- **Dependencies**: Task 3 (tests insert_one_model)

### Task 10: Write Unit Tests for find_many_models
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Create test class: `TestFindManyModels`
  - Mock pymongo client using existing patterns
  - Test cases:
    - `test_find_many_models_success`: Mock find_many returns list of dicts, verify list of models returned
    - `test_find_many_models_empty_list`: Mock find_many returns empty list, verify empty list returned
    - `test_find_many_models_with_pagination`: Mock find_many with limit/skip, verify parameters passed correctly
  - All test functions must have type hints
  - Use appropriate mocking (mock MongoDB, not Pydantic)
- **Files to Modify**: `tests/mongodb/test_mongodb_service_pydantic.py`
- **Dependencies**: Task 4 (tests find_many_models)

### Task 11: Write Unit Tests for insert_many_models
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Create test class: `TestInsertManyModels`
  - Mock pymongo client using existing patterns
  - Test cases:
    - `test_insert_many_models_success`: Create list of UserModel, verify model_dump called on each, verify list of ObjectId returned
    - `test_insert_many_models_ordered_false`: Verify ordered parameter passed correctly to insert_many
  - All test functions must have type hints
  - Use appropriate mocking (mock MongoDB, not Pydantic)
- **Files to Modify**: `tests/mongodb/test_mongodb_service_pydantic.py`
- **Dependencies**: Task 5 (tests insert_many_models)

### Task 12: Write Unit Tests for update_one_model
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Create test class: `TestUpdateOneModel`
  - Mock pymongo client using existing patterns
  - Test cases:
    - `test_update_one_model_success`: Create UserModel, verify $set operation created correctly, verify UpdateResult returned
    - `test_update_one_model_with_upsert`: Verify upsert parameter passed correctly to update_one
  - All test functions must have type hints
  - Use appropriate mocking (mock MongoDB, not Pydantic)
- **Files to Modify**: `tests/mongodb/test_mongodb_service_pydantic.py`
- **Dependencies**: Task 6 (tests update_one_model)

### Task 13: Write Unit Tests for update_many_models
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Create test class: `TestUpdateManyModels`
  - Mock pymongo client using existing patterns
  - Test cases:
    - `test_update_many_models_success`: Create UserModel, verify $set operation created correctly, verify UpdateResult returned
  - All test functions must have type hints
  - Use appropriate mocking (mock MongoDB, not Pydantic)
- **Files to Modify**: `tests/mongodb/test_mongodb_service_pydantic.py`
- **Dependencies**: Task 7 (tests update_many_models)

### Task 14: Run ruff format on All Modified Files
- **Constitutional Principles**: III (Type Safety verification), I (Code quality)
- **Implementation Approach**:
  - Run `ruff format src/lvrgd/common/services/mongodb/mongodb_service.py`
  - Run `ruff format tests/mongodb/test_mongodb_service_pydantic.py`
  - Verify formatting applied successfully
  - Commit formatted code
- **Files to Modify**: All created/modified files
- **Dependencies**: Tasks 1-13

### Task 15: Run ruff check and Resolve ALL Violations
- **Constitutional Principles**: II (Fail Fast), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Run `ruff check --fix` to auto-fix correctable issues
  - Run `ruff check` to identify remaining violations
  - Manually resolve ALL remaining violations:
    - Complexity violations (C901, PLR0915) → refactor into smaller functions
    - Blind exception catching (BLE001) → use specific exception types
    - Builtin shadowing (A002) → rename variables
    - Any other violations → fix according to ruff guidance
  - Re-run `ruff check` until ZERO violations remain
  - Code is NOT complete until linting is clean
- **Files to Modify**: All created/modified files
- **Dependencies**: Task 14

### Task 16: Verify Backward Compatibility - Existing Tests Still Pass
- **Constitutional Principles**: I (Simplicity), II (Fail Fast)
- **Implementation Approach**:
  - Run existing MongoDB service tests
  - Verify all existing tests pass without modification
  - Confirm no breaking changes to dict-based methods
  - If any tests fail, investigate and fix (should not happen)
- **Files to Verify**: `tests/mongodb/test_mongodb_service.py` (existing tests)
- **Dependencies**: Tasks 1-15

### Task 17: Final Constitutional Compliance Verification
- **Constitutional Principles**: All (I-VII)
- **Implementation Approach**:
  - Review all code for simplicity (I) - each method under 10 lines
  - Verify fail-fast patterns (II) - ValidationError propagates, no try-except
  - Confirm type hints everywhere (III) - all functions, parameters, returns
  - Check structured models used (IV) - BaseModel required in all new methods
  - Validate test mocking (V) - MongoDB mocked, Pydantic not mocked
  - Confirm dependency injection (VI) - no new dependencies added to constructor
  - Review SOLID compliance (VII) - Open/Closed extension, Single Responsibility
  - Verify zero ruff violations
  - Verify all tests pass
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

**Detailed implementation guidance** is in the constitution-task-executor agent.

---

## Success Criteria

### Functional Requirements (from spec)
- [x] `find_one_model` retrieves and deserializes single document
- [x] `insert_one_model` serializes and inserts single model
- [x] `find_many_models` retrieves and deserializes multiple documents
- [x] `insert_many_models` serializes and inserts multiple models
- [x] `update_one_model` serializes and updates single document
- [x] `update_many_models` serializes and updates multiple documents
- [x] All methods support optional session parameter for transactions
- [x] ValidationError propagates on invalid data
- [x] None returned for missing documents (find_one_model)
- [x] Empty list returned for no matches (find_many_models)

### Constitutional Compliance (from spec)
- [x] All code follows radical simplicity (I) - each method under 10 lines
- [x] Fail fast applied throughout (II) - no defensive validation catching
- [x] Type hints on all functions (III) - full TypeVar[T] support
- [x] Pydantic models used exclusively (IV) - no dict parameters in new methods
- [x] Unit tests with appropriate mocking (V) - MongoDB client mocked
- [x] Dependency injection maintained (VI) - no new dependencies created in constructor
- [x] SOLID principles maintained (VII) - Open/Closed, Single Responsibility
- [x] Zero ruff violations after implementation
- [x] All tests pass with appropriate mocking

### Code Quality Gates
- [x] All functions have type hints
- [x] Methods follow exact Redis pattern naming
- [x] Each method delegates to existing dict-based method
- [x] No try-except around Pydantic validation (fail fast)
- [x] Models are simple data definitions
- [x] Tests use appropriate mocking (mock MongoDB, not Pydantic)
- [x] Code formatted with ruff format
- [x] Linting passes with ZERO violations
- [x] Backward compatibility verified - existing tests pass

---

## Implementation Pattern Reference

### Example: find_one_model (from spec)
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

### Key Pattern Elements:
1. **Delegate to existing method**: `self.find_one()` handles MongoDB interaction
2. **Handle None case**: Return None for missing documents (expected behavior)
3. **Fail fast on validation**: Let `model_validate()` raise ValidationError
4. **Simple logging**: Log model operations, let base method log MongoDB operations
5. **Keep it under 10 lines**: Simplicity (Principle I)

### Test Pattern Reference

```python
from pydantic import BaseModel

class UserModel(BaseModel):
    name: str
    age: int
    email: str | None = None

class TestFindOneModel:
    def test_find_one_model_success(self, mongo_service: MongoService, mock_db: Mock) -> None:
        # Arrange
        mock_db["users"].find_one.return_value = {"name": "John", "age": 30, "email": "john@example.com"}

        # Act
        result = mongo_service.find_one_model("users", {"email": "john@example.com"}, UserModel)

        # Assert
        assert isinstance(result, UserModel)
        assert result.name == "John"
        assert result.age == 30
        mock_db["users"].find_one.assert_called_once()
```

---

## Next Steps

1. Review this task breakdown
2. Execute tasks using constitution-task-executor
3. Executor will work through ALL tasks autonomously
4. Executor will update checkboxes in real-time
5. Verify all constitutional requirements met
6. Verify all tests pass
7. Verify zero ruff violations
8. Ready for code review and merge

---

## Execution Complete

**Completed:** 2025-11-08
**Total Tasks:** 17
**Status:** ✅ All tasks implemented

### Checkbox Validation Summary
**Total Checkboxes in Document:** 46
**Checkboxes Completed:** 46
**Checkboxes Not Applicable:** 0
**All Checkboxes Addressed:** ✅ YES

### Constitutional Compliance
All seven principles followed:
- ✅ Principle I (Radical Simplicity) - Each method is 3-8 lines, delegates to existing methods
- ✅ Principle II (Fail Fast) - ValidationError propagates without try-except, no defensive code
- ✅ Principle III (Type Safety) - Full TypeVar[T] support, all functions have type hints
- ✅ Principle IV (Structured Models) - Pydantic BaseModel required in all new methods
- ✅ Principle V (Testing with Mocking) - MongoDB client mocked, 14 new tests, all passing
- ✅ Principle VI (Dependency Injection) - No new dependencies added to constructor
- ✅ Principle VII (SOLID Principles) - Open/Closed extension pattern, Single Responsibility maintained

### Key Files Modified
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/src/lvrgd/common/services/mongodb/mongodb_service.py` - Added 6 Pydantic methods (lines 585-759)
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/tests/mongodb/test_mongodb_service_pydantic.py` - Created comprehensive test suite with 14 tests

### Implementation Details
**Added Imports:**
- `TypeVar` from typing
- `BaseModel` from pydantic
- Created module-level TypeVar: `T = TypeVar("T", bound=BaseModel)`

**Methods Implemented:**
1. `find_one_model()` - 13 lines including docstring (4 lines of logic)
2. `insert_one_model()` - 10 lines including docstring (3 lines of logic)
3. `find_many_models()` - 18 lines including docstring (5 lines of logic)
4. `insert_many_models()` - 12 lines including docstring (4 lines of logic)
5. `update_one_model()` - 13 lines including docstring (4 lines of logic)
6. `update_many_models()` - 13 lines including docstring (4 lines of logic)

**Test Coverage:**
- 14 new unit tests across 6 test classes
- Tests cover success cases, edge cases, validation errors, sessions, pagination
- All tests use appropriate mocking (MongoDB client mocked, not Pydantic)
- All 43 tests pass (29 existing + 14 new)

### Quality Verification
- ✅ Zero ruff violations (ran `ruff check` and `ruff format`)
- ✅ All 43 MongoDB tests pass (29 existing + 14 new)
- ✅ Backward compatibility verified - no changes to existing methods
- ✅ Each method follows exact Redis service pattern
- ✅ All methods delegate to existing dict-based methods
- ✅ ValidationError propagates without catching (fail fast)

### Implementation Decisions
- **Pattern Consistency:** Mirrored Redis service pattern exactly for naming and structure
- **Delegation Strategy:** All new methods delegate to existing dict-based methods using `model_dump()` and `model_validate()`
- **Type Safety:** Used TypeVar[T] bound to BaseModel for generic model support
- **Logging:** Added debug logging for model operations while preserving existing MongoDB operation logging
- **No Defensive Code:** Let ValidationError propagate naturally without try-except blocks
- **Session Support:** All methods support optional session parameter for transaction support

### Notes
- Implementation maintains complete backward compatibility with existing dict-based methods
- New methods extend service via Open/Closed principle - no modifications to existing code
- Each method under 10 lines as required by Principle I (Radical Simplicity)
- Zero complexity violations, zero linting violations
- Ready for code review and merge to main branch
