---
name: work
description: Execute work based on user instructions with strict constitutional compliance and task tracking
argument-hint: "detailed instructions for what you want implemented"
allowed-tools: Read, Write, Bash, Grep, Glob, TodoWrite
---

Execute work based on user instructions while strictly adhering to constitutional principles with comprehensive task tracking.

## Usage

```bash
/work <detailed instructions>
```

## Examples

```bash
/work Create a new user authentication service with email validation
/work Add type hints to all functions in the auth module
/work Refactor the payment service to use dependency injection
/work Implement unit tests for the order processing pipeline
```

## Process Overview

This command implements a structured workflow:

1. **Constitution Review** - Load and understand all NON-NEGOTIABLE principles
2. **Task Breakdown** - Break instructions into discrete, actionable tasks
3. **Task Tracking Setup** - Create TodoWrite task list for progress tracking
4. **Sequential Execution** - Implement each task with status updates
5. **Constitutional Compliance** - Ensure all work follows principles
6. **Completion Summary** - Provide comprehensive summary of work done

## Steps

### 1. Validate Input

```
INSTRUCTIONS = $ARGUMENTS

If INSTRUCTIONS is empty:
  Display: "Error: Work instructions required."
  Display: "Usage: /work <detailed instructions>"
  Display: ""
  Display: "Example: /work Create a user service with email validation"
  Exit
```

### 2. Load Constitutional Principles

Read and internalize **@.claude/constitution.md** to ensure compliance with:

**NON-NEGOTIABLE PRINCIPLES:**

- **I. Radical Simplicity**
  - Always implement the simplest solution
  - Never add unnecessary complexity
  - Keep code simple, easy to understand, and easy to maintain

- **II. Fail Fast Philosophy**
  - No fallback code unless explicitly requested
  - Minimize precautionary type/instance checks
  - Trust required data exists - let it fail if it doesn't

- **III. Comprehensive Type Safety**
  - Type hints EVERYWHERE: tests, services, models, functions
  - Use Python best practices and idiomatic patterns
  - Type hints for ALL parameters and return values

- **IV. Structured Data Models**
  - Use Pydantic models for validation/serialization
  - Use dataclasses for simple data containers
  - NEVER pass around loose dictionaries for structured data

- **V. Unit Testing with Mocking**
  - Appropriate mocking strategies for external dependencies
  - Not over-engineered or excessive

- **VI. Dependency Injection**
  - Constructor injection through `__init__`
  - ALL dependencies are REQUIRED parameters (no Optional, no defaults)
  - NEVER create dependencies inside constructors
  - Pass all dependencies from outside

- **VII. SOLID Principles**
  - Single Responsibility: One reason to change
  - Open/Closed: Open for extension, closed for modification
  - Liskov Substitution: Subtypes substitutable for base types
  - Interface Segregation: Many specific interfaces over one general
  - Dependency Inversion: Depend on abstractions, not concretions

### 3. Break Down Instructions into Tasks

Analyze the instructions and create a comprehensive task breakdown:

```
Display: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Display: "WORK BREAKDOWN"
Display: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Display: "Instructions: {INSTRUCTIONS}"
Display: ""
Display: "Analyzing and breaking down into discrete tasks..."
Display: ""

Create a numbered list of actionable tasks:
- Each task should be specific and measurable
- Include file paths where applicable
- Note which constitutional principles apply
- Identify dependencies between tasks
- Estimate complexity (simple/moderate/complex)

Display the task breakdown clearly:
Display: "Tasks Identified:"
Display: "1. [Task description] - {Constitutional Principle}"
Display: "2. [Task description] - {Constitutional Principle}"
...
Display: ""
```

### 4. Initialize Task Tracking

Use TodoWrite to create a task list for progress tracking:

```
TodoWrite with tasks:
[
  {
    "description": "Task 1 description",
    "status": "pending",
    "context": "Constitutional principle(s) to follow"
  },
  {
    "description": "Task 2 description",
    "status": "pending",
    "context": "Constitutional principle(s) to follow"
  },
  ...
]

Display: "Task tracking initialized. Beginning implementation..."
Display: ""
```

### 5. Execute Tasks Sequentially

For each task in the breakdown:

```
FOR EACH TASK:

  # Mark task as in progress
  Update TodoWrite: status = "in_progress"

  Display: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  Display: "TASK {N}/{TOTAL}: {TASK_DESCRIPTION}"
  Display: "Status: IN PROGRESS"
  Display: "Constitutional Focus: {APPLICABLE_PRINCIPLES}"
  Display: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  Display: ""

  # Implement the task
  Execute task following constitutional principles:

  - Read relevant files if needed
  - Apply Radical Simplicity - choose simplest approach (functions must be <10 complexity, <50 statements)
  - Use Type Hints everywhere
  - Use Pydantic/dataclasses for data structures
  - Implement Dependency Injection (all deps REQUIRED)
  - Follow SOLID principles
  - Apply Fail Fast - no defensive programming, no blind exception catching
  - Add unit tests with appropriate mocking
  - Write to files as needed

  # LINTING QUALITY GATE (MANDATORY)
  BEFORE marking complete - Linting Quality Gate:
  1. Run: ruff format {modified_files}
  2. Run: ruff check --fix {modified_files}
  3. Run: ruff check {modified_files}
  4. If violations exist: STOP and manually resolve:
     - C901/PLR0915 (complexity >10 or >50 statements) → refactor into smaller functions (VIOLATES Principle I)
     - BLE001 (blind exception) → use specific exception types (VIOLATES Principle II)
     - PERF203 (try-except in loop) → optimize or accept with justification
     - A002 (builtin shadow) → rename variables
     - FBT* (boolean args) → use named parameters or enums
     - SIM* (simplification) → apply suggested pattern
  5. Re-run: ruff check {modified_files}
  6. Only proceed when ruff check reports ZERO violations

  Display: "Implementation complete for: {TASK_DESCRIPTION}"
  Display: "Linting: CLEAN (zero violations)"
  Display: ""

  # Mark task as completed (only after linting is clean)
  Update TodoWrite: status = "completed"

  Display: "Status: ✅ COMPLETED"
  Display: ""

END FOR
```

