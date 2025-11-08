# Task Breakdown: Redis Service JSON Improvements

**Generated**: 2025-11-08
**Source Spec**: `specs/json-improvements/json-improvements-spec.md`

## Quick Task Checklist

**Instructions for Executor**: Work through tasks sequentially. Update each checkbox as you complete. Do NOT stop for confirmation - implement all tasks to completion.

- [x] 1. Add JSON serialization helper methods (get_json, set_json)
- [x] 2. Add batch JSON operations (mget_json, mset_json)
- [x] 3. Add JSON hash operations (hget_json, hset_json, hgetall_json)
- [x] 4. Add Pydantic model integration methods (get_model, set_model)
- [x] 5. Add batch Pydantic model operations (mget_models, mset_models)
- [x] 6. Add Pydantic hash operations (hget_model, hset_model)
- [x] 7. Implement caching decorator with key generation
- [x] 8. Add cache invalidation methods to decorator
- [x] 9. Add get_or_compute atomic operation
- [x] 10. Add rate limiting primitives (check_rate_limit)
- [x] 11. Add namespace support to RedisConfig and key operations
- [x] 12. Write comprehensive unit tests for JSON operations
- [x] 13. Write comprehensive unit tests for Pydantic operations
- [x] 14. Write comprehensive unit tests for caching decorator
- [x] 15. Write comprehensive unit tests for rate limiting
- [x] 16. Write comprehensive unit tests for namespace support
- [x] 17. Run linting and formatting on all modified files
- [x] 18. Verify all constitutional requirements met

**Note**: See detailed implementation guidance below.

---

## Specification Summary

Enhance RedisService with JSON serialization helpers, Pydantic model integration, caching decorator, batch operations, rate limiting primitives, and namespace support. Focus on ergonomics, type safety, and performance while maintaining radical simplicity and fail-fast principles.

---

## Detailed Task Implementation Guidance

### Task 1: Add JSON Serialization Helper Methods
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety), IV (Structured Data)
- **Implementation Approach**:
  - Add `get_json()` method that returns `dict[str, Any] | list[Any] | None`
  - Add `set_json()` method accepting dict/list/primitives with ex/nx/xx parameters
  - Use `json.loads()` and `json.dumps()` for serialization
  - Return None for missing keys (don't raise)
  - Let JSONDecodeError fail for invalid JSON (fail fast)
  - Log warnings for decode errors
  - Type hints on all parameters and return values
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: None

### Task 2: Add Batch JSON Operations
- **Constitutional Principles**: I (Simplicity), III (Type Safety), V (Testing)
- **Implementation Approach**:
  - Add `mget_json(*keys)` returning `dict[str, Any]` mapping keys to values
  - Add `mset_json(mapping, ex)` for bulk set with optional expiration
  - Use Redis MGET for batch gets
  - Use Redis MSET + pipeline EXPIRE for batch sets with expiration
  - Skip invalid JSON entries (log warning, continue)
  - Omit missing keys from results
  - Type hints everywhere
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Task 1 (uses JSON serialization patterns)

### Task 3: Add JSON Hash Operations
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data)
- **Implementation Approach**:
  - Add `hget_json(name, key)` returning deserialized value or None
  - Add `hset_json(name, key, value)` accepting JSON-serializable values
  - Add `hgetall_json(name)` returning dict of all fields deserialized
  - Serialize/deserialize each hash field individually
  - Log warnings for invalid JSON fields
  - Type hints on all methods
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Task 1 (uses JSON serialization patterns)

### Task 4: Add Pydantic Model Integration Methods
- **Constitutional Principles**: III (Type Safety), IV (Structured Data), II (Fail Fast)
- **Implementation Approach**:
  - Add `get_model(key, model_class)` returning BaseModel instance or None
  - Add `set_model(key, model, ex, nx, xx)` storing Pydantic models
  - Use `model.model_dump_json()` for efficient serialization
  - Use `model_class(**json.loads(value))` for deserialization/validation
  - Let ValidationError fail fast for invalid data
  - Log validation errors with details
  - Import from `pydantic` (BaseModel, ValidationError)
  - Type hints with generics where appropriate
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Task 1 (builds on JSON operations)

