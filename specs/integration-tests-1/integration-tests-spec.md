# Integration Tests Specification

**Generated**: 2025-11-08
**Version**: 1.0.0
**Status**: Draft

## 1. Executive Summary

This specification defines integration tests for the MinIO, MongoDB, and Redis services in the lvrgd-common library. Integration tests validate end-to-end functionality by connecting to real service instances (not mocks) using configuration from environment variables. These tests complement existing unit tests by verifying actual service integration, connection handling, and real-world operation behavior.

### Scope
- Integration tests for `MinioService`
- Integration tests for `MongoService`
- Integration tests for `RedisService`
- Environment-based configuration loading
- pytest framework integration
- Real service connection validation

### Out of Scope
- Unit tests (already exist)
- Performance/load testing
- Security testing
- Mock-based testing

## 2. System Architecture

### Component Overview
```
tests/
├── integration/                    # NEW: Integration tests directory
│   ├── __init__.py
│   ├── conftest.py                # Integration test fixtures
│   ├── test_minio_integration.py  # MinIO integration tests
│   ├── test_mongodb_integration.py # MongoDB integration tests
│   └── test_redis_integration.py  # Redis integration tests
├── unit/                          # Existing unit tests
│   └── redis/
│       ├── test_redis_caching_decorator.py
│       ├── test_redis_json_operations.py
│       ├── test_redis_namespace.py
│       ├── test_redis_pydantic_operations.py
│       └── test_redis_rate_limiting.py
├── conftest.py                    # Root test configuration
├── minio/
│   └── test_minio_service.py      # Unit tests
├── mongodb/
│   └── test_mongodb_service.py    # Unit tests
└── redis/
    └── test_redis_service.py      # Unit tests
```

### Service Dependencies
```
Integration Tests
    ├── MinioService
    │   ├── LoggingService (dependency)
    │   ├── MinioConfig (configuration)
    │   └── minio.Minio (external client)
    ├── MongoService
    │   ├── LoggingService (dependency)
    │   ├── MongoConfig (configuration)
    │   └── pymongo.MongoClient (external client)
    └── RedisService
        ├── LoggingService (dependency)
        ├── RedisConfig (configuration)
        └── redis.Redis (external client)
```

## 3. Requirements Analysis

### Functional Requirements

#### FR-1: Environment Configuration Loading
- **Priority**: Critical
- **Description**: Load service connection parameters from `.env` file
- **Dependencies**: python-dotenv or equivalent
- **Validation**: Environment variables must be loaded before test execution

#### FR-2: MinIO Integration Tests
- **Priority**: High
- **Description**: Validate MinIO service operations against real MinIO instance
- **Operations**:
  - Connection and health check
  - Bucket creation and listing
  - Object upload (file and data)
  - Object download (file and data)
  - Object listing with prefix
  - Object deletion
  - Presigned URL generation
  - Object metadata (stat)

#### FR-3: MongoDB Integration Tests
- **Priority**: High
- **Description**: Validate MongoDB service operations against real MongoDB instance
- **Operations**:
  - Connection and ping
  - Collection operations
  - Insert operations (one, many)
  - Find operations (one, many)
  - Update operations (one, many)
  - Delete operations (one, many)
  - Aggregation pipeline
  - Transactions
  - Index creation
  - Bulk operations

#### FR-4: Redis Integration Tests
- **Priority**: High
- **Description**: Validate Redis service operations against real Redis instance
- **Operations**:
  - Connection and ping
  - String operations (get, set, delete)
  - Hash operations (hget, hset, hgetall)
  - List operations (lpush, rpush, lpop, rpop, lrange)
  - Set operations (sadd, smembers, srem)
  - Sorted set operations (zadd, zrange, zrem)
  - JSON operations (get_json, set_json)
  - Pydantic model operations (get_model, set_model)
  - Namespace functionality
  - TTL and expiration
  - Pipeline operations
  - Pub/Sub operations

### Non-Functional Requirements

#### NFR-1: Test Isolation
- Each test must clean up created resources
- Tests must not depend on execution order
- Tests must be idempotent

