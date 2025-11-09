# Async Services - Constitutional Specification

**Generated**: 2025-11-08
**Spec Type**: Constitution-Aligned

## 1. Constitutional Compliance Analysis

### Aligned Requirements

The requirement to create async versions of existing services with identical interfaces is fundamentally **constitutional**:

- **Principle I (Radical Simplicity)**: Creating async versions with identical interfaces maintains simplicity - no new abstractions, just async equivalents
- **Principle III (Type Safety)**: Existing services have comprehensive type hints that will be preserved in async versions
- **Principle IV (Structured Data)**: All three services use Pydantic models (MinioConfig, MongoConfig, RedisConfig) - no changes needed
- **Principle VI (Dependency Injection)**: All three services use proper DI with LoggingService and config models - pattern continues
- **Principle VII (SOLID)**: Each service has single responsibility; async versions maintain same boundaries

### Violations Identified

**None - This requirement is constitutionally sound.**

The user is asking for:
1. Async versions with **identical interfaces** (not over-engineered abstractions)
2. Comprehensive testing (unit + integration)
3. Review of existing services (which are already constitutional)

### Simplification Opportunities

1. **Library Selection**: Use well-established async libraries instead of creating custom async wrappers
   - MinIO: Use `aioboto3` or `minio-py` (check if async support exists)
   - MongoDB: Use `motor` (official async MongoDB driver)
   - Redis: Use `redis.asyncio` (official async Redis client, part of redis-py 4.2+)

2. **Code Reuse**: Async services should share the same Pydantic models and constants as sync versions

3. **Testing Strategy**: Leverage existing test patterns - async tests mirror sync tests with `async/await` added

## 2. Requirements Summary

### Core Functional Requirements

**FR-1: AsyncMinioService**
- Description: Create async version of MinioService with identical method signatures
- Constitutional Principles: I (simple), III (typed), IV (structured), VI (DI)
- Implementation Approach: Wrap async MinIO client library (check minio-py async support or use aioboto3)

**FR-2: AsyncMongoService**
- Description: Create async version of MongoService with identical method signatures
- Constitutional Principles: I (simple), III (typed), IV (structured), VI (DI)
- Implementation Approach: Use Motor (official async MongoDB driver from PyMongo team)

**FR-3: AsyncRedisService**
- Description: Create async version of RedisService with identical method signatures
- Constitutional Principles: I (simple), III (typed), IV (structured), VI (DI)
- Implementation Approach: Use redis.asyncio (built into redis-py 4.2+)

**FR-4: Unit Tests for Async Services**
- Description: Create unit tests mirroring existing sync service tests with mocking
- Constitutional Principles: III (typed tests), V (appropriate mocking)
- Implementation Approach: Pytest with pytest-asyncio, mock external async clients

**FR-5: Integration Tests for Async Services**
- Description: Create integration tests against real service instances
- Constitutional Principles: III (typed tests)
- Implementation Approach: Docker Compose fixtures, pytest-asyncio

### Non-Functional Requirements

- **Type Safety**: All async methods have complete type hints (Principle III)
- **Data Models**: Reuse existing Pydantic models - MinioConfig, MongoConfig, RedisConfig (Principle IV)
- **Dependency Injection**: All async services use constructor injection - logger and config REQUIRED (Principle VI)
- **Testing**: Comprehensive unit tests with mocking + integration tests against real services (Principle V)
- **Linting**: Zero ruff violations before completion (Principle II)

## 3. System Components

### Data Models (Principle IV - Structured Data)

**Reuse Existing Models** (No new models needed)
- `MinioConfig` - Located in `src/lvrgd/common/services/minio/minio_models.py`
- `MongoConfig` - Located in `src/lvrgd/common/services/mongodb/mongodb_models.py`
- `RedisConfig` - Located in `src/lvrgd/common/services/redis/redis_models.py`

### Services (Principles VI, VII - DI + SOLID)

