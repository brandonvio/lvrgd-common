# README.md

Integration test suite for lvrgd-common services validating real-world interactions with MinIO, MongoDB, and Redis infrastructure.

## Overview

The `integration-tests` directory contains comprehensive integration tests that validate the functionality of lvrgd-common services against real service instances. Unlike unit tests which use mocks, these tests connect to actual MinIO, MongoDB, and Redis servers to verify end-to-end functionality, performance, and reliability.

This test suite ensures that:
- Service implementations correctly interact with external dependencies
- Configuration models properly validate and connect to real services
- Complex operations (transactions, pipelines, bulk operations) work as expected
- Error handling behaves correctly with real service responses
- All advertised service features function in production-like conditions

## Constitution Compliance

**CRITICAL: All code in this directory MUST strictly adhere to the project constitution.**

Read and reference the project constitution at: `/Users/brandon/code/projects/lvrgd/lvrgd-common/.claude/constitution.md`

### Core Constitutional Principles (NON-NEGOTIABLE)

1. **Radical Simplicity**: Always implement the simplest solution. Never make code more complicated than needed.
   - Integration tests follow clear, linear test patterns
   - Each test validates one specific feature or operation
   - No over-engineering or unnecessary abstraction layers

2. **Fail Fast Philosophy**: Systems should fail immediately when assumptions are violated. No defensive fallback code unless explicitly requested.
   - Tests connect directly to services without fallback mechanisms
   - Environment variables must exist or tests fail (no defaults for required config)
   - Assertions are direct and explicit - failures indicate real problems

3. **Comprehensive Type Safety**: Use type hints everywhere - ALL code including tests, lambda functions, services, and models.
   - All fixtures have explicit return type annotations
   - Test methods include `-> None` return type hints
   - Service instances are properly typed (MinioService, MongoService, RedisService)

4. **Structured Data Models**: Always use dataclasses or Pydantic models. Never pass around dictionaries for structured data.
   - Configuration uses Pydantic models (MinioConfig, MongoConfig, RedisConfig)
   - Test data uses Pydantic models (MongoDocument, RedisUser) where structured data is needed
   - Raw dictionaries only used for database document insertion (as per MongoDB API design)

5. **Dependency Injection**: All services must inject dependencies through `__init__`. ALL dependencies are REQUIRED parameters (no Optional, no defaults). NEVER create dependencies inside constructors.
   - Fixtures inject LoggingService and Config objects into service constructors
   - No service creates its own logger or configuration internally
   - All dependencies flow from pytest fixtures through explicit injection

6. **SOLID Principles**: Strictly adhere to Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion.
   - Each test class focuses on one service (Single Responsibility)
   - Tests validate service interfaces without needing implementation details
   - Fixtures provide abstractions (configs, services) that tests depend on

**All developers working in this directory must read and follow `.claude/constitution.md` without exception.**

## Architecture

### Structure

```
integration-tests/
├── __init__.py                    # Module initialization with docstring
├── conftest.py                    # Pytest fixtures for service setup
├── test_minio_integration.py      # MinIO service integration tests
├── test_mongodb_integration.py    # MongoDB service integration tests
└── test_redis_integration.py      # Redis service integration tests
```

### Components

#### conftest.py
**Purpose**: Central pytest configuration providing reusable fixtures for all integration tests

**Functionality**:
- Loads environment variables from `.env` file using python-dotenv
- Provides session-scoped fixtures for:
  - `logger`: LoggingService instance with Rich console output
  - `minio_config`: MinioConfig built from environment variables
  - `mongo_config`: MongoConfig built from environment variables
  - `redis_config`: RedisConfig built from environment variables
- Provides module-scoped service fixtures:
  - `minio_service`: MinioService instance (stateless)
  - `mongo_service`: MongoService instance with cleanup (closes connection after tests)
  - `redis_service`: RedisService instance with cleanup (closes connection after tests)

**Dependencies**: LoggingService, MinioConfig, MongoConfig, RedisConfig, MinioService, MongoService, RedisService (all injected)

**Usage**: Automatically loaded by pytest; fixtures used via dependency injection in test methods