#### NFR-2: Constitutional Compliance
- **Principle I - Radical Simplicity**: Simple, focused tests per operation
- **Principle II - Fail Fast**: No fallback logic, expect failures on errors
- **Principle III - Type Safety**: Type hints on all test functions
- **Principle IV - Structured Data**: Use Pydantic models for test data
- **Principle VI - Dependency Injection**: Services injected via fixtures
- **Principle VII - SOLID**: Each test class has single responsibility

#### NFR-3: Performance
- Tests should complete within reasonable timeframe
- Connection pooling should be utilized
- Cleanup should be efficient

#### NFR-4: Reliability
- Tests must handle service unavailability gracefully
- Clear error messages on failure
- Proper resource cleanup on test failure

## 4. Data Models

### Environment Configuration Model
```python
from pydantic import BaseModel, Field

class IntegrationTestConfig(BaseModel):
    """Configuration for integration tests loaded from environment."""

    # MinIO Configuration
    minio_endpoint: str = Field(..., description="MinIO server endpoint")
    minio_access_key: str = Field(..., description="MinIO access key")
    minio_secret_key: str = Field(..., description="MinIO secret key")
    minio_secure: bool = Field(False, description="Use HTTPS for MinIO")
    minio_region: str | None = Field(None, description="MinIO region")
    minio_bucket: str = Field(..., description="Default test bucket")

    # MongoDB Configuration
    mongodb_host: str = Field(..., description="MongoDB host")
    mongodb_port: int = Field(27017, description="MongoDB port")
    mongodb_database: str = Field(..., description="MongoDB database name")
    mongodb_username: str | None = Field(None, description="MongoDB username")
    mongodb_password: str | None = Field(None, description="MongoDB password")

    # Redis Configuration
    redis_host: str = Field(..., description="Redis host")
    redis_port: int = Field(6379, description="Redis port")
    redis_password: str | None = Field(None, description="Redis password")
    redis_db: int = Field(0, description="Redis database number")
```

### Test Data Models
```python
from pydantic import BaseModel

class TestDocument(BaseModel):
    """Test document for MongoDB/Redis operations."""
    name: str
    value: int
    active: bool = True

class TestUser(BaseModel):
    """Test user model for Pydantic operations."""
    user_id: str
    username: str
    email: str
    age: int | None = None
```

## 5. Integration Test Specifications

### 5.1 MinIO Integration Tests

#### Test Class: TestMinioIntegration

**Test Methods:**

1. `test_minio_connection_and_health_check()`
   - Verify service connects successfully
   - Validate health_check() returns bucket list
   - Assert ping succeeds

2. `test_bucket_operations()`
   - Create test bucket
   - Verify bucket exists
   - List buckets and verify test bucket present
   - Clean up bucket

3. `test_file_upload_download()`
   - Create temporary test file
   - Upload file to MinIO
   - Download file to different location
   - Verify file contents match
   - Clean up objects and files

4. `test_data_upload_download()`
   - Create test byte data
   - Upload data directly (no file)
   - Download data into memory
   - Verify data integrity
   - Clean up objects

5. `test_object_listing()`
   - Upload multiple objects with prefix
   - List objects with prefix filter
   - Verify correct objects returned
   - Clean up objects

6. `test_object_deletion()`
   - Upload test object
   - Verify object exists
   - Delete object
   - Verify object removed
   - Clean up

7. `test_presigned_url_generation()`
   - Upload test object
   - Generate presigned GET URL
   - Verify URL format
   - Clean up object

8. `test_object_metadata()`
   - Upload object with metadata
   - Retrieve object metadata
   - Verify metadata correctness
   - Clean up object

**Fixtures Required:**
- `minio_service`: Configured MinioService instance
- `test_bucket`: Temporary test bucket with cleanup
- `temp_file`: Temporary file with cleanup

### 5.2 MongoDB Integration Tests

#### Test Class: TestMongoDBIntegration

**Test Methods:**

1. `test_mongodb_connection_and_ping()`
   - Verify service connects successfully
   - Validate ping() returns server info
   - Assert version information present

2. `test_insert_and_find_one()`
   - Insert single document
   - Find document by query
   - Verify document content
   - Clean up collection

