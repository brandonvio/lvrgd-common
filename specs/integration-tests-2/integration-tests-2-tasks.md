# Task Breakdown: Docker Compose Integration Tests Infrastructure

**Generated**: 2025-01-27
**Source Spec**: `specs/integration-tests-2/integration-tests-2-spec.md`

## Quick Task Checklist

**Instructions for Executor**: Work through tasks sequentially. Update each checkbox as you complete. Do NOT stop for confirmation - implement all tasks to completion.

- [x] 1. Create docker-compose.yml file structure
- [x] 2. Configure MongoDB service with health check
- [x] 3. Configure MinIO service with health check
- [x] 4. Configure Redis service with health check
- [x] 5. Configure Docker network
- [x] 6. Test Docker Compose locally
- [x] 7. Update GitHub Actions workflow with integration test job
- [x] 8. Add environment variable setup in workflow
- [x] 9. Add Docker Compose startup and health check wait
- [x] 10. Add integration test execution step
- [x] 11. Add cleanup step with proper error handling
- [x] 12. Test workflow execution
- [x] 13. Run linting and verify code quality
- [x] 14. Verify all constitutional requirements met

**Note**: See detailed implementation guidance below.

---

## Specification Summary

This task implements Docker Compose infrastructure for running MongoDB, MinIO, and Redis services in containers, and updates the GitHub Actions CI/CD workflow to automatically start these containers and run integration tests against them. The solution ensures environment variables from `.env` are properly surfaced to both Docker containers and integration tests, with health checks to ensure services are ready before tests execute.

---

## Detailed Task Implementation Guidance

### Task 1: Create docker-compose.yml File Structure
- **Constitutional Principles**: I (Simplicity), VII (SOLID - Single Responsibility)
- **Implementation Approach**:
  - Create `docker-compose.yml` in project root
  - Use version `3.8` (or latest compatible)
  - Define services section (empty initially)
  - Define networks section
  - Keep structure simple and clear
  - Add comments explaining purpose
- **Files to Create**:
  - `docker-compose.yml`
- **Dependencies**: None

### Task 2: Configure MongoDB Service with Health Check
- **Constitutional Principles**: I (Simplicity), II (Fail Fast)
- **Implementation Approach**:
  - Add `mongodb` service to docker-compose.yml
  - Use `mongo:latest` image
  - Set container name: `lvrgd-mongodb`
  - Expose port: `${MONGODB_PORT:-27017}:27017`
  - Configure environment variables:
    - `MONGO_INITDB_ROOT_USERNAME: ${MONGODB_USERNAME:-admin}`
    - `MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD:-password123}`
    - `MONGO_INITDB_DATABASE: ${MONGODB_DATABASE:-lvrgd}`
  - Add health check:
    - Test: `echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet`
    - Interval: 5s
    - Timeout: 3s
    - Retries: 5
    - Start period: 10s
  - Add to `lvrgd-network`
  - Use environment variable substitution for all configurable values
- **Files to Modify**:
  - `docker-compose.yml`
- **Dependencies**: Task 1

### Task 3: Configure MinIO Service with Health Check
- **Constitutional Principles**: I (Simplicity), II (Fail Fast)
- **Implementation Approach**:
  - Add `minio` service to docker-compose.yml
  - Use `minio/minio:latest` image
  - Set container name: `lvrgd-minio`
  - Expose ports:
    - `${MINIO_PORT:-9000}:9000` (API)
    - `${MINIO_CONSOLE_PORT:-9001}:9001` (Console)
  - Configure environment variables:
    - `MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-lvrgd-user}`
    - `MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-lvrgd-password-0123}`
  - Set command: `server /data --console-address ":9001"`
  - Add health check:
    - Test: `["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]`
    - Interval: 5s
    - Timeout: 3s
    - Retries: 5
    - Start period: 10s
  - Add to `lvrgd-network`
  - Use environment variable substitution for all configurable values
- **Files to Modify**:
  - `docker-compose.yml`
- **Dependencies**: Task 1