**Constitutional Notes**:
- Follows dependency injection: services receive logger and config as constructor parameters
- Uses Pydantic models for all configuration (MinioConfig, MongoConfig, RedisConfig)
- Type hints on all fixtures and parameters
- Fail-fast: reads required env vars without defaults (will fail if missing)

#### test_minio_integration.py
**Purpose**: Validates MinIO service operations against real MinIO instance

**Functionality**:
- Connection and health check validation
- Bucket operations (create, verify, list, delete)
- File upload/download operations with temporary files
- Data upload/download operations with bytes
- Object listing with prefix filtering
- Object deletion operations
- Presigned URL generation
- Object metadata upload and retrieval

**Dependencies**: MinioService (injected via fixture)

**Usage**: Run via pytest: `pytest integration-tests/test_minio_integration.py`

**Constitutional Notes**:
- Simple, linear test structure - each test validates one feature
- Type hints on all test methods (-> None)
- Fail-fast: assertions verify exact expected behavior
- Proper cleanup in finally blocks ensures tests don't leave artifacts

#### test_mongodb_integration.py
**Purpose**: Validates MongoDB service operations against real MongoDB instance

**Functionality**:
- Connection and ping validation
- Single and batch document insertion
- Query operations (find_one, find_many with filters)
- Update operations (update_one, update_many)
- Delete operations (delete_one, delete_many)
- Aggregation pipeline execution
- Index creation with unique constraints
- Bulk write operations
- Document counting with queries

**Dependencies**: MongoService (injected via fixture)

**Usage**: Run via pytest: `pytest integration-tests/test_mongodb_integration.py`

**Constitutional Notes**:
- Uses Pydantic model (MongoDocument) for structured test data
- Type hints including `list[Any]` for bulk operations (typing complex MongoDB operations)
- Fail-fast: expects DuplicateKeyError when testing unique constraints
- Each test creates unique collection names to avoid conflicts
- Cleanup drops test collections in finally blocks

#### test_redis_integration.py
**Purpose**: Validates Redis service operations against real Redis instance

**Functionality**:
- Connection and ping validation
- String operations (set, get, delete)
- Expiration and TTL management
- Hash field operations (hset, hget, hgetall, hdel)
- List operations (lpush, rpush, lpop, rpop, lrange)
- Set operations (sadd, smembers, srem)
- Sorted set operations (zadd, zrange, zrem)
- JSON operations (set_json, get_json, mset_json, mget_json)
- Pydantic model serialization (set_model, get_model)
- Namespace prefix functionality
- Pipeline batch operations
- Pub/Sub operations
- Increment/decrement counter operations

**Dependencies**: RedisService, RedisConfig, LoggingService (injected via fixtures)

**Usage**: Run via pytest: `pytest integration-tests/test_redis_integration.py`

**Constitutional Notes**:
- Uses Pydantic model (RedisUser) for testing model serialization
- Type hints on all test methods and parameters
- Namespace test creates new service instance with injected dependencies
- Fail-fast: expects specific values, no defensive checks
- UUID-based key names ensure test isolation

## Development

### Setup

**Prerequisites**:
- Python 3.10 or higher
- Running MinIO instance (local or remote)
- Running MongoDB instance (local or remote)
- Running Redis instance (local or remote)
- Environment variables configured (see Configuration section)

**Installation**:
```bash
# Clone repository
git clone <repository-url>
cd lvrgd-common

# Install dependencies with uv
make install

# Or manually with uv
uv sync
```

**Environment Configuration**:
Create a `.env` file in the project root with required variables (see Configuration section).

### Commands

**Run all integration tests**:
```bash
# Using Makefile (runs integration tests after unit tests)
make validate

# Direct pytest invocation
uv run python -m pytest integration-tests/ -x --tb=short
```

**Run specific service tests**:
```bash
# MinIO tests only
uv run python -m pytest integration-tests/test_minio_integration.py -v

# MongoDB tests only
uv run python -m pytest integration-tests/test_mongodb_integration.py -v

# Redis tests only
uv run python -m pytest integration-tests/test_redis_integration.py -v
```

**Run specific test method**:
```bash
# Specific test
uv run python -m pytest integration-tests/test_minio_integration.py::TestMinioIntegration::test_bucket_operations -v
```

