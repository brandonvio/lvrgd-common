# Docker Compose Integration Tests Specification

**Generated**: 2025-01-27
**Version**: 1.0.0
**Status**: Draft

## 1. Executive Summary

This specification defines the implementation of Docker Compose-based integration testing infrastructure for the lvrgd-common library. The solution will provide a docker-compose.yml file that runs all required services (MongoDB, MinIO, Redis) and update the GitHub Actions CI/CD workflow to automatically start these containers and execute integration tests against them. Environment variables from the `.env` file will be properly surfaced to both the Docker containers and the integration tests.

### Scope
- Docker Compose configuration for MongoDB, MinIO, and Redis services
- GitHub Actions workflow updates to start containers and run integration tests
- Environment variable management and propagation
- Integration test execution against containerized services
- Service health checks and startup coordination

### Out of Scope
- Unit test modifications (already exist)
- Service implementation changes
- Test code modifications (integration tests already exist)
- Local development environment setup documentation

## 2. System Architecture

### Component Overview
```
Project Root
├── docker-compose.yml              # NEW: Docker Compose configuration
├── .github/
│   └── workflows/
│       └── ci-cd.yml               # MODIFIED: Add integration test job
├── integration-tests/              # EXISTING: Integration test suite
│   ├── conftest.py                 # Loads environment variables
│   ├── test_minio_integration.py
│   ├── test_mongodb_integration.py
│   └── test_redis_integration.py
└── .env                            # EXISTING: Environment variables
```

### Service Dependencies
```
GitHub Actions CI/CD
    ├── Docker Compose
    │   ├── MongoDB Container
    │   ├── MinIO Container
    │   └── Redis Container
    └── Integration Tests
        ├── MinioService → MinIO Container
        ├── MongoService → MongoDB Container
        └── RedisService → Redis Container
```

## 3. Requirements Analysis

### Functional Requirements

#### FR-1: Docker Compose Configuration
- **Priority**: Critical
- **Description**: Create docker-compose.yml file that defines MongoDB, MinIO, and Redis services
- **Requirements**:
  - MongoDB service with authentication support
  - MinIO service with access key/secret key configuration
  - Redis service with optional password authentication
  - All services must expose ports accessible to host
  - Services must be configured with environment variables matching `.env` file structure
  - Services must have health checks to ensure readiness

#### FR-2: Environment Variable Management
- **Priority**: Critical
- **Description**: Ensure environment variables from `.env` are properly surfaced to Docker containers and integration tests
- **Requirements**:
  - Docker Compose must use environment variables from `.env` file
  - Integration tests must receive correct connection parameters
  - Environment variables must match expected names in `conftest.py`
  - Variables must be available to both containers and test execution environment

#### FR-3: GitHub Actions Integration
- **Priority**: Critical
- **Description**: Update GitHub Actions workflow to start containers and run integration tests
- **Requirements**:
  - Add new job or step to start Docker Compose services
  - Wait for services to be healthy before running tests
  - Run integration tests against containerized services
  - Properly handle service shutdown after tests complete
  - Integration tests should run in pull request workflow

#### FR-4: Service Health Checks
- **Priority**: High
- **Description**: Implement health checks to ensure services are ready before running tests
- **Requirements**:
  - Docker Compose health checks for each service
  - GitHub Actions workflow must wait for healthy status
  - Timeout handling for service startup failures
  - Clear error messages if services fail to start

### Non-Functional Requirements

#### NFR-1: Test Isolation
- Each CI/CD run must use fresh service instances
- No shared state between test runs
- Containers must be properly cleaned up after tests

#### NFR-2: Performance
- Services should start within reasonable time (< 60 seconds)
- Tests should complete efficiently
- Minimal overhead from container orchestration

#### NFR-3: Reliability
- Workflow must handle service startup failures gracefully
- Clear error messages on failure
- Proper resource cleanup on failure

#### NFR-4: Maintainability
- Docker Compose configuration must be clear and well-documented
- Environment variable mapping must be explicit
- Configuration should be easy to update

## 4. Docker Compose Specification

### 4.1 Service Definitions