**AsyncMinioService**
- Purpose: Async object storage operations (single responsibility)
- Dependencies: LoggingService (REQUIRED), MinioConfig (REQUIRED)
- Key Methods: All sync methods converted to async
  - `async def health_check() -> list[str]`
  - `async def bucket_exists(bucket_name: str) -> bool`
  - `async def ensure_bucket(bucket_name: str) -> None`
  - `async def upload_file(...) -> str`
  - `async def download_file(...) -> None`
  - `async def upload_data(...) -> str`
  - `async def download_data(...) -> bytes`
  - `async def list_objects(...) -> list[str]`
  - `async def remove_object(...) -> None`
  - `async def generate_presigned_url(...) -> str`
  - `async def stat_object(...) -> Any`
- Location: `src/lvrgd/common/services/minio/async_minio_service.py`

**AsyncMongoService**
- Purpose: Async MongoDB database operations (single responsibility)
- Dependencies: LoggingService (REQUIRED), MongoConfig (REQUIRED)
- Key Methods: All sync methods converted to async
  - `async def ping() -> dict[str, Any]`
  - `def get_collection(...) -> AsyncIOMotorCollection` (not async - returns collection handle)
  - `@asynccontextmanager async def transaction() -> AsyncIterator[ClientSession]`
  - `async def insert_one(...) -> InsertOneResult`
  - `async def insert_many(...) -> list[ObjectId]`
  - `async def find_one(...) -> dict[str, Any] | None`
  - `async def find_many(...) -> list[dict[str, Any]]`
  - `async def update_one(...) -> UpdateResult`
  - `async def update_many(...) -> UpdateResult`
  - `async def delete_one(...) -> DeleteResult`
  - `async def delete_many(...) -> DeleteResult`
  - `async def count_documents(...) -> int`
  - `async def aggregate(...) -> list[dict[str, Any]]`
  - `async def create_index(...) -> str`
  - `async def bulk_write(...) -> BulkWriteResult`
  - `async def find_one_model(...) -> T | None`
  - `async def insert_one_model(...) -> InsertOneResult`
  - `async def find_many_models(...) -> list[T]`
  - `async def insert_many_models(...) -> list[ObjectId]`
  - `async def update_one_model(...) -> UpdateResult`
  - `async def update_many_models(...) -> UpdateResult`
  - `async def close() -> None`
- Location: `src/lvrgd/common/services/mongodb/async_mongodb_service.py`

**AsyncRedisService**
- Purpose: Async Redis caching and data operations (single responsibility)
- Dependencies: LoggingService (REQUIRED), RedisConfig (REQUIRED)
- Key Methods: All sync methods converted to async
  - `async def ping() -> bool`
  - `async def get(key: str) -> str | None`
  - `async def set(...) -> bool`
  - `async def delete(*keys: str) -> int`
  - `async def exists(*keys: str) -> int`
  - `async def expire(key: str, seconds: int) -> bool`
  - `async def ttl(key: str) -> int`
  - `async def incr(key: str, amount: int = 1) -> int`
  - `async def decr(key: str, amount: int = 1) -> int`
  - Hash operations: `hget`, `hset`, `hgetall`, `hdel`
  - List operations: `lpush`, `rpush`, `lpop`, `rpop`, `lrange`
  - Set operations: `sadd`, `smembers`, `srem`
  - Sorted set operations: `zadd`, `zrange`, `zrem`
  - `@asynccontextmanager async def pipeline(...) -> AsyncIterator[Pipeline]`
  - `async def publish(channel: str, message: str) -> int`
  - `@asynccontextmanager async def subscribe(*channels: str) -> AsyncIterator[PubSub]`
  - Vector search: `create_vector_index`, `vector_search`, `drop_index`
  - JSON operations: `get_json`, `set_json`, `mget_json`, `mset_json`, `hget_json`, `hset_json`, `hgetall_json`
  - Pydantic operations: `get_model`, `set_model`, `mget_models`, `mset_models`, `hget_model`, `hset_model`
  - `def cache(...)` - Decorator (needs async version)
  - `async def get_or_compute(...) -> Any`
  - `async def check_rate_limit(...) -> tuple[bool, int]`
  - `async def close() -> None`
- Location: `src/lvrgd/common/services/redis/async_redis_service.py`

### Integration Points

**External Dependencies (Principle V - Mocking Strategy)**
- MinIO: Mock async MinIO client in unit tests; use real MinIO in integration tests
- MongoDB: Mock Motor client in unit tests; use real MongoDB in integration tests
- Redis: Mock redis.asyncio client in unit tests; use real Redis in integration tests

## 4. Architectural Approach