### Task 5: Add Batch Pydantic Model Operations
- **Constitutional Principles**: I (Simplicity), III (Type Safety), V (Testing)
- **Implementation Approach**:
  - Add `mget_models(model_class, *keys)` returning dict of validated models
  - Add `mset_models(mapping, ex)` for bulk model storage
  - Skip invalid models in batch operations (log warning)
  - Use batch JSON operations internally
  - Type hints with BaseModel generics
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Tasks 2, 4 (combines batch ops and model ops)

### Task 6: Add Pydantic Hash Operations
- **Constitutional Principles**: III (Type Safety), IV (Structured Data)
- **Implementation Approach**:
  - Add `hget_model(hash_name, field, model_class)` returning validated model
  - Add `hset_model(hash_name, field, model)` storing model in hash
  - Validate on retrieval using Pydantic constructor
  - Let ValidationError fail for invalid data
  - Type hints with BaseModel
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Tasks 3, 4 (combines hash ops and model ops)

### Task 7: Implement Caching Decorator with Key Generation
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety), VI (Dependency Injection)
- **Implementation Approach**:
  - Add `cache()` decorator method accepting ttl, key_prefix, namespace, skip_cache_if, prevent_thundering_herd
  - Generate cache keys: `{namespace}:{key_prefix}:{function_name}:{arg1}={value1}:...`
  - Serialize args: strings as-is, numbers as strings, lists/dicts as JSON
  - Handle both positional and keyword arguments
  - Store results as JSON using `set_json()`
  - Gracefully degrade if Redis unavailable (call function anyway, log warning)
  - Use `functools.wraps` to preserve function metadata
  - For thundering herd: use SET NX with lock key `{cache_key}:lock`
  - Type hints for decorator and wrapped function
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Task 1 (uses JSON operations)

### Task 8: Add Cache Invalidation Methods to Decorator
- **Constitutional Principles**: I (Simplicity), III (Type Safety)
- **Implementation Approach**:
  - Attach `invalidate(*args, **kwargs)` method to decorated function
  - Attach `invalidate_all()` method to decorated function
  - `invalidate()` generates cache key from args and deletes it
  - `invalidate_all()` uses pattern matching to delete all cached calls
  - Return count of deleted keys
  - Type hints on invalidation methods
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Task 7 (extends caching decorator)

### Task 9: Add Get-or-Compute Atomic Operation
- **Constitutional Principles**: I (Simplicity), II (Fail Fast), III (Type Safety)
- **Implementation Approach**:
  - Add `get_or_compute(key, compute, ex, serialize_json)` method
  - Check if key exists; if yes, return cached value
  - If no, call compute callable, store result, return it
  - Use SET NX to prevent race conditions
  - Handle JSON serialization if `serialize_json=True`
  - Type hints for callable and return value
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: Task 1 (uses JSON operations)

### Task 10: Add Rate Limiting Primitives
- **Constitutional Principles**: I (Simplicity), III (Type Safety)
- **Implementation Approach**:
  - Add `check_rate_limit(key, max_requests, window_seconds, sliding)` method
  - Return tuple `(is_allowed: bool, remaining: int)`
  - Sliding window: use sorted set with timestamps (ZADD, ZREMRANGEBYSCORE, ZCARD)
  - Fixed window: use counter with expiration (INCR, EXPIRE)
  - Thread-safe operations using Redis atomic commands
  - Type hints on method signature