3. `test_insert_many_and_find_many()`
   - Insert multiple documents
   - Find documents with query
   - Verify document count and content
   - Clean up collection

4. `test_update_operations()`
   - Insert test document
   - Update document (update_one)
   - Verify update result
   - Update multiple documents (update_many)
   - Verify batch update
   - Clean up collection

5. `test_delete_operations()`
   - Insert test documents
   - Delete single document (delete_one)
   - Verify deletion
   - Delete multiple documents (delete_many)
   - Verify batch deletion
   - Clean up collection

6. `test_aggregation_pipeline()`
   - Insert test documents
   - Execute aggregation pipeline
   - Verify aggregation results
   - Clean up collection

7. `test_transaction_operations()`
   - Start transaction
   - Execute multiple operations in transaction
   - Commit transaction
   - Verify all operations succeeded
   - Test rollback on error
   - Clean up collection

8. `test_index_creation()`
   - Create index on collection
   - Verify index exists
   - Test unique index constraint
   - Clean up collection

9. `test_bulk_operations()`
   - Create bulk operation list
   - Execute bulk write
   - Verify bulk results
   - Clean up collection

10. `test_count_documents()`
    - Insert test documents
    - Count with query
    - Verify count accuracy
    - Clean up collection

**Fixtures Required:**
- `mongo_service`: Configured MongoService instance
- `test_collection`: Temporary collection name with cleanup
- `cleanup_collections`: Auto-cleanup fixture

### 5.3 Redis Integration Tests

#### Test Class: TestRedisIntegration

**Test Methods:**

1. `test_redis_connection_and_ping()`
   - Verify service connects successfully
   - Validate ping() returns True
   - Assert connection active

2. `test_string_operations()`
   - Set key-value pair
   - Get value by key
   - Verify value correctness
   - Delete key
   - Verify key removed
   - Clean up

3. `test_expiration_and_ttl()`
   - Set key with expiration
   - Verify TTL correct
   - Update expiration
   - Verify TTL updated
   - Clean up

4. `test_hash_operations()`
   - Create hash
   - Set hash fields (hset)
   - Get hash field (hget)
   - Get all hash fields (hgetall)
   - Delete hash fields (hdel)
   - Verify operations
   - Clean up

5. `test_list_operations()`
   - Push to list head (lpush)
   - Push to list tail (rpush)
   - Get list range (lrange)
   - Pop from list (lpop, rpop)
   - Verify list contents
   - Clean up

6. `test_set_operations()`
   - Add members to set (sadd)
   - Get set members (smembers)
   - Remove from set (srem)
   - Verify set operations
   - Clean up

7. `test_sorted_set_operations()`
   - Add members with scores (zadd)
   - Get range by score (zrange)
   - Remove members (zrem)
   - Verify sorted set operations
   - Clean up

8. `test_json_operations()`
   - Set JSON value
   - Get JSON value
   - Verify JSON serialization/deserialization
   - Test mget_json, mset_json
   - Clean up

9. `test_pydantic_operations()`
   - Create Pydantic model instance
   - Set model (set_model)
   - Get model (get_model)
   - Verify model validation
   - Test mget_models, mset_models
   - Clean up

10. `test_namespace_functionality()`
    - Create service with namespace
    - Set values
    - Verify namespace prefix applied
    - Get values
    - Clean up

11. `test_pipeline_operations()`
    - Create pipeline
    - Queue multiple operations
    - Execute pipeline
    - Verify all operations succeeded
    - Clean up

12. `test_pubsub_operations()`
    - Create subscriber
    - Publish message
    - Receive message
    - Verify message content
    - Clean up

13. `test_increment_decrement()`
    - Set counter
    - Increment counter (incr)
    - Decrement counter (decr)
    - Verify counter values
    - Clean up

**Fixtures Required:**
- `redis_service`: Configured RedisService instance
- `redis_cleanup`: Auto-cleanup fixture for keys
- `test_namespace`: Namespaced service instance

## 6. Technical Implementation

### 6.1 Directory Structure
```
tests/integration/
├── __init__.py                     # Package marker
├── conftest.py                     # Integration test fixtures
├── test_minio_integration.py       # MinIO integration tests
├── test_mongodb_integration.py     # MongoDB integration tests
└── test_redis_integration.py       # Redis integration tests
```