#### MongoDB Service
```yaml
mongodb:
  image: mongo:latest
  container_name: lvrgd-mongodb
  ports:
    - "${MONGODB_PORT:-27017}:27017"
  environment:
    MONGO_INITDB_ROOT_USERNAME: ${MONGODB_USERNAME:-admin}
    MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD:-password123}
    MONGO_INITDB_DATABASE: ${MONGODB_DATABASE:-lvrgd}
  healthcheck:
    test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
    interval: 5s
    timeout: 3s
    retries: 5
    start_period: 10s
  networks:
    - lvrgd-network
```

#### MinIO Service
```yaml
minio:
  image: minio/minio:latest
  container_name: lvrgd-minio
  ports:
    - "${MINIO_PORT:-9000}:9000"
    - "${MINIO_CONSOLE_PORT:-9001}:9001"
  environment:
    MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-lvrgd-user}
    MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-lvrgd-password-0123}
  command: server /data --console-address ":9001"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 5s
    timeout: 3s
    retries: 5
    start_period: 10s
  networks:
    - lvrgd-network
```

#### Redis Service
```yaml
redis:
  image: redis:latest
  container_name: lvrgd-redis
  ports:
    - "${REDIS_PORT:-6379}:6379"
  command: redis-server --requirepass ${REDIS_PASSWORD:-redis123}
  healthcheck:
    test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5
    start_period: 5s
  networks:
    - lvrgd-network
```

### 4.2 Network Configuration
```yaml
networks:
  lvrgd-network:
    driver: bridge
```

### 4.3 Environment Variable Mapping

The docker-compose.yml will use environment variables from `.env` file. The following mappings are required:

**MongoDB Variables:**
- `MONGODB_HOST` → Container hostname (default: `localhost` for external access, `mongodb` for internal)
- `MONGODB_PORT` → Exposed port (default: `27017`)
- `MONGODB_DATABASE` → Database name (default: `lvrgd`)
- `MONGODB_USERNAME` → Root username (default: `admin`)
- `MONGODB_PASSWORD` → Root password (default: `password123`)

**MinIO Variables:**
- `MINIO_ENDPOINT` → `localhost:${MINIO_PORT}` for external access
- `MINIO_PORT` → Exposed API port (default: `9000`)
- `MINIO_CONSOLE_PORT` → Exposed console port (default: `9001`)
- `MINIO_ACCESS_KEY` → Root user (default: `lvrgd-user`)
- `MINIO_SECRET_KEY` → Root password (default: `lvrgd-password-0123`)
- `MINIO_SECURE` → `false` (HTTP for local testing)
- `MINIO_REGION` → Optional region setting
- `MINIO_BUCKET` → Default bucket name

**Redis Variables:**
- `REDIS_HOST` → Container hostname (default: `localhost` for external access, `redis` for internal)
- `REDIS_PORT` → Exposed port (default: `6379`)
- `REDIS_PASSWORD` → Redis password (default: `redis123`)

## 5. GitHub Actions Workflow Specification

### 5.1 Workflow Structure

The CI/CD workflow will be updated to include an integration test job that:
1. Starts Docker Compose services
2. Waits for services to be healthy
3. Runs integration tests
4. Cleans up services

### 5.2 Integration Test Job