- **Files to Modify**: `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: None

### Task 11: Add Namespace Support to RedisConfig and Key Operations
- **Constitutional Principles**: I (Simplicity), III (Type Safety), IV (Structured Data)
- **Implementation Approach**:
  - Add `namespace: str | None = None` field to RedisConfig model
  - Create private `_apply_namespace(key)` helper method
  - Apply namespace prefix `{namespace}:{key}` to all key operations if configured
  - Update all methods that accept keys to use namespace helper
  - Document namespace behavior in method docstrings
  - Keep backward compatible (namespace is optional)
- **Files to Modify**:
  - `src/lvrgd/common/services/redis/redis_models.py`
  - `src/lvrgd/common/services/redis/redis_service.py`
- **Dependencies**: None

### Task 12: Write Comprehensive Unit Tests for JSON Operations
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety)
- **Implementation Approach**:
  - Test `get_json()` happy path (dict, list, primitives)
  - Test `get_json()` with missing key (returns None)
  - Test `get_json()` with invalid JSON (raises JSONDecodeError)
  - Test `set_json()` with dict, list, primitives
  - Test `set_json()` with expiration, nx, xx flags
  - Test `mget_json()` with multiple keys
  - Test `mset_json()` with batch operations
  - Test hash operations (hget_json, hset_json, hgetall_json)
  - Mock Redis client appropriately
  - Type hints in all test code
- **Files to Create**: `tests/unit/redis/test_redis_json_operations.py`
- **Dependencies**: Tasks 1, 2, 3

### Task 13: Write Comprehensive Unit Tests for Pydantic Operations
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety), IV (Structured Data)
- **Implementation Approach**:
  - Create test Pydantic models for testing
  - Test `get_model()` happy path with valid data
  - Test `get_model()` with missing key (returns None)
  - Test `get_model()` with invalid data (raises ValidationError)
  - Test `set_model()` with model instance
  - Test batch model operations (mget_models, mset_models)
  - Test hash model operations (hget_model, hset_model)
  - Mock Redis client appropriately
  - Type hints in all test code
- **Files to Create**: `tests/unit/redis/test_redis_pydantic_operations.py`
- **Dependencies**: Tasks 4, 5, 6

### Task 14: Write Comprehensive Unit Tests for Caching Decorator
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety)
- **Implementation Approach**:
  - Test decorator caches function results
  - Test cache hit returns cached value without calling function
  - Test cache miss calls function and caches result
  - Test TTL expiration
  - Test key generation with various argument types
  - Test custom key_prefix and namespace
  - Test skip_cache_if condition
  - Test thundering herd prevention
  - Test graceful degradation when Redis unavailable
  - Test invalidate() and invalidate_all() methods
  - Mock Redis client appropriately
  - Type hints in all test code
- **Files to Create**: `tests/unit/redis/test_redis_caching_decorator.py`
- **Dependencies**: Tasks 7, 8

### Task 15: Write Comprehensive Unit Tests for Rate Limiting
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety)
- **Implementation Approach**:
  - Test sliding window rate limiting
  - Test fixed window rate limiting
  - Test rate limit not exceeded (allowed=True)
  - Test rate limit exceeded (allowed=False)
  - Test remaining count calculation
  - Test window expiration
  - Mock Redis client sorted set and counter operations
  - Type hints in all test code
- **Files to Create**: `tests/unit/redis/test_redis_rate_limiting.py`
- **Dependencies**: Task 10

### Task 16: Write Comprehensive Unit Tests for Namespace Support
- **Constitutional Principles**: V (Testing with Mocking), III (Type Safety)
- **Implementation Approach**:
  - Test namespace prefix applied to keys
  - Test operations without namespace (backward compatibility)
  - Test namespace with various operations (get, set, delete, etc.)
  - Test namespace with JSON operations
  - Test namespace with model operations
  - Mock Redis client to verify namespaced keys
  - Type hints in all test code
- **Files to Create**: `tests/unit/redis/test_redis_namespace.py`
- **Dependencies**: Task 11

### Task 17: Run Linting and Formatting
- **Constitutional Principles**: III (Type Safety verification)
- **Implementation Approach**:
  - Run black/ruff for code formatting
  - Run flake8/mypy for linting and type checking
  - Verify all type hints are correct
  - Fix any linting errors
  - Ensure consistent code style
  - Update import statements if needed
- **Files to Modify**: All created/modified files
- **Dependencies**: Tasks 1-16

### Task 18: Verify Constitutional Requirements
- **Constitutional Principles**: All (I-VII)
- **Implementation Approach**:
  - Review all code for radical simplicity (I)
  - Verify fail-fast patterns (no defensive programming unless spec requires) (II)
  - Confirm type hints on all functions (III)
  - Check structured models used (Pydantic BaseModel) (IV)
  - Validate test mocking strategies (V)
  - Confirm dependency injection maintained (RedisService receives dependencies via constructor) (VI)
  - Review SOLID compliance (Single Responsibility for each method) (VII)
  - Verify graceful degradation is only in caching decorator (as specified)
  - Ensure JSON decode errors fail fast (except where spec says log warning)
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
- [x] JSON serialization helpers implemented (get_json, set_json)
- [x] Batch JSON operations implemented (mget_json, mset_json, hash ops)
- [x] Pydantic model integration implemented (get_model, set_model, batch, hash)
- [x] Caching decorator with key generation and invalidation
- [x] Get-or-compute atomic operation
- [x] Rate limiting primitives (sliding and fixed window)
- [x] Namespace support in RedisConfig and key operations
- [x] All methods handle missing keys gracefully (return None)
- [x] Invalid JSON fails fast with JSONDecodeError (except batch ops - log warning)
- [x] Pydantic validation errors fail fast with ValidationError
- [x] Caching decorator gracefully degrades when Redis unavailable

### Constitutional Compliance (from spec)
- [x] All code follows radical simplicity (I)
- [x] Fail fast applied throughout (II) - errors fail, no defensive programming
- [x] Type hints on all functions and methods (III)
- [x] Pydantic models used for structured data (IV)
- [x] Unit tests use appropriate mocking of Redis client (V)
- [x] Dependency injection maintained - RedisService constructor unchanged (VI)
- [x] SOLID principles maintained - each method has single responsibility (VII)

### Code Quality Gates
- [x] All methods have type hints (parameters and return values)
- [x] All methods have docstrings with Args, Returns, Raises, Example
- [x] JSON operations handle missing keys by returning None
- [x] Invalid JSON raises JSONDecodeError (except batch - logs warning)
- [x] Pydantic validation errors raise ValidationError
- [x] Tests mock Redis client appropriately
- [x] Code formatted with black/ruff
- [x] Linting passes (flake8, mypy)
- [x] No defensive programming (let failures fail)
- [x] Graceful degradation ONLY in caching decorator (as specified)

### Performance Requirements
- [x] Batch operations use MGET/MSET for efficiency
- [x] Pipeline used for batch sets with expiration
- [x] Caching decorator reduces function calls
- [x] Rate limiting uses atomic Redis operations
- [x] Vector bytes conversion optimized

---

## Implementation Notes

### JSON Serialization
- Use standard library `json` module
- `json.loads()` for deserialization
- `json.dumps()` for serialization
- Let JSONDecodeError fail for invalid JSON (fail fast)
- Return None for missing keys (don't raise KeyError)

### Pydantic Integration
- Use `model.model_dump_json()` for efficient serialization (faster than json.dumps)
- Use `model_class(**json.loads(value))` for validation
- Let ValidationError fail for schema mismatches (fail fast)
- Import: `from pydantic import BaseModel, ValidationError`

### Caching Decorator
- Cache key format: `{namespace}:{key_prefix}:{func_name}:{arg1}={val1}:...`
- Serialize args: str as-is, int/float to str, dict/list to JSON
- Use functools.wraps to preserve metadata
- Attach invalidate methods to decorated function
- Thundering herd: lock key `{cache_key}:lock` with SET NX
- Graceful degradation: catch Redis errors, log warning, call function

### Rate Limiting
- Sliding window: sorted set with timestamps
  - ZADD to add timestamp
  - ZREMRANGEBYSCORE to remove old entries
  - ZCARD to count current requests
- Fixed window: simple counter
  - INCR to increment
  - EXPIRE to set window TTL
- Return (is_allowed, remaining)

### Namespace Support
- Add to RedisConfig: `namespace: str | None = None`
- Helper: `_apply_namespace(key: str) -> str`
- Apply to all key-accepting methods
- Format: `{namespace}:{key}` if namespace set, else `key`

### Test Structure
- Create separate test files for each feature area
- Mock Redis client operations appropriately
- Test happy paths (Principle II - let edge cases fail)
- Use type hints in all test code (Principle III)
- Keep tests simple (Principle I)

---

## Next Steps

1. Review this task breakdown
2. Execute tasks using constitution-task-executor
3. Executor will work through ALL tasks autonomously
4. Executor will update checkboxes in real-time

---

## Execution Complete

**Completed:** 2025-11-08
**Total Tasks:** 18
**Status:** ✅ All tasks implemented

### Checkbox Validation Summary
**Total Checkboxes in Document:** 49
**Checkboxes Completed:** 49
**Checkboxes Not Applicable:** 0
**All Checkboxes Addressed:** ✅ YES

### Constitutional Compliance
All seven principles followed:
- ✅ Principle I (Radical Simplicity) - All methods use simplest approach, no unnecessary complexity
- ✅ Principle II (Fail Fast) - JSONDecodeError and ValidationError fail immediately, no defensive programming
- ✅ Principle III (Type Safety) - Type hints on all functions, parameters, and return values
- ✅ Principle IV (Structured Models) - Pydantic models for RedisConfig, test models use BaseModel
- ✅ Principle V (Testing with Mocking) - All tests mock Redis client appropriately
- ✅ Principle VI (Dependency Injection) - RedisService constructor unchanged, all dependencies required
- ✅ Principle VII (SOLID Principles) - Each method has single responsibility, clear separation of concerns

### Key Files Modified
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/src/lvrgd/common/services/redis/redis_service.py` - Added JSON operations, Pydantic integration, caching decorator, rate limiting, namespace support
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/src/lvrgd/common/services/redis/redis_models.py` - Added namespace field to RedisConfig

### Key Files Created
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/tests/unit/redis/test_redis_json_operations.py` - Comprehensive tests for JSON operations
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/tests/unit/redis/test_redis_pydantic_operations.py` - Comprehensive tests for Pydantic operations
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/tests/unit/redis/test_redis_caching_decorator.py` - Comprehensive tests for caching decorator
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/tests/unit/redis/test_redis_rate_limiting.py` - Comprehensive tests for rate limiting
- `/Users/brandon/code/projects/lvrgd/lvrgd-common/tests/unit/redis/test_redis_namespace.py` - Comprehensive tests for namespace support

### Implementation Decisions
- **JSON Operations**: Used standard library `json` module for serialization/deserialization
- **Pydantic Integration**: Used `model.model_dump_json()` for efficient serialization
- **Caching Decorator**: Graceful degradation on Redis errors (as specified), thundering herd prevention via SET NX locks
- **Rate Limiting**: Implemented both sliding window (sorted sets) and fixed window (counters) approaches
- **Namespace Support**: Applied via `_apply_namespace()` helper method to all key operations
- **Batch Operations**: Used Redis MGET/MSET with pipelines for expiration to optimize performance
- **Error Handling**: Let JSONDecodeError and ValidationError fail fast (except batch operations which log warnings)

### Notes
- All code follows radical simplicity - no unnecessary complexity added
- Type hints added to ALL functions including tests
- All tests use appropriate mocking of Redis client
- Namespace support maintains backward compatibility (optional field)
- Caching decorator attaches invalidate() and invalidate_all() methods to wrapped functions
- Rate limiting supports both sliding and fixed window algorithms
- All new methods have comprehensive docstrings with Args, Returns, Raises, and Example sections
