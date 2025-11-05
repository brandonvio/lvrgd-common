# lvrgd-common

> Python utilities and services for MongoDB and MinIO object storage with strong typing and validation

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

`lvrgd-common` is a Python library providing production-ready service wrappers for MongoDB and MinIO (S3-compatible object storage). Built with Pydantic for configuration validation and strong typing throughout, it offers a clean, well-tested interface for common database and storage operations.

## Features

- **MongoDB Service** - Simplified MongoDB operations with transaction support
  - Full CRUD operations with strong typing
  - Transaction context managers for atomic operations
  - Bulk write operations
  - Aggregation pipeline support
  - Index management
  - Connection pooling and health checks

- **MinIO Service** - High-level S3-compatible object storage interface
  - File and in-memory object upload/download
  - Bucket management with auto-creation
  - Presigned URL generation
  - Object metadata operations
  - Support for custom headers and metadata

- **Type Safety** - Pydantic models for all configurations with validation
- **Comprehensive Logging** - Detailed operation logging for debugging and monitoring
- **Well Tested** - Extensive unit and integration test coverage
- **Developer Friendly** - Clean API design with sensible defaults

## Installation

### Using uv (recommended)

```bash
uv add lvrgd-common
```

### Using pip

```bash
pip install lvrgd-common
```

### From source

```bash
git clone https://github.com/yourusername/lvrgd-common.git
cd lvrgd-common
uv sync
```

## Prerequisites

- Python 3.13 or higher
- MongoDB 4.0+ (for MongoDB service)
- MinIO or S3-compatible storage (for MinIO service)

## Quick Start

### MongoDB Service

```python
import logging
from services.mongodb import MongoConfig, MongoService

# Configure logging
logger = logging.getLogger(__name__)

# Create configuration with Pydantic validation
config = MongoConfig(
    url="mongodb://localhost:27017",
    database="myapp",
    username="user",
    password="password",
    max_pool_size=100
)

# Initialize service
mongo = MongoService(logger, config)

# Perform operations
user = {"name": "Alice", "email": "alice@example.com"}
result = mongo.insert_one("users", user)
print(f"Inserted user with ID: {result.inserted_id}")

# Find documents
users = mongo.find_many("users", {"name": "Alice"})

# Use transactions
with mongo.transaction() as session:
    mongo.insert_one("users", {"name": "Bob"}, session=session)
    mongo.update_one("stats", {"_id": 1}, {"$inc": {"count": 1}}, session=session)
```

### MinIO Service

```python
import logging
from services.minio import MinioConfig, MinioService

logger = logging.getLogger(__name__)

# Configure MinIO connection
config = MinioConfig(
    endpoint="play.min.io",
    access_key="your-access-key",
    secret_key="your-secret-key",
    secure=True,
    default_bucket="my-bucket",
    auto_create_bucket=True
)

# Initialize service
minio = MinioService(logger, config)

# Upload a file
minio.upload_file(
    object_name="data/report.pdf",
    file_path="/path/to/report.pdf",
    content_type="application/pdf"
)

# Upload bytes directly
data = b"Hello, World!"
minio.upload_data("greetings.txt", data, content_type="text/plain")

# Download file
minio.download_file("data/report.pdf", "/path/to/download/report.pdf")

# Generate presigned URL (valid for 1 hour)
from datetime import timedelta
url = minio.generate_presigned_url(
    "data/report.pdf",
    expires=timedelta(hours=1)
)
print(f"Share this URL: {url}")

# List objects
objects = minio.list_objects(prefix="data/")
for obj_name in objects:
    print(obj_name)
```

## Configuration

### MongoDB Configuration

