# Redis Service JSON Improvements Specification

## Overview

This specification defines enhancements to the `RedisService` class to improve ergonomics, performance, and type safety when working with JSON data and caching patterns.

## Priority Levels

- **High Impact**: Core features that significantly improve developer experience
- **Medium Impact**: Useful features that prevent bugs and improve reliability
- **Nice to Have**: Advanced features for specific use cases

---

## High Impact Features

### 1. JSON Serialization Helpers

**Goal**: Provide convenient methods for storing and retrieving JSON-serializable Python objects.

#### Requirements

- Methods should automatically handle JSON serialization/deserialization
- Methods should handle missing keys gracefully (return None)
- Methods should log errors for invalid JSON
- Methods should support all standard Redis operations (get, set, delete, expire, etc.)

#### Method Signatures

```python
def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
    """Get JSON value from Redis.
    
    Args:
        key: Redis key
        
    Returns:
        Deserialized JSON value (dict, list, or primitive), or None if key doesn't exist
        
    Raises:
        json.JSONDecodeError: If value exists but is not valid JSON
    """

def set_json(
    self,
    key: str,
    value: dict[str, Any] | list[Any] | Any,
    ex: int | None = None,
    nx: bool = False,
    xx: bool = False
) -> bool:
    """Set JSON value in Redis.
    
    Args:
        key: Redis key
        value: JSON-serializable value (dict, list, or primitive)
        ex: Expiration time in seconds
        nx: Only set if key doesn't exist
        xx: Only set if key already exists
        
    Returns:
        True if successful
    """
```

#### Implementation Notes