### Design Principles Applied

**Radical Simplicity (I)**
- Use official async libraries (Motor, redis.asyncio) - don't reinvent the wheel
- Mirror sync service structure exactly - no new architectural patterns
- Keep method signatures identical except for `async def`

**Fail Fast (II)**
- Let async operations fail if connections unavailable
- No fallback logic
- Trust that required data/connections exist

**Type Safety (III)**
- All async methods fully typed including return types
- Use same type hints as sync versions
- Async generators properly typed with `AsyncIterator[T]`

**Structured Data (IV)**
- Reuse existing Pydantic config models
- No dictionaries for structured data
- Pydantic model support methods mirror sync versions

**Dependency Injection (VI)**
- Constructor injection for logger and config
- All dependencies REQUIRED (no Optional, no defaults)
- Never create dependencies inside __init__

**SOLID (VII)**
- Each async service maintains single responsibility
- Open/closed: extend sync pattern, don't modify
- Liskov: async services substitutable in async contexts
- Interface segregation: same focused interfaces as sync
- Dependency inversion: depend on abstractions (LoggingService, config models)

### File Structure

```
src/lvrgd/common/services/
├── minio/
│   ├── __init__.py (export AsyncMinioService)
│   ├── minio_models.py (existing - reuse)
│   ├── minio_service.py (existing sync service)
│   └── async_minio_service.py (NEW)
├── mongodb/
│   ├── __init__.py (export AsyncMongoService)
│   ├── mongodb_models.py (existing - reuse)
│   ├── mongodb_service.py (existing sync service)
│   └── async_mongodb_service.py (NEW)
└── redis/
    ├── __init__.py (export AsyncRedisService)
    ├── redis_models.py (existing - reuse)
    ├── redis_service.py (existing sync service)
    └── async_redis_service.py (NEW)

tests/
├── minio/
│   ├── test_minio_service.py (existing)
│   └── test_async_minio_service.py (NEW)
├── mongodb/
│   ├── test_mongodb_service.py (existing)
│   ├── test_mongodb_service_pydantic.py (existing)
│   └── test_async_mongodb_service.py (NEW)
└── redis/
    ├── test_redis_service.py (existing)
    ├── test_redis_*.py (existing specialized tests)
    └── test_async_redis_service.py (NEW)

integration-tests/
├── test_minio_integration.py (existing)
├── test_async_minio_integration.py (NEW)
├── test_mongodb_integration.py (existing)
├── test_async_mongodb_integration.py (NEW)
├── test_redis_integration.py (existing)
└── test_async_redis_integration.py (NEW)
```

## 5. Testing Strategy

### Unit Testing Approach (Principle V)

**Mocking Strategy**
- Mock async external clients (Motor, redis.asyncio, async MinIO client)
- Use pytest-asyncio for async test support
- Type hints in all test code
- Test happy path, let edge cases fail
- Mirror existing sync test structure

**Test Organization**
- One test file per async service
- Test classes organized by functionality area (same as sync tests)
- Fixture-based setup for mocked dependencies

**Example Test Structure**:
```python
@pytest.fixture
async def async_service(mock_logger: Mock, valid_config: ConfigModel) -> AsyncService:
    """Create async service with mocked client."""
    with patch("path.to.AsyncClient") as mock_client:
        service = AsyncService(mock_logger, valid_config)
        await service.initialize()  # if needed
        return service

@pytest.mark.asyncio
async def test_async_operation(async_service: AsyncService) -> None:
    """Test async operation."""
    result = await async_service.operation()
    assert result is not None
```

### Integration Testing Approach

**Real Service Testing**
- Use Docker Compose to spin up MinIO, MongoDB, Redis
- pytest-asyncio for async integration tests
- Test against real async connections
- Cleanup after each test

**Integration Test Coverage**
- AsyncMinioService: bucket operations, object upload/download, presigned URLs
- AsyncMongoService: CRUD operations, transactions, Pydantic model support
- AsyncRedisService: basic operations, JSON, Pydantic, caching, pub/sub, rate limiting

### Test Coverage

**AsyncMinioService**
- Unit tests: Mock async MinIO client, test all methods
- Integration tests: Real MinIO instance, test file/data operations