```yaml
integration-tests:
  runs-on: ubuntu-latest
  needs: []  # Can run in parallel with other jobs
  
  steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.10"
    
    - name: Install uv
      uses: astral-sh/setup-uv@v4
      with:
        version: "latest"
    
    - name: Install dependencies
      run: |
        uv sync --dev
    
    - name: Create .env file
      run: |
        cat > .env << EOF
        # MongoDB Configuration
        MONGODB_HOST=localhost
        MONGODB_PORT=27017
        MONGODB_DATABASE=lvrgd_test
        MONGODB_USERNAME=admin
        MONGODB_PASSWORD=password123
        
        # MinIO Configuration
        MINIO_ENDPOINT=localhost:9000
        MINIO_PORT=9000
        MINIO_ACCESS_KEY=lvrgd-user
        MINIO_SECRET_KEY=lvrgd-password-0123
        MINIO_SECURE=false
        MINIO_REGION=us-east-1
        MINIO_BUCKET=lvrgd-test-bucket
        
        # Redis Configuration
        REDIS_HOST=localhost
        REDIS_PORT=6379
        REDIS_PASSWORD=redis123
        EOF
    
    - name: Start Docker Compose services
      run: |
        docker-compose up -d
    
    - name: Wait for services to be healthy
      run: |
        timeout=120
        elapsed=0
        while [ $elapsed -lt $timeout ]; do
          if docker-compose ps | grep -q "healthy"; then
            echo "Services are healthy"
            break
          fi
          sleep 5
          elapsed=$((elapsed + 5))
        done
        if [ $elapsed -ge $timeout ]; then
          echo "Services failed to become healthy"
          docker-compose ps
          docker-compose logs
          exit 1
        fi
    
    - name: Run integration tests
      run: |
        uv run python -m pytest integration-tests/ -v --tb=short
      env:
        MONGODB_HOST: localhost
        MONGODB_PORT: 27017
        MONGODB_DATABASE: lvrgd_test
        MONGODB_USERNAME: admin
        MONGODB_PASSWORD: password123
        MINIO_ENDPOINT: localhost:9000
        MINIO_ACCESS_KEY: lvrgd-user
        MINIO_SECRET_KEY: lvrgd-password-0123
        MINIO_SECURE: false
        MINIO_REGION: us-east-1
        MINIO_BUCKET: lvrgd-test-bucket
        REDIS_HOST: localhost
        REDIS_PORT: 6379
        REDIS_PASSWORD: redis123
    
    - name: Stop Docker Compose services
      if: always()
      run: |
        docker-compose down -v
```

### 5.3 Alternative: Using docker-compose-wait

A more robust approach using `docker-compose-wait`:

```yaml
- name: Start Docker Compose services
  run: |
    docker-compose up -d
    
- name: Wait for services
  uses: docker/compose-action@v3
  with:
    compose-file: docker-compose.yml
    wait: true
    wait-timeout: 120
```

## 6. Environment Variable Strategy

### 6.1 Variable Sources

1. **`.env` file** (for local development)
   - Loaded by `load_dotenv()` in `conftest.py`
   - Used by Docker Compose when running locally

2. **GitHub Actions environment variables**
   - Set explicitly in workflow step
   - Override any `.env` file values
   - Ensure consistency across CI runs

### 6.2 Variable Propagation

```
.env file (local)
    ↓
docker-compose.yml (reads via ${VAR})
    ↓
Container environment
    ↓
Integration tests (via conftest.py load_dotenv())
```

```
GitHub Actions workflow
    ↓
.env file creation (from workflow)
    ↓
docker-compose.yml (reads via ${VAR})
    ↓
Container environment
    ↓
Integration tests (via explicit env vars + load_dotenv())
```

### 6.3 Required Environment Variables

**For Integration Tests (conftest.py expects):**
- `MINIO_ENDPOINT` (required)
- `MINIO_ACCESS_KEY` (required)
- `MINIO_SECRET_KEY` (required)
- `MINIO_SECURE` (optional, default: "false")
- `MINIO_REGION` (optional)
- `MINIO_BUCKET` (optional)
- `MONGODB_HOST` (required)
- `MONGODB_PORT` (required)
- `MONGODB_DATABASE` (required)
- `MONGODB_USERNAME` (optional)
- `MONGODB_PASSWORD` (optional)
- `REDIS_HOST` (required)
- `REDIS_PORT` (optional, default: "6379")
- `REDIS_PASSWORD` (optional)

## 7. Implementation Details

### 7.1 Docker Compose File Structure

```yaml
version: '3.8'

services:
  mongodb:
    # MongoDB service definition
    
  minio:
    # MinIO service definition
    
  redis:
    # Redis service definition

networks:
  lvrgd-network:
    driver: bridge
```

### 7.2 Health Check Implementation

Each service must implement health checks:
- **MongoDB**: Use `mongosh` to ping database
- **MinIO**: Use HTTP endpoint `/minio/health/live`
- **Redis**: Use `redis-cli ping` command

### 7.3 Port Configuration