### 6. Provide Completion Summary

After all tasks are complete:

```
Display: ""
Display: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Display: "                    WORK COMPLETE"
Display: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Display: ""
Display: "Original Instructions:"
Display: "{INSTRUCTIONS}"
Display: ""
Display: "Tasks Completed: {COMPLETED_COUNT}/{TOTAL_COUNT}"
Display: ""

Display: "Files Modified/Created:"
- List all files that were modified or created
- Include absolute paths
- Note type of change (created, modified, deleted)

Display: ""
Display: "Constitutional Compliance:"
- Confirm adherence to each applicable principle
- Note any documented exceptions or deviations

Display: ""
Display: "Summary:"
- Brief description of what was accomplished
- Key changes made
- Any important notes or considerations

Display: ""
Display: "Next Steps:"
- Recommend follow-up actions (testing, review, etc.)
- Suggest validation or verification steps
- Note any manual steps required

Display: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

## Error Handling

Handle errors gracefully throughout execution:

```
If error occurs during task execution:
  1. Mark current task as "failed" in TodoWrite
  2. Display error details clearly
  3. Provide context about what was being attempted
  4. Suggest resolution steps if possible
  5. Continue with remaining tasks OR stop if critical failure
  6. Include failure summary in completion report
```

## Constitutional Compliance Checklist

Every task implementation must verify:

- [ ] **Radical Simplicity** - Implemented the simplest possible solution (functions <10 complexity, <50 statements)
- [ ] **Fail Fast** - No defensive programming or unnecessary fallbacks, no blind exception catching
- [ ] **Type Safety** - Type hints on ALL functions and parameters
- [ ] **Structured Data** - Used Pydantic/dataclasses, not dicts
- [ ] **Unit Testing** - Added tests with appropriate mocking
- [ ] **Dependency Injection** - All deps REQUIRED, none created in constructors
- [ ] **SOLID Principles** - SRP, OCP, LSP, ISP, DIP all followed
- [ ] **Linting Clean** - Zero violations from `ruff check` (MANDATORY)

## Notes

### When to Use This Command

- Implementing new features or functionality
- Refactoring existing code to constitutional standards
- Adding tests or improving test coverage
- Creating new services, models, or components
- Any work requiring constitutional compliance

### Task Granularity

Tasks should be:
- **Atomic** - Each task is a complete unit of work
- **Specific** - Clear what needs to be done
- **Measurable** - Can verify when complete
- **Ordered** - Respects dependencies between tasks

### Status Updates

The command provides real-time status updates:
- **Starting** - When task begins execution
- **In Progress** - During task implementation
- **Completed** - When task finishes successfully
- **Failed** - If task encounters an error

### Quality Gates

All code must pass:
- Type hint completeness check
- Simplicity review (no unnecessary complexity, functions <10 complexity, <50 statements)
- Dependency injection validation (no Optional, no defaults)
- SOLID principles compliance
- Fail-fast philosophy adherence (no blind exception catching)
- **Linting quality gate (MANDATORY):**
  - `ruff format` applied
  - `ruff check --fix` applied
  - `ruff check` returns ZERO violations
  - All complexity, exception, and style violations resolved

## Example Execution

**Command:**
```bash
/work Add email validation to the user registration service
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORK BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Instructions: Add email validation to the user registration service

Tasks Identified:
1. Create EmailValidator dataclass with validation logic - Type Safety, Structured Data
2. Add EmailValidator to UserService via DI - Dependency Injection
3. Update UserService.register() with email validation - Type Safety, Fail Fast
4. Add unit tests for EmailValidator - Unit Testing
5. Add unit tests for UserService with email validation - Unit Testing, Mocking

Task tracking initialized. Beginning implementation...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK 1/5: Create EmailValidator dataclass
Status: IN PROGRESS
Constitutional Focus: Type Safety, Structured Data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Implementation details...]

Status: ✅ COMPLETED

[... continues for all tasks ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    WORK COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tasks Completed: 5/5

Files Modified/Created:
- /path/to/validators/email_validator.py (created)
- /path/to/services/user_service.py (modified)
- /path/to/tests/test_email_validator.py (created)
- /path/to/tests/test_user_service.py (modified)

Constitutional Compliance: ✅ All principles followed

Summary: Added email validation to user registration with proper
dependency injection, complete type safety, and comprehensive tests.

Next Steps:
1. Run test suite to verify all tests pass
2. Review code changes for quality
3. Consider integration testing if needed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## See Also

- `/generate-spec` - Generate specifications for complex features
- `/generate-tasks` - Generate detailed task breakdowns from specs
- `/execute-tasks` - Execute tasks from task files with review loop
- `/code-review` - Perform constitutional code review
- `@.claude/constitution.md` - Full constitutional principles