**AsyncMongoService**
- Unit tests: Mock Motor client, test all CRUD + Pydantic methods
- Integration tests: Real MongoDB instance, test transactions and model operations

**AsyncRedisService**
- Unit tests: Mock redis.asyncio client, test all Redis operations
- Integration tests: Real Redis instance, test caching, pub/sub, rate limiting

## 6. Implementation Constraints

### Constitutional Constraints (NON-NEGOTIABLE)

- Keep it simple - mirror sync services exactly
- Fail fast - no fallback logic in async operations
- Type hints everywhere - all async methods fully typed
- Structured models only - reuse existing Pydantic configs
- Constructor injection - all dependencies REQUIRED (no Optional, no defaults)
- SOLID compliance - maintain single responsibility per service

### Technical Constraints

**Python Version**: >=3.10 (existing project requirement)

**Library Requirements**:
- `motor>=3.3.0` - Official async MongoDB driver
- `redis>=5.0.0` - Already includes redis.asyncio
- MinIO async support - investigate options:
  - Option 1: Check if `minio>=7.2.7` has async support
  - Option 2: Use `aioboto3` for async S3-compatible operations
  - Option 3: Create thin async wrapper using `asyncio.to_thread` (fallback)

**Testing Libraries** (already in dev dependencies):
- `pytest>=8.4.2`
- `pytest-asyncio>=1.2.0`
- `pytest-mock>=3.15.1`

**Linting Requirements**:
- Zero ruff violations before completion
- Same ruff config as existing codebase
- Per-file ignores for async services if needed (minimal)

## 7. Success Criteria

### Functional Success

- [ ] AsyncMinioService implements all methods from MinioService
- [ ] AsyncMongoService implements all methods from MongoService
- [ ] AsyncRedisService implements all methods from RedisService
- [ ] All async methods have identical signatures (except async def)
- [ ] Unit tests pass for all three async services
- [ ] Integration tests pass for all three async services
- [ ] Services exported from __init__.py files

### Constitutional Success

- [ ] All code follows radical simplicity (I) - no over-engineering
- [ ] Fail fast applied throughout (II) - no defensive coding
- [ ] Type hints on all async functions (III)
- [ ] Pydantic config models reused (IV)
- [ ] Unit tests use appropriate mocking (V)
- [ ] Dependency injection implemented (VI) - all dependencies REQUIRED
- [ ] SOLID principles maintained (VII)
- [ ] Zero ruff check violations

### Quality Gates

- [ ] All async methods properly awaitable
- [ ] Async context managers use `@asynccontextmanager`
- [ ] No sync blocking calls in async code paths
- [ ] Proper cleanup in async teardown methods
- [ ] Documentation mirrors sync service docs
- [ ] All tests use pytest-asyncio markers

## 8. Implementation Details

### AsyncMinioService Specifics

**Challenge**: MinIO Python SDK may not have native async support

**Solution Options** (in order of preference):
1. **Check minio-py async**: Verify if newer versions support async
2. **Use aioboto3**: AWS S3-compatible async client works with MinIO
3. **Async wrapper**: Use `asyncio.to_thread` for CPU-bound operations (last resort)

**Method Conversions**:
- All methods become `async def`
- File I/O operations wrapped in async executors if needed
- Presigned URL generation may remain sync (cryptographic operation)

### AsyncMongoService Specifics

**Library**: Motor (official async driver)

**Key Differences from Sync**:
- `AsyncIOMotorClient` instead of `MongoClient`
- `AsyncIOMotorDatabase` instead of `Database`
- `AsyncIOMotorCollection` instead of `Collection`
- All database operations are async
- Transaction context manager uses `async with`

**Type Imports**:
```python
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
    AsyncIOMotorClientSession,
)
```

### AsyncRedisService Specifics

**Library**: redis.asyncio (part of redis-py 5.0+)

**Key Changes**:
- Import from `redis.asyncio` instead of `redis`
- All Redis operations are async
- Pipeline context manager uses `async with`
- PubSub uses async iterator pattern
- Caching decorator needs async version

**Type Imports**:
```python
from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.client import Pipeline, PubSub
```

**Decorator Challenge**:
- `cache()` decorator needs async wrapper version
- Decorate async functions, await cached operations
- Maintain same API as sync version

## 9. Migration Considerations

### Backward Compatibility