Ports must be configurable via environment variables to avoid conflicts:
- Default ports: MongoDB 27017, MinIO 9000, Redis 6379
- All ports exposed to host for test access
- Ports can be overridden via environment variables

### 7.4 Service Startup Order

Services can start in parallel (no dependencies), but tests must wait for all to be healthy:
1. Start all services in parallel
2. Wait for all health checks to pass
3. Run integration tests
4. Clean up services

## 8. Error Handling

### 8.1 Service Startup Failures

- Health check timeouts must fail the workflow
- Logs must be captured before failure
- Clear error messages indicating which service failed

### 8.2 Test Failures

- Test failures should not prevent cleanup
- Use `if: always()` for cleanup steps
- Preserve container logs for debugging

### 8.3 Port Conflicts

- Use environment variables for port configuration
- Document port requirements
- Provide clear error messages for conflicts

## 9. Testing Strategy

### 9.1 Local Testing

Developers can test Docker Compose setup locally:
```bash
# Start services
docker-compose up -d

# Run integration tests
uv run pytest integration-tests/ -v

# Stop services
docker-compose down
```

### 9.2 CI/CD Testing

- Integration tests run automatically on pull requests
- Services start fresh for each run
- No shared state between runs

### 9.3 Validation

- Verify all services start successfully
- Verify health checks pass
- Verify integration tests can connect to services
- Verify cleanup works correctly

## 10. Dependencies

### 10.1 Required Tools

- Docker (for GitHub Actions runner)
- Docker Compose (v2+)
- Python 3.10+
- pytest
- python-dotenv

### 10.2 Docker Images

- `mongo:latest` - MongoDB service
- `minio/minio:latest` - MinIO service
- `redis:latest` - Redis service

## 11. Security Considerations

### 11.1 Credential Management

- Use test-specific credentials (not production)
- Credentials in `.env` should not be committed (already in `.gitignore`)
- GitHub Actions uses explicit environment variables
- No secrets in docker-compose.yml (use environment variables)

### 11.2 Network Isolation

- Services run in isolated Docker network
- Ports exposed only to host (not public)
- No external network access required

### 11.3 Test Data Isolation

- Each test run uses fresh containers
- No persistent data between runs
- Containers destroyed after tests (`docker-compose down -v`)

## 12. Performance Considerations

### 12.1 Startup Time

- Services should start within 60 seconds
- Health checks ensure readiness before tests
- Parallel service startup reduces total time

### 12.2 Resource Usage

- Containers use minimal resources
- Services shut down immediately after tests
- No persistent resource allocation

### 12.3 Test Execution Time

- Integration tests should complete in reasonable time
- No additional overhead from containerization
- Efficient cleanup to minimize total time

## 13. Documentation Requirements

### 13.1 Docker Compose Documentation

- Comment docker-compose.yml with service descriptions
- Document environment variable requirements
- Provide usage examples

### 13.2 GitHub Actions Documentation

- Document workflow changes
- Explain service startup process
- Document troubleshooting steps

### 13.3 Developer Guide

- How to run Docker Compose locally
- How to debug service issues
- How to modify service configuration

## 14. Success Criteria

### 14.1 Functional Requirements

- ✅ Docker Compose file created with all services
- ✅ Services start successfully
- ✅ Health checks pass
- ✅ Integration tests can connect to services
- ✅ GitHub Actions workflow runs integration tests
- ✅ Environment variables properly surfaced
- ✅ Services cleaned up after tests

### 14.2 Quality Requirements

- ✅ Clear error messages on failures
- ✅ Proper resource cleanup
- ✅ No flaky test runs
- ✅ Consistent behavior across runs

### 14.3 Documentation

- ✅ Docker Compose file documented
- ✅ Workflow changes documented
- ✅ Usage instructions provided

## 15. Implementation Checklist

### Phase 1: Docker Compose Setup
- [ ] Create `docker-compose.yml` file
- [ ] Define MongoDB service with health check
- [ ] Define MinIO service with health check
- [ ] Define Redis service with health check
- [ ] Configure network
- [ ] Test locally with `docker-compose up`
- [ ] Verify all services start and become healthy