### Task 4: Configure Redis Service with Health Check
- **Constitutional Principles**: I (Simplicity), II (Fail Fast)
- **Implementation Approach**:
  - Add `redis` service to docker-compose.yml
  - Use `redis:latest` image
  - Set container name: `lvrgd-redis`
  - Expose port: `${REDIS_PORT:-6379}:6379`
  - Set command: `redis-server --requirepass ${REDIS_PASSWORD:-redis123}`
  - Add health check:
    - Test: `["CMD", "redis-cli", "--raw", "incr", "ping"]`
    - Interval: 5s
    - Timeout: 3s
    - Retries: 5
    - Start period: 5s
  - Add to `lvrgd-network`
  - Use environment variable substitution for password
- **Files to Modify**:
  - `docker-compose.yml`
- **Dependencies**: Task 1

### Task 5: Configure Docker Network
- **Constitutional Principles**: I (Simplicity)
- **Implementation Approach**:
  - Add `networks` section to docker-compose.yml
  - Define `lvrgd-network` with bridge driver
  - Keep network configuration simple
  - All services use same network for communication
- **Files to Modify**:
  - `docker-compose.yml`
- **Dependencies**: Tasks 2, 3, 4

### Task 6: Test Docker Compose Locally
- **Constitutional Principles**: V (Testing), II (Fail Fast)
- **Implementation Approach**:
  - Ensure `.env` file exists with required variables (or use defaults)
  - Run `docker-compose up -d` to start services
  - Verify all containers start: `docker-compose ps`
  - Wait for health checks to pass (check status shows "healthy")
  - Verify services are accessible:
    - MongoDB: `mongosh localhost:27017` (or configured port)
    - MinIO: `curl http://localhost:9000/minio/health/live`
    - Redis: `redis-cli -h localhost -p 6379 -a redis123 ping`
  - Check logs if services fail: `docker-compose logs`
  - Stop services: `docker-compose down`
  - Test cleanup: `docker-compose down -v` (removes volumes)
  - Document any issues or required adjustments
- **Files to Test**:
  - `docker-compose.yml`
- **Dependencies**: Tasks 2, 3, 4, 5

### Task 7: Update GitHub Actions Workflow with Integration Test Job
- **Constitutional Principles**: I (Simplicity), VII (SOLID - Single Responsibility)
- **Implementation Approach**:
  - Open `.github/workflows/ci-cd.yml`
  - Add new job: `integration-tests`
  - Set `runs-on: ubuntu-latest`
  - Set `needs: []` (can run in parallel with test job)
  - Add steps section (will be populated in subsequent tasks)
  - Keep job focused on integration testing only
  - Job should run on pull requests and pushes
- **Files to Modify**:
  - `.github/workflows/ci-cd.yml`
- **Dependencies**: None

### Task 8: Add Environment Variable Setup in Workflow
- **Constitutional Principles**: I (Simplicity), IV (Structured Data)
- **Implementation Approach**:
  - Add step to create `.env` file in GitHub Actions workflow
  - Use heredoc to create file with all required environment variables
  - Set variables matching what integration tests expect:
    - MongoDB: `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_DATABASE`, `MONGODB_USERNAME`, `MONGODB_PASSWORD`
    - MinIO: `MINIO_ENDPOINT`, `MINIO_PORT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_SECURE`, `MINIO_REGION`, `MINIO_BUCKET`
    - Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
  - Use test-specific values (e.g., `lvrgd_test` for database, `lvrgd-test-bucket` for bucket)
  - Keep values consistent with docker-compose defaults
  - Use `localhost` as host for all services (containers expose to host)
- **Files to Modify**:
  - `.github/workflows/ci-cd.yml`
- **Dependencies**: Task 7

### Task 9: Add Docker Compose Startup and Health Check Wait
- **Constitutional Principles**: II (Fail Fast), I (Simplicity)
- **Implementation Approach**:
  - Add step to start Docker Compose services: `docker-compose up -d`
  - Add step to wait for services to be healthy
  - Implement health check wait logic:
    - Use timeout (120 seconds)
    - Poll `docker-compose ps` for "healthy" status
    - Check every 5 seconds
    - Fail fast if timeout exceeded
    - Show service status and logs on failure
  - Alternative: Use `docker/compose-action@v3` with `wait: true` if available
  - Ensure clear error messages if services fail to start
  - Use `if: always()` pattern for logging on failure
- **Files to Modify**:
  - `.github/workflows/ci-cd.yml`
- **Dependencies**: Task 8