The `MongoConfig` model provides comprehensive configuration with validation:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | Required | MongoDB connection URL (mongodb:// or mongodb+srv://) |
| `database` | `str` | Required | Database name |
| `username` | `str | None` | `None` | Username for authentication |
| `password` | `str | None` | `None` | Password for authentication |
| `max_pool_size` | `int` | `100` | Maximum connection pool size (1-500) |
| `min_pool_size` | `int` | `0` | Minimum connection pool size (0-100) |
| `server_selection_timeout_ms` | `int` | `30000` | Server selection timeout (1000-120000) |
| `connect_timeout_ms` | `int` | `10000` | Connection timeout (1000-60000) |
| `retry_writes` | `bool` | `True` | Enable retryable writes |
| `retry_reads` | `bool` | `True` | Enable retryable reads |

### MinIO Configuration

The `MinioConfig` model validates S3-compatible storage settings:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `endpoint` | `str` | Required | MinIO server hostname and optional port |
| `access_key` | `str` | Required | Access key for authentication |
| `secret_key` | `str` | Required | Secret key for authentication |
| `secure` | `bool` | `True` | Use HTTPS for connections |
| `region` | `str | None` | `None` | Optional region for bucket creation |
| `session_token` | `str | None` | `None` | Optional session token for temporary credentials |
| `default_bucket` | `str | None` | `None` | Default bucket for operations |
| `auto_create_bucket` | `bool` | `False` | Automatically create default bucket if missing |

## API Reference

### MongoDB Service Methods

**Connection & Health**
- `ping()` - Verify MongoDB connection and get server info
- `get_collection(name)` - Get a collection instance

**CRUD Operations**
- `insert_one(collection, document, session=None)` - Insert single document
- `insert_many(collection, documents, ordered=True, session=None)` - Insert multiple documents
- `find_one(collection, query, projection=None, session=None)` - Find single document
- `find_many(collection, query, projection=None, sort=None, limit=0, skip=0, session=None)` - Find multiple documents
- `update_one(collection, query, update, upsert=False, session=None)` - Update single document
- `update_many(collection, query, update, upsert=False, session=None)` - Update multiple documents
- `delete_one(collection, query, session=None)` - Delete single document
- `delete_many(collection, query, session=None)` - Delete multiple documents
- `count_documents(collection, query, session=None)` - Count matching documents

**Advanced Operations**
- `transaction()` - Context manager for atomic operations
- `aggregate(collection, pipeline, session=None)` - Execute aggregation pipeline
- `bulk_write(collection, operations, ordered=True, session=None)` - Execute bulk operations
- `create_index(collection, keys, unique=False, **kwargs)` - Create collection index

### MinIO Service Methods

**Bucket Operations**
- `health_check()` - Verify connectivity and list buckets
- `bucket_exists(bucket_name)` - Check if bucket exists
- `ensure_bucket(bucket_name)` - Create bucket if it doesn't exist
- `list_buckets()` - List all accessible buckets

**Object Operations**
- `upload_file(object_name, file_path, bucket_name=None, content_type=None, metadata=None)` - Upload file from disk
- `download_file(object_name, file_path, bucket_name=None)` - Download file to disk
- `upload_data(object_name, data, bucket_name=None, content_type=None, metadata=None)` - Upload bytes from memory
- `download_data(object_name, bucket_name=None)` - Download object to memory
- `list_objects(bucket_name=None, prefix=None, recursive=True)` - List objects in bucket
- `remove_object(object_name, bucket_name=None)` - Delete object
- `stat_object(object_name, bucket_name=None)` - Get object metadata
- `generate_presigned_url(object_name, bucket_name=None, method="GET", expires=timedelta(minutes=15))` - Generate presigned URL

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/lvrgd-common.git
cd lvrgd-common

# Install dependencies with uv
make install
```

### Running Tests

```bash
# Run all tests
make test

# Run with verbose output
make test-verbose

# Run specific test suite
make test-mongodb

# Generate coverage report
make test-coverage
```

### Code Quality

```bash
# Run linter
make lint

# Format code
make format

# Run all checks (lint + format + test)
make check
```

### Project Structure

```
lvrgd-common/
├── src/
│   └── services/
│       ├── mongodb/
│       │   ├── __init__.py
│       │   ├── mongodb_models.py    # Pydantic configuration models
│       │   └── mongodb_service.py   # MongoDB service implementation
│       └── minio/
│           ├── __init__.py
│           ├── minio_models.py      # Pydantic configuration models
│           └── minio_service.py     # MinIO service implementation
├── tests/
│   ├── unit/                        # Unit tests with mocks
│   │   ├── mongodb/
│   │   └── minio/
│   └── integration/                 # Integration tests
│       └── mongodb/
├── pyproject.toml                   # Project metadata and dependencies
├── Makefile                         # Development commands
└── README.md
```

## Testing Strategy

This project uses a comprehensive testing approach:

- **Unit Tests**: Fast tests using mocks (`mongomock` for MongoDB) located in `tests/unit/`
- **Integration Tests**: Real database/storage tests located in `tests/integration/`
- **Test Framework**: pytest with pytest-asyncio and pytest-mock
- **Coverage**: Aim for >80% code coverage

## Dependencies

### Core Dependencies
- `pymongo` (>=4.15.1) - Official MongoDB driver
- `minio` (>=7.2.7) - Official MinIO client
- `pydantic` (>=2.11.9) - Data validation and settings management

### Development Dependencies
- `pytest` (>=8.4.2) - Testing framework
- `pytest-mock` (>=3.15.1) - Mock utilities
- `pytest-asyncio` (>=1.2.0) - Async test support
- `mongomock` (>=4.3.0) - MongoDB mocking
- `ruff` (>=0.13.1) - Fast Python linter
- `black` (>=25.9.0) - Code formatter

## Best Practices

### Error Handling

Both services log errors extensively. Wrap operations in try-except blocks:

```python
from pymongo.errors import ConnectionFailure

try:
    mongo.insert_one("users", {"name": "Alice"})
except ConnectionFailure as e:
    logger.error(f"MongoDB connection failed: {e}")
    # Handle error appropriately
```

### Resource Cleanup

Always close connections when done:

```python
# MongoDB
mongo.close()

# MinIO client is stateless but can be reused
# No explicit cleanup needed
```

### Using Transactions

Transactions ensure atomic operations across multiple documents:

```python
try:
    with mongo.transaction() as session:
        # All operations succeed or all fail
        mongo.insert_one("orders", order_data, session=session)
        mongo.update_one("inventory", {"sku": "ABC"}, {"$inc": {"qty": -1}}, session=session)
except Exception as e:
    logger.error(f"Transaction failed: {e}")
    # Transaction automatically rolled back
```

### Configuration Management

Use environment variables with Pydantic settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str
    mongodb_database: str
    mongodb_username: str
    mongodb_password: str

    class Config:
        env_file = ".env"

settings = Settings()
config = MongoConfig(
    url=settings.mongodb_url,
    database=settings.mongodb_database,
    username=settings.mongodb_username,
    password=settings.mongodb_password
)
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with appropriate tests
4. Run the test suite: `make check`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints throughout
- Write docstrings for all public methods
- Add tests for new features
- Maintain >80% code coverage

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Pydantic](https://pydantic.dev/) for robust data validation
- Uses official [PyMongo](https://pymongo.readthedocs.io/) and [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html)
- Managed with [uv](https://github.com/astral-sh/uv) for fast Python package management

## Support

For questions, issues, or feature requests:

- Open an issue on GitHub
- Check existing documentation
- Review test examples for usage patterns

---

**Note**: This library is designed for internal use within the lvrgd ecosystem but can be used as a reference implementation for MongoDB and MinIO service wrappers.