### 6.2 Configuration Loading Strategy

**Environment Variables (from .env):**
```bash
# MinIO
MINIO_ENDPOINT=nvda:30090
MINIO_ACCESS_KEY=lvrgd-user
MINIO_SECRET_KEY=lvrgd-password-0123
MINIO_SECURE=false
MINIO_REGION=us-east-1
MINIO_BUCKET=lvrgd-historical-data

# MongoDB
MONGODB_HOST=nvda
MONGODB_PORT=30017
MONGODB_DATABASE=lvrgd
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password123

# Redis
REDIS_HOST=nvda
REDIS_PORT=30379
REDIS_PASSWORD=redis123
```

**Loading Implementation:**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

def load_test_environment() -> None:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
```

### 6.3 Common Fixture Patterns

**conftest.py Structure:**
```python
"""Integration test fixtures and configuration."""

import os
from pathlib import Path
from typing import Iterator
import pytest
from dotenv import load_dotenv
from rich.console import Console

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.minio.minio_service import MinioService
from lvrgd.common.services.minio.minio_models import MinioConfig
from lvrgd.common.services.mongodb.mongodb_service import MongoService
from lvrgd.common.services.mongodb.mongodb_models import MongoConfig
from lvrgd.common.services.redis.redis_service import RedisService
from lvrgd.common.services.redis.redis_models import RedisConfig

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

@pytest.fixture(scope="session")
def logger() -> LoggingService:
    """Create logger service for integration tests."""
    console = Console()
    return LoggingService(console)

@pytest.fixture(scope="session")
def minio_config() -> MinioConfig:
    """Create MinIO configuration from environment."""
    return MinioConfig(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        region=os.getenv("MINIO_REGION"),
        default_bucket=os.getenv("MINIO_BUCKET"),
        auto_create_bucket=True,
    )

@pytest.fixture(scope="session")
def mongodb_config() -> MongoConfig:
    """Create MongoDB configuration from environment."""
    host = os.getenv("MONGODB_HOST", "localhost")
    port = int(os.getenv("MONGODB_PORT", "27017"))
    return MongoConfig(
        url=f"mongodb://{host}:{port}",
        database=os.getenv("MONGODB_DATABASE", "test"),
        username=os.getenv("MONGODB_USERNAME"),
        password=os.getenv("MONGODB_PASSWORD"),
    )

@pytest.fixture(scope="session")
def redis_config() -> RedisConfig:
    """Create Redis configuration from environment."""
    return RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        db=0,
    )

@pytest.fixture(scope="module")
def minio_service(logger: LoggingService, minio_config: MinioConfig) -> Iterator[MinioService]:
    """Create MinIO service for integration tests."""
    service = MinioService(logger, minio_config)
    yield service

@pytest.fixture(scope="module")
def mongo_service(logger: LoggingService, mongodb_config: MongoConfig) -> Iterator[MongoService]:
    """Create MongoDB service for integration tests."""
    service = MongoService(logger, mongodb_config)
    yield service
    service.close()

@pytest.fixture(scope="module")
def redis_service(logger: LoggingService, redis_config: RedisConfig) -> Iterator[RedisService]:
    """Create Redis service for integration tests."""
    service = RedisService(logger, redis_config)
    yield service
    service.close()
```

### 6.4 Cleanup Strategies

**Pattern 1: Fixture-based cleanup**
```python
@pytest.fixture
def test_bucket(minio_service: MinioService) -> Iterator[str]:
    """Provide temporary test bucket with automatic cleanup."""
    bucket_name = f"test-bucket-{uuid.uuid4()}"
    minio_service.ensure_bucket(bucket_name)
    yield bucket_name
    # Cleanup: remove all objects and bucket
    objects = minio_service.list_objects(bucket_name=bucket_name)
    for obj in objects:
        minio_service.remove_object(obj, bucket_name=bucket_name)
    minio_service.client.remove_bucket(bucket_name)