- Sync services remain unchanged
- Async services coexist with sync services
- Users can choose sync or async based on their application context
- Same config models work for both sync and async

### Import Strategy

**Explicit Exports**:
```python
# src/lvrgd/common/services/minio/__init__.py
from .minio_service import MinioService
from .async_minio_service import AsyncMinioService
from .minio_models import MinioConfig

__all__ = ["MinioService", "AsyncMinioService", "MinioConfig"]
```

### Usage Examples

**Sync Usage** (existing, unchanged):
```python
from lvrgd.common.services.minio import MinioService, MinioConfig
from lvrgd.common.services.logging_service import LoggingService

logger = LoggingService()
config = MinioConfig(endpoint="localhost:9000", access_key="...", secret_key="...")
minio = MinioService(logger, config)
minio.upload_file("test.txt", "/path/to/file.txt")
```

**Async Usage** (new):
```python
from lvrgd.common.services.minio import AsyncMinioService, MinioConfig
from lvrgd.common.services.logging_service import LoggingService

logger = LoggingService()
config = MinioConfig(endpoint="localhost:9000", access_key="...", secret_key="...")
async_minio = AsyncMinioService(logger, config)
await async_minio.upload_file("test.txt", "/path/to/file.txt")
```

## 10. Dependencies and Libraries

### New Dependencies Required

**Production Dependencies**:
```toml
[project]
dependencies = [
    "loguru>=0.7.3",
    "minio>=7.2.7",
    "motor>=3.3.0",  # NEW - Async MongoDB
    "pydantic>=2.11.9",
    "pymongo>=4.15.1",
    "redis>=5.0.0",  # Already includes asyncio support
    "rich>=14.2.0",
]
```

**Note**:
- `motor` is the only new production dependency
- `redis>=5.0.0` already supports async
- MinIO async support to be determined (may need `aioboto3`)

**Development Dependencies**:
- No changes needed - `pytest-asyncio>=1.2.0` already present

### Library Compatibility Matrix

| Service | Sync Library | Async Library | Status |
|---------|-------------|---------------|--------|
| MinIO | `minio>=7.2.7` | TBD (investigate) | Research needed |
| MongoDB | `pymongo>=4.15.1` | `motor>=3.3.0` | Well-established |
| Redis | `redis>=5.0.0` | `redis.asyncio` (same package) | Built-in |

## 11. Error Handling Strategy

### Constitutional Approach (Principle II - Fail Fast)

**No Defensive Programming**:
- Let async operations fail if connections unavailable
- No try-except wrappers around expected failures
- Trust that dependencies are properly configured

**Expected Errors**:
- Connection failures → Let them propagate
- Invalid credentials → Let them fail
- Network timeouts → Let them fail
- Type mismatches → Let Python's type system catch them

**Logging Only**:
- Log exceptions during initialization
- Log operation start/completion
- No error recovery logic

### Example Pattern

```python
async def upload_file(self, object_name: str, file_path: str, ...) -> str:
    """Upload file to MinIO."""
    self.log.debug("Uploading file", file_path=file_path, object_name=object_name)
    # No existence checks, no try-except - just do it
    result = await self._client.fput_object(bucket, object_name, file_path)
    self.log.info("Uploaded file", object_name=object_name, etag=result.etag)
    return result.object_name
```

## 12. Documentation Requirements

### Code Documentation

**Docstrings**:
- All async methods have Google-style docstrings
- Mirror sync service documentation
- Add "Async version of..." prefix where helpful
- Include async/await usage examples

**Type Hints**:
- Every async method fully typed
- Async return types explicit: `-> Awaitable[T]` not needed (implicit with `async def`)
- Async context managers typed: `AsyncIterator[T]`, `AsyncContextManager[T]`

**Examples in Docstrings**:
```python
async def find_one(
    self,
    collection_name: str,
    query: dict[str, Any],
    projection: dict[str, Any] | None = None,
    session: AsyncIOMotorClientSession | None = None,
) -> dict[str, Any] | None:
    """Find a single document in a collection.

    Args:
        collection_name: Name of the collection
        query: Query filter
        projection: Fields to include/exclude
        session: Optional session for transaction support

    Returns:
        Found document or None

    Example:
        user = await mongo_service.find_one(
            "users",
            {"email": "test@example.com"}
        )
    """
```