**Run with different verbosity**:
```bash
# Minimal output
uv run python -m pytest integration-tests/ -q

# Detailed output
uv run python -m pytest integration-tests/ -vv

# Show print statements
uv run python -m pytest integration-tests/ -s
```

**Stop on first failure**:
```bash
uv run python -m pytest integration-tests/ -x
```

### Workflows

**Development Process**:
1. Ensure external services (MinIO, MongoDB, Redis) are running
2. Configure `.env` with correct connection details
3. Write integration test for new service feature
4. Run test to verify it fails initially (if testing new functionality)
5. Implement service feature
6. Run integration test to verify implementation
7. Ensure cleanup code properly removes test artifacts
8. Run full integration test suite to verify no regressions

**Testing Strategy**:
- Integration tests complement unit tests (which use mocks)
- Unit tests verify logic and edge cases with mocks
- Integration tests verify real service interactions
- Run unit tests frequently during development (fast)
- Run integration tests before commits/PRs (slower but comprehensive)

**CI/CD Integration**:
Integration tests can run in CI/CD pipelines with:
- Docker Compose to spin up MinIO, MongoDB, Redis containers
- Environment variables configured in CI pipeline secrets
- Separate test databases/buckets/keyspaces to avoid conflicts

### Code Standards

**Type Hints**: Required in ALL code (functions, parameters, return values)
```python
def test_connection(self, mongo_service: MongoService) -> None:
    """Test method with type hints."""
    result: dict[str, Any] = mongo_service.ping()
```

**Simplicity**: Keep test logic simple and linear
```python
# Good: Simple, clear test flow
def test_insert_find(self, mongo_service: MongoService) -> None:
    doc = {"name": "test", "value": 42}
    mongo_service.insert_one("collection", doc)
    found = mongo_service.find_one("collection", {"name": "test"})
    assert found["value"] == 42

# Avoid: Over-engineered test helpers and abstractions
```

**Fail Fast**: Direct assertions without defensive checks
```python
# Good: Expect exact behavior
assert result.inserted_id is not None
assert found["name"] == "test-doc"

# Avoid: Defensive checking
if result and hasattr(result, 'inserted_id') and result.inserted_id:
    assert result.inserted_id is not None
```

**Models**: Use Pydantic models for structured test data
```python
# Good: Pydantic model for structured data
class RedisUser(BaseModel):
    user_id: str
    username: str
    email: str
    age: int

user = RedisUser(user_id="123", username="test", email="test@example.com", age=25)
redis_service.set_model(key, user)

# Acceptable: Dictionaries for database documents (MongoDB API design)
doc = {"name": "test", "value": 42}
mongo_service.insert_one("collection", doc)
```

**Dependency Injection**: Services receive dependencies via fixtures
```python
# Good: Fixture injects service with dependencies
@pytest.fixture(scope="module")
def mongo_service(logger: LoggingService, mongo_config: MongoConfig) -> Iterator[MongoService]:
    service = MongoService(logger=logger, config=mongo_config)
    yield service
    service.close()

# Good: Test receives service via fixture
def test_operation(self, mongo_service: MongoService) -> None:
    result = mongo_service.ping()
```

**Cleanup**: Always clean up test artifacts
```python
def test_bucket_operations(self, minio_service: MinioService) -> None:
    test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"

    try:
        # Test operations
        minio_service.ensure_bucket(test_bucket)
        assert minio_service.bucket_exists(test_bucket)
    finally:
        # Cleanup: remove bucket
        if minio_service.bucket_exists(test_bucket):
            minio_service.client.remove_bucket(test_bucket)
```

## Configuration

### Environment Variables

Integration tests require environment variables to connect to services. These are loaded from a `.env` file in the project root.

**MinIO Configuration**:
- `MINIO_ENDPOINT` (required): MinIO server endpoint (e.g., "localhost:9000")
- `MINIO_ACCESS_KEY` (required): Access key for authentication
- `MINIO_SECRET_KEY` (required): Secret key for authentication
- `MINIO_SECURE` (optional): Use HTTPS ("true" or "false", default: "false")
- `MINIO_REGION` (optional): Region for bucket creation
- `MINIO_BUCKET` (optional): Default bucket name

