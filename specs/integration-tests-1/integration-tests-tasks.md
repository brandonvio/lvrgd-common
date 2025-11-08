# Task Breakdown: Integration Tests for MinIO, MongoDB, and Redis Services

**Generated**: 2025-11-08
**Source Spec**: `specs/integration-tests-1/integration-tests-spec.md`

## Quick Task Checklist

**Instructions for Executor**: Work through tasks sequentially. Update each checkbox as you complete. Do NOT stop for confirmation - implement all tasks to completion.

- [x] 1. Create integration test directory structure
- [x] 2. Add python-dotenv dependency to pyproject.toml
- [x] 3. Create test data Pydantic models
- [x] 4. Implement integration test fixtures in conftest.py
- [x] 5. Implement MinIO integration tests
- [x] 6. Implement MongoDB integration tests
- [x] 7. Implement Redis integration tests
- [x] 8. Run linting and formatting
- [x] 9. Execute integration tests and verify
- [x] 10. Verify all constitutional requirements met

**Note**: See detailed implementation guidance below.

---

## Specification Summary

This task implements integration tests for MinIO, MongoDB, and Redis services. Unlike unit tests that use mocks, these integration tests connect to real service instances using configuration from environment variables. Tests validate end-to-end functionality including connection handling, CRUD operations, and service-specific features like transactions, pipelines, and pub/sub.

---

## Detailed Task Implementation Guidance

### Task 1: Create Integration Test Directory Structure
- **Constitutional Principles**: I (Simplicity), VII (SOLID - Single Responsibility)
- **Implementation Approach**:
  - Create `integration-tests/` directory
  - Add `__init__.py` package marker
  - Keep structure flat - one test file per service
  - Separate from existing unit tests in `tests/`
- **Files to Create**:
  - `integration-tests/__init__.py`
- **Dependencies**: None

### Task 2: Add python-dotenv Dependency to pyproject.toml
- **Constitutional Principles**: I (Simplicity)
- **Implementation Approach**:
  - Add `python-dotenv>=1.0.0` to dev dependency group
  - Required for loading environment variables from `.env` file
  - Keep dependency minimal - only what's needed
- **Files to Modify**:
  - `pyproject.toml`
- **Dependencies**: Task 1

### Task 3: Create Test Data Pydantic Models
- **Constitutional Principles**: IV (Structured Data), III (Type Safety)
- **Implementation Approach**:
  - Create simple Pydantic models for test data
  - TestDocument: name, value, active (for MongoDB/Redis)
  - TestUser: user_id, username, email, age (for Pydantic operations)
  - Models are data definitions only - no business logic
  - Use in integration test files, not separate model file
- **Files to Create**: Models defined in test files
- **Dependencies**: Task 1

### Task 4: Implement Integration Test Fixtures in conftest.py
- **Constitutional Principles**: VI (Dependency Injection), III (Type Safety), I (Simplicity)
- **Implementation Approach**:
  - Create `integration-tests/conftest.py`
  - Load environment variables from `.env` using python-dotenv
  - Create session-scoped logger fixture (LoggingService)
  - Create session-scoped config fixtures (MinioConfig, MongoConfig, RedisConfig)
  - Create module-scoped service fixtures (MinioService, MongoService, RedisService)
  - All dependencies REQUIRED (no Optional, no defaults)
  - Services injected with logger and config
  - Proper cleanup with yield/finally pattern
  - Type hints on all fixtures
- **Files to Create**:
  - `integration-tests/conftest.py`
- **Dependencies**: Tasks 1, 2

### Task 5: Implement MinIO Integration Tests
- **Constitutional Principles**: V (Testing), III (Type Safety), II (Fail Fast), I (Simplicity)
- **Implementation Approach**:
  - Create `TestMinioIntegration` class
  - Type hints on all test functions
  - Test methods (8 total):
    1. test_minio_connection_and_health_check - verify connection, health_check, ping
    2. test_bucket_operations - create, list, verify, cleanup bucket
    3. test_file_upload_download - upload file, download, verify content match
    4. test_data_upload_download - upload bytes, download, verify integrity
    5. test_object_listing - upload multiple with prefix, list filtered
    6. test_object_deletion - upload, verify exists, delete, verify removed
    7. test_presigned_url_generation - upload, generate URL, verify format
    8. test_object_metadata - upload with metadata, retrieve, verify
  - Use fixtures for minio_service
  - Implement proper cleanup in try/finally or fixture teardown
  - Use unique identifiers (uuid) for test resources
  - Fail fast - no fallback logic
  - Keep each test simple and focused