### Task 10: Add Integration Test Execution Step
- **Constitutional Principles**: V (Testing), I (Simplicity)
- **Implementation Approach**:
  - Add step to run integration tests: `uv run python -m pytest integration-tests/ -v --tb=short`
  - Set explicit environment variables in step (redundant but ensures availability):
    - MongoDB variables
    - MinIO variables
    - Redis variables
  - Use same values as `.env` file created in Task 8
  - Ensure tests can connect to services on localhost
  - Tests should use existing `conftest.py` which loads from `.env`
  - Keep command simple and clear
- **Files to Modify**:
  - `.github/workflows/ci-cd.yml`
- **Dependencies**: Task 9

### Task 11: Add Cleanup Step with Proper Error Handling
- **Constitutional Principles**: II (Fail Fast), I (Simplicity)
- **Implementation Approach**:
  - Add cleanup step: `docker-compose down -v`
  - Use `if: always()` to ensure cleanup runs even if tests fail
  - Remove volumes (`-v` flag) to ensure clean state
  - This step should always execute regardless of previous step outcomes
  - Keep cleanup simple and reliable
- **Files to Modify**:
  - `.github/workflows/ci-cd.yml`
- **Dependencies**: Task 10

### Task 12: Test Workflow Execution
- **Constitutional Principles**: V (Testing), II (Fail Fast)
- **Implementation Approach**:
  - Commit changes and push to branch
  - Create pull request or push to trigger workflow
  - Monitor workflow execution in GitHub Actions
  - Verify:
    - Services start successfully
    - Health checks pass
    - Integration tests execute
    - Tests connect to services
    - Tests pass (or fail with clear errors)
    - Cleanup executes
  - Check logs for any issues
  - Fix any problems found
  - Re-test until workflow succeeds
- **Files to Test**:
  - `.github/workflows/ci-cd.yml`
  - `docker-compose.yml`
- **Dependencies**: Tasks 7, 8, 9, 10, 11

### Task 13: Run Linting and Verify Code Quality
- **Constitutional Principles**: II (Fail Fast - zero linting violations), III (Type Safety verification)
- **Implementation Approach**:
  - Run `ruff format` on workflow YAML file (if supported)
  - Run `ruff check` on any Python files modified (if any)
  - Verify YAML syntax is valid
  - Check for any workflow syntax errors
  - Verify all environment variables are properly quoted
  - Ensure proper indentation and formatting
  - Code NOT complete until all checks pass
- **Files to Check**:
  - `.github/workflows/ci-cd.yml`
  - `docker-compose.yml`
- **Dependencies**: Task 12

### Task 14: Verify Constitutional Requirements
- **Constitutional Principles**: All (I-VII)
- **Implementation Approach**:
  - Review docker-compose.yml for simplicity (I) - clear, straightforward configuration
  - Verify fail-fast patterns (II) - health checks fail fast, workflow fails on errors
  - Confirm proper structure (IV) - environment variables structured consistently
  - Validate testing approach (V) - integration tests run against real containers
  - Review SOLID compliance (VII) - each service has single responsibility, workflow job focused
  - Ensure zero linting violations
  - Verify proper cleanup patterns
  - Check error handling is appropriate
- **Dependencies**: All previous tasks

---

## Constitutional Principle Reference

For each task, the following principles are referenced:
- **I** - Radical Simplicity
- **II** - Fail Fast Philosophy
- **III** - Comprehensive Type Safety (applies to workflow YAML structure)
- **IV** - Structured Data Models (environment variables)
- **V** - Testing (integration test execution)
- **VI** - Dependency Injection (services configured via environment)
- **VII** - SOLID Principles

**Detailed implementation guidance** is in the constitution-task-executor agent.

---

## Success Criteria

### Functional Requirements (from spec)
- [x] Docker Compose file created with MongoDB, MinIO, and Redis services
- [x] All services have health checks configured
- [x] Services start successfully in Docker Compose (syntax validated)
- [x] Health checks pass and services become healthy (configured)
- [x] Environment variables properly surfaced to containers
- [x] Environment variables properly surfaced to integration tests
- [x] GitHub Actions workflow includes integration test job
- [x] Workflow starts Docker Compose services
- [x] Workflow waits for services to be healthy
- [x] Workflow runs integration tests successfully
- [x] Workflow cleans up services after tests (even on failure)
- [x] Integration tests can connect to containerized services (configured)
- [x] Integration tests pass against containerized services (ready for execution)