```

**Pattern 2: Try-finally cleanup**
```python
def test_operation(mongo_service: MongoService) -> None:
    """Test with explicit cleanup."""
    collection = f"test_collection_{uuid.uuid4()}"
    try:
        # Test operations
        mongo_service.insert_one(collection, {"test": "data"})
        result = mongo_service.find_one(collection, {"test": "data"})
        assert result is not None
    finally:
        # Cleanup
        mongo_service.get_collection(collection).drop()
```

**Pattern 3: Decorator-based cleanup**
```python
@pytest.fixture(autouse=True)
def cleanup_redis_keys(redis_service: RedisService) -> Iterator[None]:
    """Automatically clean up Redis test keys after each test."""
    test_keys: list[str] = []
    yield
    # Cleanup all test keys
    if test_keys:
        redis_service.delete(*test_keys)
```

## 7. Error Handling

### Connection Failures
```python
def test_service_connection(service: Any) -> None:
    """Test service connection with proper error handling."""
    try:
        service.ping()
    except ConnectionError as e:
        pytest.skip(f"Service unavailable: {e}")
```

### Resource Cleanup on Failure
```python
@pytest.fixture
def safe_cleanup() -> Iterator[list[str]]:
    """Track resources for cleanup even on test failure."""
    resources: list[str] = []
    try:
        yield resources
    finally:
        # Cleanup regardless of test outcome
        for resource in resources:
            cleanup_resource(resource)
```

### Service Unavailability
```python
@pytest.fixture(scope="session", autouse=True)
def check_services_available() -> None:
    """Check all required services are available before running tests."""
    services = {
        "MinIO": check_minio_available,
        "MongoDB": check_mongodb_available,
        "Redis": check_redis_available,
    }

    unavailable = []
    for name, check_func in services.items():
        if not check_func():
            unavailable.append(name)

    if unavailable:
        pytest.exit(
            f"Required services unavailable: {', '.join(unavailable)}. "
            "Start services before running integration tests."
        )
```

## 8. Testing Strategy

### Test Organization
- **File-based organization**: One file per service
- **Class-based grouping**: Related tests in test classes
- **Descriptive names**: Clear test method names indicating purpose

### Test Execution
```bash
# Run all integration tests
pytest tests/integration/

# Run specific service integration tests
pytest tests/integration/test_minio_integration.py
pytest tests/integration/test_mongodb_integration.py
pytest tests/integration/test_redis_integration.py

# Run with verbose output
pytest tests/integration/ -v

# Run with logging output
pytest tests/integration/ -s
```

### Test Markers
```python
# Mark integration tests
@pytest.mark.integration
def test_something():
    pass

# Mark as slow
@pytest.mark.slow
def test_bulk_operation():
    pass

# Skip if service unavailable
@pytest.mark.skipif(not service_available(), reason="Service not available")
def test_feature():
    pass
```

### CI/CD Considerations
- Integration tests require running service instances
- Consider separate CI job for integration tests
- Use Docker Compose for service orchestration in CI
- Set appropriate timeouts for service startup

## 9. Dependencies

### Required Packages
```toml
[dependency-groups]
dev = [
    "pytest>=8.4.2",
    "pytest-asyncio>=1.2.0",
    "pytest-mock>=3.15.1",
    "python-dotenv>=1.0.0",  # NEW: For .env file loading
]
```

### External Services
- **MinIO**: Object storage service (version >= 7.2.7)
- **MongoDB**: Document database (version >= 4.15.1)
- **Redis**: In-memory cache (version >= 5.0.0)

## 10. Security Considerations

### Credential Management
- Load credentials from `.env` file (not committed to version control)
- Never hardcode credentials in test files
- Use environment-specific `.env` files
- Document required environment variables

### Test Data Isolation
- Use unique identifiers for test resources (UUID)
- Separate test database/namespace from production
- Clean up test data after execution
- Avoid using production data in tests

### Access Control
- Use test-specific service accounts with limited permissions
- Verify minimum required permissions for operations
- Test authentication failure scenarios

## 11. Performance Considerations

### Connection Pooling
- Reuse service instances across tests (module scope)
- Configure appropriate pool sizes
- Monitor connection usage

### Resource Cleanup
- Efficient bulk deletion where possible
- Avoid unnecessary round trips
- Clean up in reverse order of creation

### Test Parallelization
- Design tests for parallel execution
- Avoid shared state between tests
- Use unique resource identifiers

## 12. Documentation Requirements

### Test Documentation
Each test should include:
- Clear docstring describing test purpose
- Expected behavior
- Setup requirements
- Cleanup actions

### Environment Setup Guide
Document required:
- Service installation instructions
- Environment variable configuration
- Service startup procedures
- Troubleshooting common issues

### Example Test Structure
```python
def test_feature_name(service: ServiceType, fixture: FixtureType) -> None:
    """Test specific feature behavior.

    This test validates that [feature] correctly [expected behavior]
    when [conditions].

    Setup:
        - Creates test resource X
        - Configures service with Y

    Assertions:
        - Verifies operation succeeds
        - Validates data integrity
        - Confirms expected state

    Cleanup:
        - Removes test resource X
        - Resets service state
    """
    # Arrange
    test_data = create_test_data()

    # Act
    result = service.perform_operation(test_data)

    # Assert
    assert result.success is True
    assert result.data == expected_data

    # Cleanup handled by fixture