- **Files to Create**:
  - `integration-tests/test_minio_integration.py`
- **Dependencies**: Task 4

### Task 6: Implement MongoDB Integration Tests
- **Constitutional Principles**: V (Testing), III (Type Safety), II (Fail Fast), I (Simplicity)
- **Implementation Approach**:
  - Create `TestMongoDBIntegration` class
  - Type hints on all test functions
  - Test methods (10 total):
    1. test_mongodb_connection_and_ping - verify connection, ping, server info
    2. test_insert_and_find_one - insert document, find, verify content
    3. test_insert_many_and_find_many - batch insert, query multiple
    4. test_update_operations - update_one, update_many, verify results
    5. test_delete_operations - delete_one, delete_many, verify deletion
    6. test_aggregation_pipeline - insert data, run aggregation, verify results
    7. test_transaction_operations - start transaction, multiple ops, commit, test rollback
    8. test_index_creation - create index, verify exists, test unique constraint
    9. test_bulk_operations - bulk write operations, verify results
    10. test_count_documents - insert data, count with query, verify accuracy
  - Use fixtures for mongo_service
  - Use unique collection names (uuid) for isolation
  - Cleanup collections in finally blocks or fixtures
  - Use TestDocument Pydantic model for structured test data
  - Keep tests simple - one operation per test
- **Files to Create**:
  - `integration-tests/test_mongodb_integration.py`
- **Dependencies**: Task 4

### Task 7: Implement Redis Integration Tests
- **Constitutional Principles**: V (Testing), III (Type Safety), II (Fail Fast), I (Simplicity)
- **Implementation Approach**:
  - Create `TestRedisIntegration` class
  - Type hints on all test functions
  - Test methods (13 total):
    1. test_redis_connection_and_ping - verify connection, ping returns True
    2. test_string_operations - set, get, delete, verify operations
    3. test_expiration_and_ttl - set with TTL, verify expiration, update TTL
    4. test_hash_operations - hset, hget, hgetall, hdel operations
    5. test_list_operations - lpush, rpush, lrange, lpop, rpop
    6. test_set_operations - sadd, smembers, srem
    7. test_sorted_set_operations - zadd, zrange, zrem
    8. test_json_operations - set_json, get_json, mget_json, mset_json
    9. test_pydantic_operations - set_model, get_model with TestUser model
    10. test_namespace_functionality - create namespaced service, verify prefix
    11. test_pipeline_operations - create pipeline, queue ops, execute
    12. test_pubsub_operations - subscribe, publish, receive message
    13. test_increment_decrement - set counter, incr, decr, verify values
  - Use fixtures for redis_service
  - Use unique key names (uuid) for isolation
  - Cleanup keys in finally blocks or autouse fixture
  - Use TestUser Pydantic model for model operations
  - Each test validates one Redis feature area
- **Files to Create**:
  - `integration-tests/test_redis_integration.py`
- **Dependencies**: Task 4

### Task 8: Run Linting and Formatting
- **Constitutional Principles**: II (Fail Fast - zero linting violations), III (Type Safety verification)
- **Implementation Approach**:
  - Run `ruff format` on all integration test files
  - Run `ruff check --fix` to auto-fix issues
  - Run `ruff check` to identify remaining violations
  - Manually resolve ALL violations:
    - Complexity violations (C901) - refactor if any test is too complex
    - Unused imports - remove them
    - Style violations - fix patterns
  - Re-run `ruff check` until ZERO violations remain
  - Verify all type hints are correct
  - Code NOT complete until linting is clean
- **Files to Modify**: All integration test files
- **Dependencies**: Tasks 5, 6, 7

### Task 9: Execute Integration Tests and Verify
- **Constitutional Principles**: V (Testing validation)
- **Implementation Approach**:
  - Ensure `.env` file exists with required environment variables
  - Ensure MinIO, MongoDB, Redis services are running
  - Run `pytest integration-tests/ -v` to execute all integration tests
  - Verify all tests pass
  - Check for proper cleanup (no leftover resources)
  - Test with pytest markers if implemented
  - Document any service setup requirements