- Use `json.dumps()` for serialization
- Use `json.loads()` for deserialization
- Log warnings for JSON decode errors
- Return None for missing keys (don't raise exceptions)

---

### 2. Caching Decorator

**Goal**: Automatically cache function results in Redis with minimal boilerplate.

#### Requirements

- Generate cache keys from function name and arguments
- Support custom key prefixes and namespaces
- Support conditional caching (skip cache based on result)
- Support manual cache invalidation
- Gracefully degrade if Redis is unavailable (call function anyway)
- Handle argument serialization for cache keys (strings, ints, lists, dicts, etc.)
- Support TTL configuration
- Optionally prevent thundering herd (only one call computes, others wait)

#### Decorator Signature

```python
def cache(
    self,
    ttl: int,
    key_prefix: str | None = None,
    namespace: str | None = None,
    skip_cache_if: Callable[[Any], bool] | None = None,
    prevent_thundering_herd: bool = False
) -> Callable:
    """Decorator to cache function results in Redis.
    
    Args:
        ttl: Time-to-live in seconds for cached values
        key_prefix: Optional prefix for cache keys (e.g., "api:github")
        namespace: Optional namespace to avoid key collisions (e.g., "v2")
        skip_cache_if: Optional function to determine if result should be cached
        prevent_thundering_herd: If True, only one concurrent call computes, others wait
        
    Returns:
        Decorated function with cache support
        
    Example:
        @redis_service.cache(ttl=300)
        def get_user_profile(user_id: str) -> dict:
            return expensive_operation(user_id)
    """
```

#### Cache Key Generation

- Format: `{namespace}:{key_prefix}:{function_name}:{arg1}={value1}:{arg2}={value2}`
- If namespace is None, omit it
- If key_prefix is None, omit it
- Serialize arguments: strings as-is, numbers as strings, lists/dicts as JSON strings
- Handle keyword arguments and positional arguments

#### Invalidation Methods

Decorated functions should have these methods attached:

```python
def invalidate(self, *args, **kwargs) -> int:
    """Invalidate cache for specific arguments.
    
    Returns:
        Number of keys deleted
    """

def invalidate_all(self) -> int:
    """Invalidate all cached calls of this function.
    
    Returns:
        Number of keys deleted
    """
```

#### Implementation Notes

- Use `functools.wraps` to preserve function metadata
- Store function results as JSON
- If Redis is unavailable, log warning and call function anyway
- For thundering herd prevention, use Redis SET NX with a lock key
- Lock key format: `{cache_key}:lock`
- Lock TTL should be longer than expected function execution time

---

### 3. Batch JSON Operations

**Goal**: Reduce network latency by batching multiple JSON operations into single Redis round trips.

#### Requirements

- Support batch get operations (MGET)
- Support batch set operations (MSET)
- Support expiration for batch sets
- Support hash operations with JSON
- Handle missing keys gracefully (omit from results)
- Log warnings for invalid JSON in batch operations

#### Method Signatures

```python
def mget_json(self, *keys: str) -> dict[str, Any]:
    """Get multiple JSON values at once.
    
    Args:
        *keys: Redis keys to retrieve
        
    Returns:
        Dictionary mapping keys to their deserialized JSON values
        (missing keys are omitted from result)
        
    Example:
        results = redis_service.mget_json("user:123", "user:456", "user:789")
        # Returns: {
        #   "user:123": {"name": "Alice", "age": 30},
        #   "user:456": {"name": "Bob", "age": 25},
        # }
    """

def mset_json(
    self,
    mapping: dict[str, Any],
    ex: int | None = None
) -> bool:
    """Set multiple JSON values at once.
    
    Args:
        mapping: Dictionary of key-value pairs to set
        ex: Optional expiration in seconds (applied to all keys)
        
    Returns:
        True if successful
        
    Example:
        redis_service.mset_json(
            {
                "user:123": {"name": "Alice", "age": 30},
                "user:456": {"name": "Bob", "age": 25},
            },
            ex=3600
        )
    """

def hget_json(self, name: str, key: str) -> dict[str, Any] | None:
    """Get JSON value from hash field.
    
    Args:
        name: Hash name
        key: Hash field key
        
    Returns:
        Deserialized JSON value, or None if field doesn't exist
    """

def hset_json(
    self,
    name: str,
    key: str,
    value: dict[str, Any] | list[Any] | Any
) -> int:
    """Set JSON value in hash field.
    
    Args:
        name: Hash name
        key: Hash field key
        value: JSON-serializable value
        
    Returns:
        Number of fields added (1) or updated (0)
    """

def hgetall_json(self, name: str) -> dict[str, Any]:
    """Get all fields in hash as JSON.
    
    Args:
        name: Hash name
        
    Returns:
        Dictionary mapping field keys to deserialized JSON values
        
    Example:
        redis_service.hset_json("sessions", "sess_123", {"user": "alice"})
        redis_service.hset_json("sessions", "sess_456", {"user": "bob"})
        
        all_sessions = redis_service.hgetall_json("sessions")
        # Returns: {
        #   "sess_123": {"user": "alice"},
        #   "sess_456": {"user": "bob"}
        # }
    """
```

#### Implementation Notes

- Use Redis `MGET` for batch gets
- Use Redis `MSET` for batch sets
- For expiration with batch sets, use pipeline: `MSET` followed by `EXPIRE` for each key
- For hash operations, serialize/deserialize JSON for each field
- Skip invalid JSON entries in batch operations (log warning, continue)

---

### 4. Pydantic Model Integration

**Goal**: Store and retrieve strongly-typed Pydantic models with automatic validation and serialization.

#### Requirements

- Support storing Pydantic models
- Support retrieving Pydantic models with validation
- Support batch operations for models
- Support hash operations for models
- Raise `ValidationError` for invalid data
- Use `model_dump_json()` for efficient serialization
- Log errors for validation failures

#### Dependencies

- `pydantic.BaseModel`
- `pydantic.ValidationError`

#### Method Signatures

```python
from pydantic import BaseModel
from pydantic import ValidationError

def get_model(
    self,
    key: str,
    model_class: type[BaseModel]
) -> BaseModel | None:
    """Get and validate Pydantic model from Redis.
    
    Args:
        key: Redis key
        model_class: Pydantic model class to deserialize into
        
    Returns:
        Validated model instance, or None if key doesn't exist
        
    Raises:
        ValidationError: If data doesn't match model schema
        json.JSONDecodeError: If value is not valid JSON
        
    Example:
        user = redis_service.get_model("user:123", User)
        if user:
            print(user.name)  # Fully typed!
    """

def set_model(
    self,
    key: str,
    model: BaseModel,
    ex: int | None = None,
    nx: bool = False,
    xx: bool = False
) -> bool:
    """Store Pydantic model in Redis.
    
    Args:
        key: Redis key
        model: Pydantic model instance to store
        ex: Expire time in seconds
        nx: Only set if key doesn't exist
        xx: Only set if key already exists
        
    Returns:
        True if successful
        
    Example:
        user = User(id="123", name="Alice", email="alice@example.com", age=30)
        redis_service.set_model("user:123", user, ex=3600)
    """

def mget_models(
    self,
    model_class: type[BaseModel],
    *keys: str
) -> dict[str, BaseModel]:
    """Get multiple models at once.
    
    Args:
        model_class: Pydantic model class
        *keys: Redis keys to retrieve
        
    Returns:
        Dictionary mapping keys to validated model instances
        (invalid models are skipped, logged as warnings)
        
    Example:
        users = redis_service.mget_models(
            User,
            "user:123",
            "user:456",
            "user:789"
        )
    """

def mset_models(
    self,
    mapping: dict[str, BaseModel],
    ex: int | None = None
) -> bool:
    """Set multiple models at once.
    
    Args:
        mapping: Dictionary mapping keys to model instances
        ex: Optional expiration in seconds (applied to all keys)
        
    Returns:
        True if successful
        
    Example:
        redis_service.mset_models(
            {
                "user:123": User(id="123", name="Alice"),
                "user:456": User(id="456", name="Bob"),
            },
            ex=3600
        )
    """

def hset_model(
    self,
    hash_name: str,
    field: str,
    model: BaseModel
) -> int:
    """Store model in hash field.
    
    Args:
        hash_name: Hash name
        field: Hash field key
        model: Pydantic model instance
        
    Returns:
        Number of fields added (1) or updated (0)
        
    Example:
        session = UserSession(user_id="123", expires_at=...)
        redis_service.hset_model("sessions", "sess_abc", session)
    """

def hget_model(
    self,
    hash_name: str,
    field: str,
    model_class: type[BaseModel]
) -> BaseModel | None:
    """Get model from hash field.
    
    Args:
        hash_name: Hash name
        field: Hash field key
        model_class: Pydantic model class
        
    Returns:
        Validated model instance, or None if field doesn't exist
        
    Raises:
        ValidationError: If data doesn't match model schema
    """
```

#### Implementation Notes

- Use `model.model_dump_json()` for serialization (faster than `json.dumps(model.model_dump())`)
- Use `model_class(**json.loads(value))` for deserialization and validation
- Log validation errors with details
- For batch operations, skip invalid models (don't fail entire batch)
- Validation happens automatically via Pydantic constructor

---

## Medium Impact Features

### 5. Rate Limiting Primitives

**Goal**: Provide simple rate limiting utilities using Redis.

#### Requirements

- Support sliding window rate limiting
- Support fixed window rate limiting
- Return remaining quota information
- Thread-safe operations

#### Method Signatures

```python
def check_rate_limit(
    self,
    key: str,
    max_requests: int,
    window_seconds: int,
    sliding: bool = True
) -> tuple[bool, int]:
    """Check if rate limit is exceeded.
    
    Args:
        key: Rate limit key (e.g., "rate_limit:user:123")
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        sliding: If True, use sliding window; if False, use fixed window
        
    Returns:
        Tuple of (is_allowed: bool, remaining: int)
        
    Example:
        allowed, remaining = redis_service.check_rate_limit(
            "rate_limit:api:user:123",
            max_requests=100,
            window_seconds=60
        )
        if not allowed:
            raise RateLimitExceeded(f"Rate limit exceeded. {remaining} requests remaining.")
    """
```

#### Implementation Notes

- Sliding window: Use sorted set with timestamps
- Fixed window: Use counter with expiration
- Return remaining quota for user feedback

---

### 6. Key Namespacing

**Goal**: Prevent key collisions by automatically prefixing all keys with a namespace.

#### Requirements

- Support global namespace configuration
- Support per-operation namespace override
- Namespace should be prepended to all keys automatically
- Should work with all Redis operations

#### Configuration

Add to `RedisConfig`:

```python
namespace: str | None = None  # Global namespace prefix
```

#### Method Behavior

- If `namespace` is set in config, prepend `{namespace}:` to all keys
- Allow per-operation override via `namespace` parameter (if provided)
- Format: `{namespace}:{key}`

#### Implementation Notes

- Apply namespace in all methods that accept keys
- Document namespace behavior in method docstrings
- Consider backward compatibility (make it optional)

---

### 7. Get-or-Compute Atomic Operation

**Goal**: Atomically get value from cache or compute and store it.

#### Requirements

- Atomic operation (no race conditions)
- Support async computation (callable)
- Support expiration
- Return cached value if available, otherwise compute and cache

#### Method Signature

```python
def get_or_compute(
    self,
    key: str,
    compute: Callable[[], Any],
    ex: int | None = None,
    serialize_json: bool = True
) -> Any:
    """Atomically get value from cache or compute and store it.
    
    Args:
        key: Redis key
        compute: Callable that computes the value if not cached
        ex: Optional expiration in seconds
        serialize_json: If True, serialize result as JSON
        
    Returns:
        Cached value or computed value
        
    Example:
        def expensive_operation():
            return {"result": "computed"}
        
        value = redis_service.get_or_compute(
            "cache:key",
            expensive_operation,
            ex=300
        )
    """
```

#### Implementation Notes

- Use Redis `SET NX` to prevent race conditions
- If key exists, return cached value
- If key doesn't exist, compute value, store it, return it
- Handle JSON serialization if `serialize_json=True`

---

## Nice to Have Features

### 8. Vector Search Fluent Interface

**Goal**: Provide a fluent interface for building vector search queries.

#### Requirements

- Chainable query builder
- Support filtering, sorting, limiting
- Type-safe query construction

#### Method Signature

```python
class VectorQueryBuilder:
    """Fluent interface for building vector search queries."""
    
    def filter(self, field: str, value: Any) -> "VectorQueryBuilder":
        """Add filter condition."""
        
    def sort_by(self, field: str, ascending: bool = True) -> "VectorQueryBuilder":
        """Add sort condition."""
        
    def limit(self, count: int) -> "VectorQueryBuilder":
        """Set result limit."""
        
    def execute(self) -> list[dict[str, Any]]:
        """Execute query and return results."""
```

#### Implementation Notes

- Build Redis query incrementally
- Execute when `execute()` is called
- Return structured results

---

### 9. Auto-Retry Configuration

**Goal**: Automatically retry failed Redis operations with configurable backoff.

#### Requirements

- Configurable retry count
- Configurable backoff strategy (exponential, linear, fixed)
- Retry on connection errors, timeouts
- Don't retry on validation errors, key not found

#### Configuration

Add to `RedisConfig`:

```python
retry_count: int = 3
retry_backoff: str = "exponential"  # "exponential", "linear", "fixed"
retry_delay: float = 0.1  # Initial delay in seconds
```

#### Implementation Notes

- Wrap Redis operations in retry logic
- Use exponential backoff: `delay * (2 ** attempt)`
- Log retry attempts
- Raise exception after max retries

---

### 10. Temporary Key Context Managers

**Goal**: Automatically clean up temporary keys using context managers.

#### Requirements

- Create temporary keys with automatic cleanup
- Support expiration
- Support cleanup on exception

#### Method Signature

```python
@contextmanager
def temporary_key(
    self,
    key: str,
    value: str | dict[str, Any] | BaseModel,
    ex: int | None = None
) -> Iterator[str]:
    """Context manager for temporary Redis keys.
    
    Args:
        key: Redis key
        value: Value to store (string, JSON dict, or Pydantic model)
        ex: Optional expiration in seconds
        
    Yields:
        The key name
        
    Example:
        with redis_service.temporary_key("temp:data", {"foo": "bar"}, ex=60) as key:
            # Use key
            data = redis_service.get_json(key)
        # Key is automatically deleted when exiting context
    """
```

#### Implementation Notes

- Store value on enter
- Delete key on exit (even if exception occurs)
- Support JSON and Pydantic model values
- Log key creation and deletion

---

## Implementation Order

1. **JSON Serialization Helpers** (foundation for other features)
2. **Batch JSON Operations** (performance improvement)
3. **Pydantic Model Integration** (type safety)
4. **Caching Decorator** (high-value ergonomic improvement)
5. **Key Namespacing** (bug prevention)
6. **Get-or-Compute Atomic Operation** (reliability)
7. **Rate Limiting Primitives** (useful utility)
8. **Vector Search Fluent Interface** (advanced feature)
9. **Auto-Retry Configuration** (resilience)
10. **Temporary Key Context Managers** (convenience)

---

## Testing Requirements

Each feature should have:
- Unit tests for happy paths
- Unit tests for error cases (invalid JSON, missing keys, etc.)
- Unit tests for edge cases (empty dicts, None values, etc.)
- Integration tests with real Redis instance
- Performance tests for batch operations

---

## Documentation Requirements

- Docstrings for all public methods
- Type hints for all parameters and return values
- Usage examples in docstrings
- Migration guide for existing code
- Performance considerations documented

---

## Error Handling

- Log all errors with appropriate log levels
- Raise exceptions for unrecoverable errors (validation failures, etc.)
- Return None for missing keys (don't raise exceptions)
- Gracefully degrade when Redis is unavailable (for caching decorator)

---

## Backward Compatibility

- All new methods should be additive (don't break existing code)
- Existing methods should continue to work as before
- Namespace feature should be opt-in (default None)