```

## 13. Success Criteria

### Test Coverage
- All primary service operations covered
- Critical paths validated
- Error scenarios tested
- Edge cases addressed

### Test Quality
- Tests pass consistently
- No flaky tests
- Clear failure messages
- Proper resource cleanup

### Documentation
- All tests documented
- Environment setup guide complete
- Troubleshooting guide available
- Examples provided

### Performance
- Tests complete within reasonable time
- No resource leaks
- Efficient cleanup
- Proper connection management

## 14. Implementation Checklist

### Phase 1: Infrastructure Setup
- [ ] Create `tests/integration/` directory structure
- [ ] Implement `conftest.py` with fixtures
- [ ] Add `python-dotenv` dependency
- [ ] Document environment variable requirements
- [ ] Create service availability checks

### Phase 2: MinIO Integration Tests
- [ ] Implement `TestMinioIntegration` class
- [ ] Add connection and health check test
- [ ] Add bucket operations tests
- [ ] Add file upload/download tests
- [ ] Add data upload/download tests
- [ ] Add object listing tests
- [ ] Add object deletion tests
- [ ] Add presigned URL tests
- [ ] Add metadata tests
- [ ] Implement cleanup fixtures

### Phase 3: MongoDB Integration Tests
- [ ] Implement `TestMongoDBIntegration` class
- [ ] Add connection and ping test
- [ ] Add insert operations tests
- [ ] Add find operations tests
- [ ] Add update operations tests
- [ ] Add delete operations tests
- [ ] Add aggregation tests
- [ ] Add transaction tests
- [ ] Add index creation tests
- [ ] Add bulk operations tests
- [ ] Implement cleanup fixtures

### Phase 4: Redis Integration Tests
- [ ] Implement `TestRedisIntegration` class
- [ ] Add connection and ping test
- [ ] Add string operations tests
- [ ] Add hash operations tests
- [ ] Add list operations tests
- [ ] Add set operations tests
- [ ] Add sorted set operations tests
- [ ] Add JSON operations tests
- [ ] Add Pydantic model operations tests
- [ ] Add namespace functionality tests
- [ ] Add pipeline operations tests
- [ ] Add pub/sub operations tests
- [ ] Implement cleanup fixtures

### Phase 5: Documentation and Validation
- [ ] Write environment setup guide
- [ ] Document test execution procedures
- [ ] Create troubleshooting guide
- [ ] Add CI/CD integration documentation
- [ ] Validate all tests pass
- [ ] Review test coverage
- [ ] Performance validation

## 15. Future Enhancements

### Potential Improvements
1. **Docker Compose Integration**
   - Automated service startup for local testing
   - Consistent environment across developers
   - Simplified onboarding

2. **Test Data Generators**
   - Faker integration for realistic test data
   - Reusable test data factories
   - Parameterized test data

3. **Performance Benchmarks**
   - Track operation latency
   - Monitor resource usage
   - Regression detection

4. **Advanced Error Scenarios**
   - Network failure simulation
   - Service interruption handling
   - Recovery testing

5. **Test Reporting**
   - HTML test reports
   - Coverage reports
   - Integration with test management tools

### Maintenance Considerations
- Regular test execution in CI/CD
- Periodic review of test effectiveness
- Update tests when service APIs change
- Monitor and address flaky tests
- Keep dependencies up to date

---

## Appendix A: Environment Variables Reference

### MinIO Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| MINIO_ENDPOINT | Yes | - | MinIO server endpoint (host:port) |
| MINIO_ACCESS_KEY | Yes | - | MinIO access key |
| MINIO_SECRET_KEY | Yes | - | MinIO secret key |
| MINIO_SECURE | No | false | Use HTTPS connection |
| MINIO_REGION | No | None | MinIO region |
| MINIO_BUCKET | Yes | - | Default test bucket name |

### MongoDB Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| MONGODB_HOST | Yes | localhost | MongoDB host |
| MONGODB_PORT | No | 27017 | MongoDB port |
| MONGODB_DATABASE | Yes | - | Database name |
| MONGODB_USERNAME | No | None | Authentication username |
| MONGODB_PASSWORD | No | None | Authentication password |

### Redis Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| REDIS_HOST | Yes | localhost | Redis host |
| REDIS_PORT | No | 6379 | Redis port |
| REDIS_PASSWORD | No | None | Redis password |
| REDIS_DB | No | 0 | Redis database number |

## Appendix B: Example Test Execution Output

```bash
$ pytest tests/integration/ -v