**MongoDB Configuration**:
- `MONGODB_HOST` (required): MongoDB server hostname (e.g., "localhost")
- `MONGODB_PORT` (required): MongoDB server port (e.g., "27017")
- `MONGODB_DATABASE` (required): Database name for testing
- `MONGODB_USERNAME` (optional): Username for authentication
- `MONGODB_PASSWORD` (optional): Password for authentication

**Redis Configuration**:
- `REDIS_HOST` (required): Redis server hostname (e.g., "localhost")
- `REDIS_PORT` (optional): Redis server port (default: "6379")
- `REDIS_PASSWORD` (optional): Password for authentication

**Example .env file**:
```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET=test-bucket

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=test_database
MONGODB_USERNAME=testuser
MONGODB_PASSWORD=testpass

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### Dependencies

**Internal Dependencies** (from lvrgd-common):
- `lvrgd.common.services.logging_service.LoggingService` - Logging with Rich console
- `lvrgd.common.services.minio.minio_models.MinioConfig` - MinIO configuration model
- `lvrgd.common.services.minio.minio_service.MinioService` - MinIO service implementation
- `lvrgd.common.services.mongodb.mongodb_models.MongoConfig` - MongoDB configuration model
- `lvrgd.common.services.mongodb.mongodb_service.MongoService` - MongoDB service implementation
- `lvrgd.common.services.redis.redis_models.RedisConfig` - Redis configuration model
- `lvrgd.common.services.redis.redis_service.RedisService` - Redis service implementation

**External Dependencies** (from pyproject.toml):
- `pytest>=8.4.2` - Testing framework
- `python-dotenv>=1.0.0` - Environment variable loading
- `pydantic>=2.11.9` - Data validation and models
- `rich>=14.2.0` - Console output formatting
- `pymongo>=4.15.1` - MongoDB driver (used by services)
- `minio>=7.2.7` - MinIO client (used by services)
- `redis>=5.0.0` - Redis client (used by services)

**Injection Pattern**:
All services follow dependency injection:
```python
# Services require logger and config (no defaults, no Optional)
service = MinioService(logger=logger, config=config)
service = MongoService(logger=logger, config=config)
service = RedisService(logger=logger, config=config)

# Fixtures provide these dependencies
@pytest.fixture
def mongo_service(logger: LoggingService, mongo_config: MongoConfig) -> Iterator[MongoService]:
    service = MongoService(logger=logger, config=mongo_config)
    yield service
    service.close()
```

## Usage Examples

### Running Integration Tests Locally

**Setup local services with Docker**:
```bash
# Start MinIO
docker run -d \
  -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"

# Start MongoDB
docker run -d \
  -p 27017:27017 \
  --name mongodb \
  -e "MONGO_INITDB_ROOT_USERNAME=testuser" \
  -e "MONGO_INITDB_ROOT_PASSWORD=testpass" \
  mongo:latest

# Start Redis
docker run -d \
  -p 6379:6379 \
  --name redis \
  redis:latest
```

**Configure environment**:
```bash
# Create .env file in project root
cat > .env << EOF
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=test_database
MONGODB_USERNAME=testuser
MONGODB_PASSWORD=testpass

REDIS_HOST=localhost
REDIS_PORT=6379
EOF
```

**Run tests**:
```bash
# Run all integration tests
uv run python -m pytest integration-tests/ -v

# Run specific service tests
uv run python -m pytest integration-tests/test_minio_integration.py -v
```

### Writing New Integration Tests

**Follow constitutional principles**:
```python
"""Integration tests for new service feature."""

import uuid
from pydantic import BaseModel, Field

from lvrgd.common.services.myservice.myservice_service import MyService


class MyModel(BaseModel):
    """Structured data model for tests."""

    id: str = Field(..., description="Record ID")
    name: str = Field(..., description="Record name")
    value: int = Field(..., description="Record value")


class TestMyServiceIntegration:
    """Integration tests for MyService."""

    def test_basic_operation(self, myservice: MyService) -> None:
        """Test basic service operation."""
        # Arrange
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        model = MyModel(id=test_id, name="test", value=42)

        try:
            # Act
            result = myservice.create(model)
            found = myservice.get(test_id)

            # Assert
            assert result.id == test_id
            assert found.name == "test"
            assert found.value == 42

        finally:
            # Cleanup
            myservice.delete(test_id)