- **Files to Test**: All integration test files
- **Dependencies**: Tasks 5, 6, 7, 8

### Task 10: Verify Constitutional Requirements
- **Constitutional Principles**: All (I-VII)
- **Implementation Approach**:
  - Review all code for simplicity (I) - each test focuses on one operation
  - Verify fail-fast patterns (II) - no fallback logic, immediate failures
  - Confirm type hints everywhere (III) - all functions, all fixtures
  - Check structured models used (IV) - Pydantic models for test data
  - Validate testing approach (V) - integration tests use real services
  - Confirm dependency injection (VI) - services injected via fixtures, all REQUIRED
  - Review SOLID compliance (VII) - each test class has single responsibility
  - Ensure zero linting violations
  - Verify proper cleanup patterns
- **Dependencies**: All previous tasks

---

## Constitutional Principle Reference

For each task, the following principles are referenced:
- **I** - Radical Simplicity
- **II** - Fail Fast Philosophy
- **III** - Comprehensive Type Safety
- **IV** - Structured Data Models
- **V** - Unit Testing with Mocking (Integration Testing in this case)
- **VI** - Dependency Injection (all REQUIRED)
- **VII** - SOLID Principles

**Detailed implementation guidance** is in the constitution-task-executor agent.

---

## Success Criteria

### Functional Requirements (from spec)
- [ ] Environment configuration loaded from .env file
- [ ] MinIO integration tests validate all operations (8 tests)
- [ ] MongoDB integration tests validate all operations (10 tests)
- [ ] Redis integration tests validate all operations (13 tests)
- [ ] All tests properly clean up resources
- [ ] Tests are isolated and idempotent
- [ ] Connection handling validated for all services

### Constitutional Compliance (from spec)
- [ ] All code follows radical simplicity (I) - focused, simple tests
- [ ] Fail fast applied throughout (II) - no fallback logic, zero linting violations
- [ ] Type hints on all functions and fixtures (III)
- [ ] Pydantic models used for test data (IV)
- [ ] Integration tests use real services, not mocks (V)
- [ ] Dependency injection via fixtures (VI) - all REQUIRED dependencies
- [ ] SOLID principles maintained (VII) - single responsibility per test class

### Code Quality Gates
- [ ] All test functions have type hints
- [ ] All fixtures have type hints
- [ ] Services injected via pytest fixtures
- [ ] No defensive programming
- [ ] Pydantic models for structured test data
- [ ] Proper cleanup patterns implemented
- [ ] Code formatted with ruff format
- [ ] Linting passes with ZERO violations (ruff check)

### Test Coverage
- [ ] MinIO: 8 integration tests covering all operations
- [ ] MongoDB: 10 integration tests covering all operations
- [ ] Redis: 13 integration tests covering all operations
- [ ] Connection/health checks for all services
- [ ] CRUD operations validated
- [ ] Service-specific features tested (transactions, pipelines, pub/sub)

---

## Environment Variables Required

### MinIO
```bash
MINIO_ENDPOINT=nvda:30090
MINIO_ACCESS_KEY=lvrgd-user
MINIO_SECRET_KEY=lvrgd-password-0123
MINIO_SECURE=false
MINIO_REGION=us-east-1
MINIO_BUCKET=lvrgd-historical-data
```

### MongoDB
```bash
MONGODB_HOST=nvda
MONGODB_PORT=30017
MONGODB_DATABASE=lvrgd
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password123
```

### Redis
```bash
REDIS_HOST=nvda
REDIS_PORT=30379
REDIS_PASSWORD=redis123
```

---

## Test Execution Commands

```bash
# Run all integration tests
pytest integration-tests/ -v

# Run specific service integration tests
pytest integration-tests/test_minio_integration.py -v
pytest integration-tests/test_mongodb_integration.py -v
pytest integration-tests/test_redis_integration.py -v

# Run with output logging
pytest integration-tests/ -v -s

# Run with markers (if implemented)
pytest integration-tests/ -v -m integration
```

---

## Next Steps

1. Review this task breakdown
2. Execute tasks using constitution-task-executor
3. Executor will work through ALL tasks autonomously
4. Executor will update checkboxes in real-time
5. Integration tests will validate end-to-end service functionality