### Phase 2: Environment Variable Configuration
- [ ] Map `.env` variables to Docker Compose
- [ ] Verify variable propagation to containers
- [ ] Test integration tests can read variables
- [ ] Document variable requirements

### Phase 3: GitHub Actions Integration
- [ ] Add integration test job to workflow
- [ ] Create `.env` file in workflow
- [ ] Add Docker Compose startup step
- [ ] Add health check wait step
- [ ] Add integration test execution step
- [ ] Add cleanup step with `if: always()`
- [ ] Test workflow execution

### Phase 4: Validation and Testing
- [ ] Verify services start in CI
- [ ] Verify integration tests pass
- [ ] Verify cleanup works correctly
- [ ] Test error handling scenarios
- [ ] Document troubleshooting steps

### Phase 5: Documentation
- [ ] Document Docker Compose usage
- [ ] Document workflow changes
- [ ] Create developer guide
- [ ] Update README if needed

## 16. Future Enhancements

### Potential Improvements

1. **Service Version Pinning**
   - Pin specific versions instead of `latest`
   - Ensure consistent behavior across environments

2. **Parallel Test Execution**
   - Run integration tests in parallel
   - Reduce total test execution time

3. **Service Monitoring**
   - Add logging aggregation
   - Monitor service health during tests

4. **Local Development Integration**
   - Makefile targets for Docker Compose
   - Simplified local development workflow

5. **Test Data Management**
   - Seed test data in containers
   - Reset data between test runs

### Maintenance Considerations

- Keep Docker images updated
- Monitor service startup times
- Review and optimize health checks
- Update environment variable documentation as needed

---

## Appendix A: Docker Compose Full Example

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:latest
    container_name: lvrgd-mongodb
    ports:
      - "${MONGODB_PORT:-27017}:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGODB_USERNAME:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD:-password123}
      MONGO_INITDB_DATABASE: ${MONGODB_DATABASE:-lvrgd}
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s
    networks:
      - lvrgd-network

  minio:
    image: minio/minio:latest
    container_name: lvrgd-minio
    ports:
      - "${MINIO_PORT:-9000}:9000"
      - "${MINIO_CONSOLE_PORT:-9001}:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-lvrgd-user}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-lvrgd-password-0123}
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s
    networks:
      - lvrgd-network

  redis:
    image: redis:latest
    container_name: lvrgd-redis
    ports:
      - "${REDIS_PORT:-6379}:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis123}
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 5s
    networks:
      - lvrgd-network

networks:
  lvrgd-network:
    driver: bridge
```

## Appendix B: GitHub Actions Workflow Example

See Section 5.2 for complete workflow job definition.

## Appendix C: Environment Variables Reference

### MongoDB Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| MONGODB_HOST | Yes | localhost | MongoDB hostname |
| MONGODB_PORT | No | 27017 | MongoDB port |
| MONGODB_DATABASE | Yes | lvrgd | Database name |
| MONGODB_USERNAME | No | admin | Root username |
| MONGODB_PASSWORD | No | password123 | Root password |

### MinIO Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| MINIO_ENDPOINT | Yes | localhost:9000 | MinIO endpoint (host:port) |
| MINIO_PORT | No | 9000 | MinIO API port |
| MINIO_CONSOLE_PORT | No | 9001 | MinIO console port |
| MINIO_ACCESS_KEY | Yes | lvrgd-user | MinIO access key |
| MINIO_SECRET_KEY | Yes | lvrgd-password-0123 | MinIO secret key |
| MINIO_SECURE | No | false | Use HTTPS |
| MINIO_REGION | No | us-east-1 | MinIO region |
| MINIO_BUCKET | No | lvrgd-test-bucket | Default bucket name |

### Redis Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| REDIS_HOST | Yes | localhost | Redis hostname |
| REDIS_PORT | No | 6379 | Redis port |
| REDIS_PASSWORD | No | redis123 | Redis password |

---

**Document Control:**
- **Author**: AI Specification Generator
- **Reviewers**: Development Team
- **Approval Status**: Pending Review
- **Last Updated**: 2025-01-27
- **Next Review**: Upon implementation completion