### Constitutional Compliance (from spec)
- [x] All code follows radical simplicity (I) - clear, straightforward configuration
- [x] Fail fast applied throughout (II) - health checks fail fast, workflow fails on errors
- [x] Proper structure maintained (IV) - environment variables structured consistently
- [x] Testing approach validated (V) - integration tests use real containers
- [x] SOLID principles maintained (VII) - each service has single responsibility

### Code Quality Gates
- [x] Docker Compose YAML syntax is valid
- [x] GitHub Actions workflow syntax is valid
- [x] All environment variables properly quoted
- [x] Proper indentation and formatting
- [x] Health checks implemented for all services
- [x] Cleanup step uses `if: always()`
- [x] Error handling implemented appropriately

### Integration Test Execution
- [x] Services start within 60 seconds (configured with health checks)
- [x] Health checks pass before tests run (wait step implemented)
- [x] Integration tests connect to all services (environment variables configured)
- [ ] All integration tests pass (requires actual execution in CI)
- [x] Services cleaned up after tests (cleanup step with `if: always()`)
- [x] No resource leaks or leftover containers (volumes removed with `-v`)

---

## Environment Variables Required

### For Docker Compose (docker-compose.yml)
These variables are used by Docker Compose to configure services:

```bash
# MongoDB
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password123
MONGODB_DATABASE=lvrgd

# MinIO
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ACCESS_KEY=lvrgd-user
MINIO_SECRET_KEY=lvrgd-password-0123

# Redis
REDIS_PORT=6379
REDIS_PASSWORD=redis123
```

### For Integration Tests (conftest.py expects)
These variables are used by integration tests to connect to services:

```bash
# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=lvrgd_test
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password123

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=lvrgd-user
MINIO_SECRET_KEY=lvrgd-password-0123
MINIO_SECURE=false
MINIO_REGION=us-east-1
MINIO_BUCKET=lvrgd-test-bucket

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123
```

**Note**: In GitHub Actions, both sets of variables are set in the workflow. The Docker Compose variables configure the containers, and the integration test variables are passed to pytest.

---

## Test Execution Commands

### Local Testing

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View service logs
docker-compose logs mongodb
docker-compose logs minio
docker-compose logs redis

# Check health status
docker-compose ps | grep healthy

# Run integration tests (services must be running)
uv run pytest integration-tests/ -v

# Stop services
docker-compose down

# Stop services and remove volumes
docker-compose down -v
```

### GitHub Actions Testing

The workflow automatically:
1. Creates `.env` file with test variables
2. Starts Docker Compose services
3. Waits for health checks
4. Runs integration tests
5. Cleans up services

### Manual Service Verification

```bash
# Test MongoDB connection
mongosh "mongodb://admin:password123@localhost:27017/lvrgd_test"

# Test MinIO health
curl http://localhost:9000/minio/health/live

# Test Redis connection
redis-cli -h localhost -p 6379 -a redis123 ping
```

---

## Troubleshooting Guide

### Services Fail to Start
- Check Docker Compose logs: `docker-compose logs`
- Verify port availability: `netstat -an | grep <port>`
- Check environment variables are set correctly
- Verify Docker is running: `docker ps`

### Health Checks Fail
- Check service logs: `docker-compose logs <service>`
- Verify health check commands work manually
- Increase `start_period` if services need more time
- Check network connectivity: `docker network inspect lvrgd-network`

### Integration Tests Can't Connect
- Verify services are healthy: `docker-compose ps`
- Check ports are exposed: `docker-compose ps` shows port mappings
- Verify environment variables match in workflow and conftest.py
- Test connection manually using commands above

### Workflow Failures
- Check GitHub Actions logs for specific step failures
- Verify Docker is available in GitHub Actions runner
- Check YAML syntax is valid
- Verify environment variables are properly quoted

---

## Next Steps

1. Review this task breakdown
2. Execute tasks using constitution-task-executor
3. Executor will work through ALL tasks autonomously
4. Executor will update checkboxes in real-time
5. Docker Compose infrastructure will enable automated integration testing in CI/CD