```

**Test patterns to follow**:
1. Use UUID for unique test identifiers to avoid conflicts
2. Structure tests with Arrange-Act-Assert pattern
3. Always include cleanup in `finally` blocks
4. Use type hints on all parameters and return values
5. Test one feature per test method
6. Use Pydantic models for structured data
7. Inject services via pytest fixtures

### Integration with CI/CD

**GitHub Actions example**:
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      minio:
        image: minio/minio
        ports:
          - 9000:9000
        env:
          MINIO_ROOT_USER: minioadmin
          MINIO_ROOT_PASSWORD: minioadmin
        options: --health-cmd "curl -f http://localhost:9000/minio/health/live"

      mongodb:
        image: mongo:latest
        ports:
          - 27017:27017
        env:
          MONGO_INITDB_ROOT_USERNAME: testuser
          MONGO_INITDB_ROOT_PASSWORD: testpass

      redis:
        image: redis:latest
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run integration tests
        env:
          MINIO_ENDPOINT: localhost:9000
          MINIO_ACCESS_KEY: minioadmin
          MINIO_SECRET_KEY: minioadmin
          MONGODB_HOST: localhost
          MONGODB_PORT: 27017
          MONGODB_DATABASE: test_db
          MONGODB_USERNAME: testuser
          MONGODB_PASSWORD: testpass
          REDIS_HOST: localhost
          REDIS_PORT: 6379
        run: uv run python -m pytest integration-tests/ -v
```

## Notes

### Important Considerations

- **Service Availability**: Integration tests require running service instances. Tests will fail if services are unreachable.
- **Test Isolation**: Each test creates unique collections/buckets/keys using UUID prefixes to avoid conflicts when running tests in parallel.
- **Cleanup**: Tests include cleanup logic in `finally` blocks to remove test artifacts. Some tests may leave artifacts if interrupted.
- **Performance**: Integration tests are slower than unit tests due to network I/O and real service operations.
- **Environment Parity**: Use services configured similarly to production for meaningful integration testing.

### Known Limitations

- **Docker Dependencies**: Local testing requires Docker to run service containers (unless using remote services).
- **Network Requirements**: Tests require network access to service endpoints.
- **State Dependencies**: Some tests assume clean service state (no pre-existing collections/buckets/keys).
- **Timing Issues**: Pub/Sub tests may occasionally fail due to timing (message delivery is eventually consistent).

### Best Practices

- **Run Before Commits**: Always run integration tests before committing service changes.
- **Separate Test Data**: Use dedicated test databases/buckets separate from development data.
- **Monitor Cleanup**: Periodically check services for orphaned test artifacts (collections/buckets starting with "test-").
- **Environment Variables**: Never commit `.env` files with credentials to version control.
- **Service Versions**: Document service versions tested against for compatibility tracking.

### Troubleshooting

**Tests fail with connection errors**:
- Verify services are running: `docker ps`
- Check service health: `docker logs <container-name>`
- Verify environment variables in `.env` file
- Test connectivity: `telnet localhost <port>`

**Tests fail with authentication errors**:
- Verify credentials in `.env` match service configuration
- Check MongoDB user has appropriate permissions
- Verify MinIO access key/secret key are correct

**Tests leave artifacts**:
- Run cleanup manually: check service for `test-*` collections/buckets/keys
- Ensure tests have proper `finally` blocks
- Check for test interruptions (Ctrl+C during execution)

**Pub/Sub test timing issues**:
- These tests may occasionally fail due to message timing
- Retry test if it fails intermittently
- Consider increasing timeout in pubsub.get_message(timeout=1.0)

### Constitutional Reminders

**Integration tests in this directory must**:
- Use type hints on ALL functions, parameters, and return values
- Follow fail-fast philosophy - no defensive programming
- Use Pydantic models for structured test data
- Inject all service dependencies via pytest fixtures
- Keep test logic simple and linear (one feature per test)
- Clean up test artifacts in finally blocks

**When adding new integration tests**:
- Read `.claude/constitution.md` before starting
- Follow existing test patterns and structure
- Ensure proper type hints and models
- Verify cleanup code works correctly
- Run full integration suite before committing