### README Updates

- Add async services section to main README
- Include usage examples for each async service
- Document async-specific considerations (event loop, context managers)

## 13. Rollout Strategy

### Development Phases

**Phase 1: AsyncMinioService**
1. Research MinIO async library options
2. Implement AsyncMinioService
3. Write unit tests with mocking
4. Write integration tests
5. Update __init__.py exports

**Phase 2: AsyncMongoService**
1. Install and configure Motor
2. Implement AsyncMongoService
3. Write unit tests with mocking
4. Write integration tests (transactions, Pydantic)
5. Update __init__.py exports

**Phase 3: AsyncRedisService**
1. Implement AsyncRedisService with redis.asyncio
2. Implement async cache decorator
3. Write unit tests with mocking
4. Write integration tests (pub/sub, rate limiting)
5. Update __init__.py exports

**Phase 4: Documentation and Finalization**
1. Update README with async examples
2. Verify all ruff checks pass
3. Run full test suite (sync + async)
4. Update pyproject.toml if needed

### Testing Progression

1. Unit tests pass for each service individually
2. Integration tests pass for each service individually
3. All tests pass together (sync + async)
4. No ruff violations across entire codebase

## 14. Risk Assessment

### Technical Risks

**Risk 1: MinIO Async Library Support**
- **Issue**: MinIO Python SDK may not have native async support
- **Mitigation**: Research alternatives (aioboto3, asyncio.to_thread wrapper)
- **Constitutional Impact**: Low - any solution maintains simplicity

**Risk 2: Breaking Changes in Motor**
- **Issue**: Motor API might differ from PyMongo
- **Mitigation**: Review Motor documentation, use same method names
- **Constitutional Impact**: Low - maintain interface compatibility

**Risk 3: Redis Async Decorator Complexity**
- **Issue**: Cache decorator might be complex to async-ify
- **Mitigation**: Simplify if needed, focus on core caching functionality
- **Constitutional Impact**: Medium - ensure decorator stays simple

### Implementation Risks

**Risk 4: Test Complexity**
- **Issue**: Async tests might be harder to mock correctly
- **Mitigation**: Use pytest-asyncio best practices, mirror sync tests
- **Constitutional Impact**: Low - appropriate mocking is constitutional

**Risk 5: Integration Test Flakiness**
- **Issue**: Async operations might have timing issues
- **Mitigation**: Proper await usage, avoid race conditions
- **Constitutional Impact**: Low - fail fast on real issues

## 15. Next Steps

### Immediate Actions

1. **Research MinIO Async Options**
   - Check minio-py documentation for async support
   - Evaluate aioboto3 compatibility
   - Decide on implementation approach

2. **Install Dependencies**
   - Add motor to pyproject.toml
   - Add aioboto3 if needed for MinIO
   - Update dependency groups

3. **Create File Structure**
   - Create async_*_service.py files
   - Create test files
   - Update __init__.py exports

### Task Generation

**Ready for constitution-task-generator**:
- This spec provides clear requirements
- Constitutional principles are enforced
- Component boundaries are defined
- Testing strategy is outlined
- Implementation constraints are specified

### Execution Path

1. Review this constitutional specification
2. Confirm async library choices (especially MinIO)
3. Generate detailed tasks using constitution-task-generator
4. Execute tasks using constitution-task-executor
5. Verify constitutional compliance throughout

---

## Constitutional Validation

This specification enforces the 7 constitutional principles:

1. **Radical Simplicity (I)**: Mirror sync services, use official async libraries, no over-engineering
2. **Fail Fast (II)**: No defensive programming, let async operations fail naturally
3. **Type Safety (III)**: All async methods fully typed, async return types explicit
4. **Structured Data (IV)**: Reuse existing Pydantic config models
5. **Unit Testing with Mocking (V)**: Comprehensive unit tests with appropriate async client mocking
6. **Dependency Injection (VI)**: Constructor injection with REQUIRED dependencies (logger, config)
7. **SOLID Principles (VII)**: Single responsibility per service, open/closed compliance, proper abstraction

**Note**: All downstream tasks must maintain these constitutional guarantees. No complexity creep. No fallback logic. Type hints everywhere. Pydantic models only. Proper DI with REQUIRED dependencies. SOLID maintained.
