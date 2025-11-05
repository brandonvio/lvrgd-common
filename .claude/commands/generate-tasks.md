---
name: generate-tasks
description: Generate comprehensive task breakdown from specification file using constitution-task-generator agent
argument-hint: "path/to/spec-file.md"
allowed-tools: Read, Write, Grep, Glob, Agent
---

Invoke the constitution-task-generator agent to analyze a specification file and generate a comprehensive, constitution-compliant task breakdown.

The agent will read the project constitution, analyze the specification for constitutional compliance, and produce a detailed task list that ensures adherence to Radical Simplicity, Fail Fast Philosophy, Type Safety, Dependency Injection, and SOLID principles.

## Usage

```bash
/generate-tasks path/to/spec-file.md
```

## Examples

```bash
# Generate tasks for feature specification
/generate-tasks spec/feature-specification.md

# Generate tasks for parallel pipeline feature
/generate-tasks spec/parallel-pipeline.md

# Generate tasks for model optimization spec
/generate-tasks spec/model-by-task.md
```

## Steps

### 1. Validate Input
- Check if specification file path is provided via $1
- If no path provided, display usage message and exit
- Verify the specification file exists
- If file doesn't exist, show error message with provided path
- If file is not a markdown file (.md), display warning but proceed

### 2. Invoke Constitution Task Generator Agent
- Call the constitution-task-generator agent with the specification file path
- The agent will:
  - Read `@.claude/constitution.md`
  - Read and analyze the specification file
  - Assess constitutional compliance
  - Identify potential conflicts with constitution principles
  - Generate comprehensive task breakdown
  - Save tasks file as `{spec-basename}-tasks.md` in same directory as spec

### 3. Report Success
After agent completes, provide summary:
- Confirm tasks file location (absolute path)
- Display success message
- Provide next steps recommendations

## What the Agent Generates

The constitution-task-generator agent creates a comprehensive markdown file with:

**Specification Analysis:**
- Constitutional compliance assessment
- Identification of aligned requirements
- Flagging of potential conflicts with constitution
- Simplification opportunities

**Task Breakdown:**
- Phase 1: Data Models (Pydantic/dataclass definitions)
- Phase 2: Service Layer (with dependency injection patterns)
- Phase 3: Integration Layer (AWS services, external APIs)
- Phase 4: Testing (unit tests with moto mocking strategies)
- Phase 5: Documentation & Review

**Constitutional Guidance:**
- Each task explicitly references applicable principles (I-VII)
- Implementation notes enforcing constitutional compliance
- Type safety requirements
- Dependency injection patterns with code examples
- SOLID principles compliance guidance
- Complexity warnings and simplification recommendations

**Quality Assurance:**
- Radical Simplicity checklist
- Fail Fast checklist
- Type Safety checklist
- Dependency Injection checklist
- SOLID Principles checklist
- Success criteria with functional and constitutional requirements

## Output Location

Tasks file will be saved as:
```
{specification-directory}/{spec-filename-without-extension}-tasks.md
```

**Examples:**
- `spec/feature-specification.md` → `spec/feature-specification-tasks.md`
- `spec/parallel-pipeline.md` → `spec/parallel-pipeline-tasks.md`
- `docs/new-feature.md` → `docs/new-feature-tasks.md`

## Error Messages

**No file path provided:**
```
Error: Specification file path required.

Usage: /generate-tasks path/to/spec-file.md

Example: /generate-tasks spec/model-by-task.md
```

**File doesn't exist:**
```
Error: Specification file not found: {provided-path}

Please verify the file path and try again.
```

**Non-markdown file warning:**
```
Warning: File does not have .md extension: {file-path}
Proceeding with task generation anyway...
```

## Agent Integration

This command leverages the constitution-task-generator agent which:
- Enforces all seven constitutional principles
- Questions complexity at every turn
- Provides concrete implementation guidance
- Flags specification conflicts constructively
- Generates moto-based testing strategies
- Ensures proper dependency injection patterns
- Maintains SOLID principles throughout

The generated tasks integrate seamlessly with the task-executor agent for implementation tracking.

## Constitutional Principles Applied

The agent ensures all generated tasks comply with:

**I. Radical Simplicity** - Simplest possible implementation, no unnecessary complexity
**II. Fail Fast Philosophy** - No fallback logic, trust assumptions and fail immediately
**III. Comprehensive Type Safety** - Type hints everywhere, no runtime type checking
**IV. Structured Data Models** - Pydantic/dataclass models, never loose dictionaries
**V. Unit Testing with Mocking** - Comprehensive test coverage with appropriate mocking strategies
**VI. Dependency Injection** - Constructor injection, optional dependencies with type hints
**VII. SOLID Principles** - All five principles strictly applied in every task

## Next Steps After Generation

1. **Review Tasks File**: Open the generated `{spec-basename}-tasks.md`
2. **Validate Compliance**: Ensure tasks align with project requirements
3. **Execute Tasks**: Use task-executor agent or manual implementation
4. **Track Progress**: Check off completed tasks using checkbox format
5. **Code Review**: Verify constitutional compliance during implementation

The generated task breakdown provides a complete roadmap from specification to implementation, ensuring constitutional compliance and maintaining code quality throughout the development process.