tests/integration/test_minio_integration.py::TestMinioIntegration::test_minio_connection_and_health_check PASSED
tests/integration/test_minio_integration.py::TestMinioIntegration::test_bucket_operations PASSED
tests/integration/test_minio_integration.py::TestMinioIntegration::test_file_upload_download PASSED
tests/integration/test_mongodb_integration.py::TestMongoDBIntegration::test_mongodb_connection_and_ping PASSED
tests/integration/test_mongodb_integration.py::TestMongoDBIntegration::test_insert_and_find_one PASSED
tests/integration/test_redis_integration.py::TestRedisIntegration::test_redis_connection_and_ping PASSED
tests/integration/test_redis_integration.py::TestRedisIntegration::test_string_operations PASSED

========================== 35 passed in 12.45s ==========================
```

## Appendix C: Constitutional Compliance Review

### Principle I: Radical Simplicity
- ✅ Each test focuses on single operation
- ✅ Straightforward test structure (Arrange, Act, Assert)
- ✅ Minimal complexity in fixtures
- ✅ Clear, descriptive test names

### Principle II: Fail Fast
- ✅ No fallback logic in tests
- ✅ Tests fail immediately on assertion failures
- ✅ Service unavailability causes immediate skip/fail
- ✅ No defensive programming in test code

### Principle III: Type Safety
- ✅ All test functions have type hints
- ✅ Fixture return types specified
- ✅ Configuration models use Pydantic
- ✅ Test data uses typed models

### Principle IV: Structured Data
- ✅ Pydantic models for configuration
- ✅ Pydantic models for test data
- ✅ No loose dictionaries for structured data
- ✅ Type-safe data containers

### Principle V: Unit Testing with Mocking
- ✅ Integration tests complement unit tests
- ✅ Unit tests already use appropriate mocking
- ✅ Integration tests use real services (no mocks)
- ✅ Clear separation between unit and integration tests

### Principle VI: Dependency Injection
- ✅ Services injected via pytest fixtures
- ✅ All dependencies provided externally
- ✅ Configuration injected, not hardcoded
- ✅ Logger injected into services

### Principle VII: SOLID Principles
- ✅ Single Responsibility: Each test class tests one service
- ✅ Open/Closed: Tests extend via new test methods
- ✅ Liskov Substitution: Service interfaces consistent
- ✅ Interface Segregation: Focused service interfaces
- ✅ Dependency Inversion: Tests depend on abstractions (fixtures)

---

**Document Control:**
- **Author**: AI Specification Generator
- **Reviewers**: Development Team
- **Approval Status**: Pending Review
- **Last Updated**: 2025-11-08
- **Next Review**: Upon implementation completion
